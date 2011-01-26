#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import unittest
from Queue import Empty

from fetcher import Crawler, PageProcessor
from data_utils import SortedQueue


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
        self.assertRaises(SystemExit, Crawler, ['ftp://localhost'])



class PageProcessor_test(unittest.TestCase):
    def setUp(self):
        self.parser = PageProcessor()
        self.parser._theme = ['lorem', 'ipsum']
        self.parser._my_data.base_url = "http://www.test.fr"


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


    def test_calculate_score(self):
        test_page = '<html><body><p>Lorem Ipsum</p></body></html>'
        self.assertEqual(self.parser.calculate_score(test_page),1)

    def test_calculate_score2(self):
        test_page = '<html><body><p>Georges Brassens</p></body></html>'
        self.assertEqual(self.parser.calculate_score(test_page),0)


class SortedQueue_test(unittest.TestCase):
    def setUp(self):
        self.sorted_queue = SortedQueue()


    def test_put_in_sorted_queue(self):
        self.sorted_queue.put('obj')
        self.assertEqual(self.sorted_queue.get(), 'obj')


    # write a test to check that the elements are really sorted in the
    # structure
    def test_queue_is_sorted(self):
        values = ['Purus', 'Ridiculus', 'Fermentum', 'Euismod', 'Sem', 'Purus',
                 'Purus', 'Sem', 'Ridiculus', 'Sem', 'Sem', 'Sem']
        values_ordered = ['Fermentum', 'Euismod', 'Purus', 'Sem']
        for item in values:
            self.sorted_queue.put(item)
        
        sorted_values = []
        while True:
            try:
                print self.sorted_queue.qsize()
                sorted_values.append(self.sorted_queue.get_nowait())
            except Empty:
                break

        self.assertEqual(sorted_values, values_ordered)

    

if __name__ == '__main__':
    unittest.main()
