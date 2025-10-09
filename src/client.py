import sys
import socket
import os

def main():
    if len(sys.argv) < 4:
        print("Usage: python client.py <server_host> <server_port> <filename> [subdir]")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]
    subdir = sys.argv[4] if len(sys.argv) > 4 else ""

    download_dir = os.path.join("contents", subdir)
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

    if filename.lower().endswith(".html"):
        print(body.decode("utf-8", errors="replace"))
        return
    print("CWD:", os.getcwd())
    print("download_dir:", download_dir)

    os.makedirs(download_dir, exist_ok=True)
    output_path = os.path.join(download_dir, os.path.basename(filename))
    with open(output_path, "wb") as f:
        f.write(body)

    print(f"Downloaded: {output_path}, download_di: {download_dir}")

if __name__ == "__main__":
    main()
