import syslog
import sys

class slog:
    
    def __init__(self, ident=''):
        self.__ident=ident
        syslog.openlog(self.__ident)
        
    def __repr__(self):
        return 'log(' + str(self.__ident) + ')'
    
    def logMsg (self, msg):
        syslog.syslog(syslog.LOG_INFO, msg)
