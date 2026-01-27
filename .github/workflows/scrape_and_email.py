import requests
import warnings
import urllib3
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# 1. Session / Headers
# =========================================================
session = requests.Session()
session.verify = False  # 반드시 False

headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://www.ccfgroup.com/member/member.php',
}

BASE_URL = "https://www.ccfgroup.com"

# =========================================================
# 2. Login Function (session 반환)
# =========================================================
def login_ccfgroup(session, headers, login_data):
    """
    CCFGroup 로그인
    성공 시 로그인된 session 반환
    """
    login_url = "https://www.ccfgroup.com/member/member.php"

    resp = session.post(
        login_url,
        data=login_data,
        headers=headers,
        timeout=30
    )
    resp.raise_for_status()

    return session

# =========================================================
# 3. Daily / Weekly Finder
# =========================================================
today = datetime.today().date()
offset_days = 1
target_date = today - timedelta(days=offset_days)

def find_market_daily(list_url: str, title_prefix: str):
    """
    기준 날짜(target_date) 이하에서
    title_prefix로 시작하는 가장 가까운 과거 Daily 1개 링크 반환
    """
    resp = session.get(list_url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = []

    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        if not text.startswith(title_prefix):
            continue

        try:
            date_str = text[text.find("(") + 1 : text.find(")")]
            post_date = datetime.strptime(date_str, "%b %d, %Y").date()
        except Exception:
            continue

        if post_date <= target_date:
            full_url = urljoin(BASE_URL, a.get("href"))
            candidates.append((post_date, full_url))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def find_market_weekly(list_url: str, title_prefix: str):
    """
    title_prefix로 시작하는 첫 번째 Weekly 링크 1개 반환
    """
    resp = session.get(list_url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for a in soup.find_all("a"):
        if a.get_text(strip=True).startswith(title_prefix):
            return urljoin(BASE_URL, a.get("href"))

    return None

# =========================================================
# 4. URL Extract (비로그인)
# =========================================================
benzene_daily = find_market_daily(
    "https://www.ccfgroup.com/newscenter/index.php?Class_ID=100000&subclassid=C00000",
    "Benzene market daily"
)

styrene_daily = find_market_daily(
    "https://www.ccfgroup.com/newscenter/index.php?Class_ID=100000&subclassid=F00000",
    "Styrene monomer market daily"
)

styrene_weekly = find_market_weekly(
    "https://www.ccfgroup.com/newscenter/index.php?Class_ID=200000&subclassid=F00000",
    "Styrene monomer market weekly"
)

urls = {
    "benzene_daily": benzene_daily,
    "styrene_daily": styrene_daily,
    "styrene_weekly": styrene_weekly
}

print("=== Extracted URLs (No Login) ===")
for k, v in urls.items():
    print(f"{k}: {v}")

# =========================================================
# 5. Login (URL 추출 이후)
# =========================================================
# 환경변수에서 credential 가져오기
USERNAME = os.getenv('CCF_USERNAME', 'SKGlobalKorea')
PASSWORD = os.getenv('CCF_PASSWORD', 'Sk15001657')

login_data = {
    'custlogin': '1',
    'action': 'login',
    'username': USERNAME,
    'password': PASSWORD,
    'savecookie': 'savecookie'
}

session = login_ccfgroup(session, headers, login_data)
print("✅ 로그인 완료 (session 유지됨)")

# =========================================================
# 6. 로그인 상태로 URL 접근 → 테이블 추출
# =========================================================
def fetch_tables_as_df(session, url, headers):
    """
    로그인된 session으로 URL 접근 후
    페이지 내 모든 HTML 테이블을 DataFrame 리스트로 반환
    """
    if not url:
        return []

    resp = session.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    html = resp.text
    dfs = pd.read_html(html)

    return dfs

# =========================================================
# 7. 데이터 수집
# =========================================================
df_benzene_daily = fetch_tables_as_df(session, benzene_daily, headers)
df_styrene_daily = fetch_tables_as_df(session, styrene_daily, headers)
df_styrene_weekly = fetch_tables_as_df(session, styrene_weekly, headers)

print("Benzene daily tables:", len(df_benzene_daily))
print("Styrene daily tables:", len(df_styrene_daily))
print("Styrene weekly tables:", len(df_styrene_weekly))

# =========================================================
# 8. CSV 파일 저장
# =========================================================
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

csv_files = []

# Benzene Daily 저장
if df_benzene_daily:
    for idx, df in enumerate(df_benzene_daily):
        filename = output_dir / f"benzene_daily_table_{idx+1}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        csv_files.append(filename)
        print(f"✅ Saved: {filename}")

# Styrene Daily 저장
if df_styrene_daily:
    for idx, df in enumerate(df_styrene_daily):
        filename = output_dir / f"styrene_daily_table_{idx+1}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        csv_files.append(filename)
        print(f"✅ Saved: {filename}")

# Styrene Weekly 저장
if df_styrene_weekly:
    for idx, df in enumerate(df_styrene_weekly):
        filename = output_dir / f"styrene_weekly_table_{idx+1}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        csv_files.append(filename)
        print(f"✅ Saved: {filename}")

print(f"\n총 {len(csv_files)}개 CSV 파일 생성 완료")

# =========================================================
# 9. 이메일 전송 (Gmail SMTP)
# =========================================================
def send_email_with_attachments(csv_files):
    """
    Gmail SMTP를 사용하여 CSV 파일들을 첨부하여 이메일 전송
    """
    # 환경변수에서 이메일 설정 가져오기
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')  # Gmail 앱 비밀번호
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    if not all([sender_email, sender_password, recipient_email]):
        print("⚠️  이메일 환경변수가 설정되지 않았습니다.")
        print("SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL를 확인하세요.")
        return

    # 이메일 메시지 생성
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f'CCFGroup Market Data - {datetime.now().strftime("%Y-%m-%d")}'

    # 이메일 본문
    body = f"""
안녕하세요,

{datetime.now().strftime("%Y년 %m월 %d일")} CCFGroup 시장 데이터를 첨부합니다.

첨부 파일:
"""
    for csv_file in csv_files:
        body += f"- {csv_file.name}\n"

    body += "\n자동 생성된 이메일입니다."

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # CSV 파일 첨부
    for csv_file in csv_files:
        with open(csv_file, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {csv_file.name}'
            )
            msg.attach(part)

    # SMTP 서버 연결 및 이메일 전송
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print(f"✅ 이메일 전송 성공: {recipient_email}")
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")
        raise

# 이메일 전송
if csv_files:
    send_email_with_attachments(csv_files)
else:
    print("⚠️  전송할 CSV 파일이 없습니다.")
