/**
 * Apps Script로 로컬 Instagram 스크래핑 서버 원격 제어
 * 
 * 사용법:
 * 1. 로컬에서 instagram_control_server.py 실행
 * 2. Google Sheets에서 이 코드 실행
 * 3. 🤖 메뉴로 원격 제어
 */

// 로컬 서버 설정
const LOCAL_SERVER_URL = 'http://localhost:5555';
const TIMEOUT_MS = 30000; // 30초 타임아웃

/**
 * 메뉴 생성 (Google Sheets 열 때 자동 실행)
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🤖 Instagram 원격 제어')
    .addItem('📡 서버 연결 확인', 'checkServerConnection')
    .addItem('📋 스크래핑 대상 확인', 'checkScrapingTargets')
    .addSeparator()
    .addItem('🚀 전체 스크래핑 시작', 'startRemoteScraping')
    .addItem('⏹️ 스크래핑 중단', 'stopRemoteScraping')
    .addItem('📊 스크래핑 상태 확인', 'checkScrapingStatus')
    .addSeparator()
    .addItem('🎯 선택된 행만 스크래핑', 'scrapeSelectedRows')
    .addItem('🌐 로컬 대시보드 열기', 'openLocalDashboard')
    .addSeparator()
    .addItem('ℹ️ 사용법 안내', 'showUsageGuide')
    .addToUi();
}

/**
 * HTTP 요청 헬퍼 함수
 */
