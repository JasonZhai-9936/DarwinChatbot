#download from DarwinOnline
import requests
from bs4 import BeautifulSoup
import json, os, re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

#these functions handle all online text retrieval

#Test URLs
#"https://darwin-online.org.uk/content/frameset?itemID=F3450&viewtype=text&pageseq=1"
#"https://darwin-online.org.uk/content/frameset?itemID=F1643&viewtype=text&pageseq=1"

#Types of texts tested
#


#tries to get all content
def basicScrape(url):
   
    try:
        response = requests.get(url)
        response.raise_for_status()  
        print("Successfully retrieved the page")

        soup = BeautifulSoup(response.content, 'html.parser')
        
        return soup.get_text(separator="\n", strip=True)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the page: {e}")
        return None
    
    #scrapes text from a type='text' URL 
    #ONLY FOR Darwin-online.org docs
def textScraper(url):
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None
    
    print("Successfully retrieved the frameset page")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Darwin-online.org iframe handling
    noframes_link = soup.find("noframes")
    if noframes_link:
        direct_url = noframes_link.find("a")["href"]
        print(f"Found direct content link in <noframes>: {direct_url}")
    else:
        
        frame_tag = soup.find("frame", {"id": "frames::txt-frame"})
        if frame_tag:
            direct_url = frame_tag["src"]
            print(f"Found direct content link in <frame>: {direct_url}")
        else:
            print("Could not find a direct content link in the frameset")
            return None

    
    if not direct_url.startswith("http"):
        
        direct_url = requests.compat.urljoin(url, direct_url)
    
    content_response = requests.get(direct_url)
    if content_response.status_code != 200:
        print(f"Failed to retrieve the content page. Status code: {content_response.status_code}")
        return None

    print("Successfully retrieved the content page")
    content_soup = BeautifulSoup(content_response.content, 'html.parser')
    return content_soup.get_text(separator="\n", strip=True)

#returns formatted filtered texts
def getTypeTextPretty(url):
    try:
        
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        
        rows = soup.find_all("tr", class_="hit-item")
        literature_items = []
        for row in rows:
            title_link = row.find("a", href=True, style="font-weight: bold")
            #filter for all items that have a text transcribed form
            text_link = row.find("a", href=True, target="_top", string="Text")
            #sort for periodical contribution type only
            text_link = row.find("a", href=True, target="_top", string="periodical_contribution")
            
            if title_link and text_link:
                title = title_link.get_text(strip=True)
                item_type = row.find("span").get_text(strip=True)
                text_url = text_link["href"]
                
                literature_items.append({
                    "title": title,
                    "type": item_type,
                    "text_url": text_url
                })
        
        return literature_items
    
    except requests.RequestException as e:
        return {"error": str(e)}
 
#returns list of links from adv search of type='text'   
def getTypeTextLinks(url):
    try:
        
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        
        rows = soup.find_all("tr", class_="hit-item")
        
        
        literature_items = []
        for row in rows:
            title_link = row.find("a", href=True, style="font-weight: bold")
            text_link = row.find("a", href=True, target="_top", string="Text")
            
            if title_link and text_link:
                text_url = text_link["href"]
                
                literature_items.append(text_url)  
        
        return literature_items
    
    except requests.RequestException as e:
        return {"error": str(e)}
    

def filter_non_characters(text):
    # removes any non-ASCII characters or any characters that are not alphabetic
    return re.sub(r'[^a-zA-Z\s]', '', text)
    
#scrapes a list of "text" pages at Darwin online
#uses filter_non_char
def scrapeFilteredOld(filename="testFiltered2.json"):
    links = [
        "https://darwin-online.org.uk/content/frameset?itemID=F9.1&viewtype=text&pageseq=1",
        "https://darwin-online.org.uk/content/frameset?itemID=F9.2&viewtype=text&pageseq=1"
    ]
    
    results = []
    
    for link in links:
        text = textScraper(link)
        if text:
            # Apply the filter to preserve useful punctuation
            filtered_text = filter_non_characters(text)
            
            results.append({
                "url": link,
                "text": filtered_text
            })
    
   
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as json_file:
            try:
                existing_data = json.load(json_file)
                # Ensure existing_data is a list
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                # If the file is empty or invalid, start with an empty list
                existing_data = []
    else:
        existing_data = []
    
    # Combine existing data with new results
    existing_data.extend(results)
    
    # Write the combined data back to the file
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)
    
