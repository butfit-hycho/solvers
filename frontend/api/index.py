import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """API 홈페이지"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({
                "message": "GR-EAT 체험단 모집 API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": [
                    "/api/applicants - GET: 지원자 목록 조회",
                    "/api/applicants - POST: 새 지원자 등록"
                ]
            }, ensure_ascii=False)
            
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = json.dumps({"error": str(e)}, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8')) 