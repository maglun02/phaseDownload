import API
import json
import os
import sys
import asf_search as asf
import functionality

#check login for user
def run_login():
    print("run_login started")
    #get username and password
    login_path = os.path.join(
        os.path.dirname(__file__),
        "login_request.json"
    )

    with open(login_path, "r") as f:
        userInfo = json.load(f)

    username = userInfo.get("username")
    password = userInfo.get("password")

    #check login and save result for matlab
    login_result = {}

    if API.check_login(username, password):
        login_result["status"] = "success"
        print("login ok")
    else:
        login_result["status"] = "failure"
        print("login faild, password or username wrong")
        
    result_path = os.path.join(
        os.path.dirname(__file__),
        "login_result.json"
    )

    with open(result_path, "w") as f:
        json.dump(login_result, f, indent=4)


#run the first API call
def run_search():
    #read data from matlab
    request_data = functionality.read_json()
    params = functionality.build_search_parameters(request_data)
    response = API.build_api_url(params)

    #handel errors
    if response is None:
        print("request faild")
        return
    
    if response.status_code != 200:
        print("API error:", response.status_code)
        print(response.text)
        return
    
    data = response.json()
    print("Number of raw ASF features:", len(data["features"]))

    sampling = request_data.get("sampling")
    if sampling:
        data["features"] = functionality.sampling_rate(
            data["features"],
            sampling.get("rate"),
            sampling.get("unit")
        )

    info = functionality.relevant_info(data)
    
    #retive the best footprint, to get best path, frame and orbit direction
    aoi_lon, aoi_lat = functionality.find_aoi_center(request_data["aoi"])
    best_product = functionality.best_footprint(info["information"], aoi_lon, aoi_lat)

    download_info = {
        "information": [
            {
                "sceneName": product["sceneName"],
                "url": product["url"]
            }
            for product in info["information"]
        ]
    }

    #save all data for later use
    download_data_path = os.path.join(
        os.path.dirname(__file__),
        "download_data.json"
    )

    with open(download_data_path, "w") as f:
        json.dump(download_info, f, indent=4)

    #summary for matlab, containing size, footprint, path and frame 
    products = []

    for product in info["information"]:
        products.append({
            "sceneName": product["sceneName"],
            "size": round(product["size"], 2),
            "size_bytes": product["size_bytes"],
            "pathNumber": product["pathNumber"],
            "frameNumber": product["frameNumber"],
            "flightDirection": product["flightDirection"],
            "footprint": product["footprint"]
        })

    summary = {
        "product_count": info["product_count"],
        "total_size_gb": round(info["total_size_gb"], 2),
        "total_size_bytes": info["total_size_bytes"],
        "best_path": best_product["pathNumber"],
        "best_frame": best_product["frameNumber"],
        "best_direction": best_product["flightDirection"],
        "products": products
    }
    print(summary)

    summary_path = os.path.join(
        os.path.dirname(__file__),
        "search_summary.json"
    )

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)

    for product in info["information"][:5]:
        print(product["sceneName"], "-", round(product["size"], 2), "GB")
    
#if download confirmed, start downloading data
def run_download():
    #get username and password
    login_path = os.path.join(
        os.path.dirname(__file__),
        "login_request.json"
    )

    with open(login_path, "r") as f:
        userInfo = json.load(f)

    username = userInfo.get("username")
    password = userInfo.get("password")
    #get data from json file
    download_data_path = os.path.join(
        os.path.dirname(__file__),
        "download_data.json"
    )

    with open(download_data_path, "r") as f:
        info = json.load(f)

    search_summary_path = os.path.join(
        os.path.dirname(__file__),
        "search_summary.json"
    )

    with open(search_summary_path, "r") as f:
        summary = json.load(f)
    
    #check if download request is valid, if not send problem back to matlab
    compatibility = functionality.check_compatibility(summary["products"])
    if not compatibility["valid"]:
        summary = {
            "status": "invalid",
            "message": "Products are not compatible for PHASE.",
            "compatibility": compatibility
        }

        summary_path = os.path.join(
            os.path.dirname(__file__),
            "search_summary.json"
        )

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        print("Products are not compatible for PHASE.")
        return

    API.download_url(info["information"], username, password)


if __name__ == "__main__":
    mode = sys.argv[1]

    #sepreate if we want to run search, download or username/password check 
    if mode == "search":
        run_search()

    elif mode == "download":
        run_download()

    elif mode == "login":
        run_login()