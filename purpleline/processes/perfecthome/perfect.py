import json
import pandas as pd
import haversine as hs
from glob import glob
from pathlib import Path


class Property(object):
    def __init__(self, property_json) -> None:
        self.beds = property_json["bedrooms"]
        self.latitude = float(property_json["location"]["latitude"])
        self.longitude = float(property_json["location"]["longitude"])


class PerfectHome(object):

    def __init__(self,
                 propertyid,
                 bedrooms,
                 price,
                 main_image,
                 propertyTypeFullDesc,
                 property_extract_date,
                 station,
                 latitude,
                 longitude):
        self.property_extract_date = property_extract_date
        self.station = station
        self.propertyid = propertyid
        self.bedrooms = bedrooms
        self.price = price
        self.main_image = main_image
        self.propertyTypeFullDesc = propertyTypeFullDesc
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        # self.property_obj = self.get_property_info(bedrooms=bedrooms, latitude=latitude,longitude=longitude)
        (self.close_stn_name,
         self.close_stn_dist_to_prop) = self.get_close_stn_to_prop()
        (self.close_pool_name,
         self.close_pool_dist_to_prop) = self.get_close_landmark_to_prop(landmark='pool')
        (self.close_mcd_name,
         self.close_mcd_dist_to_prop) = self.get_close_landmark_to_prop(landmark='mcdonalds')
        (self.close_waitrose_name,
         self.close_waitrose_dist_to_prop) = self.get_close_landmark_to_prop(landmark='waitrose')
        (self.close_nandos_name,
         self.close_nandos_dist_to_prop) = self.get_close_landmark_to_prop(landmark='nandos')
        (self.close_gym_name,
         self.close_gym_dist_to_prop) = self.get_close_landmark_to_prop(landmark='gym')
        (self.close_school_name,
         self.close_school_dist_to_prop) = self.get_close_landmark_to_prop(landmark='school')
        self.walktoschool_score = self.walktoschool_calc()
        self.walltomcd_score = self.walltomcd_calc()
        self.walktostation_score = self.walktostation_calc()
        self.atleastthreecloseparks_score = self.atleastthreecloseparks_calc()
        self.closepool_score = self.closepool_calc()
        self.nandosnearby_score = self.nandosnearby_calc()
        self.walktoclosestgym_score = self.walktoclosestgym_calc()
        self.atleast3bed_score = self.atleast3bed_calc()
        self.waitrosewithin1mile_score = self.waitrosewithin1mile_calc()
        self.score = self.score()

    @classmethod
    def distance_from(self, loc1, loc2):
        dist = hs.haversine(loc1, loc2, unit=hs.Unit.MILES)
        return round(dist, 2)

    def get_close_stn_to_prop(self) -> tuple:
        stations_df = pd.read_csv('./purpleline/data/Elizabeth-line-stations.csv',
                        usecols=['Station', 'Latitude', 'Longitude'])

        stations_df.columns = ['Station', 'latitude', 'longitude']
        stations_df['distance_to_property'] = stations_df.apply(
            lambda row: PerfectHome.distance_from([row.latitude, row.longitude],
                                    [self.latitude, self.longitude]), axis=1)
        stations_df.sort_values(by='distance_to_property', inplace=True)
        return (stations_df['Station'].iloc[0], stations_df['distance_to_property'].iloc[0])

    def get_close_landmark_to_prop(self, landmark: str) -> tuple:
        landmarks_df = pd.read_csv('./purpleline/data/poi.csv',
                                   usecols=['station', 'poi', 'Latitude', 'Longitude', 'Link', 'Brand'])

        landmarks_df.columns = ['station', 'poi', 'Latitude', 'Longitude', 'Link', 'Brand']

        focus_df = landmarks_df.loc[landmarks_df['poi'] == landmark]
        focus_df = focus_df.copy()
        focus_df['distance_to_property'] = focus_df.apply(
            lambda row: PerfectHome.distance_from([row.Latitude, row.Longitude],
                                    [self.latitude, self.longitude]), axis=1)

        focus_df.sort_values(by='distance_to_property', inplace=True)
        # print('+++++++++++++')
        # print(focus_df.head)
        return (focus_df['station'].iloc[0], focus_df['distance_to_property'].iloc[0])


    def walktoschool_calc(self):
        if self.close_school_dist_to_prop < 1.0:
            return 10
        elif self.close_school_dist_to_prop > 1.0 and self.close_school_dist_to_prop < 1.5:
            return 7
        elif self.close_school_dist_to_prop > 1.5 and self.close_school_dist_to_prop < 2.0:
            return 5
        else:
            return 1

    def walltomcd_calc(self):
        if self.close_mcd_dist_to_prop < 1.0:
            return 10
        elif self.close_mcd_dist_to_prop > 1.0 and self.close_mcd_dist_to_prop < 1.5:
            return 7
        elif self.close_mcd_dist_to_prop > 1.5 and self.close_mcd_dist_to_prop < 2.0:
            return 5
        else:
            return 1

    def walktostation_calc(self):
        # less than a mile away is walking distance
        if self.close_stn_dist_to_prop < 1.0:
            return 10
        elif self.close_stn_dist_to_prop > 1.0 and self.close_stn_dist_to_prop < 1.5:
            return 7
        elif self.close_stn_dist_to_prop > 1.5 and self.close_stn_dist_to_prop < 2.0:
            return 5
        else:
            return 1

    def waitrosewithin1mile_calc(self):
        # less than a mile away is walking distance
        if self.close_waitrose_dist_to_prop < 1.0:
            return 10
        else:
            return 0

    def score(self) -> int:
        return (int(self.walktoschool_score +
                    self.walltomcd_score +
                    self.walktostation_score +
                    self.atleast3bed_score +
                    self.closepool_score +
                    self.waitrosewithin1mile_score +
                    self.nandosnearby_score +
                    self.walktoclosestgym_score +
                    self.atleastthreecloseparks_score
                    / 9))

    def get_property_info(self) -> Property:
        f = open(f"./purpleline/data/properties/{self.property_extract_date}/{self.station}.json", "r")
        data = json.loads(f.read())
        fil_data = [x for x in data if x['id'] in [self.propertyid]][0]
        return Property(fil_data)

    def atleast3bed_calc(self) -> int:
        if self.bedrooms < 2:
            return 1
        elif self.bedrooms in [2]:
            return 3
        else:
            return 10

    def closepool_calc(self) -> int:
        if self.close_pool_dist_to_prop < 1.0:
            return 10
        elif self.close_pool_dist_to_prop > 1.0 and self.close_pool_dist_to_prop < 1.5:
            return 7
        elif self.close_pool_dist_to_prop > 1.5 and self.close_pool_dist_to_prop < 2.0:
            return 5
        else:
            return 1

    def nandosnearby_calc(self) -> int:
        if self.close_nandos_dist_to_prop < 1.0:
            return 10
        elif self.close_nandos_dist_to_prop > 1.0 and self.close_nandos_dist_to_prop < 1.5:
            return 7
        elif self.close_nandos_dist_to_prop > 1.5 and self.close_nandos_dist_to_prop < 2.0:
            return 5
        else:
            return 1

    def walktoclosestgym_calc(self) -> int:
        if self.close_gym_dist_to_prop < 1.0:
            return 10
        elif self.close_gym_dist_to_prop > 1.0 and self.close_gym_dist_to_prop < 1.5:
            return 5
        elif self.close_gym_dist_to_prop > 1.5 and self.close_gym_dist_to_prop < 2.0:
            return 3
        else:
            return 0

    def atleastthreecloseparks_calc(self) -> int:
        landmarks_df = pd.read_csv('./purpleline/data/poi.csv',
                            usecols=['station', 'poi', 'Latitude', 'Longitude', 'Link', 'Brand'])

        landmarks_df.columns = ['station', 'poi', 'Latitude', 'Longitude', 'Link', 'Brand']

        focus_df = landmarks_df.loc[landmarks_df['poi'] == 'park']
        focus_df = focus_df.copy()
        focus_df['distance_to_property'] = focus_df.apply(
            lambda row: PerfectHome.distance_from([row.Latitude, row.Longitude],
                                    [self.latitude, self.longitude]), axis=1)

        focus_df.sort_values(by='distance_to_property', inplace=True)
        # print('+++++++++++++')
        # print(focus_df.head)
        close_park_count = 0

        for park in range(1, 4):
            if focus_df['distance_to_property'].iloc[0] < 1.0:
                close_park_count = close_park_count + 1
        # print(close_park_count)
        if close_park_count == 3:
            return 10
        else:
            return 0

    def perfectScoreDataRow(self):
        return f'{self.propertyid},' \
               f'{self.bedrooms},' \
               f'{self.price},' \
               f'{self.latitude},' \
               f'{self.longitude},' \
               f'{self.property_extract_date},' \
               f'{self.main_image},' \
               f'{self.propertyTypeFullDesc},' \
               f'{self.walktoschool_score},{self.walltomcd_score},' \
               f'{self.walktostation_score},{self.atleast3bed_score},' \
               f'{self.closepool_score},{self.waitrosewithin1mile_score},' \
               f'{self.nandosnearby_score},' \
               f'{self.walktoclosestgym_score},' \
               f'{self.atleastthreecloseparks_score},' \
               f'{self.score}'


