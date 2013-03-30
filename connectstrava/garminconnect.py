'''
Created on Mar 28, 2013


Helpful links:

http://connect.garmin.com/proxy/activity-search-service-1.2/index.html
http://connect.garmin.com/proxy/upload-service-1.1/index.html
http://connect.garmin.com/proxy/activity-service-1.2/index.html

http://www.ciscomonkey.net/gc-to-dm-export/
http://connect.garmin.com/proxy/activity-search-service-1.0/json/activities

'''
import logging
import requests

 
class ConnectClient(object):
    server = 'connect.garmin.com'
    default_user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.52 Safari/537.17'
    headers = None
    cookies = None
    creds = None
        
    def __init__(self, username, password, user_agent=None):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        if user_agent is None:
            user_agent = self.default_user_agent
        self.rsession = requests.Session()
        self.rsession.headers.update({'User-Agent': user_agent})
        self.login(username, password)
        
    def login(self, username, password):
        """
        """
        
        r = self.rsession.get('https://connect.garmin.com/signin')
                               
        params = {'login': 'login',
                  'login:loginUsernameField': username,
                  'login:password': password,
                  'login:signInButton': 'Sign In',
                  'javax.faces.ViewState': 'j_id1'}
        
        r = self.rsession.post('https://connect.garmin.com/signin',
                            data=params,
                            cookies=r.cookies)
        
        #print r.content
        
        self.cookies = r.cookies
        
    def get_activities(self, **kwargs):
        """
        Gets a JSON structure of matching activities.
        """
        r = self.rsession.get('http://connect.garmin.com/proxy/activity-search-service-1.0/json/activities',
                              params=kwargs,
                              cookies=self.cookies)
        #print r.content
        results = r.json()
        
        return results['results']['activities']
    
    def download_activity(self, activity_id, fmt='tcx'):
        """
        Download activity in specified format.
        """
        url = 'http://connect.garmin.com/proxy/activity-service-1.1/{format}/activity/{activity}'.format(format=fmt, activity=activity_id)
        r = self.rsession.get(url, params={'full': 'true'})
        return r.content