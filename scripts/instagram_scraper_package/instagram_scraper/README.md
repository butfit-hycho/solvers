
# 🚀 Instagram 스크래핑 도구 사용 가이드

## 📋 설치 완료!
설치 디렉토리: /Users/cho/project/solvers/scripts/instagram_scraper_package/instagram_scraper

## 🔧 추가 설정 필요

### 1️⃣ Google Service Account JSON 파일
- Firebase Console에서 서비스 계정 JSON 파일 다운로드
- 파일명을 `google_credentials.json`으로 변경
- `/Users/cho/project/solvers/scripts/instagram_scraper_package/instagram_scraper` 폴더에 복사

### 2️⃣ Google Sheets Apps Script 설정
1. Google Sheets 열기
2. 확장프로그램 → Apps Script
3. 아래 코드 복사/붙여넣기:

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🌐 Instagram 원격 제어')
    .addItem('🔍 상태 확인', 'checkStatus')
    .addItem('🚀 스크래핑 시작', 'startScraping')
    .addItem('⏹️ 스크래핑 중단', 'stopScraping')
    .addToUi();
}

function checkStatus() {
  try {
    const response = UrlFetchApp.fetch('https://butfit-instagram-scraper.loca.lt/status', {
      'headers': {'Bypass-Tunnel-Reminder': 'true'}
    });
    const data = JSON.parse(response.getContentText());
    
    let message = `📊 Instagram 스크래핑 상태\n\n`;
    message += `🏃‍♂️ 실행 중: ${data.is_running ? 'YES' : 'NO'}\n`;
    message += `📈 진행률: ${data.progress}/${data.total}\n`;
    message += `✅ 성공: ${data.success_count}개\n`;
    message += `❌ 실패: ${data.fail_count}개\n`;
    
    if (data.current_item) {
      message += `🎯 현재 작업: ${data.current_item}\n`;
    }
    
    SpreadsheetApp.getUi().alert('상태 확인', message, SpreadsheetApp.getUi().ButtonSet.OK);
  } catch (error) {
    SpreadsheetApp.getUi().alert('❌ 연결 오류', '로컬 서버가 실행되지 않았거나 터널이 활성화되지 않았습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

function startScraping() {
  try {
    const response = UrlFetchApp.fetch('https://butfit-instagram-scraper.loca.lt/start', {
      'method': 'POST',
      'headers': {'Bypass-Tunnel-Reminder': 'true'}
    });
    
    SpreadsheetApp.getUi().alert('🚀 스크래핑 시작', '스크래핑이 시작되었습니다!', SpreadsheetApp.getUi().ButtonSet.OK);
  } catch (error) {
    SpreadsheetApp.getUi().alert('❌ 시작 실패', error.toString(), SpreadsheetApp.getUi().ButtonSet.OK);
  }
}
```

## 🎯 사용법

### 1️⃣ 도구 실행
- 터미널에서 `./run_instagram_scraper.sh` 실행

### 2️⃣ Google Sheets에서 제어
- Google Sheets 메뉴에서 "🌐 Instagram 원격 제어" 사용
- "🚀 스크래핑 시작" 클릭
- "🔍 상태 확인"으로 진행률 모니터링

## 🆘 문제 해결

### LocalTunnel 연결 실패
```bash
npm install -g localtunnel
lt --port 5555 --subdomain butfit-instagram-scraper
```

### Python 패키지 오류
```bash
pip install selenium gspread flask flask-cors requests
```

### Chrome WebDriver 오류
- Chrome 브라우저 최신 버전 설치 확인
- selenium 패키지 재설치

---
📞 문의: 설치 과정에서 문제가 있으면 오류 메시지와 함께 문의하세요!
