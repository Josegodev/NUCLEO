from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        
        try:
            data = json.loads(body)
        except:
            data = {}

        response = {
            "tool": "echo",
            "input": data,
            "output": data
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

server = HTTPServer(("0.0.0.0", 8001), Handler)
print("MCP echo server running on :8001")
server.serve_forever()