import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import streamlit as st
import pandas as pd
import csv
import re
import re
import time
from io import BytesIO
import base64
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import zipfile
from io import StringIO

# Define SessionState class to manage session state
class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# Function to clean and process the uploaded Excel file
def get_exc_list(excel_file, search_column_name):
    df = pd.read_excel(excel_file, engine='openpyxl')
    search_queries = df[search_column_name].drop_duplicates().head(2).tolist()  # Adjusted to take only the first 3 unique values
    return search_queries

# Function to scrape product information from the website
def extract_brand(url):
    pattern = r"(?<=shop/p/)(.*?)(?=-)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def next_button(driver):
    xpath = "//li[@class='pagination__el' and text()='Следующая →']"
    pagination_button = driver.find_element(By.XPATH, xpath)
    pagination_button.click()
    time.sleep(1)

def scrape_product(driver, product, products_list):
    ActionChains(driver).click(product).perform()
    driver.implicitly_wait(20)
    open_specs_button = driver.find_element(By.XPATH, "//li[@class='tabs-content__tab null' and text()='Характеристики']")
    open_specs_button.click()
    time.sleep(1)
    spec_list = driver.find_element(By.CLASS_NAME, 'specifications-list')
    spec_list_elements = spec_list.find_elements(By.CLASS_NAME, 'specifications-list__el')
    product_info = {}
    for el_list in spec_list_elements:
        dl_elements = el_list.find_elements(By.CLASS_NAME, 'specifications-list__spec')
        for el in dl_elements:
            terms = el.find_elements(By.CLASS_NAME, 'specifications-list__spec-term-text')
            definitions = el.find_elements(By.CLASS_NAME, 'specifications-list__spec-definition')
            for term, definition in zip(terms, definitions):
                product_info[term.text] = definition.text
    price_element = driver.find_element(By.CLASS_NAME, 'item__price-left-side')
    price_text = (
        price_element.text.strip()
        .replace('Цена\n', '')
        .replace('₸', '')
        .replace(',', '')
        .replace(' ', '')
    ) if price_element else None

    brand = extract_brand(driver.current_url)

    product_info['Price'] = price_text
    product_info['Brand'] = brand

    products_list.append(product_info)

def scrape_page(driver, products_list):
    products = driver.find_elements(By.CLASS_NAME, "item-card")
    for product in products:
        try:
            scrape_product(driver, product, products_list)
        except NoSuchElementException:
            products_list.append({'Price': None, 'Brand': None})
        except Exception as e:
            products_list.append({'Price': None, 'Brand': None})
        finally:
            driver.back()
            WebDriverWait(driver, 20, ignored_exceptions=(NoSuchElementException, StaleElementReferenceException, TimeoutException)).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'item-card'))
            )

def search(driver, query):
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.search-bar__input'))
    )
    search_bar = driver.find_element(By.CSS_SELECTOR, '.search-bar__input')
    search_bar.clear()
    search_bar.send_keys(query)
    search_bar.send_keys(Keys.RETURN)
    time.sleep(2)

def find_num_pages(driver):
    span_elements = driver.find_elements(By.CLASS_NAME, 'search-result__title')
    for span in span_elements:
        span_text = span.text
        match = re.search(r'\((\d+) страницы\)', span_text)
        if match:
            return int(match.group(1))
    return 1

def main_scraping(driver, query):
    products_list = []
    search(driver, query)
    number = find_num_pages(driver)
    WebDriverWait(driver, 20, ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'item-card'))
    )
    for page in range(1, 2):  # Adjusted to scrape only the first page for demonstration
        scrape_page(driver, products_list)
        if page < number:
            next_button(driver)
    return products_list
class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def download_excel(df, filename="output.xlsx"):
    excel_writer = BytesIO()
    df.to_excel(excel_writer, index=False)
    excel_writer.seek(0)
    b64 = base64.b64encode(excel_writer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

"""
## Web scraping on Streamlit Cloud with Selenium"""
def init_webdriver():
    with st.echo():
        @st.cache_resource
        def get_driver():
            return webdriver.Chrome(
                service=Service(
                    ChromeDriverManager(driver_version='120',chrome_type=ChromeType.CHROMIUM).install()
                ),
                options=options,
            )

        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")  # Enable headless mode
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--remote-debugging-port=9222")

        driver = get_driver()
        driver.maximize_window()
        driver.get("https://kaspi.kz/shop/c/categories/")

        return driver
    
def main():
    state = SessionState(search_column_name="", processed=False)

    st.title("Product Scraping and Price Prediction")

    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    
    if uploaded_file is not None:
        search_column_name = st.text_input("Enter the column name to search", "Номенклатура")
        
        if st.button("Process"):
            with st.spinner("Processing..."):
                search_list = get_exc_list(uploaded_file, search_column_name)
                driver = init_webdriver()
                
                all_products = []
                file_contents = {}
                zip_file_path = "generated_products.zip"
                
                # Scraping and generating CSVs
                with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                    for idx, srch in enumerate(search_list):
                        products_list = main_scraping(driver, srch)
                        
                        # Convert products_list to DataFrame
                        df = pd.DataFrame(products_list)
                        
                        # Create CSV filename
                        csv_filename = f'gen_products_{idx + 1}_{srch}.csv'
                        
                        # Write DataFrame to CSV file in memory
                        csv_str = df.to_csv(index=False)
                        
                        # Write CSV file to zip archive
                        zip_file.writestr(csv_filename, csv_str)
                        file_contents[csv_filename] = csv_str

                driver.quit()
                
                st.success("Scraping completed!")

                for file_name, df in file_contents.items():
                    download_link = download_excel(df, filename=f"{file_name}.xlsx")
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.download_button(
                        label=f"Download {file_name}",
                        data=df.to_csv(index=False),
                        file_name=file_name,
                        mime='text/csv',
                        key=file_name  # Ensure each download button has a unique key
                    )
                with open(zip_file_path, 'rb') as f:
                    zip_data = f.read()
                b64_zip = base64.b64encode(zip_data).decode()
                zip_href = f'<a href="data:application/zip;base64,{b64_zip}" download="generated_products.zip">Download ZIP file</a>'
                st.markdown(zip_href, unsafe_allow_html=True)

                with open(zip_file_path, 'rb') as f:
                    zip_data = f.read()
                st.download_button(
                    label="Download All Files as ZIP",
                    data=zip_data,
                    file_name='generated_products.zip',
                    mime='application/zip'
                )


if __name__ == "__main__":
    main()
