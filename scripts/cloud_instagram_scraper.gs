/**
 * 🌐 완전 클라우드 기반 Instagram 스크래핑
 * PC 설치 없이 Google Sheets에서 바로 실행!
 * 
 * 사용법:
 * 1. Google Sheets에서 확장프로그램 > Apps Script
 * 2. 이 코드 복사/붙여넣기
 * 3. 저장 후 실행
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🚀 Instagram 스크래핑 (클라우드)')
    .addItem('📊 Instagram 정보 가져오기', 'scrapeAllInstagramProfiles')
    .addItem('🔍 빈 행만 스크래핑', 'scrapeEmptyRows')
    .addItem('📋 상태 확인', 'checkStatus')
    .addSeparator()
    .addItem('⚙️ 설정 확인', 'showSettings')
    .addToUi();
}

/**
 * 모든 Instagram 프로필 스크래핑
 */
function scrapeAllInstagramProfiles() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('데이터가 없습니다!');
    return;
  }
  
  let successCount = 0;
  let failCount = 0;
  
  // D열(Instagram URL)부터 시작
  for (let row = 2; row <= lastRow; row++) {
    const instagramUrl = sheet.getRange(row, 4).getValue(); // D열
    
    if (!instagramUrl || instagramUrl.toString().trim() === '') {
      continue;
    }
    
    // 이미 스크래핑된 행은 건너뛰기 (G, H, I열에 값이 있으면)
    const followers = sheet.getRange(row, 7).getValue(); // G열
    const following = sheet.getRange(row, 8).getValue(); // H열
    const posts = sheet.getRange(row, 9).getValue(); // I열
    
    if (followers && following && posts) {
      console.log(`행 ${row}: 이미 스크래핑됨, 건너뛰기`);
      continue;
    }
    
    console.log(`행 ${row}: Instagram 스크래핑 시작 - ${instagramUrl}`);
    
    try {
      const result = scrapeInstagramProfile(instagramUrl.toString());
      
      if (result.success) {
        // G, H, I열에 결과 입력
        sheet.getRange(row, 7).setValue(result.followers); // G열: 팔로워
        sheet.getRange(row, 8).setValue(result.following); // H열: 팔로잉  
        sheet.getRange(row, 9).setValue(result.posts); // I열: 게시물
        
        console.log(`✅ 행 ${row} 성공: ${result.followers}/${result.following}/${result.posts}`);
        successCount++;
      } else {
        console.log(`❌ 행 ${row} 실패: ${result.error}`);
        failCount++;
      }
      
      // 요청 제한 방지를 위한 지연
      Utilities.sleep(2000); // 2초 대기
      
    } catch (error) {
      console.log(`💥 행 ${row} 예외: ${error.message}`);
      failCount++;
    }
  }
  
  SpreadsheetApp.getUi().alert(
    `Instagram 스크래핑 완료!\n✅ 성공: ${successCount}개\n❌ 실패: ${failCount}개`
  );
}

/**
 * 빈 행만 스크래핑 (G, H, I열이 비어있는 행)
 */
function scrapeEmptyRows() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let emptyRows = [];
  
  // 빈 행 찾기
  for (let row = 2; row <= lastRow; row++) {
    const instagramUrl = sheet.getRange(row, 4).getValue(); // D열
    const followers = sheet.getRange(row, 7).getValue(); // G열
    const following = sheet.getRange(row, 8).getValue(); // H열
    const posts = sheet.getRange(row, 9).getValue(); // I열
    
    if (instagramUrl && (!followers || !following || !posts)) {
      emptyRows.push(row);
    }
  }
  
  if (emptyRows.length === 0) {
    SpreadsheetApp.getUi().alert('스크래핑할 빈 행이 없습니다!');
    return;
  }
  
  SpreadsheetApp.getUi().alert(`${emptyRows.length}개 행을 스크래핑합니다.`);
  
  let successCount = 0;
  let failCount = 0;
  
  emptyRows.forEach((row, index) => {
    const instagramUrl = sheet.getRange(row, 4).getValue().toString();
    
    console.log(`[${index+1}/${emptyRows.length}] 행 ${row}: ${instagramUrl}`);
    
    try {
      const result = scrapeInstagramProfile(instagramUrl);
      
      if (result.success) {
        sheet.getRange(row, 7).setValue(result.followers);
        sheet.getRange(row, 8).setValue(result.following);
        sheet.getRange(row, 9).setValue(result.posts);
        
        console.log(`✅ 성공: ${result.followers}/${result.following}/${result.posts}`);
        successCount++;
      } else {
        console.log(`❌ 실패: ${result.error}`);
        failCount++;
      }
      
      Utilities.sleep(2000); // 2초 대기
      
    } catch (error) {
      console.log(`💥 예외: ${error.message}`);
      failCount++;
    }
  });
  
  SpreadsheetApp.getUi().alert(
    `빈 행 스크래핑 완료!\n✅ 성공: ${successCount}개\n❌ 실패: ${failCount}개`
  );
}

/**
 * Instagram 프로필 스크래핑 (핵심 함수)
 */
