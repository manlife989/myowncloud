# Local Cloud Server using LEMP Stack

## Overview
This project is an attempt to understand and design a **local cloud server** using dedicated storage space on a source device (server) as cloud storage that can be accessed by users through the internet.

The project is built using the **LEMP Stack**, with:

- **Linux** as the base operating system  
- **Nginx** as the web server  
- **MySQL** for database management  
- **PHP** for backend processing  

---

## Working Principle

### File Upload
When a user uploads a file to the cloud:

1. The file location, metadata, and identifying information are stored in the **MySQL database**.
2. The actual file is uploaded to the designated storage location on the server using a **POST request**.

---

### File Retrieval
When a user requests a particular file using its identifying information:

1. The server fetches the file location from the database.
2. A **GET request** is executed to retrieve and provide the requested file to the user.

---

### File Management
The project also supports:

- **UPDATE** functionality  
  - Modifies both the database records and stored server files.

- **DELETE** functionality  
  - Removes file data from both the database and the server storage.

---

## Tech Stack

| Component | Technology |
|----------|------------|
| Operating System | Linux |
| Web Server | Nginx |
| Database | MySQL |
| Backend | PHP |

---

## Features

- Local cloud storage system
- File upload and retrieval
- Metadata management using SQL
- Update and delete operations
- Internet-based accessibility
- LEMP stack implementation

---

## Upcoming Features

- Load balancing support
- AI-based suspicious activity detection system
- Enhanced scalability and security improvements

---

## Objective
The main objective of this project is to explore the implementation of a lightweight cloud storage architecture using locally hosted infrastructure while understanding backend server communication, database management, and file handling over the internet.
