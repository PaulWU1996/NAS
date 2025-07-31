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
    
    album tree:
    /root
        /album
            /image

    video tree:
    /root
        /series
            /video

    Args:
        folder_path (str): 要扫描的根目录
        filter_option (str): 可选类型："video" 或 "album"

    Returns:
        list: 包含 metadata 字典的列表
    """
    file_list = []

    if filter_option == "album":
        for root, dirs, files in os.walk(folder_path):
            for dir_name in dirs:
                abs_path = os.path.join(root, dir_name)
                metadata = {}
                metadata["title"] = dir_name.split("-")[-1]
                metadata["model"] = [dir_name.split("-")[0]] if len(dir_name.split("-")) > 1 else [""]
                imgs = {}
                for file in os.listdir(abs_path):
                    if filter("image", file):
                        imgs[file] = {"path": os.path.join(abs_path, file),
                                      "poster": False}

                imgs = dict(sorted(imgs.items()))
                metadata["imgs"] = imgs
                metadata["path"] = abs_path
                file_list.append(metadata)
        return file_list


    if filter_option == "video":
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

    directory = "/Volumes/PRIVATE_COLLECTION/林韵瑜（Moon）Mai/林韵瑜捆绑相册"
    
    entry_list = file_traceover(directory, filter_option="album")
    print(len(entry_list))

    # files = get_all_files(directory)
    # for file in files:
    #     print(file)