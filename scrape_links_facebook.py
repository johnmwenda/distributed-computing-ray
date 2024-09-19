import re

import ray

# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sqlite3
 
import urllib.request

from time import sleep

def setup_driver(link: str):
    # instance of Options class allows
    # us to configure Headless Chrome
    options = Options()
    
    # this parameter tells Chrome that
    # it should be run without UI (Headless)
    # options.add_argument('--headless')

    # initializing webdriver for Chrome with our options
    driver = webdriver.Chrome(options=options)
    
    driver.get(link)

    return driver


def switch_stream_highest_resolution(driver):
    try:
        driver.set_window_size(1008, 1032)
        driver.execute_script("window.scrollTo(0,38)")
        a = ActionChains(driver)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,  ".x1i10hfl > .x1d69dk1")) #This is a dummy element
        )

        print("found modal .. so continuing")
        close_modal = driver.find_element(By.CSS_SELECTOR, ".x1i10hfl > .x1d69dk1")
        print(close_modal)
        if close_modal:
            print("found close modal")
            close_modal.click()

        
        resolution_switch = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,  ".x1rg5ohu > .xuk3077:nth-child(1) .x1b0d499")) #This is a dummy element
        )

        vid_window = driver.find_element(By.CSS_SELECTOR, ".x1ey2m1c:nth-child(4)")
        a.move_to_element(vid_window).perform()
        a.move_to_element(resolution_switch).click().perform()
        res_switch_1 = driver.find_element(By.CSS_SELECTOR, ".x1ypdohk > span:nth-child(3)")
        a.move_to_element(res_switch_1).click().perform()
        res_switch_2 = driver.find_element(By.CSS_SELECTOR, "div:nth-child(2) > .x1i10hfl > .x1ypdohk")
        a.move_to_element(res_switch_2).click().perform()
    except Exception as e:
        print(e)

def get_raw_video_audio_url(driver):
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "myDynamicElement"))
        )
    except Exception as e:
        pass
    finally:
        # Access requests via the `requests` attribute
        requests = list()
        video_sound_urls = set()
        for request in driver.requests:
            if request.response:
                url = re.sub(r'&bytestart=\d*&byteend=\d*\b', '', request.url)
                if request.response.headers['Content-Type'] == 'video/mp4':

                    requests.append(url)
                    # print(
                    #     url,
                    #     request.response.status_code,
                    #     request.response.headers['Content-Type']
                    # )
        
        # reversed to ensure we get correct urls after changing resolution
        for url in reversed(requests):
            video_sound_urls.add(url)
            if len(video_sound_urls) == 2:
                break
    return video_sound_urls
    

@ray.remote
class ScrapeFacebook:
    """Uses selenium to scrape a video from our page. This is mostly a CPU 
    intensive process, so better to use ThreadedActors"""
    def __init__(self, url):
        self.driver = self.setup_driver(url)

    def setup_driver(link: str):
        # instance of Options class allows
        # us to configure Headless Chrome
        options = Options()
        
        # this parameter tells Chrome that
        # it should be run without UI (Headless)
        # options.add_argument('--headless')

        # initializing webdriver for Chrome with our options
        driver = webdriver.Chrome(options=options)
        
        driver.get(link)

        return driver
    
    def setup_db_connection():
        self.conn = sqlite3.connect('./db.db')
        self.cursor = conn.cursor()

    def switch_stream_highest_resolution(self):
        try:
            self.driver.set_window_size(1008, 1032)
            self.driver.execute_script("window.scrollTo(0,38)")
            a = ActionChains(self.driver)
            
            resolution_switch = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,  ".x1rg5ohu > .xuk3077:nth-child(1) .x1b0d499")) #This is a dummy element
            )
            vid_window = self.driver.find_element(By.CSS_SELECTOR, ".x1ey2m1c:nth-child(4)")
            a.move_to_element(vid_window).perform()
            a.move_to_element(resolution_switch).click().perform()
            res_switch_1 = self.driver.find_element(By.CSS_SELECTOR, ".x1ypdohk > span:nth-child(3)")
            a.move_to_element(res_switch_1).click().perform()
            res_switch_2 = self.driver.find_element(By.CSS_SELECTOR, "div:nth-child(2) > .x1i10hfl > .x1ypdohk")
            a.move_to_element(res_switch_2).click().perform()
        except Exception as e:
            print(e)

    
    def scrape_facebook_video(self):
        try:
            element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "myDynamicElement"))
            )
        except Exception as e:
            pass
        finally:
            # Access requests via the `requests` attribute
            requests = list()
            video_sound_urls = set()
            for request in self.driver.requests:
                if request.response:
                    url = re.sub(r'&bytestart=\d*&byteend=\d*\b', '', request.url)
                    if request.response.headers['Content-Type'] == 'video/mp4':

                        requests.append(url)
                        # print(
                        #     url,
                        #     request.response.status_code,
                        #     request.response.headers['Content-Type']
                        # )
            
            # reversed to ensure we get correct urls after changing resolution
            for url in reversed(requests):
                video_sound_urls.add(url)
                if len(video_sound_urls) == 2:
                    break
        
        video_links = tuple(video_sound_urls)
        # store the links in a sqlite database
        # Insert user data into the users table
        self.setup_db_connection()
        self.cursor.execute('INSERT INTO video_urls (url_one, url_two) VALUES (?, ?)', (video_links[0], video_links[1]))
        self.conn.commit()


class FacebookDownloader:
    """Downloads facebook video and audio files concurrently. This is mostly
    IO intensive. Best to use AsyncIO concurrency"""
    pass


driver = setup_driver('https://www.facebook.com/LifeChurchInternationalKasarani/videos/477471041364803')
switch_stream_highest_resolution(driver)
video_audio_urls = get_raw_video_audio_url(driver)
print(video_audio_urls)


# print(''.join(['-'*20]))
# print(video_audio_urls)

# We can also get some information
# about page in browser.
# So let's output webpage title into
# terminal to be sure that the browser
# is actually running. 


# post install docker
# wget https://chromedriver.storage.googleapis.com/113.0.5672.63/chromedriver_linux64.zip
# unzip chromedriver_linux64.zip -d /usr/local/share/chromedriver
# sudo ln -s /usr/local/share/chromedriver/chromedriver /usr/bin/chromedriver

# sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
# sudo bash -c "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list"
# sudo apt -y update
# sudo apt -y install google-chrome-stable
# google-chrome --version  