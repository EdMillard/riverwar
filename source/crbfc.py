"""
Copyright (c) 2022 Ed Millard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import json
import requests
from typing import Dict, List, Optional
import pandas as pd
from io import StringIO
from pathlib import Path

def request_esplist()->Dict[str, str]:
    esp = {}

    path:Path = Path("data/CRBFC")
    path.mkdir(parents=True, exist_ok=True)
    file_path:Path = path / "esplist.json"
    content:Optional[Dict] = {}
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"❌ Error reading JSON file: {e}")
            content = None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            content = None
    else:
        url = 'https://www.cbrfc.noaa.gov/wsup/graph/espcond_data.py?&fdate=LATEST&area=CB&sort=basin&otype=json&qpfdays=0'
        r = request_get(url)
        if r and r.status_code == 200:
            content = r.json()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

    if content is not None:
        esp_id:List[str] = content.get('espid', [])
        esp_name:List[str] = content.get('espname', [])
        esp_river:List[str] = content.get('espriver', [])
        esp_basin:List[str] = content.get('espbasin', [])
        esp_state:List[str] = content.get('espstate', [])
        esp_fgroup_id:List[str] = content.get('espfgroupid', [])
        esp = dict(zip(esp_name, esp_id))
        pass
    return esp


def request_forecast(esp_id:str, year:int)->Optional[pd.DataFrame]:
    url = f'https://www.cbrfc.noaa.gov/wsup/graph/esptxt.py?id={esp_id}&year={year}&db=&csv=1'

    r = request_get(url)
    if r and r.status_code == 200:
        text = r.text
        # Clean common CBRFC issues
        lines = text.splitlines()
        clean_lines = []
        for line in lines:
            # Remove trailing commas
            line = line.rstrip(',')
            # Skip obvious non-data lines if needed
            if line.strip() and not line.startswith('#####'):
                clean_lines.append(line)

        clean_csv = '\n'.join(clean_lines)

        df = pd.read_csv(
            StringIO(clean_csv),
            # header=None,  # Read everything first
            skiprows=lambda x: x < 4 and len(clean_lines[x].split(',')) < 5,  # heuristic
            on_bad_lines='skip'
        )
        df = df.rename(columns={'Run Date': 'Date'})
        print(df.head())
        return df
    else:
        return None

def request_get(url:str):
    headers = {"Accept": "application/vnd.api+json"}
    retries = 0
    max_retries = 5
    while retries < max_retries:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            return r
        except requests.exceptions.ConnectTimeout as e:
            print(f'USBR RISE request timeout error, retry {retries} of {max_retries}: {e} ')
            retries += 1
    return {}