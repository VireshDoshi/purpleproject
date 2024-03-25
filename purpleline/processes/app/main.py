import glob
import sys
import streamlit as st
import pandas as pd
import requests
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium, folium_static
import json
import haversine as hs
import os
import plotly.express as px
import plotly.graph_objects as go
sys.path.insert(0, '/Users/vdoshi/github-desktop/purpleproject')
from purpleline.constants.stations import Stations  # noqa: E402
from purpleline.helper.helper import get_latest_properties_folder, get_latest_properties_folder_list  # noqa: E402,E501


STATIONS = Stations
STATIONS_LIST = Stations.list()
PROPERTY_EXTRACT_DATE = get_latest_properties_folder()
PROPERTY_EXTRACT_DATES = get_latest_properties_folder_list()
PROPERTY_DISPLAY_LIMIT = 30
ROUTE_DIRECTIONS_KEY = os.getenv('ROUTE_DIRECTIONS_KEY')
ROUTE_DIRECTIONS_HOST = os.getenv('ROUTE_DIRECTIONS_HOST')

feature_groups = {}
float_url = (
    "https://raw.githubusercontent.com/ocefpaf/secoora_assets_map/a250729bbcf2ddd12f46912d36c33f7539131bec/secoora_icons/rose.png"
)


def perfect_starter_family_property_score() -> float:
    """

    A perfect starter family home is defined below.

    1. This is defined by nearest primary school is walking distance
    2. Nearest Mcdonalds is walking distance
    3. The Nearest Elizabeth Line is walking distance
    4. There are more than 3 parks within a 1 mile radius from the property
    5. The swimming pool is less than 1 mile away from the property
    6. There is a nandos within 3 miles away
    7 .The closest Gym is waslking distance
    8. The house has minimum 3 bedrooms
    9. The house has a garden
    10. the house has a driveway
    11. There is a waitrose within 1 mile radius of the property


    What is walking distance? 0.75 miles or less
    Perfect score calculation
    apply a score zero to 1 per check where 1 is perfect
    add all the scores and then divide by the number of checks

    """
    return True


def plot_route_to_landmark(property_id: str, landmark: str, mymap: folium.Map, color: str, station: str, dash_array: str) -> int:
    if  os.path.exists(f'./purpleline/data/distances/{landmark}/{property_id}.json'):
        with open(f'./purpleline/data/distances/{landmark}/{property_id}.json', 'r') as f:
            data = json.loads(f.read())
        try:
            mls = data['features'][0]['geometry']['coordinates']
            time_to_landmark = data['features'][0]['properties']['time']
            time_to_landmark_mins=round(float(time_to_landmark/60))
            points = [(i[1], i[0]) for i in mls[0]]
            # add marker for the start and ending points
            # for point in [points[0], points[-1]]:
            #     folium.Marker(point).add_to(feature_groups[str(station)])
            # add the lines
            folium.PolyLine(points, weight=5, opacity=1, dash_array=f'{dash_array}', color=f'{color}').add_to(feature_groups[str(station)])
            return int(time_to_landmark_mins)
        except KeyError as e:
            print(f'skip plot for {property_id} with {landmark}')
            return 0


def get_directions_response(lat1, long1, lat2, long2, mode='drive'):
    url = "https://route-and-directions.p.rapidapi.com/v1/routing"
    key = ROUTE_DIRECTIONS_KEY
    host = ROUTE_DIRECTIONS_HOST
    headers = {"X-RapidAPI-Key": key, "X-RapidAPI-Host": host}
    qs = {"waypoints": f"{str(lat1)},{str(long1)}|{str(lat2)},{str(long2)}","mode": mode}
    response = requests.request("GET", url, headers=headers, params=qs)
    return response


def mark_poi(station: str, mymap: folium.Map):
    print(f'station===========mark_poi{station}')
    df = pd.read_csv('./purpleline/data/poi.csv',
                     usecols=['station', 'poi', 'Latitude', 'Longitude', 'Link'])
    df = df[(df.station == station)]
    df.columns = ['station', 'poi', 'Latitude', 'Longitude', 'Link']
    for i, row in df.iterrows():
        poi = str(row["poi"])

        popup_html = f"{poi}<br/>"

        iframe = folium.IFrame(html=popup_html)

        # Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=100)

        brands_files = [f for f in os.listdir('./purpleline/data/brands')]
        brands = [x.split('.')[0] for x in brands_files]
        if poi in brands:
            # set the icon
            icon = folium.features.CustomIcon(f'./purpleline/data/brands/{poi}.png',
                                              icon_size=(50, 50))
        else:
            icon = folium.Icon(color='red')

        folium.Marker(location=[row['Latitude'], row['Longitude']],
                      popup=popup, c=row['poi'],
                      icon=icon,
                      tooltip=f'{poi}').add_to(mymap)


