/**
 * Apps Script로 로컬 Instagram 스크래핑 서버 원격 제어 (LocalTunnel 버전)
 * 
 * 🔧 설정 방법:
 * 1. 로컬에서 instagram_control_server.py 실행
 * 2. 새 터미널에서 "lt --port 5555 --subdomain butfit-instagram-scraper" 실행  
 * 3. 생성된 URL: https://butfit-instagram-scraper.loca.lt
 * 4. Google Sheets에서 이 코드 실행 - 바로 작동!
 */

// ✅ LocalTunnel URL 설정 완료!
const NGROK_URL = 'https://butfit-instagram-scraper.loca.lt';  // 🟢 LocalTunnel URL
const TIMEOUT_MS = 30000; // 30초 타임아웃

/**
 * 메뉴 생성 (Google Sheets 열 때 자동 실행)
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🌐 Instagram 원격 제어 (LocalTunnel)')
    .addItem('🔗 LocalTunnel 상태 확인', 'showTunnelStatus')
    .addSeparator()
    .addItem('📡 서버 연결 확인', 'checkServerConnection')
    .addItem('📋 스크래핑 대상 확인', 'checkScrapingTargets')
    .addSeparator()
    .addItem('🚀 전체 스크래핑 시작', 'startRemoteScraping')
    .addItem('⏹️ 스크래핑 중단', 'stopRemoteScraping')
    .addItem('📊 스크래핑 상태 확인', 'checkScrapingStatus')
    .addSeparator()
    .addItem('🎯 선택된 행만 스크래핑', 'scrapeSelectedRows')
    .addItem('ℹ️ 사용법 안내', 'showUsageGuide')
    .addToUi();
}

/**
 * LocalTunnel 상태 확인
 */
