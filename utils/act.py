from metadata import metadata_generator, metatadata_handler, save_metadata, metadata_merger, metadata_sorted
from file import file_traceover

# def inspect(directory: str, file_type: str):
    

if __name__ == "__main__":

    # directory = "/Volumes/PRIVATE_COLLECTION/Bondage/Tyingart"
    # file_type = "video"

    directory = "/mnt/nas/林韵瑜（Moon）Mai/林韵瑜捆绑相册"
    file_type = "album"
    output_file = "/home/paulwu/NAS/mai_metadata.json"

    entry_list = file_traceover(directory, filter_option=file_type)

    print(f"Search completed! Found {len(entry_list)} {file_type} files.")
    metadata_dict = {}
    for entry in entry_list:
        entry_metadata = metadata_generator(file_type)
        entry_metadata = metatadata_handler(entry_metadata, entry, studio="TYINGRT", model="Mai") #code=file["title"] if file["studio"]=="TYINGART" else ""
        # entry_metadata = metadata_merger(entry_metadata, entry)
        metadata_dict[entry_metadata["title"]] = entry_metadata
    
    metadata_dict = metadata_sorted(metadata_dict)
    save_metadata(metadata_dict, output_file)
    print(f"Metadata saved to {output_file}.")


