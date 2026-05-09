import requests
import os
import json

def read_json():
    json_path = os.path.join(os.path.dirname(__file__), "search_request.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    return data

#setting up AOI for URL
def build_aoi(aoi):
    aoi_type = aoi["type"]
    coords = aoi["coordinates"]

    if aoi_type == "point":
        lon, lat = coords 
        return f"POINT({lon} {lat})"
    
    elif aoi_type == "line":
        line_coords = ", ".join(f"{lon} {lat}" for lon, lat in coords)
        return f"LINESTRING({line_coords})"
    
    else:
        #close the polygon
        polygon_coords = coords + [coords[0]]
        poly_string = ", ".join(f"{lon} {lat}" for lon, lat in polygon_coords)
        return f"POLYGON(({poly_string}))"

def build_search_parameters(data):
    #import parameters and harcode sentinel-1, hardcoded data just for test
    aoi = {
    "type": "polygon",
    "coordinates": [
        [10.10, 63.50],
        [10.70, 63.50],
        [10.70, 63.20],
        [10.10, 63.20]
    ]
    }
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    polarization = data.get("polarization")
    processingLevel = data.get("processingLevel")
    beamMode = data.get("beamMode")
    flightDirection = data.get("flightDirection")
    subtype = data.get("subtype")
    pathStart = data.get("pathStart")
    pathEnd = data.get("pathEnd")
    frameStart = data.get("frameStart")
    frameEnd = data.get("frameEnd")

    params = {
        "dataset": "SENTINEL-1",
        "intersectsWith": build_aoi(aoi),
        "output": "geojson"
    }

    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    if polarization:
        params["polarization"] = polarization
    if processingLevel:
        params["processing"] = processingLevel
    if beamMode:
        params["beam"] = beamMode
    if flightDirection:
        params["flight"] = flightDirection
    if subtype:
        params["subtype"] = subtype
    if pathStart:
        params["pathStart"] = pathStart
    if pathEnd:
        params["pathEnd"] = pathEnd
    if frameStart:
        params["frameStart"] = frameStart
    if frameEnd:
        params["frameEnd"] = frameEnd
    
    return params

#build URL to be send 
def build_api_url(params):
    #base URL where we can add parameters
    base_URL = "https://api.daac.asf.alaska.edu/services/search/param"

    #handeling network errors
    try:
        response = requests.get(base_URL, params=params, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        print("Request faild:", e)
        return None


#retriving relevant data for later use
def relevant_info(data):
    features = data["features"]
    results = []
    total_size = 0
    product_count = 0

    #relevant info for each picture and total size off all pictures
    for feature in features:
        props = feature["properties"]

        size_bytes = props["bytes"]
        total_size += size_bytes

        results.append({
            "sceneName": props["sceneName"],
            "url": props["url"],
            "size": props["bytes"] / (1024**3)
        })
    total_size_gb = total_size / (1024**3)
    product_count = len(results)
    return {
        "information": results,
        "total_size_gb": total_size_gb,
        "product_count" : product_count
    }

#Sampling rate if user do not want all of the pictures
def sampling_rate(information, rate):
    return information[::rate]


#using the urls from the first API call to download the files, need a way to confirme with frontend that the user
#want to download the data or if the file is to big or other sampling rate... but have to wait on frontend first
def download_url(information, username, password):
    for info in information:
        url = info["url"]

        #handeling network errors
        try:
            response = requests.get(url, auth=(username, password), stream=True , timeout=30)
        except requests.exceptions.RequestException as e:
            print("Download faild:", e)
            continue
        
        #handeling API errors
        if response.status_code != 200:
            print("Download error:", response.status_code)
            continue

        #saving file
        filename = info["sceneName"] + ".zip"

        #check if picture is downloaded
        if os.path.exists(filename):
            print(f"Skip {filename}, alredy exists")
            continue

        #downloading file in chunck to make it easier for program 
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

