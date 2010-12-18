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

# modules from the project
import logger

class Crawler:
    __user_agent = 'DummyCrawler'
    __headers = { 'User_Agent' : __user_agent }
    __url_to_visit = []


    def __init__(self, base_url):
        self.__url_to_visit += base_url
        self.__logger_instance = logger.Logger('crawler', """This is a dummy\
 crawler, written by Nicolas\
 Bontoux and Ludovic\
 Delaveau.\nAnd here is a log\
 entry. """)

        o = urlparse.urlparse(base_url)

        if (o.scheme != 'http'):
            self.__logger_instance('Exiting', 'sorry this crawler supports'
                                   + 'only the http protocol\n'
                                   + 'Exiting now ...')
            sys.exit(1)

        self.__rp = robotparser.RobotFileParser()
        self.set_domain(o.scheme + '://' + o.netloc + '/')


    def fetcher(self, url):
        """Fetches the url given as input and returns the page. Returns an empty
        string when an exception occured.
        """

        if (not self.__rp.can_fetch("*", url)):
            return ''

        html = ''
        try:
            values = {}
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data, self.__headers)

            response = urllib2.urlopen(req)
            html = response.read()
        except HTTPError, he:
            print he.code
            print he.read()
        except URLError, ex:
            print ex.reason
        return html


    def get_anchors(self, html_page):
        """Searches the anchors in a html page"""
        anchor_re = re.compile(r'<a\s*href=[\'|"](.*?)[\'|"].*>')
        html = html_page

        links = anchor_re.findall(html)
        print links


    def set_domain(self, domain):
        self.domain  = domain
        robots_url = urlparse.urljoin(domain, 'robots.txt')
        self.__logger_instance.log_event('Robots on %s' % domain,
                                         urllib2.urlopen(robots_url))
        self.__rp.set_url(urlparse.urljoin(domain, 'robots.txt'))
        self.__rp.read()



if __name__ == '__main__':
    base_url = sys.argv[1]
    a = Crawler(base_url)
    a.get_anchors(a.fetcher(base_url))
