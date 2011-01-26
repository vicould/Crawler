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



class PageProcessorTest(unittest.TestCase):
    def setUp(self):
        self.processor = PageProcessor()
        self.processor._theme = ['Lorem', 'Ipsum']


    def test_keywords(self):
        test_page = '<meta name="keywords" content="python, crawler, test" />'
        self.assertEqual(self.processor.get_header_keywords(test_page), 
                         ['python', 'crawler', 'test'])


    def test_no_keywords(self):
        self.assertEqual(self.processor.get_header_keywords(''), None)

    
    def test_none_keywords(self):
        test_page = '<meta name="keywords" content="None" />'
        self.assertEqual(self.processor.get_header_keywords(test_page), None)


    def test_add_links(self):
        test_page = '<a href="http://www.google.fr"></a>'
        self.assertEqual(self.processor.add_links(test_page, ''),
                         ['http://www.google.fr'])

    def test_add_links_local(self):
        test_page = '<a href="/python"></a>'
        self.assertEqual(self.processor.add_links(test_page,
                                                  'http://localhost/~Ludo/'),
                         ['http://localhost/python'])

    def test_add_links_internal(self):
        test_page = '<a href="#set"></a>'
        self.assertEqual(self.processor.add_links(test_page,
                                                  'http://localhost/~Ludo/python/index.html'),
                         ['http://localhost/~Ludo/python/index.html#set'])


    def test_add_links_relative(self):
        test_page = '<a href="library"></a>'
        self.assertEqual(self.processor.add_links(test_page,
                                                  'http://localhost/~Ludo/python/'),
                         ['http://localhost/~Ludo/python/library'])


    def test_clean_page(self):
        test_page = '<html><body><p>Lorem Ipsum</p></body></html>'
        self.assertEqual(self.processor.remove_tags(test_page), 'Lorem Ipsum')

    

    def test_calculate_score(self):
        test_page = '<html><body><p>Lorem Ipsum pouet</p></body></html>'
        self.assertEqual(self.processor.calculate_score(test_page),2)



if __name__ == '__main__':
    unittest.main()
