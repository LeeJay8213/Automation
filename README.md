# CCFGroup Market Data Scraper

매일 자동으로 CCFGroup 웹사이트에서 시장 데이터를 수집하고 CSV 파일로 이메일 전송하는 GitHub Actions 워크플로우

## 📋 목차
- [기능](#기능)
- [설정 방법](#설정-방법)
- [Gmail 앱 비밀번호 생성](#gmail-앱-비밀번호-생성)
- [GitHub Secrets 설정](#github-secrets-설정)
- [사용 방법](#사용-방법)
- [문제 해결](#문제-해결)

## ✨ 기능

- 매일 자동으로 다음 데이터 수집:
  - Benzene market daily
  - Styrene monomer market daily
  - Styrene monomer market weekly
- 각 테이블을 개별 CSV 파일로 저장
- 수집된 모든 CSV 파일을 이메일로 자동 전송
- GitHub Actions로 완전 자동화

## 🚀 설정 방법

### 1. 저장소 구조

```
your-repo/
├── .github/
│   └── workflows/
│       └── daily-scraping.yml
├── scrape_and_email.py
├── requirements.txt
└── README.md
```

### 2. Gmail 앱 비밀번호 생성

Gmail을 통해 이메일을 보내려면 **앱 비밀번호**가 필요합니다 (일반 Gmail 비밀번호 X).

#### 단계별 가이드:

1. **Google 계정 보안 설정** 이동
   - https://myaccount.google.com/security

2. **2단계 인증 활성화** (필수)
   - "Google에 로그인" 섹션에서 "2단계 인증" 클릭
   - 지시에 따라 설정

3. **앱 비밀번호 생성**
   - 2단계 인증 페이지 하단의 "앱 비밀번호" 클릭
   - "앱 선택"에서 "메일" 선택
   - "기기 선택"에서 "기타" 선택 → "GitHub Actions" 입력
   - "생성" 클릭
   - **16자리 비밀번호 복사** (다시 볼 수 없음!)

예시: `abcd efgh ijkl mnop` (공백 포함 또는 제거 둘 다 가능)

### 3. GitHub Secrets 설정

GitHub 저장소에서 민감 정보를 안전하게 저장합니다.

#### 단계:
1. GitHub 저장소 페이지로 이동
2. **Settings** 탭 클릭
3. 왼쪽 메뉴에서 **Secrets and variables** → **Actions** 클릭
4. **New repository secret** 버튼 클릭
5. 다음 5개의 Secrets를 추가:

| Secret Name | 설명 | 예시 |
|-------------|------|------|
| `CCF_USERNAME` | CCFGroup 로그인 아이디 | `SKGlobalKorea` |
| `CCF_PASSWORD` | CCFGroup 로그인 비밀번호 | `Sk15001657` |
| `SENDER_EMAIL` | 발신 Gmail 주소 | `your-email@gmail.com` |
| `SENDER_PASSWORD` | Gmail 앱 비밀번호 (위에서 생성) | `abcdefghijklmnop` |
| `RECIPIENT_EMAIL` | 수신 이메일 주소 | `recipient@company.com` |

#### Secret 추가 스크린샷 순서:
```
Settings → Secrets and variables → Actions → New repository secret
→ Name: CCF_USERNAME, Secret: SKGlobalKorea → Add secret
(나머지 4개도 동일하게 반복)
```

### 4. 파일 업로드

1. **저장소에 파일 추가**
   ```bash
   git add .github/workflows/daily-scraping.yml
   git add scrape_and_email.py
   git add requirements.txt
   git add README.md
   git commit -m "Add daily scraping workflow"
   git push
   ```

2. **또는 GitHub 웹에서 직접 업로드**
   - 각 파일을 해당 경로에 생성
   - `.github/workflows/` 폴더는 직접 생성 필요

## 📅 사용 방법

### 자동 실행
- 매일 **오전 10시 (한국시간)** 자동 실행
- 별도 조치 불필요

### 수동 실행 (테스트용)
1. GitHub 저장소에서 **Actions** 탭 클릭
2. 왼쪽에서 **"Daily CCFGroup Scraping"** 워크플로우 선택
3. **"Run workflow"** 버튼 클릭 → **"Run workflow"** 확인
4. 실행 결과 확인

### 실행 확인
- **Actions** 탭에서 각 실행 기록 확인
- 녹색 체크: 성공 ✅
- 빨간 X: 실패 ❌ (로그 확인 필요)

## 📧 이메일 내용

받게 될 이메일 예시:

```
제목: CCFGroup Market Data - 2025-01-27

본문:
안녕하세요,

2025년 01월 27일 CCFGroup 시장 데이터를 첨부합니다.

첨부 파일:
- benzene_daily_table_1.csv
- benzene_daily_table_2.csv
- styrene_daily_table_1.csv
- styrene_weekly_table_1.csv

자동 생성된 이메일입니다.
```

## 🛠️ 문제 해결

### 1. 이메일 전송 실패

**증상**: "이메일 전송 실패" 오류

**해결 방법**:
- Gmail 앱 비밀번호가 정확한지 확인
- 2단계 인증이 활성화되어 있는지 확인
- Secrets의 `SENDER_PASSWORD`에 공백 없이 입력했는지 확인
- Gmail이 "보안 수준이 낮은 앱" 차단하지 않는지 확인

### 2. 로그인 실패

**증상**: "로그인 완료" 메시지가 나오지 않음

**해결 방법**:
- `CCF_USERNAME`과 `CCF_PASSWORD`가 정확한지 확인
- CCFGroup 웹사이트가 정상 작동하는지 확인

### 3. CSV 파일 없음

**증상**: "전송할 CSV 파일이 없습니다" 메시지

**해결 방법**:
- 스크래핑 URL이 유효한지 확인
- 웹사이트 구조가 변경되었는지 확인
- Actions 로그에서 상세 오류 확인

### 4. 워크플로우가 실행되지 않음

**해결 방법**:
- `.github/workflows/daily-scraping.yml` 파일 경로 확인
- Actions 탭에서 워크플로우가 활성화되어 있는지 확인
- 저장소가 public인지 확인 (private 저장소는 분당 제한 있음)

## 📊 CSV 파일 다운로드

이메일 외에도 GitHub Actions Artifacts에서 CSV 파일 다운로드 가능:

1. **Actions** 탭 → 실행 기록 클릭
2. 하단 **Artifacts** 섹션에서 `market-data-csv` 다운로드
3. 7일간 보관됨

## ⚙️ 실행 시간 변경

다른 시간에 실행하고 싶다면 `daily-scraping.yml` 수정:

```yaml
on:
  schedule:
    # 매일 오후 3시 (UTC) = 한국시간 자정
    - cron: '0 15 * * *'
```

Cron 표현식 도구: https://crontab.guru/

## 🔒 보안 주의사항

- ⚠️ **절대 코드에 비밀번호를 직접 입력하지 마세요**
- ✅ 항상 GitHub Secrets 사용
- ✅ Private 저장소 사용 권장
- ✅ 정기적으로 비밀번호 변경

## 📝 라이선스

MIT License

## 💬 문의

문제가 발생하면 GitHub Issues에 등록해주세요.
