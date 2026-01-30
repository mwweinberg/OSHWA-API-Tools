import requests
from urllib.parse import urlparse
import secrets
import csv
import json
import time

#github authenticated rate limit is 5,000/hr

#so you know how long it takes to run this thing
start_time = time.time()

#url = "https://certificationapi.oshwa.org/api/projects?limit=1000"

#contentful signin stuff 
authorization_string = 'Bearer ' + secrets.oshwa_api_token
payload = {}
headers = {
    'Content-Type': 'application/json',
    'Authorization': authorization_string
}

#github signin stuff
#this is a dictionary of github credentials that you pass during requests.get()
github_headers = {
    'Authorization': 'Bearer ' + secrets.github_how_many_stars_api_token,
    'X-GitHub-Api-Version': '2022-11-28'
}




####get the total number of projects so you can loop correctly 
#API url 
url = 'https://certificationapi.oshwa.org/api/projects' 
#get the data
response = requests.request("GET", url, headers=headers, data=payload)
#parse the data
json_data = response.json()
#this is the total number of projects
total_number_of_certified_hardware = json_data['total']


#initial variables for getting all of the data
api_download_limit = 1000
api_offset = 0

#to hold all of the data 
all_data = []

####GETTING DATA SECTION#####
#function to get the api data and add it to a dict
def get_data_chunk(limit, offset): 
    #url to be constructed, including the limit (total number of responses) and offset arguments 
    url = 'https://certificationapi.oshwa.org/api/projects?limit=' + str(limit) + '&offset=' + str(offset) 
    #get the data
    response = requests.request("GET", url, headers=headers, data=payload)

    #parse the data
    json_data = response.json()
    #print(json_data)

    #append the data to the all_data dictionary
    for i in json_data['items']:
        all_data.append(i)

    
    #increment the offset
    global api_offset 
    api_offset += 1000

#fill up the list with all of the entires
# while the offset is less than the total number of hardware entries    
while api_offset < total_number_of_certified_hardware:
    #get it
    get_data_chunk(api_download_limit, api_offset)
    # print(api_offset)

#get all of the keys (just look at the first entry in the list because they are all the same)
fieldnames = list(all_data[0].keys())
#this key happens not to be in the first entry
if 'previousVersions' not in fieldnames:
    print('adding previousVersions key')
    fieldnames.append('previousVersions')
######END GETTING DATA SECTION#####

#to hold just the projects that 1) have documentation on github, and 2) have been modified below
github_projects_list = []

#this for statement is currently limited to the first five entries for testing
#remove the `[:5]` to have it work for everything
#print(all_data)
for i in all_data:
    #if github is in the documentation url
    if 'github' in i['documentationUrl']:  
        doc_url = i['documentationUrl']
        #split the url up, using the slash as the separator 
        #the url looks something like 
        #https://github.com/arturo182/pmod_rgb_oled_0.95in/
        #https://github.com/Conor-Burns/0xcb-1337/blob/main/README.md
        #when you use split it creates a list with all of the elements
        doc_url_parts = doc_url.split('/')

        #if the length of the parts list is less than 5, something has probably gone wrong
        if len(doc_url_parts) >= 5:
            #user will be the third entry
            user = doc_url_parts[3]
            #project will be the next one
            project = doc_url_parts[4]
            print(user + '  ' + project) 
        else:
            print(f'error parsing {doc_url}')
        
        #API urls look like https://api.github.com/repos/getpelican/pelican
        github_api_url = "https://api.github.com/repos/" + user + "/" + project 
        github_response = requests.get(github_api_url, headers=github_headers)
        #turn api response into json
        parsed_github_response = github_response.json()
        #fill in some variables
        try:
            stars = parsed_github_response['stargazers_count']
            forks = parsed_github_response['forks_count']
            watchers = parsed_github_response['subscribers_count']
            print('*****success!*******')
        except: 
            print(parsed_github_response)

        #add the key:value pairs to i
        i['stars']=stars
        i['forks']=forks
        i['watchers']=watchers

        #add i to github_projects_list
        github_projects_list.append(i)
    else:
        print("&&&&&&&No github for " + i['projectName'])

#print(github_projects_list)

#### creating the simplified projects list 

github_projects_list_simplified = []

#using get() allows element-by-element error  handling
for i in github_projects_list:
    temp_dict = {
        'oshwaUid': i.get('oshwaUid', None),
        'country': i.get('country', None),
        'projectName': i.get('projectName', None),
        'primaryType': i.get('primaryType', None),
        'hardwareLicense': i.get('hardwareLicense', None),
        'softwareLicense': i.get('softwareLicense', None),
        'documentationLicense': i.get('documentationLicense', None),
        'certificationDate': i.get('certificationDate', None),
        'stars': i.get('stars', -1),
        'forks': i.get('forks', -1),
        'watchers': i.get('watchers', -1), 
        'directoryUrl':('https://certification.oshwa.org/'+i.get('oshwaUid', 'list.html'))
    }

    github_projects_list_simplified.append(temp_dict)


#####write the all_data csv

#github_projects_list is a list of dictionaries
#get the keys from the first entry so you can write them as a header row (the keys from the first entry will be identical to the keys for all of the entries)
all_data_keys = github_projects_list[0].keys()

with open('github_stars_all_data.csv', 'w', newline='') as output_file:
    #write the header row
    dict_writer = csv.DictWriter(output_file, all_data_keys, extrasaction='ignore')
    dict_writer.writeheader()
    #write everything else
    dict_writer.writerows(github_projects_list)

#####write the simplified csv

simplified_keys = github_projects_list_simplified[0].keys()
with open('github_stars_simplified.csv', 'w', newline='') as output_file:
    #write the header row
    dict_writer = csv.DictWriter(output_file, simplified_keys, extrasaction='ignore')
    dict_writer.writeheader()
    #write everything else
    dict_writer.writerows(github_projects_list_simplified)

#so you know how long it takes to run this thing
end_time = time.time()
#default is in seconds, so divide by 60 to get minutes
elapsed_time = (end_time - start_time) / 60  

#you only need 2 decimal places for the time, which is what .2f does
print(f'Done! It took {elapsed_time:.2f} minutes to run.')
