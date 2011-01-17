#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs
import sys
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import urlparse
import robotparser
import re
import time
import mimetypes
from Queue import Queue, Empty
import threading

# modules from the project
from logger import Logger

url_to_visit = Queue()
html_pool = Queue()


class Crawler:
    """The class responsible for the crawling feature. After initializing the
    class with the first domain to interrogate, you can start the crawler in
    standalone mode by calling the run function.
    my_crawler = Crawler('http://www.emse.fr/') # creates the class, with
                                                # www.emse.fr as base url
    my_crawler.run() # launches the crawler in autonomous mode
    The crawler is width-first, visiting all links from one level before going
    anywhere deeper.
    """
    __user_agent = 'DummyCrawler'
    __headers = { 'User_Agent' : __user_agent }
    __url_visited = []
    __current_root = ''
    __page_workers = []


    def __init__(self, base_url, logging=False):
        """Init the crawler with the base url of the indexing. It also sets the
        gentle robot directives parser, in order to start crawling directly
        after the initialization."""
        url_to_visit.put(base_url) # start url

        self.logging = logging
        if self.logging:
            self.__logger_instance = Logger('crawler',
                                           """Initializing dummy crawler.\n""")

        # cuts the url in standart parts
        split_url = urlparse.urlparse(base_url)
        if (split_url.scheme != 'http'):
            if self.logging:
                self.__logger_instance.log_event('Exiting', ["""sorry this crawler \
supports only the http protocol. Exiting now ..."""])
            sys.exit(1)

        # __rp is the nice robot taking care of the webmaster directives
        self.__rp = robotparser.RobotFileParser()

        # sets the current domain, and calls the robot initialization function
        self.__current_root = split_url.scheme + '://'\
                + split_url.netloc + '/'
        new_rules = self.change_domain(self.__current_root)
        if self.logging:
            self.__logger_instance.log_event('New rules found on %s' %
                                                 self.__current_root,
                                                 new_rules)
            self.__logger_instance.log_short_message('Crawler initialized')


    def change_domain(self, domain):
        """Function to retrieve the content of the robots rules for the domain
        given as parameter. Returns the new rules as stream."""
        robots_url = urlparse.urljoin(domain, 'robots.txt')
        try:
            self.__rp.set_url(urlparse.urljoin(domain, 'robots.txt'))
            self.__rp.read() # parses the content of the directives
            # the rules are now in memory, we could stop here

            # returns the content of the file for logging purpose
            return urllib2.urlopen(robots_url)

        except HTTPError, e:
            self.__logger_instance.log_short_message('Could not get robots on '
                                                     + domain + ' ' + str(e))
        except URLError, e:
            self.__logger_instance.log_short_message('Could not get robots on '
                                                     + domain + ' ' + str(e))


    def fetch_page(self, url):
        """Fetches the url given as input and returns the page. Returns an empty
        string when an exception occured.
        """

        html = ''
        try:
            # builds the request
            req = urllib2.Request(url, headers=self.__headers)

            # opens the page
            response = urllib2.urlopen(req)
            # tests the MIME type of the page, crawling on non html documents
            # is not really useful.
            if (response.info().gettype() == 'text/html'):
                html = response.read()
        except HTTPError, he:
            self.__logger_instance.log_event('HTTPError', [str(he.code) + ' ',
                                                           he.read()])
        except URLError, ex:
            self.__logger_instance.log_event('URLError', [str(ex.reason)])

        return html


    def get_visited_links(self):
        return self.__url_visited


    def get_links_to_visit(self):
        return url_to_visit


    def crawl(self):
        """Call this if you want the crawler to do all his stuff without you."""
        i = 0
        # limiting the trip of the crawler
        while (i < 100):
            time.sleep(1) # waits 1s at each step
            i += 1

            # takes one url from the queue
            current_url = url_to_visit.get()

            if (current_url in self.__url_visited):
                # url was already visited once
                i -= 1
                continue

            self.__logger_instance.log_short_message('%s is current' %
                                                     current_url)

            split_url = urlparse.urlparse(current_url)
            new_root = split_url.scheme + '://' + split_url.netloc + '/'

            # domain is changing, we need to fetch the robots directives from
            # the new domain
            if (new_root != self.__current_root):
                self.__logger_instance.log_short_message("""Changing domain to\
%s""" % new_root)
                self.__current_root = new_root
                new_rules = self.change_domain(self.__current_root)
                self.__logger_instance.log_event('New rules found on %s' %
                                                 self.__current_root,
                                                 new_rules)

            # checks the url against the robots.txt directives
            if (not self.__rp.can_fetch(self.__user_agent, url)): 
                self.__logger_instance.log_event('robot non authorized', [url])
                continue

            page = self.fetch_page(current_url)
	    
            if (page == ''): # page is empty, no need to do anything with it
                continue

            html_pool.put((current_url, page)) # put the page in the pool

            self.__url_visited.append(current_url)

            # start here a new PageProcessor thread
            worker = PageProcessor(name=current_url)
            self.__page_workers.append(worker)
            worker.start()

        # end of execution
        for worker in self.__page_workers:
            # waits for all threads to finish
            if (worker.is_alive() and self.logging):
                self.__logger_instance.log_short_message('%s is still alive' %
                                                         worker.name)
            worker.join() # waits for the worker to finish



