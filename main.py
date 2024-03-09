import streamlit as st
import pandas as pd

import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium, folium_static
import json
import haversine as hs
import os


STATIONS = ["Maidenhead", "Taplow", "Twyford", "Slough", "Langley", "Reading"]
PROPERTY_EXTRACT_DATE = '2024/03/06'
PROPERTY_DISPLAY_LIMIT = 20
feature_groups = {}
float_url = (
    "https://raw.githubusercontent.com/ocefpaf/secoora_assets_map/a250729bbcf2ddd12f46912d36c33f7539131bec/secoora_icons/rose.png"
)


def mark_poi(station: str, mymap: folium.Map):

    df = pd.read_csv('./data/poi.csv',
                     usecols=['station', 'poi', 'Latitude', 'Longitude', 'Link'])
    df = df[(df.station == station)]
    df.columns = ['station', 'poi', 'Latitude', 'Longitude', 'Link']
    for i, row in df.iterrows():
        poi = str(row["poi"])

        popup_html = f"{poi}<br/>"

        iframe = folium.IFrame(html=popup_html)

        # Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=100)

        brands_files = [f for f in os.listdir('./brands')]
        brands = [x.split('.')[0] for x in brands_files]
        if poi in brands:
            # set the icon
            icon = folium.features.CustomIcon(f'./brands/{poi}.png',
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
    stations_df = pd.read_csv('Elizabeth-line-stations.csv',
                     usecols=['Station', 'Latitude', 'Longitude'])

    stations_df.columns = ['Station', 'latitude', 'longitude']
    stations_df['distance_to_property'] = stations_df.apply(
        lambda row: distance_from([row.latitude, row.longitude],
                                  [prop_loc_lat, prop_loc_lon]), axis=1)
    stations_df.sort_values(by='distance_to_property', inplace=True)
    # print(stations_df.head)
    return (stations_df['Station'].iloc[0], stations_df['distance_to_property'].iloc[0])


def mark_properties(station: str, mymap: folium.Map, property_extract_date):
    properties = read_property_file(station, property_extract_date)
    limit_properties = PROPERTY_DISPLAY_LIMIT
    property_count = 0
    feature_groups[str(station)] = folium.FeatureGroup(
        name=station, show=True).add_to(mymap)
    for property in properties:
        # create an iframe pop-up for the marker
        (closest_station, disance_to_property) = get_closest_station_to_property(
            float(property["location"]["latitude"]),
            float(property["location"]["longitude"]))
        property_id = str(property["id"])
        propertyTypeFullDesc = str(property["propertyTypeFullDescription"])
        price = str(property["price"]["displayPrices"][0]["displayPrice"])
        main_image = str(property["propertyImages"]["mainImageSrc"])
        popup_html = f"The closest Elizabeth Line station  is <b>{closest_station}</b> "
        popup_html += f"at just {disance_to_property} Miles away<i>"
        popup_html +=f"[{property_id}]</i> for this {propertyTypeFullDesc}. At only"
        popup_html += f"<b>Price:</b> {price}<br/>"
        popup_html += f"<img src='{main_image}' alt='property'>"
        iframe2 = folium.IFrame(html=popup_html, height=400, width=400)

        # Initialise the popup using the iframe
        popup = folium.Popup(iframe2, min_width=300, max_width=600)

        # Add each row to the map
        lat = float(property["location"]["latitude"])
        lon = float(property["location"]["longitude"])
        id = str(property["id"])

        folium.Marker(location=[lat, lon],
                      popup=popup, c=id,
                      icon=folium.Icon(icon="home", prefix='fa'),
                      tooltip=f"{propertyTypeFullDesc} for {price}").add_to(
                          feature_groups[str(station)])
        property_count = property_count + 1
        if property_count > limit_properties:
            break


def read_property_file(station: str, property_date) -> json:
    f = open(f"./properties/{property_date}/{station}.json", "r")
    return json.loads(f.read())


def main():
    st.set_page_config(
        page_title="Elizabeth Line Project",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title('Elizabeth Line Project')

    stations = STATIONS

    # Set the radius to 1 mile
    if "radius" not in st.session_state:
        st.session_state.radius = "1 mile"
    # Set the station to Maidenhead
    if "station" not in st.session_state:
        st.session_state.station = "Maidenhead"
        # Set the station to Maidenhead
    if "PROPERTY_EXTRACT_DATE" not in st.session_state:
        st.session_state.PROPERTY_EXTRACT_DATE = "2024/03/06"

    data = {
        "0.1 mile": 0.1,
        "1 mile": 1,
        "2 miles": 2,
        "3 miles": 3
    }

    df = pd.read_csv('Elizabeth-line-stations.csv',
                     usecols=['Station', 'Latitude', 'Longitude'])

    df.columns = ['Station', 'latitude', 'longitude']

    # m = folium.Map(location=[df.latitude.mean(), df.longitude.mean()],
    #                zoom_start=12, control_scale=True)
    session_station = st.session_state.station
    focus_df = df.query("Station == @session_station")

    # Define the folium Map
    m = folium.Map(location=[focus_df.latitude, focus_df.longitude],
                   zoom_start=13, control_scale=True)
    Fullscreen().add_to(m)

    # Loop through each row in the dataframe
    for i, row in df.iterrows():
        # Setup the content of the popup
        iframe = folium.IFrame('Station:' + str(row["Station"]))

        # Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=300)

        # Add each station to the map
        liz_icon = folium.features.CustomIcon('./icons/liz_icon.png',
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
                      fill_opacity=0.2,
                      fill=True,
                      tooltip=folium.Tooltip(text="distance from the station")
                      ).add_to(m)

    for station in stations:
        mark_properties(station, m, st.session_state.PROPERTY_EXTRACT_DATE)
        mark_poi(station, m)

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
        options=df.query("Station in @STATIONS"),
        key="station"
    )
    st.sidebar.radio(
        label="date",
        options=("2024/03/06","2024/03/07","2024/03/08" ),
        key="PROPERTY_EXTRACT_DATE"
    )


if __name__ == "__main__":
    main()
