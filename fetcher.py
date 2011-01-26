#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs
import datetime
import logging
import math
import mimetypes
import nltk
import os
from Queue import Queue, Empty
import re
import robotparser
import sys
import threading
import time
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import urlparse

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
    _keywords = []


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

        # Initiates _keywords. If there is a recurrent keyword, we put it
        # only once
        for word in keyword:
            if not self._keywords.__contains__(word):
                keywords += word


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
        except HTTPError, he:
            logging.getLogger('fetcher.Crawler').warning('While fetching\
 %s caught HTTPError %d' % (url, he.code))
        except URLError, ex:
            logging.getLogger('fetcher.Crawler').warning('While fetching\
 %s caught URLError %s' % (url, ex.reason))

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

            html_pool.put((current_url, page)) # put the page in the pool

            self._url_visited.append(current_url)

            # start here a new PageProcessor thread
            worker = PageProcessor(name=current_url,theme=self._keywords)
            self._page_workers.append(worker)
            worker.start()

        # end of execution
        for worker in self._page_workers:
            # waits for all threads to finish
            if (worker.is_alive()):
                logging.getLogger('fetcher.Crawler').info('Worker\
 %s is still alive' % worker.name)
            worker.join() # waits for the worker to finish

        logging.getLogger('fetcher.Crawler').info('############')
        logging.getLogger('fetcher.Crawler').info('Crawler ended normally,\
 after %ss of execution' % str(datetime.datetime.now() - self.starttime))



class PageProcessor(threading.Thread):
    """Worker for a html page, in order to retrieve the keywords from it and
    score its incoming links"""

    _theme = []
    _df_dict = {}


    def __init__(self, group=None, target=None, name=None, theme=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        self._theme=theme


    def get_header_keywords(self, page):
        """Looks for keywords in the page meta tag, and returns them"""
        keyword_re = re.compile(r'<meta\sname=[\'|"]keywords[\'|"]\s' 
                                + r'content=[\'|"](.*?)[\'|"].*>')
        raw_keywords = keyword_re.findall(page)
        keywords = []
        for content in raw_keywords:
            keywords.extend(content.split(', '))

        if (keywords.__len__() == 0 or 
            keywords.__len__() > 0 and keywords[0] == 'None'):
            return None

        logging.getLogger('fetcher.PageProcessor').info('Found in the\
 header %s ' % keywords)

        return keywords


    def remove_tags(self, html_page):
        """Removes all the tags in the html page"""
        cleaned_page = nltk.clean_html(html_page)
        return cleaned_page


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
                logging.getLogger('fetcher.PageProcessor').info(\
 'Removed url %s containing a file of type %s' % (link, url_type))
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
            logging.getLogger('fetcher.PageProcessor').info(\
 'Added %s to queue' % link)


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

    
    def calculate_score(self,html_page):
        """Calculates the similarity of the web page to the theme. It uses the
        cosinus formula of the vectorial model"""

        # We get all the words in the page, converted into lower case
        tokens = [x.lower() for x in
                  nltk.word_tokenize(nltk.clean_html(html_page))]

        inner_product = 0
        page_vector_norm = 0
        page_length = len(tokens)
        theme_length = len(self._theme)

        # We loop through each word of the theme and modify the vector of the
        # current page. We also do the inner product and norm step by step
        for word in self._theme:
            tf = float(tokens.count(word))/page_length

            if tf>0:
                # If the keyword has already been found, we increment its idf.
                # Otherwise an exception is raised and we initialize it
                try:
                    self._df_dict[word] += 1
                except KeyError:
                    self._df_dict[word] = 1

                df = self._df_dict[word]
                idf = 1./df
                weight = tf*idf

                inner_product += weight / theme_length
                page_vector_norm += (tf * idf)**2


        page_vector_norm = math.sqrt(page_vector_norm)


        # Classic similarity formula. Cosinus angle between our page
        # vector and the theme vector (filled with 1/len(theme))
        score = float(inner_product) / (page_vector_norm * 1./math.sqrt(theme_length))

        return score
            




        page_vector = []

        score = 0  

        for word in self._theme:
            tf = tokens.count(word)

            # Lets update the df of the current word. If its the first time we
            # find it, an excecption is raised and the word is added in the
            # df_table

            if tf>0:
                try:
                    self._df_dict[word] += 1
                except KeyError:
                    self._df_dict[word] = 1

                df = self._df_dict[word]
                idf = 1./df
                score += tf*idf

        return score



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
    crawler = Crawler(base_url=start_url, log=True, keywords=keywords)
    crawler.crawl()

