#!/usr/bin/env python3
"""
체험단 운영 툴 - 간단한 서버
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os
import threading
import time
import random
import gspread
from google.oauth2.service_account import Credentials
import psycopg
import concurrent.futures

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173", 
    "http://localhost:8080",
    "https://solvers-liard.vercel.app",
    "https://solvers-gcycn6bc1-butfit-hychos-projects.vercel.app",
    "https://solvers-qgkgemd4e-butfit-hychos-projects.vercel.app",
    "https://solvers-dg0kgn9s5-butfit-hychos-projects.vercel.app",
    "https://solvers-5dkv6i975-butfit-hychos-projects.vercel.app",
    "https://butfit-hycho.github.io"
], supports_credentials=True)

# 데이터베이스 경로 설정 (Vercel 배포 고려)
DB_PATH = os.getenv('DATABASE_PATH', '/tmp/experience_team.db' if os.getenv('VERCEL') else 'experience_team.db')

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applicants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experience_group TEXT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        instagram_url TEXT NOT NULL,
        address_zipcode TEXT,
        address_main TEXT NOT NULL,
        address_detail TEXT,
        address_full TEXT NOT NULL,
        agrees_privacy BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 기존 테이블에 experience_group 컬럼 추가 (이미 있으면 무시)
    try:
        cursor.execute('ALTER TABLE applicants ADD COLUMN experience_group TEXT')
        print("✅ experience_group 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  experience_group 컬럼이 이미 존재합니다")
        else:
            print(f"⚠️ 컬럼 추가 중 오류: {e}")
    
    conn.commit()
    conn.close()
    print("✅ 데이터베이스 초기화 완료")

# HTML 템플릿
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>BUTFIT 체험단 모집</title>
    <meta charset="utf-8">
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            background: #09080E;
            color: #ffffff;
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .main-container {
            max-width: 480px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px 0;
        }
        
        .logo {
            font-size: 32px;
            font-weight: 800;
            color: #00FF47;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        
        .subtitle {
            font-size: 16px;
            color: #888;
            font-weight: 400;
        }
        
        .container {
            background: #1A1A25;
            border-radius: 20px;
            padding: 32px 24px;
            margin-bottom: 24px;
            border: 1px solid #2A2A35;
            backdrop-filter: blur(20px);
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 8px;
            letter-spacing: -0.01em;
        }
        
        .required {
            color: #00FF47;
            font-weight: 700;
        }
        
        .form-input {
            width: 100%;
            padding: 16px;
            background: #09080E;
            border: 2px solid #2A2A35;
            border-radius: 12px;
            color: #ffffff;
            font-size: 16px;
            font-family: 'Pretendard', sans-serif;
            transition: all 0.2s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #00FF47;
            background: #0D0C12;
            box-shadow: 0 0 0 3px rgba(0, 255, 71, 0.1);
        }
        
        .form-input::placeholder {
            color: #666;
        }
        
        .form-input:read-only {
            background: #151419;
            color: #999;
            cursor: not-allowed;
        }
        
        .address-group {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .address-search {
            display: flex;
            gap: 12px;
        }
        
        .address-search .form-input {
            flex: 1;
        }
        
        .btn-address {
            background: linear-gradient(135deg, #00FF47, #00E53E);
            color: #09080E;
            border: none;
            padding: 16px 20px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
            font-family: 'Pretendard', sans-serif;
        }
        
        .btn-address:hover {
            background: linear-gradient(135deg, #00E53E, #00CC35);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 255, 71, 0.3);
        }
        
        .btn-submit {
            width: 100%;
            background: linear-gradient(135deg, #00FF47, #00E53E);
            color: #09080E;
            border: none;
            padding: 18px;
            border-radius: 16px;
            font-size: 18px;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Pretendard', sans-serif;
            letter-spacing: -0.01em;
        }
        
        .btn-submit:hover {
            background: linear-gradient(135deg, #00E53E, #00CC35);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 255, 71, 0.3);
        }
        
        .btn-submit:disabled {
            background: #2A2A35;
            color: #666;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .checkbox-group {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 20px;
            padding: 16px;
            background: #0D0C12;
            border-radius: 12px;
            border: 1px solid #2A2A35;
        }
        
        .checkbox-input {
            width: 20px;
            height: 20px;
            accent-color: #00FF47;
            margin-top: 2px;
        }
        
        .checkbox-label {
            font-size: 14px;
            color: #ffffff;
            line-height: 1.5;
            cursor: pointer;
        }
        
        .help-text {
            font-size: 13px;
            color: #888;
            margin-top: 6px;
            line-height: 1.4;
        }
        
        .privacy-notice {
            font-size: 12px;
            color: #666;
            line-height: 1.4;
            padding: 12px;
            background: #0D0C12;
            border-radius: 8px;
            border-left: 3px solid #00FF47;
            margin-top: 8px;
        }
        
        .success-message {
            background: linear-gradient(135deg, rgba(0, 255, 71, 0.1), rgba(0, 229, 62, 0.05));
            border: 2px solid rgba(0, 255, 71, 0.3);
            border-radius: 20px;
            backdrop-filter: blur(20px);
        }
        
        .form-input.error {
            border-color: #ff4757;
            box-shadow: 0 0 0 3px rgba(255, 71, 87, 0.1);
        }
        
        @media (max-width: 520px) {
            .main-container {
                padding: 16px;
                max-width: 100%;
            }
            
            .container {
                padding: 24px 20px;
            }
            
            .address-search {
                flex-direction: column;
            }
            
            .btn-address {
                padding: 16px;
            }
        }
    </style>
    <script src="https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js"></script>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <div class="logo">BUTFIT</div>
            <div class="subtitle">체험단 모집</div>
        </div>
        
        <div class="container">
            <h2 class="section-title">📝 체험단 지원서</h2>
            <form id="applicationForm">
                <div class="form-group">
                    <label class="form-label" for="name">이름 <span class="required">*</span></label>
                    <input type="text" id="name" class="form-input" placeholder="실명을 입력해주세요" required>
                </div>

                <div class="form-group">
                    <label class="form-label" for="phone">전화번호 <span class="required">*</span></label>
                    <input type="tel" id="phone" class="form-input" placeholder="010-0000-0000" required>
                    <div class="help-text">배송 및 연락을 위해 정확한 번호를 입력해주세요</div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="instagram_url">인스타그램 계정 <span class="required">*</span></label>
                    <input type="url" id="instagram_url" class="form-input" placeholder="https://instagram.com/your_account" required>
                    <div class="help-text">인스타그램 프로필 전체 링크를 입력해주세요</div>
                </div>

                <div class="form-group">
                    <label class="form-label">배송 주소 <span class="required">*</span></label>
                    <div class="address-group">
                        <div class="address-search">
                            <input type="text" id="address_zipcode" class="form-input" placeholder="우편번호" readonly>
                            <button type="button" class="btn-address" id="addressSearchBtn">주소 검색</button>
                        </div>
                        <input type="text" id="address_main" class="form-input" placeholder="기본 주소" readonly required>
                        <input type="text" id="address_detail" class="form-input" placeholder="상세 주소 (동, 호수 등)" required>
                    </div>
                    <div class="help-text">🚚 제품 배송을 위해 정확한 주소를 입력해주세요</div>
                </div>

                <div class="checkbox-group">
                    <input type="checkbox" id="agrees_privacy" class="checkbox-input" required>
                    <label class="checkbox-label" for="agrees_privacy">개인정보 수집 및 이용에 동의합니다 <span class="required">*</span></label>
                </div>
                <div class="privacy-notice">
                    수집항목: 이름, 전화번호, 인스타그램 계정, 주소<br>
                    이용목적: 체험단 운영 및 제품 배송<br>
                    보유기간: 체험단 종료 후 1개월
                </div>

                <button type="submit" class="btn-submit">지원하기</button>
            </form>
        </div>


    </div>

    <script>
        // 다음/카카오 주소 검색 API
        function searchAddress() {
            new daum.Postcode({
                oncomplete: function(data) {
                    document.getElementById('address_zipcode').value = data.zonecode;
                    document.getElementById('address_main').value = data.address;
                    document.getElementById('address_detail').focus();
                }
            }).open();
        }

        // 원래 폼 내용 저장 변수
        let originalFormContent = '';
        
        // DOM이 완전히 로드된 후 이벤트 리스너 등록
        document.addEventListener('DOMContentLoaded', function() {
            // 원래 폼 내용 저장
            const formContainer = document.querySelector('.container');
            if (formContainer) {
                originalFormContent = formContainer.innerHTML;
            }
            // 이벤트 리스너 설정
            setupEventListeners();
        });
        
        // 폼 리셋 함수
        function resetForm() {
            const formContainer = document.querySelector('.container');
            
            if (formContainer && originalFormContent) {
                // 원래 폼 내용 복원
                formContainer.innerHTML = originalFormContent;
                formContainer.className = 'container';
                
                // 이벤트 리스너 다시 등록
                setupEventListeners();
            }
            
            window.scrollTo(0, 0);
        }
        
        // 이벤트 리스너 설정 함수
        function setupEventListeners() {
            // 전화번호 자동 포맷팅
            const phoneInput = document.getElementById('phone');
            if (phoneInput) {
                phoneInput.addEventListener('input', function(e) {
                    let value = e.target.value.replace(/[^0-9]/g, '');
                    if (value.length >= 3 && value.length <= 7) {
                        value = value.substring(0, 3) + '-' + value.substring(3);
                    } else if (value.length >= 8) {
                        value = value.substring(0, 3) + '-' + value.substring(3, 7) + '-' + value.substring(7, 11);
                    }
                    e.target.value = value;
                });
            }

            // 주소 검색 버튼
            const addressSearchBtn = document.getElementById('addressSearchBtn');
            if (addressSearchBtn) {
                addressSearchBtn.addEventListener('click', searchAddress);
            }

            // 지원서 제출
            const applicationForm = document.getElementById('applicationForm');
            if (applicationForm) {
                applicationForm.addEventListener('submit', handleFormSubmit);
            }
        }
        
        // 폼 제출 핸들러 함수
        async function handleFormSubmit(e) {
            e.preventDefault();
            
            // 주소 전체 문자열 생성
            const zipcode = document.getElementById('address_zipcode').value;
            const main = document.getElementById('address_main').value;
            const detail = document.getElementById('address_detail').value;
            const fullAddress = `(${zipcode}) ${main} ${detail}`.trim();
            
            const data = {
                name: document.getElementById('name').value,
                phone: document.getElementById('phone').value,
                instagram_url: document.getElementById('instagram_url').value,
                address_zipcode: zipcode,
                address_main: main,
                address_detail: detail,
                address_full: fullAddress,
                agrees_privacy: document.getElementById('agrees_privacy').checked
            };
            
            // 유효성 검사
            if (!data.name || !data.phone || !data.instagram_url || !data.address_main || !data.address_detail) {
                alert('모든 필수 항목을 입력해주세요.');
                return;
            }
            
            if (!data.agrees_privacy) {
                alert('개인정보 수집 및 이용에 동의해주세요.');
                return;
            }
            
            // 제출 버튼 비활성화
            const submitBtn = document.querySelector('.btn-submit');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = '제출 중...';
            
            try {
                const response = await fetch('/api/applicants', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // 폼 컨테이너를 성공 메시지로 변경
                    const formContainer = document.querySelector('.container');
                    
                    if (formContainer) {
                        formContainer.innerHTML = `
                            <div style="text-align: center; padding: 40px 20px;">
                                <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                                <h3 style="color: #00FF47; font-size: 24px; margin-bottom: 12px; font-weight: 700;">지원이 완료되었습니다!</h3>
                                <p style="color: #ccc; font-size: 16px; line-height: 1.5; margin-bottom: 20px;">
                                    빠른 시일 내에 연락드리겠습니다.<br>
                                    체험단 선발 결과는 개별 연락드릴 예정입니다.
                                </p>
                                <button id="resetFormBtn" style="
                                    background: linear-gradient(135deg, #00FF47, #00E53E);
                                    color: #09080E;
                                    border: none;
                                    padding: 12px 24px;
                                    border-radius: 12px;
                                    font-weight: 700;
                                    font-size: 14px;
                                    cursor: pointer;
                                    font-family: 'Pretendard', sans-serif;
                                    transition: all 0.2s ease;
                                " onmouseover="this.style.background='linear-gradient(135deg, #00E53E, #00CC35)'; this.style.transform='translateY(-1px)'" onmouseout="this.style.background='linear-gradient(135deg, #00FF47, #00E53E)'; this.style.transform='translateY(0)'">
                                    다시 지원하기
                                </button>
                            </div>
                        `;
                        formContainer.className = 'container success-message';
                        
                        // 다시 지원하기 버튼에 이벤트 리스너 추가
                        const resetBtn = document.getElementById('resetFormBtn');
                        if (resetBtn) {
                            resetBtn.addEventListener('click', resetForm);
                        }
                    }
                    // 페이지 최상단으로 스크롤
                    window.scrollTo(0, 0);
                } else {
                    alert('오류: ' + (result.error || '알 수 없는 오류가 발생했습니다.'));
                    // 버튼 복원
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            } catch (error) {
                alert('네트워크 오류: ' + error.message);
                // 버튼 복원
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    </script>
</body>
</html>
'''

# 인스타그램 사용자명 추출 함수
def extract_instagram_username(instagram_url):
    """인스타그램 URL에서 사용자명 추출"""
    import re
    
    # 다양한 인스타그램 URL 패턴 처리
    patterns = [
        r'instagram\.com/([^/?]+)',  # 기본 패턴
        r'instagram\.com/([^/]+)/profilecard',  # profilecard 패턴
        r'instagram\.com/p/([^/?]+)',  # 게시물 패턴
        r'instagram\.com/reel/([^/?]+)',  # 릴스 패턴
    ]
    
    for pattern in patterns:
        match = re.search(pattern, instagram_url)
        if match:
            username = match.group(1)
            # profilecard나 기타 경로가 아닌 실제 사용자명만 반환
            if username not in ['p', 'reel', 'stories', 'tv']:
                return username
    
    return 'unknown_user'

# 실제 인스타그램 스크래핑 함수
def scrape_instagram_profile(username):
    """실제 인스타그램 프로필 스크래핑"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        print(f"🤖 스크래핑 시작: @{username}")
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 백그라운드 실행
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # ChromeDriver 초기화
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Instagram 프로필 페이지 접근
            profile_url = f"https://www.instagram.com/{username}/"
            driver.get(profile_url)
            
            # 페이지 로딩 대기
            time.sleep(random.uniform(2, 4))
            
            # 통계 정보 추출 시도
            followers_count = 0
            following_count = 0
            posts_count = 0
            is_private = False
            
            try:
                # 새로운 Instagram 레이아웃 선택자들
                stats_selectors = [
                    'a[href*="/followers/"] span[title]',  # 팔로워 (title 속성)
                    'a[href*="/followers/"] span',         # 팔로워 (텍스트)
                    'main section ul li:nth-child(2) span[title]',  # 대체 선택자
                    'main section ul li:nth-child(2) button span[title]',
                ]
                
                # 게시물 수 선택자 (2025년 Instagram 레이아웃 대응)
                posts_selectors = [
                    # 최신 Instagram 레이아웃 선택자들
                    'main section div div span[title]',  # 제목 속성이 있는 span
                    'main section div span',             # 메인 섹션의 첫 번째 통계
                    'article section div span',          # 아티클 내 통계
                    'div[data-testid*="user"] ~ div span', # 사용자 아바타 옆 정보
                    'header section ul li span',         # 헤더 통계 리스트
                    'main header section ul li span',    # 메인 헤더 통계
                    # 백업 선택자들
                    'main section ul li:first-child span',
                    'article header section ul li:first-child span',
                    'div[data-testid="user-avatar"] ~ div span'
                ]
                
                # 팔로워 수 추출
                for selector in stats_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.get_attribute('title') or element.text
                            if text and (',' in text or text.isdigit()):
                                followers_count = int(text.replace(',', '').replace('팔로워', '').strip())
                                print(f"📊 팔로워 수 발견: {followers_count:,}")
                                break
                        if followers_count > 0:
                            break
                    except:
                        continue
                
                # 게시물 수 추출 (개선된 로직)
                print("🔍 게시물 수 탐지 시작...")
                
                # 모든 span 요소를 검사해서 숫자만 있는 것 찾기
                try:
                    all_spans = driver.find_elements(By.CSS_SELECTOR, 'main span, article span, header span')
                    print(f"📋 전체 span 요소 {len(all_spans)}개 검사 중...")
                    
                    for span in all_spans:
                        try:
                            text = span.text.strip()
                            title = span.get_attribute('title')
                            
                            # 텍스트나 title에서 숫자 검사
                            for check_text in [text, title]:
                                if check_text:
                                    # 쉼표 제거 후 숫자인지 확인
                                    clean_text = check_text.replace(',', '').strip()
                                    if clean_text.isdigit():
                                        number = int(clean_text)
                                        # 게시물 수로 보이는 범위 (0~10000)
                                        if 0 <= number <= 10000:
                                            # 팔로워 수와 다른 숫자인지 확인
                                            if number != followers_count:
                                                posts_count = number
                                                print(f"📸 게시물 수 후보 발견: {posts_count:,} (원본: '{check_text}')")
                                                break
                        except:
                            continue
                        
                        if posts_count > 0:
                            break
                            
                except Exception as e:
                    print(f"⚠️ 전체 span 검사 실패: {e}")
                
                # 기존 선택자로도 시도
                if posts_count == 0:
                    print("🔄 기존 선택자로 재시도...")
                    for selector in posts_selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                text = element.text.strip()
                                title = element.get_attribute('title')
                                
                                for check_text in [text, title]:
                                    if check_text and check_text.replace(',', '').isdigit():
                                        number = int(check_text.replace(',', ''))
                                        if 0 <= number <= 10000 and number != followers_count:
                                            posts_count = number
                                            print(f"📸 게시물 수 발견 (선택자 {selector}): {posts_count:,}")
                                            break
                                
                                if posts_count > 0:
                                    break
                            if posts_count > 0:
                                break
                        except Exception as e:
                            print(f"⚠️ 선택자 {selector} 실패: {e}")
                            continue
                
                # 비공개 계정 확인
                try:
                    private_indicators = [
                        'span:contains("비공개 계정")',
                        'span:contains("This Account is Private")',
                        'div[data-testid="user-avatar"] ~ div:contains("비공개")'
                    ]
                    
                    for indicator in private_indicators:
                        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '비공개')]")
                        if elements:
                            is_private = True
                            print("🔒 비공개 계정 확인됨")
                            break
                except:
                    pass
                
                return {
                    'followers_count': followers_count,
                    'following_count': following_count,  # TODO: 필요시 추가
                    'posts_count': posts_count,
                    'is_private': is_private,
                    'scraping_success': True,
                    'scraping_error': None
                }
                
            except Exception as e:
                print(f"📊 데이터 추출 실패: {e}")
                return {
                    'followers_count': 0,
                    'following_count': 0,
                    'posts_count': 0,
                    'is_private': False,
                    'scraping_success': False,
                    'scraping_error': str(e)
                }
                
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ 스크래핑 초기화 실패: {e}")
        return {
            'followers_count': 0,
            'following_count': 0,
            'posts_count': 0,
            'is_private': False,
            'scraping_success': False,
            'scraping_error': f"초기화 실패: {str(e)}"
        }

