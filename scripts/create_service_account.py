#!/usr/bin/env python3
"""
Google Sheets 서비스 계정 JSON 파일 생성 도구
사용자가 Firebase/Google Cloud의 서비스 계정 정보를 입력하면 JSON 파일을 생성합니다.
"""

import json
import os

def create_service_account_json():
    """대화형으로 서비스 계정 JSON 파일 생성"""
    
    print("🔑 Google Sheets 서비스 계정 설정")
    print("=" * 50)
    print()
    print("📋 필요한 정보:")
    print("1. Google Cloud Console → APIs & Services → Credentials")
    print("2. Create Credentials → Service Account")
    print("3. 서비스 계정 생성 → Keys 탭 → Add Key → JSON")
    print("4. 다운로드된 JSON 파일의 내용을 복사")
    print()
    
    # 방법 1: 기존 JSON 파일 복사
    print("🔄 방법 1: 기존 JSON 파일 복사")
    print("기존 서비스 계정 JSON 파일이 있나요? (y/n): ", end="")
    has_file = input().lower()
    
    if has_file == 'y':
        print("JSON 파일 경로를 입력하세요: ", end="")
        source_path = input().strip()
        
        if os.path.exists(source_path):
            try:
                with open(source_path, 'r') as f:
                    service_account_data = json.load(f)
                
                target_path = "/Users/cho/project/solvers/scripts/service-account-key.json"
                with open(target_path, 'w') as f:
                    json.dump(service_account_data, f, indent=2)
                
                print(f"✅ 서비스 계정 파일 복사 완료: {target_path}")
                return target_path
                
            except Exception as e:
                print(f"❌ 파일 복사 실패: {e}")
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {source_path}")
    
    # 방법 2: 간단한 템플릿 생성
    print("\n🔄 방법 2: 간단한 템플릿 생성")
    print("Firebase 프로젝트 ID를 입력하세요 (예: solvers-9ecf1): ", end="")
    project_id = input().strip() or "solvers-9ecf1"
    
    # 간단한 템플릿 생성
    template = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "PLACEHOLDER_KEY_ID",
        "private_key": "-----BEGIN PRIVATE KEY-----\nPLACEHOLDER_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": f"google-sheets@{project_id}.iam.gserviceaccount.com",
        "client_id": "PLACEHOLDER_CLIENT_ID",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/google-sheets%40{project_id}.iam.gserviceaccount.com"
    }
    
    target_path = "/Users/cho/project/solvers/scripts/service-account-key.json"
    with open(target_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"📝 템플릿 파일 생성: {target_path}")
    print()
    print("⚠️  이 템플릿 파일은 실제로 작동하지 않습니다!")
    print("💡 다음 단계:")
    print("1. Google Cloud Console에서 실제 서비스 계정 생성")
    print("2. JSON 키 다운로드")
    print("3. 다운로드한 내용으로 위 파일 교체")
    print()
    print("🔗 Google Cloud Console:")
    print("https://console.cloud.google.com/iam-admin/serviceaccounts")
    
    return target_path

def create_minimal_working_file():
    """최소한의 작동하는 더미 파일 생성 (테스트용)"""
    
    # 실제 Firebase 프로젝트에서 사용할 수 있는 최소 구조
    minimal_data = {
        "type": "service_account",
        "project_id": "solvers-9ecf1",
        "private_key_id": "test",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
        "client_email": "test@solvers-9ecf1.iam.gserviceaccount.com",
        "client_id": "test",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    
    target_path = "/Users/cho/project/solvers/scripts/service-account-key.json"
    with open(target_path, 'w') as f:
        json.dump(minimal_data, f, indent=2)
    
    print(f"📝 최소 더미 파일 생성: {target_path}")
    print("⚠️  이 파일은 테스트용이며 실제 Google Sheets 연결은 되지 않습니다!")
    
    return target_path

if __name__ == "__main__":
    print("🚀 Google Sheets 서비스 계정 설정 시작...")
    print()
    print("어떤 방법을 사용하시겠습니까?")
    print("1. 실제 서비스 계정 설정 (권장)")
    print("2. 테스트용 더미 파일 생성 (임시)")
    print()
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "1":
        result = create_service_account_json()
        print(f"\n✅ 완료: {result}")
    elif choice == "2":
        result = create_minimal_working_file()
        print(f"\n✅ 완료: {result}")
        print("\n💡 참고: Instagram 스크래핑은 작동하지만 Google Sheets 업데이트는 실패합니다.")
    else:
        print("❌ 잘못된 선택입니다.") 