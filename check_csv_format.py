"""
Check actual station names from MTA CSV to understand naming format.
"""

import requests
import csv
from io import StringIO

url = "http://web.mta.info/developers/data/nyct/subway/Stations.csv"
response = requests.get(url, timeout=30)

csv_data = StringIO(response.text)
reader = csv.DictReader(csv_data)

print("CSV Column Headers:")
print(list(csv_data.readlines()[0].strip().split(',')))
print("\nFirst 20 stations:")
print("="*80)

csv_data = StringIO(response.text)
reader = csv.DictReader(csv_data)

for i, row in enumerate(reader):
    if i >= 20:
        break
    print(f"{row.get('GTFS Stop ID', '')} | {row.get('Stop Name', '')} | {row.get('Daytime Routes', '')}")

# Check for specific stations
print("\n" + "="*80)
print("Searching for specific stations:")
print("="*80)

csv_data = StringIO(response.text)
reader = csv.DictReader(csv_data)

search_terms = ['Times Sq', 'Grand Central', 'Coney Island', 'Flushing', 'Jamaica', 'Astoria', 'Yankee']

for row in reader:
    station_name = row.get('Stop Name', '')
    for term in search_terms:
        if term.lower() in station_name.lower():
            print(f"{row.get('GTFS Stop ID', '')} | {station_name} | {row.get('Daytime Routes', '')}")