# PROPERTY_EXTRACT_DATE = '2024/03/23'
PROPERTY_EXTRACT_DATE = '**/**/**'
header = 'propertyid,bedrooms,price,latitude,longitude,propextractdate,mainimage,propertytypefulldesc,walktoschool_score,walltomcd_score,walktostation_score,atleast3bed_score,closepool_score,waitrosewithin1mile_score,nandosnearby_score,walktoclosestgym_score,atleastthreecloseparks_score,score'

# this finds our json files
listing = glob('./purpleline/data/properties/' + PROPERTY_EXTRACT_DATE + '/*.json')
# print(listing.count)

# json_files = [pos_json for pos_json in listing if pos_json.endswith('.json')]

property_df = pd.DataFrame(columns=['propertyid',
                                    'bedrooms',
                                    'price',
                                    'main_image',
                                    'propertyTypeFullDesc',
                                    'latitude',
                                    'longitude',
                                    'station',
                                    'prop_extract_date'])
property_df["propertyid"] = pd.Series([], dtype=object)

# we need both the json and an index number so use enumerate()
index = 0
for js in listing:
    with open(js) as json_file:
        json_text = json.load(json_file)
        fil_data = [x for x in json_text]
        for data in fil_data:
            # print(json_file.name)
            propertyid = data["id"]
            bedrooms = data["bedrooms"]
            price = str(data["price"]["amount"])
            main_image = str(data["propertyImages"]["mainImageSrc"])
            propertyTypeFullDesc = str(data["propertyTypeFullDescription"])
            latitude = data["location"]["latitude"]
            longitude = data["location"]["longitude"]
            station = Path(json_file.name).stem
            prop_extract_date = str(Path(json_file.name).parts[3] + '/' + Path(json_file.name).parts[4] + '/' + Path(json_file.name).parts[5])
            # bathrooms = data["bathrooms"]
            # here I push a list of data into a pandas DataFrame at row given by 'index'
            property_df.loc[index] = [propertyid,
                                      bedrooms,
                                      price,
                                      main_image,
                                      propertyTypeFullDesc,
                                      latitude,
                                      longitude,
                                      station,
                                      prop_extract_date]
            index = index + 1


# Remove duplicate entries based on propertyid
# property_df = property_df.drop_duplicates('propertyid', keep='last')
property_df = property_df.sort_values(['propertyid'], ascending = [True]).drop_duplicates(['propertyid']).reset_index(drop=True)
# now that we have the pertinent json data in our DataFrame let's look at it
print(property_df)

with open("./purpleline/data/perfecthome/generated_scores.csv", "w") as scoresfile:
    # Writing data to a file
    scoresfile.write(header + '\n')
    # loop through the rows using iterrows()
    for index, row in property_df.iterrows():
        print(row['propertyid'])
        perfectscore = PerfectHome(row['propertyid'],
                                   row['bedrooms'],
                                   row['price'],
                                   row['main_image'],
                                   row['propertyTypeFullDesc'],
                                   row['prop_extract_date'],
                                   row['station'],
                                   row['latitude'],
                                   row['longitude']
                                   )
        scoresfile.write(perfectscore.perfectScoreDataRow() + '\n')


