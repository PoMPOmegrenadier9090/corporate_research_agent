import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(auth=os.environ.get("NOTION_API_TOKEN"))
obj_id = os.environ.get("NOTION_DB_ID")

print(f"Testing ID: {obj_id}")

try:
    print("\nTesting as DB...")
    db = client.databases.retrieve(obj_id)
    print("It's a DB!")
except Exception as e:
    print("DB retrieve error:", e)

try:
    print("\nTesting as Page...")
    page = client.pages.retrieve(obj_id)
    print("It's a Page!")
except Exception as e:
    print("Page retrieve error:", e)

try:
    print("\nTesting as Block...")
    block = client.blocks.retrieve(obj_id)
    print("It's a Block!")
    if block.get("type") == "child_database":
        print(f"Child Database found! The REAL DB ID is: {block.get('id')}")
    else:
        print(f"Block type: {block.get('type')}")
        
    children = client.blocks.children.list(block_id=obj_id)
    for c in children.get("results", []):
        if c.get("type") == "child_database":
            print(f"FOUND INLINE DB! The REAL DB ID is: {c.get('id')}")
            
except Exception as e:
    print("Block retrieve error:", e)
