# byteVision – AI-Powered Objectives & Key Results (OKR) Management Platform

An enterprise-grade AI-powered Objectives and Key Results (OKR) management platform inspired by Microsoft Viva Goals. Built using React, FastAPI, LangGraph, and SQLite, the platform leverages Agentic AI to automate objective planning, intelligent task decomposition, progress tracking, deadline optimization, and AI-powered recommendations.

---

## 🚀 Features

- AI-powered Objective & Key Result (OKR) Management
- Agentic AI Workflow using LangGraph
- Automatic Task & Subtask Generation
- Intelligent Goal Planning
- AI Recommendation Engine
- Smart Deadline Scheduling
- Progress Tracking & Analytics
- Dashboard with Real-Time Insights
- Automated Reminder & Notification System
- RESTful API Architecture
- Responsive React + Material UI Interface
- Modular & Scalable Backend

---

## 🏗️ System Architecture

```
React.js Frontend
        │
        ▼
 FastAPI REST APIs
        │
        ▼
 LangGraph AI Agents
        │
        ▼
 SQLite Database
        │
        ▼
 Reminder Scheduler
```

---

## 💻 Technology Stack

### Frontend
- React.js
- Material UI
- Axios
- React Markdown

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic

### AI Layer
- LangGraph
- LangChain
- Google Gemini
- OpenAI Compatible Models

### Database
- SQLite

### Tools
- Git
- GitHub
- VS Code

---

## 📌 Core Modules

### 🎯 Objective Management
- Create and manage Objectives
- AI-assisted objective creation
- Automatic task decomposition

### 📋 Task Management
- Task & Subtask Management
- Progress Monitoring
- Deadline Optimization
- Status Tracking

### 🤖 AI Agent Workflow

- Input Analysis
- Objective Planning
- Task Planning
- Weight Assignment
- Schedule Generation
- Progress Analysis
- Recommendation Generation

### 📊 Dashboard

- Overall Progress
- Objective Analytics
- Task Status
- Due Tasks
- Reminder Dashboard

### 🔔 Notification System

- Automated Reminders
- Due Date Alerts
- Deadline Notifications

---

## 📂 Project Structure

```
byteVision
│
├── frontend
│   ├── components
│   ├── pages
│   ├── services
│   └── assets
│
├── backend
│   ├── api
│   ├── agents
│   ├── database
│   ├── scheduler
│   ├── models
│   └── services
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/your-username/byteVision-AI-OKR-Management-System.git

cd byteVision-AI-OKR-Management-System
```

### Backend

```bash
pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm start
```

---

## 🔮 Future Enhancements

- JWT Authentication
- Role-Based Access Control (RBAC)
- Team Collaboration
- Slack Integration
- Microsoft Teams Integration
- Google Calendar Sync
- Docker Deployment
- Kubernetes
- PostgreSQL
- Cloud Deployment
- Mobile Application
- Predictive Analytics
- AI Performance Forecasting

---

## 🎯 Project Highlights

- Full Stack Web Application
- Agentic AI Workflow
- Enterprise Dashboard
- REST API Architecture
- Intelligent Goal Planning
- Smart Task Automation
- Modular Architecture
- Real-Time Analytics
- Responsive UI
- Scalable Design

---

## 📖 Inspiration

Inspired by **Microsoft Viva Goals**, this project extends traditional OKR management by integrating Agentic AI to automate planning, execution, monitoring, and intelligent decision-making.

---

## 👨‍💻 Developer

**Vishnu K**

**Full Stack Developer | AI Engineer**

### Skills

- React.js
- FastAPI
- Python
- LangGraph
- LangChain
- SQL
- REST APIs
- Material UI
- Git
- GitHub

---

## 📄 License

This project is developed for educational, research, and portfolio purposes.

==============================================================================================================================================================================================================
<!-- # Viva Goals-Inspired OKR Tracker Frontend

This is a modern, interactive React frontend for your OKR/goal management system, inspired by Microsoft Viva Goals.

## Features
- Create, view, and manage objectives, tasks, and subtasks
- AI-powered input and task generation
- Progress tracking and review flows
- Reminders for upcoming/incomplete subtasks
- Professional, enterprise-grade UI (Material-UI)

## Setup

1. **Install dependencies:**

   ```sh
   cd frontend
   npm install
   ```

2. **Start the development server:**

   ```sh
   npm start
   ```

   The app will run at [http://localhost:3000](http://localhost:3000).

3. **Backend requirements:**
   - The backend API (FastAPI, see `api_server.py`) must be running and accessible at the same host/port or proxied to `/api` and `/reminders` endpoints.
   - See backend files for API details.

## Project Structure
- `src/components/ObjectiveForm.js` — Create new objectives
- `src/components/ObjectivesDashboard.js` — List and track objectives
- `src/components/TasksView.js` — View/manage tasks and subtasks
- `src/components/RemindersPanel.js` — Check reminders
- `src/App.js` — Main app shell and navigation

## Customization
- The UI uses Material-UI and can be themed via `src/index.js`.
- API endpoints can be changed in the axios calls if your backend is hosted elsewhere.

---

For any issues, ensure your backend is running and accessible. The frontend expects the API described in `api_server.py`.  -->

