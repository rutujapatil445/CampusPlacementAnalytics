# Campus Placement Analytics

An interactive campus placement management and analytics platform that helps students track their academic profile, skills, projects, certifications, internships, placement applications, and placement readiness.

The system also provides TPO/Admin dashboards for managing companies, placement drives, eligibility criteria, applications, and placement analytics.

## 🚀 Features

### 👩‍🎓 Student Module

* Student registration and login
* Role-based authentication
* Academic profile management
* 10th, 12th/Diploma percentage and CGPA tracking
* Backlog and academic gap tracking
* Skills management
* Project management
* Internship and certification management
* Company eligibility checking
* Placement drive/application tracking
* Placement readiness score
* ML-based placement prediction
* Interactive student dashboard

### 👨‍💼 TPO/Admin Module

* Admin/TPO authentication
* Student management
* Company management
* Placement drive management
* Eligibility criteria management
* Application monitoring
* Placement statistics
* Analytics dashboard
* Student performance insights

### 🤖 Machine Learning

The project uses a beginner-friendly **Logistic Regression** model to estimate placement probability based on selected student-related features.

The ML module includes:

* Dataset generation
* Feature extraction
* Binary target creation
* Train-test split
* Logistic Regression
* Model evaluation
* Model saving/loading
* Placement probability prediction
* Feature importance

The ML implementation is intentionally kept transparent so that the prediction process can be understood and explained easily.

## 📊 Analytics

The analytics module provides insights related to:

* Student placement status
* Company placement trends
* Eligibility statistics
* Application statistics
* Student readiness
* Academic performance

Interactive visualizations are implemented using Streamlit-compatible data visualization tools.

## 🛠️ Technologies Used

### Programming

* Python

### Frontend / UI

* Streamlit

### Database

* MySQL

### Python Libraries

* Pandas
* NumPy
* Scikit-learn
* PyMySQL / MySQL Connector
* Plotly
* bcrypt

### Development Tools

* PyCharm
* Git
* GitHub

## 🏗️ Project Structure

```text
CampusPlacementAnalytics/
│
├── config/
│   ├── database.py
│   └── settings.py
│
├── database/
│   ├── README.md
│   ├── schema.sql
│   ├── seed_data.sql
│   └── generate_sample_data.py
│
├── modules/
│   ├── auth.py
│   ├── student_manager.py
│   ├── portfolio_manager.py
│   ├── company_manager.py
│   ├── eligibility_engine.py
│   ├── application_manager.py
│   ├── readiness_engine.py
│   ├── analytics_engine.py
│   └── ml_model.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_student_manager.py
│   ├── test_portfolio_manager.py
│   ├── test_company_manager.py
│   ├── test_eligibility_engine.py
│   ├── test_application_manager.py
│   ├── test_readiness_engine.py
│   ├── test_analytics_engine.py
│   ├── test_ml_model.py
│   └── test_database_connection.py
│
├── ui/
│   ├── app.py
│   ├── components.py
│   ├── styles.py
│   ├── student_views.py
│   └── admin_views.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔄 Application Workflow

```text
Student / TPO
      ↓
Authentication
      ↓
Role-Based Access
      ↓
Student Profile / Admin Dashboard
      ↓
Academic + Skills + Projects + Internships
      ↓
Company & Placement Drives
      ↓
Eligibility Engine
      ↓
Placement Applications
      ↓
Readiness Score
      ↓
ML Placement Prediction
      ↓
Analytics Dashboard
```

## 🤖 ML Workflow

```text
Student Data
     ↓
Feature Extraction
     ↓
Data Preparation
     ↓
Train-Test Split
     ↓
Logistic Regression
     ↓
Model Evaluation
     ↓
Placement Prediction
     ↓
Probability + Feature Importance
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/rutujapatil445/CampusPlacementAnalytics.git
cd CampusPlacementAnalytics
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows:**

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file using `.env.example` as a reference.

Do not upload your actual `.env` file because it may contain database credentials.

### 6. Configure MySQL

Create the required database and execute:

```text
database/schema.sql
```

Then use the sample data script or:

```text
database/seed_data.sql
```

to populate the database.

### 7. Run the Streamlit application

From the project root:

```bash
python -m streamlit run ui/app.py
```

The application will open in your browser.

## 🧪 Testing

The project includes separate tests for the major modules.

Run:

```bash
pytest
```

The ML module also includes tests covering:

* Dataset generation
* Model training
* Model evaluation
* Model serialization
* Student prediction
* Invalid student handling
* Feature importance

## 🔐 Security

* Database credentials are stored through environment variables.
* `.env` is excluded using `.gitignore`.
* Passwords are handled using password hashing.
* Role-based access is implemented for Student and Admin/TPO users.

## 🎯 Project Objective

The main objective of Campus Placement Analytics is to provide a centralized platform for managing campus placement activities while giving students useful insights into their placement readiness and helping TPOs analyze placement-related data.

## 🔮 Future Enhancements

* Advanced ML models
* More placement prediction features
* Email notifications
* Resume analysis
* Real-time placement notifications
* Cloud deployment
* Advanced analytics
* Automated report generation

## 👩‍💻 Developer

**Rutuja Patil**

B.Tech Computer Engineering
AISSMS IOIT, Pune

GitHub: [rutujapatil445](https://github.com/rutujapatil445)
