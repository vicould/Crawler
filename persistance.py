#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
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
    """Class to write down the datas collected to a repository of html files. A
    pers folder is created if non existent, containing then a folder for each
    day you runned the Crawler. Then, when you executed the crawler, a
    repository in the daily folder is created, named with the execution start
    time. See FileWriter doc string for more infos on the internal structure of
    the repository."""
    def __init__(self):
        self._init_repo()
        self._init_folders()


    def _init_repo(self):
        # creates the pers folder if non existing
        try:
            os.listdir(os.path.join(os.getcwd(), 'pers'))
        except OSError, err:
            if err.errno == 2:
                os.mkdir('pers', 0755)
                logging.getLogger('persistance.DataPersistance').info('\
Created pers folder in the current path, with mode 0755')


    def _init_folders(self):
        # Creates the folder for the current day and then the actual time
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
                    logging.getLogger('persistance.DataPersistance').info('\
Created day folder in the current path, with mode 0755')

            # creates now folder
            self._path = os.path.join(self._path,
                                  datetime.now().strftime('%H:%M:%S'))
            os.mkdir(self._path, 0755)
            logging.getLogger('persistance.DataPersistance').info('Created\
 %s folder to store the current results' % self._path)


    def launch_dump(self, top10):
        """Launch the dump of the result pool, with the page rank top 10."""
        self._starttime = datetime.now()
        logging.getLogger('persistance.DataPersistance').info('Starting result\
 dumping')

        for i in range(5):
            fw = FileWriter(self._path)
            fw.daemon = True
            fw.start()

        result_pool.join()
        logging.getLogger('persistance.DataPersistance').info('Result dumping\
 finished, starting domain summaries.')
        # once the result_pool is empty, it is time to write down the files for
        # each domain, and then the index file
        for i in range(5):
            fw = FileWriter(self._path, True)
            fw.daemon = True
            fw.start()

        url_per_domain.join()
        # now the index
        logging.getLogger('persistance.DataPersistance').info('Domain\
 all written, finishing dumping with global summary.')
        fw = FileWriter(self._path)
        fw._create_summary_page(domain_set, top10)
        logging.getLogger('persistance.DataPersistance').info('Finished\
 dumping after %ss of execution' % 
                        str(datetime.now() - self._starttime))



