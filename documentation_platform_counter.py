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

#cuts out https://, anything after /(inclusive), and also removes www.
def normalize_url(url):
    # Add scheme if missing (needed for urlparse to work correctly)
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # Parse the URL
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Remove 'www.' prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

url_counter = {}

# count the urls
for i in all_data:
    #use the normalize_url function to strip down url
    i['documentationUrl'] = normalize_url(i['documentationUrl'])  
    doc_url = i['documentationUrl']
    #if it is already in the url_counter dict
    if doc_url in url_counter:
        #increment count by 1
        url_counter[doc_url] = url_counter[doc_url]+1        
    else:
        #add it to the url_counter dict
        url_counter[doc_url] = 1

print(url_counter)

sorted_url_counter = {k: v for k, v in sorted(url_counter.items(), key=lambda item: item[1])}

print(sorted_url_counter)



with open('documentation_platforms.csv', 'w') as csv_file:   
    writer = csv.writer(csv_file)
    for key, value in sorted_url_counter.items():
        writer.writerow([key, value])  
