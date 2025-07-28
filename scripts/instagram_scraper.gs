/**
 * Google Apps Script용 인스타그램 스크래핑 도구 (최신 컬럼 구조 적용)
 * 구글 시트에서 직접 실행 가능
 * 
 * 컬럼 구조: 체험단, 이름, 휴대폰, 인스타그램, 우편번호, 주소, 팔로워, 팔로잉, 게시물, 지점, 멤버십이름, 시작일, 종료일, 재등록여부, (빈칸), 제출일시
 */

/**
 * 메뉴 생성 함수 (스프레드시트 열 때 자동 실행)
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔧 버핏체험단 도구')
    .addSubMenu(
      ui.createMenu('📱 인스타그램 스크래핑')
        .addItem('🚀 전체 일괄 스크래핑', 'batchInstagramScraping')
        .addItem('👆 선택된 행만 스크래핑', 'scrapeSingleRow')
        .addSeparator()
        .addItem('📝 수동 입력', 'manualInputInstagramData')
        .addItem('🧹 스크래핑 결과 초기화', 'clearInstagramData')
    )
    .addSubMenu(
      ui.createMenu('📊 데이터 관리')
        .addItem('📈 스크래핑 현황 확인', 'checkScrapingStatus')
        .addItem('📋 빈 데이터 찾기', 'findEmptyData')
        .addItem('🔍 중복 데이터 확인', 'findDuplicateData')
    )
    .addSubMenu(
      ui.createMenu('⚙️ 설정')
        .addItem('🎯 테스트 스크래핑', 'testScraping')
        .addItem('📖 사용법 보기', 'showInstructions')
        .addItem('ℹ️ 정보', 'showAbout')
    )
    .addToUi();
}

/**
 * 사용법 안내
 */
function showInstructions() {
  const instructions = `
📱 버핏체험단 인스타그램 스크래핑 도구 사용법

📋 컬럼 구조 (최신):
체험단, 이름, 휴대폰, 인스타그램, 우편번호, 주소, 팔로워, 팔로잉, 게시물, 지점, 멤버십이름, 시작일, 종료일, 재등록여부, (빈칸), 제출일시

🔧 기능:
1. 🚀 전체 일괄 스크래핑
   - 빈 인스타그램 정보가 있는 모든 행을 자동으로 처리
   - 인스타그램 URL이 있지만 팔로워/팔로잉/게시물 정보가 비어있는 행들을 찾아서 스크래핑
   - 시간이 오래 걸릴 수 있음 (행당 2-3초)

2. 👆 선택된 행만 스크래핑  
   - 특정 행을 선택한 후 실행
   - 빠른 테스트나 재시도에 유용

3. 📝 수동 입력
   - 스크래핑이 실패한 경우 직접 입력
   - 팔로워, 팔로잉, 게시물 수를 차례로 입력

4. 📊 데이터 관리
   - 현황 확인, 빈 데이터 찾기, 중복 확인 등

⚠️ 주의사항:
- Instagram 정책상 스크래핑이 실패할 수 있습니다
- 실패 시 수동 입력을 이용해주세요
- 요청 간격을 두어 차단을 방지합니다
- 스크래핑 결과는 G, H, I 열(팔로워, 팔로잉, 게시물)에 저장됩니다
  `;
  
  Browser.msgBox('사용법 안내', instructions, Browser.Buttons.OK);
}

/**
 * 정보 표시
 */
function showAbout() {
  const about = `
🔧 버핏체험단 인스타그램 스크래핑 도구

버전: 2.1 (최신 컬럼 구조 적용)
개발: AI Assistant
목적: 체험단 지원자 인스타그램 정보 자동 수집

📊 대상 컬럼:
• D열: 인스타그램 URL (입력)
• G열: 팔로워 수 (스크래핑 결과)
• H열: 팔로잉 수 (스크래핑 결과)  
• I열: 게시물 수 (스크래핑 결과)

기능:
✅ 자동 인스타그램 스크래핑
✅ 수동 데이터 입력
✅ 데이터 현황 관리
✅ 중복/빈 데이터 확인

문의: 관리자에게 연락하세요
  `;
  
  Browser.msgBox('도구 정보', about, Browser.Buttons.OK);
}

/**
 * 스크래핑 현황 확인
 */
