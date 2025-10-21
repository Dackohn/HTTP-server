import os
import sys
import socket
import threading
import time
from urllib.parse import unquote, quote
from threading import Lock

MIME_TYPES = {
    ".html": "text/html",
    ".png": "image/png",
    ".pdf": "application/pdf",
}

request_counter = {}
counter_lock = Lock()

rate_limit_data = {}
rate_limit_lock = Lock()
RATE_LIMIT = 5


def generate_directory_listing(path, base_url):
    items = sorted(os.listdir(path))
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {base_url}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1 {{
            font-size: 32px;
            margin-bottom: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 800px;
            margin-top: 20px;
        }}
        th {{
            background-color: #f0f0f0;
            border: 1px solid #000;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            border: 1px solid #000;
            padding: 10px;
        }}
        td.hits {{
            text-align: right;
            width: 100px;
        }}
        a {{
            color: blue;
            text-decoration: underline;
        }}
        a:visited {{
            color: purple;
        }}
    </style>
</head>
<body>
    <h1>Directory listing for {base_url if base_url else '/'}</h1>
    <hr>
    <table>
        <tr>
            <th>File / Directory</th>
            <th>Hits</th>
        </tr>
"""
    if base_url.strip("/") != "":
        parent_url = os.path.dirname(base_url.rstrip("/"))
        if parent_url == "":
            parent_url = "/"
        html += f'        <tr><td colspan="2"><a href="{quote(parent_url)}">Back to parent directory</a></td></tr>\n'

    for item in items:
        
        if base_url == "/":
            item_url = f"/{item}"
        else:
            item_url = f"{base_url.rstrip('/')}/{item}"

        # Use the same item_url as the counter key
        lookup_key = item_url

        with counter_lock:
            count = request_counter.get(lookup_key, 0)

        full_item_path = os.path.join(path, item)
        if os.path.isdir(full_item_path):
            html += f'        <tr><td><a href="{quote(item_url)}/">{item}/</a></td><td class="hits">{count}</td></tr>\n'
        else:
            html += f'        <tr><td><a href="{quote(item_url)}">{item}</a></td><td class="hits">{count}</td></tr>\n'

    html += """    </table>
</body>
</html>
"""
    return html.encode()



def check_rate_limit(client_ip):
    """Check if the client has exceeded the rate limit."""
    with rate_limit_lock:
        now = time.time()
        if client_ip not in rate_limit_data:
            rate_limit_data[client_ip] = []
        rate_limit_data[client_ip] = [
            ts for ts in rate_limit_data[client_ip] if now - ts < 1.0
        ]
        if len(rate_limit_data[client_ip]) >= RATE_LIMIT:
            return False
        rate_limit_data[client_ip].append(now)
        return True


def handle_client(conn, base_dir, client_addr):
    client_ip = client_addr[0]
    
    if not check_rate_limit(client_ip):
        body = b"Rate limit exceeded"
        response = (
            b"HTTP/1.1 429 Too Many Requests\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + body
        )
        try:
            conn.sendall(response)
            conn.shutdown(socket.SHUT_WR)
        except Exception as e:
            print(f"Send error: {e}")
        finally:
            conn.close()
        return

    time.sleep(1)
    
    request = conn.recv(4096).decode("utf-8")
    if not request:
        conn.close()
        return
    
    parts = request.split()
    if len(parts) < 2:
        conn.close()
        return
    
    method, raw_path = parts[0], parts[1]
    path = unquote(raw_path)
    
    if method != "GET":
        conn.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
        conn.close()
        return
    
    # Always use normalized URL path starting with "/"
    key = "/" + path.strip("/")
    if key == "//":
        key = "/"  # root
    with counter_lock:
        if key not in request_counter:
            request_counter[key] = 0
        request_counter[key] += 1
        print(f"DEBUG: Incremented counter for '{key}'. Current value: {request_counter[key]}")
    
    target_path = os.path.join(base_dir, path.lstrip("/"))
    
    if os.path.isdir(target_path):
        body = generate_directory_listing(target_path, path)
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + body)
    elif os.path.isfile(target_path):
        ext = os.path.splitext(target_path)[1]
        mime = MIME_TYPES.get(ext, "application/octet-stream")
        try:
            with open(target_path, "rb") as f:
                data = f.read()
            header = f"HTTP/1.1 200 OK\r\nContent-Type: {mime}\r\nContent-Length: {len(data)}\r\n\r\n".encode()
            conn.sendall(header + data)
        except Exception as e:
            print(f"Error reading file: {e}")
            conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    else:
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    
    conn.close()




def main():
    if len(sys.argv) < 2:
        print("Usage: python server.py <directory>")
        return
    
    base_dir = sys.argv[1]
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 8000))
    server_socket.listen(10)
    print("Serving HTTP on port 8000 (multithreaded)...")
    
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, base_dir, addr))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    main()