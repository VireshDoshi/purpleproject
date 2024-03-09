import json
import pandas as pd
import haversine as hs
import os


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

    list_files()


if __name__ == "__main__":
    main()
