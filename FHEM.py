from slog import slog
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class FHEM:
    
    def __init__(self, baseURL = None, user='', passw='', l=None):
        if baseURL == None:
            # Place standard url of your fhem server here
            self.__BASEURL = ''
        else:
            self.__BASEURL = baseURL
        if l == None:
            self.__log = slog('FHEM class', True)
        else:
            self.__log = l
        self.__session        = requests.session()
        self.__session.auth   = (user, passw)
        # Place your server certificate here if you use https
        self.__session.verify = '/etc/ssl/certs'
        if self.__session.verify == False:
            # Suppress error warnings of unverified https requests
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


    def __repr__(self):
        return 'FHEM(' + self.__BASEURL + ', ' + self.__session.auth[0] + ', ' + self.__session.auth[1] + ', ' + self.__log + ')'

    
    def get_token(self, url):
        try:
            self.__log.logMsg('Initiating connection with FHEM server: ' + url, 3)
            r = self.__session.get(url)
        except requests.exceptions.RequestException as e:
            self.__log.logMsg('Requests error when getting token: ' + str(e), 2)
        else:
            token = r.text
            token = token[token.find('csrf_'):]
            token = token[:token.find("\'")]
            self.__log.logMsg('Received token from FHEM server: ' + token, 4)
        return token

    
    def send_command(self, cmd):
        # cmd is the FHEM command
        # type: (object) -> object
        # url = self.__BASEURL + 'cmd=set+licht+on'
        url   = self.__BASEURL
        token = self.get_token(url)
        data  = {'fwcsrf': token}
        url   = url + 'cmd=' + cmd
        try:
            self.__log.logMsg('Sending data to FHEM server: ' + data, 4)
            r = self.__session.get(url, data=data)
        except requests.exceptions.RequestException as e:
            self.__log.logMsg('Requests error when posting command: ' + str(e), 2)
        
