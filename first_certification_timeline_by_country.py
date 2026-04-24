import requests
import secrets
import csv

authorization_string = 'Bearer ' + secrets.oshwa_api_token
payload = {}
headers = {
    'Content-Type': 'application/json',
    'Authorization': authorization_string
}

url = 'https://certificationapi.oshwa.org/api/projects'
response = requests.request("GET", url, headers=headers, data=payload)
json_data = response.json()
total_number_of_certified_hardware = json_data['total']

api_download_limit = 1000
api_offset = 0
all_data = []

def get_data_chunk(limit, offset):
    url = 'https://certificationapi.oshwa.org/api/projects?limit=' + str(limit) + '&offset=' + str(offset)
    response = requests.request("GET", url, headers=headers, data=payload)
    json_data = response.json()
    for i in json_data['items']:
        all_data.append(i)
    global api_offset
    api_offset += 1000

while api_offset < total_number_of_certified_hardware:
    get_data_chunk(api_download_limit, api_offset)

# For each country, find the entry with the lowest UID number (i.e. the first certification).
# UIDs are formatted as two-letter country code + six-digit number (e.g. JP000002).
# The numeric suffix reliably identifies order within a country.
first_by_country = {}

for item in all_data:
    uid = item.get('oshwaUid', '')
    if len(uid) < 3:
        continue
    country_code = uid[:2]
    try:
        uid_number = int(uid[2:])
    except ValueError:
        continue

    if country_code not in first_by_country:
        first_by_country[country_code] = (uid_number, item)
    elif uid_number < first_by_country[country_code][0]:
        first_by_country[country_code] = (uid_number, item)

# Build rows, sorted by certificationDate so the output is a timeline
rows = []
for country_code, (_, item) in first_by_country.items():
    raw_date = item.get('certificationDate', '')
    date = raw_date[:10] if raw_date else 'unknown'
    rows.append({
        'date': date,
        'country': item.get('country', ''),
        'country_code': country_code,
        'project_name': item.get('projectName', ''),
        'oshwa_uid': item.get('oshwaUid', ''),
        'link': 'https://certification.oshwa.org/' + item.get('oshwaUid', '').lower() + '.html'
    })

rows.sort(key=lambda r: (r['date'] == 'unknown', r['date']))

with open('first_certification_timeline_by_country.csv', 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['date', 'country', 'country_code', 'project_name', 'oshwa_uid', 'link'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. First certifications found for {len(rows)} countries.")