class PageProcessor(threading.Thread):
    """Worker for a html page, in order to retrieve the keywords from it and
    score its incoming links"""
    def __init__(self, group=None, target=None, name=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)

        logging_instance = kwargs.get('logging_instance')
        self.logging = bool(logging_instance)
        if self.logging:
            self.__logger_instance = logging_instance


    def get_header_keywords(self, page):
        """Looks for keywords in the page meta tag, and returns them"""
        keyword_re = re.compile(r'<meta\sname=[\'|"]keywords[\'|"]\s' 
                                + r'content=[\'|"](.*?)[\'|"].*>')
        raw_keywords = keyword_re.findall(page)
        keywords = []
        for content in raw_keywords:
            keywords.extend(content.split(', '))

        if (keywords.__len__() == 0 or keywords.__len__() > 0 and keywords[0] == 'None'):
            return None

        return keywords


    def remove_tags(self, html_page):
        """Removes all the tags in the html page"""
        pass


    def add_links(self, html_page, base_url):
        """Searches the anchors in a html page, and recreates them using the
        current location given as parameter."""
        anchor_re = re.compile(r'<a\s*href=[\'|"](.*?)[\'|"].*>')
        links = anchor_re.findall(html_page)

        splitted_base = urlparse.urlparse(base_url)

        new_links = []

        for link in links:
            url_type,_ = mimetypes.guess_type(link)
            
            if (url_type != None and not url_type.__contains__('text')):
                # url points to a file containing something else than text (can
                # be pictures, PDF files etc.)
                if self.logging:
                    self.__logger_instance.log_short_message("""Removed url %s
containing a file of type %s""" % (link, url_type))
                continue
            
            if (link.startswith('/')):
                # add the root, the link is local
                link = urlparse.urljoin(splitted_base.scheme + '://' +
                                        splitted_base.netloc, link)
            elif (link.startswith('#')):
                # add where we are, the link is internal
                link = urlparse.urljoin(base_url, link)
            elif (not link.startswith('http')):
                # huh ?
                link = urlparse.urljoin(base_url, link)

            if (not link.startswith('http')):
                # link has not the good protocol
                continue

            new_links.append(link)
            url_to_visit.put(link)


        return new_links


    def run(self):
        try:
            # gets a page from the queue
            url, html = html_pool.get_nowait()

            # runs only 
            if (url != None and html != None):
                links = self.add_links(html, url)
                keywords = self.get_header_keywords(html)
        except Empty:
            pass



if __name__ == '__main__':
    if (sys.argv.__len__() < 2):
        print 'Enter entry point url as argument'
        sys.exit(1)
    base_url = sys.argv[1]
    crawler = Crawler(base_url, True)
    crawler.crawl()

