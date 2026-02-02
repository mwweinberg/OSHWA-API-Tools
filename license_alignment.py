import requests
from urllib.parse import urlparse
import secrets
import csv
import json
import time



#so you know how long it takes to run this thing
start_time = time.time()

#variable to decide if you want to hit the contentful API to get the listing data
#if 0, load from csv
#if 1, hit the api
get_data_via_api = 0

#url = "https://certificationapi.oshwa.org/api/projects?limit=1000"

#contentful signin stuff 
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

def get_data_from_api():
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


def get_data_from_csv():
    with open('github_stars_all_data_20260202.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields from strings to integers
            row['stars'] = int(row['stars']) if row['stars'] else -1
            row['forks'] = int(row['forks']) if row['forks'] else -1
            row['watchers'] = int(row['watchers']) if row['watchers'] else -1
            
            all_data.append(row)

    print(f"Loaded {len(all_data)} projects from CSV")


#gets data from source depending on get_data_via_api variable
if get_data_via_api == 0:
    get_data_from_csv()
elif get_data_via_api == 1:
    get_data_from_api()
else: 
    print("error selecting data source")

######END GETTING DATA SECTION#####

def check_license_compatibility(hardware_lic, software_lic, doc_lic):
    """
    Check if licenses are compatible with each other for open source hardware projects.
    Returns: (status: str, issues: list of strings)
    status can be: 'compatible', 'incompatible', or 'cannot_assess'
    """
    issues = []
    warnings = []
    
    # Check for 'Other' licenses - treat as cannot assess
    if hardware_lic == 'Other':
        return ('cannot_assess', ["Hardware license is 'Other' - cannot verify compatibility"])
    if software_lic == 'Other':
        return ('cannot_assess', ["Software license is 'Other' - cannot verify compatibility"])
    if doc_lic == 'Other':
        return ('cannot_assess', ["Documentation license is 'Other' - cannot verify compatibility"])
    
    # Check for missing hardware license
    if not hardware_lic:
        return ('cannot_assess', ["Hardware license missing - cannot assess compatibility"])
    
    # Normalize missing licenses
    if not software_lic:
        software_lic = None
    if not doc_lic:
        doc_lic = None
    
    # Skip if no software
    if software_lic == "No software":
        software_lic = None
    
    # Define license categories
    strong_copyleft = ['GPL', 'GPL-3.0-only', 'GPL-3.0-or-later', 'CERN-OHL-S-2.0', 'AGPL', 'TAPR']
    weak_copyleft = ['LGPL', 'CERN-OHL-W-2.0', 'Mozilla', 'CC-BY-SA-4.0', 'CC BY-SA']
    permissive = ['MIT', 'Apache', 'BSD', 'CC-BY-4.0', 'CC BY', 'CERN-OHL-P-2.0', 'Solderpad']
    public_domain = ['CC0-1.0', 'CC 0']
    
    # Legacy/unclear
    legacy = ['CERN', 'CERN-OHL-1.2']
    
    def get_license_type(lic):
        if not lic:
            return None
        if lic in strong_copyleft:
            return 'strong_copyleft'
        if lic in weak_copyleft:
            return 'weak_copyleft'
        if lic in permissive:
            return 'permissive'
        if lic in public_domain:
            return 'public_domain'
        if lic in legacy:
            return 'legacy'
        return 'unknown'
    
    hw_type = get_license_type(hardware_lic)
    sw_type = get_license_type(software_lic)
    doc_type = get_license_type(doc_lic)
    
    # Check hardware-software compatibility
    if sw_type:
        # Strong copyleft hardware with permissive software is problematic
        if hw_type == 'strong_copyleft' and sw_type == 'permissive':
            issues.append(f"Incompatible: {hardware_lic} hardware requires derivative works to be under same license, but software is permissive {software_lic}")
        
        # GPL hardware with non-GPL software is usually incompatible
        if 'GPL' in hardware_lic and 'GPL' not in software_lic and sw_type != 'public_domain':
            issues.append(f"Likely incompatible: GPL hardware ({hardware_lic}) with non-GPL software ({software_lic})")
        
        # TAPR hardware with non-copyleft software
        if hardware_lic == 'TAPR' and sw_type in ['permissive', 'weak_copyleft']:
            issues.append(f"Likely incompatible: TAPR hardware with non-copyleft software ({software_lic})")
        
        # CERN-OHL-S with non-copyleft software
        if hardware_lic == 'CERN-OHL-S-2.0' and sw_type in ['permissive', 'weak_copyleft']:
            issues.append(f"Incompatible: CERN-OHL-S-2.0 hardware requires strongly reciprocal license, but software is {software_lic}")
    
    # Check hardware-documentation compatibility
    if doc_type:
        # Strong copyleft hardware with permissive documentation
        if hw_type == 'strong_copyleft' and doc_type == 'permissive':
            warnings.append(f"Unusual combination: {hardware_lic} hardware with permissive {doc_lic} documentation - may be intentional but worth reviewing")
        
        # Creative Commons licenses (designed for content) on hardware
        if hardware_lic.startswith('CC') and hardware_lic not in ['CC0-1.0']:
            warnings.append(f"CC licenses ({hardware_lic}) are designed for creative content, not hardware - consider CERN-OHL or similar")
    
    # Check for legacy licenses
    if hw_type == 'legacy':
        warnings.append(f"Legacy hardware license ({hardware_lic}) - consider updating to CERN-OHL-2.0 family")
    
    # Documentation-software compatibility (usually less strict)
    # Most combinations are acceptable since they govern different types of content
    
    # Determine overall status
    if len(issues) > 0:
        status = 'incompatible'
        all_notes = issues + warnings
    else:
        status = 'compatible'
        all_notes = warnings if warnings else ["No compatibility issues detected"]
    
    return (status, all_notes)

# Analyze all projects
compatibility_report = []

for item in all_data:
    status, notes = check_license_compatibility(
        item.get('hardwareLicense', ''),
        item.get('softwareLicense', ''),
        item.get('documentationLicense', '')
    )
    
    item['license_status'] = status
    item['compatibility_notes'] = '; '.join(notes)
    
    compatibility_report.append({
        'projectName': item.get('projectName', ''),
        'oshwaUid': item.get('oshwaUid', ''),
        'hardwareLicense': item.get('hardwareLicense', ''),
        'softwareLicense': item.get('softwareLicense', ''),
        'documentationLicense': item.get('documentationLicense', ''),
        'status': status,
        'notes': '; '.join(notes)
    })

# Print summary
total = len(compatibility_report)
compatible = sum(1 for r in compatibility_report if r['status'] == 'compatible')
incompatible = sum(1 for r in compatibility_report if r['status'] == 'incompatible')
cannot_assess = sum(1 for r in compatibility_report if r['status'] == 'cannot_assess')

print(f"\n=== LICENSE COMPATIBILITY SUMMARY ===")
print(f"Total projects: {total}")
print(f"Compatible: {compatible}")
print(f"Incompatible: {incompatible}")
print(f"Cannot assess: {cannot_assess}")

# Show incompatible projects
print(f"\n=== INCOMPATIBLE PROJECTS ===")
for r in compatibility_report:
    if r['status'] == 'incompatible':
        print(f"\n{r['projectName']} ({r['oshwaUid']})")
        print(f"  HW: {r['hardwareLicense']} | SW: {r['softwareLicense']} | Doc: {r['documentationLicense']}")
        print(f"  Issues: {r['notes']}")

# Show cannot assess projects
print(f"\n=== CANNOT ASSESS PROJECTS ===")
for r in compatibility_report:
    if r['status'] == 'cannot_assess':
        print(f"\n{r['projectName']} ({r['oshwaUid']})")
        print(f"  HW: {r['hardwareLicense']} | SW: {r['softwareLicense']} | Doc: {r['documentationLicense']}")
        print(f"  Reason: {r['notes']}")

# Save full report to CSV
with open('license_compatibility_report_full.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['projectName', 'oshwaUid', 'hardwareLicense', 'softwareLicense', 'documentationLicense', 'status', 'notes'])
    writer.writeheader()
    writer.writerows(compatibility_report)

print("\nFull report saved to license_compatibility_report_full.csv")

# Create summary report
from collections import Counter

# Count notes for cannot_assess and incompatible
cannot_assess_notes = []
incompatible_notes = []

for r in compatibility_report:
    if r['status'] == 'cannot_assess':
        cannot_assess_notes.append(r['notes'])
    elif r['status'] == 'incompatible':
        incompatible_notes.append(r['notes'])

cannot_assess_counts = Counter(cannot_assess_notes)
incompatible_counts = Counter(incompatible_notes)

# Build summary data
summary_data = []

# Add overall counts
summary_data.append({
    'category': 'Overall',
    'subcategory': 'Compatible',
    'count': compatible
})
summary_data.append({
    'category': 'Overall',
    'subcategory': 'Incompatible',
    'count': incompatible
})
summary_data.append({
    'category': 'Overall',
    'subcategory': 'Cannot Assess',
    'count': cannot_assess
})

# Add cannot_assess breakdown
for note, count in cannot_assess_counts.items():
    summary_data.append({
        'category': 'Cannot Assess Reasons',
        'subcategory': note,
        'count': count
    })

# Add incompatible breakdown
for note, count in incompatible_counts.items():
    summary_data.append({
        'category': 'Incompatible Reasons',
        'subcategory': note,
        'count': count
    })

# Save summary report to CSV
with open('license_compatibility_report_summary.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['category', 'subcategory', 'count'])
    writer.writeheader()
    writer.writerows(summary_data)

print("Summary report saved to license_compatibility_report_summary.csv")






#so you know how long it takes to run this thing
end_time = time.time()
#default is in seconds, so divide by 60 to get minutes
elapsed_time = (end_time - start_time) / 60  
#you only need 2 decimal places for the time, which is what .2f does
print(f'Done! It took {elapsed_time:.2f} minutes to run.')