function checkScrapingStatus() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const instagramCol = headers.indexOf('인스타그램');  // D열
  const followersCol = headers.indexOf('팔로워');     // G열
  
  if (instagramCol === -1) {
    Browser.msgBox('오류', '인스타그램 컬럼을 찾을 수 없습니다.', Browser.Buttons.OK);
    return;
  }
  
  let totalRows = data.length - 1; // 헤더 제외
  let hasInstagram = 0;
  let hasFollowers = 0;
  let completed = 0;
  let pending = 0;
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const instagramAccount = row[instagramCol];
    const followersValue = row[followersCol];
    
    if (instagramAccount && instagramAccount.trim()) {
      hasInstagram++;
      
      if (followersValue && followersValue !== '') {
        hasFollowers++;
        completed++;
      } else {
        pending++;
      }
    }
  }
  
  const status = `
📊 인스타그램 스크래핑 현황

📋 전체 데이터: ${totalRows}개
📱 인스타그램 계정 있음: ${hasInstagram}개
✅ 스크래핑 완료: ${completed}개
⏳ 스크래핑 대기: ${pending}개
📈 완료율: ${hasInstagram > 0 ? Math.round((completed/hasInstagram)*100) : 0}%

${pending > 0 ? '💡 "전체 일괄 스크래핑"을 실행해보세요!' : '🎉 모든 스크래핑이 완료되었습니다!'}
  `;
  
  Browser.msgBox('스크래핑 현황', status, Browser.Buttons.OK);
}

/**
 * 빈 데이터 찾기
 */
function findEmptyData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const nameCol = headers.indexOf('이름');
  const instagramCol = headers.indexOf('인스타그램');
  const followersCol = headers.indexOf('팔로워');
  
  let emptyInstagram = [];
  let emptyFollowers = [];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const name = row[nameCol] || `${i+1}행`;
    const instagramAccount = row[instagramCol];
    const followersValue = row[followersCol];
    
    if (!instagramAccount || !instagramAccount.trim()) {
      emptyInstagram.push(name);
    } else if (!followersValue || followersValue === '') {
      emptyFollowers.push(name);
    }
  }
  
  let message = '🔍 빈 데이터 검색 결과\n\n';
  
  if (emptyInstagram.length > 0) {
    message += `📱 인스타그램 계정 없음 (${emptyInstagram.length}개):\n`;
    message += emptyInstagram.slice(0, 10).join(', ');
    if (emptyInstagram.length > 10) {
      message += ` 외 ${emptyInstagram.length - 10}개`;
    }
    message += '\n\n';
  }
  
  if (emptyFollowers.length > 0) {
    message += `📊 팔로워 정보 없음 (${emptyFollowers.length}개):\n`;
    message += emptyFollowers.slice(0, 10).join(', ');
    if (emptyFollowers.length > 10) {
      message += ` 외 ${emptyFollowers.length - 10}개`;
    }
    message += '\n\n';
  }
  
  if (emptyInstagram.length === 0 && emptyFollowers.length === 0) {
    message += '🎉 모든 데이터가 완전합니다!';
  }
  
  Browser.msgBox('빈 데이터 검색', message, Browser.Buttons.OK);
}

/**
 * 중복 데이터 확인
 */
function findDuplicateData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const nameCol = headers.indexOf('이름');
  const phoneCol = headers.indexOf('휴대폰');  // 휴대폰으로 변경
  const instagramCol = headers.indexOf('인스타그램');
  
  let phoneMap = new Map();
  let instagramMap = new Map();
  let duplicates = [];
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const name = row[nameCol] || `${i+1}행`;
    const phone = row[phoneCol];
    const instagram = row[instagramCol];
    
    // 전화번호 중복 체크
    if (phone && phone.trim()) {
      if (phoneMap.has(phone)) {
        duplicates.push(`📞 휴대폰 중복: ${name} ↔ ${phoneMap.get(phone)}`);
      } else {
        phoneMap.set(phone, name);
      }
    }
    
    // 인스타그램 중복 체크  
    if (instagram && instagram.trim()) {
      if (instagramMap.has(instagram)) {
        duplicates.push(`📱 인스타그램 중복: ${name} ↔ ${instagramMap.get(instagram)}`);
      } else {
        instagramMap.set(instagram, name);
      }
    }
  }
  
  let message = '🔍 중복 데이터 검색 결과\n\n';
  
  if (duplicates.length > 0) {
    message += duplicates.slice(0, 10).join('\n');
    if (duplicates.length > 10) {
      message += `\n\n... 외 ${duplicates.length - 10}개 더`;
    }
  } else {
    message += '🎉 중복 데이터가 없습니다!';
  }
  
  Browser.msgBox('중복 데이터 검색', message, Browser.Buttons.OK);
}

/**
 * 스크래핑 결과 초기화
 */
