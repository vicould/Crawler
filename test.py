#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import unittest
from Queue import Empty

from fetcher import Crawler, PageProcessor


class CrawlerTest(unittest.TestCase):
    def setUp(self):
        self.first_links = ['http://localhost/']
        self.crawler = Crawler(self.first_links)


    def test_initial_link(self):
        links = []
        result_queue = self.crawler.get_links_to_visit()
        try:
            while True:
                links.append(result_queue.get_nowait())
        except Empty:
            pass

        self.assertEqual(links, self.first_links)


    def test_protocol_failure(self):
        self.assertRaises(SystemExit, Crawler, 'ftp://localhost')



class PageProcessor_test(unittest.TestCase):
    def setUp(self):
        self.parser = PageProcessor()


    def test_keyword(self):
        test_page = '<html><head><meta name="keywords" content="test, bla,\
 python" /></head></html>'
        keywords,_,_,_ = self.parser._parse('http://localhost', test_page)
        self.assertEqual(keywords, ['test', 'bla', 'python'])


    def test_none_keyword(self):
        test_page = '<html><head><meta name="keywords"\
 content="None" /></head></html>'
        keywords,_,_,_ = self.parser._parse('http://localhost', test_page)
        self.assertEqual(keywords, [])


    def test_link(self):
        test_page = u'<html><head><title>Test</title></head><body><a href="/local" />\
 </body></html>'
        _,_,links,_ = self.parser._parse('http://localhost', test_page)
        self.assertEqual(links, ['/local'])



if __name__ == '__main__':
    unittest.main()
