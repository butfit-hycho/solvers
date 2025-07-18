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

app = Flask(__name__)
CORS(app)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('experience_team.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applicants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                            <button type="button" class="btn-address" onclick="searchAddress()">주소 검색</button>
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

        <div class="container">
            <div class="success-message" id="successMessage" style="display: none;">
                <div style="text-align: center; padding: 40px 20px;">
                    <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
                    <h3 style="color: #00FF47; font-size: 24px; margin-bottom: 12px;">지원이 완료되었습니다!</h3>
                    <p style="color: #ccc; font-size: 16px; line-height: 1.5;">
                        빠른 시일 내에 연락드리겠습니다.<br>
                        체험단 선발 결과는 개별 연락드릴 예정입니다.
                    </p>
                    <button onclick="resetForm()" style="margin-top: 20px; background: #2A2A35; color: #fff; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer;">다시 지원하기</button>
                </div>
            </div>
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

                 // 전화번호 자동 포맷팅
         document.getElementById('phone').addEventListener('input', function(e) {
             let value = e.target.value.replace(/[^0-9]/g, '');
             if (value.length >= 3 && value.length <= 7) {
                 value = value.substring(0, 3) + '-' + value.substring(3);
             } else if (value.length >= 8) {
                 value = value.substring(0, 3) + '-' + value.substring(3, 7) + '-' + value.substring(7, 11);
             }
             e.target.value = value;
         });

        // 지원서 제출
        document.getElementById('applicationForm').addEventListener('submit', async (e) => {
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
            
            try {
                const response = await fetch('/api/applicants', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // 폼 숨기고 성공 메시지 표시
                    document.querySelector('.container:first-of-type').style.display = 'none';
                    document.getElementById('successMessage').style.display = 'block';
                    // 페이지 최상단으로 스크롤
                    window.scrollTo(0, 0);
                } else {
                    alert('오류: ' + (result.error || '알 수 없는 오류가 발생했습니다.'));
                }
            } catch (error) {
                alert('네트워크 오류: ' + error.message);
            }
        });
        
        // 폼 리셋 함수
        function resetForm() {
            document.getElementById('successMessage').style.display = 'none';
            document.querySelector('.container:first-of-type').style.display = 'block';
            document.getElementById('applicationForm').reset();
            window.scrollTo(0, 0);
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
        conn = sqlite3.connect('experience_team.db')
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
        conn = sqlite3.connect('experience_team.db')
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

# 백그라운드 데이터 수집 작업 (수정)
def background_data_collection(applicant_id, instagram_url, phone):
    """백그라운드에서 인스타그램 데이터 + 멤버십 조회 + 구글 시트 업데이트"""
    print(f"🚀 백그라운드 데이터 수집 시작 - ID: {applicant_id}")
    
    # 인스타그램 데이터 수집
    collect_instagram_data(instagram_url, applicant_id)
    
    # 멤버십 상태 조회  
    membership_result = check_membership_status(phone, applicant_id)
    
    # 잠시 대기 후 구글 시트 업데이트
    time.sleep(2)
    
    # 최신 데이터 가져와서 구글 시트 업데이트
    try:
        conn = sqlite3.connect('experience_team.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type, i.collected_at,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        WHERE a.id = ?
        ''', (applicant_id,))
        
        row = cursor.fetchone()
        if row:
            applicant_data = {
                'created_at': row[9],
                'name': row[1],
                'phone': row[2],
                'instagram_url': row[3],
                'address_full': row[7],
                'agrees_privacy': bool(row[8]),
                'followers_count': row[10],
                'media_count': row[11],
                'ig_username': row[12],
                'account_type': row[13],
                'instagram_collected_at': row[14],
                'is_member': bool(row[15]) if row[15] is not None else False,
                'membership_type': row[16],
                'member_id': row[17],
                'expiry_date': row[18],
                'start_date': row[19],  # SQLite에서 가져온 시작일
                'branch_name': row[20],  # SQLite에서 가져온 지점명
                'membership_checked_at': row[21],
                # 실제 멤버십 조회 결과 (SQLite 데이터로 대체되지만 호환성 유지)
                'member_name': membership_result.get('member_name'),
                'member_birth': membership_result.get('member_birth'),
                'membership_start_date': row[19] or membership_result.get('start_date'),
                'membership_end_date': row[18] or membership_result.get('end_date')
            }
            
            # 구글 시트 업데이트
            update_google_sheet(applicant_data)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 실패: {e}")
    
    print(f"🎉 백그라운드 데이터 수집 완료 - ID: {applicant_id}")

# 구글 시트 연동 설정
GOOGLE_SHEETS_CREDENTIALS_FILE = 'google_credentials.json'  # 서비스 계정 인증 파일
GOOGLE_SHEETS_URL = None  # 환경변수나 설정에서 가져올 예정

def setup_google_sheets():
    """구글 시트 연동 설정"""
    try:
        if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
            print("⚠️  구글 시트 인증 파일이 없습니다. 수동으로 설정해주세요.")
            return None
            
        # 구글 시트 API 인증
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            GOOGLE_SHEETS_CREDENTIALS_FILE, 
            scopes=scope
        )
        
        client = gspread.authorize(credentials)
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
            
            # 상세한 헤더 설정
            worksheet = spreadsheet.sheet1
            headers = [
                '지원일시', '이름', '전화번호', '인스타그램 사용자명', '인스타그램 링크',
                '주소', '팔로워수', '게시물수',
                '멤버십상품명', '멤버십시작일', '멤버십종료일', '지점명'
            ]
            worksheet.append_row(headers)
            
            # 헤더 스타일링 (12개 컬럼)
            worksheet.format('A1:L1', {
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
        
        # 상세한 데이터 행 생성
        row_data = [
            applicant_data.get('created_at', ''),
            applicant_data.get('name', ''),
            applicant_data.get('phone', ''),
            applicant_data.get('ig_username', ''),
            applicant_data.get('instagram_url', ''),
            applicant_data.get('address_full', ''),
            applicant_data.get('followers_count', '') or '0',
            applicant_data.get('media_count', '') or '0',
            applicant_data.get('membership_type', ''),
            str(applicant_data.get('membership_start_date', '')) if applicant_data.get('membership_start_date') else '',
            str(applicant_data.get('membership_end_date', '')) if applicant_data.get('membership_end_date') else '',
            applicant_data.get('branch_name', '')
        ]
        
        # 시트에 데이터 추가
        worksheet.append_row(row_data)
        
        print(f"✅ 구글 시트 업데이트 완료: {applicant_data.get('name')}")
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
        
        # 상세한 헤더 재설정
        headers = [
            '지원일시', '이름', '전화번호', '인스타그램 사용자명', '인스타그램 링크',
            '주소', '팔로워수', '게시물수',
            '멤버십상품명', '멤버십시작일', '멤버십종료일', '지점명'
        ]
        worksheet.append_row(headers)
        
        # 모든 지원자 데이터 가져오기
        conn = sqlite3.connect('experience_team.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type, i.collected_at,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        ORDER BY a.created_at DESC
        ''')
        
        # 상세한 데이터 변환 및 시트에 추가
        all_rows = []
        for row in cursor.fetchall():
            row_data = [
                row[9] or '',  # created_at
                row[1] or '',  # name
                row[2] or '',  # phone
                row[12] or '',  # ig_username
                row[3] or '',  # instagram_url
                row[7] or '',  # address_full
                row[10] or '0',  # followers_count
                row[11] or '0',  # media_count
                row[16] or '',  # membership_type
                str(row[19]) if row[19] else '',  # start_date (시작일)
                str(row[18]) if row[18] else '',  # expiry_date (종료일)
                row[20] or ''  # branch_name (지점명)
            ]
            all_rows.append(row_data)
        
        # 일괄 업데이트
        if all_rows:
            worksheet.append_rows(all_rows)
        
        conn.close()
        
        # 헤더 스타일링 (12개 컬럼)
        worksheet.format('A1:L1', {
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
        conn = sqlite3.connect('experience_team.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        ORDER BY a.created_at DESC
        ''')
        
        applicants = []
        for row in cursor.fetchall():
            applicants.append({
                'id': row[0],
                'name': row[1],
                'phone': row[2],
                'instagram_url': row[3],
                'address_zipcode': row[4],
                'address_main': row[5],
                'address_detail': row[6],
                'address_full': row[7],
                'agrees_privacy': bool(row[8]),
                'created_at': row[9],
                # 인스타그램 데이터
                'followers_count': row[10],
                'media_count': row[11], 
                'ig_username': row[12],
                'account_type': row[13],
                # 멤버십 데이터
                'is_member': bool(row[14]) if row[14] is not None else None,
                'membership_type': row[15],
                'member_id': row[16],
                'expiry_date': row[17],
                'start_date': row[18],
                'branch_name': row[19]
            })
        
        conn.close()
        return jsonify({'applicants': applicants, 'count': len(applicants)})
    
    elif request.method == 'POST':
        # 새 지원자 생성
        data = request.get_json()
        
        try:
            conn = sqlite3.connect('experience_team.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO applicants (name, phone, instagram_url, address_zipcode, address_main, address_detail, address_full, agrees_privacy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
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
    conn = sqlite3.connect('experience_team.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        a.*,
        i.followers_count, i.media_count, i.username, i.account_type, i.collected_at,
        m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at
    FROM applicants a
    LEFT JOIN instagram_data i ON a.id = i.applicant_id
    LEFT JOIN membership_data m ON a.id = m.applicant_id
    ORDER BY a.created_at DESC
    ''')
    
    applicants = []
    for row in cursor.fetchall():
        applicant = {
            'id': row[0],
            'name': row[1],
            'phone': row[2],
            'instagram_url': row[3],
            'address_full': row[7],
            'agrees_privacy': bool(row[8]),
            'created_at': row[9],
            'instagram_data': {
                'followers_count': row[10],
                'media_count': row[11],
                'username': row[12],
                'account_type': row[13],
                'collected_at': row[14]
            } if row[10] is not None else None,
            'membership_data': {
                'is_member': bool(row[15]) if row[15] is not None else None,
                'membership_type': row[16],
                'member_id': row[17],
                'expiry_date': row[18],
                'start_date': row[19],
                'branch_name': row[20],
                'checked_at': row[21]
            } if row[15] is not None else None
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

@app.route('/health')
def health():
    """헬스 체크"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 체험단 운영 툴 시작 중...")
    init_db()
    print("🌐 서버 실행: http://localhost:8000")
    print("📊 관리자 페이지: http://localhost:8000")
    
    app.run(host='0.0.0.0', port=8000, debug=True) 