function clearInstagramData() {
  const response = Browser.msgBox(
    '데이터 초기화', 
    '정말로 모든 인스타그램 스크래핑 결과를 초기화하시겠습니까?\n(팔로워, 팔로잉, 게시물 수가 모두 삭제됩니다)', 
    Browser.Buttons.YES_NO
  );
  
  if (response !== Browser.Buttons.YES) return;
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const followersCol = headers.indexOf('팔로워');  // G열
  const followingCol = headers.indexOf('팔로잉'); // H열
  const postsCol = headers.indexOf('게시물');     // I열
  
  let cleared = 0;
  
  for (let i = 1; i < data.length; i++) {
    if (followersCol !== -1) {
      sheet.getRange(i + 1, followersCol + 1).setValue('');
      cleared++;
    }
    if (followingCol !== -1) {
      sheet.getRange(i + 1, followingCol + 1).setValue('');
    }
    if (postsCol !== -1) {
      sheet.getRange(i + 1, postsCol + 1).setValue('');
    }
  }
  
  Browser.msgBox('초기화 완료', `${cleared}개 행의 인스타그램 데이터가 초기화되었습니다.`, Browser.Buttons.OK);
}

/**
 * 메인 함수: 빈 인스타그램 정보를 일괄 스크래핑 (진행률 표시)
 */
function batchInstagramScraping() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // 컬럼 인덱스 찾기 (최신 구조)
  const nameCol = headers.indexOf('이름');
  const instagramCol = headers.indexOf('인스타그램'); // D열
  const followersCol = headers.indexOf('팔로워');     // G열
  const followingCol = headers.indexOf('팔로잉');    // H열
  const postsCol = headers.indexOf('게시물');        // I열
  
  if (instagramCol === -1) {
    Browser.msgBox('오류', '인스타그램 컬럼을 찾을 수 없습니다.\n컬럼명이 "인스타그램"인지 확인해주세요.', Browser.Buttons.OK);
    return;
  }
  
  // 빈 인스타그램 정보 행 찾기
  let emptyRows = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const instagramAccount = row[instagramCol];
    const followersValue = row[followersCol];
    
    if (instagramAccount && instagramAccount.trim() && (!followersValue || followersValue === '')) {
      emptyRows.push({
        index: i,
        name: row[nameCol] || `${i+1}행`,
        instagram: instagramAccount
      });
    }
  }
  
  if (emptyRows.length === 0) {
    Browser.msgBox('알림', '스크래핑할 대상이 없습니다.\n모든 인스타그램 정보가 이미 채워져 있습니다.', Browser.Buttons.OK);
    return;
  }
  
  // 시작 확인
  const response = Browser.msgBox(
    '일괄 스크래핑 시작', 
    `${emptyRows.length}개의 인스타그램 계정을 스크래핑합니다.\n예상 소요시간: ${Math.ceil(emptyRows.length * 2.5)}초\n\n계속하시겠습니까?`, 
    Browser.Buttons.YES_NO
  );
  
  if (response !== Browser.Buttons.YES) return;
  
  let processed = 0;
  let failed = 0;
  
  // 각 행에 대해 스크래핑 수행
  for (let i = 0; i < emptyRows.length; i++) {
    const rowData = emptyRows[i];
    
    try {
      console.log(`[${i+1}/${emptyRows.length}] ${rowData.name} 스크래핑 중...`);
      
      // 인스타그램 정보 스크래핑 시도
      const result = scrapeInstagramProfile(rowData.instagram);
      
      if (result.success) {
        // 구글 시트 업데이트 (G, H, I 열)
        if (followersCol !== -1) sheet.getRange(rowData.index + 1, followersCol + 1).setValue(result.followers);
        if (followingCol !== -1) sheet.getRange(rowData.index + 1, followingCol + 1).setValue(result.following);
        if (postsCol !== -1) sheet.getRange(rowData.index + 1, postsCol + 1).setValue(result.posts);
        
        processed++;
        console.log(`✅ ${rowData.name} 완료: 팔로워 ${result.followers}, 팔로잉 ${result.following}, 게시물 ${result.posts}`);
      } else {
        failed++;
        console.log(`❌ ${rowData.name} 실패: ${result.error}`);
      }
      
      // 진행률 표시 (5개마다)
      if ((i + 1) % 5 === 0 || i === emptyRows.length - 1) {
        const progress = Math.round(((i + 1) / emptyRows.length) * 100);
        SpreadsheetApp.getActiveSpreadsheet().toast(
          `진행률: ${progress}% (${i + 1}/${emptyRows.length})`,
          '인스타그램 스크래핑',
          3
        );
      }
      
      // 요청 간격 (Instagram 정책 준수)
      if (i < emptyRows.length - 1) {
        Utilities.sleep(2500); // 2.5초 대기
      }
      
    } catch (error) {
      failed++;
      console.log(`❌ ${rowData.name} 오류: ${error.toString()}`);
    }
  }
  
  // 최종 결과 표시
  const successRate = Math.round((processed / emptyRows.length) * 100);
  Browser.msgBox(
    '일괄 스크래핑 완료', 
    `✅ 성공: ${processed}개\n❌ 실패: ${failed}개\n📊 성공률: ${successRate}%\n\n${failed > 0 ? '실패한 항목은 수동 입력을 이용해주세요.' : '모든 스크래핑이 완료되었습니다!'}`, 
    Browser.Buttons.OK
  );
}

