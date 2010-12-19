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
    __user_agent = 'DummyCrawler'
    __headers = { 'User_Agent' : __user_agent }
    __url_to_visit = []
    __url_visited = []
    __current_domain = ''


    def __init__(self, base_url):
        """Constructor"""
        self.__url_to_visit.append(base_url) # start url
        self.__logger_instance = logger.Logger('crawler', """This is a dummy\
 crawler, written by Nicolas Bontoux and Ludovic Delaveau.\nAnd here is a log\
 entry. """) # initializes the logger used to keep track of the event

        split_url = urlparse.urlparse(base_url)
        if (split_url.scheme != 'http'):
            self.__logger_instance('Exiting', 'sorry this crawler supports'
                                   + 'only the http protocol\n'
                                   + 'Exiting now ...')
            sys.exit(1)

        # __rp is the nice robot taking care of the webmaster directives
        self.__rp = robotparser.RobotFileParser()
        self.__current_domain = split_url.scheme + '://'\
                                        + split_url.netloc + '/'
        self.set_domain(self.__current_domain)


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
            values = {}
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data, self.__headers)

            response = urllib2.urlopen(req)
            if (response.info().gettype() == 'text/html'):
                html = response.read()
        except HTTPError, he:
            self.__logger_instance.log_event('HTTPError', [str(he.code) + ' ',
                                                      he.read()])
        except URLError, ex:
            self.__logger_instance.log_event('URLError', [str(ex.reason)])
        return html


    def get_anchors(self, html_page, base_url):
        """Searches the anchors in a html page"""
        anchor_re = re.compile(r'<a\s*href=[\'|"](.*?)[\'|"].*>')
        links = anchor_re.findall(html_page)

        if (links.__len__() > 0):
            self.__logger_instance.log_event('New links found', links)
        
        for link in links:
            if (link.startswith('/')):
                link = urlparse.urljoin(self.__current_domain, link)
            elif (link.startswith('#')):
                link = urlparse.urljoin(base_url, link)
            elif (not link.startswith('http')):
                link = urlparse.urljoin(base_url, link)

            if (link not in self.__url_to_visit and link not in
                self.__url_visited):
                self.__url_to_visit.append(link)


    def get_keywords(self, html_page, base_url):
        """Looks for keywords in the page"""
        keyword_re = re.compile(r'<meta\sname=[\'|"]keywords[\'|"]\s' 
                   + r'content=[\'|"](.*?)[\'|"].*>')
        keywords = keyword_re.findall(html_page)

        if (keywords.__len__() > 0):
            self.__logger_instance.log_event('New keywords found'
                                             + ' for the current page',
                                             keywords)


    def set_domain(self, domain):
        """Sets the domain of the current request in order to use the robots
        directives."""
        robots_url = urlparse.urljoin(domain, 'robots.txt')
        try:
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


    def handler(self):
        i = 0
        while (i < 100 and self.__url_to_visit.__len__() > 0):
            i = i + 1
            current_url = self.__url_to_visit.pop(0)
            split_url = urlparse.urlparse(current_url)
            new_domain = split_url.scheme + '://' + split_url.netloc + '/'

            if (new_domain != self.__current_domain):
                self.__current_domain = new_domain
                self.set_domain(self.__current_domain)

            page = self.fetch_page(current_url)
            if (page = ''): # page is empty, no need to do anything with it
               continue

            self.__url_visited.append(current_url)
            self.get_anchors(page, current_url)
            self.get_keywords(page, current_url)


if __name__ == '__main__':
    base_url = sys.argv[1]
    a = Crawler(base_url)
    a.handler()

