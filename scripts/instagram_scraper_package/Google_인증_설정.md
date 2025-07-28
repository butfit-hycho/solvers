# 🔑 Google Sheets 인증 설정 상세 가이드

## 🎯 목표
Google Sheets에 Instagram 스크래핑 결과를 자동으로 저장하기 위한 인증 파일 생성

---

## 📋 단계별 가이드

### **1️⃣ Firebase Console 접속**
1. **브라우저에서** https://console.firebase.google.com **접속**
2. **Google 계정으로 로그인**

### **2️⃣ 프로젝트 선택**
1. **기존 프로젝트가 있으면** → **해당 프로젝트 클릭**
2. **새 프로젝트 만들기** → **프로젝트 이름 입력** → **만들기**

### **3️⃣ 서비스 계정 생성**
1. **좌측 메뉴에서** ⚙️ **"프로젝트 설정"** 클릭
2. **"서비스 계정"** 탭 클릭
3. **"새 비공개 키 생성"** 버튼 클릭
4. **"키 유형: JSON"** 선택 → **"키 생성"** 클릭

### **4️⃣ JSON 파일 다운로드**
1. **JSON 파일이 자동으로 다운로드됨**
2. **파일명 예시**: `project-name-123456-firebase-adminsdk-abcde-1234567890.json`

### **5️⃣ 파일명 변경 및 복사**
1. **다운로드된 파일명을** `google_credentials.json` **으로 변경**
2. **`instagram_scraper` 폴더에 복사**

**올바른 위치:**
```
instagram_scraper/
├── batch_instagram_scraper.py
├── instagram_control_server.py
├── google_credentials.json          ← 여기!
└── run_instagram_scraper.sh
```

---

## 🔍 JSON 파일 내용 확인

**올바른 JSON 파일은 다음과 같은 구조를 가집니다:**

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-...@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

**중요한 필드들:**
- ✅ `"type": "service_account"`
- ✅ `"project_id": "your-project-id"`
- ✅ `"client_email": "...@...iam.gserviceaccount.com"`
- ✅ `"private_key": "-----BEGIN PRIVATE KEY-----..."`

---

## 🔧 Google Sheets API 활성화

### **1️⃣ Google Cloud Console 접속**
1. https://console.cloud.google.com **접속**
2. **동일한 프로젝트 선택**

### **2️⃣ API 활성화**
1. **좌측 메뉴** → **"API 및 서비스"** → **"라이브러리"**
2. **"Google Sheets API"** 검색 → **클릭**
3. **"사용 설정"** 클릭
4. **"Google Drive API"**도 동일하게 활성화

---

## 🎯 Google Sheets 권한 설정

### **1️⃣ 서비스 계정 이메일 복사**
**JSON 파일에서 `client_email` 값 복사**
```json
"client_email": "firebase-adminsdk-abc123@your-project.iam.gserviceaccount.com"
```

### **2️⃣ Google Sheets에 권한 부여**
1. **대상 Google Sheets 열기**
2. **우측 상단 "공유"** 버튼 클릭
3. **복사한 서비스 계정 이메일 입력**
4. **권한: "편집자"** 선택
5. **"전송"** 클릭

---

## ✅ 설정 완료 확인

### **1️⃣ 파일 위치 확인**
```bash
ls -la instagram_scraper/google_credentials.json
```

### **2️⃣ 파일 내용 확인**
```bash
head -5 instagram_scraper/google_credentials.json
```

**출력 예시:**
```json
{
  "type": "service_account",
  "project_id": "your-project-123456",
  "private_key_id": "abcdef1234567890",
  "private_key": "-----BEGIN PRIVATE KEY-----\n..."
```

### **3️⃣ 권한 확인**
- **Google Sheets에서 서비스 계정 이메일이 "편집자"로 공유되어 있는지 확인**

---

## 🆘 문제 해결

### **❌ "인증 실패" 오류**
**원인:** 잘못된 JSON 파일 또는 권한 없음
**해결:**
1. **JSON 파일 재다운로드**
2. **Google Sheets 편집자 권한 재부여**
3. **파일명이 정확히 `google_credentials.json`인지 확인**

### **❌ "API 비활성화" 오류**
**원인:** Google Sheets API 미활성화
**해결:**
1. **Google Cloud Console** → **API 라이브러리**
2. **Google Sheets API + Google Drive API 활성화**

### **❌ "파일을 찾을 수 없음" 오류**
**원인:** 파일 위치 오류
**해결:**
1. **파일이 `instagram_scraper/` 폴더에 있는지 확인**
2. **파일명이 정확히 `google_credentials.json`인지 확인**

---

## 🎉 성공 확인

**인증 설정이 성공하면:**
1. **Instagram 스크래핑 결과가 Google Sheets에 자동 저장됨**
2. **오류 메시지 없이 "Google Sheets 업데이트 완료!" 메시지 출력**

---

## 📞 추가 도움

**여전히 문제가 있다면:**
1. **오류 메시지 전체 내용**
2. **JSON 파일의 `client_email` 값**
3. **Google Sheets URL**

**위 정보와 함께 문의해주세요!** 🚀 