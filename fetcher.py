#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs
import datetime
import logging
import mimetypes
import nltk
import os
from Queue import Queue, Empty
import re
import robotparser
import sys
import threading
from threading import local
import time
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import urlparse
import xml.parsers.expat
from xml.parsers.expat import ExpatError

# local modules
import logger


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
    _user_agent = 'DummyCrawler'
    _headers = { 'User_Agent' : _user_agent }
    _url_visited = []
    _current_root = ''
    _page_workers = []


    def __init__(self, base_url, log=False, keywords=None):
        """Init the crawler with the base url of the indexing. It also sets the
        gentle robot directives parser, in order to start crawling directly
        after the initialization."""
        self.starttime = datetime.datetime.now()
        self.log = log
        self.__init_logger()
        logging.getLogger('fetcher.Crawler').info('Starting crawler')

        for url in base_url:
            url_to_visit.put(url) # start url
            logging.getLogger('fetcher.Crawler').info(url)

        # cuts the url in standard parts
        split_url = urlparse.urlparse(base_url[0])
        if (not split_url.scheme.startswith('http')):
            logging.getLogger('fetcher.Crawler').critical('This crawler\
 only supports the http and https protocol, exiting')
            sys.exit(1)

        # _rp is the nice robot taking care of the webmaster directives
        self._rp = robotparser.RobotFileParser()

        # sets the current domain, and calls the robot initialization function
        self._current_root = split_url.scheme + '://'\
                + split_url.netloc + '/'
        new_rules = self.change_domain(self._current_root)
        logging.getLogger('fetcher.Crawler').info('End of initialization')
        logging.getLogger('fetcher.Crawler').info('############')


    def __init_logger(self):
        """Inits the logger used internally, calling a few utilities to handle
        events, write them properly etc.
        Should be called at the beginning of the constructor, logger is used
        widely if activated."""
        try:
            # just preventing from further call
            if (self._logger_initialized):
                pass
        except AttributeError:
            # attribute does not exist, configuring the logger
            if (not self.log):
                logging.basicConfig()
                logger_inst = logging.getLogger('fetcher')
                dh = logger.NullHandler()
                logger_inst.addHandler(dh) # adds the dummy handler, doing nothing
            else:
                # tests if the log folder exists
                try:
                    os.listdir(os.path.join(os.getcwd(), 'log'))
                except OSError, err:
                    if err.errno == 2:
                        os.mkdir('log', 0755)
                        print 'Created log dir with mode 755'

                name = ''.join(['log/', '_'.join(['crawler', \
datetime.datetime.now().strftime('%m-%d_%H-%M')]), '.log'])
                logging.basicConfig(level=logging.DEBUG, filename=name,\
                                    format='%(asctime)s %(name)s %(levelname)s\
 %(message)s', datefmt='%m.%d %H:%M:%S', filemode='w')

            self._logger_initialized = True


    def change_domain(self, domain):
        """Function to retrieve the content of the robots rules for the domain
        given as parameter. Returns the new rules as stream."""
        robots_url = urlparse.urljoin(domain, 'robots.txt')
        try:
            self._rp.set_url(urlparse.urljoin(domain, 'robots.txt'))
            self._rp.read() # parses the content of the directives
            # the rules are now in memory, we could stop here
            rules = urllib2.urlopen(robots_url).readlines()

            logging.getLogger('fetcher.Crawler').info('New rules found\
on %s' % domain)
            for rule in rules:
                logging.getLogger('fetcher.Crawler').\
