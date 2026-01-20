from underground import SubwayFeed
from mappings import get_mta_station_name, get_mta_direction, calculate_minutes_until, MTA_LINES

def get_station_arrivals(feed, stop_id, station_name=None):
    arrivals = []
    if station_name is None:
        station_name = get_mta_station_name(stop_id)
    for entity in feed.entity:
        if hasattr(entity, 'trip_update') and entity.trip_update:
            trip = entity.trip_update
            route_id = trip.trip.route_id
            if route_id not in MTA_LINES:
                continue
            if trip.stop_time_update:
                for stop_update in trip.stop_time_update:
                    if stop_update.stop_id.startswith(stop_id):
                        if hasattr(stop_update, 'arrival') and stop_update.arrival:
                            arrival_time = stop_update.arrival.time
                            minutes = calculate_minutes_until(arrival_time)
                            if minutes >= 0:
                                direction = get_mta_direction(stop_update.stop_id, route_id)
                                arrivals.append({'line': route_id, 'direction': direction, 'minutes': minutes, 'time': arrival_time})
    arrivals.sort(key=lambda x: x['time'])
    next_arrivals = arrivals[:5]
    print(f'MTA - {station_name} ({stop_id})')
    print('-' * 60)
    if next_arrivals:
        for arrival in next_arrivals:
            time_str = 'Now' if arrival['minutes'] == 0 else f"{arrival['minutes']} min"
            print(f"  [{arrival['line']}] {arrival['direction']:25s} - {time_str}")
        print(f'  Total: {len(arrivals)} arrivals')
    else:
        print('  No arrivals')
    print()

def test_mta_stations():
    print('=' * 60)
    print('MTA SUBWAY - Real-time Test')
    print('=' * 60)
    print()
    for feed_name, stop_id, name in [('A', 'A27', 'Fulton St'), ('A', 'A32', '34 St'), ('L', 'L03', '14 St')]:
        try:
            feed = SubwayFeed.get(feed_name)
            get_station_arrivals(feed, stop_id, name)
        except Exception as e:
            print(f'Error: {e}')
    print('=' * 60)

if __name__ == '__main__':
    test_mta_stations()