#scrapes a single page for all 'text' docs and saves to json
#need to have '.json' in arg
import os
import json

def scrapeAdvSearchPage(url, filename="test1.json"):
    links = getTypeTextLinks(url)
    
    if isinstance(links, dict) and "error" in links:
        return
    
    results = []
    
    for link in links:
        text = textScraper(link)
        if text:
            results.append({
                "url": link,
                "text": text
            })
    
    # Check if the file exists and read existing data
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as json_file:
            try:
                existing_data = json.load(json_file)
                # Ensure existing_data is a list
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                
                existing_data = []
    else:
        existing_data = []
    
    # Combine existing data with new results
    existing_data.extend(results)
    
    # Write the combined data back to the file
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)
  
#couldnt figure out how to iterate and change url );
urls = ["https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=6&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=7&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=8&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=9&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
 ]


urls2 = [
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=1&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=2&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=3&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=4&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=5&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=6&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=7&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=8&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
    "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=9&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=100",
]
     
def scrape_pages(urls):
    for url in (urls):
        print(f"now on {url}")
        scrapeAdvSearchPage(url, "test2.json")   
        
        
def textScrapeTest():
    url = "https://darwin-online.org.uk/content/search-results?pageno=0&pagesize=50&sort=date-ascending&freetext=&allfields=&searchid=&name=Darwin+Charles+Robert&dateafter=&datebefore=&searchtitle=&description=&place=&publisher=&periodical=&published=true&havetext=true"
    content = basicScrape(url)
    print(content[:1000])

def advSearchScrapeTest():
    url = "https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=1&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=10"
    content = getTypeTextLinks(url)
    
    if isinstance(content, list):  
        print(str(content)[:1000])  
    else:
        print(content)
    
def scrape_entire_link(url):
    """
    Scrapes the entire content from the given URL.
    
    Args:
        url (str): The URL of the webpage to scrape.
        
    Returns:
        str or None: The text content of the webpage with whitespace standardized,
                     or None if an error occurs.
    """
    import requests
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url)
        response.raise_for_status()  
        print("Successfully retrieved the page")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the page: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    output = soup.get_text(separator="\n", strip=True)
    print(output)
    
def remove_all_newlines(text):
    """
    Removes all newline characters ('\n') from the text, regardless of context.
    
    Args:
        text (str): The text to process.
        
    Returns:
        str: The text with all newline characters removed.
    """
    if text is None:
        return None
        
    # Replace all newline characters with spaces
    # This handles \n, \r, and \r\n combinations
    result = text.replace('\n', ' ').replace('\r', ' ')
    
    # Remove multiple consecutive spaces that might have been created
    while '  ' in result:
        result = result.replace('  ', ' ')
        
    return result

