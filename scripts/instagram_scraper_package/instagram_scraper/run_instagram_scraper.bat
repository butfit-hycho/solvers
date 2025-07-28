@echo off
chcp 65001 >nul
cls

echo 🚀 Instagram 스크래핑 도구 시작
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo 🔍 Python 환경 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 💡 Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

echo 📦 필요한 패키지 확인 중...
python -c "
import sys
required_packages = ['flask', 'flask_cors', 'gspread', 'requests', 'selenium']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError:
        missing_packages.append(package)
        print(f'❌ {package} (설치 필요)')

if missing_packages:
    print(f'\n⚠️ 누락된 패키지: {missing_packages}')
    print('💡 바로시작.py에서 \"1번 처음 설치\"를 다시 실행해주세요.')
    sys.exit(1)
else:
    print('\n✅ 모든 패키지가 설치되어 있습니다!')
"

if errorlevel 1 (
    echo.
    echo ❌ 패키지 확인 실패
    echo 💡 바로시작.py에서 '1번 처음 설치'를 다시 실행해주세요.
    pause
    exit /b 1
)

echo.
echo 📡 LocalTunnel 터널 시작 중...
echo 🌐 URL: https://butfit-instagram-scraper.loca.lt

start /B lt --port 5555 --subdomain butfit-instagram-scraper

echo ⏳ LocalTunnel 연결 대기 중...
timeout /t 5 /nobreak >nul

echo.
echo 🐍 Instagram 스크래핑 서버 시작 중...
echo 🎯 포트: 5555
echo 🔗 로컬: http://localhost:5555
echo.
echo ⏹️  종료하려면 Ctrl+C를 누르세요
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

python instagram_control_server.py

echo.
echo 🧹 정리 작업 중...
taskkill /f /im lt.exe >nul 2>&1
echo ✅ Instagram 스크래핑 도구가 종료되었습니다.
pause 