#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import unittest

from logger import Logger
from fetcher import Crawler


class FetcherTest(unittest.TestCase):
    def setUp(self):
        self.first_link = 'http://localhost/'
        self.crawler = Crawler(self.first_link)

    def test_initial_link(self):
        self.assertEqual(self.crawler.get_links_to_visit(), [self.first_link])

    def test_keywords(self):
        test_page = '<meta name="keywords" content="python, crawler, test" />'
        self.assertEqual(self.crawler.get_keywords(test_page), 
                         ['python, crawler, test'])




class LoggerTest(unittest.TestCase):


    def setUp(self):
        self.header = 'header\n'
        self.filename = ''.join(['_'.join(['prefix',
                                           datetime.now().strftime('%m-%d_%H-%M')]),
                                 '.log'])
        self.logger = Logger('prefix', self.header)


    def test_prefix(self):
        self.assertTrue(os.listdir(os.path.join(os.getcwd(),
                                                'log')).__contains__(self.filename))


    def test_header(self):
        log_file = open(''.join(['log/', self.filename]))
        self.assertTrue(log_file.readline(), self.header)
        log_file.close()



if __name__ == '__main__':
    unittest.main()
