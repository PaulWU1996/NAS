"""
This module provides utility functions for file operations.
"""

import os
import sys
from typing import List, Optional

# === File Extensions ===

file_extensions = {
    "video": ["mp4", "mkv", "avi", "mov"],
    "image": ["jpg", "jpeg", "png", "gif"],
    "audio": ["mp3", "wav", "flac"],
    "document": ["pdf", "docx", "txt"],
}

# === File Traceover ===

def filter(type: str, file: str) -> bool:
    """Filter files based on type and file extension.

    Args:
        type (str): video, image, audio, document
        file (str): file name with extension
    """
    if type not in file_extensions:
        raise ValueError(f"Unsupported type: {type}")
    file_extension = file.split('.')[-1].lower()
    if file_extension in file_extensions[type]:
        return True
    else:
        return False

def file_traceover(folder_path: str, filter_option: Optional[str] = None) -> List[dict]:
    """File Traceover

    This function traces all files in a given folder and its subfolders.

    Args:
        folder_path (str): _description_

    Returns:
        list: _description_
    """
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if filter_option is not None:
                if filter(filter_option, file):
                    file_list.append({
                        "title": file.split('.')[0].upper() if len(file)==2 else file[:-(len(file.split(".")[-1])+1)],
                        "path": os.path.join(root, file),
                        "type": filter_option,
                        "studio": root.split('/')[-2].upper(),
                        "series": root.split('/')[-1].upper(),
                    })
            else:
                file_list.append(file.split('.')[0].upper())
    return file_list



def get_all_files(folder_path):
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            file_list.append(full_path)
    return file_list

# Example usage
if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    directory = "/Volumes/PRIVATE_COLLECTION/Bondage/Tyingart"
    
    vid_list = file_traceover(directory, filter_option="video")
    print(vid_list[0])

    # files = get_all_files(directory)
    # for file in files:
    #     print(file)