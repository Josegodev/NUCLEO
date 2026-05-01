import requests

url = "http://127.0.0.1:8001"

payload = {
    "message": "hola MCP"
}

r = requests.post(url, json=payload)

print(r.json())