from metadata import metadata_generator, metatadata_handler, save_metadata
from file import file_traceover

# def inspect(directory: str, file_type: str):
    

if __name__ == "__main__":

    directory = "/Volumes/PRIVATE_COLLECTION/Bondage/Tyingart"
    file_type = "video"

    file_list = file_traceover(directory, filter_option=file_type)
    print(f"Search completed! Found {len(file_list)} {file_type} files.")
    metadata_dict = {}
    for file in file_list:
        file_metadata = metadata_generator("video")
        file_metadata = metatadata_handler(file_metadata, file, code=file["title"] if file["studio"]=="TYINGART" else "")
        metadata_dict[file_metadata["title"]] = file_metadata

    save_metadata(dict(sorted(metadata_dict.items())), "tyingart_video_metadata.json")
    print(f"Metadata saved to video_metadata.json")


