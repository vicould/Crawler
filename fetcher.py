#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs
import datetime
import HTMLParser
from HTMLParser import HTMLParseError
import logging
import math
import mimetools
import mimetypes
import nltk
import optparse
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

# local modules
from data_utils import SortedQueue
import logger
from persistance import DataPersistance, result_pool
from ranking import PageRank
from ranking import page_rank_queue


url_to_visit = SortedQueue()
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


    def __init__(self, *args, **kwargs):
        """Init the crawler with the base url of the indexing. It also sets the
        gentle robot directives parser, in order to start crawling directly
        after the initialization."""
        self.starttime = datetime.datetime.now()
        self.log = kwargs.get('log', False)
        self._iterations = kwargs.get('iterations', 15)
        self._init_logger()
        logging.getLogger('fetcher.Crawler').info('Starting crawler')

        base_url = kwargs['base_url']

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


    def _init_logger(self):
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
        while i < self._iterations:
            time.sleep(1) # waits 1s at each step

            # takes one url from the queue, with a timeout of 5 seconds
            try:
                current_url = url_to_visit.get(timeout=5)
            except Empty:
                logging.getLogger('fetcher.Crawler').critical('Not enough\
 links in the pool, exiting crawling after having waited for 5 seconds')
                break

            if (current_url in self._url_visited):
                # url was already visited once
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

            print("Fetching page n° %i. URL: %s" % (i+1,current_url))

            page = self.fetch_page(current_url)

            if (page == ''): # page is empty, no need to do anything with it
                continue

            # feeds the pool with data, in order to make the processors work
            logging.getLogger('fetcher.Crawler').info('Added %s to pool' %
                                                     current_url)
            html_pool.put((current_url, page))
            self._url_visited.append(current_url)

            url_to_visit.task_done()
            i += 1

        # end of execution
        if (not html_pool.empty()):
            logging.getLogger('fetcher.Crawler').info('Waiting for processors\
to finish their work')
            html_pool.join()

        logging.getLogger('fetcher.Crawler').info('############')
        logging.getLogger('fetcher.Crawler').info('Crawler ended normally,\
 after %ss of execution' % str(datetime.datetime.now() - self.starttime))



##### FETCHER END ######


