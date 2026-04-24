import requests
import secrets
import csv
from collections import defaultdict

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

# Count certifications per date (YYYY-MM-DD)
certs_per_date = defaultdict(int)
for item in all_data:
    raw_date = item.get('certificationDate', '')
    # certificationDate is a full ISO datetime string; keep only the date portion
    date = raw_date[:10] if raw_date else 'unknown'
    certs_per_date[date] += 1

# Sort by date, leaving any 'unknown' entries at the end
sorted_dates = sorted(
    certs_per_date.keys(),
    key=lambda d: (d == 'unknown', d)
)

# Build rows with running cumulative total
rows = []
cumulative = 0
for date in sorted_dates:
    count = certs_per_date[date]
    cumulative += count
    rows.append({'date': date, 'new_certifications': count, 'cumulative_total': cumulative})

with open('cumulative_certs_over_time.csv', 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['date', 'new_certifications', 'cumulative_total'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. {len(rows)} date entries written, {cumulative} total certifications.")
