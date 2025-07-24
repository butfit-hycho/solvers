#!/usr/bin/env python3
"""
GR-EAT 체험단 모집 API - Glitch 배포용
완전 무료, 카드 등록 불필요
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import random
from datetime import datetime

app = Flask(__name__)

# CORS 설정 - 모든 도메인 허용 (Glitch에서는 간단하게)
CORS(app, origins="*")

# 메모리 내 데이터 저장 (임시)
applicants_data = []

@app.route('/')
def home():
    """API 홈페이지"""
    return jsonify({
        "message": "🎯 GR-EAT 체험단 모집 API",
        "version": "1.0.0",
        "status": "running",
        "platform": "Glitch (무료 호스팅)",
        "endpoints": {
            "GET /api/applicants": "지원자 목록 조회",
            "POST /api/applicants": "새 지원자 등록"
        }
    })

@app.route('/api/applicants', methods=['GET'])
def get_applicants():
    """지원자 목록 조회"""
    try:
        return jsonify(applicants_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applicants', methods=['POST'])
def create_applicant():
    """새 지원자 생성"""
    try:
        data = request.get_json()
        print(f"📝 새 지원자 데이터 수신: {data}")
        
        # 필수 필드 검증
        required_fields = ['name', 'phone', 'instagram_url', 'address_main']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 필드가 필요합니다'}), 400
        
        # Mock Instagram 데이터 생성
        instagram_username = data['instagram_url'].split('/')[-1].split('?')[0]
        instagram_data = {
            "followers": random.randint(100, 10000),
            "following": random.randint(50, 1000),
            "posts": random.randint(10, 500),
            "is_private": random.choice([True, False])
        }
        
        # 새 지원자 데이터 생성
        applicant_id = len(applicants_data) + 1
        new_applicant = {
            'id': applicant_id,
            'experience_group': data.get('experience_group', ''),
            'name': data['name'],
            'phone': data['phone'],
            'instagram_url': data['instagram_url'],
            'address_zipcode': data.get('address_zipcode', ''),
            'address_main': data['address_main'],
            'address_detail': data.get('address_detail', ''),
            'instagram_data': instagram_data,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 메모리에 저장
        applicants_data.append(new_applicant)
        
        print(f"✅ 지원자 저장 완료 (ID: {applicant_id}) - 총 {len(applicants_data)}명")
        
        return jsonify({
            'message': '지원서가 성공적으로 제출되었습니다! 🎉',
            'applicant_id': applicant_id,
            'instagram_data': instagram_data
        }), 201
        
    except Exception as e:
        print(f"❌ 지원자 생성 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "platform": "Glitch",
        "applicants_count": len(applicants_data),
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    print("🚀 GR-EAT 체험단 API 시작 중... (Glitch)")
    print("🌟 완전 무료 호스팅!")
    app.run(host='0.0.0.0', port=3000, debug=True) 