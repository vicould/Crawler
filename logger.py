# -*- coding: utf-8 -*-
import datetime
import os

class Logger:
    """Logger class, receiving two types of events to log"""
    filename = ''
    header = []


    def __init__(self, prefix, header):
        """Initializes the logger, creating a new file with the given prefix,
        and writes down the header to the file."""
        if (not os.listdir(os.getcwd()).__contains__('log')):
            os.mkdir('log', 0755)


        self.filename = ''.join(['log/', 
                                 '_'.join([prefix,
                                           datetime.datetime.now().strftime('%m-%d_%H-%M')]),
                                 '.log'])
        self.header += [header, datetime.datetime.now().strftime("%c") + '\n']
        """writes header"""
        file = open(self.filename, 'w')
        file.writelines(self.header)
        file.write('\n\n\n')
        file.close()


    def log_short_message(self, msg):
        """Writes a single (small) message"""
        file = open(self.filename, 'a')
        file.write(datetime.datetime.now().strftime("%c") + ' - ' + msg + '\n')
        file.close()


    def log_event(self, event_name, event):
        """Writes an event occuring to the current log file. 
        event_name is written, and then the description of the event is added.
        Event should be an iterable."""
        if event is None:
            return
        file = open(self.filename, 'a')
        file.write(datetime.datetime.now().strftime("%c") + ' ' + event_name + ':\n')
        for line in event:
            file.write('    ' + line)
        file.write('\n\n')
        file.close()

