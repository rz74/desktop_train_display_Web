import csv

# Read the stops.txt to find WTC stops
with open('stops.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print("WTC/Cortlandt stops:")
    for row in reader:
        stop_name = row.get('stop_name', '')
        stop_id = row.get('stop_id', '')
        if 'world trade' in stop_name.lower() or 'cortlandt' in stop_name.lower():
            print(f"{stop_id}: {stop_name}")
