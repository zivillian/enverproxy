from slog import slog
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class FHEM:
    
    def __init__(self, baseURL = None, user='', passw='', l=None):
        if baseURL == None:
            self.__BASEURL = 'https://enver:Test@homeservice.eitelwein.net:8083/fhem?'
        else:
            self.__BASEURL = baseURL
        if l == None:
            self.__log = slog('FHEM class', True)
        else:
            self.__log = l
        self.__session        = requests.session()
        self.__session.auth   = (user, passw)
        self.__session.verify ='server-ca.pem'
        self.__session.verify=False
    
    def __repr__(self):
        return 'FHEM(' + self.__BASEURL + ', ' + self.__session.auth[0] + ', ' + self.__session.auth[1] + ', ' + self.__log + ')'
    
    def get_token(self, url):
        try:
            r = self.__session.get(url)
            token = r.text
            token = token[token.find('csrf_'):]
            token = token[:token.find("\'")]
        except ConnectionError as e:
            self.__log.logMsg('Requests error when getting token: ' + str(e))
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
        except ConnectionError as e:
            self.__log.logMsg('Requests error when posting command: ' + str(e))
        
