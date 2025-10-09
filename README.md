<div align="center">

# 💰 **Personal Finance Advisor**  

<img src="[https://github.com/user-attachments/assets/your-banner-image-id](https://github.com/MadhuryaPasan/Personal-Finance-Advisor.git)" alt="Personal Finance Advisor Banner" width="800"/>

### 🧠 AI-Powered Personal Finance Management System  
Seamlessly manage your **expenses**, **budgets**, and **savings goals** — powered by **Streamlit**, **FastAPI**, and **Machine Learning**.

---

[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Language-Python-3670A0?logo=python)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ⚙️ **Overview**

**Personal Finance Advisor** is an intelligent system that simplifies financial management with AI.  
It helps users:
- 🧾 Automatically **categorize expenses**
- 🎯 **Plan and track savings goals**
- 💰 **Create and monitor budgets**

All accessible through a beautiful **Streamlit dashboard** and a robust **FastAPI backend**.

---

## 🧠 **Core AI Agents**

| Agent | Description | Icon |
|:------|:-------------|:----:|
| **💳 Expense Categorizer Agent** | Uses AI/ML to analyze transaction text and automatically classify it into categories | 🤖 |
| **📊 Budget Tracker Agent** | Monitors monthly spending against limits and alerts when overspending | 📈 |
| **🎯 Saving Goal Planner Agent** | Helps users plan savings goals and calculate required contributions | 💰 |

---

## 🚀 **Key Features**

- 🤖 AI-driven **Expense Categorization**  
- 🎯 Smart **Goal Tracking** with real-time feedback  
- 💸 Customizable **Budget Management**  
- 🔐 Secure **Google OAuth Login**  
- ⚙️ Comprehensive **RESTful API**  
- 📊 Interactive **Streamlit Dashboard**

---

## 🏗️ **Architecture**

| Component | Technology |
|------------|-------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **Authentication** | Google OAuth + JWT |
| **AI/ML** | Expense Categorization Model |

---

## 📋 **Prerequisites**

- Python **3.8+**
- `pip` package manager  
- Google OAuth credentials  

---

## ⚙️ **Installation & Setup**

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/Personal-Finance-Advisor.git
cd Personal-Finance-Advisor
````

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
pip install google-auth google-auth-oauthlib
```

### 3️⃣ Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Google+ API**
3. Generate **OAuth 2.0 credentials**
4. Download `credentials.json` → place it in your project root

---

## 🧩 **Running the Application**

### ▶️ Start Streamlit Frontend

```bash
streamlit run app.py
```

### ▶️ Start FastAPI Backend

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 🌐 Access

* **Frontend:** [http://localhost:8501](http://localhost:8501)
* **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 **JWT Authentication Setup**

1. Run the Streamlit app
2. Login with your **Google account**
3. Go to the **ExpenseCat** page
4. Copy your **JWT Token** for Postman or API testing

> 💡 *JWT token regenerates every time Streamlit restarts. Always use a new one.*

---

## 🧪 **API Testing Guide (Postman)**

### 📬 Headers

| Key             | Value                     |
| --------------- | ------------------------- |
| `Content-Type`  | `application/json`        |
| `Authorization` | `Bearer <your_jwt_token>` |

---

### 🔍 Health Check

```http
GET http://localhost:8000/health
```

---

### 💳 Expense Categorizer Agent

```http
POST http://localhost:8000/predict
```

**Body:**

```json
{
  "transaction": "car service rs 1000"
}
```

---

### 🎯 Create Financial Goal

```http
POST http://localhost:8000/create_goal
```

**Body:**

```json
{
  "goal_name": "Vacation",
  "target_amount": 5000.0,
  "deadline": "2026-01-01",
  "current_savings": 1000.0
}
```

---

### 📈 Track Goal Progress

```http
POST http://localhost:8000/track_goal
```

**Body:**

```json
{
  "goal": {
    "goal_name": "Vacation",
    "target_amount": 5000.0,
    "deadline": "2026-01-01",
    "current_savings": 1000.0,
    "remaining_amount": 4000.0,
    "monthly_savings_needed": 333,
    "weekly_savings_needed": 77
  },
  "recent_transactions": [
    {
      "type": "Expense",
      "category": "Transport",
      "amount": "rs 1000",
      "user_request": "car service rs 1000"
    }
  ],
  "additional_savings": 500.0
}
```

---

### 💰 Set Budget

```http
POST http://localhost:8000/set_budget
```

**Body:**

```json
{
  "category": "Transport",
  "monthly_limit": 500.0,
  "start_date": "2025-09-01"
}
```

---

### 📊 Monitor Budget

```http
POST http://localhost:8000/monitor_budget
```

**Body:**

```json
{
  "budget": {
    "category": "Transport",
    "monthly_limit": 500.0,
    "start_date": "2025-09-01",
    "current_spent": 0.0
  },
  "recent_transactions": [
    {
      "type": "Expense",
      "category": "Transport",
      "amount": "rs 600",
      "user_request": "car service rs 600"
    }
  ],
  "goal": {
    "goal_name": "Vacation",
    "target_amount": 5000.0
  }
}
```

---

## 📁 **Project Structure**

```
Personal-Finance-Advisor/
├── api/                    # FastAPI backend
│   ├── main.py             # API main application
│   └── ...                 # API modules
├── app.py                  # Streamlit frontend
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🔧 **Configuration**

Create a `.env` file:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret_key
```

---

## 👥 **Contributors**

| Name          | Role                     |
| ------------- | ------------------------ |
| **Your Name** | Developer & Project Lead |

---

## 🪲 **Known Issues**

* 🔄 JWT token regenerates when Streamlit restarts
* ⚙️ Backend and frontend must both be active for full functionality

---

## 🔮 **Future Enhancements**

* [ ] Persistent JWT token storage
* [ ] Mobile app (React Native / Flutter)
* [ ] Integration with live banking APIs
* [ ] Advanced analytics dashboard
* [ ] Multi-currency support
* [ ] AI model optimization

---

## 📝 **License**

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for more details.

---

## 📞 **Support**

💬 Need help?
Email: `your-email@example.com`
or create an **Issue** on the repository.

---

<div align="center">

✨ *Built with ❤️ using Streamlit + FastAPI + AI* <br> <img src="https://img.shields.io/badge/Streamlit-FastAPI-Python?style=for-the-badge&logo=python&color=blue"/>

</div>
```

---

