import os
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import time

EMAIL = os.environ["EMAIL"]
APP_PASSWORD = os.environ["APP_PASSWORD"]
BASE_URL = "https://www.jobs.nhs.uk/candidate/search/results?staffGroup=MEDICAL_AND_DENTAL&payRange=0-10%2C10-20%2C20-30%2C30-40%2C40-50%2C50-60&searchFormType=sortBy&sort=publicationDateDesc&language=en"

def load_previous_job_ids():
    try:
        with open("jobs.txt", "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_current_job_ids(job_ids):
    with open("jobs.txt", "w") as f:
        f.write("\n".join(job_ids))

def scrape_all_pages():  # <--- LINE 15 (example)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    jobs = []
    page = 1
    
    while True:
        url = f"{BASE_URL}&page={page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        job_listings = soup.select('li.nhsuk-list-panel.search-result[data-test="search-result"]')
        
        if not job_listings:
            print(f"⏹️ No jobs found on page {page}, stopping pagination")
            break

        for job in job_listings:
            title_link = job.select_one('h2.nhsuk-heading-m a[data-test="search-result-job-title"]')
            if not title_link:
                continue

            href = title_link['href']
            job_id = href.split('/')[-1].split('?')[0]
            title = title_link.get_text(strip=True)
            
            jobs.append({
                "ID": job_id,
                "Title": title,
                "Link": f"https://www.jobs.nhs.uk{href}"
            })

        print(f"✅ Found {len(job_listings)} jobs on page {page}")
        page += 1
        time.sleep(1)

    return jobs  # <--- MAKE SURE THIS IS INDENTED UNDER scrape_all_pages()

def send_email(new_jobs):  # <--- NEXT FUNCTION STARTS AT SAME INDENT LEVEL
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"New NHS Jobs: {len(new_jobs)}"
        msg['From'] = EMAIL
        msg['To'] = "nermeen1899@hotmail.com"

        body = "🚨 New Job Alerts:\n\n"
        for job in new_jobs:
            body += f"▸ {job['Title']}\n{job['Link']}\n\n"
        body += "Cheers,\nYour Job Bot 🕵️♂️"

        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)
            print("✅ Email sent")
            
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")

def monitor():  # <--- THIS FUNCTION AT SAME LEVEL AS OTHERS
    previous_ids = load_previous_job_ids()
    current_jobs = scrape_all_pages()
    current_ids = {job["ID"] for job in current_jobs}
    
    new_jobs = [job for job in current_jobs if job["ID"] not in previous_ids]
    
    if new_jobs:
        print(f"🎉 {len(new_jobs)} NEW JOBS!")
        send_email(new_jobs)
    else:
        print("👀 No new jobs")
    
    save_current_job_ids(current_ids)

if __name__ == "__main__":
    if not EMAIL or not APP_PASSWORD:
        raise ValueError("Missing email credentials")
    monitor()
