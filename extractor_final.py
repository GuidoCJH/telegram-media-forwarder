import json
import re

def extract_tiktok_photos(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html)
    if not match:
        print("No script tag found")
        return []

    try:
        data = json.loads(match.group(1))
        # Estructura típica:
        # data["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]["imagePost"]["images"]
        
        default_scope = data.get("__DEFAULT_SCOPE__", {})
        video_detail = default_scope.get("webapp.video-detail", {})
        item_info = video_detail.get("itemInfo", {})
        item_struct = item_info.get("itemStruct", {})
        image_post = item_struct.get("imagePost", {})
        images = image_post.get("images", [])
        
        photo_urls = []
        for img in images:
            # Preferimos el display_image o el URL más largo
            url = img.get("display_image", {}).get("url_list", [None])[0]
            if not url:
                url = img.get("imageURL", {}).get("url_list", [None])[0]
            if url:
                photo_urls.append(url)
        
        title = item_struct.get("desc", "TikTok Slideshow")
        return photo_urls, title
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return [], "Error"

urls, title = extract_tiktok_photos('tiktok_curl.html')
print(f"Found {len(urls)} photos")
print(f"Title: {title}")
for u in urls:
    print(u)
