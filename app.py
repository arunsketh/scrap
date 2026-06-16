import streamlit as st
import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- SCRAPING FUNCTION ---
def scrape_interactive_data(url, card_selector, name_selector, desc_selector, scroll_count, wait_time):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    extracted_data = []
    
    try:
        driver.get(url)
        time.sleep(wait_time)
        
        # Interactive Auto-Scrolling
        if scroll_count > 0:
            status_text = st.empty()
            for i in range(scroll_count):
                status_text.info(f"🔄 Scrolling page... (Step {i+1}/{scroll_count})")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            status_text.empty()
            
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Target elements using UI-provided selectors
        company_cards = soup.select(card_selector)
        
        for card in company_cards:
            # Using CSS selectors allows for much more flexible targeting
            name_element = card.select_one(name_selector) if name_selector else None
            desc_element = card.select_one(desc_selector) if desc_selector else None
            
            name = name_element.text.strip() if name_element else "N/A"
            description = desc_element.text.strip() if desc_element else "N/A"
            
            # Skip empty entries
            if name != "N/A" or description != "N/A":
                extracted_data.append({
                    "Company Name": name,
                    "Description": description
                })
                
        return extracted_data
        
    except Exception as e:
        st.error(f"❌ Scraping failed: {e}")
        return []
    finally:
        driver.quit()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Interactive Scraper", page_icon="⚙️", layout="wide")

st.title("🚀 Interactive Web Directory Scraper")
st.markdown("Customize your scraping targets dynamically, preview the data, and filter results on the fly.")

# --- SIDEBAR: CONTROL CENTER ---
st.sidebar.header("🛠️ Scraper Configuration")

target_url = st.sidebar.text_input(
    "Target URL:", 
    placeholder="https://example.com/directory"
)

with st.sidebar.expander("🎯 HTML Element Selectors", expanded=True):
    st.markdown("[What are CSS Selectors?](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_selectors)")
    card_sel = st.text_input("Parent Card Selector:", value="div.company-card-class", help="The container wrapping each company entry (e.g., 'div.card' or 'li.item')")
    name_sel = st.text_input("Company Name Selector:", value="h2.company-name-class", help="The element inside the card containing the name (e.g., 'h2' or 'span.title')")
    desc_sel = st.text_input("Description Selector:", value="p.description-class", help="The element inside the card containing the text (e.g., 'p' or 'div.text')")

with st.sidebar.expander("⏳ Performance & Scrolling", expanded=False):
    scroll_loops = st.slider("Infinite Scroll Depth:", min_value=0, max_value=20, value=2, help="How many times the scraper should scroll down to load more data.")
    load_delay = st.slider("Initial Page Load Delay (seconds):", min_value=2, max_value=10, value=4, help="Time given for JavaScript elements to load properly.")

start_scrape = st.sidebar.button("⚡ Start Extraction", use_container_width=True)

# --- MAIN PAGE: LOGIC & INTERACTIVE INTERFACE ---
if start_scrape:
    if not target_url:
        st.warning("⚠️ Please provide a target URL in the sidebar configuration first!")
    else:
        with st.spinner("🕵️ Opening background browser and analyzing layout..."):
            raw_results = scrape_interactive_data(
                url=target_url,
                card_selector=card_sel,
                name_selector=name_sel,
                desc_selector=desc_sel,
                scroll_count=scroll_loops,
                wait_time=load_delay
            )
            
            if raw_results:
                # Save data to session state so it persists during user interactions
                st.session_state['scraped_df'] = pd.DataFrame(raw_results)
                st.success(f"🎉 Successfully extracted {len(raw_results)} records!")
            else:
                st.error("❌ No data found. Try inspecting the website elements and adjusting your CSS selectors in the sidebar.")

# --- DYNAMIC INTERACTION ZONE ---
if 'scraped_df' in st.session_state:
    df = st.session_state['scraped_df']
    
    st.write("---")
    st.subheader("🔍 Filter & Explore Extracted Data")
    
    # Live Search Interface
    search_query = st.text_input("⌨️ Live Search (Filters company names or descriptions instantly):", "")
    
    if search_query:
        filtered_df = df[
            df['Company Name'].str.contains(search_query, case=False, na=False) | 
            df['Description'].str.contains(search_query, case=False, na=False)
        ]
    else:
        filtered_df = df

    # Data Presentation Layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"Showing **{len(filtered_df)}** out of **{len(df)}** total items discovered.")
        # Render table with built-in sorting and column resizing capabilities
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
    with col2:
        st.markdown("### 📥 Export Options")
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Current View (CSV)",
            data=csv_data,
            file_name="filtered_directory_export.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        if st.button("🗑️ Clear Cache / Start Over", use_container_width=True):
            del st.session_state['scraped_df']
            st.rerun()
