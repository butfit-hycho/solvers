import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse
import random

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORS preflight 요청 처리"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """지원자 목록 조회"""
        try:
            # 임시 데이터 (실제로는 데이터베이스에서 가져와야 함)
            applicants = [
                {
                    "id": 1,
                    "experience_group": "오리지널소스",
                    "name": "테스트 사용자",
                    "phone": "010-1234-5678",
                    "instagram_url": "https://instagram.com/test",
                    "address_zipcode": "12345",
                    "address_main": "서울시 강남구",
                    "address_detail": "123번지",
                    "created_at": "2025-01-24 10:30:00"
                }
            ]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(applicants, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = json.dumps({"error": str(e)}, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8'))

    def do_POST(self):
        """새 지원자 생성"""
        try:
            # 요청 데이터 읽기
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 필수 필드 검증
            required_fields = ['name', 'phone', 'instagram_url', 'address_main']
            for field in required_fields:
                if not data.get(field):
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    error_response = json.dumps({
                        "error": f"{field} 필드가 필요합니다"
                    }, ensure_ascii=False)
                    self.wfile.write(error_response.encode('utf-8'))
                    return
            
            # Mock Instagram 데이터 생성
            instagram_username = data['instagram_url'].split('/')[-1].split('?')[0]
            instagram_data = {
                "followers": random.randint(100, 10000),
                "following": random.randint(50, 1000),
                "posts": random.randint(10, 500),
                "is_private": random.choice([True, False])
            }
            
            # 새 지원자 ID 생성
            applicant_id = random.randint(1000, 9999)
            
            # 성공 응답
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                "message": "지원서가 성공적으로 제출되었습니다!",
                "applicant_id": applicant_id,
                "instagram_data": instagram_data
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
            
            print(f"✅ 새 지원자 등록: {data['name']} (ID: {applicant_id})")
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = json.dumps({
                "error": "잘못된 JSON 형식입니다"
            }, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = json.dumps({"error": str(e)}, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8')) 