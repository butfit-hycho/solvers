# 체험단 운영 툴 (Experience Team Management Tool)

체험단 모집부터 관리까지 자동화된 워크플로우를 제공하는 통합 관리 도구입니다.

## 📋 프로젝트 개요

이 프로젝트는 체험단 운영의 전체 프로세스를 자동화하여 효율적인 관리를 가능하게 합니다:

1. **체험단 모집 설문** - 온라인 설문을 통한 체험단 지원자 수집
2. **인스타그램 정보 수집** - 지원자의 인스타그램 계정 분석 (팔로워, 게시물 등)
3. **멤버십 검수** - 내부 DB와 연동하여 기존 회원 여부 확인
4. **데이터 통합 관리** - 구글 시트 또는 백오피스를 통한 종합 정보 관리

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   설문 폼       │ -> │   백엔드 API     │ -> │  데이터 저장소   │
│   (Frontend)    │    │   (Python)       │    │  (DB + Sheets)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ 인스타그램 스크래핑 │
                       │ + 멤버십 검수     │
                       └──────────────────┘
```

## 🚀 주요 기능

### 1. 체험단 모집 시스템
- 웹 기반 설문 폼
- 필수/선택 항목 설정 가능
- 인스타그램 계정 정보 수집
- 실시간 지원자 현황 확인

### 2. 인스타그램 정보 수집
- 팔로워 수 자동 수집
- 게시물 수 및 최근 활동 분석
- 인플루언서 등급 자동 분류
- 스크래핑 결과 데이터베이스 저장

### 3. 멤버십 검수 시스템
- 내부 회원 DB와 자동 매칭
- 중복 지원 방지
- 기존 체험단 참여 이력 확인
- 블랙리스트 관리

### 4. 데이터 관리 백오피스
- 구글 스프레드시트 실시간 연동
- 지원자 정보 종합 대시보드
- 선발/탈락 관리 기능
- 엑셀 내보내기 지원

## 📁 프로젝트 구조

```
solvers/
├── README.md                 # 프로젝트 문서
├── requirements.txt          # Python 의존성
├── app/                      # 메인 애플리케이션
│   ├── main.py              # FastAPI 메인 앱
│   ├── config.py            # 설정 관리
│   ├── database.py          # DB 연결 설정
│   ├── models/              # 데이터 모델
│   │   ├── applicant.py     # 지원자 모델
│   │   ├── instagram.py     # 인스타그램 정보 모델
│   │   └── membership.py    # 멤버십 정보 모델
│   ├── api/                 # API 엔드포인트
│   │   ├── survey.py        # 설문 관련 API
│   │   ├── instagram.py     # 인스타그램 스크래핑 API
│   │   ├── membership.py    # 멤버십 검수 API
│   │   └── admin.py         # 관리자 API
│   ├── services/            # 비즈니스 로직
│   │   ├── scraper.py       # 인스타그램 스크래핑
│   │   ├── membership_checker.py # 멤버십 검수
│   │   └── google_sheets.py # 구글 시트 연동
│   └── utils/               # 유틸리티
│       ├── validators.py    # 데이터 검증
│       └── helpers.py       # 도우미 함수
├── frontend/                # 프론트엔드 (선택사항)
│   ├── index.html          # 설문 폼
│   ├── admin.html          # 관리자 대시보드
│   ├── css/                # 스타일시트
│   └── js/                 # JavaScript
├── data/                   # 데이터 파일
│   ├── database.db         # SQLite 데이터베이스
│   └── exports/            # 내보내기 파일들
├── scripts/                # 유틸리티 스크립트
│   ├── setup_db.py         # DB 초기화
│   └── sync_sheets.py      # 구글 시트 동기화
├── tests/                  # 테스트 파일
└── docs/                   # 추가 문서

```

## 🛠️ 기술 스택

### Backend
- **Python 3.9+** - 메인 개발 언어
- **FastAPI** - 고성능 웹 프레임워크
- **SQLAlchemy** - ORM 및 데이터베이스 관리
- **Pydantic** - 데이터 검증 및 직렬화

### 데이터 수집 & 연동
- **Selenium/BeautifulSoup** - 인스타그램 스크래핑
- **Google Sheets API** - 구글 스프레드시트 연동
- **SQLite/PostgreSQL** - 데이터베이스

### Frontend (선택사항)
- **HTML5/CSS3/JavaScript** - 기본 웹 인터페이스
- **Bootstrap** - 반응형 디자인
- **Chart.js** - 데이터 시각화

## ⚙️ 설치 및 실행

### 1. 환경 설정
```bash
# 프로젝트 클론
git clone <repository-url>
cd solvers

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 필요한 API 키 및 설정 입력
# - Google Sheets API 키
# - 데이터베이스 URL
# - Instagram 스크래핑 설정
```

### 3. 데이터베이스 초기화
```bash
python3 scripts/setup_db.py
```

### 4. 서버 실행
```bash
# 개발 서버 실행
python3 app/main.py

# 또는 uvicorn 사용
uvicorn app.main:app --reload --port 8000
```

## 📊 사용 방법

### 1. 체험단 모집 설문 만들기
- 관리자 대시보드에서 새 설문 생성
- 필수 항목 및 질문 설정
- 설문 링크 생성 및 공유

### 2. 지원자 관리
- 실시간 지원자 현황 모니터링
- 인스타그램 정보 자동 수집 확인
- 멤버십 검수 결과 검토

### 3. 데이터 내보내기
- 구글 스프레드시트로 자동 동기화
- Excel 파일로 내보내기
- 커스텀 필터링 및 정렬

## 🔐 보안 및 준수사항

- **개인정보보호**: 수집된 데이터는 암호화되어 저장
- **Instagram 정책 준수**: 공개된 정보만 수집, API 제한 준수
- **GDPR 준수**: 데이터 삭제 요청 처리 기능 포함

## 🤝 기여 방법

1. Fork 프로젝트
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치 푸시 (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🆘 지원 및 문의

- 이슈 리포트: GitHub Issues 탭 활용
- 기능 제안: Discussions 섹션 활용
- 긴급 문의: [연락처 정보]

---

**Note**: 이 도구는 Instagram의 이용약관을 준수하며, 공개된 정보만을 수집합니다. 상업적 이용 시 해당 플랫폼의 정책을 확인하시기 바랍니다. 