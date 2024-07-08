import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from utils.config import *
from utils.constants import *
from utils.status import *
from utils.utils import build_url


def init_browser(firefox_profile_path: str) -> webdriver.Firefox:
    options: Options = Options()
    if get_headless():
        options.add_argument("--headless")
    options.add_argument("-profile")
    options.add_argument(firefox_profile_path)
    service: Service = Service(GeckoDriverManager().install())
    browser: webdriver.Firefox = webdriver.Firefox(service=service, options=options)
    return browser


def get_channel_id(browser) -> str:
    driver = browser
    driver.get("https://studio.youtube.com")
    time.sleep(2)
    channel_id = driver.current_url.split("/")[-1]
    return channel_id


def upload_video(browser, video_path, title, description, is_for_kids) -> str:
    try:
        title = title[:100]
        description = description[:300]

        driver = browser
        verbose = get_verbose()
        driver.get("https://www.youtube.com/upload")
        FILE_PICKER_TAG = "ytcp-uploads-file-picker"
        file_picker = driver.find_element(By.TAG_NAME, FILE_PICKER_TAG)
        INPUT_TAG = "input"
        file_input = file_picker.find_element(By.TAG_NAME, INPUT_TAG)
        file_input.send_keys(video_path)
        time.sleep(5)
        textboxes = driver.find_elements(By.ID, YOUTUBE_TEXTBOX_ID)
        title_el = textboxes[0]
        description_el = textboxes[-1]
        if verbose:
            info("\t=> Setting title...")
        title_el.click()
        time.sleep(1)
        title_el.clear()
        title_el.send_keys(title)
        if verbose:
            info("\t=> Setting description...")
        try:
            time.sleep(5)
            description_el.click()
            time.sleep(0.5)
            description_el.clear()
            description_el.send_keys(description)
        except:
            warning("Description not clickable, skipping...")
        time.sleep(0.5)
        if verbose:
            info("\t=> Setting `made for kids` option...")

        is_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_MADE_FOR_KIDS_NAME)
        is_not_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_NOT_MADE_FOR_KIDS_NAME)

        if not is_for_kids:
            is_not_for_kids_checkbox.click()
        else:
            is_for_kids_checkbox.click()

        time.sleep(0.5)
        if verbose:
            info("\t=> Clicking next...")
        next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
        next_button.click()
        if verbose:
            info("\t=> Clicking next again...")
        next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
        next_button.click()
        time.sleep(2)
        if verbose:
            info("\t=> Clicking next again...")
        next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
        next_button.click()
        if verbose:
            info("\t=> Setting as public...")
        radio_button = driver.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)
        radio_button[2].click()
        if verbose:
            info("\t=> Clicking done button...")
        done_button = driver.find_element(By.ID, YOUTUBE_DONE_BUTTON_ID)
        done_button.click()
        time.sleep(2)
        if verbose:
            info("\t=> Getting video URL...")
        driver.get(f"https://studio.youtube.com/channel/{get_channel_id(browser)}/videos/short")
        time.sleep(2)
        videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
        first_video = videos[0]
        anchor_tag = first_video.find_element(By.TAG_NAME, "a")
        href = anchor_tag.get_attribute("href")
        if verbose:
            info(f"\t=> Extracting video ID from URL: {href}")
        video_id = href.split("/")[-2]
        url = build_url(video_id)
        if verbose:
            success(f" => Uploaded Video: {url}")
        driver.quit()

        return url
    except:
        browser.quit()
        return ""
