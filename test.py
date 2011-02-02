#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import unittest
from Queue import Empty

from fetcher import Crawler, PageProcessor
from data_utils import SortedQueue, SynchronizedDict


class CrawlerTest(unittest.TestCase):
    def setUp(self):
        self.first_links = ['http://localhost/']
        self.crawler = Crawler(base_url=self.first_links)


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
        print '\nyou should soon have a CRITICAL log message'
        self.assertRaises(SystemExit, Crawler, base_url=['ftp://localhost'])



class PageProcessor_test(unittest.TestCase):
    def setUp(self):
        self.parser = PageProcessor()
        self.parser._theme = ['lorem', 'ipsum']
        self.parser._my_data.base_url = "http://www.test.fr"


    def test_keyword(self):
        test_page = '<html><head><meta name="keywords" content="test, bla,\
 python" /></head></html>'
        keywords = self.parser._parse('http://localhost',
                                      test_page)['keywords']
        self.assertEqual(keywords, ['test', 'bla', 'python'])


    def test_none_keyword(self):
        test_page = '<html><head><meta name="keywords"\
 content="None" /></head></html>'
        keywords = self.parser._parse('http://localhost',
                                      test_page)['keywords']
        self.assertEqual(keywords, [])


    def test_link(self):
        test_page = u'<html><head><title>Test</title></head><body>\
<a href="/local" /></body></html>'
        links = self.parser._parse('http://localhost', test_page)['links']
        self.assertEqual(links, ['/local'])


    def test_calculate_score(self):
        test_page = '<html><body><p>Lorem Ipsum</p></body></html>'
        self.parser._parse('http://localhost', test_page)
        self.assertEqual(self.parser.calculate_score(test_page),1)

    def test_calculate_score2(self):
        test_page = '<html><body><p>Georges Brassens</p></body></html>'
        self.parser._parse('http://localhost', test_page)
        self.assertEqual(self.parser.calculate_score(test_page),0)


    def test_data(self):
        test_page = '<html><body><p>Georges Brassens</p></body></html>'
        text_content = \
self.parser._parse('http://localhost', test_page)['text_content']
        self.assertEqual(text_content, 'Georges Brassens')


    def test_anchor(self):
        test_page = u'<html><head><title>Test</title></head><body>\
<a href="/local">Bouh</a></body></html>'
        link, anchor = self.parser._parse('http://localhost',
                                          test_page)['anchors'][0]
        self.assertEqual(anchor, 'bouh')


    def test_script(self):
        test_page = u'<html><head><title>Test</title></head><body>\
<script>LFDKNG</script><a href="/local">Bouh</a></body></html>'
        link, anchor = self.parser._parse('http://localhost',
                                          test_page)['anchors'][0]
        self.assertEqual(anchor, 'bouh')



class SortedQueue_test(unittest.TestCase):
    def setUp(self):
        self.sorted_queue = SortedQueue()


    def test_put(self):
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
                sorted_values.append(self.sorted_queue.get_nowait())
            except Empty:
                break

        self.assertEqual(sorted_values, values_ordered)



class SynchronizedDict_test(unittest.TestCase):
    def setUp(self):
        self.dict_inst = SynchronizedDict()


    def test_put(self):
        self.dict_inst.put('Babar', 'éléphant')
        self.assertEqual(self.dict_inst.get(), ('Babar', ['éléphant']))

    def test_add(self):
        self.dict_inst.put('Babar', 'éléphant')
        self.dict_inst.add_item_to_key('Babar', 'roi')
        self.assertEqual(self.dict_inst.get(), ('Babar', ['éléphant', 'roi']))

    def test_get_key(self):
        self.dict_inst.put('Babar', 'éléphant')
        self.dict_inst.put('Céleste', 'femme de babar')
        self.assertEqual(self.dict_inst.get_with_key('Céleste'),
                                                 ['femme de babar'])


    def test_replace(self):
        self.dict_inst.put('Babar', 'éléphant')
        self.dict_inst.put('Babar', 'roi')
        self.assertEqual(self.dict_inst.get(), ('Babar', ['roi']))


    def test_add_failed(self):
        self.assertRaises(KeyError, self.dict_inst.add_item_to_key, 1, 2)


    def test_get_failed(self):
        self.dict_inst.put(2, 3)
        self.assertRaises(KeyError, self.dict_inst.get_with_key, 1)


    def test_empty_get_nowait(self):
        self.assertRaises(Empty, self.dict_inst.get_nowait)


    def test_empty_get_timeout(self):
        print '\ntesting get from empty dict, probably waiting 2 seconds'
        self.assertRaises(Empty, self.dict_inst.get, timeout=2)


    def test_empty_get_key(self):
        self.assertRaises(Empty, self.dict_inst.get_with_key, 1)


if __name__ == '__main__':
    unittest.main()
