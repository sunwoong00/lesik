## Getting Started


### Clone Repository

    $ git clone https://github.com/iiVSX/lesik.git
    
### Execute code

    1. 필요한 패키지 준비
        - pip install -r requirements.txt 을 통해 필요한 패키지를 다운 받는다
        - cd Backend → venv/bin/activate을 통해 가상환경을 실행 시킨다

    2. cd Backend → python -u ./lesik.py 을 통해 코드를 실행, (http://localhost:5000/) 로 접속한다
    
## API 설명

### 1) ETRI Open api

#### Request, Response 예시

    {
        request_json = {
            "argument": {
                "analysis_code": analysis_code,
                "text": original_recipe
            }
        }
        http = urllib3.PoolManager()
        response = http.request(
            "POST",
            open_api_url,
            headers={"Content-Type": "application/json; charset=UTF-8", "Authorization" : access_key},
            body=json.dumps(request_json)
        )
    }

### 2) KoELECTRA api


