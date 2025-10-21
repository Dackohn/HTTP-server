import sys
import socket
import time
import threading
import re
import random



def crawl_links(host, port, path, visited=None):
    """Recursively visit all links starting from a directory."""
    if visited is None:
        visited = set()
    if path in visited:
        return
    visited.add(path)

    print(f"📂 Visiting: {path}")
    status_code, body = make_request(host, port, path)
    if status_code != 200:
        print(f"  Failed ({status_code})")
        return

    links = extract_links(body)
    for link in links:
        if not link.startswith("/"):
            if path.endswith("/"):
                link = path + link
            else:
                link = path + "/" + link

        link = link.replace("//", "/")

        if link.endswith("/"):
            crawl_links(host, port, link, visited)
        else:
            print(f"  Fetching file: {link}")
            code, _ = make_request(host, port, link)
            print(f"    → {code}")



def make_request(host, port, path):
    """Make a single HTTP request using raw sockets."""
    request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
    
    try:
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
        
        # Parse response
        header, _, body = response.partition(b"\r\n\r\n")
        header_str = header.decode("utf-8", errors="replace")
        
        # Extract status code
        status_line = header_str.split("\r\n")[0]
        status_code = int(status_line.split()[1]) if len(status_line.split()) > 1 else 0
        
        return status_code, body
    except Exception as e:
        print(f"Error making request to {path}: {e}")
        return 0, b""


def extract_links(html_content):
    """Extract all links from HTML content (files and directories)."""
    html_str = html_content.decode("utf-8", errors="replace")
    
    # Find all href attributes in <a> tags
    # Pattern: <a href="...">
    links = re.findall(r'<a\s+href="([^"]+)"', html_str, re.IGNORECASE)
    
    # Filter out parent directory links and external links
    valid_links = []
    for link in links:
        # Skip parent directory, external links, and anchors
        if link.startswith("http") or link.startswith("#") or "parent" in link.lower():
            continue
        valid_links.append(link)
    
    return valid_links


