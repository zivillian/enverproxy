import syslog
import sys

class slog:
    
    def __init__(self, ident='', debug=False):
        self.__DEBUG=debug
        self.__ident=ident
        syslog.openlog(self.__ident)
        
    def __repr__(self):
        return 'log(' + str(self.__ident) + ', ' + str(self.__DEBUG) + ')'
    
    def logMsg (self, msg):
        if self.__DEBUG:
            print(msg, file=sys.stderr)
        syslog.syslog(syslog.LOG_INFO, msg)