def scrapeFiltered(filename="Darwin_writings.json", title_mapping=None):
    """
    Scrapes Darwin Online text pages, filters out newlines and non-letters,
    and saves the results (without duplicates) in a JSON file.
    """
    # 1) Default mapping (fixed URL with no trailing space)
    if title_mapping is None:
        title_mapping = {
            "https://darwin-online.org.uk/content/frameset?itemID=F9.1&viewtype=text&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 1 Fossil Mammalia", 
            "https://darwin-online.org.uk/content/frameset?itemID=F9.2&viewtype=text&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 2 Mammalia", 
            "https://darwin-online.org.uk/content/frameset?viewtype=text&itemID=F9.3&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 3 Birds", 
            "https://darwin-online.org.uk/content/frameset?viewtype=text&itemID=F9.4&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 4 Fish",
            "https://darwin-online.org.uk/content/frameset?viewtype=text&itemID=F9.5&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 5 Reptiles",
            "https://darwin-online.org.uk/content/frameset?itemID=F10.1&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Proceedings of the first expedition",
            "https://darwin-online.org.uk/content/frameset?itemID=F10.2&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Proceedings of the second expedition",
            "https://darwin-online.org.uk/content/frameset?itemID=F10.3&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Darwin, C. R. 1839. Journal and remarks",
            "https://darwin-online.org.uk/content/frameset?itemID=F14&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Journal of researches into the natural history and geology of the countries visited during the voyage of H.M.S. Beagle round the world. London: Murray",
            "https://darwin-online.org.uk/content/frameset?itemID=F339.1&viewtype=text&pageseq=1": "Fossil Cirripedia: The Lepadidae; or, pedunculated cirripedes",
            "https://darwin-online.org.uk/content/frameset?itemID=F339.2&viewtype=text&pageseq=1": "Fossil Cirripedia: The Balanidae, (or sessile cirripedes); the Verrucidae",
            "https://darwin-online.org.uk/content/frameset?itemID=F391&viewtype=text&pageseq=1": "On the Origin of Species",
            "https://darwin-online.org.uk/content/frameset?itemID=F801&viewtype=text&pageseq=1": "Fertilisation of Orchids",
            "https://darwin-online.org.uk/content/frameset?itemID=F880.1&viewtype=text&pageseq=1": "The variation of animals and plants under domestication Vol1",
            "https://darwin-online.org.uk/content/frameset?itemID=F880.2&viewtype=text&pageseq=1": "The variation of animals and plants under domestication Vol2",
            "https://darwin-online.org.uk/content/frameset?itemID=F937.1&viewtype=text&pageseq=1": "The Descent of Man Vol 1",
            "https://darwin-online.org.uk/content/frameset?itemID=F937.2&viewtype=text&pageseq=1": "The Descent of Man Vol 2",
            "https://darwin-online.org.uk/content/frameset?itemID=F1142&viewtype=text&pageseq=1": "The expression of the emotions in man and animals",
            "https://darwin-online.org.uk/content/frameset?itemID=F1217&viewtype=text&pageseq=1": "Insectivorous Plants",
            "https://darwin-online.org.uk/content/frameset?itemID=F1733&viewtype=text&pageseq=1": "Climbing Plants",
            "https://darwin-online.org.uk/content/frameset?itemID=F1249&viewtype=text&pageseq=1": "Cross and Self Fertilisation",
            "https://darwin-online.org.uk/content/frameset?itemID=F1277&viewtype=text&pageseq=1": "The different forms of flowers on plants of the same species",
            "https://darwin-online.org.uk/content/frameset?itemID=F1319&viewtype=text&pageseq=1": "Erasmus Darwin",
            "https://darwin-online.org.uk/content/frameset?itemID=F1325&viewtype=text&pageseq=1": "The Power of Movement in Plants",
            "https://darwin-online.org.uk/content/frameset?itemID=F1357&viewtype=text&pageseq=1": "The formation of vegetable mould, through the action of worms, with observations on their habits",
            "https://darwin-online.org.uk/content/frameset?itemID=F1452.1&viewtype=text&pageseq=1": "The life and letters of Charles Darwin, including an autobiographical chapter Vol 1",
            "https://darwin-online.org.uk/content/frameset?itemID=F1452.2&viewtype=text&pageseq=1": "The life and letters of Charles Darwin, including an autobiographical chapter Vol 2",
            "https://darwin-online.org.uk/content/frameset?itemID=F1452.3&viewtype=text&pageseq=1": "The life and letters of Charles Darwin, including an autobiographical chapter Vol 3",
            "https://darwin-online.org.uk/content/frameset?itemID=F1552.1&viewtype=text&pageseq=1": "Emma Darwin: wife of Charles Darwin. A century of family letters. Click to see illustrations Vol 1",
            "https://darwin-online.org.uk/content/frameset?itemID=F1552.2&viewtype=text&pageseq=1": "Emma Darwin: wife of Charles Darwin. A century of family letters. Click to see illustrations Vol 2",
            "https://darwin-online.org.uk/content/frameset?itemID=CUL-DAR158.1-76&viewtype=text&pageseq=1": "The autobiography of Charles Darwin",
            "https://darwin-online.org.uk/content/frameset?itemID=CUL-DAR210.9.30&viewtype=text&pageseq=1": "Darwin's personal diary"
            
        }

    # 2) Load existing data once
    try:
        with open(filename, "r", encoding="utf-8") as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    existing_urls = {item["url"] for item in existing}
    new_results = []

    for raw_url, title in title_mapping.items():
        url = raw_url.strip()                    # strip stray whitespace
        if url in existing_urls:
            print(f"Skipping already-scraped URL: {url}")
            continue

        print(f"Processing: {url}")
        raw = textScraper(url)
        if not raw:
            print(f"  → Failed retrieval, skipping.")
            continue

        # 3) Chain newline removal then non-letter filtering
        cleaned = filter_non_characters(remove_all_newlines(raw))
        new_results.append({
            "url": url,
            "label": title,
            "text": cleaned
        })

    # 4) Append & write back only once
    if new_results:
        existing.extend(new_results)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=4)
        print(f"Appended {len(new_results)} new items.")
    else:
        print("No new items to append.")
 