info(''.join(['    ', rule[:rule.__len__()-1]]))

            # returns the content of the file for logging purpose
            return rules

        except HTTPError as e:
            logging.getLogger('fetcher.Crawler').warning('Could not\
 get robots on %s, %s' % (domain, e.code))
        except URLError, e:
            logging.getLogger('fetcher.Crawler').warning('Could not\
 get robots on %s, %s' % (domain, e.reason))


    def fetch_page(self, url):
        """Fetches the url given as input and returns the page. Returns an
        empty string when an exception occured."""

        html = ''
        try:
            # builds the request
            req = urllib2.Request(url, headers=self._headers)

            # opens the page
            response = urllib2.urlopen(req)
            # tests the MIME type of the page, crawling on non html documents
            # is not really useful.
            if (response.info().gettype() == 'text/html'):
                html = response.read()
                logging.getLogger('fetcher.Crawler').info('Page fetched')
        except HTTPError, he:
            logging.getLogger('fetcher.Crawler').warning('While fetching\
 caught HTTPError %s' % he.code)
        except URLError, ex:
            logging.getLogger('fetcher.Crawler').warning('While fetching\
 caught URLError %s' % ex.reason)

        return html


    def get_visited_links(self):
        return self._url_visited


    def get_links_to_visit(self):
        return url_to_visit


    def crawl(self):
        """Call this if you want the crawler to do all his stuff without
        you."""
        i = 0
        # limiting the trip of the crawler
        while (i < 10):
            time.sleep(1) # waits 1s at each step
            i += 1

            # takes one url from the queue
            current_url = url_to_visit.get()

            if (current_url in self._url_visited):
                # url was already visited once
                i -= 1
                logging.getLogger('fetcher.Crawler').info('%s has already\
 been visited at least once' % current_url)
                continue

            logging.getLogger('fetcher.Crawler').info('%s is now current' %
                                                      current_url)

            split_url = urlparse.urlparse(current_url)
            new_root = split_url.scheme + '://' + split_url.netloc + '/'

            # domain is changing, we need to fetch the robots directives from
            # the new domain
            if (new_root != self._current_root):
                self._current_root = new_root
                new_rules = self.change_domain(self._current_root)
                logging.getLogger('fetcher.Crawler').info('Changing domain\
 to %s' % new_root)

            # checks the url against the robots.txt directives
            if (not self._rp.can_fetch(self._user_agent, current_url)): 
                logging.getLogger('fetcher.Crawler').info('Robot non\
 authorized on %s' % current_url)
                continue

            page = self.fetch_page(current_url)
	    
            if (page == ''): # page is empty, no need to do anything with it
                continue

            # feeds the pool with data, in order to make the processors work
            html_pool.put((current_url, page))
            self._url_visited.append(current_url)

            url_to_visit.task_done()

        # end of execution
        if (not html_pool.empty()):
            logging.getLogger('fetcher.Crawler').info('Waiting for processors\
to finish their work')
            html_pool.join()

        logging.getLogger('fetcher.Crawler').info('############')
        logging.getLogger('fetcher.Crawler').info('Crawler ended normally,\
 after %ss of execution' % str(datetime.datetime.now() - self.starttime))



