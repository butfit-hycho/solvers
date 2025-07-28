#!/usr/bin/env python3
"""
Instagram 스크래핑 원격 제어 서버
Apps Script에서 HTTP 요청으로 로컬 스크래핑을 제어할 수 있음

사용법: python3 instagram_control_server.py
접속: http://localhost:5555
"""

import os
import sys
import json
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import gspread

# 현재 스크립트의 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from batch_instagram_scraper import LocalInstagramScraper

app = Flask(__name__)
CORS(app)  # Apps Script에서 접근 가능하도록

# 전역 변수
scraping_status = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "current_item": "",
    "success_count": 0,
    "fail_count": 0,
    "start_time": None,
    "last_update": None
}

class InstagramControlServer:
    def __init__(self):
        self.scraper = None
        
    def get_empty_rows(self):
        """스크래핑이 필요한 행들 조회"""
        try:
            scraper = LocalInstagramScraper()
            if not scraper.connect_google_sheet():
                return {"error": "Google Sheets 연결 실패"}
            
            empty_rows = scraper.find_empty_instagram_rows()
            return {
                "success": True,
                "empty_rows": len(empty_rows),
                "rows": [{"name": row["name"], "instagram_url": row["instagram_url"]} for row in empty_rows[:10]]  # 최대 10개만 미리보기
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run_scraping(self, target_rows=None):
        """백그라운드에서 스크래핑 실행 (스레드 안전성 개선)"""
        global scraping_status
        
        try:
            scraping_status.update({
                "is_running": True,
                "progress": 0,
                "success_count": 0,
                "fail_count": 0,
                "start_time": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat(),
                "error": None
            })
            
            # 각 스레드에서 새로운 스크래퍼 인스턴스 생성
            scraper = LocalInstagramScraper()
            
            # Google Sheets 연결
            if not scraper.connect_google_sheet():
                scraping_status["is_running"] = False
                scraping_status["error"] = "Google Sheets 연결 실패"
                return
            
            # Selenium 설정 (백업용) - 스레드 안전성 개선
            try:
                selenium_ready = scraper.setup_selenium()
                if not selenium_ready:
                    print("⚠️  Selenium 설정 실패 - requests 방법만 사용")
            except Exception as selenium_error:
                print(f"⚠️  Selenium 초기화 오류: {selenium_error}")
                selenium_ready = False
            
            # 스크래핑 대상 찾기
            empty_rows = scraper.find_empty_instagram_rows()
            
            if target_rows:
                # 특정 행만 처리
                empty_rows = [row for row in empty_rows if row["name"] in target_rows]
            
            scraping_status["total"] = len(empty_rows)
            
            if not empty_rows:
                scraping_status["is_running"] = False
                scraping_status["error"] = "스크래핑할 대상이 없습니다"
                return
            
            batch_updates = []
            
            # 각 행 처리
            for i, row_data in enumerate(empty_rows):
                if not scraping_status["is_running"]:  # 중단 요청 시
                    break
                
                scraping_status.update({
                    "progress": i + 1,
                    "current_item": f"{row_data['name']} ({row_data['instagram_url']})",
                    "last_update": datetime.now().isoformat()
                })
                
                # Instagram 스크래핑 (최적화된 버전)
                result = scraper.scrape_instagram_profile(row_data['instagram_url'])
                
                if result['success']:
                    # 배치 업데이트용 데이터 준비
                    batch_updates.append({
                        'row_num': row_data['row_num'],
                        'data': result
                    })
                    scraping_status["success_count"] += 1
                else:
                    scraping_status["fail_count"] += 1
                
                # 5개씩 모이거나 마지막이면 배치 업데이트
                if len(batch_updates) >= 5 or i == len(empty_rows) - 1:
                    if batch_updates:
                        if scraper.update_instagram_data_batch(batch_updates):
                            print(f"📊 {len(batch_updates)}개 배치 업데이트 완료")
                        else:
                            print(f"⚠️ 배치 업데이트 실패 - 개별 업데이트로 fallback")
                        batch_updates = []
                
                # 요청 간격 단축 (2초 → 0.5초)
                if i < len(empty_rows) - 1:
                    time.sleep(0.5)
            
            # 완료
            scraping_status.update({
                "is_running": False,
                "current_item": "완료",
                "last_update": datetime.now().isoformat()
            })
            
            # Chrome 드라이버 종료
            if hasattr(scraper, 'driver') and scraper.driver:
                try:
                    scraper.driver.quit()
                    print("🔚 Chrome WebDriver 종료")
                except:
                    pass
                
        except Exception as e:
            scraping_status.update({
                "is_running": False,
                "error": f"스크래핑 오류: {str(e)} (타입: {type(e).__name__})",
                "last_update": datetime.now().isoformat()
            })
            print(f"❌ 스크래핑 오류: {e}")
            print(f"오류 타입: {type(e).__name__}")
            
            # WebDriver 정리
            try:
                if hasattr(scraper, 'driver') and scraper.driver:
                    scraper.driver.quit()
                    print("🔚 예외 상황에서 Chrome WebDriver 종료")
            except:
                pass

# 전역 서버 인스턴스
control_server = InstagramControlServer()

@app.route('/')
def home():
    """웹 대시보드"""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Instagram 스크래핑 제어 서버</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
            .running { background-color: #e3f2fd; border: 1px solid #2196f3; }
            .stopped { background-color: #f3e5f5; border: 1px solid #9c27b0; }
            .error { background-color: #ffebee; border: 1px solid #f44336; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
            .start-btn { background-color: #4caf50; color: white; }
            .stop-btn { background-color: #f44336; color: white; }
            .check-btn { background-color: #2196f3; color: white; }
            pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🤖 Instagram 스크래핑 제어 서버</h1>
        
        <div id="status-panel">
            <h3>📊 현재 상태</h3>
            <div id="status" class="status stopped">서버 대기 중...</div>
        </div>
        
        <div>
            <h3>🎮 제어 패널</h3>
            <button class="check-btn" onclick="checkEmpty()">📋 스크래핑 대상 확인</button>
            <button class="start-btn" onclick="startScraping()">🚀 전체 스크래핑 시작</button>
            <button class="stop-btn" onclick="stopScraping()">⏹️ 스크래핑 중단</button>
        </div>
        
        <div>
            <h3>📈 결과</h3>
            <pre id="result">대기 중...</pre>
        </div>
        
        <div>
            <h3>🔗 API 엔드포인트</h3>
            <ul>
                <li><strong>GET /status</strong> - 현재 상태 조회</li>
                <li><strong>GET /check</strong> - 스크래핑 대상 확인</li>
                <li><strong>POST /start</strong> - 스크래핑 시작</li>
                <li><strong>POST /stop</strong> - 스크래핑 중단</li>
            </ul>
        </div>
        
        <script>
            function updateStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusDiv = document.getElementById('status');
                        const resultPre = document.getElementById('result');
                        
                        if (data.is_running) {
                            statusDiv.className = 'status running';
                            statusDiv.innerHTML = `
                                🔄 스크래핑 실행 중...<br>
                                📊 진행률: ${data.progress}/${data.total} (${Math.round(data.progress/data.total*100)}%)<br>
                                📱 현재: ${data.current_item}<br>
                                ✅ 성공: ${data.success_count}개 | ❌ 실패: ${data.fail_count}개
                            `;
                        } else {
                            statusDiv.className = 'status stopped';
                            statusDiv.innerHTML = '⏸️ 대기 중';
                        }
                        
                        if (data.error) {
                            statusDiv.className = 'status error';
                            statusDiv.innerHTML = '❌ 오류: ' + data.error;
                        }
                        
                        resultPre.textContent = JSON.stringify(data, null, 2);
                    })
                    .catch(error => {
                        document.getElementById('status').innerHTML = '❌ 서버 연결 오류';
                    });
            }
            
            function checkEmpty() {
                fetch('/check')
                    .then(response => response.json())
                    .then(data => {
                        alert(JSON.stringify(data, null, 2));
                    });
            }
            
            function startScraping() {
                if (confirm('전체 Instagram 스크래핑을 시작하시겠습니까?')) {
                    fetch('/start', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => {
                            alert(data.message || '스크래핑이 시작되었습니다.');
                        });
                }
            }
            
            function stopScraping() {
                if (confirm('스크래핑을 중단하시겠습니까?')) {
                    fetch('/stop', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => {
                            alert(data.message || '스크래핑이 중단되었습니다.');
                        });
                }
            }
            
            // 자동 상태 업데이트 (3초마다)
            setInterval(updateStatus, 3000);
            updateStatus(); // 초기 로드
        </script>
    </body>
    </html>
    """
    return dashboard_html

@app.route('/status')
def get_status():
    """현재 스크래핑 상태 조회"""
    return jsonify(scraping_status)

@app.route('/check')
def check_empty():
    """스크래핑 대상 확인"""
    result = control_server.get_empty_rows()
    return jsonify(result)

@app.route('/start', methods=['POST'])
def start_scraping():
    """스크래핑 시작"""
    global scraping_status
    
    if scraping_status["is_running"]:
        return jsonify({"error": "이미 스크래핑이 실행 중입니다"}), 400
    
    # 백그라운드에서 스크래핑 실행
    thread = threading.Thread(target=control_server.run_scraping)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "스크래핑이 시작되었습니다", "status": "started"})

@app.route('/stop', methods=['POST'])
def stop_scraping():
    """스크래핑 중단"""
    global scraping_status
    scraping_status["is_running"] = False
    scraping_status["current_item"] = "중단됨"
    scraping_status["last_update"] = datetime.now().isoformat()
    
    return jsonify({"message": "스크래핑이 중단되었습니다", "status": "stopped"})

@app.route('/scrape_specific', methods=['POST'])
def scrape_specific():
    """특정 행만 스크래핑"""
    global scraping_status
    
    if scraping_status["is_running"]:
        return jsonify({"error": "이미 스크래핑이 실행 중입니다"}), 400
    
    data = request.get_json()
    target_rows = data.get('target_rows', [])
    
    if not target_rows:
        return jsonify({"error": "target_rows가 필요합니다"}), 400
    
    # 백그라운드에서 특정 행만 스크래핑
    thread = threading.Thread(target=control_server.run_scraping, args=(target_rows,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": f"{len(target_rows)}개 행 스크래핑이 시작되었습니다", "status": "started"})

if __name__ == '__main__':
    print("="*60)
    print("🤖 Instagram 스크래핑 제어 서버")
    print("="*60)
    print("📡 서버 주소: http://localhost:5555")
    print("🌐 웹 대시보드: http://localhost:5555")
    print("📋 API 엔드포인트:")
    print("  GET  /status - 현재 상태")
    print("  GET  /check  - 스크래핑 대상 확인")
    print("  POST /start  - 전체 스크래핑 시작")
    print("  POST /stop   - 스크래핑 중단")
    print("  POST /scrape_specific - 특정 행만 스크래핑")
    print("="*60)
    print("💡 Apps Script에서 이 서버로 HTTP 요청을 보내서 제어하세요!")
    print("⚠️  Ctrl+C로 서버 종료")
    print("="*60)
    
    try:
        app.run(host='0.0.0.0', port=5555, debug=False)
    except KeyboardInterrupt:
        print("\n🔚 서버가 종료되었습니다.") 