"""
Quick station_lines.json generator - focuses on major stations only.
Uses smart defaults and manual curation for best results.
"""
import json
from pathlib import Path

def generate_smart_station_lines():
    """Generate station_lines.json with smart defaults and key stations."""
    
    print("Generating smart station_lines.json...")
    
    station_lines_data = {
        "metadata": {
            "version": "2.1",
            "last_updated": "2026-01-27",
            "description": "Curated station lines with smart defaults",
            "coverage": "Major stations + complexes + all PATH"
        },
        
        # PATH stations - all have known routes
        "path_stations": {
            "World Trade Center": ["NWK-WTC"],
            "Exchange Place": ["JSQ-33", "NWK-WTC"],
            "Newport": ["JSQ-33", "HOB-33"],
            "Grove St": ["JSQ-33", "NWK-WTC"],
            "Journal Square": ["JSQ-33", "HOB-33"],
            "Harrison": ["JSQ-33", "NWK-WTC"],
            "Newark Penn Station": ["NWK-WTC"],
            "Christopher Street": ["JSQ-33", "HOB-33"],
            "9th St": ["JSQ-33", "HOB-33"],
            "14th St": ["JSQ-33", "HOB-33"],
            "23rd St": ["JSQ-33", "HOB-33"],
            "33rd St": ["JSQ-33", "HOB-33"],
            "Hoboken": ["HOB-33", "HOB-WTC"]
        },
        
        # Station complexes - merged lines from all constituent stations
        "complexes": {
            "WTC": ["1", "2", "3", "4", "5", "A", "C", "E", "J", "Z", "R", "W"],
            "33rd St": ["B", "D", "F", "M", "N", "Q", "R", "W"],
            "14th St": ["4", "5", "6", "L", "N", "Q", "R", "W"],
            "23rd St": ["F", "M"],
            "Christopher St": ["1"]
        },
        
        # Major MTA hubs and transfer stations
        "mta_stations": {
            # Manhattan - Major Hubs
            "127": ["1", "2", "3", "7", "N", "Q", "R", "W", "S"],  # Times Sq-42 St
            "631": ["4", "5", "6", "L", "N", "Q", "R", "W"],  # 14 St-Union Sq
            "418": ["2", "3", "4", "5", "A", "C", "J", "Z"],  # Fulton St
            "A42": ["1", "2", "3"],  # 96 St (1/2/3)
            "617": ["A", "C", "E"],  # 42 St-Port Authority
            "635": ["7"],  # Grand Central-42 St
            "R01": ["N", "R", "W"],  # Atlantic Av-Barclays
            "D15": ["B", "D", "F", "M"],  # Grand St
            
            # Manhattan - Single line stations
            "A27": ["1"],  # 79 St
            "E01": ["1"],  # WTC Cortlandt
            "142": ["R", "W"],  # Cortlandt St
            "A38": ["A", "C"],  # Chambers St (A/C)
            
            # Express vs Local lines
            "D01": ["B", "D", "Q"],  # 7 Av (B/D/Q)
            "R16": ["N", "Q", "R", "W"],  # Canal St (N/Q/R/W)
            
            # Brooklyn
            "G08": ["G"],  # Metropolitan Av
            "L01": ["L"],  # Bedford Av
            "M01": ["M"],  # Metropolitan Av
            "F01": ["F"],  # Bergen St
            "Q01": ["Q"],  # DeKalb Av
            "J01": ["J", "Z"],  # Marcy Av
            
            # Queens
            "713": ["7"],  # 52 St (7 train)
            "615": ["6"],  # E 149 St
            "M11": ["M"],  # Myrtle Av
            
            # Express stations
            "726": ["7"],  # 34 St-Hudson Yards
            "254": ["3"],  # Junius St
            
            # Staten Island Railway (select stations)
            "S17": ["SIR"],  # Annadale
            "S01": ["SIR"]   # St George
        }
    }
    
    # Save to file
    output_file = Path(__file__).parent / "station_lines.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(station_lines_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"PATH stations: {len(station_lines_data['path_stations'])}")
    print(f"Complexes: {len(station_lines_data['complexes'])}")
    print(f"MTA stations: {len(station_lines_data['mta_stations'])}")
    print(f"Total coverage: {len(station_lines_data['path_stations']) + len(station_lines_data['complexes']) + len(station_lines_data['mta_stations'])} stations")
    print(f"\nOutput saved to: {output_file}")
    print("=" * 60)
    
    print("\nNote: This covers major stations. For unlisted stations,")
    print("the system will fetch lines dynamically from live data.")


if __name__ == "__main__":
    generate_smart_station_lines()
