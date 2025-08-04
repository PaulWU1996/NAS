from json.TYINGART.web.metadata import metadata_generator, metatadata_handler, load_metadata, save_metadata, metadata_merger, metadata_sorted
from utils.file import file_traceover

def inspect(directory: str, output_file: str, file_type: str):
    
    entry_list = file_traceover(directory, filter_option=file_type)

    print(f"Search completed! Found {len(entry_list)} {file_type} files.")
    metadata_dict = {}
    for entry in entry_list:
        entry_metadata = metadata_generator(file_type)
        entry_metadata = metatadata_handler(entry_metadata, entry,)

        if file_type == "album":
            if len(entry_metadata["model"]) == 0:
                model = "Unknown"
            elif len(entry_metadata["model"]) == 1:
                model = entry_metadata["model"][0]
            else:
                models = entry_metadata["model"]
                model = ", ".join(models)
            metadata_dict["{}-{}".format(model, entry_metadata["title"])] = entry_metadata
        elif file_type == "video":
            metadata_dict[entry_metadata["title"]] = entry_metadata
    
    save_metadata(metadata_sorted(metadata_dict), output_file)
    print(f"Metadata saved to {output_file}.")

"""
standard workflow for future
"""

# step 1: inspect the directory and save metadata
# inspect(directory="/mnt/nas/Bondage/Woods木子正/",
#             output_file="video_metadata.json",
#             file_type="video")

if __name__ == "__main__":

    from pathlib import Path
    inspect(directory="/mnt/nas/Dancer/耿爽爽/",
            output_file="gss_video_metadata.json",
            file_type="video")

    data = load_metadata("gss_video_metadata.json")

    i = 235
    for k, v in data.items():
        poster_path = v["path"][:-4]+".Cover.jpg"
        if Path(poster_path).is_file():
            data[k]["poster"] = poster_path
        data[k]["model"] = ["耿爽爽"]
        data[k]["description"] = v["title"]
        data[k]["series"] = "耿爽爽"
        data[k]["studio"] = ["Bilibili"]
        data[k]["code"] = f"BB-{i:03d}"
        i += 1
    save_metadata(metadata_sorted(data), "gss_video_metadata.json")

    new = {}
    for k, v in data.items():
        new[v["code"]] = v

    save_metadata(metadata_sorted(new), "gss_video_metadata.json")
