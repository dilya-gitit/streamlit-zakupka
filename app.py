import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
"""
## Web scraping on Streamlit Cloud with Selenium"""
def init_webdriver():
    with st.echo():
        @st.cache_resource
        def get_driver():
            return webdriver.Chrome(
                service=Service(
                    ChromeDriverManager(driver_version='125',chrome_type=ChromeType.CHROMIUM).install()
                ),
                options=options,
            )

        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")

        driver = get_driver()
        driver.get("https://kaspi.kz/shop/c/categories/")

        return driver
    

