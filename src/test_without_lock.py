import os
import sys
import socket
import threading
import time
from urllib.parse import unquote, quote
from collections import defaultdict

MIME_TYPES = {
    ".html": "text/html",
    ".png": "image/png",
    ".pdf": "application/pdf",
}

request_counter_naive = defaultdict(int)

request_counter_safe = defaultdict(int)
counter_lock = threading.Lock()

USE_SAFE_VERSION = False 


def generate_directory_listing(path, base_url):
    items = sorted(os.listdir(path))
    counter_type = "Thread-Safe" if USE_SAFE_VERSION else "Naive (Race Condition)"
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {base_url}</title>
</head>
<body>
    <h1>Directory listing for {base_url}</h1>
    <p><strong>Counter Type: {counter_type}</strong></p>
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
        full_path = os.path.join(path, item)
        
        # Just display counter without increment
        count = request_counter_safe[full_path] if USE_SAFE_VERSION else request_counter_naive[full_path]
        
        if os.path.isdir(full_path):
            html += f'        <li><a href="{item_path}/">{item}/</a> <em>(Requests: {count})</em></li>\n'
        else:
            html += f'        <li><a href="{item_path}">{item}</a> <em>(Requests: {count})</em></li>\n'
    
    html += """    </ul>
    <hr>
</body>
</html>
"""
    return html.encode()




def increment_counter_naive(key):
    """UNSAFE: Increment counter without synchronization.
    
    This demonstrates a race condition. The increment operation consists of:
    1. Read current value
    2. Add 1
    3. Write new value
    
    When multiple threads execute this simultaneously, they can interleave,
    causing lost updates.
    """
    # Add artificial delay to make race condition more visible
    current = request_counter_naive[key]
    time.sleep(0.001)  # Simulate some processing time
    request_counter_naive[key] = current + 1


def increment_counter_safe(key):
    """SAFE: Increment counter with lock synchronization.
    
    The lock ensures that only one thread can execute the critical section
    at a time, preventing lost updates.
    """
    with counter_lock:
        current = request_counter_safe[key]
        time.sleep(0.001)  # Same delay, but protected by lock
        request_counter_safe[key] = current + 1


def handle_client(conn, base_dir, client_addr):
    """Handle a single client connection."""
    request = conn.recv(4096).decode("utf-8")
    if not request:
        conn.close()
        return
    time.sleep(0.2)
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
    
    target_path = os.path.join(base_dir, path.lstrip("/"))
    
    # Increment counter here for directories and files
    if USE_SAFE_VERSION:
        increment_counter_safe(target_path)
    else:
        increment_counter_naive(target_path)
    
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
    global USE_SAFE_VERSION
    
    if len(sys.argv) < 2:
        print("Usage: python server_race_demo.py <directory> [--safe]")
        print("  --safe: Use thread-safe counter (default: naive version with race condition)")
        return
    
    base_dir = sys.argv[1]
    if "--safe" in sys.argv:
        USE_SAFE_VERSION = True
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 8001))
    server_socket.listen(10)
    
    version = "SAFE (with locks)" if USE_SAFE_VERSION else "NAIVE (race condition)"
    print(f"Serving HTTP on port 8001 ({version})...")
    print(f"\nTo test the race condition:")
    print(f"1. Run this server (current mode: {version})")
    print(f"2. Run: python test_race.py")
    print(f"3. Compare expected vs actual counter values")
    print(f"4. Restart with --safe flag to see the fix\n")
    
    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, base_dir, addr))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    main()