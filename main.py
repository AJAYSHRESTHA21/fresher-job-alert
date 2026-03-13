import requests
from bs4 import BeautifulSoup
import json, os, smtplib, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from companies import COMPANIES

SEEN_JOBS_FILE = "seen_jobs.json"

FRESHER_KEYWORDS = [
    "fresher", "freshers", "trainee", "graduate", "entry level",
    "entry-level", "0-1 year", "0-2 year", "0 years", "campus",
    "junior", "associate engineer", "associate"
]

# ── Only IT/CS/MCA related jobs will pass this filter ──
IT_KEYWORDS = [
    # Roles
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
    # Fields
    "information technology", "computer science", "it fresher",
    "mca", "btech", "b.tech", "be ", "bsc it", "bca",
    "software trainee", "it trainee", "tech trainee",
    "graduate engineer trainee", "get", "engineering trainee",
]

# ── Jobs with these titles are NOT IT — reject them ──
EXCLUDE_KEYWORDS = [
    "marketing", "sales", "accountant", "ca fresher", "finance",
    "hr fresher", "human resource", "procurement", "supply chain",
    "content writer", "graphic design", "fashion", "textile",
    "civil engineer", "mechanical engineer", "electrical engineer",
    "chemical engineer", "biotech", "pharma", "medical",
    "teacher", "professor", "lecturer", "education",
    "legal", "lawyer", "advocate", "customer care", "bpo",
]

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


# ─── FRESHER + IT FILTER ───────────────────────────────────────────────────
def is_relevant_job(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_KEYWORDS):
        return False
    is_fresher = any(kw in t for kw in FRESHER_KEYWORDS)
    is_it = any(kw in t for kw in IT_KEYWORDS)
    return is_fresher or is_it


# ─── HTML EMAIL ────────────────────────────────────────────────────────────
def build_email(new_jobs: list) -> str:
    date_str = datetime.now().strftime("%d %B %Y")
    rows = ""
    for j in new_jobs:
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <b style="color:#1a73e8;">{j['title']}</b><br>
            🏢 {j['company']}&nbsp;&nbsp;|&nbsp;&nbsp;📍 {j['location']}<br>
            <small style="color:#888;">Source: {j['source']}</small>
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;text-align:center;vertical-align:middle;">
            <a href="{j['link']}" style="background:#1a73e8;color:#fff;padding:8px 16px;
               border-radius:4px;text-decoration:none;font-size:13px;">Apply Now</a><br><br>
            <a href="{j['official_page']}" style="font-size:11px;color:#888;">Official Page</a>
          </td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;color:#333;">
      <div style="background:#1a73e8;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;">🎓 Fresher Job Alert</h1>
        <p style="color:#cfe2ff;margin:6px 0 0;">{date_str} — {len(new_jobs)} New Job(s) Found</p>
      </div>
      <div style="background:#f9f9f9;padding:16px 24px;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;">
        <p>Hi there! 👋 Here are today's <b>fresher IT/CS/MCA job openings</b> from top service-based companies:</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:6px;border:1px solid #eee;">
          {rows}
        </table>
        <p style="font-size:12px;color:#aaa;margin-top:20px;text-align:center;">
          Sourced from Indeed, Naukri & LinkedIn &nbsp;|&nbsp; Auto-generated by Fresher Job Alert Bot
        </p>
      </div>
    </body></html>"""
    return html


# ─── SEND EMAIL ────────────────────────────────────────────────────────────
def send_email(html: str, job_count: int):
    sender    = os.environ["EMAIL_SENDER"]
    password  = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["EMAIL_RECIPIENT"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎓 {job_count} New Fresher IT Jobs Today — {datetime.now().strftime('%d %b %Y')}"
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.sendmail(sender, recipient, msg.as_string())
    print(f"✅ Email sent with {job_count} jobs!")


# ─── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*55}")
    print(f"  Fresher Job Alert Bot — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*55}\n")

    seen = load_seen_jobs()
    all_new_jobs = []

    for company in COMPANIES:
        print(f"🔍 Scanning: {company['name']}")
        candidates = []
        candidates += scrape_indeed(company)
        time.sleep(1)
        candidates += scrape_naukri(company)
        time.sleep(1)
        candidates += scrape_linkedin(company)
        time.sleep(1)

        for job in candidates:
            if job["id"] not in seen:
                seen.add(job["id"])
                if is_relevant_job(job["title"]):
                    all_new_jobs.append(job)
                    print(f"  ✅ NEW IT JOB: {job['title']} @ {job['company']} [{job['source']}]")
                else:
                    print(f"  ⛔ SKIPPED (not IT): {job['title']}")

    save_seen_jobs(seen)
    print(f"\n📦 Total new jobs found: {len(all_new_jobs)}")

    if all_new_jobs:
        html = build_email(all_new_jobs)
        send_email(html, len(all_new_jobs))
    else:
        print("📭 No IT/CS/MCA fresher jobs found today. No email sent.")

if __name__ == "__main__":
    main()
