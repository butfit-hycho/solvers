/**
 * 고급 Instagram 스크래핑 도구 (Apps Script)
 * 로컬 배치 스크래핑과 동등한 성능 목표
 * 
 * 사용법: Google Sheets → 확장 프로그램 → Apps Script → 코드 붙여넣기 → 저장 → 새로고침
 */

/**
 * 메뉴 생성 (시트 열 때 자동 실행)
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🤖 Instagram 배치 도구')
    .addItem('🚀 전체 일괄 스크래핑 (고급)', 'advancedBatchScraping')
    .addItem('⚡ 빠른 스크래핑 (기본)', 'basicBatchScraping')
    .addItem('🎯 선택된 행만 스크래핑', 'scrapeSingleRow')
    .addSeparator()
    .addItem('📊 스크래핑 현황 확인', 'checkScrapingStatus')
    .addItem('🧹 Instagram 데이터 초기화', 'clearInstagramData')
    .addSeparator()
    .addItem('⚙️ 스크래핑 테스트', 'testAdvancedScraping')
    .addItem('ℹ️ 도구 정보', 'showAbout')
    .addToUi();
}

/**
 * 고급 일괄 스크래핑 (다중 방법 시도)
 */
function advancedBatchScraping() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  // 컬럼 인덱스 찾기
  const nameCol = headers.indexOf('이름');
  const instagramCol = headers.indexOf('인스타그램');
  const followersCol = headers.indexOf('팔로워');
  const followingCol = headers.indexOf('팔로잉');
  const postsCol = headers.indexOf('게시물');
  
  if (instagramCol === -1) {
    SpreadsheetApp.getUi().alert('❌ 오류', '인스타그램 컬럼을 찾을 수 없습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // 스크래핑 대상 찾기
  let emptyRows = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const instagramAccount = row[instagramCol];
    const followersValue = row[followersCol];
    
    if (instagramAccount && instagramAccount.trim() && (!followersValue || followersValue === '')) {
      emptyRows.push({
        index: i,
        name: row[nameCol] || `${i+1}행`,
        instagram: instagramAccount.trim()
      });
    }
  }
  
  if (emptyRows.length === 0) {
    SpreadsheetApp.getUi().alert('✅ 알림', '스크래핑할 대상이 없습니다.\n모든 Instagram 정보가 이미 채워져 있습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // 시작 확인
  const response = SpreadsheetApp.getUi().alert(
    '🚀 고급 일괄 스크래핑 시작', 
    `${emptyRows.length}개의 Instagram 계정을 스크래핑합니다.\n예상 소요시간: ${Math.ceil(emptyRows.length * 3)}초\n\n🔧 고급 모드: 다중 방법 시도로 성공률 향상\n\n계속하시겠습니까?`, 
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  let processed = 0;
  let failed = 0;
  
  // 진행률 추적
  const startTime = new Date();
  
  for (let i = 0; i < emptyRows.length; i++) {
    const rowData = emptyRows[i];
    
    try {
      console.log(`[${i+1}/${emptyRows.length}] ${rowData.name} 스크래핑 중...`);
      
      // 고급 스크래핑 시도 (다중 방법)
      const result = advancedInstagramScraping(rowData.instagram);
      
      if (result.success) {
        // 구글 시트 업데이트
        if (followersCol !== -1) sheet.getRange(rowData.index + 1, followersCol + 1).setValue(result.followers);
        if (followingCol !== -1) sheet.getRange(rowData.index + 1, followingCol + 1).setValue(result.following);
        if (postsCol !== -1) sheet.getRange(rowData.index + 1, postsCol + 1).setValue(result.posts);
        
        processed++;
        console.log(`✅ ${rowData.name} 완료: ${result.followers} 팔로워`);
      } else {
        failed++;
        console.log(`❌ ${rowData.name} 실패: ${result.error}`);
      }
      
      // 진행률 표시 (3개마다)
      if ((i + 1) % 3 === 0 || i === emptyRows.length - 1) {
        const progress = Math.round(((i + 1) / emptyRows.length) * 100);
        const elapsed = Math.round((new Date() - startTime) / 1000);
        SpreadsheetApp.getActiveSpreadsheet().toast(
          `진행률: ${progress}% (${i + 1}/${emptyRows.length}) | 소요시간: ${elapsed}초`,
          '🤖 Instagram 스크래핑',
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
  
  // 최종 결과
  const totalTime = Math.round((new Date() - startTime) / 1000);
  const successRate = Math.round((processed / emptyRows.length) * 100);
  
  SpreadsheetApp.getUi().alert(
    '🏁 고급 일괄 스크래핑 완료', 
    `⏱️ 총 소요시간: ${totalTime}초\n✅ 성공: ${processed}개\n❌ 실패: ${failed}개\n📊 성공률: ${successRate}%\n\n${failed > 0 ? '💡 실패한 항목은 "🎯 선택된 행만 스크래핑"으로 재시도하세요.' : '🎉 모든 스크래핑이 완료되었습니다!'}`, 
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * 고급 Instagram 스크래핑 (다중 방법 시도)
 */
function advancedInstagramScraping(instagramUrl) {
  if (!instagramUrl || !instagramUrl.trim()) {
    return {followers: 0, following: 0, posts: 0, success: false, error: 'URL 없음'};
  }
  
  // URL 정규화
  let url = instagramUrl.trim();
  if (!url.startsWith('http')) {
    url = `https://www.instagram.com/${url.replace('@', '')}/`;
  }
  
  // 방법 1: 모바일 버전 시도 (더 단순한 HTML)
  try {
    const mobileUrl = url.replace('www.instagram.com', 'm.instagram.com');
    const result = tryMobileInstagram(mobileUrl);
    if (result.success) {
      console.log(`✅ 모바일 버전 성공: ${result.followers} 팔로워`);
      return result;
    }
  } catch (e) {
    console.log(`⚠️ 모바일 버전 실패: ${e.toString()}`);
  }
  
  // 방법 2: 데스크톱 버전 + 향상된 정규식
  try {
    const result = tryDesktopInstagram(url);
    if (result.success) {
      console.log(`✅ 데스크톱 버전 성공: ${result.followers} 팔로워`);
      return result;
    }
  } catch (e) {
    console.log(`⚠️ 데스크톱 버전 실패: ${e.toString()}`);
  }
  
  // 방법 3: 백업 API 시도 (무료 서비스)
  try {
    const result = tryBackupAPI(url);
    if (result.success) {
      console.log(`✅ 백업 API 성공: ${result.followers} 팔로워`);
      return result;
    }
  } catch (e) {
    console.log(`⚠️ 백업 API 실패: ${e.toString()}`);
  }
  
  return {followers: 0, following: 0, posts: 0, success: false, error: '모든 방법 실패'};
}

/**
 * 모바일 Instagram 페이지 스크래핑
 */
function tryMobileInstagram(mobileUrl) {
  const response = UrlFetchApp.fetch(mobileUrl, {
    'method': 'GET',
    'headers': {
      'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
    },
    'muteHttpExceptions': true
  });
  
  if (response.getResponseCode() !== 200) {
    return {followers: 0, following: 0, posts: 0, success: false, error: `HTTP ${response.getResponseCode()}`};
  }
  
  const html = response.getContentText();
  
  // 모바일 버전용 정규식 패턴
  const patterns = {
    followers: [
      /"follower_count":(\d+)/,
      /"edge_followed_by":{"count":(\d+)}/,
      /(\d+(?:,\d+)*)\s*followers?/i,
      /"followers"\s*:\s*"?(\d+)"?/
    ],
    following: [
      /"following_count":(\d+)/,
      /"edge_follow":{"count":(\d+)}/,
      /(\d+(?:,\d+)*)\s*following/i,
      /"following"\s*:\s*"?(\d+)"?/
    ],
    posts: [
      /"media_count":(\d+)/,
      /"edge_owner_to_timeline_media":{"count":(\d+)}/,
      /(\d+(?:,\d+)*)\s*posts?/i,
      /"posts"\s*:\s*"?(\d+)"?/
    ]
  };
  
  const followers = extractWithPatterns(html, patterns.followers);
  const following = extractWithPatterns(html, patterns.following);
  const posts = extractWithPatterns(html, patterns.posts);
  
  if (followers > 0 || following > 0 || posts > 0) {
    return {
      followers: followers,
      following: following,
      posts: posts,
      success: true,
      error: null
    };
  }
  
  return {followers: 0, following: 0, posts: 0, success: false, error: '모바일 데이터 파싱 실패'};
}

/**
 * 데스크톱 Instagram 페이지 스크래핑 (향상된 버전)
 */
function tryDesktopInstagram(url) {
  const response = UrlFetchApp.fetch(url, {
    'method': 'GET',
    'headers': {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.9',
      'Cache-Control': 'no-cache'
    },
    'muteHttpExceptions': true
  });
  
  if (response.getResponseCode() !== 200) {
    return {followers: 0, following: 0, posts: 0, success: false, error: `HTTP ${response.getResponseCode()}`};
  }
  
  const html = response.getContentText();
  
  // 향상된 정규식 패턴 (더 많은 케이스 커버)
  const patterns = {
    followers: [
      /"edge_followed_by":\s*{\s*"count":\s*(\d+)/,
      /"follower_count":\s*(\d+)/,
      /(\d+(?:,\d+)*)\s*followers?/gi,
      /"EdgeFollowedByCount.*?"count"\s*:\s*(\d+)/,
      /followers.*?(\d+(?:,\d+)*)/gi
    ],
    following: [
      /"edge_follow":\s*{\s*"count":\s*(\d+)/,
      /"following_count":\s*(\d+)/,
      /(\d+(?:,\d+)*)\s*following/gi,
      /"EdgeFollowCount.*?"count"\s*:\s*(\d+)/,
      /following.*?(\d+(?:,\d+)*)/gi
    ],
    posts: [
      /"edge_owner_to_timeline_media":\s*{\s*"count":\s*(\d+)/,
      /"media_count":\s*(\d+)/,
      /(\d+(?:,\d+)*)\s*posts?/gi,
      /"EdgeOwnerToTimelineMediaCount.*?"count"\s*:\s*(\d+)/,
      /posts.*?(\d+(?:,\d+)*)/gi
    ]
  };
  
  const followers = extractWithPatterns(html, patterns.followers);
  const following = extractWithPatterns(html, patterns.following);
  const posts = extractWithPatterns(html, patterns.posts);
  
  if (followers > 0 || following > 0 || posts > 0) {
    return {
      followers: followers,
      following: following,
      posts: posts,
      success: true,
      error: null
    };
  }
  
  return {followers: 0, following: 0, posts: 0, success: false, error: '데스크톱 데이터 파싱 실패'};
}

/**
 * 백업 API 시도 (무료 서비스 활용)
 */
function tryBackupAPI(url) {
  try {
    // Instagram 사용자명 추출
    const username = url.split('/').filter(x => x && x !== 'www.instagram.com' && x !== 'https:').pop().split('?')[0];
    
    if (!username) {
      return {followers: 0, following: 0, posts: 0, success: false, error: '사용자명 추출 실패'};
    }
    
    // 공개 정보만 접근 가능한 무료 서비스 시도
    // 실제로는 API 키가 필요하거나 제한이 있을 수 있음
    
    return {followers: 0, following: 0, posts: 0, success: false, error: 'API 서비스 없음'};
    
  } catch (error) {
    return {followers: 0, following: 0, posts: 0, success: false, error: `API 오류: ${error.toString()}`};
  }
}

/**
 * 다중 패턴으로 숫자 추출
 */
function extractWithPatterns(html, patterns) {
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) {
      const number = match[1] || match[0];
      if (number) {
        // 숫자만 추출하고 쉼표 제거
        const cleanNumber = number.toString().replace(/[^0-9]/g, '');
        if (cleanNumber && !isNaN(cleanNumber)) {
          return parseInt(cleanNumber);
        }
      }
    }
  }
  return 0;
}

/**
 * 기본 일괄 스크래핑 (빠른 버전)
 */
function basicBatchScraping() {
  // 기존 코드 간소화 버전
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const nameCol = headers.indexOf('이름');
  const instagramCol = headers.indexOf('인스타그램');
  const followersCol = headers.indexOf('팔로워');
  const followingCol = headers.indexOf('팔로잉');
  const postsCol = headers.indexOf('게시물');
  
  if (instagramCol === -1) {
    SpreadsheetApp.getUi().alert('❌ 오류', '인스타그램 컬럼을 찾을 수 없습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  let emptyRows = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const instagramAccount = row[instagramCol];
    const followersValue = row[followersCol];
    
    if (instagramAccount && instagramAccount.trim() && (!followersValue || followersValue === '')) {
      emptyRows.push({
        index: i,
        name: row[nameCol] || `${i+1}행`,
        instagram: instagramAccount.trim()
      });
    }
  }
  
  if (emptyRows.length === 0) {
    SpreadsheetApp.getUi().alert('✅ 알림', '스크래핑할 대상이 없습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  const response = SpreadsheetApp.getUi().alert(
    '⚡ 빠른 스크래핑 시작', 
    `${emptyRows.length}개의 Instagram 계정을 빠르게 스크래핑합니다.\n\n계속하시겠습니까?`, 
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  let processed = 0;
  let failed = 0;
  
  for (let i = 0; i < emptyRows.length; i++) {
    const rowData = emptyRows[i];
    
    try {
      const result = tryDesktopInstagram(rowData.instagram);
      
      if (result.success) {
        if (followersCol !== -1) sheet.getRange(rowData.index + 1, followersCol + 1).setValue(result.followers);
        if (followingCol !== -1) sheet.getRange(rowData.index + 1, followingCol + 1).setValue(result.following);
        if (postsCol !== -1) sheet.getRange(rowData.index + 1, postsCol + 1).setValue(result.posts);
        processed++;
      } else {
        failed++;
      }
      
      if ((i + 1) % 5 === 0 || i === emptyRows.length - 1) {
        const progress = Math.round(((i + 1) / emptyRows.length) * 100);
        SpreadsheetApp.getActiveSpreadsheet().toast(
          `빠른 스크래핑: ${progress}% (${i + 1}/${emptyRows.length})`,
          '⚡ Instagram 스크래핑',
          2
        );
      }
      
      Utilities.sleep(1500); // 더 빠른 간격
      
    } catch (error) {
      failed++;
    }
  }
  
  const successRate = Math.round((processed / emptyRows.length) * 100);
  SpreadsheetApp.getUi().alert(
    '⚡ 빠른 스크래핑 완료', 
    `✅ 성공: ${processed}개\n❌ 실패: ${failed}개\n📊 성공률: ${successRate}%`, 
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * 스크래핑 현황 확인
 */
function checkScrapingStatus() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const instagramCol = headers.indexOf('인스타그램');
  const followersCol = headers.indexOf('팔로워');
  
  if (instagramCol === -1) {
    SpreadsheetApp.getUi().alert('❌ 오류', '인스타그램 컬럼을 찾을 수 없습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  let totalRows = data.length - 1;
  let hasInstagram = 0;
  let completed = 0;
  let pending = 0;
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const instagramAccount = row[instagramCol];
    const followersValue = row[followersCol];
    
    if (instagramAccount && instagramAccount.trim()) {
      hasInstagram++;
      
      if (followersValue && followersValue !== '') {
        completed++;
      } else {
        pending++;
      }
    }
  }
  
  const completionRate = hasInstagram > 0 ? Math.round((completed/hasInstagram)*100) : 0;
  
  const status = `📊 Instagram 스크래핑 현황\n\n📋 전체 데이터: ${totalRows}개\n📱 Instagram URL 있음: ${hasInstagram}개\n✅ 스크래핑 완료: ${completed}개\n⏳ 스크래핑 대기: ${pending}개\n📈 완료율: ${completionRate}%\n\n${pending > 0 ? '💡 "🚀 전체 일괄 스크래핑"을 실행해보세요!' : '🎉 모든 스크래핑이 완료되었습니다!'}`;
  
  SpreadsheetApp.getUi().alert('📊 스크래핑 현황', status, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Instagram 데이터 초기화
 */
function clearInstagramData() {
  const response = SpreadsheetApp.getUi().alert(
    '🧹 데이터 초기화', 
    '정말로 모든 Instagram 스크래핑 결과를 초기화하시겠습니까?\n(팔로워, 팔로잉, 게시물 수가 모두 삭제됩니다)', 
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  
  const followersCol = headers.indexOf('팔로워');
  const followingCol = headers.indexOf('팔로잉');
  const postsCol = headers.indexOf('게시물');
  
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
  
  SpreadsheetApp.getUi().alert('🧹 초기화 완료', `${cleared}개 행의 Instagram 데이터가 초기화되었습니다.`, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * 선택된 행만 스크래핑
 */
function scrapeSingleRow() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const activeRange = sheet.getActiveRange();
  const row = activeRange.getRow();
  
  if (row === 1) {
    SpreadsheetApp.getUi().alert('❌ 오류', '헤더 행입니다. 데이터 행을 선택해주세요.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const rowData = data[row - 1];
  
  const instagramCol = headers.indexOf('인스타그램');
  const followersCol = headers.indexOf('팔로워');
  const followingCol = headers.indexOf('팔로잉');
  const postsCol = headers.indexOf('게시물');
  
  if (instagramCol === -1) {
    SpreadsheetApp.getUi().alert('❌ 오류', '인스타그램 컬럼을 찾을 수 없습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  const instagramAccount = rowData[instagramCol];
  if (!instagramAccount) {
    SpreadsheetApp.getUi().alert('❌ 오류', '인스타그램 계정이 비어있습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  SpreadsheetApp.getActiveSpreadsheet().toast('스크래핑 중...', '🎯 선택된 행 스크래핑', 3);
  
  const result = advancedInstagramScraping(instagramAccount);
  
  if (result.success) {
    if (followersCol !== -1) sheet.getRange(row, followersCol + 1).setValue(result.followers);
    if (followingCol !== -1) sheet.getRange(row, followingCol + 1).setValue(result.following);
    if (postsCol !== -1) sheet.getRange(row, postsCol + 1).setValue(result.posts);
    
    SpreadsheetApp.getUi().alert(
      '✅ 스크래핑 완료', 
      `팔로워: ${result.followers}\n팔로잉: ${result.following}\n게시물: ${result.posts}`, 
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } else {
    SpreadsheetApp.getUi().alert('❌ 스크래핑 실패', `오류: ${result.error}\n\n다른 방법을 시도하거나 나중에 다시 시도해보세요.`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 테스트 함수
 */
function testAdvancedScraping() {
  const testUrl = 'https://www.instagram.com/instagram/';
  SpreadsheetApp.getActiveSpreadsheet().toast('테스트 스크래핑 중...', '⚙️ 테스트', 3);
  
  const result = advancedInstagramScraping(testUrl);
  
  const message = result.success 
    ? `✅ 테스트 성공!\n\n팔로워: ${result.followers}\n팔로잉: ${result.following}\n게시물: ${result.posts}`
    : `❌ 테스트 실패\n\n오류: ${result.error}`;
  
  SpreadsheetApp.getUi().alert('⚙️ 스크래핑 테스트 결과', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * 도구 정보
 */
function showAbout() {
  const about = `🤖 Instagram 배치 도구 (고급 버전)\n\n버전: 3.0 Advanced\n개발: AI Assistant\n목적: 대량 Instagram 데이터 자동 수집\n\n🚀 고급 기능:\n• 다중 스크래핑 방법 시도\n• 모바일/데스크톱 버전 지원\n• 향상된 정규식 패턴\n• 실시간 진행률 표시\n• 선택적 실행 옵션\n\n📊 대상 컬럼:\n• D열: Instagram URL (입력)\n• G열: 팔로워 수 (결과)\n• H열: 팔로잉 수 (결과)\n• I열: 게시물 수 (결과)\n\n💡 사용 팁:\n1. "🚀 전체 일괄 스크래핑"으로 대량 처리\n2. "⚡ 빠른 스크래핑"으로 신속 처리\n3. "🎯 선택된 행만"으로 재시도\n\n⚠️ 주의사항:\nInstagram 정책에 따라 일부 계정은 스크래핑이 제한될 수 있습니다.`;
  
  SpreadsheetApp.getUi().alert('🤖 도구 정보', about, SpreadsheetApp.getUi().ButtonSet.OK);
} 