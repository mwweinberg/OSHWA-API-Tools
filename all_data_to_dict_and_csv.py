#This code stub will
#1. put all of the entries in the OSHWA database into a list called 'all_data'
#2. export all of the entries as a csv called 'all_data.csv'
#it assumes the existence of a 'secrets.py' file in this folder

import requests
from urllib.parse import urlparse
import secrets
import csv


#url = "https://certificationapi.oshwa.org/api/projects?limit=1000"

#signin stuff 
authorization_string = 'Bearer ' + secrets.oshwa_api_token
payload = {}
headers = {
    'Content-Type': 'application/json',
    'Authorization': authorization_string
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


with open('all_data.csv', 'w') as csv_file:
    #imports the fieldnames from above
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    #writes the header row based on the fieldnames 
    writer.writeheader()
    #writes one row per institution blob
    writer.writerows(all_data)    
