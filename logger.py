# -*- coding: utf-8 -*-
import datetime
import os
import logging



class NullHandler(logging.Handler):
    """Empty handler doing strictly nothing"""
    def emit(self, record):
        pass


