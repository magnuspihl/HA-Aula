# aula.py
# Author: Morten Helmstedt. E-mail: helmstedt@gmail.com
''' An example of how to log in to the Danish LMS Aula (https://aula.dk) and
extract data from the API. Could be further developed to also submit data and/or to
create your own web or terminal interface(s) for Aula.'''
 
# Imports
import requests                 # Perform http/https requests
from bs4 import BeautifulSoup   # Parse HTML pages
import json                     # Needed to print JSON API data
 
# User info
user = {
    'username': 'magn494n',
    'password': '9JVnhe7EJEbv'
}
 
# Start requests session
session = requests.Session()
     
# Get login page
url = 'https://login.aula.dk/auth/login.php?type=unilogin'
response = session.get(url)
 
# Login is handled by a loop where each page is first parsed by BeautifulSoup.
# Then the destination of the form is saved as the next url to post to and all
# inputs are collected with special cases for the username and password input.
# Once the loop reaches the Aula front page the loop is exited. The loop has a
# maximum number of iterations to avoid an infinite loop if something changes
# with the Aula login.
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
                            data[input['name']] = user['username']
                            # print('Filled username')
                        # Save password if input is a password field
                        elif input['name'] == 'password':
                            data[input['name']] = user['password']
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
                response = session.post(url, data=data)
            # If there's no data, just try to post to the destination without data
            else:
                response = session.post(url)
            # If the url of the response is the Aula front page, loop is exited
            if response.url == 'https://www.aula.dk:443/portal/':
                success = True
    # If some error occurs, try to just ignore it
    except:
        pass
    # One is added to counter each time the loop runs independent of outcome
    counter += 1
 
# Login succeeded without an HTTP error code and API requests can begin 
if success == True and response.status_code == 200:
    # print("Login succeeded")
    # All API requests go to the below url
    # Each request has a number of parameters, of which method is always included
    # Data is returned in JSON
    url = 'https://www.aula.dk/api/v13/'
 
    ### First API request. This request must be run to generate correct correct cookies for subsequent requests. ###
    params = {
        'method': 'profiles.getProfilesByLogin'
    }
    response_profile = session.get(url, params=params).json()
    # print(json.dumps(response_profile, indent=4))
     
    ### Second API request. This request must be run to generate correct correct cookies for subsequent requests. ###
    params = {
        'method': 'profiles.getProfileContext',
        'portalrole': 'guardian',   # 'guardian' for parents (or other guardians), 'employee' for employees
    }
    response_profile_context = session.get(url, params=params).json()
    # print(json.dumps(response_profile_context, indent=4))
 
    # Loop to get institutions and children associated with profile and save
    # them to lists
    institutions = []
    institution_profiles = []
    children = []
    for institution in response_profile_context['data']['institutions']:
        institutions.append(institution['institutionCode'])
        institution_profiles.append(institution['institutionProfileId'])
        for child in institution['children']:
            children.append(child['id'])
    
    # Get daily overview
    for child in children:
        params = {
            'method': 'presence.getDailyOverview',
            'childIds[]': '3437552'
        }
        response_daily_overview = session.get(url, params=params).json()
        overview = response_daily_overview['data'][0]
        print('Daily Overview (' + overview['institutionProfile']['name'] + '):')
        print('Arrived: ' + overview['checkInTime'])
        print('Leaving: ' + (overview['checkOutTime'] or '(Unknown)'))
        print('Status: ' + str(overview['status'])) #3 when "Til stede"
        print('Activity: ' + str(overview['activityType'])) #0 when "Til stede"
 
# Login failed for some unknown reason
else:
    print("Login failed")