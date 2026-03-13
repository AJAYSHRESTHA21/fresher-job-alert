import requests
from bs4 import BeautifulSoup
import json, os, smtplib, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from companies import COMPANIES

SEEN_JOBS_FILE   = "seen_jobs.json"
WEEKLY_JOBS_FILE = "weekly_jobs.json"

FRESHER_KEYWORDS = [
    "fresher", "freshers", "trainee", "graduate", "entry level",
    "entry-level", "0-1 year", "0-2 year", "0 years", "campus",
    "junior", "associate engineer", "associate"
]

IT_KEYWORDS = [
    "software", "developer", "engineer", "programmer", "coder",
    "backend", "frontend", "full stack", "fullstack", "web developer",
    "mobile developer", "android", "ios", "app developer",
    "devops", "cloud", "sre", "site reliability",
    "data analyst", "data engineer", "data scientist", "ml engineer",
    "machine learning", "artificial intelligence", "ai engineer",
    "python", "java", "javascript", "react", "node", "angular",
    "dot net", ".net", "c++", "golang", "ruby",
    "database", "sql", "mysql", "oracle dba", "mongodb",
    "network engineer", "system admin", "sysadmin", "linux admin",
    "cybersecurity", "security analyst", "ethical hacker", "pen test",
    "qa engineer", "test engineer", "automation tester", "sdet",
    "it support", "technical support", "helpdesk", "service desk",
    "erp", "sap consultant", "salesforce", "servicenow",
    "business analyst", "system analyst", "it analyst",
    "iot", "embedded", "firmware", "vlsi", "hardware engineer",
    "blockchain", "uiux", "ui/ux", "ui developer",
    "information technology", "computer science", "it fresher",
    "mca", "btech", "b.tech", "be ", "bsc it", "bca",
    "software trainee", "it trainee", "tech trainee",
    "graduate engineer trainee", "get", "engineering trainee",
]

EXCLUDE_KEYWORDS = [
    "marketing", "sales", "accountant", "ca fresher", "finance",
    "hr fresher", "human resource", "procurement", "supply chain",
    "content writer", "graphic design", "fashion", "textile",
    "civil engineer", "mechanical engineer", "electrical engineer",
    "chemical engineer", "biotech", "pharma", "medical",
    "teacher", "professor", "lecturer", "education",
    "legal", "lawyer", "advocate", "customer care", "bpo",
]

RESUME_TIPS = [
    "🖊️ Keep your resume to <b>1 page</b> — recruiters spend only 6 seconds on it!",
    "📌 Add a <b>Skills section</b> with Python, Java, SQL, or whatever you know.",
    "🎯 Tailor your resume <b>for each company</b> — mention their tech stack.",
    "📁 Save resume as <b>PDF</b> with name format: <i>YourName_Resume.pdf</i>",
    "🔗 Add your <b>GitHub / LinkedIn</b> profile link on your resume.",
    "📊 Mention <b>projects with results</b> — e.g. 'Built REST API used by 200+ users'",
    "✅ Use <b>action verbs</b> — Developed, Built, Designed, Implemented, Optimized",
    "🏆 Add <b>certifications</b> — Google, AWS, HackerRank badges all count!",
]

INTERVIEW_PREP = {
    "TCS":               "https://www.geeksforgeeks.org/tcs-interview-experience/",
    "Infosys":           "https://www.geeksforgeeks.org/infosys-interview-experience/",
    "Wipro":             "https://www.geeksforgeeks.org/wipro-interview-experience/",
    "HCL Technologies":  "https://www.geeksforgeeks.org/hcl-interview-experience/",
    "Accenture":         "https://www.geeksforgeeks.org/accenture-interview-experience/",
    "Cognizant":         "https://www.geeksforgeeks.org/cognizant-interview-experience/",
    "Capgemini":         "https://www.geeksforgeeks.org/capgemini-interview-experience/",
    "IBM India":         "https://www.geeksforgeeks.org/ibm-interview-experience/",
    "Tech Mahindra":     "https://www.geeksforgeeks.org/tech-mahindra-interview-experience/",
    "Hexaware":          "https://www.geeksforgeeks.org/hexaware-interview-experience/",
    "default":           "https://www.geeksforgeeks.org/company-interview-corner/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ─── SEEN JOBS ─────────────────────────────────────────────────────────────
def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen: set):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f, indent=2)


