import json
import sys
import pandas as pd
import haversine as hs
import os
from geopy.geocoders import Nominatim
import requests
# import geojson
import time
sys.path.insert(0, '/Users/vdoshi/github-desktop/purpleproject')
from purpleline.constants.stations import Stations  # noqa: E402
from purpleline.helper.helper import get_latest_properties_folder  # noqa: E402



STATIONS = Stations
ROUTE_DIRECTIONS_KEY = os.getenv('ROUTE_DIRECTIONS_KEY')
ROUTE_DIRECTIONS_HOST = os.getenv('ROUTE_DIRECTIONS_HOST')
PROPERTY_EXTRACT_DATE = get_latest_properties_folder()
PROPERTY_DISPLAY_LIMIT = 2


def get_lat_long_from_address(address):
    locator = Nominatim(user_agent='myGeocoder')
    location = locator.geocode(address)
    return location.latitude, location.longitude


def read_property_file(station: str, property_date) -> json:
    f = open(f"./purpleline/data/properties/{property_date}/{station}.json", "r")
    return json.loads(f.read())


def get_directions_res(lat1, long1, lat2, long2, mode='drive'):
    url = "https://route-and-directions.p.rapidapi.com/v1/routing"
    key = ROUTE_DIRECTIONS_KEY
    host = ROUTE_DIRECTIONS_HOST
    headers = {"X-RapidAPI-Key": key, "X-RapidAPI-Host": host}
    qs = {"waypoints": f"{str(lat1)},{str(long1)}|{str(lat2)},{str(long2)}","mode": mode}  # noqa: E231, E501
    response = requests.request("GET", url, headers=headers, params=qs)
    return response


def get_distances_for_properties(landmark):
    # go through the list of properties in the json file
    limit_properties = PROPERTY_DISPLAY_LIMIT
    property_count = 0

    for station in STATIONS:
        properties = read_property_file(station, PROPERTY_EXTRACT_DATE)
        for property in properties:
            prop_id = str(property["id"])
            prop_lat = float(property["location"]["latitude"])
            prop_lan = float(property["location"]["longitude"])

            df = pd.read_csv('./purpleline/data/poi.csv',
                             usecols=['station', 'poi', 'Latitude', 'Longitude', 'Link'])  # noqa: E501
            df = df[(df.station == 'all')]

            for i, row in df.iterrows():
                landmark_coord = row['Latitude'], row['Longitude']

                # heathrow_coord = 51.473419, -0.491683

            if not os.path.exists(f'./purpleline/data/distances/{landmark}/{prop_id}.json'):
                res = get_directions_res(prop_lat,prop_lan, landmark_coord[0], landmark_coord[1])
                time.sleep(2)
                json_object = json.dumps(res.json())
                with open(f"./purpleline/data/distances/{landmark}/{prop_id}.json", "w") as outfile:
                    outfile.write(json_object)

            property_count = property_count + 1
            if property_count > limit_properties:
                break


def main():
    # response = get_directions_res(51.518667426954124,-0.7226749105747798, 51.473419, -0.491683)
    get_distances_for_properties("ikea")


if __name__ == "__main__":
    main()
