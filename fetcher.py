#!/usr/bin/python
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

# modules from the project
import logger

class Crawler:
    """The class responsible for the crawling feature. After initializing the
    class with the first domain to interrogate, you can start the crawler in
    standalone mode by calling the run function.
    Example:
    >>> my_crawler = Crawler('http://www.emse.fr/') # creates the class, with
                                                    # www.emse.fr as base url
    >>> my_crawler.run() # launch the crawler in autonomous mode
    The crawler is width-first, visiting all links from one level before going
    anywhere deeper.
    """
    __user_agent = 'DummyCrawler'
    __headers = { 'User_Agent' : __user_agent }
    __url_to_visit = []
    __url_visited = []
    __current_root = ''


    def __init__(self, base_url):
        """Init the crawler with the base url of the indexing. It also sets the
        gentle robot directives parser, in order to start crawling directly
        after the initialization."""
        self.__url_to_visit.append(base_url) # start url
        self.__logger_instance = logger.Logger('crawler', """Initializing
dummy crawler.\n""") # initializes the logger used to keep track of the event

        # cuts the url in standart parts
        split_url = urlparse.urlparse(base_url)
        if (split_url.scheme != 'http'):
            self.__logger_instance('Exiting', 'sorry this crawler supports'
                                   + 'only the http protocol\n'
                                   + 'Exiting now ...')
            sys.exit(1)

        # __rp is the nice robot taking care of the webmaster directives
        self.__rp = robotparser.RobotFileParser()
        # set the domain of the 
        self.__current_root = split_url.scheme + '://'\
                                        + split_url.netloc + '/'
        self.change_domain(self.__current_root)
        self.__logger_instance.log_short_message('Crawler initialized')


    def change_domain(self, domain):
        """Sets the domain of the current request in order to use the robots
        directives."""
        robots_url = urlparse.urljoin(domain, 'robots.txt')
        try:
            # logs the content of the directives
            self.__logger_instance.log_event('Robots on %s' % domain,
                                             urllib2.urlopen(robots_url))
            self.__rp.set_url(urlparse.urljoin(domain, 'robots.txt'))
            self.__rp.read() # parses the content of the directives
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
        # checks the robots.txt directives
        if (not self.__rp.can_fetch("*", url)): 
            self.__logger_instance.log_event('robot non authorized', [url])
            return ''

        html = ''
        try:
            # builds the request
            values = {}
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data, self.__headers)

            # opens the page
            response = urllib2.urlopen(req)
            # tests the MIME type of the page, crawling on non html documents
            # is not really useful. Maybe it could be checked previously,
            # in order to avoid loading useless files, with the mimetypes
            # module.
            if (response.info().gettype() == 'text/html'):
                html = response.read()
        except HTTPError, he:
            self.__logger_instance.log_event('HTTPError', [str(he.code) + ' ',
                                                      he.read()])
        except URLError, ex:
            self.__logger_instance.log_event('URLError', [str(ex.reason)])
        return html


    def add_links(self, html_page, base_url):
        """Searches the anchors in a html page, and recreates them using the
        current location given as parameter."""
        anchor_re = re.compile(r'<a\s*href=[\'|"](.*?)[\'|"].*>')
        links = anchor_re.findall(html_page)

        if (links.__len__() > 0):
            self.__logger_instance.log_event('New links found', links)
        
        for link in links:
            if (link.startswith('/')):
                # add the root, the link is local
                link = urlparse.urljoin(self.__current_root, link)
            elif (link.startswith('#')):
                # add where we are, the link is internal
                link = urlparse.urljoin(base_url, link)
            elif (not link.startswith('http')):
                # huh ?
                link = urlparse.urljoin(base_url, link)

            # avoids duplicates, and already visited links
            if (link not in self.__url_to_visit and link not in
                self.__url_visited):
                self.__url_to_visit.append(link)


    def get_keywords(self, html_page, base_url):
        """Looks for keywords in the page meta tag"""
        keyword_re = re.compile(r'<meta\sname=[\'|"]keywords[\'|"]\s' 
                   + r'content=[\'|"](.*?)[\'|"].*>')
        keywords = keyword_re.findall(html_page)

        if (keywords.__len__() > 0):
            self.__logger_instance.log_event('New keywords found'
                                             + ' for the current page',
                                             keywords)

    
    def remove_tags(self, html_page):
        """Removes all the tags in the html page"""
        pass


    def run(self):
        """Call this if you want the crawler to do all his stuff without you."""
        i = 0
        # limiting the trip of the crawler
        while (i < 100 and self.__url_to_visit.__len__() > 0):
            time.sleep(1) # waits 1s at each step
            i = i + 1
            # takes the first url to visit
            current_url = self.__url_to_visit.pop(0)
            split_url = urlparse.urlparse(current_url)
            new_root = split_url.scheme + '://' + split_url.netloc + '/'

            # domain is changing, we need to fetch the robots directives from
            # the new domain
            if (new_root != self.__current_root):
                self.__current_root = new_domain
                self.change_domain(self.__current_root)

            page = self.fetch_page(current_url)
            if (page == ''): # page is empty, no need to do anything with it
               continue

            self.__url_visited.append(current_url)
            self.add_links(page, current_url)
            self.get_keywords(page, current_url)



if __name__ == '__main__':
    base_url = sys.argv[1]
    a = Crawler(base_url)
    a.run()

