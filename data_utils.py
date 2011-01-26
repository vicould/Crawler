#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
from Queue import Queue, Empty
import sqlite3
import threading
from threading import local
import os



class SortedQueue(Queue):
    """Queue storing only unique elements, or incrementing the score when
    duplicates are being put. Therefore, the most important element is
    returned when calling the get method"""
    def _init(self, maxsize):
        self._queue = [] # our queue is a basic list


    def _qsize(self, len=len):
        return len(self._queue)


    def _put(self, item):
        """Organizes the new queue with the element"""
        if len(self._queue) == 0:
            self._queue.append((item, 1))
            return
        i = 0
        item_score = 1
        # could be way better optimized, no time for that now
        for value, score in self._queue:
            if (item == value):
                # adds the score
                item_score += score
                # removes the element from the list
                self._queue.pop(i)
                break
            i += 1

        i = 0
        # tries to find where to put the element
        for value, score in self._queue:
            # next element is more important, stores the value here
            if (item_score <= score):
                self._queue.insert(i, (item, item_score))
                return
            i += 1

    
    def _get(self):
        value = self._queue.pop()[0]
        return value



class data_persistance:
    """Class to write down the datas collected"""
    def __init__(self):
        self._init_folders()

 
    def _init_repo(self):
        try:
            os.listdir(os.path.join(os.getcwd()))
        except OSError, os:
            if err.errno == 2:
                os.mkdir('pers', 0755)


    def _init_folders(self):
        """Creates the folder for the current day and then the """
        try:
            if (self.prefix):
                return
        except AttributeError:
            # creates today folder
            self._path = os.path.join('pers', datetime.now().day)
            try:
                os.listdir(os.path.join(os.getcwd(), self._path))
            except OSError, err:
                if err.errno == 2:
                    os.mkdir(self._path, 0755)

            # creates now folder
            self._path = ''.join([self._path,
                                  datetime.now().strftime('%H:%M:%S')])
            os.mkdir(self._path, 0755)



    def _init_db(self, columns_name):
        try:
            # just preventing from further call
            if (self._conn):
                pass
        except AttributeError:
            name = ''.join(['pers/', '_'.join(['crawler', \
            datetime.datetime.now().strftime('%m-%d_%H-%M')]), '.db'])
            self._conn = sqlite3.connect(name)


    def dump_pool_to_html(pool):
        keywords, anchors_list, _ , text_content = pool



class FileWriter(threading.Thread):
    def __init__(self, group=None, target=None, name=None, *args, **kwargs):
        threading.Thread.__init__(self, name=name, args=args, kwargs=kwargs)
        self._my_data = local()


    def create_one_page(self, page_name, anchors, keywords, text_content):
        page = self._prepare_header(page_name)


    def _prepare_header(self, title):
        return '<html><head><title>%s</title></head><body><h1>%s</h1>' %\
    (title, title)

 
    def _prepare_footer(self):
        return '</body></html>'


    def run(self):
        pass

