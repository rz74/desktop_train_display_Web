import httpx
from google.transit import gtfs_realtime_pb2
from mappings import get_path_station_name, get_path_route_name, calculate_minutes_until

def get_station_arrivals(feed, stop_id):
    trains = []
    station_name = get_path_station_name(stop_id)
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip = entity.trip_update
            route_id = trip.trip.route_id if hasattr(trip.trip, 'route_id') else 'PATH'
            for stop_update in trip.stop_time_update:
                if stop_update.stop_id == stop_id:
                    if stop_update.HasField('arrival'):
                        arrival_time = stop_update.arrival.time
                        minutes = calculate_minutes_until(arrival_time)
                        if minutes >= 0:
                            trains.append({'route': route_id, 'route_name': get_path_route_name(route_id), 'minutes': minutes, 'time': arrival_time})
    trains.sort(key=lambda x: x['time'])
    print(f'PATH - {station_name} ({stop_id})')
    print('-' * 60)
    if trains:
        for train in trains[:5]:
            time_str = 'Now' if train['minutes'] == 0 else f"{train['minutes']} min"
            print(f"  [{train['route_name']:20s}] - {time_str}")
        print(f'  Total: {len(trains)} trains')
    else:
        print('  No data')
    print()

def test_path_stations():
    url = 'https://path.transitdata.nyc/gtfsrt'
    try:
        print('Fetching PATH data...')
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        print('=' * 60)
        print('PATH TRAIN - Real-time Test')
        print('=' * 60)
        print()
        for stop_id in ['26734', '26722', '26731', '26730']:
            get_station_arrivals(feed, stop_id)
        print('=' * 60)
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_path_stations()
