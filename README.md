# SecAI

> A fully local AI assistant with Retrieval-Augmented Generation (RAG), document chat, and streaming responses powered by Ollama, ChromaDB, FastAPI, React, and Docker.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)

---

## Overview

SecAI is a privacy-first local AI assistant that runs entirely on your own machine.

Developed as an internship project at **Necurity Solutions**, the goal of SecAI is to demonstrate how a production-style Retrieval-Augmented Generation (RAG) system can be built using open-source technologies while keeping all data and AI inference local.

No cloud APIs.

No subscription fees.

No external data sharing.

Users can upload their own documents, ask questions about them, and receive answers with source citations generated from the actual content of those documents.

---

## Features

### General AI Chat

* Local conversational AI using Mistral via Ollama
* Real-time streaming responses using Server-Sent Events (SSE)
* Persistent chat history
* Multiple chat threads

### RAG Document Assistant

* Upload personal documents
* Semantic search using embeddings
* Context-aware responses
* Source citations included in answers
* Per-user document isolation

### Supported File Types

* PDF
* DOCX
* XLSX
* TXT
* CSV

### Authentication & Security

* JWT Authentication
* Password hashing
* Redis-based token revocation
* User-level document isolation

### Fully Local Deployment

* No OpenAI API
* No cloud vector database
* No external AI services
* All data remains on your machine

---

## Architecture

```text
Browser
   │
   ▼
Nginx
   │
   ├── React Frontend
   │
   └── FastAPI Backend
           │
           ├── PostgreSQL
           ├── Redis
           ├── ChromaDB
           └── Ollama (Host Machine)
```

---

## Tech Stack

### Frontend

* React
* Vite
* Tailwind CSS
* Axios

### Backend

* FastAPI
* SQLAlchemy
* Alembic
* Pydantic

### AI & RAG

* Ollama
* Mistral
* LangChain
* ChromaDB
* Sentence Transformers
* all-MiniLM-L6-v2

### Infrastructure

* Docker
* Docker Compose
* Nginx
* PostgreSQL
* Redis

---

## Project Structure

```text
secai/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── routers/
│   │   └── utils/
│   │
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
│
├── nginx/
├── uploads/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Core Workflow

### Document Ingestion Pipeline

```text
Upload File
     │
     ▼
Text Extraction
     │
     ▼
Chunking
     │
     ▼
Embedding Generation
     │
     ▼
ChromaDB Storage
```

### RAG Query Pipeline

```text
User Question
      │
      ▼
Generate Query Embedding
      │
      ▼
ChromaDB Similarity Search
      │
      ▼
Retrieve Relevant Chunks
      │
      ▼
Build Context
      │
      ▼
Mistral via Ollama
      │
      ▼
Stream Response + Citations
```

---

## Supported Document Processing

| File Type | Processing Library |
| --------- | ------------------ |
| PDF       | pdfplumber         |
| DOCX      | python-docx        |
| XLSX      | openpyxl           |
| TXT       | Native Reader      |
| CSV       | Python csv         |

---

## Getting Started

### Prerequisites

Install the following:

* Docker Desktop
* Git
* Ollama

---

### Install Ollama

#### Linux / macOS

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows

Download and install from:

https://ollama.com

Pull the default model:

```bash
ollama pull mistral
```

Verify installation:

```bash
ollama run mistral
```

---

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/secai.git

cd secai
```

---

## Configuration

A complete `.env.example` file is included in the repository.

Copy it to `.env` and adjust values if required for your environment.

---

## Run the Project

Build and start all services:

```bash
docker compose up --build
```

---

## Services

| Service         | Port  |
| --------------- | ----- |
| Frontend        | 80    |
| FastAPI Backend | 8000  |
| PostgreSQL      | 5432  |
| Redis           | 6379  |
| ChromaDB        | 8000  |
| Ollama          | 11434 |

---

## API Overview

### Authentication

```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### Documents

```http
POST   /api/files/upload
GET    /api/files
GET    /api/files/{id}/status
DELETE /api/files/{id}
```

### Chat

```http
POST   /api/chat/threads
GET    /api/chat/threads
DELETE /api/chat/threads/{id}

GET    /api/chat/threads/{id}/messages

GET    /api/chat/threads/{id}/stream
```

---

## Security Design

Each user receives an isolated ChromaDB collection:

```text
user_{user_id}
```

Every document and chat operation is ownership-validated before access is granted.

This ensures users cannot access another user's documents, embeddings, or chat history.

---

## Performance Targets

| Metric                 | Target       |
| ---------------------- | ------------ |
| First Token Latency    | < 5 seconds  |
| API Response Time      | < 200 ms     |
| 10 Page PDF Processing | < 30 seconds |
| Maximum Upload Size    | 50 MB        |

---

## Future Improvements

* Hybrid search combining vector and keyword retrieval
* Conversation memory
* OCR support for scanned PDFs
* Document summarization
* Knowledge graph integration
* Local model switching
* GPU acceleration options
* Advanced citation ranking
* Multi-document retrieval optimization

---

## Acknowledgements

This project was developed as part of an internship at **Necurity Solutions Network Security Private Ltd**.

The project explores modern AI application architecture including local LLM deployment, Retrieval-Augmented Generation, vector databases, semantic search, document processing, and real-time streaming systems.

---

## Author
**Subash Venkat**
