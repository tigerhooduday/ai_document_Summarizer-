
# 📄 AI Document Summarization Service  
A full-stack LLM-powered document summarizer built with **FastAPI**, **Python**, **React (Vite)**, **Groq/OpenAI**, and deployed on **Google Cloud Run** + **Hostinger**.

This project was created as a coding assignment to demonstrate:
- Backend API design  
- LLM integration  
- Document/file processing  
- Frontend UI development  
- Deployment & DevOps skills  
- Clean project structure & error handling  

---

## 🚀 Features

### ✅ Upload or paste text  
Supports:
- Plain text  
- PDF  
- Word (.docx)  
- Markdown  
- Images (OCR optional if added later)  
- And more  

### ✅ Summarization styles  
- **Brief**
- **Detailed**
- **Bullet points**

### ✅ LLM integration
Supports:
- **Groq (Llama 3.1/3.2/3.3 models)**  
- **OpenAI (fallback option)**  
- **Local stub mode** for testing without API cost

### ✅ Modern UI  
- Glassmorphism + light theme  
- Mobile-responsive  
- Drag-and-drop file upload  
- Real-time status + error messages  
- Clean designer-style interface  

### ✅ Full error handling  
- Size validation  
- Invalid extension  
- LLM quota/rate limit fallback  
- CORS rules  
- Cloud Run logging  

### ✅ Deployment  
- **Backend:** Google Cloud Run (Docker container)  
- **Frontend:** Hostinger static hosting  

---

## 🏗️ Tech Stack

### **Frontend**
- React (Vite)
- JSX components
- Glassy UI with CSS
- Fetch API for backend calls

### **Backend**
- Python 3.11
- FastAPI
- Uvicorn
- Groq API client
- OpenAI (optional)
- python-multipart, aiofiles
- Docker

### **DevOps**
- Google Artifact Registry
- Google Cloud Build
- Google Cloud Run
- Hostinger static hosting
- Environment variables via Secret Manager / Cloud Run

---

## 📁 Project Structure

```

Project-Assignment/
├── README.md
├── LICENSE
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       ├── services/api.js
│       └── styles/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── cloudbuild.yaml
│   ├── app/
│   │   ├── main.py
│   │   ├── api/summarize.py
│   │   ├── services/llm_client.py
│   │   └── models/schemas.py
│   └── README_BACKEND.md
└── .gitignore

````

---

## 🔧 Backend Setup (Local)

### 1. Create virtual env
```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

```
USE_GROQ=true
GROQ_API_KEY=your-api-key
GROQ_MODEL=llama-3.3-70b-versatile
FRONTEND_ALLOW_ORIGINS=http://localhost:5173
BACKEND_PORT=8000
```

### 4. Run locally

```bash
uvicorn app.main:app --reload --port 8000
```

Visit:

```
http://localhost:8000
http://localhost:8000/docs
```

---

## 🎨 Frontend Setup (Local)

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Create `.env`

```
VITE_API_BASE=http://localhost:8000
```

### 3. Run dev mode

```bash
npm run dev
```

---

## ☁️ Deployment

### 🚀 **Backend → Google Cloud Run**

#### 1. Build and push image

```bash
gcloud builds submit --config cloudbuild.yaml --project=ai-projectbackend --region=asia-south2
```

#### 2. Deploy

```bash
gcloud run deploy ai-document-summarizer \
  --image="asia-south2-docker.pkg.dev/ai-projectbackend/ai-document-summarizer/ai-document-summarizer:BUILD_ID" \
  --platform=managed --region=asia-south2 \
  --allow-unauthenticated --memory=256Mi \
  --set-env-vars="FRONTEND_ALLOW_ORIGINS=*"
```

#### 3. Cloud Run URL

```
https://ai-document-summarizer-xxxxx.asia-south2.run.app
```

---

### 🎯 **Frontend → Hostinger Deployment**

1. Build the frontend:

```bash
npm run build
```

2. Upload `dist/` folder to:

```
public_html/Project/AI/ai_document_Summarizer/
```

3. Update API URL via:

```
VITE_API_BASE=https://your-cloud-run-url
```

4. Done ✔

---

## 🔐 Environment Variables

| Variable                 | Description                     |
| ------------------------ | ------------------------------- |
| `USE_GROQ`               | Enable Groq provider            |
| `GROQ_API_KEY`           | Groq API key                    |
| `GROQ_MODEL`             | e.g. llama-3.3-70b-versatile    |
| `OPENAI_API_KEY`         | optional                        |
| `FRONTEND_ALLOW_ORIGINS` | CORS allowed origins            |
| `BACKEND_PORT`           | backend port (Cloud Run = 8080) |

---

## 📡 API — `/api/summarize`

### **POST** `/api/summarize`

**Request body (text mode):**

```json
{
  "text": "Your text...",
  "style": "brief"
}
```

**Request body (file mode):**

```
multipart/form-data:
  file: <uploaded-file>
  style: brief | detailed | bullets
```

**Response:**

```json
{
  "summary": "Generated summary text..."
}
```

---


---

## 📝 License

MIT License — see LICENSE file.

---

## ✨ Author

**Uday Garg**
Portfolio: [https://www.udaygarg.com](https://www.udaygarg.com)
AI Projects | Web Development | Cloud Engineering


````