function scrapeInstagramProfile(instagramUrl) {
  try {
    // URL 정규화
    let url = instagramUrl.trim();
    if (!url.startsWith('http')) {
      url = `https://www.instagram.com/${url.replace('@', '')}/`;
    }
    
    console.log(`🔍 스크래핑 시도: ${url}`);
    
    // HTTP 요청 옵션
    const options = {
      'method': 'GET',
      'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
      },
      'muteHttpExceptions': true
    };
    
    // Instagram 페이지 요청
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      console.log(`❌ HTTP 오류: ${responseCode}`);
      return {
        followers: 0,
        following: 0,
        posts: 0,
        success: false,
        error: `HTTP ${responseCode}`
      };
    }
    
    const html = response.getContentText();
    
    // 로그인 페이지 체크
    if (html.includes('accounts/login') || html.includes('Login • Instagram')) {
      console.log(`⚠️ 로그인 페이지 감지`);
      return {
        followers: 0,
        following: 0,
        posts: 0,
        success: false,
        error: '로그인 요구'
      };
    }
    
    // 숫자 파싱 함수 (k/M/B 지원)
    function parseNumber(text) {
      if (!text) return 0;
      
      text = text.replace(/,/g, '').trim().toUpperCase();
      
      if (text.endsWith('K')) {
        return parseInt(parseFloat(text.slice(0, -1)) * 1000);
      } else if (text.endsWith('M')) {
        return parseInt(parseFloat(text.slice(0, -1)) * 1000000);
      } else if (text.endsWith('B')) {
        return parseInt(parseFloat(text.slice(0, -1)) * 1000000000);
      } else {
        try {
          return parseInt(parseFloat(text));
        } catch (e) {
          return 0;
        }
      }
    }
    
    // 정규식으로 데이터 추출
    const followersRegex = /(\d+(?:[.,]\d+)*[KMBkmb]?)\s*followers?/gi;
    const followingRegex = /(\d+(?:[.,]\d+)*[KMBkmb]?)\s*following/gi;
    const postsRegex = /(\d+(?:[.,]\d+)*[KMBkmb]?)\s*posts?/gi;
    
    const followersMatch = followersRegex.exec(html);
    const followingMatch = followingRegex.exec(html);
    const postsMatch = postsRegex.exec(html);
    
    const followers = followersMatch ? parseNumber(followersMatch[1]) : 0;
    const following = followingMatch ? parseNumber(followingMatch[1]) : 0;
    const posts = postsMatch ? parseNumber(postsMatch[1]) : 0;
    
    if (followers > 0 || following > 0 || posts > 0) {
      console.log(`✅ 성공: 팔로워 ${followers.toLocaleString()}, 팔로잉 ${following.toLocaleString()}, 게시물 ${posts.toLocaleString()}`);
      return {
        followers: followers,
        following: following,
        posts: posts,
        success: true,
        error: null
      };
    } else {
      console.log(`⚠️ 데이터 없음`);
      return {
        followers: 0,
        following: 0,
        posts: 0,
        success: false,
        error: '데이터 없음'
      };
    }
    
  } catch (error) {
    console.log(`💥 예외 발생: ${error.message}`);
    return {
      followers: 0,
      following: 0,
      posts: 0,
      success: false,
      error: error.message
    };
  }
}

/**
 * 상태 확인
 */
function checkStatus() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  
  let totalRows = 0;
  let completedRows = 0;
  let emptyRows = 0;
  
  for (let row = 2; row <= lastRow; row++) {
    const instagramUrl = sheet.getRange(row, 4).getValue();
    
    if (instagramUrl && instagramUrl.toString().trim() !== '') {
      totalRows++;
      
      const followers = sheet.getRange(row, 7).getValue();
      const following = sheet.getRange(row, 8).getValue();
      const posts = sheet.getRange(row, 9).getValue();
      
      if (followers && following && posts) {
        completedRows++;
      } else {
        emptyRows++;
      }
    }
  }
  
  SpreadsheetApp.getUi().alert(
    `📊 Instagram 스크래핑 상태\n\n` +
    `📋 전체 Instagram URL: ${totalRows}개\n` +
    `✅ 완료된 행: ${completedRows}개\n` +
    `⏳ 대기 중인 행: ${emptyRows}개\n` +
    `📈 완료율: ${totalRows > 0 ? Math.round((completedRows / totalRows) * 100) : 0}%`
  );
}

/**
 * 설정 확인
 */
function showSettings() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetUrl = SpreadsheetApp.getActiveSpreadsheet().getUrl();
  
  SpreadsheetApp.getUi().alert(
    `⚙️ 클라우드 Instagram 스크래핑 설정\n\n` +
    `📋 시트: ${sheet.getName()}\n` +
    `🔗 URL: ${sheetUrl}\n\n` +
    `📌 컬럼 구성:\n` +
    `• D열: Instagram URL\n` +
    `• G열: 팔로워 수\n` +
    `• H열: 팔로잉 수\n` +
    `• I열: 게시물 수\n\n` +
    `🚀 PC 설치 없이 브라우저에서만 실행됩니다!`
  );
}

/**
 * 테스트 함수 (개별 URL 테스트용)
 */
function testInstagramScraping() {
  const testUrl = 'https://www.instagram.com/malangjay/';
  console.log(`🧪 테스트 시작: ${testUrl}`);
  
  const result = scrapeInstagramProfile(testUrl);
  console.log(`📊 테스트 결과:`, result);
  
  SpreadsheetApp.getUi().alert(
    `🧪 테스트 결과\n\n` +
    `URL: ${testUrl}\n` +
    `성공: ${result.success ? 'YES' : 'NO'}\n` +
    `팔로워: ${result.followers.toLocaleString()}\n` +
    `팔로잉: ${result.following.toLocaleString()}\n` +
    `게시물: ${result.posts.toLocaleString()}\n` +
    `오류: ${result.error || '없음'}`
  );
} 