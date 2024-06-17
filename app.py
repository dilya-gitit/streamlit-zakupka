import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import platform
from webdriver_manager.core.os_manager import ChromeType

st.title('米国株価可視化アプリ')

def scrape_and_download():
    url = "https://kaspi.kz/shop/c/categories/"
    if platform.system() == "Windows":
        options = webdriver.ChromeOptions()
        chrome_service = ChromeService(executable_path=ChromeDriverManager().install())
    else:
        options = webdriver.ChromeOptions()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        options.add_argument('--user-agent=' + ua)
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        chrome_service = ChromeService(executable_path=ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    browser = webdriver.Chrome(options=options, service=chrome_service)
    browser.get(url)

    # Example scraping logic - you can customize this to your needs
    page_title = browser.title
    page_source = browser.page_source

    # Saving the page source to a file
    file_path = "page_content.html"
    with open(file_path, "w", encoding='utf-8') as file:
        file.write(page_source)

    browser.quit()

    return page_title, file_path

if st.button('Scrape and Download'):
    st.write('Scraping in progress...')
    page_title, file_path = scrape_and_download()
    st.write(f'Page Title: {page_title}')
    st.write('Scraping done.')

    with open(file_path, "r", encoding='utf-8') as file:
        file_content = file.read()
        st.download_button(
            label="Download Page Content",
            data=file_content,
            file_name="page_content.html",
            mime="text/html"
        )
else:
    st.write('Click the button to scrape the page.')