function makeRequest(endpoint, method = 'GET', payload = null) {
  try {
    const url = `${LOCAL_SERVER_URL}${endpoint}`;
    const options = {
      'method': method,
      'headers': {
        'Content-Type': 'application/json'
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
    
    console.log(`응답: ${statusCode} - ${responseText}`);
    
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
  SpreadsheetApp.getActiveSpreadsheet().toast('로컬 서버 연결 확인 중...', '📡 연결 테스트', 3);
  
  const result = makeRequest('/status');
  
  if (result.success) {
    const status = result.data;
    const message = `✅ 로컬 서버 연결 성공!\n\n📊 현재 상태:\n• 실행 중: ${status.is_running ? '예' : '아니오'}\n• 마지막 업데이트: ${status.last_update || '없음'}\n\n🌐 대시보드: ${LOCAL_SERVER_URL}`;
    
    SpreadsheetApp.getUi().alert('📡 서버 연결 확인', message, SpreadsheetApp.getUi().ButtonSet.OK);
  } else {
    const errorMessage = `❌ 로컬 서버 연결 실패\n\n오류: ${result.error}\n\n💡 해결 방법:\n1. 로컬에서 instagram_control_server.py 실행 확인\n2. 서버 주소 확인: ${LOCAL_SERVER_URL}\n3. 방화벽 설정 확인`;
    
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
    
    let message = `📋 스크래핑 대상 조회 결과\n\n📊 총 ${data.empty_rows}개의 대상이 있습니다.\n\n`;
    
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
    `${targetCount}개의 Instagram 계정을 스크래핑합니다.\n예상 소요시간: ${Math.ceil(targetCount * 2.5)}초\n\n로컬 서버에서 실행되므로 안정적입니다.\n\n계속하시겠습니까?`,
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );
  
  if (response !== SpreadsheetApp.getUi().Button.YES) return;
  
  // 스크래핑 시작
  SpreadsheetApp.getActiveSpreadsheet().toast('로컬 서버로 스크래핑 명령 전송 중...', '🚀 스크래핑 시작', 5);
  
  const startResult = makeRequest('/start', 'POST');
  
  if (startResult.success) {
    SpreadsheetApp.getUi().alert(
      '🚀 스크래핑 시작됨',
      `✅ ${startResult.data.message}\n\n📊 진행 상황은 "📊 스크래핑 상태 확인"으로 모니터링하세요.\n🌐 실시간 대시보드: ${LOCAL_SERVER_URL}`,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    
    // 자동으로 상태 확인 창 열기
    setTimeout(() => {
      checkScrapingStatus();
    }, 2000);
    
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
      message += `🔄 실행 중\n`;
      message += `📈 진행률: ${status.progress}/${status.total} (${progress}%)\n`;
      message += `📱 현재 작업: ${status.current_item}\n`;
      message += `✅ 성공: ${status.success_count}개\n`;
      message += `❌ 실패: ${status.fail_count}개\n`;
      message += `⏰ 시작 시간: ${status.start_time}\n`;
      message += `🔄 마지막 업데이트: ${status.last_update}`;
    } else {
      message += `⏸️ 대기 중\n`;
      
      if (status.success_count > 0 || status.fail_count > 0) {
        message += `\n📊 최근 결과:\n`;
        message += `✅ 성공: ${status.success_count}개\n`;
        message += `❌ 실패: ${status.fail_count}개\n`;
        const total = status.success_count + status.fail_count;
        const successRate = total > 0 ? Math.round((status.success_count / total) * 100) : 0;
        message += `📈 성공률: ${successRate}%`;
      }
      
      if (status.error) {
        message += `\n❌ 오류: ${status.error}`;
      }
    }
    
    message += `\n\n🌐 실시간 대시보드: ${LOCAL_SERVER_URL}`;
    
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
    `선택된 ${selectedRows.length}개 행을 스크래핑합니다:\n\n${selectedRows.slice(0, 5).join(', ')}${selectedRows.length > 5 ? ` 외 ${selectedRows.length - 5}개` : ''}\n\n계속하시겠습니까?`,
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
 * 로컬 대시보드 열기 안내
 */
function openLocalDashboard() {
  const message = `🌐 로컬 대시보드\n\n브라우저에서 다음 주소를 열어주세요:\n\n${LOCAL_SERVER_URL}\n\n대시보드에서는 다음 기능을 사용할 수 있습니다:\n• 실시간 진행률 모니터링\n• 스크래핑 제어\n• 상세 로그 확인\n\n💡 로컬 서버가 실행 중이어야 합니다.`;
  
  SpreadsheetApp.getUi().alert('🌐 로컬 대시보드', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * 사용법 안내
 */
function showUsageGuide() {
  const guide = `📖 Instagram 원격 제어 사용법\n\n🔧 설정:\n1. 로컬에서 instagram_control_server.py 실행\n2. 서버 주소: ${LOCAL_SERVER_URL}\n\n🎮 사용법:\n1. "📡 서버 연결 확인"으로 연결 상태 확인\n2. "📋 스크래핑 대상 확인"으로 작업량 파악\n3. "🚀 전체 스크래핑 시작"으로 실행\n4. "📊 스크래핑 상태 확인"으로 진행 상황 모니터링\n\n🎯 고급 기능:\n• "🎯 선택된 행만 스크래핑": 특정 행만 처리\n• "🌐 로컬 대시보드": 실시간 웹 모니터링\n• "⏹️ 스크래핑 중단": 진행 중인 작업 중단\n\n✅ 장점:\n• 로컬의 안정적인 스크래핑 성능\n• 클라우드의 편리한 제어\n• 실시간 진행 상황 확인\n• 언제 어디서나 원격 제어`;
  
  SpreadsheetApp.getUi().alert('📖 사용법 안내', guide, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * 자동 상태 업데이트 (선택사항)
 */
function autoUpdateStatus() {
  // 트리거를 설정하여 주기적으로 상태를 확인할 수 있음
  // 실제 운영시에는 필요에 따라 활성화
  
  const result = makeRequest('/status');
  if (result.success && result.data.is_running) {
    const status = result.data;
    const progress = status.total > 0 ? Math.round((status.progress / status.total) * 100) : 0;
    
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `진행률: ${progress}% (${status.progress}/${status.total})`,
      '🔄 스크래핑 진행 중',
      3
    );
  }
} 