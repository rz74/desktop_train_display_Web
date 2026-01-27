import json

with open('coordinate_mapping.json') as f:
    cm = json.load(f)

mta = cm.get('mta', {})

print('723 in mapping:', '723' in mta)
print('901 in mapping:', '901' in mta)

if '723' in mta:
    print('723:', mta['723']['stop_name'])
if '901' in mta:
    print('901:', mta['901']['stop_name'])

# Check if they exist anywhere else
for section in cm.keys():
    if section != 'metadata':
        data = cm[section]
        if isinstance(data, dict):
            if '723' in data:
                print(f'Found 723 in {section}:', data['723'].get('stop_name', 'N/A'))
            if '901' in data:
                print(f'Found 901 in {section}:', data['901'].get('stop_name', 'N/A'))
