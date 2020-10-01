import syslog
import sys
from datetime import datetime

class slog:
    
    # Verbosity levels (1-5)
    #   1 = only start/stop
    #   2 = + status and errors
    #   3 = + flow control
    #   4 = + data 
    #   5 = anything
    
    def __init__(self, ident='', verbosity = 3, log_type='syslog', cat = syslog.LOG_INFO):
        self.__ident    = ident
        self.__cat      = cat
        self.set_verbosity(verbosity)
        if log_type == 'sys.stdout':
            log_type=sys.stdout
        else:
            log_type='syslog'
        if log_type == 'syslog':
            syslog.openlog(self.__ident)
        self.__log_type = log_type

    def __repr__(self):
        return 'log(' + str(self.__ident) + ')'
    
    def logMsg (self, msg, vlevel = 3, cat = None):
        if cat == None:
            cat = self.__cat
        # Only write to log if vlevel <= verbosity
        if vlevel <= self.__verbosity:
            if self.__log_type == 'syslog':
                syslog.syslog(cat, msg)
            else:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(now + ' ' + self.__ident + ': ' + msg, file=self.__log_type)

    def set_verbosity(self, verbosity):
        if verbosity < 1:
            verbosity = 1
        if verbosity > 5:
            verbosity = 5
        self.__verbosity = verbosity