/**
 * 인스타그램 프로필 정보 스크래핑
 * @param {string} instagramUrl - 인스타그램 URL 또는 사용자명
 * @return {Object} 스크래핑 결과
 */
function scrapeInstagramProfile(instagramUrl) {
  if (!instagramUrl || !instagramUrl.trim()) {
    return {followers: 0, following: 0, posts: 0, success: false, error: 'URL 없음'};
  }
  
  // URL 정규화
  let url = instagramUrl.trim();
  if (!url.startsWith('http')) {
    url = `https://www.instagram.com/${url.replace('@', '')}/`;
  }
  
  try {
    // 방법 1: UrlFetchApp으로 HTML 요청
    const response = UrlFetchApp.fetch(url, {
      'method': 'GET',
      'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      },
      'muteHttpExceptions': true
    });
    
    if (response.getResponseCode() !== 200) {
      return {followers: 0, following: 0, posts: 0, success: false, error: `HTTP ${response.getResponseCode()}`};
    }
    
    const html = response.getContentText();
    
    // 간단한 정규식으로 데이터 추출 시도
    const result = parseInstagramHTML(html);
    
    if (result.success) {
      return result;
    }
    
    // 방법 2: 외부 API 사용 (예시)
    return tryExternalAPI(url);
    
  } catch (error) {
    return {followers: 0, following: 0, posts: 0, success: false, error: error.toString()};
  }
}

/**
 * HTML에서 인스타그램 정보 파싱
 * @param {string} html - Instagram 페이지 HTML
 * @return {Object} 파싱 결과
 */
function parseInstagramHTML(html) {
  try {
    // JSON-LD 스크립트에서 데이터 추출 시도
    const jsonLdMatch = html.match(/<script type="application\/ld\+json"[^>]*>(.*?)<\/script>/s);
    if (jsonLdMatch) {
      const jsonData = JSON.parse(jsonLdMatch[1]);
      if (jsonData && jsonData.mainEntityOfPage) {
        // 구조화된 데이터에서 정보 추출
        // Instagram의 구조화된 데이터는 제한적이므로 다른 방법 필요
      }
    }
    
    // 메타태그에서 정보 추출 시도
    const followerMatch = html.match(/(\d+(?:,\d+)*)\s*Followers/i);
    const followingMatch = html.match(/(\d+(?:,\d+)*)\s*Following/i);
    const postsMatch = html.match(/(\d+(?:,\d+)*)\s*Posts/i);
    
    if (followerMatch || followingMatch || postsMatch) {
      return {
        followers: followerMatch ? parseInt(followerMatch[1].replace(/,/g, '')) : 0,
        following: followingMatch ? parseInt(followingMatch[1].replace(/,/g, '')) : 0,
        posts: postsMatch ? parseInt(postsMatch[1].replace(/,/g, '')) : 0,
        success: true,
        error: null
      };
    }
    
    return {followers: 0, following: 0, posts: 0, success: false, error: '데이터 파싱 실패'};
    
  } catch (error) {
    return {followers: 0, following: 0, posts: 0, success: false, error: `파싱 오류: ${error.toString()}`};
  }
}

/**
 * 외부 API를 사용한 스크래핑 시도 (예시)
 * @param {string} url - 인스타그램 URL
 * @return {Object} API 결과
 */
