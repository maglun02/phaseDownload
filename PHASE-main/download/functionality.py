import json
import os

def read_json():
    json_path = os.path.join(os.path.dirname(__file__), "search_request.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    return data

#setting up AOI for URL
def build_aoi(aoi):
    aoi_type = aoi["type"]
    
    if aoi_type == "point":
        lon, lat = aoi["coordinates"]
        return f"POINT({lon} {lat})"
    
    elif aoi_type == "line":
        coords = aoi["coordinates"]
        line_coords = ", ".join(f"{lon} {lat}" for lon, lat in coords)
        return f"LINESTRING({line_coords})"
    
    elif aoi_type in ["polygon", "rectangle"]:
        #close the polygon
        coords = aoi.get("coordinates", aoi.get("corners"))
        polygon_coords = coords + [coords[0]]
        poly_string = ", ".join(f"{lon} {lat}" for lon, lat in polygon_coords)
        return f"POLYGON(({poly_string}))"
    
    else:
        raise ValueError(f"Unsupported AOI type: {aoi_type}")
    
#handling parameters that can have multiple values
def handle_multi_variable(params, asf_name, value):
    if value:
        params[asf_name] = value

#build search parameter for url search
def build_search_parameters(data):
    #import parameters and harcode sentinel-1, hardcoded data just for test
    aoi = data["aoi"]
    start_date = data.get("startDate")
    end_date = data.get("endDate") 
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
        params["start"] = start_date
    if end_date:
        params["end"] = end_date
    handle_multi_variable(params, "polarization", data.get("polarization"))
    handle_multi_variable(params, "processingLevel", data.get("processingLevel"))
    handle_multi_variable(params, "beamMode", data.get("beamMode")) 
    handle_multi_variable(params, "flightDirection", data.get("flightDirection"))
    handle_multi_variable(params, "platform", data.get("subtype"))
    handle_multi_variable(params, "groupID", data.get("groupID"))  
     
    if pathStart and pathEnd:
        params["relativeOrbit"] = f"{pathStart}-{pathEnd}"
    elif pathStart:
        params["relativeOrbit"] = pathStart
    elif pathEnd:
        params["relativeOrbit"] = pathEnd
    
    if frameStart and frameEnd:
        params["frame"] = f"{frameStart}-{frameEnd}"
    elif frameStart:
        params["frame"] = frameStart
    elif frameEnd:
        params["frame"] = frameEnd
    return params

#retriving relevant data for later use
def relevant_info(data):
    features = data["features"]
    results = []
    total_size = 0
    product_count = 0

    #relevant info for each picture and total size off all pictures
    for feature in features:
        props = feature["properties"]
        print(json.dumps(feature["geometry"], indent=2))

        if not props["url"].endswith(".zip"):
            continue
        
        allowed_levels = ["SLC"]
        if props["processingLevel"] not in allowed_levels:
            continue
        
        size_bytes = props["bytes"]
        total_size += size_bytes

        results.append({
        "sceneName": props["sceneName"],
        "url": props["url"],
        "size": props["bytes"] / (1024**3),
        "size_bytes": props["bytes"],
        "pathNumber": props["pathNumber"],
        "frameNumber": props["frameNumber"],
        "footprint": feature["geometry"],
        "flightDirection": props["flightDirection"]
    })

    total_size_gb = total_size / (1024**3)
    product_count = len(results)
    return {
        "information": results,
        "total_size_gb": total_size_gb,
        "total_size_bytes": total_size,
        "product_count" : product_count
    }

#Sampling rate if user do not want all of the pictures
def sampling_rate(information, rate):
    return information[::rate]

#cheking if paths and orbits are the same
def check_compatibility(information):
    #retrieving information from search summary 
    paths = {product["pathNumber"] for product in information}
    frame = {product["frameNumber"] for product in information}
    direction = {product["flightDirection"] for product in information}

    #check if they are the same
    results = {
        "same_path": len(paths) == 1,
        "same_frame": len(frame) == 1,
        "same_direction": len(direction) == 1,
        "paths": list(paths),
        "frames": list(frame),
        "direction": list(direction)
    }

    results["valid"] = (
        results["same_path"]
        and results["same_frame"]
        and results["same_direction"]
    )

    return results