def scrapeFilteredold(filename="testFiltered2.json", title_mapping=None):
    """
    Scrapes Darwin Online text pages, filters out non-alphabetic characters,
    and saves the results in a JSON file with manual title labels.
    
    Args:
        filename (str): Name of the JSON file to save the output.
        title_mapping (dict): A dictionary mapping URLs to their manual titles.
                              If a URL is not found in the dictionary, a default
                              title 'Untitled' is used.
    """
    # If no title mapping is provided, create a default one
    if title_mapping is None:
        title_mapping = {
            "https://darwin-online.org.uk/content/frameset?itemID=F9.1&viewtype=text&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 1 Fossil Mammalia", 
            "https://darwin-online.org.uk/content/frameset?itemID=F9.2&viewtype=text&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 2 Mammalia", 
            "https://darwin-online.org.uk/content/frameset?viewtype=text&itemID=F9.3&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 3 Birds", 
            "https://darwin-online.org.uk/content/frameset?viewtype=text&itemID=F9.4&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 4 Fish",
            "https://darwin-online.org.uk/content/frameset?viewtype=text&itemID=F9.5&pageseq=1": "The Zoology of the Voyage of H.M.S. Beagle: Part 5 Reptiles",
            "https://darwin-online.org.uk/content/frameset?itemID=F10.1&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Proceedings of the first expedition",
            "https://darwin-online.org.uk/content/frameset?itemID=F10.2&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Proceedings of the second expedition",
            "https://darwin-online.org.uk/content/frameset?itemID=F10.3&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Darwin, C. R. 1839. Journal and remarks",
            "https://darwin-online.org.uk/content/frameset?itemID=F14&viewtype=text&pageseq=1": "Journal of Researches (Voyage of the Beagle): Journal of researches into the natural history and geology of the countries visited during the voyage of H.M.S. Beagle round the world. London: Murray",
            "https://darwin-online.org.uk/content/frameset?itemID=F339.1&viewtype=text&pageseq=1": "Fossil Cirripedia: The Lepadidae; or, pedunculated cirripedes",
            "https://darwin-online.org.uk/content/frameset?itemID=F339.2&viewtype=text&pageseq=1": "Fossil Cirripedia: The Balanidae, (or sessile cirripedes); the Verrucidae",
            "https://darwin-online.org.uk/content/frameset?itemID=F391&viewtype=text&pageseq=1": "On the Origin of Species",
            "https://darwin-online.org.uk/content/frameset?itemID=F801&viewtype=text&pageseq=1": "Fertilisation of Orchids",
            "https://darwin-online.org.uk/content/frameset?itemID=F880.1&viewtype=text&pageseq=1": "The variation of animals and plants under domestication Vol1",
            "https://darwin-online.org.uk/content/frameset?itemID=F880.2&viewtype=text&pageseq=1": "The variation of animals and plants under domestication Vol2",
            "https://darwin-online.org.uk/content/frameset?itemID=F937.1&viewtype=text&pageseq=1": "The Descent of Man Vol 1",
            "https://darwin-online.org.uk/content/frameset?itemID=F937.2&viewtype=text&pageseq=1": "The Descent of Man Vol 2",
            "https://darwin-online.org.uk/content/frameset?itemID=F1142&viewtype=text&pageseq=1": "The expression of the emotions in man and animals",
            "https://darwin-online.org.uk/content/frameset?itemID=F1217&viewtype=text&pageseq=1": "Insectivorous Plants",
            "https://darwin-online.org.uk/content/frameset?itemID=F1733&viewtype=text&pageseq=1": "Climbing Plants",
            "https://darwin-online.org.uk/content/frameset?itemID=F1249&viewtype=text&pageseq=1": "Cross and Self Fertilisation",
            "https://darwin-online.org.uk/content/frameset?itemID=F1277&viewtype=text&pageseq=1": "The different forms of flowers on plants of the same species",
            "https://darwin-online.org.uk/content/frameset?itemID=F1319&viewtype=text&pageseq=1": "Erasmus Darwin",
            "https://darwin-online.org.uk/content/frameset?itemID=F1325&viewtype=text&pageseq=1": "The Power of Movement in Plants",
            "https://darwin-online.org.uk/content/frameset?itemID=F1357&viewtype=text&pageseq=1": "The formation of vegetable mould, through the action of worms, with observations on their habits",
            "https://darwin-online.org.uk/content/frameset?itemID=F1452.1&viewtype=text&pageseq=1": "The life and letters of Charles Darwin, including an autobiographical chapter Vol 1",
            "https://darwin-online.org.uk/content/frameset?itemID=F1452.2&viewtype=text&pageseq=1": "The life and letters of Charles Darwin, including an autobiographical chapter Vol 2",
            "https://darwin-online.org.uk/content/frameset?itemID=F1452.3&viewtype=text&pageseq=1": "The life and letters of Charles Darwin, including an autobiographical chapter Vol 3",
            "https://darwin-online.org.uk/content/frameset?itemID=F1552.1&viewtype=text&pageseq=1": "Emma Darwin: wife of Charles Darwin. A century of family letters. Click to see illustrations Vol 1",
            "https://darwin-online.org.uk/content/frameset?itemID=F1552.2&viewtype=text&pageseq=1": "Emma Darwin: wife of Charles Darwin. A century of family letters. Click to see illustrations Vol 2",
            "https://darwin-online.org.uk/content/frameset?itemID=CUL-DAR158.1-76&viewtype=text&pageseq=1": "The autobiography of Charles Darwin",
            "https://darwin-online.org.uk/content/frameset?itemID=CUL-DAR210.9.30&viewtype=text&pageseq=1": "Darwin's personal diary"
            
        }
    
    results = []
    
    for link, title in title_mapping.items():
        print(f"Processing link: {link}")
        text = textScraper(link)
        if text:
            filtered_text = remove_all_newlines(text)
            # Filter the text while preserving spaces (and removing non-letter characters)
            filtered_text = filter_non_characters(text)
            results.append({
                "url": link,
                "label": title,
                "text": filtered_text
            })
        else:
            print(f"Skipping link {link} due to retrieval issues.")
    
    # Load any existing data in the JSON file if it exists
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as json_file:
            try:
                existing_data = json.load(json_file)
                if not isinstance(existing_data, list):
                    existing_data = []
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    
    # Append the new results to the existing data
    existing_urls = [item["url"] for item in existing_data]
    for result in results:
        if result["url"] not in existing_urls:
            existing_data.append(result)
    existing_data.extend(results)
    
    # Write the combined data back to the JSON file
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    #textScrapeTest()
    #advSearchScrapeTest()
    #scrape_pages(urls)
    #scrape_entire_link("https://darwin-online.org.uk/content/frameset?itemID=F181&viewtype=text&pageseq=1")
    
    scrapeFiltered()
    
    
    #scrapeAllResults("https://darwin-online.org.uk/content/search-results?freetext=&description=&allfields=&language=English&published=true&sort=date-ascending&havetext=true&dateafter=&searchtitle=&searchid=&pageno=2&periodical=&name=Darwin+Charles+Robert&publisher=&datebefore=&place=&pagesize=10")
