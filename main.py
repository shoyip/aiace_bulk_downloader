"""
This script uses scraping techniques (i.e. Selenium) in order to bulk download
data from the Meta Data for Good platform. If the name of the dataset and the
time interval of interest are provided, then files are downloaded.

There should also be an .env file in the same folder of the script, containing
the environment variables that define the Meta Data for Good Partner ID
`FBDFG_PID`, the Facebook username `FBDFG_USER`, the Facebook password
`FBDFG_PASS` and the download folder path `DOWNLOAD_FOLDER`.

Last update: 2022-10-09
"""

import os
from pathlib import Path
from time import time
from dotenv import load_dotenv, find_dotenv
from bulk_downloader import Dataset

# find .env file and load the environment variables
load_dotenv(find_dotenv())

# assign environment variables to python variables
partner_id = os.environ.get("FBDFG_PID")
username = os.environ.get("FBDFG_USER")
password = os.environ.get("FBDFG_PASS")
download_folder = os.environ.get("DOWNLOAD_FOLDER")

starting_url = f"https://partners.facebook.com/data_for_good/data/?partner_id={partner_id}"
ds_choices = ["Italy Coronavirus Disease Prevention Map Feb 24 2020 Id"]
dst_choices = [
    "[Discontinued] Facebook Population (Administrative Regions) v1",
    "[Discontinued] Facebook Population (Tile Level) v1",
    "[Discontinued] Movement Between Administrative Regions v1",
    "[Discontinued] Movement Between Tiles v1",
    "[Discontinued] Colocation"
]

def main():
    print("Welcome to the Meta Data for Good Coronavirus Data Bulk Downloader.")
    print("Please select the dataset of your choice:")
    
    for i, ds_choice in enumerate(ds_choices):
        print(f"[{i}]", ds_choice)

    user_ds_choice = int(input("Your choice: "))

    if (user_ds_choice < len(ds_choices)):
        search_term = ds_choices[user_ds_choice]
    else:
        print("Please enter a valid option.")
        exit()

    print("Please now select the dataset type of your choice:")

    for i, dst_choice in enumerate(dst_choices):
        print(f"[{i}]", dst_choice)
    
    user_dst_choice = int(input("Your choice: "))

    if (user_dst_choice < len(dst_choices)):
        dataset_type = dst_choices[user_dst_choice]
    else:
        print("Please enter a valid option.")
        exit()

    dest_folder = Path(download_folder) / search_term / dataset_type
    dest_folder.mkdir(parents=True, exist_ok=True)

    # Let us define the Dataset object for the dataset that we want to scrape
    ds = Dataset(starting_url, str(dest_folder.absolute()))
    # Let us navigate into the website and log in with our credentials
    start = time()
    print(f"[LOG] Logging in the Meta Data for Good platform... ({time() - start:.2f} s)")
    ds.allow_cookies()
    ds.visit_login()
    ds.allow_cookies()
    ds.perform_login(username=username, password=password)

    # Now we look for the dataset of our interest and open the download
    # dialog box
    print(f"[LOG] Looking up for the desired search term / dataset... ({time() - start:.2f} s)")
    ds.filter_ds(search_term, dataset_type)
    ds.open_dl_dialog()

    # Let us open the calendar and explore the available dates
    print(f"[LOG] Scanning available dates ({time() - start:.2f} s)")
    ds.open_calendar()
    available_dates = ds.scan_all_dates()
    print(f"\nREPORT ({time() - start:.2f} s)\n================")
    print(f"There are {len(available_dates)} avilable dates between {min(available_dates).strftime('%Y-%m-%d')} and {max(available_dates).strftime('%Y-%m-%d')}\n")
    ds.send_escape()
    ds.send_escape()

    # Given the informations about the cardinality of the dataset, the size of
    # the blocks for the download have to be chosen
    print("Choose the size of the block for the bulk download (choose an integer):")
    block_size = int(input("Your choice: "))
    
    # What is the size of the folder?
    start_size = 0
    for e in os.scandir(dest_folder):
        start_size += os.path.getsize(e)

    # Now start iteratively downloading the datasets
    ds.download_iteration(block_size)

    # What is the final size of the folder?
    end_size = 0
    for e in os.scandir(dest_folder):
        end_size += os.path.getsize(e)

    print("DOWNLOAD COMPLETE!")
    print("==================")
    print(f"The data has been saved in {str(dest_folder)}.")
    print(f"{end_size/1024/1024:.0f} MB of data were downloaded in total.")

    ds.browser.quit()

if __name__ == "__main__":
    main()