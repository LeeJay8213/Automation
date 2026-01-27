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
import os

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
# 8. 이메일 전송 (DataFrame을 HTML 테이블로)
# =========================================================
def send_email_with_dataframes(df_benzene_daily, df_styrene_daily, df_styrene_weekly):
    """
    Gmail SMTP를 사용하여 DataFrame들을 HTML 테이블로 변환하여 이메일 본문에 포함
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
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f'CCFGroup Market Data - {datetime.now().strftime("%Y-%m-%d")}'

    # HTML 본문 생성
    html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 20px; }}
          h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
          h3 {{ color: #34495e; margin-top: 30px; }}
          table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
          th {{ background-color: #3498db; color: white; padding: 10px; text-align: left; }}
          td {{ border: 1px solid #ddd; padding: 8px; }}
          tr:nth-child(even) {{ background-color: #f2f2f2; }}
          .info {{ color: #7f8c8d; font-size: 12px; margin-top: 40px; }}
        </style>
      </head>
      <body>
        <h2>CCFGroup Market Data Report</h2>
        <p><strong>날짜:</strong> {datetime.now().strftime("%Y년 %m월 %d일")}</p>
    """

    # Benzene Daily 테이블 추가
    if df_benzene_daily:
        html_body += "<h3>📊 Benzene Market Daily</h3>"
        for idx, df in enumerate(df_benzene_daily):
            html_body += f"<h4>Table {idx+1}</h4>"
            html_body += df.to_html(index=False, border=0, classes='dataframe')
    else:
        html_body += "<h3>📊 Benzene Market Daily</h3><p>데이터 없음</p>"

    # Styrene Daily 테이블 추가
    if df_styrene_daily:
        html_body += "<h3>📊 Styrene Monomer Market Daily</h3>"
        for idx, df in enumerate(df_styrene_daily):
            html_body += f"<h4>Table {idx+1}</h4>"
            html_body += df.to_html(index=False, border=0, classes='dataframe')
    else:
        html_body += "<h3>📊 Styrene Monomer Market Daily</h3><p>데이터 없음</p>"

    # Styrene Weekly 테이블 추가
    if df_styrene_weekly:
        html_body += "<h3>📊 Styrene Monomer Market Weekly</h3>"
        for idx, df in enumerate(df_styrene_weekly):
            html_body += f"<h4>Table {idx+1}</h4>"
            html_body += df.to_html(index=False, border=0, classes='dataframe')
    else:
        html_body += "<h3>📊 Styrene Monomer Market Weekly</h3><p>데이터 없음</p>"

    html_body += """
        <p class="info">이 이메일은 자동으로 생성되었습니다.</p>
      </body>
    </html>
    """

    # HTML 본문 첨부
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

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
send_email_with_dataframes(df_benzene_daily, df_styrene_daily, df_styrene_weekly)
