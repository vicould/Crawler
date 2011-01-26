#!/usr/bin/env python
# -*- coding: utf-8 -*-


from Queue import Queue, Empty



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
                print 'inserting %s at %d' % (value, i)
                self._queue.insert(i, (item, item_score))
                return
            i += 1

    
    def _get(self):
        value = self._queue.pop()[0]
        return value




