import syslog
import sys

class slog:
    
    # Verbosity levels (1-5)
    #   1 = only start/stop
    #   2 = + status and errors
    #   3 = + flow control
    #   4 = + data 
    #   5 = anything
    
    def __init__(self, ident='', verbosity = 3, cat = syslog.LOG_INFO):
        self.__ident     = ident
        self.__verbosity = verbosity
        self.__cat       = cat
        syslog.openlog(self.__ident)
        
    def __repr__(self):
        return 'log(' + str(self.__ident) + ')'
    
    def logMsg (self, msg, vlevel = 3, cat = None):
        if cat == None:
            cat = self.__cat
        # Only write to log if vlevel >= verbosity
        if vlevel <= self.__verbosity:
            syslog.syslog(cat, msg)

    def set_verbosity(self, verbosity):
        if verbosity < 1:
            verbosity = 1
        if verbosity > 5:
            verbosity = 5
        self.__verbosity = verbosity