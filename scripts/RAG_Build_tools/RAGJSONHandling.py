#chunk nad overflow newly downloaded json
import json
import re
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np
from tqdm import tqdm


# Function to load the JSON data from file
def load_json_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def chunk_text_data(input_json, max_chunk_size=1000, search_window=20, output_file_name="chunked_Wiki.json"):
    chunked_data = []
    for entry in input_json:
        text = entry['text']
        url = entry['url']
        label = entry['label']

        # Check if text is a string. Convert to string if it's a number.
        if not isinstance(text, str):
            text = str(text)

        # Remove newline characters and extra spaces
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text).strip()

        start_index = 0
        while start_index < len(text):
            end_index = min(start_index + max_chunk_size, len(text))
            boundary_index = -1

            # Search for a period within the defined window
            for i in range(end_index - start_index):  # Corrected range
                if i > search_window: break # added break condition to prevent infinite loop
                period_index = text.find(". ", start_index + i, start_index + i + 2) #added +2 to prevent infinite loop
                if period_index != -1:
                    boundary_index = period_index
                    break

            if boundary_index != -1:
                end_index = boundary_index + 2
            elif end_index < len(text):
                boundary_index = text.find(". ", end_index, end_index + search_window)
                if boundary_index != -1:
                    end_index = boundary_index + 2
                else:
                    end_index = min(start_index + max_chunk_size, len(text))
            else:
                end_index = min(start_index + max_chunk_size, len(text))

            chunk = text[start_index:end_index].strip()
            chunked_data.append({'text': chunk, 'label': label})
            start_index = end_index

    with open(output_file_name, 'w') as outfile:
        json.dump(chunked_data, outfile, indent=4)

    return chunked_data


def add_key_to_json(input_json, new_key, new_value):
    for entry in input_json:
        entry[new_key] = new_value
    return input_json

import json

#combines 2 filtered json lists
def combine_json(file1, file2, output_file):
    # Read the first file
    try:
        with open(file1, 'r') as f1:
            data1 = json.load(f1)
    except FileNotFoundError:
        data1 = []
    except json.JSONDecodeError:
        data1 = []

    # Read the second file
    try:
        with open(file2, 'r') as f2:
            data2 = json.load(f2)
    except FileNotFoundError:
        data2 = []
    except json.JSONDecodeError:
        data2 = []

    # Combine both data sets
    combined_data = data1 + data2

    # Write the combined data to the output file
    with open(output_file, 'w') as output:
        json.dump(combined_data, output, indent=4)
    print("combine done")

def chunkingNew(input_json, max_chunk_size=1000, output_file_name="chunked_wiki.json"):
    chunked_data = []
    
    for entry in input_json:
        text = entry['text']
        label = entry['label']
        
        # Check if text is a string. Convert to string if it's a number.
        if not isinstance(text, str):
            text = str(text)
        
        # Remove newline characters and extra spaces
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text).strip()

        # Calculate how many chunks will be needed
        total_chunks = (len(text) // max_chunk_size) + (1 if len(text) % max_chunk_size != 0 else 0)

        # Split text into chunks
        start_index = 0
        for chunk_number in range(1, total_chunks + 1):
            end_index = min(start_index + max_chunk_size, len(text))
            chunk = text[start_index:end_index].strip()
            
            # Modify the label to reflect chunk number and total chunks
            chunked_label = f"{label} {chunk_number}/{total_chunks}"

            # Add the chunk to the data with the new label
            chunked_data.append({'text': chunk, 'label': chunked_label})

            # Update the start index for the next chunk
            start_index = end_index

    # Save the chunked data to a new JSON file
    with open(output_file_name, 'w') as outfile:
        json.dump(chunked_data, outfile, indent=4)

    return chunked_data



def main():
    jsonFile = load_json_from_file("wikiAll.json")
    #updated_json = add_key_to_json(jsonFile, 'label', 'myBook')  
    #combine_json("final.json", "testFiltered2.json", "finalCombined.json")

    #chunked_data = chunkingNew("finalCombined.json", output_file_name="final_chunked.json")
    chunk_text_data(jsonFile) #removed the redundant file name
    
main()