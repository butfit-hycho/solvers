#!/bin/bash
echo "🚀 Instagram 스크래핑 도구 시작"
echo

echo "📡 LocalTunnel 터널 시작 중..."
lt --port 5555 --subdomain butfit-instagram-scraper &

echo "⏳ 3초 대기..."
sleep 3

echo "🐍 Python 서버 시작 중..."
python3 instagram_control_server.py
