공식에 없는 내용

1. 코일 에나멜 굵기에 따라서도 확인할 수 있어야함.
- 굵다 - 열 적게 발생 - 효율 증가 비용 증가
- 얇다 - 열 많이 발생 - 비용 감소

2. 코어 내경
- 코일 굵기에 따른 회전수 최대치 만족.
- 코어 내경이 작으면 작을수록 효율적

L은 고정값
코일 굵기는 고정값

배포 (Deployment)

1) Streamlit Cloud
- 저장소를 공개 또는 초대 공유 후 Streamlit Cloud에서 앱 생성
- 파일: `app_streamlit.py`
- Python 버전 3.11, Requirements: `requirements.txt`

2) Docker
- 빌드: `docker build -t toroid-app .`
- 실행: `docker run -p 8501:8501 toroid-app`
- 접속: `http://localhost:8501`

3) Heroku/Render류 (Procfile 사용)
- `Procfile` 포함 배포 (웹 dyno/서비스)
- 포트: `$PORT` 환경변수 사용

오프라인 HTML
- `offline.html` 파일을 브라우저로 열면 네트워크 없이도 CSV 업로드/계산/결과 다운로드가 가능합니다.# toroid-connector
# toroid-connector
# toroid-connector
