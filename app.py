import streamlit as st
import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- SCAPING FUNCTION ---
def scrape_data(url):
    # 1. Setup Chrome options for headless mode (required for web apps)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 2. Initialize the browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        time.sleep(4) # Wait for initial load
        
        # Optional: Add scrolling logic here if the page requires it
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(3)
        
        # 3. Grab the HTML and parse it
        soup = BeautifulSoup(driver.page_source, "html.parser")
        extracted_data = []
        
        # --- UPDATE THESE CLASSES BASED ON YOUR TARGET WEBSITE ---
        company_cards = soup.find_all("div", class_="YOUR-COMPANY-CARD-CLASS") 
        
        for card in company_cards:
            name_element = card.find("h2", class_="YOUR-COMPANY-NAME-CLASS")
            description_element = card.find("p", class_="YOUR-DESCRIPTION-CLASS")
            
            name = name_element.text.strip() if name_element else "N/A"
            description = description_element.text.strip() if description_element else "N/A"
            
            extracted_data.append({
                "Company Name": name,
                "Description": description
            })
            
        return extracted_data
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []
    finally:
        driver.quit() # Always close the browser!

# --- STREAMLIT UI ---
st.set_page_config(page_title="Directory Scraper", page_icon="🕵️")

st.title("Web Directory Scraper")
st.markdown("Enter the URL of the directory you want to scrape. The app will extract the company names and descriptions into a downloadable CSV.")

# Input field for the URL
target_url = st.text_input("Enter Target URL:", placeholder="https://example.com/directory")

# Button to trigger the scrape
if st.button("Start Scraping"):
    if not target_url:
        st.warning("Please enter a URL first!")
    else:
        with st.spinner("Firing up the browser and scraping data... This might take a few seconds."):
            
            # Run the scraping function
            results = scrape_data(target_url)
            
            if results:
                st.success(f"Successfully extracted {len(results)} companies!")
                
                # Convert to Pandas DataFrame for display and download
                df = pd.DataFrame(results)
                
                # Display the data in an interactive table
                st.dataframe(df, use_container_width=True)
                
                # Create a download button for the CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name="scraped_directory.csv",
                    mime="text/csv",
                )
            else:
                st.info("No data was found. Please check your HTML class names or ensure the page loaded correctly.")
