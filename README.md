<div align="center">

# 💰 **Personal Finance Advisor**  


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

- Python **3.12+**
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

#### 🌟 **Recommended: Create a Virtual Environment**

```bash
# Create a new virtual environment
python -m venv finance-advisor-env

# Activate the virtual environment
# On Windows:
finance-advisor-env\Scripts\activate

# On macOS/Linux:
source finance-advisor-env/bin/activate
```

#### 📦 **Install Required Packages**

```bash
pip install -r requirements.txt
```

> 💡 **Tip**: Using a virtual environment isolates your project dependencies and prevents conflicts with other Python projects.

#### ✅ **Verify Installation**

```bash
# Check if all packages are installed correctly
pip list
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

---

## 🔑 **JWT Authentication Setup**

1. Run the Streamlit app
2. Login with your **Google account**
3. Go to the **ExpenseCat** page
4. Copy your **JWT Token** for Postman or API testing

> 💡 *JWT token regenerates every time Streamlit restarts. Always use a new one.*

---

## 📁 **Project Structure**

```
Personal-Finance-Advisor/
├── 📁 .streamlit/                   # Streamlit configuration
│   ├── client_secret.json           # Google OAuth credentials
│   └── secrets.toml                 # Streamlit secrets
├── 📁 agents/                       # AI Agents
│   ├── __init__.py
│   ├── BudgetTracker.py            # Budget tracking agent
│   ├── ExpenseCategorizer.py       # Expense categorization agent
│   ├── SavingGoalPlanner.py        # Savings goal planner agent
│   └── transactionsAgent.py        # Transaction processing agent
├── 📁 api/                          # FastAPI backend
│   └── main.py                      # FastAPI main application
├── 📁 controller/                   # Controllers
│   ├── 📁 database/                 # Database controllers
│   │   ├── __init__.py
│   │   └── database.py              # Database operations
│   └── 📁 helpers/                  # Helper functions
│       ├── __init__.py
│       ├── agentClassifier.py       # Agent classification helper
│       ├── auth.py                  # Authentication helper
│       ├── budgetTrackerSuggestion.py # Budget tracking suggestions
│       └── savinggoalplannersummerization.py # Goal planning helper
├── 📁 models/                       # Machine Learning models
│   ├── 📁 expense_income_category/  # Expense categorization models
│   │   ├── 📁 textcat/
│   │   │   ├── config.cfg
│   │   │   ├── meta.json
│   │   │   └── tokenizer
│   │   └── 📁 vocab/
│   │       ├── config.cfg
│   │       ├── meta.json
│   │       └── tokenizer
│   ├── 📁 expense_income_type/      # Income type classification models
│   │   ├── 📁 textcat/
│   │   │   ├── config.cfg
│   │   │   ├── meta.json
│   │   │   └── tokenizer
│   │   └── 📁 vocab/
│   │       ├── config.cfg
│   │       ├── meta.json
│   │       └── tokenizer
│   └── 📁 train_Expense_Categorizer/ # Training data and scripts
│       ├── expenses_income_dataset.csv # Training dataset
│       └── train.ipynb              # Training notebook
├── 📁 pages/                        # Streamlit pages
│   ├── home.py                      # Home page
│   ├── insights.py                  # Insights and analytics page
│   └── New Experimental LLM.py     # Experimental LLM features
├── app.py                          # Main Streamlit application
├── chat_main_db_v1.db             # SQLite database
├── expense_classifier.log          # Application logs
├── .gitignore                      # Git ignore file
├── LICENSE                         # MIT License
├── README.md                       # Project documentation
└── requirements.txt                # Python dependencies
```

## 🔧 **Configuration**

Create a `.env` file:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret_key
```

---

## 👥 **Contributors**

| Student ID | Name | Email |
|------------|------|-------|
| IT23191488 | Perera P.K.M.P | it23191488@my.sliit.lk |
| IT23 |  | it23@my.sliit.lk |
| IT23 |  | it23@my.sliit.lk |
| IT23343320 | Senadeera D.M.K.K | it23343320@my.sliit.lk |
---


## 📝 **License**

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for more details.

---

## 📞 **Support**

💬 Need help? Have questions or found a bug?

Please create an **Issue** on our [GitHub Issues](https://github.com/MadhuryaPasan/Personal-Finance-Advisor/issues) page.

We'll get back to you as soon as possible! 🚀

---

<div align="center">

✨ *Built with ❤️ using Streamlit + FastAPI + AI* <br> <img src="https://img.shields.io/badge/Streamlit-FastAPI-Python?style=for-the-badge&logo=python&color=blue"/>

</div>
```

---

