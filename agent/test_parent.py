import os
import json
from notion_client import Client
client = Client(auth=os.environ.get("NOTION_API_TOKEN"))

print("Testing sample_company page parent...")
page = client.pages.retrieve('335718ff-b6a8-80e9-8eea-d7b2cc21c3ce')
parent = page.get("parent")
print("Parent is:", json.dumps(parent, indent=2))
