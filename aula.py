from multiprocessing import AuthenticationError
import requests
from bs4 import BeautifulSoup
import json
from .const import *

class AulaApi:
    def __init__(self, username = 'magn494n', password = 'LokaleZone71'):
        self.username = username
        self.password = password
    
    def _login(self):
        self.session = requests.Session()
        response = self.session.get(LOGIN_URL)
        counter = 0
        success = False
        while success == False and counter < 10:
            try:
                # Parse response using BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                # print('Got soup')
                # Get destination of form element (assumes only one)
                url = soup.form['action']
                # print('Found action URL', url)
                
                # If form has a destination, inputs are collected and names and values
                # for posting to form destination are saved to a dictionary called data
                if url:
                    # Get all inputs from page
                    inputs = soup.find_all('input')
                    # Check whether page has inputs
                    if inputs:
                        # Create empty dictionary 
                        data = {}
                        # Loop through inputs
                        for input in inputs:
                            # Some inputs may have no names or values so a try/except
                            # construction is used.
                            try:
                                # Login takes place in single input steps, which
                                # is the reason for the if/elif construction
                                # Save username if input is a username field
                                if input['name'] == 'username':
                                    data[input['name']] = self.username
                                    # print('Filled username')
                                # Save password if input is a password field
                                elif input['name'] == 'password':
                                    data[input['name']] = self.password
                                    # print('Filled password')
                                # For employees the login procedure has an additional field to select a role
                                # If an employee needs to login in a parent role, this value needs to be changed
                                elif input['name'] == 'selected-aktoer':
                                    data[input['name']] = "MEDARBEJDER_EKSTERN"
                                # For all other inputs, save name and value of input
                                else:
                                    data[input['name']] = input['value']
                            # If input has no value, an error is caught but needs no handling
                            # since inputs without values do not need to be posted to next
                            # destination.
                            except:
                                pass
                    # If there's data in the dictionary, it is submitted to the destination url
                    if data:
                        response = self.session.post(url, data=data)
                    # If there's no data, just try to post to the destination without data
                    else:
                        response = self.session.post(url)
                    # If the url of the response is the Aula front page, loop is exited
                    if response.url == 'https://www.aula.dk:443/portal/':
                        success = True
            # If some error occurs, try to just ignore it
            except:
                pass
            # One is added to counter each time the loop runs independent of outcome
            counter += 1
        if success == True and response.status_code == 200:
            params = { 'method': 'profiles.getProfilesByLogin' }
            response_profile = self.session.get(API_URL, params=params).json()
            params = {
                'method': 'profiles.getProfileContext',
                'portalrole': 'guardian',   # 'guardian' for parents (or other guardians), 'employee' for employees
            }
            response_profile_context = self.session.get(API_URL, params=params).json()
            
            self.institutions = []
            self.institution_profiles = []
            self.children = []
            for institution in response_profile_context['data']['institutions']:
                # print(json.dumps(response_profile_context['data'], indent=4))
                self.institutions.append(institution['institutionCode'])
                self.institution_profiles.append(institution['institutionProfileId'])
                for child in institution['children']:
                    # print(json.dumps(child, indent=4))
                    self.children.append(child['id'])
        else:
            raise AuthenticationError()

    def _get_daily_overview(self):
        for child in self.children:
            params = {
                'method': 'presence.getDailyOverview',
                'childIds[]': child
            }
            response_daily_overview = self.session.get(API_URL, params=params).json()
            overview = response_daily_overview['data'][0]
            return {
                ATTR_NAME: overview[ATTR_INSTITUTION_PROFILE][ATTR_NAME],
                ATTR_STATUS: overview[ATTR_STATUS]
            }