class PageProcessor(threading.Thread):
    """Worker for a html page, in order to retrieve the keywords from it and
    score its incoming links"""

    _theme = []
    _df_dict = {}


    def __init__(self, group=None, target=None, name=None, theme=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        self._theme=theme
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


    def _handle_start_element(self, name, attrs, startend=False):
        if name == 'script':
            self._my_data.script = True
            return
        elif self._my_data.script:
            return
        elif (name == 'a'):
            # link
            for attr, value in attrs:
                if attr == "href":
                    self._my_data.is_anchor = not startend
                    self._my_data.anchor_data = ''
                    link = value
                    self._my_data.current_link = self._rebuild_link(link)
                    # we'll be storing later a tuple of anchors and
                    # corresponding link
                    self._my_data.links_list.append(self._my_data.current_link)
                    break

        elif (name == 'meta'):
            keyword = False
            for attr, value in attrs:
                if (value == "keywords"):
                    keyword = True
                elif (keyword and attr == 'content'):
                    self._my_data.header_keywords = value.split(', ')
                    if ('None' in self._my_data.header_keywords and
                        self._my_data.header_keywords.__len__() == 1):
                        # none keyword, should not be added
                        self._my_data.header_keywords = []
                    else:
                        logging.getLogger('fetcher.CrawlerHTMLParser').info(\
'Found %s in the header' % self._my_data.header_keywords)
                    break


    def _handle_startend_element(self, name, attrs):
        self._handle_start_element(name, attrs, True)


    def _handle_end_element(self, name):
        if name == 'script':
            self._my_data.script = False
            return
        elif self._my_data.script:
            return
        elif (self._my_data.is_anchor and name == 'a'):
            self._my_data.is_anchor = False
            # stores the content of the anchor in the local variable
            self._my_data.anchors_list.append((self._my_data.current_link,
                                               self._my_data.anchor_data))


    def _handle_data(self, data):
        if (self._my_data.is_anchor):
            # we are in the middle of an anchor, save the data
            self._my_data.anchor_data = \
                    ''.join([self._my_data.anchor_data, data.lower()])
            # string is converted to lowercase, easier to look for
        self._my_data.text_content =\
                ''.join([self._my_data.text_content, data])


    def _parse(self, base_url, html_page):
        """Parses an html page and returns a huge data_structure, which is a
        dictionary:
            * a tuple containing as first item the header_keywords found in the
            header of the page inside the meta name="keywords" element
            * the list of anchors found in the page (in fact a list of tuple
            with the link as first value and the anchor's data in the
            second position)
            * the list of the links found in the page
            * the content of the page without the html tags.
        The keys in this dictionary after this call are url, keywords, anchors,
        links and text_content """
        self._my_data.base_url = base_url
        self._my_data.splitted_url = urlparse.urlparse(base_url)
        self._my_data.is_anchor = False
        self._my_data.anchors_list = []
        self._my_data.links_list = []
        self._my_data.text_content = ''
        self._my_data.header_keywords = []
        self._my_data.script = False

        # it is necessary to create a new instance of the parser each time,
        # no choice.

        self._parser = HTMLParser.HTMLParser()
        self._parser.handle_starttag = self._handle_start_element
        self._parser.handle_startendtag = self._handle_startend_element
        self._parser.handle_endtag = self._handle_end_element
        self._parser.handle_data = self._handle_data

        error = 0
        for line in html_page.splitlines(True):
            try:
                self._parser.feed(line)
            except HTMLParseError as e:
                error += 1
                logging.getLogger('fetcher.PageProcessor').warn('HTMLParseError\
 %s line %d colon %d in %s' % (e.msg, e.lineno, e.offset, base_url))
                if error == 30:
                    logging.getLogger('fetcher.PageProcessor').warn('Stopping\
 here for this page, too many errors')
                    break
            except UnicodeDecodeError as e:
                logging.getLogger('fetcher.PageProcessor').warn('UnicodeDecode\
Error %s' % e.reason)
                self._parser.reset()
                break
        # last call to the parser as requested by the doc
        try:
            self._parser.close()
        except HTMLParseError as e:
            logging.getLogger('fetcher.PageProcessor').warn('HTMLParseError %s\
line %d colon %d in %s' % (e.msg, e.lineno, e.offset, base_url))

        logging.getLogger('fetcher.PageProcessor').info('Page %s processed' %
                                                        base_url)


        # adds links list to page rank container, in the form of the tuple
        # (base_url, targets)
        page_rank_queue.put((base_url, self._my_data.links_list))

        return {'url' : base_url, 'keywords' : self._my_data.header_keywords,
                'anchors' : self._my_data.anchors_list,
                'links' : self._my_data.links_list,
                'text_content' : self._my_data.text_content}


    def calculate_score(self,tmp_result):
        """Calculates the similarity of the web page to the theme. It uses the
        cosinus formula of the vectorial model"""

        # We get all the words in the page, converted into lower case
        tokens = [x.lower() for x in  tmp_result['text_content'].split()]

        inner_product = 0
        page_vector_norm = 0
        theme_length = len(self._theme)

        # We loop through each word of the theme and modify the vector of the
        # current page. We also do the inner product and norm step by step
        for word in self._theme:
            tf = tokens.count(word)

            if tf>0:
                # If the keyword has already been found, we increment its df.
                # Otherwise an exception is raised and we initialize it
                try:
                    self._df_dict[word] += 1
                except KeyError:
                    self._df_dict[word] = 1

                tmp_result['keywords_found']+=[word]

                df = self._df_dict[word]
                idf = 1./df
                weight = tf*idf

                inner_product += weight / theme_length
                page_vector_norm += (tf * idf)**2


        page_vector_norm = math.sqrt(page_vector_norm)

        if page_vector_norm == 0:
            score = 0
            logging.getLogger("fetcher.PageProcessor").info("No keywords\
found on this page: %s" % self._my_data.base_url)

        else:
            # Classic similarity formula. Cosinus angle between our page
            # vector and the theme vector (filled with 1/len(theme))
            score = float(inner_product) / (page_vector_norm * 1./math.sqrt(theme_length))

        return score


    def run(self):
        try:
            while True:
                # gets a page from the queue
                url, html = html_pool.get()

                # runs only
                if (url != None and html != None):
                    tmp_result = self._parse(url, html)

                    tmp_result['keywords_found'] = []

                    # add here the call to the score method, and add the result in
                    # the tmp_result using put
                    keywords = tmp_result['keywords']
                    score = self.calculate_score(tmp_result)

                    for x in keywords:
                        if (self._theme.__contains__(x)):
                            score += (1-score)*0.1

                    print("%s a pour score %f" % (url,score))

                    if (score > 0.4):
                        tmp_result["score"]=score
                        result_pool.put(tmp_result)

                # tells to the pool that we finished working on the element,
                # because the number of tasks is analysed to wait before
                # shutting down the script
                html_pool.task_done()

        except Empty:
            pass



def main(args):
    kwargs = {'log':True}
    if (args.__len__() > 1):
        usage_str = u'usage: %prog [options] -u URL -t THEME'
        description_str = u'This is a dummy thematic crawler written in Python,\
 using threads to process each page collected and to write down the results.\n\
Written by Nicolas Bontoux and Ludovic Delaveau for the aspects avancés du\
web crawler project.'
        parser = optparse.OptionParser(description=description_str,
                                      usage=usage_str)

        parser.add_option('-u', '--url', dest='base_url', help='start crawling\
 using this URL', metavar='URL')
        parser.add_option('-t', '--theme', dest='theme', help='sets the THEME\
 for the crawler', metavar='THEME')
        parser.add_option('-n', '--iterations', type='int', dest='iterations',
                          help='do only I iterations', metavar='I', default=10)

        (options, args) = parser.parse_args()
        try:
            kwargs['base_url'] = options.base_url.split(',')
            kwargs['theme'] = options.theme
        except AttributeError:
            parser.error('theme and url arguments required')
            parser.print_help()

        kwargs['iterations'] = options.iterations

    else:
        options = {}
        print 'Welcome to the dummy python crawler.'
        try:
            while True:
                theme = raw_input('Enter keywords (theme) for the crawler \
(separated by commas)\n--> ')
                if (theme.__len__() > 0):
                        break
                print 'Please enter keywords (theme)'

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
        kwargs['theme'] = theme
        kwargs['base_url'] = start_url

    theme = kwargs['theme']
    theme = [x.lower() for x in theme.split(',')]
    # To avoid duplicates
    theme = list(set(theme))

    kwargs['theme'] = theme

    for i in range(5):
        p = PageProcessor(theme=theme)
        p.daemon = True
        p.start()

    # crawls !
    crawler = Crawler(**kwargs)
    crawler.crawl()

    # computest page rank scores for the 10 best pages
    pr = PageRank()
    top10 = pr.get_top10()

    # dumps results
    pers = DataPersistance()
    pers.launch_dump(top10)



if __name__ == '__main__':
   main(sys.argv)
