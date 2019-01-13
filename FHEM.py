import urllib.request, urllib.error, urllib.parse
import ssl
import cmd
from slog import slog
import requests

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
        self.__session = requests.session()
        self.__session.auth = (user, passw)
    
    def __repr__(self):
        return self.__BASEURL
    
    def get_token(self, url):
        """nurl = urllib.parse.urlsplit(url)
        username = nurl.username
        password = nurl.password
        url = url.replace(username + ':' + password + '@', '')
        url = url.replace(" ", "%20")
        ssl._create_default_https_context = ssl._create_unverified_context
        p = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        p.add_password(None, url, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(p)
        opener = urllib.request.build_opener(handler)
        urllib.request.install_opener(opener)
        try:
            uu = urllib.request.urlopen(
                url=url,
                data=None,
                timeout=10
            )
            token = str(uu.read())
            token = token[token.find('csrf_'):]
            token = token[:token.find("\'")]
            return token
        except urllib.error.URLError as e:
            urllib.error.URLError.reason = e
            self.__log.logMsg('URLError: ' + str(urllib.error.URLError.reason))
            return False
        """
        r = self.__session.get(url)
        token = r.text
        token = token[token.find('csrf_'):]
        token = token[:token.find("\'")]
        return token
    
    def send_command(self, cmd):
        # cmd is the FHEM command
        # type: (object) -> object
        # url = self.__BASEURL + 'cmd=set+licht+on'
        url = self.__BASEURL + 'cmd=' + cmd
            token = self.get_token(self.__BASEURL)
            data = {'fwcsrf': token}
            data = urllib.parse.urlencode(data)
            data = data.encode('utf-8')
            nurl = urllib.parse.urlsplit(url)
            username = nurl.username
            password = nurl.password
            url = url.replace(username + ':' + password + '@', '')
            url = url.replace(" ", "%20")
            ssl._create_default_https_context = ssl._create_unverified_context
            p = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            p.add_password(None, url, username, password)
            handler = urllib.request.HTTPBasicAuthHandler(p)
            opener = urllib.request.build_opener(handler)
            urllib.request.install_opener(opener)
            try:
                urllib.request.urlopen(
                    url=url,
                    data=data,
                    timeout=10
                )
            except urllib.error.URLError as e:
                urllib.error.URLError.reason = e
                self.__log.logMsg('URLError: ' + str(urllib.error.URLError.reason))
                return False
