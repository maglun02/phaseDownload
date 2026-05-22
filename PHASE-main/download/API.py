import requests
import os
import asf_search as asf

#check user credentials 
def check_login(username, password):
    try:
        session = asf.ASFSession().auth_with_creds(username, password)
        response = session.get(
            "https://urs.earthdata.nasa.gov/profile",
            timeout=30
        )

        if response.status_code == 200:
            return True

        print("Login failed with status:", response.status_code)
        return False
    
    except Exception as e:
        print("Login failed:", e)   
        return False

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



#using the urls from the first API call to download the files
def download_url(information, username, password):
    #create a session with credentials for download
    session = asf.ASFSession().auth_with_creds(username, password)

    #get the urls from data
    urls = [item["url"] for item in information]

    #path to download folder
    download_folder = os.path.join(
        os.path.dirname(__file__),
        "..",
        "PHASE_Preprocessing",
        "slaves"
        )

    #create folder if it not exist
    os.makedirs(download_folder, exist_ok=True)

    #download using the found url, credentials from session and a path for files to be stored
    asf.download_urls(
        urls=urls,
        path=download_folder,
        session=session

    )