def test_concurrent_requests(host, port, num_requests=10, path="/"):
    """Test server with concurrent requests."""
    print(f"\n{'='*70}")
    print(f"Testing with {num_requests} concurrent requests")
    print(f"Target: http://{host}:{port}{path}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    results = []
    
    def worker(req_id):
        req_start = time.time()
        status_code, body = make_request(host, port, path)
        req_time = time.time() - req_start
        results.append({
            'id': req_id,
            'status': status_code,
            'time': req_time,
            'success': status_code == 200
        })
        print(f"  Request {req_id}: {status_code} - {req_time:.3f}s")
    
    # Create and start threads
    threads = []
    for i in range(num_requests):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = sum(1 for r in results if r['success'])
    avg_time = sum(r['time'] for r in results) / len(results)
    
    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Successful requests: {successful}/{num_requests}")
    print(f"  Average request time: {avg_time:.3f}s")
    print(f"  Throughput: {successful/total_time:.2f} requests/second")
    print(f"{'='*70}\n")
    
    return results


def test_rate_limiting(host, port):
    """Test rate limiting functionality."""
    print(f"\n{'='*70}")
    print("Testing Rate Limiting (300 requests/second)")
    print(f"{'='*70}\n")
    
    print("Test 1: Sending 10 concurrent requests (all at once)...")
    start = time.time()
    results = []
    
    def worker_rapid(req_id, results_list):
        status_code, body = make_request(host, port, "/")
        results_list.append(status_code)
        status_text = "OK" if status_code == 200 else "TOO MANY REQUESTS" if status_code == 429 else "ERROR"
        print(f"  Request {req_id+1}: {status_code} - {status_text}")
    
    threads = []
    for i in range(10):
        thread = threading.Thread(target=worker_rapid, args=(i, results))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start
    limited = sum(1 for s in results if s == 429)
    successful = sum(1 for s in results if s == 200)
    
    print(f"\nResult: {successful} successful, {limited} rate-limited")
    print(f"Time: {elapsed:.3f}s")
    if successful > 0:
        print(f"Throughput: {successful/elapsed:.2f} requests/second")
    print("\nWaiting 2 seconds for rate limit to reset...")
    time.sleep(2)
    
    print("\nTest 2: Sending 10 requests with controlled delay (0.25s between requests)...")
    start = time.time()
    results = []
    
    def worker_controlled(req_id, results_list, delay):
        time.sleep(delay) 
        status_code, body = make_request(host, port, "/")
        results_list.append(status_code)
        status_text = "OK" if status_code == 200 else "TOO MANY REQUESTS" if status_code == 429 else "ERROR"
        print(f"  Request {req_id+1}: {status_code} - {status_text}")
    
    threads = []
    for i in range(10):
        delay = i * 0.25 
        thread = threading.Thread(target=worker_controlled, args=(i, results, delay))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start
    limited = sum(1 for s in results if s == 429)
    successful = sum(1 for s in results if s == 200)

    print(f"\nResult: {successful} successful, {limited} rate-limited")
    print(f"Time: {elapsed:.3f}s")
    if successful > 0:
        print(f"Throughput: {successful/elapsed:.2f} requests/second")
    print(f"{'='*70}\n")


def test_random_links(host, port, num_clicks=5):
    """Fetch the root page and randomly click on links."""
    print(f"\n{'='*70}")
    print(f"Testing Random Link Navigation ({num_clicks} clicks)")
    print(f"{'='*70}\n")
    
    current_path = "/"
    visited_paths = []
    
    for click in range(num_clicks):
        print(f"\nClick {click + 1}: Fetching {current_path}")
        status_code, body = make_request(host, port, current_path)
        
        if status_code != 200:
            print(f"  ❌ Failed to fetch (status: {status_code})")
            break
        
        visited_paths.append(current_path)
        print(f"  ✓ Successfully fetched (status: {status_code})")
        
        links = extract_links(body)
        
        if not links:
            print(f"  No links found on this page. Stopping.")
            break
        
        print(f"  Found {len(links)} link(s): {links}")
        
        next_link = random.choice(links)
        print(f"  → Randomly selected: {next_link}")
        
        if not next_link.startswith("/"):

            if current_path.endswith("/"):
                current_path = current_path + next_link
            else:

                current_dir = "/".join(current_path.split("/")[:-1])
                current_path = current_dir + "/" + next_link if current_dir else "/" + next_link
        else:

            current_path = next_link
        

        current_path = current_path.replace("//", "/")
    
    print(f"\n{'='*70}")
    print(f"Navigation Summary:")
    print(f"  Visited {len(visited_paths)} page(s):")
    for i, path in enumerate(visited_paths, 1):
        print(f"    {i}. {path}")
    print(f"{'='*70}\n")


def test_counter(host, port, target_path="/", num_requests=40, max_workers=20):
    """Recursively access all links and make multiple requests to each, randomized order."""
    print(f"\n{'='*70}")
    print("Testing Recursive Request Counter (Concurrent + Randomized)")
    print(f"Starting from: {target_path}")
    print(f"Making {num_requests} requests per link in random order")
    print(f"{'='*70}\n")

    all_links = set()
    def collect_links(host, port, path):
        if path in all_links:
            return
        all_links.add(path)

        status_code, body = make_request(host, port, path)
        if status_code != 200:
            return

        links = extract_links(body)
        for link in links:
            if not link.startswith("/"):
                if path.endswith("/"):
                    link = path + link
                else:
                    link = path + "/" + link
            link = link.replace("//", "/")
            if link.endswith("/"):
                collect_links(host, port, link)
            else:
                all_links.add(link)

    collect_links(host, port, target_path)
    all_links = list(all_links)
    print(f"Found {len(all_links)} unique link(s)")

    requests_to_make = []
    for link in all_links:
        requests_to_make.extend([link] * num_requests)

    random.shuffle(requests_to_make)
    def worker(link):
        code, _ = make_request(host, port, link)
        print(f"Request to {link} → {code}")
        return code

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, link) for link in requests_to_make]
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # Step 4: Summary
    from collections import Counter
    counts = Counter(results)
    print(f"\n{'='*70}")
    print("Request Summary:")
    for status, count in counts.items():
        print(f"  Status {status}: {count} requests")
    print(f"{'='*70}\n")




def main():
    if len(sys.argv) < 3:
        print("Usage: python test_client.py <host> <port> [test_type]")
        print("\nTest types:")
        print("  concurrent  - Test concurrent request handling (default)")
        print("  ratelimit   - Test rate limiting")
        print("  counter     - Test request counter")
        print("  random      - Random link navigation")
        print("  all         - Run all tests")
        print("\nExamples:")
        print("  python test_client.py localhost 8000")
        print("  python test_client.py localhost 8000 ratelimit")
        print("  python test_client.py localhost 8000 all")
        return
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    test_type = sys.argv[3] if len(sys.argv) > 3 else "concurrent"
    
    print("="*70)
    print("HTTP SERVER TESTING CLIENT (Socket-based)")
    print("="*70)
    print(f"Target server: {host}:{port}")
    print(f"Test type: {test_type}\n")
    
    if test_type == "concurrent" or test_type == "all":
        test_concurrent_requests(host, port, num_requests=10)
    
    if test_type == "ratelimit" or test_type == "all":
        test_rate_limiting(host, port)
    
    if test_type == "counter" or test_type == "all":
        test_counter(host, port, target_path="/")
    
    if test_type == "random" or test_type == "all":
        test_random_links(host, port, num_clicks=5)
    
    print("\n" + "="*70)
    print("Testing complete!")
    print("="*70)


if __name__ == "__main__":
    main()