def miles_to_meters(miles):
    return miles*1609


def distance_from(loc1, loc2):
    dist = hs.haversine(loc1, loc2, unit=hs.Unit.MILES)
    return round(dist, 2)


def get_closest_station_to_property(prop_loc_lat, prop_loc_lon) -> tuple:
    stations_df = pd.read_csv('./purpleline/data/Elizabeth-line-stations.csv',
                     usecols=['Station', 'Latitude', 'Longitude'])

    stations_df.columns = ['Station', 'latitude', 'longitude']
    stations_df['distance_to_property'] = stations_df.apply(
        lambda row: distance_from([row.latitude, row.longitude],
                                  [prop_loc_lat, prop_loc_lon]), axis=1)
    stations_df.sort_values(by='distance_to_property', inplace=True)
    # print(stations_df.head)
    return (stations_df['Station'].iloc[0], stations_df['distance_to_property'].iloc[0])


def get_closest_landmark_to_property(prop_loc_lat,
                                     prop_loc_lon,
                                     landmark: str) -> tuple:
    landmarks_df = pd.read_csv('./purpleline/data/poi.csv',
                     usecols=['station', 'poi', 'Latitude', 'Longitude', 'Link'])

    landmarks_df.columns = ['station', 'poi', 'Latitude', 'Longitude', 'Link']
    focus_df = landmarks_df.query(f"poi == '{landmark}'")
    focus_df['distance_to_property'] = focus_df.apply(
        lambda row: distance_from([row.Latitude, row.Longitude],
                                  [prop_loc_lat, prop_loc_lon]), axis=1)
    focus_df.sort_values(by='distance_to_property', inplace=True)
    # print(stations_df.head)
    return (focus_df['station'].iloc[0], focus_df['distance_to_property'].iloc[0])


def mark_properties(station: str, mymap: folium.Map, property_extract_date):
    properties = read_property_file(station, property_extract_date)

    df_scores = pd.read_csv('./purpleline/data/perfecthome/generated_scores.csv',
                            usecols=['propertyid', 'walktoschool_score',
                                     'walltomcd_score', 'walktostation_score',
                                     'atleast3bed_score',
                                     'closepool_score', 'waitrosewithin1mile_score',
                                     'nandosnearby_score',
                                     'walktoclosestgym_score',
                                     'atleastthreecloseparks_score',
                                     'score'], dtype=str)
    print(df_scores.head)
    limit_properties = PROPERTY_DISPLAY_LIMIT
    property_count = 0
    feature_groups[str(station)] = folium.FeatureGroup(
        name=station, show=True).add_to(mymap)
    for property in properties:
        # create an iframe pop-up for the marker
        (closest_station, disance_to_property) = get_closest_station_to_property(
            float(property["location"]["latitude"]),
            float(property["location"]["longitude"]))
        (closest_mcdonalds, disance_to_property_mcdonalds) = get_closest_landmark_to_property(
            float(property["location"]["latitude"]),
            float(property["location"]["longitude"]),
            landmark='mcdonalds')
        property_id = str(property["id"])
        propertyTypeFullDesc = str(property["propertyTypeFullDescription"])
        price = str(property["price"]["displayPrices"][0]["displayPrice"])
        main_image = str(property["propertyImages"]["mainImageSrc"])

        # Add each row to the map
        lat = float(property["location"]["latitude"])
        lon = float(property["location"]["longitude"])
        id = str(property["id"])


        # plot the distance to Heathrow
        print(property_id)
        heathrow_time_int = plot_route_to_landmark(property_id=property_id,
                               landmark='heathrow', mymap=mymap, color='green', station=str(station), dash_array='20')
        # Plot ikea routes
        ikea_time_int = plot_route_to_landmark(property_id=property_id,
                               landmark='ikea', mymap=mymap, color='yellow', station=str(station), dash_array='10') 
        # Plot gatwick routes
        gatwick_time_int = plot_route_to_landmark(property_id=property_id,
                               landmark='gatwick', mymap=mymap, color='orange', station=str(station), dash_array='10') 

        popup_html = f"<h4>{propertyTypeFullDesc}</h4>"
        popup_html += f"The closest Elizabeth Line station  is <b>{closest_station}</b> "
        popup_html += f"at just {disance_to_property} Miles away<i>"
        popup_html += f"The closest Mcdonalds is in <b>{closest_mcdonalds}</b> "
        popup_html += f"at just {disance_to_property_mcdonalds} Miles away<i>"
        popup_html +=f"[{property_id}]</i> for this {propertyTypeFullDesc}. At only"
        popup_html += f"<b>Price:</b> {price}<br/>"
        popup_html += f"<h4>it will take {heathrow_time_int} mins to travel to Heathrow by car</h4>"
        popup_html += f"<h4>it will take {ikea_time_int} mins to travel to Ikea by car</h4>"
        popup_html += f"<h4>it will take {gatwick_time_int} mins to travel to Gatwick by car</h4>"

        popup_html += f"<img src='{main_image}' alt='property'>"
        iframe2 = folium.IFrame(html=popup_html, height=400, width=400)

        # Initialise the popup using the iframe
        popup = folium.Popup(iframe2, min_width=300, max_width=600)

        # score = df_scores.query('propertyid == @property_id')['score'].values[0]
        print(property_id)
        try:
            score = df_scores.loc[df_scores.propertyid == property_id,'score'].values[0]
            # print(score.values[0])
            score_str = str(score)
            # score = "100"
            icon = folium.features.CustomIcon(f'./purpleline/data/numicons/{score_str}.png',
                                          icon_size=(50, 50))
        except IndexError:
            icon = folium.Icon(icon='home', prefix='fa')
            print(f'This property doesnt have a perfect score entry {property_id}')

        folium.Marker(location=[lat, lon],
                      popup=popup, c=id,
                      icon=icon,
                      tooltip=f"{propertyTypeFullDesc} for {price}").add_to(
                          feature_groups[str(station)])
        property_count = property_count + 1
        if property_count > limit_properties:
            break


