#!/usr/bin/env python
# -*- coding: utf-8 -*-


from multiprocessing import Lock, Queue



class ImportanceQueue(Queue):
    """Sorted mutable queue, stored regarding the importance of the terms.
    It is interfaced like a normal queue with the classic get and put methods,
    but internally the items are sorted to return the more put item.
    When you are using a put with an element already stored, it increments its
    relative importance and sorts the queue"""
    pass
