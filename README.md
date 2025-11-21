
# 🌟 **AI Document Summarizer**

A modern, fast, cloud-ready LLM-powered service for summarizing documents with multiple styles and multi-file support.

> Built with **React + Vite**, **FastAPI**, **Groq LLaMA**, and deployed on **Google Cloud Run** + **Hostinger**.
> A clean, production-ready architecture suitable for scaling future AI projects.

---

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Backend-FastAPI-brightgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/LLM-Groq%20LLaMA3-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Deployed%20On-Google%20Cloud%20Run-yellow?style=for-the-badge"/>
</p>

---

# 📌 **Table of Contents**

* [✨ Overview](#-overview)
* [🧠 Features](#-features)
* [📐 Architecture](#-architecture)
* [🧰 Tech Stack](#-tech-stack)
* [⚙️ Setup Instructions](#️-setup-instructions)

  * [Backend Setup](#1-backend-setup-fastapi--groq)
  * [Frontend Setup](#2-frontend-setup-react--vite)
* [🚀 Deployment](#-deployment)
* [📝 Brief Explanation – Approach & Design Decisions](#-brief-explanation--approach--design-decisions)
* [📷 Screenshots](#-screenshots)
* [📄 License](#-license)

---

# ✨ **Overview**

The **AI Document Summarizer** allows users to upload text or documents and instantly generate:

* **Brief summaries**
* **Detailed summaries**
* **Bullet-style summaries**

It supports multiple file formats:

`TXT, PDF, DOCX, Markdown, JSON, CSV`

The backend uses **Groq LLaMA-3.3 (70B)** for extremely fast inference, and the frontend features a **beautiful glassy UI** that is mobile-friendly.

---

# 🧠 **Features**

### ✔ Upload multiple document formats

TXT, PDF, DOCX, MD, JSON, CSV

### ✔ LLM-Powered Summaries

Using **Groq LLaMA3.3-70B** (free & fast)

### ✔ Three summary modes

* **Brief**
* **Detailed**
* **Bullet Points**

### ✔ Beautiful modern UI

Glassy, responsive, elegant, creative.

### ✔ Cloud-Ready Architecture

Backend → Google Cloud Run
Frontend → Hostinger

### ✔ Handles errors gracefully

Quota errors, invalid file, timeout, etc.

---

# 📐 **Architecture**

```
                         ┌────────────────────────┐
                         │        Frontend        │
                         │  React + Vite (UI)     │
                         │  Hostinger Static Site │
                         └───────────┬────────────┘
                                     │ HTTPS
                                     ▼
                     ┌─────────────────────────────────┐
                     │            Backend              │
                     │        FastAPI + Uvicorn        │
                     │  Cloud Run (Docker Container)   │
                     └───────────┬─────────────────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │      Groq Cloud      │
                      │  (LLaMA 3.3 70B)     │
                      └──────────────────────┘
```

---

# 🧰 **Tech Stack**

### **Frontend**

* React (JSX)
* Vite
* Tailwind-like custom styling
* Glassmorphic UI

### **Backend**

* Python 3.11
* FastAPI
* Uvicorn
* Groq SDK
* File parsers (pdfplumber, python-docx, markdown, csv, json)

### **Deployment**

* Google Cloud Run (Docker)
* Google Artifact Registry
* Hostinger Static Hosting (for frontend)
* gcloud CLI + Cloud Build

---
# 📁 Project Structure

Project-Assignment/
├── README.md
├── LICENSE
├── frontend/
│ ├── package.json
│ ├── vite.config.js
│ ├── public/
│ └── src/
│ ├── App.jsx
│ ├── main.jsx
│ ├── components/
│ ├── services/api.js
│ └── styles/
├── backend/
│ ├── Dockerfile
│ ├── requirements.txt
│ ├── cloudbuild.yaml
│ ├── app/
│ │ ├── main.py
│ │ ├── api/summarize.py
│ │ ├── services/llm_client.py
│ │ └── models/schemas.py
│ └── README_BACKEND.md
└── .gitignore

---------

# ⚙️ **Setup Instructions**

## 1️⃣ **Backend Setup (FastAPI + Groq)**

### **Clone repo**

```bash
git clone https://github.com/tigerhooduday/ai_document_Summarizer-/
cd backend
```

### **Create virtual env**

```bash
python -m venv .venv
source .venv/bin/activate   # Mac
.venv\Scripts\activate      # Windows
```

### **Install dependencies**

```bash
pip install -r requirements.txt
```

### **Create `.env`**

```
USE_GROQ=true
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### **Run server**

```bash
uvicorn app.main:app --reload
```

### 🚀 Local API Endpoint

```
http://localhost:8000/api/summarize
```

---

## 2️⃣ **Frontend Setup (React + Vite)**

### **Go to frontend folder**

```bash
cd frontend
```

### **Install dependencies**

```bash
npm install
```

### **Create `.env`**

```
VITE_API_BASE=http://localhost:8000
```

### **Run frontend**

```bash
npm run dev
```

---

# 🚀 **Deployment**

### **Backend (Google Cloud Run)**

Uses:

* Dockerfile
* cloudbuild.yaml
* Artifact Registry
* Cloud Run

### To deploy:

```bash
gcloud builds submit --config cloudbuild.yaml --project <projectname>
gcloud run deploy ai-document-summarizer \
  --image <latest-image-url> \
  --region asia-south2 \
  --allow-unauthenticated
```

### **Frontend (Hostinger)**

1. Build frontend:

   ```bash
   npm run build
   ```
2. Upload `dist/` folder to Hostinger File Manager
3. Set environment variable:

   ```
   VITE_API_BASE="https://your-cloudrun-url"
   ```

---

# 📝 **Brief Explanation – Approach & Design Decisions**

### **1. Clear separation of frontend and backend**

* React handles UI/UX
* FastAPI handles summarization API
* Makes deployment modular
* Easier scaling for future AI tools

### **2. Groq selected as LLM provider**

* OpenAI quota issues → fallback to Groq
* Groq is **fast**, **free**, and supports **OpenAI-compatible API**
* Ideal for workloads needing high speed

### **3. Multi-file support**

Backend supports:

* TXT → direct read
* PDF → pdfplumber extraction
* DOCX → python-docx
* Markdown → markdown lib
* CSV & JSON → structured content extraction

### **4. Solid error handling**

* Handles invalid file format
* Handles empty text
* Handles LLM quota errors
* Returns user-friendly messages

### **5. Modern UI with glassmorphism**

* Clean, creative, aesthetic
* Mobile-friendly
* Smooth interactions
* Encourages ease of use

### **6. Correct CORS & Cloud-Ready Deployment**

* CORS controlled via Cloud Run env variable
* Cloud Run handles scaling & traffic
* Zero idle cost (min-instances=0)
* Frontend communicates via environment-specified API

### **7. Future extensibility**

This architecture allows easily adding:

* OCR
* RAG summarization
* AI chat
* Embedding generator
* Multiple AI providers

---



# 📄 **License**

MIT License
You are free to use, modify, and distribute this project.


