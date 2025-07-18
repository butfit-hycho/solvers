# BUTFIT 체험단 모집 프론트엔드

BUTFIT 체험단 모집을 위한 웹 애플리케이션 프론트엔드입니다.

## 🚀 주요 기능

- **모던 디자인**: Pretendard 폰트와 네온 그린 (#00FF47) 테마
- **반응형 레이아웃**: 모바일 우선 디자인
- **실시간 유효성 검사**: 폼 입력 검증
- **주소 자동완성**: 다음/카카오 Postcode API 연동
- **전화번호 자동 포맷팅**: 010-0000-0000 형식

## 🛠️ 기술 스택

- **HTML5/CSS3/JavaScript** - 순수 웹 기술
- **Pretendard Font** - 한글 최적화 폰트
- **Daum Postcode API** - 주소 검색
- **Vercel** - 배포 플랫폼

## 📱 페이지 구성

### 메인 페이지 (`/`)
- 체험단 지원서 폼
- 이름, 전화번호, 인스타그램 계정, 배송 주소 입력
- 개인정보 동의 및 제출

### 성공 페이지
- 지원 완료 메시지
- 다시 지원하기 버튼

## 🔧 로컬 개발

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 브라우저에서 접속
# http://localhost:3000
```

## 🌐 배포

### Vercel 자동 배포
1. GitHub 저장소와 연결
2. Vercel에서 자동 빌드 및 배포
3. 도메인 설정 완료

### 수동 배포
```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel --prod
```

## ⚙️ 환경 설정

### API 엔드포인트 변경
`index.html` 파일의 JavaScript 섹션에서 API URL을 수정하세요:

```javascript
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-backend-url.com'; // 실제 백엔드 URL로 변경
```

## 📊 폼 데이터 구조

```json
{
  "name": "홍길동",
  "phone": "010-1234-5678",
  "instagram_url": "https://instagram.com/username",
  "address_zipcode": "12345",
  "address_main": "서울시 강남구 테헤란로",
  "address_detail": "123호",
  "address_full": "(12345) 서울시 강남구 테헤란로 123호",
  "agrees_privacy": true
}
```

## 🎨 디자인 시스템

### 컬러 팔레트
- **Primary**: #00FF47 (네온 그린)
- **Background**: #09080E (다크 그레이)
- **Container**: #1A1A25 (라이트 그레이)
- **Border**: #2A2A35 (미드 그레이)

### 타이포그래피
- **Font Family**: Pretendard
- **Title**: 32px, 800 weight
- **Body**: 16px, 400 weight
- **Label**: 14px, 600 weight

## 🔐 보안

- **HTTPS Only**: 모든 통신 암호화
- **CORS 설정**: 안전한 크로스 오리진 요청
- **CSP 헤더**: 콘텐츠 보안 정책 적용

## 📱 브라우저 지원

- **Chrome**: 90+
- **Safari**: 14+
- **Firefox**: 88+
- **Edge**: 90+

## 🚨 문제 해결

### API 연결 오류
1. 백엔드 서버가 실행 중인지 확인
2. CORS 설정이 올바른지 확인
3. API URL이 정확한지 확인

### 주소 검색 오류
1. Daum Postcode API 스크립트 로딩 확인
2. 네트워크 연결 상태 확인

## 📝 라이선스

MIT License

## 👥 팀

- **Frontend**: Vercel 배포
- **Backend**: Flask API 서버
- **Database**: SQLite + PostgreSQL
- **Analytics**: Google Sheets 연동 