class FileWriter(threading.Thread):
    """Thread writing down the result of the crawling. Depending on the boolean
    set in the constructor, it will dump the result data structures, or build
    the summary for each domain.
    The pages are then written to the disk, in the path described in the class
    DataPersistance. For each repository, you have an index.html, which is the
    global summary pointing to each of the domains visited. Then, a folder is
    created for each domain, containing a summary pointing to the urls of the
    domain which have been visited, and all the different pages for each url."""
    def __init__(self, path, domain_dump=False, group=None, target=None,\
                 name=None, *args, **kwargs):
        """Constructor. Set domain_dump argument to True if you want to print
        out only the domains summaries rather than just the results."""
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        self._domain_dump = domain_dump
        self._path = path
        self._my_data = local()


    def _create_summary_page(self, urls, top10):
        # creates the global summary, pointing to all the domains found while
        # crawling
        page = self._prepare_header('Summary page')
        page = ''.join([page, '<h2>Domain index</h2>\n<ul>\n'])
        while True:
            try:
                domain = urls.get_nowait()
                page = ''.join([page, '<li><a href="%s">%s</a></li>\n' %
                                (''.join([domain, '/index.html']), domain)])
            except Empty:
                break
        page = ''.join([page, '</ul>\n<h2>Page rank top 10</h2><ul>\n'])
        for score, link in top10:
            page = ''.join([page, '<li>Score %s for %s</li>\n' %
                            (score, link)])
        page = ''.join([page, '</ul>\n', self._prepare_footer()])
        self._write_file('index.html', page, summary_page=True)


    def _create_domain_page(self, domain, urls):
        # creates the summary page for the domain, containing a list of all
        # pages which can be found in the current domain
        page = ''.join([self._prepare_header(domain),
                        '<a href="../index.html">Return to global summary</a>\
\n<p><ul>\n'])
        for url in urls:
            page = ''.join([page, '<li><a href="%s">%s</a></li>\n' %
                            (self._build_path_from_link(url), url)])
        page = ''.join([page, '</ul></p>\n', self._prepare_footer()])
        self._write_file('index.html', page)


    def _create_page(self, page_url, *args, **kwargs):
        # creates one page, with the page_url as argument. You can add other
        # arguments to write down passing keyworded arguments.
        # more infos about *args and **kwargs here :
        # http://www.saltycrane.com/blog/2008/01/how-to-use-args-and-kwargs-in-python/
        page = ''.join([self._prepare_header(page_url),
                        '<a href="index.html">Return to domain summary</a>\n'])
        for key,value in kwargs.items():
            try:
                page = ''.join([page, self._prepare_section(key,value)])
            except UnicodeDecodeError as e:
                logging.getLogger('persistance.FileWriter').warning('Unicode\
DecodeError %s' % e.reason)
        page = ''.join([page, self._prepare_footer()])
        self._write_file(page_url, page, filename_url=True)


    def _prepare_header(self, title):
        # returns the header of the page with the specified title
        return '<html>\n<head><title>%s</title></head>\
\n<body>\n<h1>%s</h1>\n' % (title, title)


    def _prepare_footer(self):
        # ends the content and closes the tags
        return '</body>\n</html>\n'


    def _prepare_section(self, section_name, content):
        # prepare one section of the page, with the section name and the
        # content given as parameter
        html = '<h2>%s</h2>\n<p>' % section_name
        if section_name == 'anchors':
            html = ''.join([html, self._prepare_anchor(content)])
        elif section_name == 'links':
            html = ''.join([html, self._prepare_links(content)])
        elif hasattr(content, '__iter__'):
            # unknown content, tries to iterate it
            html = ''.join([html, '<ul>\n'])
            for item in content:
                html = ''.join([html, '<li>%s</li>\n' % item])
            html = ''.join([html, '</ul>'])
        else:
            # non iterable content, just writes it
            html = ''.join([html, '%s' % content])
        return ''.join([html, '</p>\n'])


    def _prepare_anchor(self, anchors):
        # builds the list of anchors
        content = '<ul>'
        for link, anchor in anchors:
            try:
                content = ''.join([content, '<li><a href="%s">%s</a></li>\n' %
                     (self._build_path_from_link(link), anchor)])
            except UnicodeDecodeError as e:
                logging.getLogger('persistance.FileWriter').warning('Unicode\
DecodeError %s' % e.reason)
        return ''.join([content, '</ul>\n'])


    def _prepare_links(self, links):
        # builds the list of links
        content = '<ul>'
        for link in links:
            content = ''.join([content, '<li><a href="%s">%s</a></li>\n' %
                     (self._build_path_from_link(link), link)])
        return ''.join([content, '</ul>\n'])


    def _build_path_from_link(self, link):
        # rebuilds a path from the link, i.e. goes one folder upper if domain
        # changes, and replaces the .html at the end of the name by _.html.
        # This change is made in order to avoid overwriting index.html with our
        # summary, so index.html becomes index_.html
        splitted_url = urlparse.urlparse(link)
        url_domain = splitted_url.netloc
        path = splitted_url.path[1:].replace('/', '_')
        if not path.endswith('.html'):
            path = ''.join([path, '_.html'])
        else:
            path.replace('.html', '_.html')
        if url_domain != self._my_data.current_domain:
            path = ''.join(['../', url_domain, path])
            # goes up from one level and adds the path to the new domain
        return path


    def _write_file(self, filename, content, filename_url = False, summary_page=False):
        # write a file to the disk, filename_url is here to specify the name
        # comes from an url (and is not a domain summary), and summary_page
        # tells the function it is the global summary we are writing, so the
        # path to this page is the root of the repo.
        if filename_url:
            url = filename
            filename = urlparse.urlparse(filename).path[1:].replace('/', '_')
            if not filename.endswith('.html'):
                filename = ''.join([filename, '_.html'])
            else:
                filename = filename.replace('.html', '_.html')
        if not summary_page:
            current_path = os.path.join(self._path,
                                        self._my_data.current_domain)
            try:
                os.listdir(current_path)
            except OSError as err:
                # creates the folder for the current domain
                if err.errno == 2:
                    os.mkdir(current_path, 0755)
                logging.getLogger('persistance.FileWriter').info('Created\
 domain folder under %s' % current_path)
        else:
            current_path = self._path

        html_file = open(os.path.join(current_path,
                                      filename.replace('/', '_')), 'wb')
        try:
            html_file.write(content.encode('utf-8'))
        except UnicodeDecodeError as e:
            logging.getLogger('persistance.FileWriter').warning('UnicodeEncode\
Error %s' % e.reason)
        html_file.close()
        if filename_url:
            logging.getLogger('persistance.FileWriter').info('Wrote %s html\
to store %s content' % (filename, url))
        else:
            logging.getLogger('persistance.FileWriter').info('Wrote %s to %s'\
 % (filename, current_path))


    def _analyze_url(self, url):
        # analyzes the url and update the domain dict with the current url
        splitted_url = urlparse.urlparse(url)
        self._my_data.current_domain = splitted_url.netloc
        domain_set.put(splitted_url.netloc)
        try:
            url_per_domain.add_item_to_key(splitted_url.netloc, url)
        except KeyError: # domain not found in the dict, creates a new entry
            url_per_domain.put(splitted_url.netloc, url)


    def run(self):
        """Runs one thread, with task depending on the parameter passed in the
        constructor: either dumps the result pool, or builds the domains
        summaries."""
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
