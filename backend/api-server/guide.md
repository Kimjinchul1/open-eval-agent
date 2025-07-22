전통적인 웹서버 스택:

1. 클라이언트 (브라우저, 앱)          # 요청하는 사람 (손님)
   ↓ HTTP 요청
   
2. 웹서버 (Nginx, Apache)           # 요청 받아서 전달하는 역할 (웨이터)
   ↓ 요청 라우팅
   
3. WSGI/ASGI 서버 (Uvicorn, Gunicorn)  # Python 앱을 실행해주는 서버 (주방장)
   ↓ Python 앱 실행
   
4. 웹 프레임워크 (FastAPI, Django)      # 실제 로직 처리하는 코드 (요리사)
   ↓ 비즈니스 로직
   
5. 데이터베이스 (MySQL, PostgreSQL)    # 데이터 저장소 (창고)
