"""
This module provides support for handling metadata
"""

import json
import os
import re
import unicodedata
from typing import Optional

# === Metadata Template ===

video_metadata_template = {
        "title": "",
        "description": "",
        "keywords": [],
        "studio": [],
        "code": "",
        "series": "",
        "model": [],
        "poster": "",
        "path": ""
    }

album_metadata_template = {
    "title": "",
    "description": "",
    "keywords": [],
    "code": "",
    "model": [],
    "studio": "",
    "path": "",
    "poster": "", 
    "imgs": {}
}

img_metadata_template = {
    "path": "",
    "poster": False
}

model_metadata_template = {
    "name": "",
    "real_name": [],
    "studio": [],
    "ID": "",
    "SNS": [],
    "description": "",
    "comments": "",
    "beauty_score": 0,
    "figure_score": 0,
    "leg_score": 0,
    "age": "",
    "poster": "",
}

# === Metadata File Handling ===

def save_metadata(metadata: dict, file_path: Optional[str]) -> None:
    """
    Save metadata to a JSON file.
    
    Args:
        metadata (dict): Metadata dictionary to save.
        file_path (str): Path to the file where metadata will be saved.
    """
    if file_path is None:
        pass
        # raise ValueError("File path cannot be None")
    
    with open(file_path, 'w') as f: # type: ignore
        json.dump(metadata, f, indent=4, ensure_ascii=False)

def load_metadata(file_path: str) -> dict:
    """
    Load metadata from a JSON file.
    
    Args:
        file_path (str): Path to the file from which metadata will be loaded.
    
    Returns:
        dict: Loaded metadata dictionary.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Metadata file {file_path} does not exist")
    
    with open(file_path, 'r') as f:
        return json.load(f)

# === Metadata Functions ===

# 新增：标准化 key 的工具函数
def normalize_key(title: str) -> str:
    """
    标准化 metadata 的 key 用于匹配，例如移除 # 前空格，统一引号，规范大小写等。
    保留如 H-Cup 结构，不将其视为无效片段。
    """
    title = unicodedata.normalize("NFKC", title)
    title = title.strip().lower()
    title = title.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    title = re.sub(r'(?<!\s)#', ' #', title)  # 补空格
    title = re.sub(r'\s+#', '#', title)       # 去空格后统一为紧贴
    title = re.sub(r'[\u200b\u200e\u200f\u202a-\u202e]', '', title)
    title = re.sub(r'\s*-\s*', ' - ', title)
    title = re.sub(r'(?<![a-z])\s+', ' ', title)
    return title

def metadata_generator(metadata_type: str) -> dict:
    """
    Generate metadata based on the specified type and provided attributes.
    
    Args:
        metadata_type (str): Type of metadata to generate ('video', 'album', 'model').
    
    Returns:
        dict: Populated metadata dictionary.
    """
    if metadata_type == "video":
        template = video_metadata_template.copy()
    elif metadata_type == "album":
        template = album_metadata_template.copy()
    elif metadata_type == "model":
        template = model_metadata_template.copy()
    else:
        raise ValueError("Unsupported metadata type")

    return template

def metadata_checker(metadata: dict, metadata_type: str) -> bool:
    """
    Check if the provided metadata dictionary contains all required fields.
    
    Args:
        metadata (dict): Metadata dictionary to check.
        metadata_type (str): Type of metadata ('video', 'album', 'model').
    
    Returns:
        bool: True if all required fields are present, False otherwise.
    """
    if metadata_type == "video":
        required_fields = video_metadata_template.keys()
    elif metadata_type == "album":
        required_fields = album_metadata_template.keys()
    elif metadata_type == "model":
        required_fields = model_metadata_template.keys()
    else:
        raise ValueError("Unsupported metadata type")

    return all(field in metadata and metadata[field] for field in required_fields)

def metatadata_handler(original_metadata: dict, addition_metadata: Optional[dict], **kwargs) -> dict:
    """Handle metadata by updating keys and values.

    Args:
        original_metadata (dict): Base metadata to update.
        addition_metadata (Optional[dict]): Incoming metadata to apply.
        **kwargs: Additional key-value pairs to apply.

    Returns:
        dict: Updated metadata dictionary.
    """
    if addition_metadata is None:
        addition_metadata = {}

    # Overwrite or add all keys from addition_metadata
    for key, value in addition_metadata.items():
        original_metadata[key] = value

    # Overwrite or add all keys from kwargs
    for key, value in kwargs.items():
        original_metadata[key] = value

    return original_metadata

def metadata_sorted(metadata: dict) -> dict:
    """
    Sort metadata dictionary by keys.
    
    Args:
        metadata (dict): Metadata dictionary to sort.
    
    Returns:
        dict: Sorted metadata dictionary.
    """

    return dict(sorted(metadata.items(), key=lambda item: item[0]))

def metadata_merger(original_metadata: dict, addition_metadata: dict) -> dict:
    """
    Merge two metadata dictionaries.
    
    Args:
        original_metadata (dict): Original metadata dictionary.
        addition_metadata (dict): Additional metadata dictionary to merge.
    
    Returns:
        dict: Merged metadata dictionary.
    """
    
    merged_metadata = original_metadata.copy()
    for key, value in addition_metadata.items():
        if key in merged_metadata and isinstance(merged_metadata[key], list) and isinstance(value, list):
            merged_metadata[key].extend(value)
        else:
            merged_metadata[key] = value
    
    return merged_metadata  

if __name__ == "__main__":

    # original_metadata = load_metadata("tyingart_album_metadata_cleaned.json")
    # addition_metadata = load_metadata("tyingart_web_album_metadata_cleaned.json")

    # # 创建标准化后的键映射
    # addition_map = {normalize_key(k): k for k in addition_metadata}

    # for key in list(original_metadata.keys()):
    #     norm_key = normalize_key(key)
    #     if norm_key in addition_map:
    #         matched_key = addition_map[norm_key]
    #         original_metadata[key] = metadata_merger(original_metadata[key], addition_metadata[matched_key])
    #     else:
    #         # 尝试 fallback：去掉 # 后内容再匹配
    #         fallback_key = norm_key.split("#")[0].strip()
    #         for norm_add, real_add in addition_map.items():
    #             if fallback_key == norm_add or fallback_key in norm_add:
    #                 original_metadata[key] = metadata_merger(original_metadata[key], addition_metadata[real_add])
    #                 break

    # # 自动补充缺失字段的条目（不止 code）
    # for key in original_metadata:
    #     if not original_metadata[key].get("code", "").strip():
    #         norm_key = normalize_key(key)
    #         addition_key = addition_map.get(norm_key, None)
    #         if not addition_key:
    #             # 尝试 fallback 模式
    #             fallback_key = norm_key.split("#")[0].strip()
    #             for norm_add, real_add in addition_map.items():
    #                 if fallback_key == norm_add or fallback_key in norm_add:
    #                     addition_key = real_add
    #                     break
    #         if addition_key:
    #             add_entry = addition_metadata.get(addition_key, {})
    #             original_metadata[key] = metadata_merger(original_metadata[key], add_entry)

    # save_metadata(original_metadata, "ty_album_metadata_updated.json")

    # data = load_metadata("ty_album_metadata_updated.json")
    # i = 0
    # for k, v in data.items():
    #     if v["code"] == "":
    #         i += 1
    #         print(f"缺少 code 字段: {k}")
    # print(len(data))
    # print(f"共有 {i} 个条目缺少 code 字段")


    data = load_metadata("model_metadata.json")
    new = {}
    for k, v in data.items():
        new[v['name']] = v
    save_metadata(metadata_sorted(new), "model_metadata_updated.json")