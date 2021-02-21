import sys
import logging
import logging.handlers
import graypy

class slog:
    
    # Verbosity levels (1-5)
    #   1 = only start/stop
    #   2 = + status and errors
    #   3 = + flow control
    #   4 = + data 
    #   5 = anything
    
    def __init__(self, ident='', verbosity = 3, log_type='syslog', log_address='/dev/log', log_port=514, cat = logging.INFO):
        self.__ident    = ident
        self.__cat      = cat
        self.set_verbosity(verbosity)
        self.__type     = log_type
        self.__address  = log_address
        self.__port     = log_port
        
        if log_type == 'sys.stdout':
            ch = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
        elif log_type == 'sys.stderr':
            ch = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
        elif log_type == 'gelf':
            ch = graypy.GELFUDPHandler(log_address, log_port)
        else:
            # default is to log to syslog
            log_type='syslog'
            
        if log_type == 'syslog':
            if log_address == '/dev/log':
                ch = logging.handlers.SysLogHandler(address=log_address, facility='daemon')
            else:
                ch = logging.handlers.SysLogHandler(address=(log_address, log_port), facility='daemon')
            formatter = logging.Formatter('%(name)s: %(message)s')
            ch.setFormatter(formatter)
           
        self.__logger = logging.getLogger(self.__ident)
        self.__logger.setLevel(self.__cat)   
        if self.__logger.handlers:
            # remove previous handler
            self.__logger.handlers.pop()
        self.__logger.addHandler(ch)
        if log_type == 'gelf':
            # insert a logging adapter to add static fields
            orig_logger = self.__logger
            self.__logger = logging.LoggerAdapter(logging.getLogger(self.__ident), {'application_name': 'envertecproxy', 'log_type': 'smarthome'})

    def __repr__(self):
        return 'log(' + str(self.__ident) + ',' + self.__verbosity + ',' + self.__type + ',' + self.__address + ',' + self.__port + ')'
    
    def logMsg (self, msg, vlevel = 3, cat = None):
        if cat == None:
            cat = self.__cat
        # Only write to log if vlevel <= verbosity
        if vlevel <= self.__verbosity:
            self.__logger.log(cat, msg)
            
    def set_verbosity(self, verbosity):
        if verbosity < 1:
            verbosity = 1
        if verbosity > 5:
            verbosity = 5
        self.__verbosity = verbosity
