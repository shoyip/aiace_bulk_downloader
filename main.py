"""
This script uses scraping techniques (i.e. Selenium) in order to bulk download
data from the Meta Data for Good platform. If the name of the dataset and the
time interval of interest are provided, then files are downloaded.

There should also be an .env file in the same folder of the script, containing
the environment variables that define the Meta Data for Good Partner ID
`FBDFG_PID`, the Facebook username `FBDFG_USER`, the Facebook password
`FBDFG_PASS` and the download folder path `DOWNLOAD_FOLDER`.

Last update: 2022-10-08
"""

import os
from pathlib import Path
from time import sleep, time
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta
from collections import namedtuple
import pandas as pd

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains as AC
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

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
country = "Italy (ITA)"

DateAvail = namedtuple("DateAvail", ["element", "date", "available"])

class Dataset():
    def __init__(self, dest_folder):
        # Create a browser instance
        options = Options()
        options.headless = False
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        print(os.path.isdir(dest_folder))
        options.set_preference("browser.download.dir", dest_folder)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        self.browser = Firefox(options=options)
        self.browser.get(starting_url)
    
    def wait_element(self, element):
        WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable(element)
        )
    
    def wait_and_click(self, element):
        self.wait_element(element)
        element.click()
    
    def allow_cookies(self):
        allow_cookies_btn = self.browser \
            .find_element(By.XPATH, "//button[@title='Only allow essential cookies']")
        self.wait_and_click(allow_cookies_btn)
    
    def visit_login(self):
        visit_login_btn = self.browser \
            .find_element(By.LINK_TEXT, "Log In")
        self.wait_and_click(visit_login_btn)

    def fill_field(element, text):
        element.send_keys(text)
    
    def perform_login(self, username, password):
        username_field = self.browser.find_element(By.ID, "email")
        password_field = self.browser.find_element(By.ID, "pass")
        login_btn = self.browser.find_element(By.ID, "loginbutton")
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_btn.click()
    
    def filter_ds(self, search_term, dataset_type=None, country=None, discontinued=True):
        sleep(5)
        discontinued_checkbox = self.browser \
            .find_element(By.XPATH, "//div[text()='Show discontinued datasets']")
        search_field = self.browser \
            .find_element(By.XPATH, "//input[@placeholder='Find datasets by name']")
        dstype_field = self.browser \
            .find_element(By.XPATH, "((//*[text()='Dataset type'])[1]//following::input)[1]")
        country_field = self.browser \
            .find_element(By.XPATH, "((//*[text()='Paese'])[1]//following::input)[1]")
        self.wait_element(discontinued_checkbox)
        self.wait_element(search_field)
        search_field.send_keys(search_term)
        if discontinued:
            discontinued_checkbox.click()
        if dataset_type is not None:
            dstype_field.send_keys(dataset_type)
            dstype_field.send_keys(Keys.RETURN)
        if country is not None:
            country_field.send_keys(country)
            country.send_keys(Keys.RETURN)
    
    def open_dl_dialog(self):
        # should wait for the search result to be ready
        sleep(1)
        open_dl_link = self.browser \
            .find_element(By.XPATH, "//a[text()='Scarica']")
        self.wait_and_click(open_dl_link)
    
    def open_calendar(self):
        calendar_btn = self.browser \
            .find_element(By.XPATH, "(//div[text()='Intervallo di date']//following::span)[1]")
        self.wait_and_click(calendar_btn)

    def scan_visible_dates(self):
        calendar_months_h2 = self.browser \
            .find_elements(By.XPATH, "//h2[contains(@id, 'js_')]")
        availability_arr = []
        for calendar_month_h2 in calendar_months_h2:
            mmyyyy = calendar_month_h2.get_attribute("id") \
                .split("-")[1:]
            yyyy = mmyyyy[1].zfill(4)
            mm = mmyyyy[0].zfill(2)
            days_div = calendar_month_h2 \
                .find_elements(By.XPATH, "..//child::div[@role='button']")
            for day_div in days_div:
                dd = day_div.text.zfill(2)
                date = datetime.fromisoformat(f"{yyyy}-{mm}-{dd}")
                # buttons are disabled (true) if the date is unavailable and viceversa
                avail = False if day_div.get_attribute("aria-disabled") == "true" else True
                availability_arr.append(
                    DateAvail(day_div, date, avail)
                )
        availability_df = pd.DataFrame(availability_arr).set_index("date")
        n_available_dates = len(availability_df.query("available==True"))
        return availability_df, n_available_dates
    
    def scan_all_dates(self):
        total_availability_df_arr = []
        n_available_dates = 1
        while (n_available_dates):
            availability_df, n_available_dates = self.scan_visible_dates()
            total_availability_df_arr.append(availability_df)
            self.goto_prev_month(2)
        total_availability_df = pd.concat(total_availability_df_arr, axis=0)
        available_dates = list(total_availability_df.query("available==True").index)
        self.available_dates = available_dates
        self.available_dates.sort()
        self.total_availability_df = total_availability_df
        return available_dates
    
    def goto_prev_month(self, n):
        # go back in the calendar by n months
        prev_month_btn = self.browser \
            .find_element(By.XPATH, "(//div[text()='Mese precedente']//following::div)[1]")
        for i in range(n):
            prev_month_btn.click()
    
    def send_escape(self):
        AC(self.browser).send_keys(Keys.ESCAPE).perform()

    def choose_date_interval(self, block_size, current_date, next_date):
        # what are the dates in the current view?
        availability_df, _ = self.scan_visible_dates()
        availability_df.loc[current_date].element.click()
        # go back of `block_size` days, is the date still in the view?
        next_date = current_date - timedelta(days=block_size)
        if next_date in availability_df.query("available==True").index:
            # the date is visible, select and click the element
            availability_df.loc[next_date].element.click()
        else:
            # if the date is not visible, there are two options:
            # either the date is in another pane, or the date is not anymore
            # in the scope of the available dates. let's change pane and see.
            self.goto_prev_month(1)
        current_date = next_date
        next_date = current_date - timedelta(days=block_size)
        sleep(.5)
        return availability_df

    def download_iteration(self, block_size):
        self.open_dl_dialog()
        self.open_calendar()
        # starting values of the iteration
        current_date = self.available_dates[-1]
        next_date = current_date - timedelta(days=block_size)
        while (next_date > self.available_dates[0]):
            availability_df = self.choose_date_interval(block_size=block_size,
                current_date=current_date, next_date=next_date)
            update_btn = self.browser \
                .find_element(By.XPATH, "//div[text()='Aggiorna']")
            self.wait_and_click(update_btn)
            download_btn = self.browser \
                .find_element(By.XPATH, "//div[text()='Download files']")
            self.wait_and_click(download_btn)
            sleep(10)
        # in the latter case, we should set the beginning of this dataset
        # time interval to be the last available date (i.e. the smallest)
        last_event = availability_df.loc[self.available_dates[0]]
        last_event.element.click()

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
    ds = Dataset(str(dest_folder.absolute()))
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
    print(f"\nREPORT ({time() - start:.2f} s)\n===============")
    print(f"There are {len(available_dates)} avilable dates between {min(available_dates).strftime('%Y-%m-%d')} and {max(available_dates).strftime('%Y-%m-%d')}\n")
    ds.send_escape()
    ds.send_escape()

    # Given the informations about the cardinality of the dataset, the size of
    # the blocks for the download have to be chosen
    print("Choose the size of the block for the bulk download (choose an integer):")
    block_size = int(input("Your choice: "))
    
    ds.download_iteration(block_size)

if __name__ == "__main__":
    main()