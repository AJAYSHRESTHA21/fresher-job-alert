# 🎓 Fresher Job Alert Bot

Automatically searches **30 top service-based companies** for fresher roles and sends a daily email alert — completely FREE using GitHub Actions.

---

## 🏢 Companies Tracked (30 Total)

### Tier 1 — Giant MNCs
TCS | Infosys | Wipro | HCL Technologies | Accenture | Cognizant | Capgemini | IBM India | Oracle India | SAP India

### Tier 2 — Large Service Companies
Tech Mahindra | LTIMindtree | Mphasis | Hexaware | Zensar | Persistent Systems | Sonata Software | Kyndryl | Dell Technologies | NIIT Technologies

### Tier 3 — Mid-size Active Fresher Hiring
Mastech Digital | Birlasoft | Coforge | Cyient | Tata Elxsi | KPIT Technologies | Happiest Minds | Sasken | Mindtree | Infotech Enterprises

---

## 📁 Project Structure

```
fresher-job-alert/
├── main.py                        ← scrapes jobs & sends email
├── companies.py                   ← all 30 companies + career URLs
├── requirements.txt               ← python dependencies
├── seen_jobs.json                 ← tracks sent jobs (auto-created)
└── .github/
    └── workflows/
        └── job_alert.yml          ← runs daily at 9 AM IST (FREE)
```

---

## 🚀 Setup Instructions (One Time)

### Step 1: Fork / Upload to GitHub
1. Go to [github.com](https://github.com) → Create a **new public/private repo** named `fresher-job-alert`
2. Upload all files (drag & drop works)

### Step 2: Allow Gmail to send emails
1. Go to your Google Account → **Security**
2. Turn ON **2-Step Verification**
3. Then go to **App Passwords** → create one for "Mail"
4. Copy the 16-digit password — this is your `EMAIL_PASSWORD`

### Step 3: Add GitHub Secrets
Go to your repo → **Settings → Secrets and variables → Actions → New secret**

| Secret Name       | Value                          |
|-------------------|--------------------------------|
| `EMAIL_SENDER`    | your Gmail (e.g. you@gmail.com)|
| `EMAIL_PASSWORD`  | 16-digit App Password          |
| `EMAIL_RECIPIENT` | email where you want alerts    |

### Step 4: Enable GitHub Actions
- Go to **Actions** tab in your repo
- Click **"I understand my workflows, go ahead and enable them"**

### ✅ Done! 
The bot will run every day at **9:00 AM IST** automatically.

---

## ▶️ Run Manually Anytime
Go to **Actions → Fresher Job Alert → Run workflow**

---

## 🔍 Sources Searched Per Company
1. **Indeed India** — india's top job board
2. **Naukri.com** — largest Indian job portal
3. **LinkedIn** — professional network
4. **Official Career Page** — direct company website

---

## 📧 Sample Email
You'll receive a beautifully formatted HTML email with:
- ✅ Job Title
- 🏢 Company Name
- 📍 Location
- 🔗 Apply Now button
- 🌐 Official Career Page link