# 인스타그램 데이터 수집 함수 (스크래핑 버전)
def collect_instagram_data(instagram_url, applicant_id):
    """인스타그램 데이터 수집 (실제 스크래핑)"""
    try:
        print(f"🔍 인스타그램 데이터 수집 시작: {instagram_url}")
        
        # URL에서 실제 사용자명 추출
        username = extract_instagram_username(instagram_url)
        print(f"📝 추출된 사용자명: {username}")
        
        # 실제 스크래핑 실행
        scraped_data = scrape_instagram_profile(username)
        
        # 스크래핑 성공 여부에 따라 데이터 구성
        if scraped_data['scraping_success']:
            instagram_data = {
                'followers_count': scraped_data['followers_count'],
                'media_count': scraped_data['posts_count'],  # posts_count를 media_count로 매핑
                'username': username,
                'account_type': 'private' if scraped_data['is_private'] else 'public'
            }
            print(f"✅ 실제 데이터 수집 성공: 팔로워 {instagram_data['followers_count']:,}, 게시물 {instagram_data['media_count']:,}")
        else:
            # 스크래핑 실패시 더미 데이터 + 오류 정보
            instagram_data = {
                'followers_count': 0,
                'media_count': 0,
                'username': username,
                'account_type': 'unknown'
            }
            print(f"⚠️ 스크래핑 실패, 기본 데이터 사용: {scraped_data['scraping_error']}")
        
        # 딜레이 추가 (Instagram 차단 방지)
        time.sleep(random.uniform(1, 3))
        
        # 데이터베이스에 저장
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 인스타그램 정보 테이블 생성 (없으면)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS instagram_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER,
            instagram_url TEXT,
            followers_count INTEGER,
            media_count INTEGER,
            username TEXT,
            account_type TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (applicant_id) REFERENCES applicants (id)
        )
        ''')
        
        # 인스타그램 데이터 저장
        cursor.execute('''
            INSERT INTO instagram_data 
            (applicant_id, instagram_url, followers_count, media_count, username, account_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            applicant_id,
            instagram_url,
            instagram_data['followers_count'],
            instagram_data['media_count'],
            instagram_data['username'],
            instagram_data['account_type']
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 인스타그램 데이터 저장 완료: {instagram_data}")
        
    except Exception as e:
        print(f"❌ 인스타그램 데이터 수집 실패: {e}")

# PostgreSQL 데이터베이스 연결 설정
POSTGRES_CONFIG = {
    'host': 'butfitseoul-replica.cjilul7too7t.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'dbname': 'master_20221217',
    'user': 'hycho',
    'password': 'gaW4Charohchee5shigh0aemeeThohyu'
}

def get_postgres_connection():
    """PostgreSQL 데이터베이스 연결"""
    try:
        conn = psycopg.connect(
            host=POSTGRES_CONFIG['host'],
            port=POSTGRES_CONFIG['port'],
            dbname=POSTGRES_CONFIG['dbname'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password']
        )
        print("✅ PostgreSQL 연결 성공")
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return None

def test_postgres_connection():
    """PostgreSQL 연결 테스트"""
    try:
        conn = get_postgres_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"✅ PostgreSQL 버전: {version[0]}")
                
                # 테이블 목록 확인
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                print(f"📋 사용 가능한 테이블: {[table[0] for table in tables[:10]]}")  # 첫 10개만 표시
                
            conn.close()
            return True
    except Exception as e:
        print(f"❌ PostgreSQL 테스트 실패: {e}")
        return False

# 멤버십 조회 함수 (실제 DB 연결)
def check_membership_status_real(phone, applicant_id):
    """실제 PostgreSQL DB에서 멤버십 상태 조회"""
    try:
        print(f"🔍 실제 DB에서 멤버십 조회 시작: {phone}")
        
        conn = get_postgres_connection()
        if not conn:
            print("❌ DB 연결 실패 - 더미 데이터 사용")
            return check_membership_status_dummy(phone, applicant_id)
        
        with conn.cursor() as cursor:
            # 실제 멤버십 조회 쿼리 (신도림 조건 제거, 지점명 추가)
            membership_query = """
            WITH membership_data AS (
                SELECT
                    a.id AS mbs1_id,
                    TO_CHAR(f.pay_date, 'YYYY-MM-DD') AS mbs1_결제일,
                    TO_CHAR(f.pay_date, 'YYYY-MM') AS mbs1_결제월,
                    a.begin_date AS mbs1_시작일,
                    a.end_date AS mbs1_종료일,
                    TO_CHAR(a.end_date, 'YYYY-MM') AS mbs1_종료월,
                    a.title AS mbs1_상품명,
                    b.item_price AS mbs1_가격,
                    d.name AS mbs1_지점,
                    e.id AS mbs1_user_id,
                    e.name AS mbs1_user_name,
                    REGEXP_REPLACE (e.phone_number, '(02|.{3})(.+)(.{4})', '\\1-\\2-\\3')  AS mbs1_user_phone,
                    ROW_NUMBER() OVER (PARTITION BY e.id ORDER BY a.end_date DESC) AS rn,
                    e.birth_date as mbs1_user_birth
                FROM
                    b_payment_btransactionlog b
                    LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
                    LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
                    LEFT JOIN b_class_bplace d ON d.id = b.b_place_id
                    LEFT JOIN user_user e ON e.id = c.user_id
                    LEFT JOIN b_payment_btransaction f ON f.id = b.transaction_id
                WHERE
                    a.refund_transaction_id IS NULL
                    AND a.id IS NOT NULL
            ),
            -- 현재 유효한 멤버십이 있는 회원 (현재 날짜 이후까지 멤버십이 존재하는 회원)
            active_membership AS (
                SELECT *
                FROM membership_data
                WHERE mbs1_종료일 >= CURRENT_DATE  -- 현재 유효한 멤버십만 선택
                  AND rn = 1 -- 가장 최근 멤버십만 선택
                  AND mbs1_상품명 NOT LIKE '%%버핏레이스%%' -- 제외할 멤버십 1
                  AND mbs1_상품명 NOT LIKE '%%건강 선물%%' -- 제외할 멤버십 2
                  AND mbs1_상품명 NOT LIKE '%%리뉴얼%%' -- 제외할 멤버십 3
                  AND mbs1_상품명 NOT LIKE '%%베네핏%%' -- 제외할 멤버십 4
            )
            -- 최종 결과 출력 (특정 전화번호로 검색, 지점명 포함)
            SELECT 
                am.mbs1_user_name AS "회원이름",
                am.mbs1_user_phone AS "전화번호",
                am.mbs1_user_birth as "생년월",
                am.mbs1_상품명 AS "현재멤버십상품명",
                am.mbs1_시작일 AS "이용시작일",
                am.mbs1_종료일 AS "이용종료일",
                am.mbs1_user_id AS "회원ID",
                am.mbs1_지점 AS "지점명"
            FROM 
                active_membership am
            WHERE
                am.mbs1_user_name NOT LIKE '%%탈퇴%%'
                AND am.mbs1_user_phone = %s
            ORDER BY 
                am.mbs1_user_name ASC, am.mbs1_종료일 DESC
            LIMIT 1;
            """
            
            cursor.execute(membership_query, (phone,))
            result = cursor.fetchone()
            
            if result:
                membership_data = {
                    'is_member': True,
                    'member_name': result[0],
                    'member_phone': result[1], 
                    'member_birth': result[2],
                    'membership_type': result[3],
                    'start_date': result[4].strftime('%Y-%m-%d') if result[4] else None,
                    'end_date': result[5].strftime('%Y-%m-%d') if result[5] else None,
                    'member_id': str(result[6]),
                    'branch_name': result[7]  # 지점명 추가
                }
                print(f"✅ 실제 DB에서 회원 정보 발견: {membership_data['member_name']} ({membership_data['membership_type']}) - {membership_data['branch_name']}")
            else:
                membership_data = {
                    'is_member': False,
                    'member_name': None,
                    'member_phone': None,
                    'member_birth': None,
                    'membership_type': None,
                    'start_date': None,
                    'end_date': None,
                    'member_id': None,
                    'branch_name': None
                }
                print(f"ℹ️ 실제 DB에서 유효한 회원 정보 없음")
        
        conn.close()
        
        # SQLite에 결과 저장 (전체 정보 포함)
        save_membership_to_sqlite(applicant_id, phone, {
            'is_member': membership_data['is_member'],
            'membership_type': membership_data['membership_type'],
            'member_id': membership_data['member_id'],
            'expiry_date': membership_data['end_date'],
            'start_date': membership_data['start_date'],
            'branch_name': membership_data['branch_name']
        })
        
        return membership_data
        
    except Exception as e:
        print(f"❌ 실제 DB 멤버십 조회 실패: {e}")
        # 오류 시 더미 데이터로 폴백
        return check_membership_status_dummy(phone, applicant_id)

def get_membership_history_real(phone):
    """실제 PostgreSQL DB에서 멤버십 히스토리 전체 조회 (재등록 여부 확인용)"""
    try:
        print(f"📜 실제 DB에서 멤버십 히스토리 조회 시작: {phone}")
        
        conn = get_postgres_connection()
        if not conn:
            print("❌ DB 연결 실패 - 빈 히스토리 반환")
            return []
        
        with conn.cursor() as cursor:
            # 제공받은 쿼리를 기반으로 한 개선된 멤버십 히스토리 조회
            history_query = """
            WITH RECURSIVE category AS (
                SELECT a.id AS id, a.name AS name 
                FROM b_payment_bmaincategory a 
                WHERE a.depth = 1
                UNION ALL
                SELECT a.id AS id, c.name 
                FROM b_payment_bmaincategory a 
                JOIN category c ON a.parent_id = c.id 
                WHERE a.depth IN (2, 3)
            ),
            
            mbs_data1 AS (
                SELECT 
                    f.name AS 지점명,
                    CASE WHEN m.id IS NOT NULL THEN m.id ELSE k.id END AS user_id,
                    CASE WHEN m.id IS NOT NULL THEN m.name ELSE k.name END AS 회원명,
                    CASE WHEN m.id IS NOT NULL THEN regexp_replace(m.phone_number, '(02|.{3})(.+)(.{4})', '\\1-\\2-\\3') 
                         ELSE regexp_replace(k.phone_number, '(02|.{3})(.+)(.{4})', '\\1-\\2-\\3') END AS 연락처,
                    a.id AS mbs1_id,
                    c.pay_date AS mbs1_결제일,
                    a.begin_date AS mbs1_시작일,
                    a.end_date AS mbs1_종료일,
                    CASE 
                        WHEN b.is_transfer IS TRUE AND tf.id IS NULL THEN '양도 수수료'
                        WHEN b.is_transfer IS FALSE AND tf.id IS NOT NULL THEN CONCAT(tf.title, '(양수)')
                        WHEN b.is_refund IS TRUE AND rf.id IS NULL THEN CONCAT('(환불)', b.item_info ->> 'description')
                        WHEN b.is_refund IS FALSE AND rf.id IS NOT NULL THEN CONCAT('(환불)', rf.title)
                        WHEN a.id IS NULL AND b.id IS NULL THEN c.pg_log ->> 'name'
                        WHEN a.id IS NULL THEN COALESCE(b.item_info ->> 'description', b.item_info ->> 'name')
                        ELSE a.title 
                    END AS mbs1_상품명,
                    ROUND(
                        CASE 
                            WHEN c.is_transfer IS TRUE THEN c.final_price / 1.1
                            WHEN b.is_refund IS TRUE THEN -b.item_price / 1.1
                            ELSE b.item_price / 1.1
                        END
                    ) AS mbs1_가격,
                    e.name AS mbs1_카테고리,
                    -- 현재 상태 판단
                    CASE 
                        WHEN a.end_date >= CURRENT_DATE THEN 'active'
                        WHEN a.end_date < CURRENT_DATE THEN 'expired'
                        ELSE 'unknown'
                    END AS status
                FROM b_payment_btransaction c 
                    LEFT JOIN b_payment_btransactionlog b ON b.transaction_id = c.id
                    LEFT JOIN b_payment_bproductitem bi ON bi.id = b.item_id
                    LEFT JOIN b_payment_badditionalproductitem bai ON bai.id = b.item_id
                    LEFT JOIN b_payment_blocalitem bli ON bli.id = b.item_id
                    LEFT JOIN b_class_bmembership a ON b.id = a.transaction_log_id
                    LEFT JOIN category e ON e.id = (
                        CASE 
                            WHEN b.item_type = 'item' THEN bi.category_id
                            WHEN b.item_type = 'add_item' THEN bai.category_id
                            WHEN b.item_type = 'local_item' THEN bli.category_id
                        END
                    )
                    LEFT JOIN b_class_bplace f ON f.id = b.b_place_id
                    LEFT JOIN user_user k ON k.id = c.user_id
                    LEFT JOIN b_class_bpass l ON l.id = a.b_pass_id
                    LEFT JOIN user_user m ON m.id = l.user_id
                    LEFT JOIN (
                        SELECT id, original_log_id, item_info ->> 'description' AS title
                        FROM b_payment_btransactionlog
                        WHERE is_refund = TRUE
                    ) rf ON rf.original_log_id = b.id
                    LEFT JOIN (
                        SELECT a.id, a.original_log_id, item_info ->> 'description' AS title
                        FROM b_payment_btransactionlog a
                        LEFT JOIN b_class_bmembership b ON b.transaction_log_id = a.id
                        WHERE is_transfer = TRUE
                    ) tf ON tf.original_log_id = b.id
                WHERE 
                    (b.item_price != 0 OR b.is_transfer = TRUE)
                    AND (a.id IS NULL OR a.title NOT LIKE '%%안심결제%%')
                    AND a.title NOT LIKE '%%임직원%%'
                    AND a.refund_transaction_id IS NULL
                    AND a.id IS NOT NULL
                    AND (CASE WHEN m.id IS NOT NULL THEN regexp_replace(m.phone_number, '(02|.{3})(.+)(.{4})', '\\1-\\2-\\3') 
                         ELSE regexp_replace(k.phone_number, '(02|.{3})(.+)(.{4})', '\\1-\\2-\\3') END) = %s
                    AND a.title NOT LIKE '%%버핏레이스%%'
                    AND a.title NOT LIKE '%%건강 선물%%'
                    AND a.title NOT LIKE '%%리뉴얼%%'
                    AND a.title NOT LIKE '%%베네핏%%'
                    AND (CASE WHEN m.id IS NOT NULL THEN m.name ELSE k.name END) NOT LIKE '%%탈퇴%%'
            ),
            
            mbs_data2 AS (
                SELECT mbs1.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY mbs1.지점명, mbs1.user_id
                        ORDER BY 
                            CASE 
                                WHEN mbs1.mbs1_종료일 IS NOT NULL THEN 0 
                                ELSE 1 
                            END ASC,
                            mbs1.mbs1_종료일 ASC,
                            mbs1.mbs1_id ASC
                    ) AS mbs1_회차
                FROM mbs_data1 mbs1 
            ),
            
            mbs_data3 AS (
                SELECT mbs22.*,
                       mbs2.mbs1_id AS mbs2_id,
                       mbs2.mbs1_결제일 AS mbs2_결제일,
                       mbs2.mbs1_시작일 AS mbs2_시작일,
                       mbs2.mbs1_종료일 AS mbs2_종료일,
                       mbs2.mbs1_상품명 AS mbs2_상품명,
                       mbs2.mbs1_가격 AS mbs2_가격,
                       mbs2.mbs1_카테고리 AS mbs2_카테고리
                FROM mbs_data2 mbs22
                LEFT JOIN mbs_data2 mbs2 
                    ON mbs22.지점명 = mbs2.지점명 
                    AND mbs22.user_id = mbs2.user_id 
                    AND mbs2.mbs1_회차 = mbs22.mbs1_회차 + 1
            )
            
            SELECT 
                mbs1_상품명 AS "상품명",
                mbs1_시작일 AS "시작일",
                mbs1_종료일 AS "종료일",
                mbs1_결제일 AS "결제일",
                mbs1_가격 AS "가격",
                지점명 AS "지점명",
                status AS "상태",
                mbs1_회차 AS "회차",
                mbs2_id AS "다음멤버십ID",
                mbs2_상품명 AS "다음상품명", 
                mbs2_종료일 AS "다음종료일"
            FROM 
                mbs_data3
            ORDER BY 
                mbs1_회차 ASC;
            """
            
            cursor.execute(history_query, (phone,))
            results = cursor.fetchall()
            
            history_list = []
            has_future_membership = False
            future_end_date = None
            
            for row in results:
                history_item = {
                    'membership_type': row[0],
                    'start_date': row[1].strftime('%Y-%m-%d') if row[1] else None,
                    'end_date': row[2].strftime('%Y-%m-%d') if row[2] else None,
                    'payment_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                    'price': row[4],
                    'branch_name': row[5],
                    'status': row[6],
                    'sequence': row[7],  # 회차
                    'next_membership_id': row[8],
                    'next_membership_name': row[9],
                    'next_end_date': row[10].strftime('%Y-%m-%d') if row[10] else None
                }
                history_list.append(history_item)
                
                # 현재 Active 멤버십에 다음 멤버십이 있는지 확인
                if history_item['status'] == 'active' and history_item['next_membership_id']:
                    has_future_membership = True
                    future_end_date = history_item['next_end_date']
            
            print(f"📋 개선된 멤버십 히스토리 조회 완료: {len(history_list)}건")
            
            # 재등록 여부 분석 (개선된 로직)
            active_count = len([h for h in history_list if h['status'] == 'active'])
            expired_count = len([h for h in history_list if h['status'] == 'expired'])
            total_count = len(history_list)
            
            # 현재 Active 멤버십 이후의 멤버십 여부 확인 (회차 기반)
            future_membership_status = "X"  # 기본값: 없음
            
            if has_future_membership and future_end_date:
                future_membership_status = f"O ({future_end_date})"
            
            analysis = {
                'total_memberships': total_count,
                'active_memberships': active_count,
                'expired_memberships': expired_count,
                'has_reregistration': total_count > 1,  # 기존 호환성 유지
                'future_membership_status': future_membership_status,  # 새로운 표시 방식
                'membership_history': history_list
            }
            
            print(f"🔍 개선된 재등록 분석: 총 {total_count}회, 미래 멤버십: {future_membership_status}")
            
        conn.close()
        return analysis
        
    except Exception as e:
        print(f"❌ 개선된 DB 멤버십 히스토리 조회 실패: {e}")
        return {
            'total_memberships': 0,
            'active_memberships': 0,
            'expired_memberships': 0,
            'has_reregistration': False,
            'future_membership_status': 'X',
            'membership_history': []
        }

def check_membership_status_dummy(phone, applicant_id):
    """더미 데이터를 사용한 멤버십 조회 (기존 로직)"""
    dummy_membership = {
        'is_member': phone.startswith('010-1'),
        'membership_type': 'GOLD' if phone.startswith('010-1') else None,
        'expiry_date': '2025-12-31' if phone.startswith('010-1') else None,
        'member_id': 'M' + phone.replace('-', '')[-6:] if phone.startswith('010-1') else None
    }
    
    save_membership_to_sqlite(applicant_id, phone, dummy_membership)
    return dummy_membership

def save_membership_to_sqlite(applicant_id, phone, membership_data):
    """SQLite에 멤버십 데이터 저장 (지점명 포함)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 기존 테이블에 지점명 컬럼이 있는지 확인
        cursor.execute("PRAGMA table_info(membership_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 멤버십 정보 테이블 생성 또는 업데이트 (지점명, 시작일 추가)
        if 'membership_data' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            # 테이블이 없으면 새로 생성 (지점명 포함)
            cursor.execute('''
            CREATE TABLE membership_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER,
                phone TEXT,
                is_member BOOLEAN,
                membership_type TEXT,
                member_id TEXT,
                expiry_date TEXT,
                start_date TEXT,
                branch_name TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (applicant_id) REFERENCES applicants (id)
            )
            ''')
        else:
            # 기존 테이블에 컬럼 추가 (없으면)
            if 'branch_name' not in columns:
                cursor.execute('ALTER TABLE membership_data ADD COLUMN branch_name TEXT')
            if 'start_date' not in columns:
                cursor.execute('ALTER TABLE membership_data ADD COLUMN start_date TEXT')
        
        # 멤버십 데이터 저장 (지점명, 시작일 포함)
        cursor.execute('''
            INSERT INTO membership_data 
            (applicant_id, phone, is_member, membership_type, member_id, expiry_date, start_date, branch_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            applicant_id,
            phone,
            membership_data['is_member'],
            membership_data['membership_type'],
            membership_data['member_id'],
            membership_data['expiry_date'],
            membership_data.get('start_date'),
            membership_data.get('branch_name')
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ SQLite에 멤버십 데이터 저장 완료 (지점명: {membership_data.get('branch_name', 'N/A')})")
        
    except Exception as e:
        print(f"❌ SQLite 멤버십 데이터 저장 실패: {e}")

# 기존 check_membership_status 함수를 실제 DB 사용으로 변경
def check_membership_status(phone, applicant_id):
    """멤버십 상태 조회 (실제 DB 우선, 오류시 더미)"""
    return check_membership_status_real(phone, applicant_id)

# 백그라운드 데이터 수집 작업 (병렬처리로 개선)
def background_data_collection(applicant_id, instagram_url, phone):
    """백그라운드에서 인스타그램 데이터 + 멤버십 조회를 병렬 처리 + 구글 시트 업데이트"""
    print(f"🚀 병렬 백그라운드 데이터 수집 시작 - ID: {applicant_id}")
    
    # 병렬 처리를 위한 결과 저장 변수
    instagram_result = {}
    membership_result = {}
    membership_history = {}
    
    def collect_instagram_parallel():
        """인스타그램 데이터 수집 (병렬)"""
        try:
            print(f"📸 인스타그램 스크래핑 시작 (병렬): {instagram_url}")
            collect_instagram_data(instagram_url, applicant_id)
            instagram_result['status'] = 'completed'
            print(f"✅ 인스타그램 스크래핑 완료 (병렬)")
        except Exception as e:
            print(f"❌ 인스타그램 스크래핑 실패 (병렬): {e}")
            instagram_result['status'] = 'failed'
            instagram_result['error'] = str(e)
    
    def collect_membership_parallel():
        """멤버십 데이터 수집 (병렬)"""
        try:
            print(f"💳 멤버십 조회 시작 (병렬): {phone}")
            # 기본 멤버십 상태 조회
            membership_result.update(check_membership_status(phone, applicant_id))
            print(f"📜 멤버십 히스토리 조회 시작 (병렬): {phone}")
            # 멤버십 히스토리 조회
            membership_history.update(get_membership_history_real(phone))
            print(f"✅ 멤버십 조회 완료 (병렬)")
        except Exception as e:
            print(f"❌ 멤버십 조회 실패 (병렬): {e}")
            membership_result['error'] = str(e)
            membership_history['error'] = str(e)
    
    # ThreadPoolExecutor로 병렬 실행
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 두 작업을 동시에 실행
        future_instagram = executor.submit(collect_instagram_parallel)
        future_membership = executor.submit(collect_membership_parallel)
        
        # 모든 작업 완료까지 대기
        concurrent.futures.wait([future_instagram, future_membership])
    
    elapsed_time = time.time() - start_time
    print(f"⚡ 병렬 처리 완료 - 소요시간: {elapsed_time:.2f}초")
    
    # 잠시 대기 후 구글 시트 업데이트
    time.sleep(1)
    
    # 최신 데이터 가져와서 구글 시트 업데이트
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 멤버십 히스토리 정보를 SQLite에 저장 (새 테이블)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS membership_history_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER,
            phone TEXT,
            total_memberships INTEGER,
            active_memberships INTEGER,
            expired_memberships INTEGER,
            has_reregistration BOOLEAN,
            future_membership_status TEXT,
            history_json TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (applicant_id) REFERENCES applicants (id)
        )
        ''')
        
        # 기존 테이블에 새 컬럼 추가 (없으면)
        try:
            cursor.execute('ALTER TABLE membership_history_data ADD COLUMN future_membership_status TEXT')
        except sqlite3.OperationalError:
            pass  # 컬럼이 이미 존재하면 무시
        
        # 멤버십 히스토리 데이터 저장 (오류가 없는 경우에만)
        if membership_history and not membership_history.get('error'):
            import json
            cursor.execute('''
                INSERT OR REPLACE INTO membership_history_data 
                (applicant_id, phone, total_memberships, active_memberships, expired_memberships, has_reregistration, future_membership_status, history_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                applicant_id,
                phone,
                membership_history.get('total_memberships', 0),
                membership_history.get('active_memberships', 0),
                membership_history.get('expired_memberships', 0),
                membership_history.get('has_reregistration', False),
                membership_history.get('future_membership_status', 'X'),
                json.dumps(membership_history.get('membership_history', []), ensure_ascii=False, default=str)
            ))
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type, i.collected_at,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at,
            mh.total_memberships, mh.has_reregistration, mh.future_membership_status
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        LEFT JOIN membership_history_data mh ON a.id = mh.applicant_id
        WHERE a.id = ?
        ''', (applicant_id,))
        
        row = cursor.fetchone()
        if row:
            applicant_data = {
                'experience_group': row[1],
                'created_at': row[10],
                'name': row[2],
                'phone': row[3],
                'instagram_url': row[4],
                'address_full': row[8],
                'agrees_privacy': bool(row[9]),
                'followers_count': row[11],
                'media_count': row[12],
                'ig_username': row[13],
                'account_type': row[14],
                'instagram_collected_at': row[15],
                'is_member': bool(row[16]) if row[16] is not None else False,
                'membership_type': row[17],
                'member_id': row[18],
                'expiry_date': row[19],
                'start_date': row[20],
                'branch_name': row[21],
                'membership_checked_at': row[22],
                'total_memberships': row[23] or 0,
                'has_reregistration': bool(row[24]) if row[24] is not None else False,
                'future_membership_status': row[25] or 'X',
                # 실제 멤버십 조회 결과 
                'member_name': membership_result.get('member_name'),
                'member_birth': membership_result.get('member_birth'),
                'membership_start_date': row[20] or membership_result.get('start_date'),
                'membership_end_date': row[19] or membership_result.get('end_date')
            }
            
            # 구글 시트 업데이트
            update_google_sheet(applicant_data)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 실패: {e}")
    
    print(f"🎉 병렬 백그라운드 데이터 수집 완료 - ID: {applicant_id}, 총 소요시간: {time.time() - start_time:.2f}초")

# 구글 시트 연동 설정
GOOGLE_SHEETS_CREDENTIALS_FILE = 'google_credentials.json'  # 서비스 계정 인증 파일
GOOGLE_SHEETS_URL = None  # 환경변수나 설정에서 가져올 예정

def setup_google_sheets():
    """구글 시트 연동 설정 (환경변수 지원)"""
    try:
        # 환경변수에서 Google credentials JSON 확인 (Vercel 배포용)
        google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        if google_creds_json:
            # 환경변수에서 JSON 문자열로 설정된 경우
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                tmp_file.write(google_creds_json)
                tmp_credentials_file = tmp_file.name
            
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(tmp_credentials_file, scopes=scope)
            os.unlink(tmp_credentials_file)  # 임시 파일 삭제
            
        elif os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
            # 로컬 파일에서 읽기
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=scope)
            
        else:
            print("⚠️  구글 시트 인증 파일이 없습니다. 수동으로 설정해주세요.")
            return None
            
        client = gspread.authorize(creds)
        print("✅ 구글 시트 연동 준비 완료")
        return client
        
    except Exception as e:
        print(f"❌ 구글 시트 연동 실패: {e}")
        return None

def create_or_get_spreadsheet(client, spreadsheet_name="BUTFIT 체험단 지원자 관리"):
    """구글 시트 생성 또는 기존 시트 가져오기"""
    try:
        # 기존 지정된 시트 ID 사용 (Drive 용량 문제로 새 생성 불가)
        EXISTING_SPREADSHEET_ID = "1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ"
        
        try:
            # 기존 시트 ID로 직접 접근
            spreadsheet = client.open_by_key(EXISTING_SPREADSHEET_ID)
            print(f"✅ 기존 구글 시트 연결: {spreadsheet.url}")
            return spreadsheet
        except Exception as e:
            print(f"⚠️ 지정된 시트 접근 실패, 이름으로 재시도: {e}")
            # 시트 이름으로 찾기 시도
            try:
                spreadsheet = client.open(spreadsheet_name)
                print(f"✅ 이름으로 구글 시트 연결: {spreadsheet.url}")
                return spreadsheet
            except gspread.SpreadsheetNotFound:
                # 새 시트 생성 (용량 문제시 실패할 수 있음)
                spreadsheet = client.create(spreadsheet_name)
            
            # 새로운 양식에 맞는 헤더 설정
            worksheet = spreadsheet.sheet1
            headers = [
                '체험단', '지원일시', '이름', '전화번호', '인스타그램ID', '인스타링크',
                '팔로워수', '게시물수', '주소', '지점명', '멤버십상품명',
                '시작일', '종료일', '재등록여부'
            ]
            worksheet.append_row(headers)
            
            # 헤더 스타일링 (14개 컬럼)
            worksheet.format('A1:N1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
            })
            
            print(f"✅ 새 구글 시트 생성: {spreadsheet.url}")
            return spreadsheet
            
    except Exception as e:
        print(f"❌ 구글 시트 생성/연결 실패: {e}")
        return None

def update_google_sheet(applicant_data):
    """구글 시트에 지원자 데이터 업데이트"""
    try:
        client = setup_google_sheets()
        if not client:
            return False
            
        spreadsheet = create_or_get_spreadsheet(client)
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.sheet1
        
        # 새로운 양식에 맞는 데이터 행 생성
        # 체험단 / 지원일시 / 이름/ 전화번호/인스타그램ID/인스타링크/팔로워수/게시물수/주소/지점명/멤버십상품명/시작일/종료일/재등록여부
        row_data = [
            applicant_data.get('experience_group', ''),             # 체험단
            applicant_data.get('created_at', ''),                    # 지원일시
            applicant_data.get('name', ''),                          # 이름
            applicant_data.get('phone', ''),                         # 전화번호
            applicant_data.get('ig_username', ''),                   # 인스타그램ID
            applicant_data.get('instagram_url', ''),                 # 인스타링크
            applicant_data.get('followers_count', '') or '0',        # 팔로워수
            applicant_data.get('media_count', '') or '0',            # 게시물수
            applicant_data.get('address_full', ''),                  # 주소
            applicant_data.get('branch_name', ''),                   # 지점명
            applicant_data.get('membership_type', ''),               # 멤버십상품명
            str(applicant_data.get('membership_start_date', '')) if applicant_data.get('membership_start_date') else '',  # 시작일
            str(applicant_data.get('membership_end_date', '')) if applicant_data.get('membership_end_date') else '',      # 종료일
            applicant_data.get('future_membership_status', 'X')  # 미래 멤버십 여부 (X 또는 O (종료일))
        ]
        
        # 시트에 데이터 추가
        worksheet.append_row(row_data)
        
        print(f"✅ 구글 시트 업데이트 완료: {applicant_data.get('name')} (재등록: {applicant_data.get('has_reregistration', False)})")
        return True
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 실패: {e}")
        return False

def sync_all_data_to_google_sheet():
    """모든 지원자 데이터를 구글 시트에 동기화"""
    try:
        client = setup_google_sheets()
        if not client:
            return False
            
        spreadsheet = create_or_get_spreadsheet(client)
        if not spreadsheet:
            return False
            
        worksheet = spreadsheet.sheet1
        
        # 기존 데이터 모두 삭제 (헤더 제외)
        worksheet.clear()
        
        # 새로운 양식에 맞는 헤더 재설정
        headers = [
            '체험단', '지원일시', '이름', '전화번호', '인스타그램ID', '인스타링크',
            '팔로워수', '게시물수', '주소', '지점명', '멤버십상품명',
            '시작일', '종료일', '재등록여부'
        ]
        worksheet.append_row(headers)
        
        # 모든 지원자 데이터 가져오기 (멤버십 히스토리 포함)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type, i.collected_at,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at,
            mh.total_memberships, mh.has_reregistration, mh.future_membership_status
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        LEFT JOIN membership_history_data mh ON a.id = mh.applicant_id
        ORDER BY a.created_at DESC
        ''')
        
        # 새로운 양식에 맞는 데이터 변환 및 시트에 추가
        all_rows = []
        for row in cursor.fetchall():
            row_data = [
                row[1] or '',                                         # 체험단 (experience_group)
                row[10] or '',                                        # 지원일시 (created_at)
                row[2] or '',                                         # 이름
                row[3] or '',                                         # 전화번호  
                row[13] or '',                                        # 인스타그램ID
                row[4] or '',                                         # 인스타링크
                row[11] or '0',                                       # 팔로워수
                row[12] or '0',                                       # 게시물수
                row[8] or '',                                         # 주소 (address_full)
                row[21] or '',                                        # 지점명
                row[17] or '',                                        # 멤버십상품명
                str(row[20]) if row[20] else '',                      # 시작일
                str(row[19]) if row[19] else '',                      # 종료일
                row[25] or 'X'                                        # 미래 멤버십 여부 (X 또는 O (종료일))
            ]
            all_rows.append(row_data)
        
        # 일괄 업데이트
        if all_rows:
            worksheet.append_rows(all_rows)
        
        conn.close()
        
        # 헤더 스타일링 (14개 컬럼)
        worksheet.format('A1:N1', {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
        })
        
        print(f"✅ 전체 데이터 구글 시트 동기화 완료: {len(all_rows)}건")
        return True
        
    except Exception as e:
        print(f"❌ 전체 데이터 동기화 실패: {e}")
        return False

@app.route('/')
def home():
    """홈페이지"""
    return HTML_TEMPLATE

@app.route('/api/applicants', methods=['GET', 'POST'])
def api_applicants():
    """지원자 API"""
    
    if request.method == 'GET':
        # 지원자 목록 조회 (인스타그램 + 멤버십 데이터 포함)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name,
            mh.total_memberships, mh.has_reregistration, mh.future_membership_status
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        LEFT JOIN membership_history_data mh ON a.id = mh.applicant_id
        ORDER BY a.created_at DESC
        ''')
        
        applicants = []
        for row in cursor.fetchall():
            applicants.append({
                'id': row[0],
                'experience_group': row[1],
                'name': row[2],
                'phone': row[3],
                'instagram_url': row[4],
                'address_zipcode': row[5],
                'address_main': row[6],
                'address_detail': row[7],
                'address_full': row[8],
                'agrees_privacy': bool(row[9]),
                'created_at': row[10],
                # 인스타그램 데이터
                'followers_count': row[11],
                'media_count': row[12], 
                'ig_username': row[13],
                'account_type': row[14],
                # 멤버십 데이터
                'is_member': bool(row[15]) if row[15] is not None else None,
                'membership_type': row[16],
                'member_id': row[17],
                'expiry_date': row[18],
                'start_date': row[19],
                'branch_name': row[20],
                # 멤버십 히스토리
                'total_memberships': row[21] or 0,
                'has_reregistration': bool(row[22]) if row[22] is not None else False,
                'future_membership_status': row[23] or 'X'
            })
        
        conn.close()
        return jsonify({'applicants': applicants, 'count': len(applicants)})
    
    elif request.method == 'POST':
        # 새 지원자 생성
        data = request.get_json()
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO applicants (experience_group, name, phone, instagram_url, address_zipcode, address_main, address_detail, address_full, agrees_privacy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('experience_group'),
                data.get('name'),
                data.get('phone'),
                data.get('instagram_url'),
                data.get('address_zipcode'),
                data.get('address_main'),
                data.get('address_detail'),
                data.get('address_full'),
                data.get('agrees_privacy', False)
            ))
            
            conn.commit()
            applicant_id = cursor.lastrowid
            conn.close()
            
            # 백그라운드에서 인스타그램 데이터 + 멤버십 조회 실행
            thread = threading.Thread(
                target=background_data_collection,
                args=(applicant_id, data.get('instagram_url'), data.get('phone'))
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({'success': True, 'id': applicant_id}), 201
            
        except sqlite3.IntegrityError:
            return jsonify({'error': '이미 등록된 정보입니다. 중복 지원은 불가능합니다.'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# 관리자용 상세 데이터 조회 API 추가
@app.route('/api/admin/applicants')
def admin_applicants():
    """관리자용 상세 지원자 데이터"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        a.*,
        i.followers_count, i.media_count, i.username, i.account_type, i.collected_at,
        m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at,
        mh.total_memberships, mh.has_reregistration, mh.future_membership_status
    FROM applicants a
    LEFT JOIN instagram_data i ON a.id = i.applicant_id
    LEFT JOIN membership_data m ON a.id = m.applicant_id
    LEFT JOIN membership_history_data mh ON a.id = mh.applicant_id
    ORDER BY a.created_at DESC
    ''')
    
    applicants = []
    for row in cursor.fetchall():
        applicant = {
            'id': row[0],
            'experience_group': row[1],
            'name': row[2],
            'phone': row[3],
            'instagram_url': row[4],
            'address_full': row[8],
            'agrees_privacy': bool(row[9]),
            'created_at': row[10],
            'instagram_data': {
                'followers_count': row[11],
                'media_count': row[12],
                'username': row[13],
                'account_type': row[14],
                'collected_at': row[15]
            } if row[11] is not None else None,
            'membership_data': {
                'is_member': bool(row[16]) if row[16] is not None else None,
                'membership_type': row[17],
                'member_id': row[18],
                'expiry_date': row[19],
                'start_date': row[20],
                'branch_name': row[21],
                'checked_at': row[22]
            } if row[16] is not None else None,
            'membership_history': {
                'total_memberships': row[23] or 0,
                'has_reregistration': bool(row[24]) if row[24] is not None else False,
                'future_membership_status': row[25] or 'X'
            } if row[23] is not None else None
        }
        applicants.append(applicant)
    
    conn.close()
    return jsonify({'applicants': applicants, 'count': len(applicants)})

# 구글 시트 동기화 API 추가
@app.route('/api/admin/sync-google-sheet')
def sync_google_sheet():
    """관리자용: 구글 시트 전체 동기화"""
    try:
        success = sync_all_data_to_google_sheet()
        if success:
            return jsonify({'success': True, 'message': '구글 시트 동기화 완료'})
        else:
            return jsonify({'success': False, 'message': '구글 시트 동기화 실패'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류: {str(e)}'}), 500

# PostgreSQL 연결 테스트 API 추가
@app.route('/api/admin/test-postgres')
def test_postgres():
    """관리자용: PostgreSQL 연결 테스트"""
    try:
        success = test_postgres_connection()
        if success:
            return jsonify({'success': True, 'message': 'PostgreSQL 연결 성공'})
        else:
            return jsonify({'success': False, 'message': 'PostgreSQL 연결 실패'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류: {str(e)}'}), 500

@app.route('/api/admin/test-membership')
def test_membership():
    """관리자용: 멤버십 조회 테스트"""
    try:
        test_phone = '010-1234-5678'  # 테스트용 전화번호
        result = check_membership_status_real(test_phone, 0)
        return jsonify({
            'success': True, 
            'message': '멤버십 조회 테스트 완료',
            'test_phone': test_phone,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류: {str(e)}'}), 500

@app.route('/api/membership/history/<phone>')
def get_membership_history(phone):
    """멤버십 히스토리 조회 API (재등록 여부 확인)"""
    try:
        # 전화번호 형식 정규화 (하이픈 추가)
        if not '-' in phone and len(phone) == 11:
            formatted_phone = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        else:
            formatted_phone = phone
            
        result = get_membership_history_real(formatted_phone)
        
        return jsonify({
            'success': True,
            'phone': formatted_phone,
            'analysis': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류: {str(e)}'}), 500

@app.route('/api/admin/membership/bulk-history', methods=['POST'])
def get_bulk_membership_history():
    """여러 전화번호의 멤버십 히스토리 일괄 조회"""
    try:
        data = request.get_json()
        phone_numbers = data.get('phone_numbers', [])
        
        if not phone_numbers:
            return jsonify({'error': '전화번호 목록이 필요합니다.'}), 400
        
        results = {}
        for phone in phone_numbers:
            # 전화번호 형식 정규화
            if not '-' in phone and len(phone) == 11:
                formatted_phone = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
            else:
                formatted_phone = phone
                
            results[formatted_phone] = get_membership_history_real(formatted_phone)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_checked': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류: {str(e)}'}), 500

@app.route('/health')
def health():
    """헬스 체크"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/favicon.ico')
def favicon():
    """파비콘 요청 처리"""
    from flask import Response
    return Response('', status=204)

# Vercel 또는 운영 환경에서 자동 초기화
if os.getenv('VERCEL') or os.getenv('PRODUCTION'):
    try:
        init_db()
        print("✅ 데이터베이스 초기화 완료 (운영 환경)")
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")

if __name__ == '__main__':
    print("🚀 체험단 운영 툴 시작 중...")
    init_db()
    print("🌐 서버 실행: http://localhost:8000")
    print("📊 관리자 페이지: http://localhost:8000")
    
    # 로컬 개발 환경에서만 실행
    app.run(host='0.0.0.0', port=8000, debug=True) 