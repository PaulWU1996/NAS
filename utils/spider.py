"""
This module provides spider support for extracting metadata
"""


import requests
import re
import json
from bs4 import BeautifulSoup
from metadata import load_metadata, save_metadata, metadata_sorted, model_metadata_template, video_metadata_template, album_metadata_template, img_metadata_template
import time
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
                    entries.append(f"{s}{txt.lower()}")

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
        category (str): The category to scrape. (Can be a specific path like 'videos', 'albums', etc.)
        max_page (int): Maximum number of pages to scrape.
        keywords (list): List of keywords to filter entries. For example, ["/video/"], ["/gallery/], ["product", "retail"].
        etype (str): Type of entry to extract metadata for ('video', 'album', 'model').
    
    Returns:
        None
    
    """

    url = f"{website}/{category}"
    # Step 1: Extract entries from pages
    entries = entry_extract_from_page(
        url=url,
        keywords=keywords,
        max_page=max_page
    )

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
        else:
            raise ValueError(f"Unsupported entry type: {etype}")
        data[i+1] = metadata
        

    # Step 3: Save metadata to file
    save_metadata(metadata_sorted(data), output_file)
    print(f"Metadata saved to {output_file}") 


if __name__ == "__main__":
    # Example usage
    workflow_spider(
        website="https://example.com",
        category="videos",
        max_page=10,
        keywords=["/video/"],
        etype="video",
        output_file="video_metadata.json"
    )