def read_property_file(station: str, property_date) -> json:
    f = open(f"./purpleline/data/properties/{property_date}/{station}.json", "r")
    return json.loads(f.read())


def plot_pie_chart(df_scores: pd, prop_id: int) -> None:
    df_prop = df_scores[df_scores["propertyid"] == prop_id]
    perfect_score = df_prop["score"].values[0]
    print(perfect_score)
    # delete unwanted columns
    df_prop = df_prop.drop(['score', 'propertyid'], axis=1)
    # print(df_prop)

    # transpose (switch columns/rows)
    df_prop = df_prop.transpose(copy=True)
    # reset index
    df_prop.reset_index(inplace=True)
    # use first row of DataFrame as header
    df_prop.columns = df_prop.iloc[0]

    # # delete first row
    # df_prop = df_prop.iloc[1:]
    column_names = ['attribute', 'score']
    df_prop.columns = column_names
    fig2 = go.Figure(data=go.Pie(labels=["walk to school","walk to macdonalds","walk to the station", "has at least 3 bedrooms", "close to a swimming pool", "waitrose is 1 mile away", "nandos is nearyby", "walk to the gym", "at least 3 parks nearby"], values=df_prop['score'], sort=False, hole=.40, showlegend=False))
    fig2.update_traces(textposition='inside', textinfo='label+percent')
    fig2.update_layout(margin=dict(l=20, r=20, t=30, b=0), annotations=[
    dict(
        text=f'<b>{perfect_score}%</b>', 
        x=0.5, y=0.5, 
        font_size=32,
        showarrow=False
        )]
    )
    st.plotly_chart(fig2, use_container_width=True, theme='streamlit')
        
