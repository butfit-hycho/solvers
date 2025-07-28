#!/bin/bash

# Instagram 스크래핑 실행 스크립트
# 사용법: ./run_instagram_scraper.sh

echo "🚀 Instagram 스크래핑 시작..."
echo "📅 실행 시간: $(date)"

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 및 스크래핑 실행
source venv_local/bin/activate
python3 batch_instagram_scraper.py

echo "✅ Instagram 스크래핑 완료!"
echo "📅 완료 시간: $(date)"
echo "🔗 Google Sheets: https://docs.google.com/spreadsheets/d/1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ/edit" 