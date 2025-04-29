# Social Contract App

Social Contract is an action-based social network where users enter symbolic contracts with friends, committing to shared goals (e.g. work out daily, no social media for a month...).  They stay accountable by posting story-based progress updates (like BeReal), which act as proof of work.
Our AI verifies these updates and rewards successful task completions with Social Contract Tokens. For example, if a user commits to reducing YouTube usage, they must post a screenshot of their phone’s daily screen time. If AI detects YouTube wasn’t used, they earn a token.
Users can also join or host public contracts (like Telegram groups) to participate in trending challenges, contribute to shared progress, and learn from mentors. This expands goal-setting beyond friend circles, creating a decentralized hub for accountability and learning.

## Features
- 📝 **Create Contracts** – Users define group challenges with deadlines.
- 📩 **Messaging System** – Each contract has a built-in group chat.
- ✅ **Task Completion Tracking** – Users submit proof to mark tasks as complete.
- 🤖 **AI Verification (Limited)** – Automate proof validation.

---

## Try it Out

The app can be found at: https://social-contract.onrender.com.
You can only access it on a mobile browser (preferably Chrome). If you open it on a computer, you'll see a landing page with setup instructions for your phone.
Social Contract is a Progressive Web App (PWA) - it works like a mobile app without requiring an app store download.
To install it on your phone:
- Open the link in your web browser on mobile phone: https://social-contract.onrender.com 
- Look for the "Add to Home Screen" or "Install App" option (usually found in the share menu or browser settings).
- Confirm the installation.

---

## 🛠 Tech Stack
- **Backend**: Flask, Python  
- **Frontend**: HTML, CSS, JavaScript  
- **Database**: SQLite (MVP), PostgreSQL (future)  

---

## 🚀 Getting Started

Note: use the 'main' branch to deploy.

### **1. Clone the Repo**
```sh
git clone https://github.com/SocialContractT/The-Social-Contract.git
cd The-Social-Contract
```

### **2. Install Requirements**
```sh
pip install -r requirements.txt
```

### **3. Run on a Gunicorn server**
```sh
gunicorn -k eventlet -w 1 -b 0.0.0.0:8080 run:gunicorn_app
```
