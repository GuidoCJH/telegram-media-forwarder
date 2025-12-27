import json
import re

def extract_photos(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Intento 1: SIGI_STATE
    sigi = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', html)
    if sigi:
        data = json.loads(sigi.group(1))
        # Navegar por el JSON para encontrar fotos
        print("Found SIGI_STATE")
        return data

    # Intento 2: __UNIVERSAL_DATA_FOR_REHYDRATION__
    universal = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html)
    if universal:
        data = json.loads(universal.group(1))
        print("Found UNIVERSAL_DATA")
        return data

    print("Nothing found")
    return None

data = extract_photos('tiktok_sample.html')
if data:
    with open('tiktok_extracted.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Extracted to tiktok_extracted.json")