class PageProcessor(threading.Thread):
    """Worker for a html page, in order to retrieve the keywords from it and
    score its incoming links"""
    def __init__(self, group=None, target=None, name=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        self._my_data = local()


    def _rebuild_link(self, link):
        url_type,_ = mimetypes.guess_type(link)

        if (url_type != None and not url_type.__contains__('text')):
            # url points to a file containing something else than text (can
            # be pictures, PDF files etc.)
            logging.getLogger('fetcher.CrawlerHTMLParser').info(\
'Removed url %s containing a file of type %s' % (link, url_type))
            return ''

        if (link.startswith('/')):
            # adds the root, the link is local but absolute
            link = urlparse.urljoin(self._my_data.splitted_url.scheme + '://' +
                                    self._my_data.splitted_url.netloc, link)
        elif (link.startswith('#')):
            # adds where we are, the link is internal
            link = urlparse.urljoin(self._my_data.base_url, link)
        elif (not link.startswith('http')):
            # links points from here
            link = urlparse.urljoin(self._my_data.base_url, link)

        if (not link.startswith('http')):
            # link has not the good protocol
            return ''

        logging.getLogger('fetcher.CrawlerHTMLParser').info('Added %s to queue'
                                                            % link)
        url_to_visit.put(link)
        return link


    def _handle_start_element(self, name, attrs):
        if (name == 'a'):
            # link
            self._my_data.is_anchor = True
            self._my_data.anchor_data = ''
            try:
                link = attrs['href']
                self._my_data.current_link = self._rebuild_link(link)
                # we'll be storing later a tuple of anchors and corresponding link
                self._my_data.links_list.append(link)
            except KeyError:
                logging.getLogger('fetcher.CrawlerHTMLParser').warning('Whut ?\
 anchor without any link ?')

        if (name == 'meta'):
            try:
                if (attrs.get('name') == 'keywords'):
                    self._my_data.keywords = attrs['content'].split(', ')
                    if ('None' in self._my_data.keywords and
                        self._my_data.keywords.__len__() == 1):
                        # none keyword, should not be added
                        self._my_data.keywords = []
                    else:
                        logging.getLogger('fetcher.CrawlerHTMLParser').info(\
'Found %s in the header' % self._my_data.keywords)
            except KeyError:
                pass


    def _handle_end_element(self, name):
        if (name == 'a'):
            self._my_data.is_anchor = False
            self._my_data.anchors_list.append((self._my_data.current_link, self._my_data.anchor_data))


    def _handle_data(self, data):
        if (self._my_data.is_anchor):
            # we are in the middle of an anchor, save the data
            ''.join([self._my_data.anchor_data, data])
        self._my_data.text_content = ''.join([self._my_data.text_content, data])


    def _parse(self, base_url, html_page):
        """Parses an html page and returns a huge data_structure:
            * a tuple containing as first item the keywords found in the header
            of the page inside the meta name="keywords" element
            * the list of anchors found in the page (in fact a list of tuple
            with the link as first value and the anchor's data in the
            second position)
            * the list of the links found in the page
            * the content of the page without the html tags.
            """
        self._my_data.base_url = base_url
        self._my_data.splitted_url = urlparse.urlparse(base_url)
        self._my_data.is_anchor = False
        self._my_data.anchors_list = []
        self._my_data.links_list = []
        self._my_data.text_content = ''
        self._my_data.keywords = []

        self._parser = xml.parsers.expat.ParserCreate()
        self._parser.StartElementHandler = self._handle_start_element
        self._parser.EndElementHandler = self._handle_end_element
        self._parser.CharacterDataHandler = self._handle_data
        
        for line in html_page.splitlines(True):
            try:
                self._parser.Parse(line)
                self._parser.Parse('', True)
            except ExpatError as e:
                logging.getLogger('fetcher.PageProcessor').warn('ExpatError %d\
 line %d colon %d in %s' % (e.code, e.lineno, e.offset, base_url))
        # last call to the parser as requested by the doc
            
        return (self._my_data.keywords, self._my_data.anchors_list,
                self._my_data.links_list, self._my_data.text_content)


    def run(self):
        try:
            while True:
                # gets a page from the queue
                url, html = html_pool.get()

                # runs only 
                if (url != None and html != None):
                   self._parse(url, html) 

                html_pool.task_done()

        except Empty:
            pass

    

if __name__ == '__main__':
    if (sys.argv.__len__() > 1):
        start_url = sys.argv[1:]
        keywords = None
    else:
        print 'Welcome to the dummy python crawler.'
        try:
            keywords = raw_input('Enter keywords for the crawler\n--> ')
            while True:
                start_url = raw_input('Enter start urls seperated by\
    commas\n--> ')
                if (start_url.__len__() > 0):
                    break
                print 'Please enter an url'
        except EOFError:
            print '\nCaught EOF, exiting'
            sys.exit(1)
        start_url = start_url.split(',')
    for i in range(5):
        p = PageProcessor()
        p.daemon = True
        p.start()

    crawler = Crawler(base_url=start_url, log=True, keywords=keywords)
    crawler.crawl()

