import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
client = Client(auth=os.environ.get("NOTION_API_TOKEN"))

try:
    print("Searching for ALL resources this integration can access...")
    response = client.search()
    results = response.get("results", [])
    if not results:
        print("Integration found 0 resources! It doesn't have access to anything.")
    else:
        for r in results:
            obj_type = r.get("object")
            id = r.get("id")
            title = "Unknown"
            if obj_type == "database":
                title_arr = r.get("title", [])
                if title_arr:
                    title = title_arr[0].get("plain_text", "Unknown")
            elif obj_type == "page":
                # Find title in properties
                props = r.get("properties", {})
                for k, v in props.items():
                    if v.get("type") == "title":
                        t_arr = v.get("title", [])
                        if t_arr:
                            title = t_arr[0].get("plain_text", "Unknown")
                        break
            print(f"- [{obj_type}] ID={id} Title='{title}'")
except Exception as e:
    print("Search error:", e)
