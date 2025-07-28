#!/usr/bin/env python3
"""
🚀 Instagram 스크래핑 도구 자동 설치 스크립트
다른 PC에서 쉽게 설치하고 실행할 수 있도록 도와주는 도구

사용법: python3 portable_instagram_setup.py
"""

import os
import sys
import subprocess
import platform
import json
import urllib.request
import zipfile
import shutil
from pathlib import Path

class PortableInstagramSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.current_dir = Path.cwd()
        self.install_dir = self.current_dir / "instagram_scraper"
        
    def print_step(self, step, message):
        """단계별 진행 상황 출력"""
        print(f"\n🔹 [{step}] {message}")
        
    def check_python(self):
        """Python 버전 확인"""
        self.print_step("1/8", "Python 버전 확인")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} 확인됨")
            return True
        else:
            print(f"❌ Python 3.8 이상이 필요합니다. 현재: {version.major}.{version.minor}")
            return False
    
    def check_chrome(self):
        """Chrome 브라우저 확인"""
        self.print_step("2/8", "Chrome 브라우저 확인")
        
        chrome_paths = {
            'darwin': ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'],
            'linux': ['/usr/bin/google-chrome', '/usr/bin/chromium-browser'],
            'windows': [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
            ]
        }
        
        if self.system in chrome_paths:
            for path in chrome_paths[self.system]:
                if os.path.exists(path):
                    print(f"✅ Chrome 브라우저 발견: {path}")
                    return True
        
        print(f"❌ Chrome 브라우저를 찾을 수 없습니다.")
        print(f"📥 다운로드: https://www.google.com/chrome/")
        return False
    
    def check_node(self):
        """Node.js 확인 및 설치"""
        self.print_step("3/8", "Node.js 확인")
        
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js 확인됨: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print(f"❌ Node.js가 설치되지 않았습니다.")
        
        # macOS Homebrew 자동 설치 시도
        if self.system == 'darwin':
            try:
                self.print_step("3/8", "Homebrew로 Node.js 설치 시도")
                subprocess.run(['brew', 'install', 'node'], check=True)
                print(f"✅ Node.js 설치 완료")
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass
        
        print(f"📥 수동 설치 필요: https://nodejs.org/")
        return False
    
    def create_directory(self):
        """설치 디렉토리 생성"""
        self.print_step("4/8", "설치 디렉토리 생성")
        
        try:
            self.install_dir.mkdir(exist_ok=True)
            print(f"✅ 디렉토리 생성됨: {self.install_dir}")
            return True
        except Exception as e:
            print(f"❌ 디렉토리 생성 실패: {e}")
            return False
    
    def install_python_packages(self):
        """Python 패키지 설치"""
        self.print_step("5/8", "Python 패키지 설치")
        
        packages = [
            'selenium>=4.0.0',
            'gspread>=6.0.0',
            'flask>=2.0.0',
            'flask-cors>=4.0.0',
            'requests>=2.25.0',
            'google-auth>=2.0.0',
            'google-auth-oauthlib>=1.0.0',
            'google-auth-httplib2>=0.1.0'
        ]
        
        try:
            print(f"📦 패키지 설치 중...")
            for package in packages:
                print(f"   🔹 {package}")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
            
            print(f"✅ 모든 Python 패키지 설치 완료")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 패키지 설치 실패: {e}")
            return False
    
    def install_localtunnel(self):
        """LocalTunnel 설치"""
        self.print_step("6/8", "LocalTunnel 설치")
        
        try:
            subprocess.run(['npm', 'install', '-g', 'localtunnel'], check=True)
            print(f"✅ LocalTunnel 설치 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ LocalTunnel 설치 실패: {e}")
            print(f"💡 수동 설치: npm install -g localtunnel")
            return False
    
    def download_scripts(self):
        """스크립트 파일들 다운로드/복사"""
        self.print_step("7/8", "스크립트 파일 설정")
        
        # 현재 디렉토리에서 필요한 파일들 복사
        files_to_copy = [
            'batch_instagram_scraper.py',
            'instagram_control_server.py'
        ]
        
        try:
            for filename in files_to_copy:
                src_file = self.current_dir / filename
                dst_file = self.install_dir / filename
                
                if src_file.exists():
                    shutil.copy2(src_file, dst_file)
                    print(f"   ✅ {filename}")
                else:
                    print(f"   ⚠️  {filename} 없음 - 나중에 추가 필요")
            
            # 실행 스크립트 생성
            self.create_run_script()
            print(f"✅ 스크립트 설정 완료")
            return True
            
        except Exception as e:
            print(f"❌ 스크립트 설정 실패: {e}")
            return False
    
    def create_run_script(self):
        """실행 스크립트 생성"""
        
        if self.system == 'windows':
            # Windows 배치 파일
            script_content = '''@echo off
echo 🚀 Instagram 스크래핑 도구 시작
echo.

echo 📡 LocalTunnel 터널 시작 중...
start /B lt --port 5555 --subdomain butfit-instagram-scraper

echo ⏳ 3초 대기...
timeout /t 3 /nobreak >nul

echo 🐍 Python 서버 시작 중...
python instagram_control_server.py

pause
'''
            script_file = self.install_dir / "run_instagram_scraper.bat"
            
        else:
            # macOS/Linux 셸 스크립트
            script_content = '''#!/bin/bash
echo "🚀 Instagram 스크래핑 도구 시작"
echo

echo "📡 LocalTunnel 터널 시작 중..."
lt --port 5555 --subdomain butfit-instagram-scraper &

echo "⏳ 3초 대기..."
sleep 3

echo "🐍 Python 서버 시작 중..."
python3 instagram_control_server.py
'''
            script_file = self.install_dir / "run_instagram_scraper.sh"
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 실행 권한 부여 (Unix 계열)
        if self.system != 'windows':
            os.chmod(script_file, 0o755)
        
        print(f"   ✅ 실행 스크립트: {script_file.name}")
    
    def create_setup_guide(self):
        """설정 가이드 생성"""
        self.print_step("8/8", "설정 가이드 생성")
        
        guide_content = f"""
# 🚀 Instagram 스크래핑 도구 사용 가이드

## 📋 설치 완료!
설치 디렉토리: {self.install_dir}

## 🔧 추가 설정 필요

### 1️⃣ Google Service Account JSON 파일
- Firebase Console에서 서비스 계정 JSON 파일 다운로드
- 파일명을 `google_credentials.json`으로 변경
- `{self.install_dir}` 폴더에 복사

### 2️⃣ Google Sheets Apps Script 설정
1. Google Sheets 열기
2. 확장프로그램 → Apps Script
3. 아래 코드 복사/붙여넣기:

```javascript
function onOpen() {{
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🌐 Instagram 원격 제어')
    .addItem('🔍 상태 확인', 'checkStatus')
    .addItem('🚀 스크래핑 시작', 'startScraping')
    .addItem('⏹️ 스크래핑 중단', 'stopScraping')
    .addToUi();
}}

function checkStatus() {{
  try {{
    const response = UrlFetchApp.fetch('https://butfit-instagram-scraper.loca.lt/status', {{
      'headers': {{'Bypass-Tunnel-Reminder': 'true'}}
    }});
    const data = JSON.parse(response.getContentText());
    
    let message = `📊 Instagram 스크래핑 상태\\n\\n`;
    message += `🏃‍♂️ 실행 중: ${{data.is_running ? 'YES' : 'NO'}}\\n`;
    message += `📈 진행률: ${{data.progress}}/${{data.total}}\\n`;
    message += `✅ 성공: ${{data.success_count}}개\\n`;
    message += `❌ 실패: ${{data.fail_count}}개\\n`;
    
    if (data.current_item) {{
      message += `🎯 현재 작업: ${{data.current_item}}\\n`;
    }}
    
    SpreadsheetApp.getUi().alert('상태 확인', message, SpreadsheetApp.getUi().ButtonSet.OK);
  }} catch (error) {{
    SpreadsheetApp.getUi().alert('❌ 연결 오류', '로컬 서버가 실행되지 않았거나 터널이 활성화되지 않았습니다.', SpreadsheetApp.getUi().ButtonSet.OK);
  }}
}}

function startScraping() {{
  try {{
    const response = UrlFetchApp.fetch('https://butfit-instagram-scraper.loca.lt/start', {{
      'method': 'POST',
      'headers': {{'Bypass-Tunnel-Reminder': 'true'}}
    }});
    
    SpreadsheetApp.getUi().alert('🚀 스크래핑 시작', '스크래핑이 시작되었습니다!', SpreadsheetApp.getUi().ButtonSet.OK);
  }} catch (error) {{
    SpreadsheetApp.getUi().alert('❌ 시작 실패', error.toString(), SpreadsheetApp.getUi().ButtonSet.OK);
  }}
}}
```

## 🎯 사용법

### 1️⃣ 도구 실행
"""

        if self.system == 'windows':
            guide_content += "- `run_instagram_scraper.bat` 더블클릭\n"
        else:
            guide_content += "- 터미널에서 `./run_instagram_scraper.sh` 실행\n"

        guide_content += """
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
"""
        
        guide_file = self.install_dir / "README.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✅ 사용 가이드: {guide_file}")
        return True
    
    def run_setup(self):
        """전체 설치 과정 실행"""
        print("🚀 Instagram 스크래핑 도구 자동 설치 시작")
        print(f"📍 시스템: {self.system}")
        print(f"📂 설치 위치: {self.install_dir}")
        
        steps = [
            ("Python 버전", self.check_python),
            ("Chrome 브라우저", self.check_chrome),
            ("Node.js", self.check_node),
            ("디렉토리 생성", self.create_directory),
            ("Python 패키지", self.install_python_packages),
            ("LocalTunnel", self.install_localtunnel),
            ("스크립트 파일", self.download_scripts),
            ("사용 가이드", self.create_setup_guide)
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
                else:
                    print(f"⚠️ {step_name} 단계에서 문제가 발생했습니다.")
            except Exception as e:
                print(f"❌ {step_name} 단계 실행 중 오류: {e}")
        
        print(f"\n🏁 설치 완료!")
        print(f"✅ 성공: {success_count}/{len(steps)} 단계")
        
        if success_count == len(steps):
            print(f"\n🎉 모든 설치가 완료되었습니다!")
            print(f"📋 다음 단계:")
            print(f"   1. {self.install_dir}/README.md 파일 확인")
            print(f"   2. Google Service Account JSON 파일 추가")
            print(f"   3. Google Sheets Apps Script 설정")
            print(f"   4. run_instagram_scraper.{'bat' if self.system == 'windows' else 'sh'} 실행")
        else:
            print(f"\n⚠️ 일부 단계에서 문제가 발생했습니다.")
            print(f"📋 {self.install_dir}/README.md 파일을 확인하여 수동 설정을 완료해주세요.")

if __name__ == "__main__":
    setup = PortableInstagramSetup()
    setup.run_setup() 