def main():

    @st.cache_data  # 👈 Add the caching decorator
    def load_data(url):
        df = pd.read_csv(url)
        return df

    st.set_page_config(
        page_title="Elizabeth Line Project",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title('Elizabeth Line Project')

    # stations = STATIONS

    # Set the radius to 1 mile
    if "radius" not in st.session_state:
        st.session_state.radius = "1 mile"
    # Set the station to Maidenhead
    if "station" not in st.session_state:
        st.session_state.station = STATIONS.MAIDENHEAD.value.name
        # Set the station to Maidenhead
    if "PROPERTY_EXTRACT_DATE" not in st.session_state:
        st.session_state.PROPERTY_EXTRACT_DATE = PROPERTY_EXTRACT_DATE

    data = {
        "0.1 mile": 0.1,
        "1 mile": 1,
        "2 miles": 2,
        "3 miles": 3
    }

    df_scores = load_data("./purpleline/data/perfecthome/generated_scores.csv")

    df = pd.read_csv('./purpleline/data/Elizabeth-line-stations.csv',
                     usecols=['Station', 'Latitude', 'Longitude'])

    df.columns = ['Station', 'latitude', 'longitude']

    # m = folium.Map(location=[df.latitude.mean(), df.longitude.mean()],
    #                zoom_start=12, control_scale=True)
    session_station = st.session_state.station
    focus_df = df.query("Station == @session_station")

    # Define the folium Map
    m = folium.Map(location=[focus_df.latitude, focus_df.longitude],
                   zoom_start=15, control_scale=True)
    Fullscreen().add_to(m)

    # Loop through each row in the dataframe
    for i, row in df.iterrows():
        # Setup the content of the popup
        iframe = folium.IFrame('Station:' + str(row["Station"]))

        # Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=300)

        # Add each station to the map
        liz_icon = folium.features.CustomIcon('./purpleline/data/icons/liz_icon.png',
                                     icon_size=(59, 48))

        folium.Marker(location=[row['latitude'], row['longitude']],
                      popup=popup, c=row['Station'],
                      icon=liz_icon
                      ).add_to(m)

        # radius is in meters
        radius = miles_to_meters(data[st.session_state.radius])
        folium.Circle([row['latitude'], row['longitude']],
                      radius=radius,
                      color="purple",
                      dash_array='10',
                      fill_opacity=0.02,
                      fill=True,
                      tooltip=folium.Tooltip(text="distance from the station")
                      ).add_to(m)

    for station in STATIONS:
        mark_properties(station.value.name, m, st.session_state.PROPERTY_EXTRACT_DATE)
        mark_poi(station.value.name, m)

    folium.LayerControl().add_to(m)
    st_data = st_folium(m, width=1250, use_container_width=True)

    # st.sidebar.image()
    st.sidebar.selectbox(
        label="What radius do you want to assign?",
        options=("0.1 mile", "1 mile", "2 miles", "3 miles"),
        key="radius"
    )
    st.sidebar.radio(
        label="station",
        options=df.query("Station in @STATIONS_LIST"),
        key="station"
    )
    st.sidebar.radio(
        label="Extraction Date",
        options=PROPERTY_EXTRACT_DATES,
        key="PROPERTY_EXTRACT_DATE"
    )
    st.sidebar.write("Find your perfect home along near the Elizabeth Line. The pefect family home has minumum 3 beds, walkable to schools, parks, mcdonalds, near Nandos and a Swimming pool and near a Waitrose ")

    col1, col2, col3 = st.columns(3)

    with col1:
        # 145297841,10,10,10,10,10,10,7,10,10,78
        plot_pie_chart(df_scores=df_scores, prop_id=145297841)
        st.image('https://media.rightmove.co.uk:443/dir/crop/10:9-16:9/153k/152918/145297841/152918_RX279922_IMG_00_0000_max_476x317.jpeg', caption='78 - Perfectly positioned to enjoy the convenience of Maidenhead town centre and a short walk to Oldfield primary school, this beautiful home has been thoughtfully extended and updated')

        # # Plot the Pie Chart
        # df_prop = df_scores[df_scores["propertyid"] == 145297841]
        # # delete unwanted columns
        # df_prop = df_prop.drop(['score', 'propertyid'], axis=1)
        # # print(df_prop)

        # # transpose (switch columns/rows)
        # df_prop = df_prop.transpose(copy=True)
        # # reset index
        # df_prop.reset_index(inplace=True)
        # # use first row of DataFrame as header
        # df_prop.columns = df_prop.iloc[0]

        # # # delete first row
        # # df_prop = df_prop.iloc[1:]
        # column_names = ['attribute', 'score']
        # df_prop.columns = column_names
        # fig2 = go.Figure(data=go.Pie(labels=["walk to school","walk to macdonalds","walk to the station", "has at least 3 bedrooms", "close to a swimming pool", "waitrose is 1 mile away", "nandos is nearyby", "walk to the gym", "at least 3 parks nearby"], values=df_prop['score'], sort=False, hole=.40, showlegend=False))
        # fig2.update_traces(textposition='inside', textinfo='label+percent')
        # fig2.update_layout(margin=dict(l=20, r=20, t=30, b=0), annotations=[
        # dict(
        #     text='<b>78%</b>', 
        #     x=0.5, y=0.5, 
        #     font_size=32,
        #     showarrow=False
        #     )]
        # )
        # st.plotly_chart(fig2, use_container_width=True, theme='streamlit')


    with col2:
        # 145212074,10,10,10,10,7,10,7,10,10,75
        st.image('https://media.rightmove.co.uk:443/dir/crop/10:9-16:9/225k/224927/145212074/224927_1271621_IMG_00_0000_max_476x317.jpeg', caption='75 - Featuring an impressively large rear garden and 2 garages, this spacious 4 bedroom family home is set at the end of a quiet residential cul-de-sac situated a short distance from Maidenhead town centre')
        plot_pie_chart(df_scores=df_scores, prop_id=145212074)

    with col3:
        # 145244900,10,10,10,10,7,10,10,5,10,73
        st.image('https://media.rightmove.co.uk:443/dir/crop/10:9-16:9/63k/62080/145244900/62080_UK-S-41951_IMG_00_0001_max_476x317.jpeg', caption='73 - Exquisite four-bedroom river-front home')
        plot_pie_chart(df_scores=df_scores, prop_id=145244900)


if __name__ == "__main__":
    main()
