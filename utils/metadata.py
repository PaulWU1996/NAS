"""
This module provides support for handling metadata
"""

import json
import os
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
    
    with open(file_path, 'w') as f:
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
    
    # model_metadata = load_metadata("tyingart_model_metadata.json")

    # for model_name, metadata in model_metadata.items():
    #     template = metadata_generator("model")
    #     model_metadata[model_name] = metadata_merger(template, metadata)
    #     model_metadata[model_name]["studio"] = ["TYINGART"] 

    # save_metadata(model_metadata, "TYINGART_MODEL_LATEST.json")

    # directory = "/Volumes/PRIVATE_COLLECTION/林韵瑜（Moon）Mai/林韵瑜捆绑视频"
    
    # from file import file_traceover
    # vid_list = file_traceover(directory, filter_option="video")
    # print(vid_list)

    # metadata_dict = {}
    # for vid in vid_list:
    #     metadata = metadata_generator("video")
    #     metadata = metatadata_handler(metadata, vid)
    #     metadata["studio"] = "TYINGART"
    #     metadata["model"] = ["Mai"]
    #     metadata_dict[metadata["title"]] = metadata
    # save_metadata(metadata_sorted(metadata_dict), f"mai_metadata.json")


    original_metadata = load_metadata("tyingart_album_metadata_cleaned.json")
    addition_metadata = load_metadata("tyingart_web_album_metadata_cleaned.json")

    for key in original_metadata.keys():
        if key in addition_metadata.keys():
            original_metadata[key] = metadata_merger(original_metadata[key], addition_metadata[key])
    save_metadata(original_metadata, "ty_album_metadata_updated.json")


    # # Clean up the metadata 
    # original_metadata = load_metadata("tyingart_web_album_metadata.json")

    # processed_metadata = {}
    # for key, metadata in original_metadata.items():
    #         # if key.split("-")[0] != "":
    #         #     processed_metadata[key] = metadata
    #         if type(metadata["model"]) is list:
    #             models = metadata["model"]
    #             model = ""
    #             for m in models:
    #                 model += m + ", "
    #             model = model[:-2]  # Remove the last comma and space 
    #             processed_metadata["{}-{}".format(model, metadata["title"])] = metadata
    #         elif type(metadata["model"]) is str:
    #             processed_metadata["{}-{}".format(metadata["model"], metadata["title"])] = metadata
    # save_metadata(processed_metadata, "tyingart_web_album_metadata_cleaned.json")
