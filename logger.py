import datetime

class Logger:
    filename = ''
    header = []


    def __init__(self, prefix, header):
        self.filename = prefix + '_' + datetime.datetime.now().strftime('%m-%d_%H-%M')\
                 + '.log'
        self.header += [header, datetime.datetime.now().strftime("%c") + '\n']
        """writes header"""
        file = open(self.filename, 'w')
        file.writelines(self.header)
        file.write('\n\n\n')
        file.close()

    def log_event(self, event_name, event):
        """Writes an event occuring to the current log file. 
        event_name is written, and then the description of the event is added.
        Event should be an iterable."""
        file = open(self.filename, 'a')
        file.write(event_name + ':\n')
        for line in event:
            file.write('    ' + line)
        file.write('\n\n')

