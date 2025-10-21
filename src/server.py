import os
import sys
import socket
from urllib.parse import unquote,quote
import time

MIME_TYPES = {
    ".html": "text/html",
    ".png": "image/png",
    ".pdf": "application/pdf",
}

def generate_directory_listing(path, base_url):
    items = sorted(os.listdir(path))
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {base_url}</title>
</head>
<body>
    <h1>Directory listing for {base_url}</h1>
    <hr>
    <ul>
"""

    if base_url.strip("/") != "":
        parent_url = os.path.dirname(base_url.rstrip("/"))
        if parent_url == "":
            parent_url = "/"
        html += f'        <li><a href="{quote(parent_url)}">Back to parent directory</a></li>\n'


    for item in items:
        item_path = os.path.join(base_url, item).replace("\\", "/")
        if os.path.isdir(os.path.join(path, item)):
            html += f'        <li><a href="{item_path}/">{item}/</a></li>\n'
        else:
            html += f'        <li><a href="{item_path}">{item}</a></li>\n'

    html += """    </ul>
    <hr>
</body>
</html>
"""
    return html.encode()

def handle_client(conn, base_dir):
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
    time.sleep(1)
    target_path = os.path.join(base_dir, path.lstrip("/"))
    if os.path.isdir(target_path):
        body = generate_directory_listing(target_path, path)
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + body)
    elif os.path.isfile(target_path):
        ext = os.path.splitext(target_path)[1]
        mime = MIME_TYPES.get(ext, None)
        if not mime:
            conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
        else:
            with open(target_path, "rb") as f:
                data = f.read()
            header = f"HTTP/1.1 200 OK\r\nContent-Type: {mime}\r\n\r\n".encode()
            conn.sendall(header + data)
    else:
        conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python server.py <directory>")
        return

    base_dir = sys.argv[1]
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 8000))
    server_socket.listen(10)

    print("Serving HTTP on port 8000...")

    while True:
        conn, _ = server_socket.accept()
        handle_client(conn, base_dir)

if __name__ == "__main__":
    main()