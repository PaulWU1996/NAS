"""
This module provides spider support for extracting metadata
"""


import requests
import re
import json
from bs4 import BeautifulSoup
from metadata import load_metadata, save_metadata, metadata_sorted, model_metadata_template, video_metadata_template, album_metadata_template, img_metadata_template
import time
import random
from requests.exceptions import RequestException
from functools import wraps
import logging

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"'{func.__name__}' raised an error: {e}", exc_info=True)
            raise
    return wrapper

@log_call
def fetch_with_retry(url, retries=2, delay=5, timeout=5):
    """
    Fetches a URL with retry support.

    Args:
        url (str): URL to fetch.
        retries (int): Number of retry attempts.
        delay (int): Delay between retries (seconds).
        timeout (int): Timeout per request (seconds).

    Returns:
        str or None: HTML content if successful, else None.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"Fetching (attempt {attempt}): {url}")
            res = requests.get(url, timeout=timeout)
            res.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
            return res.text
        except RequestException as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                print(f"Failed to fetch {url} after {retries} attempts.")
                return None
@log_call
def entry_extract_from_page(url: str, keywords:list, max_page: int=100,) -> list:
    """
    Extract entries list from a base URL.

    Args:
        url (str): The base URL to extract entries from.
        keywords (list): Keywords to filter entries. For example, ["/model/"]
        max_page (int): Maximum number of pages to scrape.

    Returns:
        list: A list containing the extracted metadata.
    """
    
    base_url = url + "?page="
    entries = []

    for p in range(max_page):
        page_url = f"{base_url}{p}"
        html = fetch_with_retry(page_url)
        if not html:
            raise ValueError(f"Failed to connect to {page_url}")
        soup = BeautifulSoup(html, 'html.parser')

        for link in soup.find_all("a"):
            href = link.get('href')
            txt = link.text

            for s in keywords:
                if str(href).startswith(s):
                    # print(txt)
                    entries.append(f"{href.lower()}")

    return entries

@log_call
def album_extract_metadata(url: str) -> dict:
    """
    Extract metadata from a given URL.

    Args:
        url (str): The URL to extract metadata from.

    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    html = fetch_with_retry(url)
    if not html:
        raise ValueError(f"Failed to connect to {url}")
    soup = BeautifulSoup(html, 'html.parser')
    metadata = album_metadata_template.copy()

    title_tag = soup.find('meta', attrs={'property': 'og:title'})
    if title_tag and 'content' in title_tag.attrs:
        metadata['title'] = " ".join(title_tag['content'].split()[1:-1])
        metadata['code'] = title_tag['content'].split()[0].split(".")[-1] 
    else: 
        metadata['title'] =""

    description_tag = soup.find('meta', attrs={'name': 'description'})
    if description_tag and 'content' in description_tag.attrs:
        metadata['description'] = description_tag['content']
    else:
        metadata['description'] = ""

    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_tag and 'content' in keywords_tag.attrs:
        metadata['keywords'] = keywords_tag['content'].split(',')
    else:
        metadata['keywords'] = []

    # code_tag = soup.find('meta', attrs={'property': 'og:url'})
    # if code_tag and 'content' in code_tag.attrs:
    #     # Extract the code from the URL
    #     metadata['code'] = code_tag['content'].split('/')[-1].upper()
    # else:
    #     metadata['code'] = ""
    
    # Find the section containing the model info
    model_div = soup.find("div", class_="field-name-taxonomy-vocabulary-2")
    if model_div:
        name_tag = model_div.find("a")
        if name_tag:
            metadata['model'] = name_tag.text.strip()
        else:
            metadata['model'] = ""
    else:
        metadata['model'] = ""

    return metadata

