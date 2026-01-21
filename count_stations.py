"""Count stations in the current system and check MTA total"""

# Count current stations in app.py
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the MTA_STATIONS dictionary
start = content.find('MTA_STATIONS = {')
end = content.find('\nDUAL_SYSTEM_STATIONS', start)
mta_section = content[start:end]

# Count unique station names (not aliases)
# Each entry is like "station name": [(...), ...]
station_entries = re.findall(r'^\s+"([^"]+)":\s+\[', mta_section, re.MULTILINE)

print(f"Total entries in MTA_STATIONS: {len(station_entries)}")
print(f"(Note: This includes aliases like 'wtc', '72 st', etc.)")

# Count unique stations by looking at actual station names in tuples
station_names = set()
for match in re.findall(r'\("([^"]+)",\s+"[^"]+",\s+"([^"]+)"\)', mta_section):
    stop_id, name = match
    station_names.add(name)

print(f"\nUnique station names: {len(station_names)}")
print(f"\nSample stations:")
for name in sorted(list(station_names))[:20]:
    print(f"  - {name}")

print(f"\n\nMTA SYSTEM FACTS:")
print(f"  - Total MTA subway stations: ~472")
print(f"  - Total stations in our system: {len(station_names)}")
print(f"  - Coverage: {len(station_names)/472*100:.1f}%")
print(f"  - Missing: ~{472 - len(station_names)} stations")
