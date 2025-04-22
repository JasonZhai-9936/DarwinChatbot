#turns chunked json into FAISS vector db
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate

from langchain.chains import LLMChain

from langchain_community.llms import HuggingFaceHub

import json
import os
from sentence_transformers import SentenceTransformer

def chunkedJSONToList(json_file='chunked_Wiki.json'):
    """
    Function to process the JSON data and return a list of combined strings
    (text and URL) and their associated metadata (e.g., 'label').

    Args:
        json_file (str): The path to the JSON file.

    Returns:
        combined_list (list): A list of combined text and URL.
        metadata_list (list): A list of metadata corresponding to each document.
    """
    # Open the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Initialize empty lists for text and metadata
    combined_list = []
    metadata_list = []
    
    # Loop through each item in the JSON data
    for item in data:
        # Combine 'url' and 'text' into one string
        #combined_string = f"URL: {item['url']} | Text: {item['text']}"
        
        # Append combined string to the list
        combined_list.append(item['text'])
        
        # Use .get() to avoid KeyError if 'topic' is missing
        topic = item.get('label', '')  # Default to 'Unknown' if 'topic' is missing
        
        # Add metadata with 'label' as the key
        metadata_list.append({"label": topic})  # 'label' is the key for metadata
    
    return combined_list, metadata_list

def pdf_to_faiss():
    """
    Function to create a FAISS index from a set of text documents with associated
    metadata. It will also save the FAISS index to a local file for future use.
    
    Returns:
        db (FAISS): The FAISS vector store.
    """
    print("Creating new FAISS index...")
    
    # Initialize HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Retrieve both the texts and metadata
    texts, metadata = chunkedJSONToList("chunked_Wiki.json")  # Get text and metadata from the JSON
    
    # Use FAISS to create an index with texts and their metadata
    db = FAISS.from_texts(texts, embeddings, metadatas=metadata)
    
    # Save the FAISS index to disk for future use
    db.save_local("faiss_index_file")
    print(f"FAISS index saved to faiss_index_file")

    return db

def answer(db, query):
    """
    Function to perform a similarity search on the FAISS index.
    
    Args:
        db (FAISS): The FAISS index.
    
    Returns:
        docs (list): A list of documents matching the search query.
    """
    docs = db.similarity_search(query, k=10)
    
    if not query:
        return
    
    # Format the documents and include metadata in the output prompt
    formatted_docs = []
    for doc in docs:
        # Access the document and its associated metadata
        text = doc.page_content  # Use the 'page_content' attribute for text
        metadata = doc.metadata  # Use the 'metadata' attribute
        
        # Create a formatted output string that includes the text and metadata ('label')
        formatted_doc = f"Text: {text}\nLabel: {metadata.get('label', 'N/A')}"
        formatted_docs.append(formatted_doc)
    
    return formatted_docs

def query(query):
   
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    db = FAISS.load_local("faiss_index_file", embeddings, allow_dangerous_deserialization=True)#if already made
    
    
    formatted_results = answer(db, query)  # Get the similarity search results and format them
    for result in formatted_results:
        print(result)  # Print the results
        
    return formatted_results 


def search_vector_db(prompt):
    """
    Searches the FAISS vector database for the most relevant documents based on the given prompt.

    Args:
        prompt (str): The search query.

    Returns:
        list: A list of the most relevant documents with metadata.
    """
    if not prompt:
        print("⚠️ Please provide a valid query.")
        return []

    # Load embeddings and FAISS index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    db = FAISS.load_local("faiss_index_file", embeddings, allow_dangerous_deserialization=True)

    # Perform similarity search
    results = answer(db, prompt)

    # Display results
    for result in results:
        print(result)

    return results

def main():
    """
    Main function to create a FAISS index and perform a similarity search.
    """
    #for making new
    db = pdf_to_faiss()  # Create the FAISS index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    db = FAISS.load_local("faiss_index_file", embeddings, allow_dangerous_deserialization=True)#if already made
    
    
    formatted_results = answer(db, 'earthworm')  # Get the similarity search results and format them
    for result in formatted_results:
        print(result)  # Print the results
        
    return formatted_results

if __name__ == "__main__":
    main()
