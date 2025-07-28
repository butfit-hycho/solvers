# 🚀 Instagram 스크래핑 도구 v2.1 ✨

**Google Sheets에서 Instagram 정보를 자동으로 수집하는 완전 자동화 도구**

## ✨ 주요 기능

- 📱 **Instagram 자동 스크래핑**: 팔로워, 팔로잉, 게시물 수 자동 수집
- 🌐 **원격 제어**: Google Sheets에서 버튼 클릭으로 스크래핑 시작/중단
- ⚡ **k/M/B 지원**: 1.1k, 2.5M, 1B 형식 자동 변환
- 🔄 **실시간 업데이트**: 스크래핑 결과가 바로 Google Sheets에 저장
- 🖥️ **멀티 플랫폼**: Windows, macOS, Linux 지원
- 🛡️ **안정성 강화**: 패키지 검증 및 오류 처리 개선 ✨
- 📦 **의존성 관리**: requirements.txt로 명확한 패키지 관리 ✨
- 🎯 **특정 행 스크래핑**: 원하는 행만 선택하여 개별 처리 ✨

---

## 📦 포함 파일들

```
instagram_scraper_package/
├── 📄 바로시작.py                    # 올인원 실행 프로그램 ⭐
├── 📄 portable_instagram_setup.py    # 자동 설치 스크립트
├── 📄 batch_instagram_scraper.py     # Instagram 스크래핑 엔진
├── 📄 instagram_control_server.py    # 원격 제어 서버
├── 📄 requirements.txt               # Python 패키지 의존성 ✨
├── 📄 설치_가이드.md                 # 상세 설치 가이드
├── 📄 Google_인증_설정.md            # Google 인증 설정법
├── 📄 README.md                      # 이 파일
└── 📁 instagram_scraper/             # 실행 환경
    ├── 📄 run_instagram_scraper.sh   # macOS/Linux 실행 스크립트 ✨
    ├── 📄 run_instagram_scraper.bat  # Windows 실행 스크립트 ✨
    └── ... (자동 생성 파일들)
```

---

## 🚀 빠른 시작 (3단계)

### **1️⃣ 바로시작 프로그램 실행**
```bash
python3 바로시작.py
```

**메뉴에서 "1️⃣ 처음 설치" 선택**
- ✅ Python 패키지 자동 설치
- ✅ Node.js + LocalTunnel 자동 설치  
- ✅ 실행 스크립트 자동 생성

### **2️⃣ Google 인증 파일 추가**
1. **Firebase Console** → **서비스 계정** → **JSON 키 생성**
2. **파일명을 `google_credentials.json`으로 변경**
3. **`instagram_scraper` 폴더에 복사**

💡 자세한 내용: `Google_인증_설정.md` 참고

### **3️⃣ Google Sheets Apps Script 설정**
1. **Google Sheets** → **확장프로그램** → **Apps Script**
2. **메뉴 코드 복사/붙여넣기** (설치_가이드.md에 있음)
3. **저장 후 Google Sheets에서 "🌐 Instagram 원격 제어" 메뉴 사용**

---

## 🎮 사용법

### **도구 실행**
```bash
# 바로시작 프로그램에서
python3 바로시작.py
# → "2️⃣ 바로 실행" 선택

# 또는 직접 실행
cd instagram_scraper
./run_instagram_scraper.sh      # macOS/Linux
run_instagram_scraper.bat       # Windows
```

### **Google Sheets에서 제어**
1. **Google Sheets 열기**
2. **메뉴: "🌐 Instagram 원격 제어"**
3. **"🚀 스크래핑 시작"** 클릭
4. **"🔍 상태 확인"**으로 진행률 모니터링

---

## 📊 Google Sheets 컬럼 구조

| 컬럼 | 내용 | 설명 |
|------|------|------|
| **D열** | Instagram URL | 스크래핑 대상 URL 입력 |
| **G열** | 팔로워 수 | 자동으로 채워짐 |
| **H열** | 팔로잉 수 | 자동으로 채워짐 |
| **I열** | 게시물 수 | 자동으로 채워짐 |

**예시:**
```
D열: https://www.instagram.com/username/
G열: 42,000 (자동)
H열: 7,159 (자동)  
I열: 2,082 (자동)
```

---

## ⭐ 특별 기능

### **숫자 형식 자동 변환**
- **1.1k** → **1,100**
- **2.5M** → **2,500,000**
- **1B** → **1,000,000,000**

### **실시간 진행률 표시**
- Google Sheets에서 스크래핑 진행 상황 실시간 확인
- 성공/실패 개수 모니터링

### **안정적인 스크래핑**
- Instagram 차단 우회 기술 적용
- requests 우선 → Selenium 백업 시스템

---

## 🆘 문제 해결

### **❌ "Chrome WebDriver 오류"**
→ Chrome 브라우저 최신 버전 설치

### **❌ "Node.js 없음"**  
→ https://nodejs.org/ 에서 Node.js 설치

### **❌ "Google Sheets 인증 실패"**
→ `Google_인증_설정.md` 가이드 참고

### **❌ "Instagram 스크래핑 실패"**
→ 일시적 차단, 몇 분 후 재시도

---

## 💡 도움말

**더 자세한 정보:**
- 📖 **설치_가이드.md**: 완전한 설치 가이드
- 🔧 **Google_인증_설정.md**: Google 인증 상세 설명
- 🚀 **바로시작.py**: 대화형 메뉴로 모든 기능 접근

**문제가 생기면:**
1. **오류 메시지 전체 복사**
2. **어떤 단계에서 발생했는지 설명**
3. **OS 정보 (Windows/macOS/Linux)**

---

## 🎉 설치 성공 후

**✅ Google Sheets에서 버튼 클릭만으로 Instagram 스크래핑**
**✅ 실시간 진행률 모니터링**
**✅ 자동 k/M/B 형식 변환**
**✅ 안정적이고 빠른 스크래핑**

**이제 Instagram 마케팅 데이터 수집이 완전 자동화됩니다!** 🚀

---

## 📞 지원

**Instagram 스크래핑 도구 v2.0**
- **개발**: AI Assistant  
- **특징**: 완전 자동화, 멀티 플랫폼 지원
- **업데이트**: 2024년 최신 Instagram API 대응

**행복한 스크래핑 되세요!** 😊 