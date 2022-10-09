from time import sleep, time

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

DateAvail = namedtuple("DateAvail", ["element", "date", "available"])

class Dataset():
    """
    The `Dataset` class serves as the main object in order to interact with the
    **bulk downloader tool**. When it is initiated, a Firefox WebDriver will be
    started in headless mode and the Meta Data for Good webpage will be opened.
    """
    def __init__(self, starting_url: str, dest_folder: str):
        """
        Instantiate a `Dataset` object.

        Parameters
        ----------
        starting_url: str
            URL of the Meta Data for Good webpage
        dest_folder: str
            Path of the destination folder as a string
        """
        options = Options()
        options.headless = True
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", dest_folder)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        self.browser = Firefox(options=options)
        self.browser.get(starting_url)
        self.dest_folder = dest_folder
    
    def wait_element(self, element):
        """
        Wait that an element is ready for interaction.

        Parameters
        ----------
        element: selenium.webdriver.remote.webelement.WebElement
            Element that we are waiting for
        """
        WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable(element)
        )
    
    def wait_and_click(self, element):
        """
        Wait an element and when it is ready, click on it.

        Parameters
        ----------
        element: selenium.webdriver.remote.webelement.WebElement
            Element that we are waiting for
        """
        self.wait_element(element)
        element.click()
    
    def allow_cookies(self):
        """
        Check whether the cookie dialog box has popped up, and in case click the
        accept button.
        """
        try:
            allow_cookies_btn = self.browser \
                .find_element(By.XPATH, "//button[@title='Only allow essential cookies']")
            self.wait_and_click(allow_cookies_btn)
        except:
            pass
    
    def visit_login(self):
        """
        Visit the login page from the starting page.
        """
        visit_login_btn = self.browser \
            .find_element(By.LINK_TEXT, "Log In")
        self.wait_and_click(visit_login_btn)

    def fill_field(element, text):
        """
        Write a string to a text field.

        Parameters
        ----------
        element: selenium.webdriver.remote.webelement.WebElement
            Element of the textfield of type `input`
        text: str
            Text to be written in the field
        """
        element.send_keys(text)
    
    def perform_login(self, username, password):
        """
        Takes username and password as inputs and logs into the Meta Data for
        Good Platform.

        Parameters
        ----------
        username: str
            Username of the Facebook user, usually an email. The user should be
            approved for access to the Meta Data for Good platform, please contact
            the PI if you need this approval.
        password: str
            Password of the Facebook user.
        """
        username_field = self.browser.find_element(By.ID, "email")
        password_field = self.browser.find_element(By.ID, "pass")
        login_btn = self.browser.find_element(By.ID, "loginbutton")
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_btn.click()
    
    def filter_ds(self, search_term: str, dataset_type: str = None,
        country: str = None, discontinued: str = True):
        """
        Once the main page has been loaded, filter the datasets by search term,
        dataset type, country and/or discontinued state of the dataset.

        Parameters
        ----------
        search_term: str
            The search term to be input in the main search text field (i.e.
            *Italy Coronavirus Disease Prevention Map Feb 24 2020 Id*)
        dataset_type: str
            The type of dataset (i.e. *[Discontinued] Movement Between Tiles v1*)
        country: str
            The country of interest (i.e. *Italy (ITA)*)
        discontinued: bool
            Whether you would like to look up also for discontinued datasets. This
            option is defaulted to True, in order to have the widest variety of
            datasets available
        """
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
        """
        Open the download dialog from the search result interface.
        """
        # should wait for the search result to be ready
        sleep(1)
        open_dl_link = self.browser \
            .find_element(By.XPATH, "//a[text()='Scarica']")
        self.wait_and_click(open_dl_link)
    
    def open_calendar(self):
        """
        Open the calendar panel from the download dialog box.
        """
        calendar_btn = self.browser \
            .find_element(By.XPATH, "(//div[text()='Intervallo di date']//following::span)[1]")
        self.wait_and_click(calendar_btn)

    def scan_visible_dates(self) -> tuple[pd.DataFrame, int]:
        """
        Scan visible dates. When using the calendar panel, scan through the
        visible dates and returns a DataFrame object containing informations
        about the dates, and an integer indicating the number of dates that
        have datasets available for download

        Returns
        -------
        availability_df: DataFrame
            DataFrame containing the WebDriver element and the availability state
            for each datum. The DataFrame is indexed by date.
        n_available_dates: int
            The integer number of dates that are available in that calendar view.
        """
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
    
    def scan_all_dates(self) -> list:
        """
        From the calendar panel, check all the available dates.

        Scans through and saves all the available dates, and returns the sorted list
        of available dates.

        Returns
        -------
        available_dates: list
            List of available dates
        """
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
        """
        From the calendar panel, move the view back of `n` months.

        Parameters
        ----------
        n: int
            Integer number of months to go back by
        """
        # go back in the calendar by n months
        prev_month_btn = self.browser \
            .find_element(By.XPATH, "(//div[text()='Mese precedente']//following::div)[1]")
        for i in range(n):
            prev_month_btn.click()
    
    def send_escape(self):
        """
        Send an escape signal to the browser. Useful to get out of dialog boxes.
        """
        AC(self.browser).send_keys(Keys.ESCAPE).perform()

    def choose_date_interval(self, current_date: datetime, next_date: datetime) -> pd.DataFrame:
        """
        From the calendar panel, select (i.e. click) the correct interval of dates
        between `next_date` and `current_date` (where `next_date < current_date`,
        because the scan is performed backwards in time).

        Parameters
        ----------
        current_date: datetime.datetime
            Datetime object of the first date to be selected
        next_date: datetime.datetime
            Datetime object of the second date to be selected

        Returns
        -------
        availability_df: DataFrame
            DataFrame containing the WebDriver element and the availability state
            for each datum. The DataFrame is indexed by date.
        """
        # what are the visible dates?
        availability_df, _ = self.scan_visible_dates()
        # now select the current date and the next date
        try:
            availability_df.loc[current_date].element.click()
            availability_df.loc[next_date].element.click()
        except KeyError:
            self.goto_prev_month(1)
            availability_df, _ = self.scan_visible_dates()
            availability_df.loc[next_date].element.click()
            # I don't know why this should not be selected but it works like this so...
            # availability_df.loc[current_date].element.click()
        return availability_df

    def download_iteration(self, block_size: int):
        """
        This function contains the main function that performs the iteration over
        the blocks and downloads the datasets.

        First of all, it opens another tab containing the download page
        (`about:downloads`) and focuses back to the previous page. Then it opens
        the dialog box, opens the calendar and starts the loop: until the dates
        do not reach the last possible date that can be chosen, this function
        will continue to select the correct date interval, download the dataset,
        wait until the download has been completed and restart with the following
        dataset.

        The check of the completion of the download happens with a polling of the
        previously opened `about:downloads` page.

        Parameters
        ----------
        block_size: int
            Size of the block to be downloaded **in terms of days** (i.e. if I
            choose 14, the method will choose a two weeks interval regardless
            of the number of datasets that incur). It is at the sole discretion
            of the user to choose a reasonable number, since too big of a number
            of datasets will make the website crash and unable to download the
            data.
        """
        start = time()
        # open the download tab
        self.browser.execute_script("window.open('');")
        self.browser.switch_to.window(self.browser.window_handles[1])
        self.browser.get("about:downloads")
        self.browser.switch_to.window(self.browser.window_handles[0])
        # open the download dialog box
        self.open_dl_dialog()
        self.open_calendar()
        # starting values of the iteration
        current_date = self.available_dates[-1]
        next_date = current_date - timedelta(days=block_size)
        while (next_date > self.available_dates[0]):
            print(f"[LOG] Downloading data between {next_date} and {current_date} (time elapsed: {time()-start:.2f} s)...")
            _ = self.choose_date_interval(current_date=current_date, next_date=next_date)
            update_btn = self.browser \
                .find_element(By.XPATH, "//div[text()='Aggiorna']")
            self.wait_and_click(update_btn)
            download_btn = self.browser \
                .find_element(By.XPATH, "//div[text()='Download files']")
            self.wait_and_click(download_btn)

            current_date = next_date
            next_date = current_date - timedelta(days=block_size)
            # print("[DEBUG] Current date:", current_date)
            # print("[DEBUG] Next date:", next_date)
            # now wait for the download to finish
            self.browser.switch_to.window(self.browser.window_handles[1])
            self.dl_check()
            self.browser.switch_to.window(self.browser.window_handles[0])
            self.open_dl_dialog()
            self.open_calendar()
        # in the latter case, we should set the beginning of this dataset
        # time interval to be the last available date (i.e. the smallest)
        self.goto_prev_month(1)
        self.choose_date_interval(current_date, self.available_dates[0])
    
    def dl_check(self):
        """
        Check whether there are active download processes.
        """
        while True:
            download_elements = self.browser.find_elements(By.CSS_SELECTOR, ".download")
            download_states = [bool(download_element.get_attribute("state")) for download_element in download_elements]
            if any(download_states) is False:
                sleep(1)
            else:
                break