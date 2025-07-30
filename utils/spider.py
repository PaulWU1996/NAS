"""
This module provides spider support for extracting metadata
"""


import requests
import re
import json
from bs4 import BeautifulSoup
from metadata import save_metadata
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
    metadata = {}

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
    metadata = {}

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
    metadata = {}

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

    # 假设每个 model 是一个块（你可以按实际包裹结构调整）
    for model_block in soup.select('.group-t-model-info'):
        name_div = model_block.select_one('.field-name-field-model-name')
        name = name_div.get_text(strip=True) if name_div else None

        figure = None

        for label_div in model_block.select('.field-label'):
            label = label_div.get_text(strip=True)
            
            if label == 'Age:':
                next_sibling = label_div.find_next_sibling(text=True)
                age = next_sibling.strip() if next_sibling else None
            
            elif label == 'Figure:':
                next_sibling = label_div.find_next_sibling(text=True)
                figure = next_sibling.strip() if next_sibling else None

        avatar_img = model_block.find_previous("div", class_="field-name-field-model-avatar")
        poster_url = None
        if avatar_img:
            img_tag = avatar_img.find("img")
            if img_tag and img_tag.has_attr("src"):
                poster_url = img_tag["src"].split("?")[0] # 去掉查询参数
                            

        return{
                "name": name,
                "age": age,
                "figure": figure or "",
                "poster": poster_url or "",
            }


if __name__ == "__main__":
    # url = "https://tyingart.com/gallery/001076"
    # url = "https://tyingart.com/product/tac-005"

    # metadata = album_extract_metadata(url)
    # metadata = retail_extract_metadata(url)
    # print(metadata)

    # metadata_dict = {}
    # start = 90
    # end = 1081
    # for i in range(start,end): 

    #     if i < 1043:
    #         url = f"https://tyingart.com/gallery/{i:05d}"
    #     else:
    #         url = f"https://tyingart.com/gallery/{i:06d}"
    #     try:
    #         metadata = album_extract_metadata(url)
    #         metadata_dict[metadata["code"]] = metadata
    #         print(f"Progress: {i}/{end-start} - {metadata['title']}")
    #     except Exception as e:
    #         print(f"Error processing {url}: {e}")
    #         with open("failed_urls.txt", "a") as f:
    #             f.write(f"{url}\n")

    # save_metadata(dict(sorted(metadata_dict.items())), "tyingart_web_album_metadata.json")

    # from metadata import load_metadata, save_metadata

    # retails = load_metadata("retail.json")
    # metadata_dict = {}
    # for code in retails.keys():

    #     if code.startswith("SP-"):
    #         code = "".join(code.split("-"))  # e.g., SP-001 -> SP-001

    #     url1 = f"https://tyingart.com/product/{code}"
    #     url2 = f"https://tyingart.com/retail/{code}"

    #     try:
    #         metadata = retail_extract_metadata(url1)
    #         metadata_dict[metadata["code"]] = metadata
    #         print(f"Processed: {code} - {metadata['title']}")
    #         continue
    #     except Exception as e:
    #         pass

    #     try:
    #         metadata = retail_extract_metadata(url2)
    #         metadata_dict[metadata["code"]] = metadata
    #         print(f"Processed: {code} - {metadata['title']}")
    #         continue
    #     except Exception as e:
    #         pass

    # save_metadata(dict(sorted(metadata_dict.items())), "tyingart_web_retail_metadata.json")

    
    # metadata_dict = {}
    # start = 115# 13
    # end = 116# 292 # 00200 new vol{}s 
    # for i in range(start,end):
    #     if i < 200:
    #         url = f"https://tyingart.com/video/vol{i:03d}s"
    #     else:
    #         url = f"https://tyingart.com/video/{i:05d}"

    #     if i == 115:
    #         url = "https://tyingart.com/video/00115"  # Special case for vol115s

    #     try:
    #         metadata = video_extract_metadata(url)
    #         metadata["code"] = f"VOL-{i:03d}"
    #         metadata_dict[metadata["code"]] = metadata
    #         print(f"Progress: {i}/{end-start} - {metadata['title']}")
    #     except Exception as e:
    #         print(f"Error processing {url}: {e}")
    #         with open("failed_urls.txt", "a") as f:
    #             f.write(f"{url}\n")
                
    # save_metadata(dict(sorted(metadata_dict.items())), "web_video_metadata.json")




    URLPREFIX = "https://tyingart.com/model/"

    from metadata import load_metadata, save_metadata
    metadata = load_metadata("TYINGART_VID_LATEST.json")

    model_list = []
    for key, value in metadata.items():
        models = value["model"]
        for model in models:
            if model not in model_list:
                model_list.append(model)
    model_list = sorted(model_list)

    print(f"Total models: {len(model_list)}")

    metadata_dict = {}

    for model in model_list:
        url = URLPREFIX + model.replace(" ", "-").lower()
        try:
            model_info = model_extract_metadata(url)
    
            print(f"Processed: {model_info['name']}")
            metadata_dict[model_info["name"]] = model_info
        except Exception as e:
            print(f"Error processing {url}: {e}")
            with open("failed_model_urls.txt", "a") as f:
                f.write(f"{url}\n")

    save_metadata(dict(sorted(metadata_dict.items())), "tyingart_model_metadata.json")