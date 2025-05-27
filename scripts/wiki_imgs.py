import requests
import webbrowser

def search_wikimedia_images(query, limit=5):
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url"
    }

    res = requests.get(url, params=params)
    data = res.json()

    images = []
    for page in data.get("query", {}).get("pages", {}).values():
        if "imageinfo" in page:
            images.append({
                "title": page.get("title"),
                "url": page["imageinfo"][0]["url"]
            })

    return images

if __name__ == "__main__":
    query = "Charles Darwin"
    images = search_wikimedia_images(query, limit=5)

    if images:
        print(f"\nTop Wikimedia Image Results for: '{query}'\n")
        for i, img in enumerate(images, 1):
            print(f"{i}. {img['title']}\n   {img['url']}\n")

            # Open in default browser (optional)
            webbrowser.open(img['url'])
    else:
        print("No images found.")
