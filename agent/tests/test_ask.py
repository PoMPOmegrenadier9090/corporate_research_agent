import requests
import sys

def ask_agent(prompt: str, url: str = "http://localhost:8000/ask"):
    """
    Sends a prompt to the agent's /ask endpoint and prints the result.
    """
    payload = {"prompt": prompt}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "error" in result and result["error"]:
            print(f"Error from agent: {result['error']}")
        else:
            print(result.get("response", "No response text found."))
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ask.py \"Your prompt here\"")
        sys.exit(1)
        
    prompt_arg = sys.argv[1]
    ask_agent(prompt_arg)
