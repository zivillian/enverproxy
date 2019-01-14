from slog import slog
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class FHEM:
    
    def __init__(self, baseURL = None, user='', passw='', l=None):
        if baseURL == None:
            # Place standard url of your fhem server here
            self.__BASEURL = 'https://homeservice.eitelwein.net:8083/fhem?'
        else:
            self.__BASEURL = baseURL
        if l == None:
            self.__log = slog('FHEM class', True)
        else:
            self.__log = l
        self.__session        = requests.session()
        self.__session.auth   = (user, passw)
        # Place your server certificate here if you use https
        self.__session.verify = 'server-cert.pem'
        self.__session.verify = False
        if self.__session.verify == False:
            # Suppress error warnings of unverified https requests
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def __repr__(self):
        return 'FHEM(' + self.__BASEURL + ', ' + self.__session.auth[0] + ', ' + self.__session.auth[1] + ', ' + self.__log + ')'
    
    def get_token(self, url):
        try:
            r = self.__session.get(url)
        except Exception as e:
            self.__log.logMsg('Requests error when getting token: ' + str(e))
        else:
            token = r.text
            token = token[token.find('csrf_'):]
            token = token[:token.find("\'")]
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
            r = self.__session.get(url, data=data)
        except Exception as e:
            self.__log.logMsg('Requests error when posting command: ' + str(e))
        