@log_call
def retail_extract_metadata(url: str) -> dict:
    """
    Extract metadata from a retail URL.

    Args:
        url (str): The retail URL to extract metadata from.

    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    html = fetch_with_retry(url)
    if not html:
        raise ValueError(f"Failed to connect to {url}")
    soup = BeautifulSoup(html, 'html.parser')
    metadata = video_metadata_template.copy()

    title_tag = soup.find('meta', attrs={'property': 'og:title'})
    if title_tag and 'content' in title_tag.attrs:
        metadata['title'] = title_tag["content"]#" ".join(title_tag['content'].split()[1:-1]) 
    else: 
        metadata['title'] =""

    description_tag = soup.find('meta', attrs={'name': 'description'})
    if description_tag and 'content' in description_tag.attrs:
        metadata['description'] = description_tag['content']
    else:
        metadata['description'] = ""

    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_tag and 'content' in keywords_tag.attrs:
        metadata['keywords'] = keywords_tag['content'].split(',')
    else:
        metadata['keywords'] = []

    code_tag = soup.find('meta', attrs={'property': 'og:url'})
    if code_tag and 'content' in code_tag.attrs:
        # Extract the code from the URL
        metadata['code'] = code_tag['content'].split('/')[-1].upper()
    else:
        metadata['code'] = ""

    # Step 1: Locate the block with the specific field class
    model_sections = soup.find_all("div", class_="field-name-taxonomy-vocabulary-2")

    for section in model_sections:
        # Step 2: Confirm the label is exactly '出演モデル'
        label = section.find("div", class_="field-label")
        if not label:
            continue
        label_text = label.get_text(strip=True).replace('\u00a0', '')  # remove &nbsp;
        models = []
        if "出演モデル" in label_text:
            # Step 3: Extract all <a> tags inside the section
            model_links = section.find_all("a", href=True)
            models= [a.get_text(strip=True) for a in model_links if a.get_text(strip=True)]
            
    metadata["model"] = models if models else ""
    return metadata

@log_call
def video_extract_metadata(url: str) -> dict:
    """
    Extract metadata from a retail URL.

    Args:
        url (str): The retail URL to extract metadata from.

    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    html = fetch_with_retry(url)
    if not html:
        raise ValueError(f"Failed to connect to {url}")
    soup = BeautifulSoup(html, 'html.parser')
    metadata = video_metadata_template.copy()

    title_tag = soup.find('meta', attrs={'property': 'og:title'})
    if title_tag and 'content' in title_tag.attrs:
        metadata['title'] = title_tag["content"]#" ".join(title_tag['content'].split()[1:-1]) 
    else: 
        metadata['title'] =""

    description_tag = soup.find('meta', attrs={'name': 'description'})
    if description_tag and 'content' in description_tag.attrs:
        metadata['description'] = description_tag['content']
    else:
        metadata['description'] = ""

    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_tag and 'content' in keywords_tag.attrs:
        metadata['keywords'] = keywords_tag['content'].split(',')
    else:
        metadata['keywords'] = []

    code_tag = soup.find('meta', attrs={'property': 'og:url'})
    if code_tag and 'content' in code_tag.attrs:
        # Extract the code from the URL
        metadata['code'] = code_tag['content'].split('/')[-1].upper()
    else:
        # code = metadata["title"].split()[0].lower().split(".")[-1]
        # if code[-1].lower() == "s":
        #     metadata['code'] = code[:-1]
        # else:
        #     metadata['code'] = code
        metadata['code'] = ""

    # Step 1: Locate the block with the specific field class
    model_sections = soup.find_all("div", class_="field-name-taxonomy-vocabulary-2")

    for section in model_sections:
        # Step 2: Confirm the label is exactly '出演モデル'
        label = section.find("div", class_="field-label")
        if not label:
            continue
        label_text = label.get_text(strip=True).replace('\u00a0', '')  # remove &nbsp;
        models = []
        if "モデル" in label_text:
            # Step 3: Extract all <a> tags inside the section
            model_links = section.find_all("a", href=True)
            models= [a.get_text(strip=True) for a in model_links if a.get_text(strip=True)]
            
    metadata["model"] = models if models else ""
    return metadata

@log_call
def model_extract_metadata(url: str) -> dict:
    """
    Extract metadata from a model URL.

    Args:
        url (str): The model URL to extract metadata from.

    Returns:
        dict: A dictionary containing the extracted metadata.
    """
    html = fetch_with_retry(url)
    if not html:
        raise ValueError(f"Failed to connect to {url}")
    soup = BeautifulSoup(html, 'html.parser')

    info = model_metadata_template.copy()
    info["name"] = url.split("/")[-1].title()  # Extract name from URL

    # 假设每个 model 是一个块（你可以按实际包裹结构调整）
    for model_block in soup.select('.group-t-model-info'):
        name_div = model_block.select_one('.field-name-field-model-name')
        name = name_div.get_text(strip=True) if name_div else None


        for label_div in model_block.select('.field-label'):
            label = label_div.get_text(strip=True)
            
            if label == 'Age:':
                next_sibling = label_div.find_next_sibling(text=True)
                info["age"] = next_sibling.strip() if next_sibling else ""
            
            elif label == 'Figure:':
                next_sibling = label_div.find_next_sibling(text=True)
                info["figure"] = next_sibling.strip() if next_sibling else None

        avatar_img = model_block.find_previous("div", class_="field-name-field-model-avatar")
        poster_url = None
        if avatar_img:
            img_tag = avatar_img.find("img")
            if img_tag and img_tag.has_attr("src"):
                poster_url = img_tag["src"].split("?")[0] # 去掉查询参数
                info["poster"] = poster_url
        
        return info