# ─── WEEKLY JOBS ───────────────────────────────────────────────────────────
def load_weekly_jobs():
    if os.path.exists(WEEKLY_JOBS_FILE):
        with open(WEEKLY_JOBS_FILE, "r") as f:
            return json.load(f)
    return []

def save_weekly_jobs(jobs: list):
    with open(WEEKLY_JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def clear_weekly_jobs():
    with open(WEEKLY_JOBS_FILE, "w") as f:
        json.dump([], f)


# ─── INDEED INDIA ──────────────────────────────────────────────────────────
def scrape_indeed(company: dict) -> list:
    jobs = []
    query = requests.utils.quote(company["search_name"])
    url = f"https://in.indeed.com/jobs?q={query}&l=India&fromage=7"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.find_all("div", class_="job_seen_beacon")[:8]:
            try:
                title_el = card.find("span", attrs={"title": True})
                title = title_el["title"] if title_el else ""
                link_el = card.find("a", class_="jcs-JobTitle")
                job_id = link_el["data-jk"] if link_el and link_el.get("data-jk") else None
                if not job_id:
                    continue
                link = f"https://in.indeed.com/viewjob?jk={job_id}"
                company_el = card.find("span", attrs={"data-testid": "company-name"})
                cname = company_el.get_text(strip=True) if company_el else company["name"]
                loc_el = card.find("div", attrs={"data-testid": "text-location"})
                location = loc_el.get_text(strip=True) if loc_el else "India"
                jobs.append({
                    "id": f"indeed_{job_id}",
                    "title": title, "company": cname,
                    "location": location, "link": link,
                    "source": "Indeed India", "official_page": company["career_url"],
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [Indeed] {company['name']}: {e}")
    return jobs


# ─── NAUKRI.COM ────────────────────────────────────────────────────────────
def scrape_naukri(company: dict) -> list:
    jobs = []
    query = requests.utils.quote(company["search_name"])
    url = f"https://www.naukri.com/jobs-in-india?k={query}&experience=0"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.find_all("article", attrs={"class": lambda c: c and "jobTuple" in " ".join(c)})[:8]:
            try:
                title_el = card.find("a", class_="title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                job_id = link.split("?")[0].split("/")[-1]
                cname_el = card.find("a", class_="subTitle")
                cname = cname_el.get_text(strip=True) if cname_el else company["name"]
                loc_el = card.find("li", class_="location")
                location = loc_el.get_text(strip=True) if loc_el else "India"
                jobs.append({
                    "id": f"naukri_{job_id}",
                    "title": title, "company": cname,
                    "location": location, "link": link,
                    "source": "Naukri.com", "official_page": company["career_url"],
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [Naukri] {company['name']}: {e}")
    return jobs


# ─── LINKEDIN PUBLIC ───────────────────────────────────────────────────────
def scrape_linkedin(company: dict) -> list:
    jobs = []
    query = requests.utils.quote(f"{company['name']} fresher")
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={query}"
        f"&location=India&f_E=1&f_TPR=r604800&position=1&pageNum=0"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.find_all("div", class_="base-card")[:8]:
            try:
                title_el = card.find("h3", class_="base-search-card__title")
                title = title_el.get_text(strip=True) if title_el else ""
                link_el = card.find("a", class_="base-card__full-link")
                link = link_el["href"] if link_el else ""
                job_id = link.split("?")[0].split("-")[-1]
                cname_el = card.find("h4", class_="base-search-card__subtitle")
                cname = cname_el.get_text(strip=True) if cname_el else company["name"]
                loc_el = card.find("span", class_="job-search-card__location")
                location = loc_el.get_text(strip=True) if loc_el else "India"
                if job_id:
                    jobs.append({
                        "id": f"linkedin_{job_id}",
                        "title": title, "company": cname,
                        "location": location, "link": link,
                        "source": "LinkedIn", "official_page": company["career_url"],
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"  [LinkedIn] {company['name']}: {e}")
    return jobs


# ─── GLASSDOOR INDIA ───────────────────────────────────────────────────────
def scrape_glassdoor(company: dict) -> list:
    jobs = []
    query = requests.utils.quote(f"{company['name']} fresher India")
    url = f"https://www.glassdoor.co.in/Job/india-{query}-jobs-SRCH_IL.0,5_IN115_KO6,{6+len(company['name'])}.htm"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.find_all("li", class_="react-job-listing")[:6]:
            try:
                title_el = card.find("a", attrs={"data-test": "job-title"})
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = "https://www.glassdoor.co.in" + title_el.get("href", "")
                job_id = link.split("?")[0].split("-")[-1].replace(".htm", "")
                cname_el = card.find("div", class_="job-search-key-l93og5")
                cname = cname_el.get_text(strip=True) if cname_el else company["name"]
                loc_el = card.find("div", attrs={"data-test": "emp-location"})
                location = loc_el.get_text(strip=True) if loc_el else "India"
                if job_id:
                    jobs.append({
                        "id": f"glassdoor_{job_id}",
                        "title": title, "company": cname,
                        "location": location, "link": link,
                        "source": "Glassdoor", "official_page": company["career_url"],
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"  [Glassdoor] {company['name']}: {e}")
    return jobs


# ─── INTERNSHALA ───────────────────────────────────────────────────────────
def scrape_internshala(company: dict) -> list:
    jobs = []
    query = requests.utils.quote(company["name"])
    url = f"https://internshala.com/jobs/keyword-{query}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.find_all("div", class_="individual_internship")[:6]:
            try:
                title_el = card.find("h3", class_="job-internship-name")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link_el = card.find("a", class_="view_detail_button")
                link = "https://internshala.com" + link_el.get("href", "") if link_el else ""
                job_id = link.split("/")[-2] if link else ""
                cname_el = card.find("p", class_="company-name")
                cname = cname_el.get_text(strip=True) if cname_el else company["name"]
                loc_el = card.find("p", class_="row-1-item")
                location = loc_el.get_text(strip=True) if loc_el else "India"
                if job_id:
                    jobs.append({
                        "id": f"internshala_{job_id}",
                        "title": title, "company": cname,
                        "location": location, "link": link,
                        "source": "Internshala", "official_page": company["career_url"],
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"  [Internshala] {company['name']}: {e}")
    return jobs


# ─── FRESHER + IT FILTER ───────────────────────────────────────────────────
def is_relevant_job(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_KEYWORDS):
        return False
    is_fresher = any(kw in t for kw in FRESHER_KEYWORDS)
    is_it = any(kw in t for kw in IT_KEYWORDS)
    return is_fresher or is_it

def get_resume_tip() -> str:
    day_index = datetime.now().timetuple().tm_yday % len(RESUME_TIPS)
    return RESUME_TIPS[day_index]

def get_prep_link(company_name: str) -> str:
    return INTERVIEW_PREP.get(company_name, INTERVIEW_PREP["default"])


# ─── DAILY EMAIL ───────────────────────────────────────────────────────────
def build_daily_email(new_jobs: list) -> str:
    date_str   = datetime.now().strftime("%d %B %Y")
    resume_tip = get_resume_tip()
    rows = ""
    for j in new_jobs:
        prep_link = get_prep_link(j["company"])
        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee;">
            <b style="color:#1a73e8;font-size:15px;">{j['title']}</b><br>
            🏢 {j['company']}&nbsp;&nbsp;|&nbsp;&nbsp;📍 {j['location']}<br>
            <small style="color:#888;">Source: {j['source']}</small>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;text-align:center;vertical-align:middle;min-width:130px;">
            <a href="{j['link']}" style="background:#1a73e8;color:#fff;padding:8px 14px;
               border-radius:4px;text-decoration:none;font-size:13px;display:block;margin-bottom:6px;">
               🚀 Apply Now</a>
            <a href="{j['official_page']}" style="background:#f1f3f4;color:#555;padding:5px 10px;
               border-radius:4px;text-decoration:none;font-size:11px;display:block;margin-bottom:6px;">
               🏢 Official Page</a>
            <a href="{prep_link}" style="background:#e8f5e9;color:#2e7d32;padding:5px 10px;
               border-radius:4px;text-decoration:none;font-size:11px;display:block;">
               📚 Interview Prep</a>
          </td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;color:#333;">
      <div style="background:#1a73e8;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;">🎓 Fresher IT Job Alert</h1>
        <p style="color:#cfe2ff;margin:6px 0 0;">{date_str} — {len(new_jobs)} New Job(s) Found</p>
      </div>
      <div style="background:#f9f9f9;padding:16px 24px;border:1px solid #ddd;border-top:none;">
        <p>👋 Hi! Here are today's <b>fresher IT/CS/MCA job openings</b> from top companies:</p>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:6px;border:1px solid #eee;">
          {rows}
        </table>
        <div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;
                    margin-top:20px;border-radius:4px;">
          <b style="color:#e65100;">💡 Resume Tip of the Day</b><br>
          <span style="font-size:14px;">{resume_tip}</span>
        </div>
        <div style="margin-top:16px;padding:14px 18px;background:#e8f5e9;border-radius:4px;">
          <b style="color:#2e7d32;">🔗 Useful Links for Freshers</b><br><br>
          <a href="https://www.geeksforgeeks.org/company-interview-corner/" style="color:#1a73e8;">📚 Company Interview Experiences (GFG)</a><br>
          <a href="https://leetcode.com/problemset/" style="color:#1a73e8;">💻 Practice Coding (LeetCode)</a><br>
          <a href="https://www.hackerrank.com/dashboard" style="color:#1a73e8;">🏆 HackerRank Certifications</a><br>
          <a href="https://grow.google/certificates/" style="color:#1a73e8;">🎓 Free Google Certifications</a>
        </div>
        <p style="font-size:11px;color:#aaa;margin-top:16px;text-align:center;">
          Sourced from Indeed • Naukri • LinkedIn • Glassdoor • Internshala &nbsp;|&nbsp;
          Auto-generated by Fresher Job Alert Bot
        </p>
      </div>
    </body></html>"""
    return html


# ─── WEEKLY EMAIL ──────────────────────────────────────────────────────────
def build_weekly_email(all_jobs: list) -> str:
    date_str = datetime.now().strftime("%d %B %Y")
    company_counts = {}
    for j in all_jobs:
        company_counts[j["company"]] = company_counts.get(j["company"], 0) + 1
    top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    source_counts = {}
    for j in all_jobs:
        source_counts[j["source"]] = source_counts.get(j["source"], 0) + 1
    top_jobs = all_jobs[:10]
    rows = ""
    for j in top_jobs:
        prep_link = get_prep_link(j["company"])
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <b style="color:#1a73e8;">{j['title']}</b><br>
            🏢 {j['company']} &nbsp;|&nbsp; 📍 {j['location']}<br>
            <small style="color:#888;">{j['source']}</small>
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;text-align:center;vertical-align:middle;">
            <a href="{j['link']}" style="background:#1a73e8;color:#fff;padding:7px 12px;
               border-radius:4px;text-decoration:none;font-size:12px;display:block;margin-bottom:5px;">
               🚀 Apply</a>
            <a href="{prep_link}" style="background:#e8f5e9;color:#2e7d32;padding:5px 10px;
               border-radius:4px;text-decoration:none;font-size:11px;display:block;">
               📚 Prep</a>
          </td>
        </tr>"""
    company_rows = ""
    for cname, count in top_companies:
        company_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;">{cname}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:center;">
            <b style="color:#1a73e8;">{count}</b> jobs
          </td>
        </tr>"""
    source_rows = ""
    for src, count in source_counts.items():
        source_rows += f"<span style='margin-right:16px;'>📌 <b>{src}</b>: {count}</span>"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;color:#333;">
      <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:28px;
                  border-radius:8px 8px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;">📊 Weekly Fresher Job Report</h1>
        <p style="color:#cfe2ff;margin:8px 0 0;">Week ending {date_str}</p>
      </div>
      <div style="background:#f9f9f9;padding:20px 24px;border:1px solid #ddd;border-top:none;
                  border-radius:0 0 8px 8px;">
        <div style="background:#fff;border-radius:6px;padding:16px;margin-bottom:20px;
                    border:1px solid #eee;text-align:center;">
          <h2 style="margin:0 0 12px;color:#333;">📈 This Week's Stats</h2>
          <div style="display:inline-block;margin:0 20px;">
            <div style="font-size:32px;font-weight:bold;color:#1a73e8;">{len(all_jobs)}</div>
            <div style="font-size:13px;color:#888;">Total Jobs Found</div>
          </div>
          <div style="display:inline-block;margin:0 20px;">
            <div style="font-size:32px;font-weight:bold;color:#34a853;">{len(set(j['company'] for j in all_jobs))}</div>
            <div style="font-size:13px;color:#888;">Companies Hiring</div>
          </div>
          <div style="display:inline-block;margin:0 20px;">
            <div style="font-size:32px;font-weight:bold;color:#fbbc04;">{len(source_counts)}</div>
            <div style="font-size:13px;color:#888;">Sources Searched</div>
          </div>
        </div>
        <h3 style="color:#333;">🏆 Top Hiring Companies This Week</h3>
        <table width="100%" style="background:#fff;border-radius:6px;border:1px solid #eee;margin-bottom:20px;">
          {company_rows}
        </table>
        <div style="background:#e3f2fd;padding:12px 16px;border-radius:6px;margin-bottom:20px;font-size:13px;">
          <b>📡 Sources:</b><br><br>{source_rows}
        </div>
        <h3 style="color:#333;">🎯 Top 10 Jobs This Week</h3>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:6px;border:1px solid #eee;margin-bottom:20px;">
          {rows}
        </table>
        <div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;
                    border-radius:4px;margin-bottom:16px;">
          <b style="color:#e65100;">🎓 Weekend Prep Checklist</b><br><br>
          ✅ Update your resume with latest projects<br>
          ✅ Practice 5 coding problems on LeetCode<br>
          ✅ Check 1 company's interview experience on GFG<br>
          ✅ Apply to at least 3 jobs from this week's list<br>
          ✅ Complete 1 free certification (Google / HackerRank)
        </div>
        <div style="background:#e8f5e9;padding:14px 18px;border-radius:4px;">
          <b style="color:#2e7d32;">🔗 Fresher Resources</b><br><br>
          <a href="https://www.geeksforgeeks.org/company-interview-corner/" style="color:#1a73e8;">📚 Interview Experiences (GFG)</a><br>
          <a href="https://leetcode.com/problemset/" style="color:#1a73e8;">💻 LeetCode Practice</a><br>
          <a href="https://www.hackerrank.com/dashboard" style="color:#1a73e8;">🏆 HackerRank Certifications</a><br>
          <a href="https://grow.google/certificates/" style="color:#1a73e8;">🎓 Google Free Certifications</a><br>
          <a href="https://www.coursera.org/courses?query=free" style="color:#1a73e8;">📖 Free Coursera Courses</a>
        </div>
        <p style="font-size:11px;color:#aaa;margin-top:16px;text-align:center;">
          Auto-generated Weekly Report by Fresher Job Alert Bot &nbsp;|&nbsp; Have a great weekend! 🎉
        </p>
      </div>
    </body></html>"""
    return html


# ─── NO JOBS EMAIL ─────────────────────────────────────────────────────────
def send_no_jobs_email():
    sender    = os.environ["EMAIL_SENDER"]
    password  = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_RECIPIENT"]
    date_str  = datetime.now().strftime("%d %B %Y")
    resume_tip = get_resume_tip()
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;color:#333;">
      <div style="background:#e53935;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;">📭 No New Fresher Jobs Today</h1>
        <p style="color:#ffcdd2;margin:6px 0 0;">{date_str}</p>
      </div>
      <div style="background:#f9f9f9;padding:16px 24px;border:1px solid #ddd;
                  border-top:none;border-radius:0 0 8px 8px;">
        <p>👋 Hi! We scanned <b>30 top companies</b> across
           <b>Indeed, Naukri, LinkedIn, Glassdoor & Internshala</b>
           but found <b>no new IT/CS/MCA fresher jobs</b> today.</p>
        <p>Don't worry — use today to prepare! 💪</p>
        <div style="background:#fff8e1;border-left:4px solid #ffc107;
                    padding:14px 18px;border-radius:4px;margin-top:16px;">
          <b style="color:#e65100;">💡 Resume Tip of the Day</b><br>
          <span style="font-size:14px;">{resume_tip}</span>
        </div>
        <div style="margin-top:16px;padding:14px 18px;background:#e8f5e9;border-radius:4px;">
          <b style="color:#2e7d32;">🔗 Use Today to Prepare</b><br><br>
          <a href="https://leetcode.com/problemset/" style="color:#1a73e8;">💻 Practice Coding (LeetCode)</a><br>
          <a href="https://www.geeksforgeeks.org/company-interview-corner/" style="color:#1a73e8;">📚 Interview Experiences (GFG)</a><br>
          <a href="https://www.hackerrank.com/dashboard" style="color:#1a73e8;">🏆 Earn HackerRank Certificate</a><br>
          <a href="https://grow.google/certificates/" style="color:#1a73e8;">🎓 Free Google Certifications</a>
        </div>
        <p style="font-size:11px;color:#aaa;margin-top:16px;text-align:center;">
          We'll alert you the moment new jobs appear! 🔔
        </p>
      </div>
    </body></html>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📭 No Fresher IT Jobs Today — {date_str}"
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.sendmail(sender, recipient, msg.as_string())
    print("✅ No-jobs email sent!")


# ─── SEND EMAIL ────────────────────────────────────────────────────────────
def send_email(html: str, subject: str):
    sender    = os.environ["EMAIL_SENDER"]
    password  = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_RECIPIENT"]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.sendmail(sender, recipient, msg.as_string())
    print(f"✅ Email sent: {subject}")


# ─── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*55}")
    print(f"  Fresher Job Alert Bot — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*55}\n")

    is_friday = datetime.now().weekday() == 4

    seen         = load_seen_jobs()
    weekly_jobs  = load_weekly_jobs()
    all_new_jobs = []

    for company in COMPANIES:
        print(f"🔍 Scanning: {company['name']}")
        candidates = []
        candidates += scrape_indeed(company);      time.sleep(1)
        candidates += scrape_naukri(company);      time.sleep(1)
        candidates += scrape_linkedin(company);    time.sleep(1)
        candidates += scrape_glassdoor(company);   time.sleep(1)
        candidates += scrape_internshala(company); time.sleep(1)

        for job in candidates:
            if job["id"] not in seen:
                seen.add(job["id"])
                if is_relevant_job(job["title"]):
                    all_new_jobs.append(job)
                    weekly_jobs.append(job)
                    print(f"  ✅ NEW: {job['title']} @ {job['company']} [{job['source']}]")
                else:
                    print(f"  ⛔ SKIPPED: {job['title']}")

    save_seen_jobs(seen)
    save_weekly_jobs(weekly_jobs)
    print(f"\n📦 Total new jobs today: {len(all_new_jobs)}")

    if all_new_jobs:
        html = build_daily_email(all_new_jobs)
        send_email(html, f"🎓 {len(all_new_jobs)} New Fresher IT Jobs — {datetime.now().strftime('%d %b %Y')}")
    else:
        send_no_jobs_email()

    if is_friday and weekly_jobs:
        print(f"\n📊 Friday! Sending weekly summary ({len(weekly_jobs)} jobs this week)...")
        html = build_weekly_email(weekly_jobs)
        send_email(html, f"📊 Weekly Fresher Job Report — {datetime.now().strftime('%d %b %Y')}")
        clear_weekly_jobs()
        print("✅ Weekly jobs log cleared for next week.")

if __name__ == "__main__":
    main()
