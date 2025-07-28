#!/usr/bin/env python3
"""
로컬 Instagram 스크래핑 도구 (최신 컬럼 구조 적용)
Google Sheets에서 Instagram URL을 읽어와서 팔로워/팔로잉/게시물 수를 스크래핑하여 업데이트

컬럼 구조: 체험단, 이름, 휴대폰, 인스타그램, 우편번호, 주소, 팔로워, 팔로잉, 게시물, 지점, 멤버십이름, 시작일, 종료일, 재등록여부, (빈칸), 제출일시
"""

import os
import sys
import time
import json
import gspread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import re
from datetime import datetime

class LocalInstagramScraper:
    def __init__(self, service_account_path=None):
        """초기화"""
        if service_account_path is None:
            # 현재 스크립트 위치를 기준으로 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            service_account_path = os.path.join(parent_dir, 'secrets', 'google-service-account.json')
            
            # 대체 경로들 시도
            if not os.path.exists(service_account_path):
                alt_paths = [
                    os.path.join(parent_dir, 'google_credentials.json'),
                    '../secrets/google-service-account.json',
                    'secrets/google-service-account.json',
                    'google_credentials.json'
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        service_account_path = alt_path
                        break
        
        self.service_account_path = service_account_path
        self.sheet = None
        self.driver = None
        
        # 컬럼 인덱스 (0-based)
        self.columns = {
            '체험단': 0,      # A열
            '이름': 1,        # B열  
            '휴대폰': 2,      # C열
            '인스타그램': 3,  # D열
            '우편번호': 4,    # E열
            '주소': 5,        # F열
            '팔로워': 6,      # G열
            '팔로잉': 7,      # H열
            '게시물': 8,      # I열
            '지점': 9,        # J열
            '멤버십이름': 10, # K열
            '시작일': 11,     # L열
            '종료일': 12,     # M열
            '재등록여부': 13, # N열
            '빈칸': 14,       # O열
            '제출일시': 15    # P열
        }
        
        print("🔧 로컬 Instagram 스크래핑 도구 시작")
        print(f"📋 대상 컬럼: D열(인스타그램) → G,H,I열(팔로워,팔로잉,게시물)")

    def connect_google_sheet(self):
        """Google Sheets 연결"""
        try:
            if not os.path.exists(self.service_account_path):
                print(f"❌ 서비스 계정 파일을 찾을 수 없습니다: {self.service_account_path}")
                print("💡 Google Cloud Console에서 서비스 계정 JSON 키를 다운로드하세요")
                return False
            
            gc = gspread.service_account(self.service_account_path)
            
            # 구글 시트 URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ/edit?gid=0#gid=0"
            spreadsheet = gc.open_by_url(sheet_url)
            self.sheet = spreadsheet.sheet1
            
            print("✅ Google Sheets 연결 성공")
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets 연결 실패: {e}")
            return False

    def setup_selenium(self):
        """Selenium WebDriver 설정"""
        try:
            chrome_options = Options()
            # Instagram 차단 우회를 위한 설정
            chrome_options.add_argument('--headless')  # 백그라운드 실행
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 자동화 감지 방지
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # 이미지 로딩 비활성화
            # chrome_options.add_argument('--disable-javascript')  # Instagram은 JavaScript 필요
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 더 현실적인 User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            
            # 자동화 감지 방지
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 이미지 및 CSS 로딩 비활성화 (속도 향상)
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_settings.plugins": 2,
                "profile.managed_default_content_settings.popups": 2,
                "profile.managed_default_content_settings.geolocation": 2,
                "profile.managed_default_content_settings.media_stream": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            # 자동화 감지 우회 JavaScript 실행
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome WebDriver 설정 완료 (Instagram 우회 설정 적용)")
            return True
            
        except Exception as e:
            print(f"❌ Chrome WebDriver 설정 실패: {e}")
            print("💡 Chrome과 ChromeDriver가 설치되어 있는지 확인하세요")
            return False

    def scrape_instagram_profile(self, url):
        """Instagram 프로필 스크래핑 (성능 최적화 버전)"""
        print(f"  🔍 {url} 스크래핑 중...")
        
        # 1단계: requests 방법 우선 시도 (빠름)
        print("    📡 requests 방법 시도...")
        result = self.scrape_with_requests(url)
        
        if result['success']:
            return result
        
        print("    🔄 Selenium 백업 방법 시도...")
        # 2단계: requests 실패 시 Selenium 사용 (느리지만 안정적)
        
        try:
            if not self.driver:
                print("  ❌ Chrome WebDriver가 설정되지 않음")
                return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "WebDriver 없음"}
            
            # Instagram 페이지 로드 (타임아웃 단축)
            self.driver.set_page_load_timeout(10)  # 15초 → 10초로 단축
            self.driver.get(url)
            
            # 페이지 로딩 대기 (단축)
            wait = WebDriverWait(self.driver, 8)  # 10초 → 8초로 단축
            
            # 통계 정보가 포함된 요소들 찾기
            stat_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li"))
            )
            
            followers = 0
            following = 0
            posts = 0
            
            # 각 통계 요소에서 숫자 추출
            for element in stat_elements:
                text = element.text.lower()
                
                # k/M/B 형식을 숫자로 변환하는 함수
                def parse_number(text):
                    if not text:
                        return 0
                    
                    text = text.replace(',', '').strip().upper()
                    
                    if text.endswith('K'):
                        return int(float(text[:-1]) * 1000)
                    elif text.endswith('M'):
                        return int(float(text[:-1]) * 1000000)
                    elif text.endswith('B'):
                        return int(float(text[:-1]) * 1000000000)
                    else:
                        try:
                            return int(float(text))
                        except:
                            return 0
                
                # 숫자와 단위 추출
                import re
                numbers = re.findall(r'([\d,\.]+[kmb]?)\s*(post|follower|following)', text)
                
                for number, unit in numbers:
                    value = parse_number(number)
                    if 'post' in unit:
                        posts = value
                    elif 'follower' in unit:
                        followers = value
                    elif 'following' in unit:
                        following = value
            
            if followers > 0 or following > 0 or posts > 0:
                print(f"  ✅ 성공: 팔로워 {followers:,}, 팔로잉 {following:,}, 게시물 {posts:,}")
                return {
                    "followers": followers,
                    "following": following, 
                    "posts": posts,
                    "success": True,
                    "error": None
                }
            else:
                print(f"  ⚠️  데이터를 찾을 수 없음")
                return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "데이터 없음"}
                
        except TimeoutException:
            print(f"  ❌ 페이지 로딩 시간 초과")
            return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "시간 초과"}
        except Exception as e:
            print(f"  ❌ 스크래핑 오류: {e}")
            return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": str(e)}
    
    def scrape_with_requests(self, url):
        """requests를 사용한 빠른 Instagram 스크래핑 (백업 방법)"""
        try:
            import requests
            import re
            
            headers = {
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
                'Cache-Control': 'max-age=0',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # 로그인 페이지로 리다이렉트 확인
                if 'accounts/login' in response.url or 'Login • Instagram' in html:
                    print(f"    ⚠️ 로그인 페이지 감지")
                    return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "로그인 요구"}
                
                # k/M/B 형식을 숫자로 변환하는 함수
                def parse_number(text):
                    if not text:
                        return 0
                    
                    text = text.replace(',', '').strip().upper()
                    
                    if text.endswith('K'):
                        return int(float(text[:-1]) * 1000)
                    elif text.endswith('M'):
                        return int(float(text[:-1]) * 1000000)
                    elif text.endswith('B'):
                        return int(float(text[:-1]) * 1000000000)
                    else:
                        try:
                            return int(float(text))
                        except:
                            return 0
                
                # 정규식으로 숫자 패턴 찾기 (k/M/B 형식 지원)
                followers_pattern = r'(\d+(?:[.,]\d+)*[KMBkmb]?)\s*followers?'
                following_pattern = r'(\d+(?:[.,]\d+)*[KMBkmb]?)\s*following'
                posts_pattern = r'(\d+(?:[.,]\d+)*[KMBkmb]?)\s*posts?'
                
                followers_match = re.search(followers_pattern, html, re.IGNORECASE)
                following_match = re.search(following_pattern, html, re.IGNORECASE)
                posts_match = re.search(posts_pattern, html, re.IGNORECASE)
                
                followers = parse_number(followers_match.group(1)) if followers_match else 0
                following = parse_number(following_match.group(1)) if following_match else 0
                posts = parse_number(posts_match.group(1)) if posts_match else 0
                
                if followers > 0 or following > 0 or posts > 0:
                    print(f"    ✅ requests 성공: 팔로워 {followers:,}, 팔로잉 {following:,}, 게시물 {posts:,}")
                    return {
                        "followers": followers,
                        "following": following,
                        "posts": posts,
                        "success": True,
                        "error": None
                    }
                else:
                    print(f"    ⚠️ requests: 데이터 없음")
                    return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "데이터 없음"}
            else:
                print(f"    ❌ HTTP {response.status_code}")
                return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"    ❌ requests 실패: {e}")
            return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": str(e)}

    def find_empty_instagram_rows(self):
        """스크래핑이 필요한 행들 찾기"""
        try:
            all_data = self.sheet.get_all_values()
            if len(all_data) <= 1:
                print("📋 데이터가 없습니다")
                return []
            
            headers = all_data[0]
            print(f"📋 전체 {len(all_data)-1}개 행 확인 중...")
            
            empty_rows = []
            for i, row in enumerate(all_data[1:], start=2):  # 2번째 행부터 (헤더 제외)
                try:
                    # 안전한 인덱스 접근
                    instagram_url = row[self.columns['인스타그램']] if len(row) > self.columns['인스타그램'] else ""
                    followers = row[self.columns['팔로워']] if len(row) > self.columns['팔로워'] else ""
                    name = row[self.columns['이름']] if len(row) > self.columns['이름'] else f"{i}행"
                    
                    # Instagram URL이 있지만 팔로워 정보가 비어있는 경우
                    if instagram_url and instagram_url.strip() and (not followers or followers.strip() == ""):
                        empty_rows.append({
                            'row_num': i,
                            'name': name,
                            'instagram_url': instagram_url.strip()
                        })
                        
                except (IndexError, ValueError) as e:
                    print(f"  ⚠️  {i}행 데이터 오류: {e}")
                    continue
            
            print(f"📊 스크래핑 대상: {len(empty_rows)}개 행")
            return empty_rows
            
        except Exception as e:
            print(f"❌ 데이터 조회 실패: {e}")
            return []

    def update_instagram_data_batch(self, updates):
        """Instagram 데이터를 시트에 배치 업데이트 (성능 향상)"""
        try:
            if not updates:
                return True
            
            # 배치 업데이트용 범위와 값 준비
            batch_data = []
            for update in updates:
                row_num = update['row_num']
                data = update['data']
                
                # G, H, I 열 범위 (팔로워, 팔로잉, 게시물)
                range_name = f'G{row_num}:I{row_num}'
                values = [[data['followers'], data['following'], data['posts']]]
                
                batch_data.append({
                    'range': range_name,
                    'values': values
                })
            
            # 배치 업데이트 실행
            print(f"    📊 {len(batch_data)}개 행 배치 업데이트 중...")
            
            # Google Sheets API batch update
            body = {
                'valueInputOption': 'RAW',
                'data': batch_data
            }
            
            result = self.sheet.spreadsheet.batch_update(body)
            print(f"    ✅ 배치 업데이트 완료: {len(batch_data)}개 범위")
            return True
            
        except Exception as e:
            print(f"  ❌ 배치 업데이트 실패: {e}")
            # 실패 시 개별 업데이트로 fallback
            for update in updates:
                try:
                    row_num = update['row_num']
                    data = update['data']
                    self.update_instagram_data(row_num, data)
                except:
                    continue
            return False

    def update_instagram_data(self, row_num, instagram_data):
        """Instagram 데이터를 시트에 업데이트 (개별)"""
        try:
            # G, H, I 열에 데이터 업데이트
            self.sheet.update_cell(row_num, self.columns['팔로워'] + 1, instagram_data['followers'])
            self.sheet.update_cell(row_num, self.columns['팔로잉'] + 1, instagram_data['following'])
            self.sheet.update_cell(row_num, self.columns['게시물'] + 1, instagram_data['posts'])
            return True
            
        except Exception as e:
            print(f"  ❌ 시트 업데이트 실패: {e}")
            return False

    def run_batch_scraping(self):
        """일괄 스크래핑 실행 (성능 최적화 버전)"""
        print("\n🚀 일괄 Instagram 스크래핑 시작 (최적화됨)")
        
        # Google Sheets 연결
        if not self.connect_google_sheet():
            return
        
        # Selenium 설정 (백업용)
        selenium_ready = self.setup_selenium()
        if not selenium_ready:
            print("⚠️  Selenium 설정 실패 - requests 방법만 사용")
        
        try:
            # 스크래핑 대상 찾기
            empty_rows = self.find_empty_instagram_rows()
            
            if not empty_rows:
                print("✅ 스크래핑할 대상이 없습니다!")
                return
            
            print(f"\n📱 {len(empty_rows)}개 계정 스크래핑 시작...")
            
            success_count = 0
            fail_count = 0
            batch_updates = []
            
            for i, row_data in enumerate(empty_rows, 1):
                print(f"\n[{i}/{len(empty_rows)}] {row_data['name']} 처리 중...")
                
                # Instagram 스크래핑
                result = self.scrape_instagram_profile(row_data['instagram_url'])
                
                if result['success']:
                    # 배치 업데이트용 데이터 준비
                    batch_updates.append({
                        'row_num': row_data['row_num'],
                        'data': result
                    })
                    success_count += 1
                    print(f"  ✅ 스크래핑 완료")
                else:
                    fail_count += 1
                    print(f"  ❌ 실패: {result['error']}")
                
                # 5개씩 모이거나 마지막이면 배치 업데이트
                if len(batch_updates) >= 5 or i == len(empty_rows):
                    if batch_updates:
                        self.update_instagram_data_batch(batch_updates)
                        batch_updates = []
                
                # 요청 간격 단축 (2초 → 0.5초)
                if i < len(empty_rows):
                    print(f"  ⏳ 0.5초 대기...")
                    time.sleep(0.5)
            
            # 최종 결과
            print(f"\n🏁 일괄 스크래핑 완료!")
            print(f"✅ 성공: {success_count}개")
            print(f"❌ 실패: {fail_count}개")
            print(f"📊 성공률: {success_count/(success_count+fail_count)*100:.1f}%")
            
        except KeyboardInterrupt:
            print("\n⏹️  사용자가 중단했습니다")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
        finally:
            # Chrome 드라이버 종료
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                    print("🔚 Chrome WebDriver 종료")
                except:
                    pass

def main():
    """메인 함수"""
    print("="*60)
    print("🔧 로컬 Instagram 스크래핑 도구")
    print("="*60)
    
    # 서비스 계정 파일 경로 확인
    service_account_path = '../secrets/google-service-account.json'
    if not os.path.exists(service_account_path):
        print(f"❌ 서비스 계정 파일을 찾을 수 없습니다: {service_account_path}")
        print("\n💡 설정 방법:")
        print("1. Google Cloud Console → IAM 및 관리 → 서비스 계정")
        print("2. 서비스 계정 생성 및 JSON 키 다운로드")
        print("3. 파일을 secrets/google-service-account.json으로 저장")
        print("4. Google Sheets에 서비스 계정 이메일 공유 권한 부여")
        return
    
    try:
        scraper = LocalInstagramScraper(service_account_path)
        scraper.run_batch_scraping()
    except Exception as e:
        print(f"❌ 프로그램 실행 오류: {e}")

if __name__ == "__main__":
    main() 