def workflow_spider(website: str,
                    category: str,
                    max_page: int = 50,
                    keywords: list = [],
                    etype: str = "video",
                    output_file: str = "metadata.json"
                    ) -> None:
    """
    Main workflow for the spider to extract entries and metadata.
    
    Args:
        website (str): The base website URL. (Must include http:// or https://)
        category (str): The category to scrape. (Can be a specific path like 'video', 'albums', etc.)
        max_page (int): Maximum number of pages to scrape.
        keywords (list): List of keywords to filter entries. For example, ["/video/"], ["/gallery/], ["product", "retail"].
        etype (str): Type of entry to extract metadata for ('video', 'album', 'model').
    
    Returns:
        None
    
    """
    if website[-1] == "/":
        website = website[:-1]
    url = f"{website}/{category}"
    # Step 1: Extract entries from pages
    entries = entry_extract_from_page(
        url=url,
        keywords=keywords,
        max_page=max_page
    )
    entries = set(entries)  # Remove duplicates
    entries = list(entries)
    
    filter_entries = []
    for entry in entries:
        for keyword in keywords:
            if entry.strip() == keyword:
                filter_entries.append(entry)
    filter_entries = set(filter_entries)  # Remove duplicates
    entries = set(entries) - set(filter_entries)  # Remove filtered entries
    entries = list(entries)

    data = {}
    i = 0
    for entry in entries:
        entry_url = f"{website}/{entry}"
        print(f"Processing entry: {entry_url}")

        # Step 2: Extract metadata based on type
        if etype == "video":
            metadata = video_extract_metadata(entry_url)
        elif etype == "album":
            metadata = album_extract_metadata(entry_url)
        elif etype == "model":
            metadata = model_extract_metadata(entry_url)
        elif etype == "retail":
            metadata = retail_extract_metadata(entry_url)
        else:
            raise ValueError(f"Unsupported entry type: {etype}")
        data[i+1] = metadata
        i += 1
        

    # Step 3: Save metadata to file
    save_metadata(metadata_sorted(data), output_file)
    print(f"Metadata saved to {output_file}") 


if __name__ == "__main__":
    # Example usage
    # workflow_spider(
    #     website="https://tyingart.com/",
    #     category="gallery",
    #     max_page= 35,
    #     keywords=["/gallery/"],
    #     etype="album",
    #     output_file="album_metadata.json"
    # )

    # p = 0
    # page_list = []
    # for p in range(1,12):
    #     page_url = f"https://www.syclub.club/page/{p}?cat&s=%E8%8B%8F%E6%A8%B1"
    #     html = fetch_with_retry(page_url)
    #     if not html:
    #         raise ValueError(f"Failed to connect to {page_url}")
    #     soup = BeautifulSoup(html, 'html.parser')

    #     for link in soup.find_all("a"):
    #         href = link.get('href')
    #         txt = link.text

    #         if str(href).endswith(".html"):
    #             print(f"Found url: {href}")
    #             page_list.append(href)

    # page_list = list(set(page_list))  # Remove duplicates

    # with open("syclub_page_list.txt", "w") as f:
    #     for page in page_list:
    #         f.write(f"{page}\n")

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    with open("syclub_page_list.txt", "r") as f:
        page_list = f.readlines()
    page_list = [page.strip() for page in page_list if page.strip()]

    print(f"Total pages to process: {len(page_list)}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

record = {}
failed_pages = []
connection_failures = []
# 设置登录用 Cookie（注意：必须先访问一个同域页面）
driver.get("https://www.syclub.club")
driver.add_cookie({
    'name': 'wordpress_logged_in_2a29f1f47c6d4e333e26cab932bdbf62',
    'value': 'eagleheart|1755551530|KcHkMIJ0o8IQi5F9xO5P1CxvElqg5ihDzpv2aPhQ4GX|a5504e9c69878e14abf3915a8568e4ed95ef71607429df6cdac5369d347690e4',
    'domain': 'www.syclub.club'
})
for page_url in page_list:
    try:
        driver.get(page_url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"❌ Failed to load page: {page_url} -> {e}")
        connection_failures.append(page_url)
        continue

    video_url = None
    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string and "video_data" in script.string:
            match = re.search(r'video_data\s*=\s*(\[\{.*?\}\]);', script.string)
            if match:
                try:
                    video_data = json.loads(match.group(1))
                    video_url = video_data[0].get("src")
                    break
                except Exception as e:
                    print("⚠️ JSON parse error:", e)

    title_tag = soup.find("title")
    title_text = title_tag.text if title_tag else ""

    if video_url:
        print("🎯 Video URL:", video_url)
    else:
        print("⚠️ Video URL not found.")
        failed_pages.append(page_url)

    if title_text:
        print("📝 Page Title:", title_text)

    if video_url and title_text:
        record[title_text] = video_url
        time.sleep(random.uniform(3, 8))

driver.quit()
save_metadata(record, "syclub_video_metadata.json")

with open("syclub_failed_pages.txt", "w") as f:
    for url in failed_pages:
        f.write(url + "\n")

with open("syclub_connection_failures.txt", "w") as f:
    for url in connection_failures:
        f.write(url + "\n")