"""
This module provides support for handling metadata
"""

import json
import os
from typing import Optional

# === Metadata Template ===

video_metadata_template = {
    "title": "",
    "code": "",
    "series": "",
    "model": [], 
    "studio": "",
    "description": "",
    "path": "",
    "poster": "",
    "tags": [],
}

album_metadata_template = {
    "title": "",
    "model": [],
    "studio": "",
}

model_metadata_template = {
    "name": "",
    "nickname": [],
    "studio": [],
    "ID": "",
    "SNS": [],
    "description": "",
    "comments": "",
    "beauty": int,
    "figure": int,
    "leg": int,
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
        template = ablum_metadata_template.copy()
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
    """Handle metadata by updating keys and values,

    Args:
        original_metadata (dict): _description_
        addition_metadata_type (str): _description_
        **kwargs: Additional key-value pairs to update in the metadata.

    Returns:
        dict: Updated metadata dictionary.
    """

    if addition_metadata is None:
        addition_metadata = {}

    # Update original metadata with additional metadata
    for key, value in addition_metadata.items():
        if key in original_metadata:
            original_metadata[key] = value
    
    # Update original metadata with keyword arguments
    for key, value in kwargs.items():
        if key in original_metadata:
            original_metadata[key] = value 
    
    return original_metadata

if __name__ == "__main__":

    # ty_web = load_metadata("tyingart_web_album_metadata.json")
    
    # sorted_metadata = {int(k) if str(k).isdigit() else k: v for k, v in ty_web.items()}
    # sorted_metadata = dict(sorted(sorted_metadata.items(), key=lambda x: x[0] if isinstance(x[0], int) else str(x[0])))

    # save_metadata(sorted_metadata, "album_metadata.json")

    # # Load both JSON files
    # with open("tyingart_video_metadata.json", "r") as f:
    #     addition_metadata = json.load(f)

    # with open("TYINGART_VID_LATEST.json", "r") as f:
    #     original_metadata = json.load(f)

    # # Create a map from title to addition entry
    # title_map = {v["title"]: v for v in addition_metadata.values()}

    # # Merge data
    # for key, original in original_metadata.items():
    #     code = original.get("code")
    #     if not code:
    #         continue
    #     addition = title_map.get(code)
    #     if addition:
    #         # Merge desired fields if they exist in addition and are non-empty
    #         for field in ["keywords", "description", "code", "model"]:
    #             if field in addition and addition[field]:
    #                 original[field] = addition[field]

    # # Save back to file
    # with open("1.json", "w") as f:
    #     json.dump(original_metadata, f, ensure_ascii=False, indent=4)

    # with open("TYINGART_VID_LATEST.json", "r") as f:
    #     metadata = json.load(f)

    # # metadata = {v["code"]: v for k, v in metadata.items() if v["code"]!= ""}
    # metadata = dict(sorted(metadata.items(), key=lambda x: x[0]))
    # save_metadata(metadata, "TYINGART_VID_LATEST.json")


    # Load both JSON files
    with open("tyingart_video_metadata.json", "r") as f:
        addition_metadata = json.load(f)

    with open("TYINGART_VID_LATEST.json", "r") as f:
        original_metadata = json.load(f)


    # Merge data
    for key, original in original_metadata.items():
        code = original.get("code")
        if not code:
            continue
        addition = addition_metadata.get(code)
        if addition:
            # Merge desired fields if they exist in addition and are non-empty
            poster = addition.get("path")[:-3]
            if os.path.exists(poster+"jpg"):
                original["poster"] = poster+"jpg"
            elif os.path.exists(poster+"jpeg"):
                original["poster"] = poster+"jpeg"

            for field in ["path"]:
                if field in addition and addition[field]:
                    original[field] = addition[field]

    # Save back to file
    with open("1.json", "w") as f:
        json.dump(original_metadata, f, ensure_ascii=False, indent=4)
