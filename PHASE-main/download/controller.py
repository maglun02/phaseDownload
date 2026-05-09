import API

def run_search():
    data = API.read_json()
    params = API.build_search_parameters(data)
    response = API.build_api_url(params)

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
    print("Product count:", info["product_count"])

    print("Total size GB:", info["total_size_gb"])

    print("First 5 products:")

    for product in info["information"][:5]:

        print(product["sceneName"], "-", round(product["size"], 2), "GB")

if __name__ == "__main__":
    run_search()