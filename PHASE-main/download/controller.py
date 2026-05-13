import API
import json
import os
import sys

#run the first API call
def run_search():
    #read data from matlab
    data = API.read_json()
    params = API.build_search_parameters(data)
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

    info = API.relevant_info(data)

    #save all data for later use
    download_data_path = os.path.join(
        os.path.dirname(__file__),
        "download_data.json"
    )

    with open(download_data_path, "w") as f:
        json.dump(info, f, indent=4)

    #summary for matlab popup
    summary = {
        "product_count": info["product_count"],
        "total_size_gb": round(info["total_size_gb"], 2)
    }
    print(summary)

    summary_path = os.path.join(
        os.path.dirname(__file__),
        "search_summary.json"
    )

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)

    #print check 
    print("Product count:", info["product_count"])
    print("Total size GB:", info["total_size_gb"])
    print("First 5 products:")

    for product in info["information"][:5]:
        print(product["sceneName"], "-", round(product["size"], 2), "GB")
    
#if download confirmed, start downloading data
def run_download():
    #hardcode username and pasword for now
    
    #get data from json file
    download_data_path = os.path.join(
        os.path.dirname(__file__),
        "download_data.json"
    )

    with open(download_data_path, "r") as f:
        info = json.load(f)

    API.download_url(info["information"], user_name, password)


if __name__ == "__main__":
    mode = sys.argv[1]

    #sepreate if we want to run search or download
    if mode == "search":
        run_search()

    elif mode == "download":
        run_download()