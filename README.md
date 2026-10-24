# TEST NOVA

## Online Test & Examination Platform

Test Nova is a web-based online test and examination platform developed as a college mini-project using Python Flask. It allows teachers to create and manage online tests while students can attempt timed tests and view their results and performance.

---

## Features

### Student Module

- Student registration and login
- Student dashboard
- View available tests
- View test details
- Attempt online MCQ tests
- Countdown timer
- Previous and Next question navigation
- Question palette
- Mark questions for review
- Automatic test submission when time expires
- Automatic score calculation
- View test results
- View result history
- Performance statistics
- Personal best score
- Student leaderboard
- Student profile
- Change password

### Teacher Module

- Teacher registration and login
- Teacher dashboard
- Create tests
- Add MCQ questions
- Add four options for each question
- Select correct answer
- Edit questions
- Delete questions
- Set test duration
- Set total marks
- Set passing marks
- Publish tests
- Manage created tests
- View student results
- View result reports
- Teacher profile
- Change password

### Security

- Session-based authentication
- Password hashing
- Student and teacher role-based access
- Protected dashboards
- Unauthorized page access prevention

---

## Technology Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript

### Database
- SQLite
- SQLAlchemy ORM

### Development Tool
- Visual Studio Code

---

## Project Structure

```text
mini project/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
│
├── instance/
│   └── testnova.db
│
├── templates/
│   ├── base.html
│   ├── index.html
│   │
│   ├── auth/
│   │
│   ├── student/
│   │
│   └── teacher/
│
└── static/
    ├── css/
    ├── js/
    └── images/