function tryExternalAPI(url) {
  // 예시: RapidAPI의 Instagram API 사용
  // 실제 사용시에는 API 키가 필요합니다
  
  try {
    // 무료 Instagram API 서비스 예시 (실제로는 API 키 필요)
    /*
    const apiUrl = 'https://instagram-scraper-2022.p.rapidapi.com/ig/info_username/';
    const username = url.split('/').filter(x => x).pop();
    
    const response = UrlFetchApp.fetch(apiUrl, {
      'method': 'POST',
      'headers': {
        'X-RapidAPI-Key': 'YOUR_API_KEY_HERE',
        'X-RapidAPI-Host': 'instagram-scraper-2022.p.rapidapi.com',
        'Content-Type': 'application/json'
      },
      'payload': JSON.stringify({username: username})
    });
    
    const data = JSON.parse(response.getContentText());
    // API 응답 처리...
    */
    
    return {followers: 0, following: 0, posts: 0, success: false, error: 'API 키 필요'};
    
  } catch (error) {
    return {followers: 0, following: 0, posts: 0, success: false, error: `API 오류: ${error.toString()}`};
  }
}

/**
 * 현재 선택된 행의 인스타그램 정보 스크래핑
 */
function scrapeSingleRow() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const activeRange = sheet.getActiveRange();
  const row = activeRange.getRow();
  
  if (row === 1) {
    Browser.msgBox('오류', '헤더 행입니다. 데이터 행을 선택해주세요.', Browser.Buttons.OK);
    return;
  }
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rowData = data[row - 1];
  
  const instagramCol = headers.indexOf('인스타그램'); // D열
  const followersCol = headers.indexOf('팔로워');     // G열
  const followingCol = headers.indexOf('팔로잉');    // H열
  const postsCol = headers.indexOf('게시물');        // I열
  
  if (instagramCol === -1) {
    Browser.msgBox('오류', '인스타그램 컬럼을 찾을 수 없습니다.', Browser.Buttons.OK);
    return;
  }
  
  const instagramAccount = rowData[instagramCol];
  if (!instagramAccount) {
    Browser.msgBox('오류', '인스타그램 계정이 비어있습니다.', Browser.Buttons.OK);
    return;
  }
  
  const result = scrapeInstagramProfile(instagramAccount);
  
  if (result.success) {
    if (followersCol !== -1) sheet.getRange(row, followersCol + 1).setValue(result.followers);
    if (followingCol !== -1) sheet.getRange(row, followingCol + 1).setValue(result.following);
    if (postsCol !== -1) sheet.getRange(row, postsCol + 1).setValue(result.posts);
    
    Browser.msgBox(
      '스크래핑 완료', 
      `팔로워: ${result.followers}, 팔로잉: ${result.following}, 게시물: ${result.posts}`, 
      Browser.Buttons.OK
    );
  } else {
    Browser.msgBox('스크래핑 실패', result.error, Browser.Buttons.OK);
  }
}

/**
 * 수동 입력을 위한 헬퍼 함수
 */
function manualInputInstagramData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const activeRange = sheet.getActiveRange();
  const row = activeRange.getRow();
  
  if (row === 1) {
    Browser.msgBox('오류', '헤더 행입니다. 데이터 행을 선택해주세요.', Browser.Buttons.OK);
    return;
  }
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rowData = data[row - 1];
  
  const nameCol = headers.indexOf('이름');
  const followersCol = headers.indexOf('팔로워');  // G열
  const followingCol = headers.indexOf('팔로잉'); // H열
  const postsCol = headers.indexOf('게시물');     // I열
  
  const name = nameCol !== -1 ? rowData[nameCol] : `${row}행`;
  
  const followers = Browser.inputBox(
    '수동 입력', 
    `${name}의 팔로워 수를 입력하세요:`, 
    Browser.Buttons.OK_CANCEL
  );
  
  if (followers === 'cancel') return;
  
  const following = Browser.inputBox(
    '수동 입력', 
    `${name}의 팔로잉 수를 입력하세요:`, 
    Browser.Buttons.OK_CANCEL
  );
  
  if (following === 'cancel') return;
  
  const posts = Browser.inputBox(
    '수동 입력', 
    `${name}의 게시물 수를 입력하세요:`, 
    Browser.Buttons.OK_CANCEL
  );
  
  if (posts === 'cancel') return;
  
  // 시트 업데이트 (G, H, I 열)
  if (followersCol !== -1) sheet.getRange(row, followersCol + 1).setValue(parseInt(followers) || 0);
  if (followingCol !== -1) sheet.getRange(row, followingCol + 1).setValue(parseInt(following) || 0);
  if (postsCol !== -1) sheet.getRange(row, postsCol + 1).setValue(parseInt(posts) || 0);
  
  Browser.msgBox('완료', '데이터가 업데이트되었습니다.', Browser.Buttons.OK);
}

/**
 * 테스트 함수
 */
function testScraping() {
  const testUrl = 'https://www.instagram.com/test_account/';
  const result = scrapeInstagramProfile(testUrl);
  console.log('테스트 결과:', result);
} 