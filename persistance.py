#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
from Queue import Queue, Empty
import threading
from threading import local
import urlparse


from data_utils import SynchronizedDict, SetQueue



result_pool = Queue()
url_per_domain = SynchronizedDict()
domain_set = SetQueue()



class DataPersistance:
    """Class to write down the datas collected"""
    def __init__(self):
        self._init_repo()
        self._init_folders()


    def _init_repo(self):
        try:
            os.listdir(os.path.join(os.getcwd(), 'pers'))
        except OSError, err:
            if err.errno == 2:
                os.mkdir('pers', 0755)


    def _init_folders(self):
        """Creates the folder for the current day and then the actual time"""
        try:
            if (self.prefix):
                return
        except AttributeError:
            # creates today folder
            self._path = os.path.join('pers', str(datetime.now().day))
            try:
                os.listdir(os.path.join(os.getcwd(), self._path))
            except OSError, err:
                if err.errno == 2:
                    os.mkdir(self._path, 0755)

            # creates now folder
            self._path = os.path.join(self._path,
                                  datetime.now().strftime('%H:%M:%S'))
            os.mkdir(self._path, 0755)


    def launch_dump(self):
        # result pool dumping
        for i in range(5):
            fw = FileWriter(self._path)
            fw.daemon = True
            fw.start()

        result_pool.join()
        # once the result_pool is empty, it is time to write down the files for
        # each domain, and then the index file
        for i in range(5):
            fw = FileWriter(self._path, True)
            fw.daemon = True
            fw.start()

        url_per_domain.join()
        # now the index
        fw = FileWriter(self._path)
        fw._create_summary_page(domain_set)



class FileWriter(threading.Thread):
    """Thread writing to the disk the dump of one page, i.e. the url, the links
    and the corresponding anchors, the keywords, the various scores and finally
    the content of the page cleant of the html tags."""
    def __init__(self, path, domain_dump=False, group=None, target=None,\
                 name=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        self._domain_dump = domain_dump
        self._path = path
        self._my_data = local()


    def _create_summary_page(self, urls):
        page = self._prepare_header('Summary page')
        page = ''.join([page, '<p><ul>\n'])
        while True:
            try:
                domain = urls.get_nowait()
                page = ''.join([page, '<li><a href="%s">%s</a></li>\n' %
                                (''.join([domain, '/index.html']), domain)])
            except Empty:
                break
        page = ''.join([page, '</ul></p>\n'])
        page = ''.join([page, self._prepare_footer()])
        self._write_file('index.html', page, summary_page=True)


    def _create_domain_page(self, domain, urls):
        page = self._prepare_header(domain)
        page = ''.join([page, '<p><ul>\n'])
        for url in urls:
            page = ''.join([page, '<li><a href="%s">%s</a></li>\n' %
                            (self._build_path_from_link(url), url)])
        page = ''.join([page, '</ul></p>\n'])
        page = ''.join([page, self._prepare_footer()])
        self._write_file('index.html', page)


    def _create_page(self, page_url, *args, **kwargs):
        page = self._prepare_header(page_url)
        for key,value in kwargs.items():
            page = ''.join([page, self._prepare_section(key,value)])
        page = ''.join([page, self._prepare_footer()])
        self._write_file(page_url, page, filename_url=True)


    def _prepare_header(self, title):
        return '<html>\n<head><title>%s</title></head>\
 \n<body>\n<h1>%s</h1>\n' % (title, title)


    def _prepare_footer(self):
        return '</body>\n</html>\n'


    def _prepare_section(self, section_name, content):
        html = '<h2>%s</h2>\n<p>' % section_name
        if section_name == 'anchors':
            html = ''.join([html, self._prepare_anchor(content)])
        elif section_name == 'links':
            html = ''.join([html, self._prepare_links(content)])
        elif hasattr(content, '__iter__'):
            html = ''.join([html, '<ul>\n'])
            for item in content:
                html = ''.join([html, '<li>%s</li>\n' % item])
            html = ''.join([html, '</ul>'])
        else:
            html = ''.join([html, '%s' % content])
        return ''.join([html, '</p>\n'])


    def _prepare_anchor(self, anchors):
        content = '<ul>'
        for link, anchor in anchors:
            content = ''.join([content, '<li><a href="%s">%s</a></li>\n' %
                     (self._build_path_from_link(link), anchor)])
        return ''.join([content, '</ul>\n'])


    def _prepare_links(self, links):
        content = '<ul>'
        for link in links:
            content = ''.join([content, '<li><a href="%s">%s</a></li>\n' %
                     (self._build_path_from_link(link), link)])
        return ''.join([content, '</ul>\n'])


    def _build_path_from_link(self, link):
        splitted_url = urlparse.urlparse(link)
        url_domain = splitted_url.netloc
        path = splitted_url.path[1:].replace('/', '_')
        if not path.endswith('.html'):
            path = ''.join([path, '_.html'])
        if url_domain != self._my_data.current_domain:
            path = ''.join(['../', url_domain, path])
            # goes up from one level and adds the path to the new domain
        return path


    def _write_file(self, filename, content, filename_url = False, summary_page=False):
        if filename_url:
            filename = urlparse.urlparse(filename).path[1:].replace('/', '_')
            if not filename.endswith('.html'):
                filename = ''.join([filename, '_.html'])
        if not summary_page:
            current_path = os.path.join(self._path,
                                        self._my_data.current_domain)
            try:
                os.listdir(current_path)
            except OSError as err:
                # creates the folder for the current domain
                if err.errno == 2:
                    os.mkdir(current_path, 0755)
        else:
            current_path = self._path

        html_file = open(os.path.join(current_path,
                                      filename.replace('/', '_')), 'wb')
        html_file.write(content)
        html_file.close()


    def _analyze_url(self, url):
        # analyzes the url and update the domain dict with the current url
        splitted_url = urlparse.urlparse(url)
        self._my_data.current_domain = splitted_url.netloc
        domain_set.put(splitted_url.netloc)
        try:
            url_per_domain.add_item_to_key(splitted_url.netloc, url)
        except KeyError: # domain not found in the dict, creates a new entry
            url_per_domain.put(splitted_url.netloc, url)


    def change_state(self, new_task):
        """Changes the global state of the thread: all urls have been written
        down, it is time to write the one about the domains."""


    def run(self):
        while not self._domain_dump:
            datas = result_pool.get()
            url = datas.get('url', 'non saved')
            self._analyze_url(url)
            self._create_page(url, **datas)

            result_pool.task_done()


        while self._domain_dump:
            domain, links = url_per_domain.get()
            self._my_data.current_domain = domain
            self._create_domain_page(domain, links)

            url_per_domain.task_done()
