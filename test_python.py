import json
import pandas as pd
import haversine as hs
import os
from geopy.geocoders import Nominatim
import requests
import glob
from datetime import date

ROUTE_DIRECTIONS_KEY = os.getenv('ROUTE_DIRECTIONS_KEY')
ROUTE_DIRECTIONS_HOST = os.getenv('ROUTE_DIRECTIONS_HOST')


def get_todays_date() -> str:
    return f'{date.today():%Y/%m/%d}'


def get_latest_properties_folder_list() -> list:
    items = glob.iglob('./purpleline/data/properties/202[0-9]/[0-9][0-9]/[0-9][0-9]',
                       recursive=True)
    folderlist = []
    reverse_folders_full = sorted(items, reverse=True)
    for folder in reverse_folders_full:
        split_latest_folder = folder.split("/")
        latest_folder = split_latest_folder[-3:]
        folderlist.append(latest_folder[0] + '/' + latest_folder[1] + '/' + latest_folder[2])
    return folderlist

def get_latest_properties_folder(directory):
    # items = os.listdir(directory)
    items = glob.iglob('./purpleline/data/properties/202[0-9]/[0-9][0-9]/[0-9][0-9]', recursive=True)

    latest_folders = sorted(items, reverse=True)
    split_latest_folder = latest_folders[0].split("/")
    latest_folder = split_latest_folder[-3:]
    return latest_folder[0] + '/' + latest_folder[1] + '/' + latest_folder[2]

def get_lat_long_from_address(address):
    locator = Nominatim(user_agent='myGeocoder')
    location = locator.geocode(address)
    return location.latitude, location.longitude
# example
# address = 'Zeeweg 94, 2051 EC Overveen'
# get_lat_long_from_address(address)
# >>> (52.4013046, 4.5425025)


def get_directions_response(lat1, long1, lat2, long2, mode='drive'):
    url = "https://route-and-directions.p.rapidapi.com/v1/routing"
    key = ROUTE_DIRECTIONS_KEY
    host = ROUTE_DIRECTIONS_HOST
    headers = {"X-RapidAPI-Key": key, "X-RapidAPI-Host": host}
    qs = {"waypoints": f"{str(lat1)},{str(long1)}|{str(lat2)},{str(long2)}","mode": mode}
    response = requests.request("GET", url, headers=headers, params=qs)
    return response


def distance_from(loc1, loc2):
    dist = hs.haversine(loc1, loc2, unit=hs.Unit.MILES)
    return round(dist, 2)


def get_closest_station_to_property(prop_loc_lat, prop_loc_lon) -> tuple:
    stations_df = pd.read_csv('Elizabeth-line-stations.csv',
                     usecols=['Station', 'Latitude', 'Longitude'])

    stations_df.columns = ['Station', 'latitude', 'longitude']
    # stations_df['distance_to_property'] = stations_df.apply(lambda row: row['latitude'] * row['longitude'], axis=1)
    stations_df['distance_to_property'] = stations_df.apply(lambda row: distance_from([row.latitude,row.longitude], [prop_loc_lat,prop_loc_lon]), axis=1)

    stations_df.sort_values(by='distance_to_property', inplace=True)
    # print(stations_df.head)
    return (stations_df['Station'].iloc[0], stations_df['distance_to_property'].iloc[0])
    # print(stations_df['Station'].iloc[0])


def list_files():
    brands_files = [f for f in os.listdir('./brands')]
    brands = [x.split('.')[0] for x in brands_files]
    print(brands)


def main():

    # Read in station data for Maidenhead
    # JSON file
    # f = open('properties/Taplow.json', "r")
    # property_file = json.loads(f.read())

    # for property in property_file:
    #     prop_id = str(property["id"])
    #     (closest_station, disance_to_property) = get_closest_station_to_property(float(property["location"]["latitude"]), 
    #                                      float(property["location"]["longitude"]))
    #     print(f'House:{prop_id} closest station is {closest_station} at a distance of {disance_to_property} Miles' )

    # list_files()
    # address = '3 chalgrove close, maidenhead, SL6 1XN'
    # lat,long = get_lat_long_from_address(address)
    # print(f'lat={lat}, long={long}')

    # response = get_directions_response(51.518667426954124,-0.7226749105747798, 51.473419, -0.491683)
    # print(response.raw)

    folder_list = get_latest_properties_folder_list()
    print(folder_list)

    today = get_todays_date()



if __name__ == "__main__":
    main()
