# 🧠 AI Study Buddy

An advanced, full-stack, multimodal AI application that transforms raw lecture notes, PDFs, and syllabi into structured study guides, interactive 3D flashcards, and dynamic quizzes. Powered by Google's Gemini models and featuring a fully responsive, mobile-first design.

## ✨ Core Features

* **Multimodal Input Engine:** Process raw text, code blocks, images, or PDF documents.
* **Intelligent Summarization:** Generates structured Markdown study guides with explicit top-level concepts and an "Explain Like I'm 5" (ELI5) analogy section.
* **Interactive 3D Flashcards:** Automatically extracts key terms and definitions, rendering them into a CSS-driven 3D flip-card grid.
* **Quiz Runner:** Generates 4-option multiple-choice questions with real-time feedback and detailed explanations for the correct answers.
* **Dynamic Model Selection:** Choose between Gemini 2.5 Flash, Gemini 1.5 Flash-8B, and Gemini 1.5 Pro directly from the UI.
* **Mobile-First UI:** Fully responsive architecture featuring a sliding drawer sidebar and fluid layout for mobile study sessions.

---

## 🛠️ Tech Stack

**Frontend (Client)**
* Framework: Next.js (React)
* Styling: Tailwind CSS
* Deployment: Vercel

**Backend (API)**
* Framework: FastAPI (Python)
* Database ORM: SQLModel / SQLite
* AI Integration: Google GenAI SDK (Gemini API)
* Data Validation: Pydantic (Structured JSON Output)
* Deployment: Render

---

## ⚠️ Architecture & Deployment Notes (Read Before Using)

This application utilizes a synchronous HTTP request pipeline. If deployed on free-tier cloud providers (like Render), edge load balancers enforce a strict **100-second timeout** on all requests.

* **Safe Zone:** Text inputs and small PDFs (1 MB - 10 MB / ~10 to 150 pages). These will reliably process within 30-60 seconds.
* **Timeout Zone:** Massive PDFs (15 MB+ / 300+ pages). The Google Gemini API will successfully process the file in the background, but the cloud provider will sever the browser connection before the backend can return the result, resulting in an `ERR_CONNECTION_RESET` or `504 Gateway Timeout`.

To process massive textbooks without timeouts, clone the repository and run the backend **locally**, where time restrictions do not apply.

---

## 🚀 Local Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/AzeemAhmad-dev/ai-study-buddy.git](https://github.com/AzeemAhmad-dev/ai-study-buddy.git)
cd ai-study-buddy
```

### 2. Backend Setup
```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment Variables
# Create a .env file in the backend directory:
# GEMINI_API_KEY=your_google_gemini_api_key

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install

# Environment Variables
# Create a .env.local file in the frontend directory:
# NEXT_PUBLIC_API_URL=http://localhost:10000

# Start the Next.js development server
npm run dev
```

Visit `http://localhost:3000` in your browser to access the dashboard.

---

## 🗺️ Future Roadmap

* **Asynchronous Message Queues:** Implement Redis + Celery workers to handle massive textbook processing without relying on open HTTP connections.
* **Cloud Database Migration:** Transition from local SQLite to a hosted PostgreSQL instance for permanent, cross-device deck storage.
* **Authentication:** Integrate NextAuth.js for multi-tenant user login and private study deck isolation.

---

## 📄 License
This project is licensed under the MIT License.
