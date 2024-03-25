import sys
import asyncio
import json
from json.decoder import JSONDecodeError
from typing import List, TypedDict
from urllib.parse import urlencode
from httpx import AsyncClient, Response
import os
sys.path.insert(0, '/Users/vdoshi/github-desktop/purpleproject')
from purpleline.constants.stations import Stations  # noqa: E402

# LOCATIONS = ["Maidenhead-2", "Taplow-1", "Twyford-0", "Slough-1", "Langley-4", "Reading-0"]
LOCATIONS=Stations.rightmove_list()
PROPERTY_EXTRACT_DATE = '2024/03/23'
RESULTS_PER_PAGE = 24
MIN_BEDS = 3
MAX_BEDS = 6
MAX_DAYS_ADDED = 3
RADIUS = "2.0"
# 1. establish HTTP client with browser-like headers to avoid being blocked
client = AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,lt;q=0.8,et;q=0.7,de;q=0.6",
    },
    follow_redirects=True,
    http2=True,  # enable http2 to reduce block chance
    timeout=30,
)


async def find_locations(query: str) -> List[str]:
    """use rightmove's typeahead api to find location IDs. Returns list of location IDs in most likely order"""
    # rightmove uses two character long tokens so "cornwall" becomes "CO/RN/WA/LL"
    tokenize_query = "".join(c + ("/" if i % 2 == 0 else "") for i, c in enumerate(query.upper(), start=1))
    url = f"https://www.rightmove.co.uk/typeAhead/uknostreet/{tokenize_query.strip('/')}/"
    response = await client.get(url)
    data = json.loads(response.text)
    return [prediction["locationIdentifier"] for prediction in data["typeAheadLocations"]]


async def scrape_search(location_id: str) -> dict:

    def make_url(offset: int) -> str:
        url = "https://www.rightmove.co.uk/api/_search?"
        params = {
            "areaSizeUnit": "sqft",
            "channel": "BUY",  # BUY or RENT
            "currencyCode": "GBP",
            "includeSSTC": "false",
            "index": offset,  # page offset
            "isFetching": "false",
            "locationIdentifier": location_id,  # e.g.: "REGION^61294",
            "numberOfPropertiesPerPage": RESULTS_PER_PAGE,
            "radius": RADIUS,
            "sortType": "6",
            "viewType": "LIST",
            "minBedrooms": MIN_BEDS,
            "maxBedrooms": MAX_BEDS,
            "maxDaysSinceAdded": MAX_DAYS_ADDED
        }
        return url + urlencode(params)

    print(make_url(0))
    first_page = await client.get(make_url(0))
    try:
        first_page_data = json.loads(first_page.content)
        total_results = int(first_page_data['resultCount'].replace(',', ''))
        results = first_page_data['properties']

        other_pages = []
        # rightmove sets the API limit to 1000 properties
        max_api_results = 1000
        for offset in range(RESULTS_PER_PAGE, total_results, RESULTS_PER_PAGE):
            # stop scraping more pages when the scraper reach the API limit
            if offset >= max_api_results:
                break
            other_pages.append(client.get(make_url(offset)))
        for response in asyncio.as_completed(other_pages):
            response = await response
            try:
                data = json.loads(response.text)
                results.extend(data['properties'])
            except JSONDecodeError as e:
                data = {}
                results.extend(data['properties'])
    except JSONDecodeError as e:
            results = {}
    return results


# Example run:
async def run():
    # Creating an empty dictionary
    # myLocations = {}

    # myLocations["Maidenhead"] = "STATION^5951"
    # myLocations["Taplow"] = "STATION%5E9047"
    # myLocations["Twyford"] = "STATION%5E9368"

    # for station, location_id in myLocations.items():
    locations = LOCATIONS
    for location in locations:
        loc_list = location.split("-")
        loc = loc_list[0]
        loc_array = int(loc_list[1])
        location_ids = await find_locations(loc)
        print(f"loc={loc} location_ids={location_ids} location_id={location_ids[loc_array]}")
        if not os.path.exists(f'./purpleline/data/properties/{PROPERTY_EXTRACT_DATE}/{loc}.json'):
            search_results = await scrape_search(location_ids[loc_array])
            json_object = json.dumps(search_results, indent=2)

            if not os.path.exists(f'./purpleline/data/properties/{PROPERTY_EXTRACT_DATE}'):
                os.makedirs(f'./purpleline/data/properties/{PROPERTY_EXTRACT_DATE}')

            with open(f"./purpleline/data/properties/{PROPERTY_EXTRACT_DATE}/{loc}.json", "w") as outfile:
                outfile.write(json_object)


if __name__ == "__main__":
    asyncio.run(run())
