#downloads Darwin's and related wiki pages
import mediawikiapi
import json
import re
import os

def get_page_section_content(page_title, section_title=None):
    """
    Get the plaintext content of a specific section from a Wikipedia page.
    If section_title is None, get the main section (introduction).
    
    Args:
        page_title (str): The title of the Wikipedia page
        section_title (str, optional): The title of the section to get
        
    Returns:
        str: The plaintext content of the section
    """
    # Initialize the MediaWiki API client
    wiki = mediawikiapi.MediaWikiAPI()
    
    # Get the page content
    page = wiki.page(page_title)
    
    # If no section is specified, return the summary (intro section)
    if section_title is None:
        return page.summary
    
    # Get the content of the specified section
    try:
        section_content = page.section(section_title)
        return section_content if section_content else ""
    except Exception as e:
        print(f"Error getting section '{section_title}': {e}")
        return ""

def generate_wiki_json(page_title, section_indices, output_file="wiki_data.json"):
    """
    Generate a JSON file with the content of selected sections from a Wikipedia page.
    
    Args:
        page_title (str): The title of the Wikipedia page
        section_indices (list): List of section indices to include (1-based)
        output_file (str): The path to the output JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize the MediaWiki API client
        wiki = mediawikiapi.MediaWikiAPI()
        
        # Get the page content
        page = wiki.page(page_title)
        
        # Get the page URL
        page_url = page.url
        
        # Get all section titles
        all_sections = page.sections
        
        # Create the result list
        result = []
        
        # Get the intro section (not included in sections list)
        intro_text = page.summary
        if intro_text:
            result.append({
                "url": page_url,
                "text": intro_text,
                "label": "Introduction"
            })
        
        # Process selected sections
        for index in section_indices:
            # Adjust for 0-based indexing
            if 1 <= index <= len(all_sections):
                section_title = all_sections[index - 1]
                section_text = page.section(section_title)
                
                if section_text and len(section_text.strip()) > 0:
                    result.append({
                        "url": page_url,
                        "text": section_text,
                        "label": section_title
                    })
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully wrote {len(result)} sections to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error generating JSON: {e}")
        return False

def get_darwin_links(section_indices=range(1, 19)):
    """
    Get all links from Charles Darwin's Wikipedia page from specified sections.
    
    Args:
        section_indices (list): List of section indices to include (1-based)
    
    Returns:
        list: List of Wikipedia links from the specified sections
    """
    try:
        # Initialize the MediaWiki API client
        wiki = mediawikiapi.MediaWikiAPI()
        
        # Get Darwin's page
        darwin_page = wiki.page("Charles Darwin")
        
        # Get all section titles
        all_sections = darwin_page.sections
        
        # Get links from the page
        all_links = darwin_page.links
        
        # Filter out non-Wikipedia links and special pages
        wiki_links = [link for link in all_links 
                    if not link.startswith("File:") 
                    and not link.startswith("Category:") 
                    and not link.startswith("Template:")]
        
        # This is a simplified approach since the mediawikiapi doesn't directly 
        # provide section-specific links. In a real application, you might need 
        # to parse the HTML to get section-specific links.
        
        return wiki_links
        
    except Exception as e:
        print(f"Error getting Darwin's links: {e}")
        return []

def download_wiki_page_content(page_title):
    """
    Download all content from a Wikipedia page up to the "See also" section.
    
    Args:
        page_title (str): The title of the Wikipedia page
        
    Returns:
        dict: Dictionary with page_url, full_text, and sections info
    """
    try:
        # Initialize the MediaWiki API client
        wiki = mediawikiapi.MediaWikiAPI()
        
        # Get the page content
        page = wiki.page(page_title)
        
        # Get the page URL
        page_url = page.url
        
        # Get all section titles
        all_sections = page.sections
        
        # Get the intro section
        intro_text = page.summary
        
        # Initialize the full text with the intro
        full_text = intro_text + "\n\n"
        
        # Find "See also" section index if it exists
        see_also_index = -1
        for i, section in enumerate(all_sections):
            if section.lower() == "see also":
                see_also_index = i
                break
        
        # Get content of all sections up to "See also"
        section_end = see_also_index if see_also_index >= 0 else len(all_sections)
        
        for i in range(section_end):
            section_title = all_sections[i]
            section_text = page.section(section_title)
            
            if section_text and len(section_text.strip()) > 0:
                full_text += f"== {section_title} ==\n{section_text}\n\n"
        
        return {
            "url": page_url,
            "text": full_text,
            "title": page_title
        }
        
    except Exception as e:
        print(f"Error downloading page '{page_title}': {e}")
        return None

def process_darwin_related_pages(output_file="wikiOthers.json", max_pages=20):
    """
    Process related pages from Darwin's Wikipedia page and save content to JSON.
    
    Args:
        output_file (str): The path to the output JSON file
        max_pages (int): Maximum number of related pages to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get links from Darwin's page
        darwin_links = get_darwin_links()
        
        # Create the result list
        result = []
        
        # Process a limited number of pages to avoid excessive API calls
        processed_count = 0
        
        for link in darwin_links:
            if processed_count >= max_pages:
                break
                
            print(f"Processing page: {link}")
            page_data = download_wiki_page_content(link)
            
            if page_data:
                result.append({
                    "url": page_data["url"],
                    "text": page_data["text"],
                    "label": page_data["title"]
                })
                processed_count += 1
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully wrote {len(result)} related pages to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing Darwin related pages: {e}")
        return False

def getDarwinMain():
    """
    Main function for downloading Darwin's Wikipedia page sections.
    """
    # Charles Darwin's Wikipedia page
    page_title = "Charles Darwin"
    
    # Select sections 1-18 (exclude "See also", "Notes", "Citations", "Bibliography", "External links")
    section_indices = list(range(1, 19))  # Sections 1-18
    
    # Generate the JSON file
    output_file = "wikiDarwin.json"
    generate_wiki_json(page_title, section_indices, output_file)
    
    # Verify the file was created
    if os.path.exists(output_file):
        print(f"File '{output_file}' created successfully")
        # Print the file size
        file_size = os.path.getsize(output_file) / 1024  # Convert to KB
        print(f"File size: {file_size:.2f} KB")

def count_darwin_links():
    """
    Count the total number of links on Charles Darwin's Wikipedia page.
    
    Returns:
        int: The total number of links (excluding special pages like File:, Category:, Template:)
        int: The total number of all links including special pages
    """
    try:
        # Initialize the MediaWiki API client
        wiki = mediawikiapi.MediaWikiAPI()
        
        # Get Darwin's page
        darwin_page = wiki.page("Charles Darwin")
        
        # Get all links from the page
        all_links = darwin_page.links
        
        # Count all links
        total_all_links = len(all_links)
        
        # Filter out non-Wikipedia links and special pages
        wiki_links = [link for link in all_links 
                    if not link.startswith("File:") 
                    and not link.startswith("Category:") 
                    and not link.startswith("Template:")]
        
        # Count regular Wikipedia links
        total_wiki_links = len(wiki_links)
        
        print(f"Total Wikipedia links (excluding special pages): {total_wiki_links}")
        print(f"Total links (including special pages): {total_all_links}")
        
        return total_wiki_links, total_all_links
        
    except Exception as e:
        print(f"Error counting Darwin's links: {e}")
        return 0, 0
    
if __name__ == "__main__":
    # Process Darwin's main page
    # print("Processing Darwin's main page...")
    # getDarwinMain()
    count_darwin_links()
    # Process Darwin's related pages
    print("\nProcessing Darwin's related pages...")
    #process_darwin_related_pages(max_pages=4)  # Limit to 10 pages for demonstration