function showTunnelStatus() {
  const setup = `🔗 LocalTunnel 상태 확인

📋 현재 설정: ✅ ${NGROK_URL}

🛠️ 실행 방법:
1. 터미널에서 "instagram_control_server.py" 실행
2. 새 터미널에서 "lt --port 5555 --subdomain butfit-instagram-scraper" 실행
3. 생성된 URL: ${NGROK_URL}
4. 바로 사용 가능! (설정 변경 불필요)

✅ 장점:
• 고정 URL: 매번 같은 주소 사용
• 토큰 불필요: 바로 실행 가능
• 무료 사용: 별도 인증 없음
• 안정적 연결: 지속적 터널링

💡 LocalTunnel 명령어:
lt --port 5555 --subdomain butfit-instagram-scraper

🌐 생성된 URL: ${NGROK_URL}`;

  SpreadsheetApp.getUi().alert('🔗 LocalTunnel 상태', setup, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * HTTP 요청 헬퍼 함수 (ngrok 최적화)
 */
function makeRequest(endpoint, method = 'GET', payload = null) {
  // URL 유효성 검사 (LocalTunnel은 이미 설정됨)
  if (!NGROK_URL || NGROK_URL === 'https://YOUR_NGROK_URL_HERE') {
    return {
      success: false,
      error: 'LocalTunnel URL 설정 오류. "🔗 LocalTunnel 상태 확인"을 참조하세요.',
      statusCode: 0
    };
  }
  
  try {
    const url = `${NGROK_URL}${endpoint}`;
          const options = {
        'method': method,
        'headers': {
          'Content-Type': 'application/json',
          'Bypass-Tunnel-Reminder': 'true'  // LocalTunnel 경고 스킵
        },
        'muteHttpExceptions': true
      };
    
    if (payload) {
      options.payload = JSON.stringify(payload);
    }
    
    console.log(`요청: ${method} ${url}`);
    
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    console.log(`응답: ${statusCode} - ${responseText.substring(0, 200)}`);
    
    if (statusCode >= 200 && statusCode < 300) {
      return {
        success: true,
        data: JSON.parse(responseText),
        statusCode: statusCode
      };
    } else {
      return {
        success: false,
        error: `HTTP ${statusCode}: ${responseText}`,
        statusCode: statusCode
      };
    }
    
  } catch (error) {
    return {
      success: false,
      error: `연결 오류: ${error.toString()}`,
      statusCode: 0
    };
  }
}

/**
 * 서버 연결 확인
 */
function checkServerConnection() {
  SpreadsheetApp.getActiveSpreadsheet().toast('LocalTunnel 서버 연결 확인 중...', '📡 연결 테스트', 3);
  
  const result = makeRequest('/status');
  
  if (result.success) {
    const status = result.data;
    const message = `✅ LocalTunnel 서버 연결 성공!

📊 현재 상태:
• 실행 중: ${status.is_running ? '예' : '아니오'}
• 마지막 업데이트: ${status.last_update || '없음'}

🌐 LocalTunnel URL: ${NGROK_URL}
🎯 로컬 서버: http://localhost:5555`;
    
    SpreadsheetApp.getUi().alert('📡 서버 연결 확인', message, SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    const errorMessage = `❌ LocalTunnel 서버 연결 실패

오류: ${result.error}

💡 해결 방법:
1. LocalTunnel 실행 확인: "lt --port 5555 --subdomain butfit-instagram-scraper"
2. 로컬 서버 실행 확인: instagram_control_server.py
3. "🔗 LocalTunnel 상태 확인" 메뉴 참조
4. 인터넷 연결 상태 확인

🌐 URL: ${NGROK_URL}`;
    
    SpreadsheetApp.getUi().alert('❌ 연결 오류', errorMessage, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 스크래핑 대상 확인
 */
function checkScrapingTargets() {
  SpreadsheetApp.getActiveSpreadsheet().toast('스크래핑 대상 확인 중...', '📋 대상 조회', 3);
  
  const result = makeRequest('/check');
  
  if (result.success) {
    const data = result.data;
    
    if (data.error) {
      SpreadsheetApp.getUi().alert('❌ 조회 오류', `오류: ${data.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
      return;
    }
    
    let message = `📋 스크래핑 대상 조회 결과

📊 총 ${data.empty_rows}개의 대상이 있습니다.

`;
    
    if (data.rows && data.rows.length > 0) {
      message += '🔍 대상 미리보기 (최대 10개):\n';
      data.rows.forEach((row, index) => {
        message += `${index + 1}. ${row.name} - ${row.instagram_url}\n`;
      });
      
      if (data.empty_rows > 10) {
        message += `\n... 외 ${data.empty_rows - 10}개 더`;
      }
    } else {
      message += '🎉 모든 Instagram 정보가 이미 완료되었습니다!';
    }
    
    SpreadsheetApp.getUi().alert('📋 스크래핑 대상', message, SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    SpreadsheetApp.getUi().alert('❌ 조회 실패', `오류: ${result.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 전체 스크래핑 시작
 */
function startRemoteScraping() {
  // 먼저 대상 확인
  const checkResult = makeRequest('/check');
  
  if (!checkResult.success) {
    SpreadsheetApp.getUi().alert('❌ 오류', `서버 연결 실패: ${checkResult.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  const targetCount = checkResult.data.empty_rows || 0;
  
  if (targetCount === 0) {
    SpreadsheetApp.getUi().alert('✅ 알림', '스크래핑할 대상이 없습니다.\n모든 Instagram 정보가 이미 완료되었습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // 시작 확인
  const response = SpreadsheetApp.getUi().alert(
    '🚀 원격 스크래핑 시작',
    `${targetCount}개의 Instagram 계정을 스크래핑합니다.
예상 소요시간: ${Math.ceil(targetCount * 2.5)}초

🌐 LocalTunnel을 통해 로컬 서버에서 안정적으로 실행됩니다.

계속하시겠습니까?`,
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  // 스크래핑 시작
  SpreadsheetApp.getActiveSpreadsheet().toast('LocalTunnel로 스크래핑 명령 전송 중...', '🚀 스크래핑 시작', 5);
  
  const startResult = makeRequest('/start', 'POST');
  
  if (startResult.success) {
          SpreadsheetApp.getUi().alert(
        '🚀 스크래핑 시작됨',
        `✅ ${startResult.data.message}

📊 진행 상황은 "📊 스크래핑 상태 확인"으로 모니터링하세요.
🌐 LocalTunnel URL: ${NGROK_URL}`,
        SpreadsheetApp.getUi().ButtonSet.OK
      );
    
  } else {
    SpreadsheetApp.getUi().alert('❌ 시작 실패', `오류: ${startResult.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 스크래핑 중단
 */
function stopRemoteScraping() {
  const response = SpreadsheetApp.getUi().alert(
    '⏹️ 스크래핑 중단',
    '정말로 진행 중인 스크래핑을 중단하시겠습니까?',
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  SpreadsheetApp.getActiveSpreadsheet().toast('스크래핑 중단 명령 전송 중...', '⏹️ 중단', 3);
  
  const result = makeRequest('/stop', 'POST');
  
  if (result.success) {
    SpreadsheetApp.getUi().alert('⏹️ 중단 완료', result.data.message, SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    SpreadsheetApp.getUi().alert('❌ 중단 실패', `오류: ${result.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 스크래핑 상태 확인
 */
function checkScrapingStatus() {
  SpreadsheetApp.getActiveSpreadsheet().toast('스크래핑 상태 확인 중...', '📊 상태 조회', 3);
  
  const result = makeRequest('/status');
  
  if (result.success) {
    const status = result.data;
    
    let message = '📊 스크래핑 상태\n\n';
    
    if (status.is_running) {
      const progress = status.total > 0 ? Math.round((status.progress / status.total) * 100) : 0;
      message += `🔄 실행 중
📈 진행률: ${status.progress}/${status.total} (${progress}%)
📱 현재 작업: ${status.current_item}
✅ 성공: ${status.success_count}개
❌ 실패: ${status.fail_count}개
⏰ 시작 시간: ${status.start_time}
🔄 마지막 업데이트: ${status.last_update}`;
    } else {
      message += `⏸️ 대기 중`;
      
      if (status.success_count > 0 || status.fail_count > 0) {
        message += `

📊 최근 결과:
✅ 성공: ${status.success_count}개
❌ 실패: ${status.fail_count}개`;
        const total = status.success_count + status.fail_count;
        const successRate = total > 0 ? Math.round((status.success_count / total) * 100) : 0;
        message += `
📈 성공률: ${successRate}%`;
      }
      
      if (status.error) {
        message += `
❌ 오류: ${status.error}`;
      }
    }
    
    message += `

🌐 LocalTunnel URL: ${NGROK_URL}`;
    
    SpreadsheetApp.getUi().alert('📊 스크래핑 상태', message, SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    SpreadsheetApp.getUi().alert('❌ 상태 조회 실패', `오류: ${result.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 선택된 행만 스크래핑
 */
function scrapeSelectedRows() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const activeRange = sheet.getActiveRange();
  const selectedRows = [];
  
  // 선택된 범위에서 이름 추출
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const nameCol = headers.indexOf('이름');
  
  if (nameCol === -1) {
    SpreadsheetApp.getUi().alert('❌ 오류', '이름 컬럼을 찾을 수 없습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  const startRow = activeRange.getRow();
  const numRows = activeRange.getNumRows();
  
  for (let i = 0; i < numRows; i++) {
    const rowIndex = startRow + i - 1;
    if (rowIndex > 0 && rowIndex < data.length) { // 헤더 제외
      const rowData = data[rowIndex];
      const name = rowData[nameCol];
      if (name && name.trim()) {
        selectedRows.push(name.trim());
      }
    }
  }
  
  if (selectedRows.length === 0) {
    SpreadsheetApp.getUi().alert('❌ 오류', '선택된 행에서 유효한 이름을 찾을 수 없습니다.\n이름이 있는 행을 선택해주세요.', SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  // 확인
  const response = SpreadsheetApp.getUi().alert(
    '🎯 선택된 행 스크래핑',
    `선택된 ${selectedRows.length}개 행을 스크래핑합니다:

${selectedRows.slice(0, 5).join(', ')}${selectedRows.length > 5 ? ` 외 ${selectedRows.length - 5}개` : ''}

계속하시겠습니까?`,
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  // 특정 행 스크래핑 요청
  SpreadsheetApp.getActiveSpreadsheet().toast('선택된 행 스크래핑 시작...', '🎯 선택 스크래핑', 5);
  
  const result = makeRequest('/scrape_specific', 'POST', {
    target_rows: selectedRows
  });
  
  if (result.success) {
    SpreadsheetApp.getUi().alert('🎯 스크래핑 시작', result.data.message, SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    SpreadsheetApp.getUi().alert('❌ 스크래핑 실패', `오류: ${result.error}`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * 사용법 안내
 */
function showUsageGuide() {
  const guide = `📖 Instagram 원격 제어 사용법 (LocalTunnel 버전)

🔧 초기 설정:
1. 로컬에서 instagram_control_server.py 실행
2. 새 터미널에서 "lt --port 5555 --subdomain butfit-instagram-scraper" 실행
3. 생성된 URL: ${NGROK_URL} (이미 설정됨)
4. Google Sheets에서 바로 사용!

🎮 사용법:
1. "📡 서버 연결 확인"으로 LocalTunnel 연결 상태 확인
2. "📋 스크래핑 대상 확인"으로 작업량 파악
3. "🚀 전체 스크래핑 시작"으로 실행
4. "📊 스크래핑 상태 확인"으로 진행 상황 모니터링

🎯 고급 기능:
• "🎯 선택된 행만 스크래핑": 특정 행만 처리
• "⏹️ 스크래핑 중단": 진행 중인 작업 중단

✅ 장점:
• 고정 URL: 매번 같은 주소 사용
• 토큰 불필요: 바로 실행 가능
• 무료 사용: 별도 인증 없음
• 로컬의 안정적인 스크래핑 성능 (90%+ 성공률)
• 클라우드의 편리한 제어
• 실시간 진행 상황 확인
• 언제 어디서나 원격 제어

🌐 현재 LocalTunnel URL: ${NGROK_URL}`;
  
  SpreadsheetApp.getUi().alert('📖 사용법 안내', guide, SpreadsheetApp.getUi().ButtonSet.OK);
} 