# Laboratory Report: HTTP Server & Client

## 1. Source Directory

The source directory consists of two files [server\.py](https://github.com/Dackohn/HTTP-server/blob/master/src/server.py) that is responsible for all the web server stuff, receiving requests and responding to them and a [client\.py](https://github.com/Dackohn/HTTP-server/blob/master/src/client.py) that initiates the comunication and the requests, as well as downloading fileas and printing the contents of html files.
### [Source Directory](https://github.com/Dackohn/HTTP-server/tree/master/src)

## 2. Docker Compose & Dockerfile

The docker compose and dockerfile are really straight forward for this laboratory work only copying the necesary server and client files into the container as well as mounting the repository that is meant to be visible on the web page.

### [Docker Compose](https://github.com/Dackohn/HTTP-server/blob/master/docker-compose.yml)

### [Dockerfile](https://github.com/Dackohn/HTTP-server/blob/master/Dockerfile)

---

## 3. Starting the Container

The container is started by simply running the command ```docker compose up --build -d```

![Container Start Screenshot](docks/build_container.png){: width=300}

---

## 4. Running the Server

The command that is use to run the server is ```python server.py <served_directory>```. The current docker_compose runs the command automaticaly when the container is created:
![Server Start Command](docks/server_start.png){: width=300}

## 5. Contents of the Served Directory

Accessing the main endpoint of the server displays all files and folders in the served directory, sorted alphabetically, as shown in the image below:
![Served dyrectory](docks/served_directory.png){: width=300}

## 5. Accesing different types of files
### 404 Error
This screenshot demonstrates the server's response when attempting to access a file that does not exist. The server correctly returns a 404 Not Found error.
![Inexistent file](docks/inexistend_file.png){: width=300}

### HTML File with Image
This screenshot shows how the server serves an HTML file containing an embedded image. The page is rendered correctly in the browser, displaying both the HTML content and the image.
![HTML with image](docks/html_with_image.png){: width=300}

### PDF File
This image illustrates the server delivering a PDF file. The PDF is accessible and can be opened or downloaded by the client.
![PDF file](docks/pdf_file.png){: width=300}

### PNG File
This screenshot shows the server serving a PNG image. The image loads correctly in the browser, demonstrating proper handling of binary file types.
![PNG file](docks/png_file.png){: width=300}
