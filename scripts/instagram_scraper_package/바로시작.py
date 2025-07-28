#!/usr/bin/env python3
"""
🚀 Instagram 스크래핑 도구 - 바로 시작!
설치부터 실행까지 모든 것을 자동화

사용법: python3 바로시작.py
"""

import os
import sys
import time
import subprocess
import shutil
from pathlib import Path

def show_banner():
    """시작 배너 출력"""
    print("""
🚀 Instagram 스크래핑 도구 v2.1 ✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Google Sheets에서 Instagram 정보 자동 수집
⚡ 설치부터 실행까지 완전 자동화
🎯 특정 행만 선택 스크래핑 기능 추가 ✨
🌐 어떤 PC에서든 5분 만에 설정 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

def check_requirements():
    """기본 요구사항 확인"""
    print("🔍 시스템 요구사항 확인 중...")
    
    # Python 버전 확인
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8 이상이 필요합니다. 현재: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} 확인")
    
    # 필요한 파일들 확인
    required_files = [
        'portable_instagram_setup.py',
        'batch_instagram_scraper.py', 
        'instagram_control_server.py'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 필수 파일 없음: {file}")
            return False
        print(f"✅ {file}")
    
    # Google 인증 파일 확인
    if Path("google_credentials.json").exists():
        print(f"✅ google_credentials.json (패키지에 포함됨)")
    
    return True

def show_menu():
    """메인 메뉴 출력"""
    print("""
📋 다음 중 선택하세요:

1️⃣  🛠️  처음 설치 (자동 설치 + 설정)
2️⃣  🚀  바로 실행 (이미 설치된 경우)
3️⃣  🔧  Google 인증 설정 가이드 보기
4️⃣  📊  사용법 및 문제해결 가이드 보기
5️⃣  ❌  종료

""")

def setup_google_credentials():
    """Google 인증 파일 자동 설정"""
    source_file = Path("google_credentials.json")
    target_file = Path("instagram_scraper/google_credentials.json")
    
    if source_file.exists() and Path("instagram_scraper").exists():
        try:
            shutil.copy2(source_file, target_file)
            print(f"✅ Google 인증 파일 자동 설정 완료!")
            return True
        except Exception as e:
            print(f"⚠️ Google 인증 파일 복사 실패: {e}")
            return False
    
    return False

def auto_install():
    """자동 설치 실행"""
    print("🛠️ 자동 설치를 시작합니다...")
    print("📦 Python 패키지, Node.js, LocalTunnel 등을 설치합니다.")
    print("⏱️ 약 3-5분 소요됩니다.\n")
    
    response = input("계속하시겠습니까? (y/N): ").strip().lower()
    if response != 'y':
        print("설치를 취소했습니다.")
        return
    
    try:
        # 자동 설치 스크립트 실행
        result = subprocess.run([sys.executable, 'portable_instagram_setup.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n🎉 자동 설치가 완료되었습니다!")
            
            # Google 인증 파일 자동 설정 시도
            if setup_google_credentials():
                print("🔑 Google 인증 파일도 자동으로 설정되었습니다!")
                print("\n📋 설치 완료!")
                print("   ✅ Python 패키지 설치")
                print("   ✅ Node.js + LocalTunnel 설치")
                print("   ✅ 실행 스크립트 생성")
                print("   ✅ Google 인증 파일 설정")
                print("\n🚀 이제 '2번 바로 실행'을 선택하면 됩니다!")
            else:
                print("\n📋 다음 단계:")
                print("   1. Google Service Account JSON 파일 추가")
                print("   2. Google Sheets Apps Script 설정")
                print("   3. 도구 실행")
                print("\n💡 자세한 내용은 '3번 메뉴'에서 확인하세요!")
        else:
            print(f"\n❌ 설치 중 오류 발생:\n{result.stderr}")
            
    except Exception as e:
        print(f"❌ 설치 실행 중 오류: {e}")

def quick_start():
    """빠른 실행"""
    print("🚀 Instagram 스크래핑 도구를 시작합니다...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # 기본 요구사항 확인
    print("🔍 시스템 확인 중...")
    
    # Python 패키지 확인
    print("📦 Python 패키지 확인...")
    required_packages = ['flask', 'flask_cors', 'gspread', 'requests', 'selenium']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} (설치 필요)")
    
    if missing_packages:
        print(f"\n⚠️ 누락된 패키지가 있습니다: {missing_packages}")
        print("💡 먼저 '1번 메뉴 - 처음 설치'를 실행해주세요.")
        return
    
    # Google 인증 파일 확인 및 자동 설정
    print("\n🔑 Google 인증 파일 확인...")
    if not Path("instagram_scraper/google_credentials.json").exists():
        if Path("google_credentials.json").exists():
            print("🔄 Google 인증 파일을 설정 중...")
            if setup_google_credentials():
                print("✅ Google 인증 파일 설정 완료!")
            else:
                print("❌ Google 인증 파일 설정 실패!")
                return
        else:
            print("❌ Google 인증 파일이 없습니다!")
            print("📋 먼저 Google Service Account JSON 파일을 설정해주세요.")
            print("💡 '3번 메뉴 - Google 인증 설정 가이드'를 참고하세요.")
            return
    else:
        print("✅ Google 인증 파일이 설정되어 있습니다!")
    
    # 실행 스크립트 확인
    print("\n📜 실행 스크립트 확인...")
    script_path = None
    
    # 플랫폼에 따라 스크립트 선택
    if sys.platform == "win32":
        script_path = Path("instagram_scraper/run_instagram_scraper.bat")
        if script_path.exists():
            print("✅ Windows 실행 스크립트 발견")
        else:
            print("❌ Windows 실행 스크립트를 찾을 수 없습니다.")
    else:
        script_path = Path("instagram_scraper/run_instagram_scraper.sh")
        if script_path.exists():
            print("✅ Unix/Mac 실행 스크립트 발견")
        else:
            print("❌ Unix/Mac 실행 스크립트를 찾을 수 없습니다.")
    
    if not script_path or not script_path.exists():
        print("💡 먼저 '1번 메뉴 - 처음 설치'를 실행해주세요.")
        return
    
    print("\n✅ 모든 설정이 완료되었습니다!")
    print("🚀 Instagram 스크래핑 도구를 시작합니다...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        # 스크립트 실행
        if script_path.suffix == '.sh':
            # macOS/Linux
            os.system(f"cd instagram_scraper && bash run_instagram_scraper.sh")
        else:
            # Windows
            os.system(f"cd instagram_scraper && run_instagram_scraper.bat")
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")
        print("💡 문제가 지속되면 '1번 메뉴 - 처음 설치'를 다시 실행해보세요.")

def show_google_auth_guide():
    """Google 인증 설정 가이드 출력"""
    # 패키지에 포함된 인증 파일 확인
    if Path("google_credentials.json").exists():
        print("✅ Google 인증 파일이 이미 패키지에 포함되어 있습니다!")
        print("📋 '1번 처음 설치'를 실행하면 자동으로 설정됩니다.")
        print("")
    
    guide_file = Path("Google_인증_설정.md")
    
    if guide_file.exists():
        print("📖 Google 인증 설정 가이드를 열고 있습니다...")
        
        # 파일 열기 시도
        try:
            if sys.platform == "darwin":  # macOS
                os.system(f"open '{guide_file}'")
            elif sys.platform == "win32":  # Windows  
                os.system(f"start '{guide_file}'")
            else:  # Linux
                os.system(f"xdg-open '{guide_file}'")
                
            print("✅ 가이드 파일이 기본 프로그램으로 열렸습니다.")
        except:
            print("📋 가이드 파일을 수동으로 열어주세요:")
            print(f"   파일 위치: {guide_file.absolute()}")
    else:
        print("❌ 가이드 파일을 찾을 수 없습니다.")
    
    print("\n🔑 Google 인증 설정 요약:")
    print("1. Firebase Console (https://console.firebase.google.com)")
    print("2. 프로젝트 설정 → 서비스 계정")
    print("3. 새 비공개 키 생성 (JSON)")
    print("4. 파일명을 'google_credentials.json'으로 변경")
    print("5. 'instagram_scraper' 폴더에 복사")
    print("6. Google Sheets에 서비스 계정 편집자 권한 부여")

def show_usage_guide():
    """사용법 가이드 출력"""
    guide_file = Path("설치_가이드.md")
    
    if guide_file.exists():
        print("📖 사용법 가이드를 열고 있습니다...")
        
        # 파일 열기 시도
        try:
            if sys.platform == "darwin":  # macOS
                os.system(f"open '{guide_file}'")
            elif sys.platform == "win32":  # Windows
                os.system(f"start '{guide_file}'")
            else:  # Linux
                os.system(f"xdg-open '{guide_file}'")
                
            print("✅ 가이드 파일이 기본 프로그램으로 열렸습니다.")
        except:
            print("📋 가이드 파일을 수동으로 열어주세요:")
            print(f"   파일 위치: {guide_file.absolute()}")
    else:
        print("❌ 가이드 파일을 찾을 수 없습니다.")
    
    print("\n📱 사용법 요약:")
    print("1. 도구 실행 (run_instagram_scraper.sh/.bat)")
    print("2. Google Sheets에서 '🌐 Instagram 원격 제어' 메뉴 사용")
    print("3. '🚀 스크래핑 시작' 클릭")
    print("4. '🔍 상태 확인'으로 진행률 모니터링")
    
    print("\n🔧 Google Sheets 컬럼 구조:")
    print("D열(인스타그램) → G열(팔로워), H열(팔로잉), I열(게시물)")

def main():
    """메인 함수"""
    show_banner()
    
    if not check_requirements():
        print("\n❌ 시스템 요구사항을 만족하지 않습니다.")
        print("📋 Python 3.8 이상과 필수 파일들이 필요합니다.")
        return
    
    while True:
        show_menu()
        
        try:
            choice = input("선택하세요 (1-5): ").strip()
            
            if choice == '1':
                auto_install()
            elif choice == '2':
                quick_start()
            elif choice == '3':
                show_google_auth_guide()
            elif choice == '4':
                show_usage_guide()
            elif choice == '5':
                print("👋 Instagram 스크래핑 도구를 종료합니다.")
                break
            else:
                print("❌ 잘못된 선택입니다. 1-5 중에서 선택해주세요.")
            
            input("\n계속하려면 Enter를 누르세요...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Instagram 스크래핑 도구를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main() 