import sys
import socket
import os

def main():
    if len(sys.argv) < 4:
        print("Usage: python client.py <server_host> <server_port> <filename>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]

    request = f"GET /{filename} HTTP/1.0\r\nHost: {host}\r\n\r\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(request.encode("utf-8"))

    response = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response += chunk
    s.close()

    header, _, body = response.partition(b"\r\n\r\n")

    os.makedirs("contents/downloads", exist_ok=True)
    output_path = os.path.join("contents/downloads", os.path.basename(filename))
    with open(output_path, "wb") as f:
        f.write(body)

    print(f"Downloaded: {output_path}")

if __name__ == "__main__":
    main()
