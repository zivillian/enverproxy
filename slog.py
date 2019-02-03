import syslog
import sys

class slog:
    
    # Verbosity levels (1-5)
    #   1 = only start/stop
    #   2 = + errors
    #   3 = + flow control
    #   4 = + data 
    #   5 = anything
    
    def __init__(self, ident='', verbosity = 3):
        self.__ident     = ident
        self.__verbosity = verbosity
        syslog.openlog(self.__ident)
        
    def __repr__(self):
        return 'log(' + str(self.__ident) + ')'
    
    def logMsg (self, msg, vlevel = 3, cat = syslog.LOG_INFO):
        # Only write to log if vlevel >= verbosity
        if vlevel <= self.__verbosity:
            syslog.syslog(cat, msg)

    def set_verbosity(self, verbosity):
        if verbosity < 1:
            verbosity = 1
        if verbosity > 5:
            verbosity = 5
        self.__verbosity = verbosity