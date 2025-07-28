# Firebase Functions용 Chrome 설치 Dockerfile
FROM python:3.11-slim

# 시스템 패키지 업데이트 및 Chrome 의존성 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Chrome 저장소 추가
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Chrome 설치
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver는 webdriver-manager가 자동으로 처리

# 작업 디렉토리 설정
WORKDIR /workspace

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Functions Framework 시작
CMD ["python", "-m", "functions_framework", "--target=api", "--port=8080"] 