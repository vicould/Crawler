#!/usr/bin/env python
# -*- coding: utf-8 -*-


from Queue import Queue, Empty, Full
import threading
from threading import local
from time import time as _time
import os


class ArrayQueue(Queue):
    def _init(self, maxsize):
        self._queue = []


    def _qsize(self, len=len):
        return len(self._queue)


    def _put(self, item):
        self._queue.append(item)


    def _get(self):
        return self._queue.pop()


    def get_copy(self):
        return self._queue



class SetQueue(Queue):
    def _init(self, maxsize):
        self.queue = set([])


    def _qsize(self, len=len):
        return len(self.queue)


    def _put(self, item):
        self.queue.add(item)


    def _get(self):
        return self.queue.pop()



class SortedQueue(Queue):
    """Queue storing only unique elements, or incrementing the score when
    duplicates are being put. Therefore, the most important element is
    returned when calling the get method"""
    def _init(self, maxsize):
        self.queue = [] # our queue is a basic list


    def _qsize(self, len=len):
        return len(self.queue)


    def _put(self, item):
        """Organizes the new queue with the element"""
        if len(self.queue) == 0:
            self.queue.append((item, 1))
            return
        i = 0
        item_score = 1
        # could be way better optimized, no time for that now
        for value, score in self.queue:
            if (item == value):
                # adds the score
                item_score += score
                # removes the element from the list
                self.queue.pop(i)
                break
            i += 1

        i = 0
        # tries to find where to put the element
        for value, score in self.queue:
            # next element is more important, stores the value here
            if (item_score <= score):
                self.queue.insert(i, (item, item_score))
                return
            i += 1


    def _get(self):
        value = self.queue.pop()[0]
        return value



class SynchronizedDict:
    """Class implementing a synchronized dictionary, allowing concurential
    access to the elements of the dict. It is a special dict as values are
    stored as a list, so that you can add elements to an existing key if
    needed, thanks to the add_item_to_key method.
    To retrieve an element from the dict you have two choices, either calling
    get which will return an arbitrary mapping from the dict, or calling the
    get_with_key method which will return only the list of values.
    It does not provide any iterator either on the keys or the values.
    This class is largely inspired by the Queue class from the standard
    library."""
    def __init__(self, maxsize=0):
        try:
            import threading
        except ImportError:
            import dummy_threading as threading
        self.maxsize = maxsize
        self._init(maxsize)
        self.mutex = threading.Lock()
        self.not_full = threading.Condition(self.mutex)
        self.not_empty = threading.Condition(self.mutex)
        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0


    def task_done(self):
        """Indicates that a formerly endictd task is complete.

        Used by dict consumer threads.  For each get() used to fetch a task,
        a subsequent call to task_done() tells the dict that the processing
        on the task is complete.

        If a join() is currently blocking, it will resume when all items
        have been processed (meaning that a task_done() call was received
        for every item that had been put() into the dict).

        Raises a ValueError if called more times than there were items
        placed in the dict.
        """
        self.all_tasks_done.acquire()
        try:
            unfinished = self.unfinished_tasks - 1
            if unfinished  <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished
        finally:
            self.all_tasks_done.release()


    def join(self):
        """Blocks until all items in the dict have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the
        dict. The count goes down whenever a consumer thread calls task_done()
        to indicate the item was retrieved and all work on it is complete.

        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        self.all_tasks_done.acquire()
        try:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()
        finally:
            self.all_tasks_done.release()


    def qsize(self):
        """Returns the approximate size of the dict (not reliable!)."""
        self.mutex.acquire()
        n = self._qsize()
        self.mutex.release()
        return n


    def empty(self):
        """Returns True if the dict is empty, False otherwise (not reliable!)."""
        self.mutex.acquire()
        n = not self._qsize()
        self.mutex.release()
        return n


    def full(self):
        """Returns True if the dict is full, False otherwise (not reliable!)."""
        self.mutex.acquire()
        n = 0 < self.maxsize == self._qsize()
        self.mutex.release()
        return n


    def put(self, key, item, block=True, timeout=None):
        """Puts in the dict the mapping between an item and a dict.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a positive number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the dict if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        self.not_full.acquire()
        try:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() == self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() == self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                else:
                    endtime = _time() + timeout
                    while self._qsize() == self.maxsize:
                        remaining = endtime - _time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            old = self._put(key, item)
            if not old:
                self.unfinished_tasks += 1
            self.not_empty.notify()
        finally:
            self.not_full.release()


    def put_nowait(self, key, item):
        """Puts the mapping between the key and the item in the dict without
        blocking.

        Only endict the item if a free slot is immediately available.
        Otherwise raise the Full exception.
        """
        return self.put(key, item, False)


    def add_item_to_key(self, key, item):
        """Method to add a value to an existing key. Use put with the name of
        the key if you want to overwrite the current value associated with the
        key if it exists.
        Adding an item to an existing key shouldn't block in any way, that's
        why there isn't a block or timeout argument"""
        self.not_full.acquire()
        try:
            self._add_item_to_key(key, item)
        finally:
            self.not_full.release()


    def get_with_key(self, key):
        """Removes and returns the item corresponding to the given key from the
        dict. It raises Empty if no key was found in the dict, KeyError if the
        specific key is not in the dictionary.

        This call is not blocking, as you want a specific entry in the dict: it
        is there and is returned, or it's not there, and a KeyError exception
        is raised.
        """
        self.not_empty.acquire()
        try:
            if not self._qsize():
                raise Empty
            else:
                item = self._get_with_key(key)
                self.not_full.notify()
                return item
        finally:
            self.not_empty.release()


    def get(self, block=True, timeout=None):
        """Removes and returns one arbitrary mapping. Contrary to the
        get_with_key method, this call can be blocking.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a positive number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case)."""
        self.not_empty.acquire()
        try:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            else:
                endtime = _time() + timeout
                while not self._qsize():
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            self.not_full.notify()
            return item
        finally:
            self.not_empty.release()


    def get_nowait(self):
        """Removes and returns an arbitrary mapping from the dict without
        blocking.

        Only get a mapping if one is immediately available. Otherwise
        raise the Empty exception.
        """
        return self.get(False)


    def _init(self, maxsize=0):
        self.dict = {}

    def _qsize(self):
        return len(self.dict)


    def _put(self, key, item):
        old = False
        if key in self.dict:
            old = True
        self.dict[key] = [item]
        return old


    # adds an item to an existing place
    def _add_item_to_key(self, key, item):
        self.dict[key].append(item)


    # returns the value of the key
    def _get_with_key(self, key):
        return self.dict.pop(key)


    def _get(self):
        return self.dict.popitem()
