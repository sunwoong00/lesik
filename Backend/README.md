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

디지털 레시피 분석을 위해 사용: 형태소 분석 api, 의미역 인식 api

#### api 사용 예시

    {
        request_json = {
            "argument": {
                "analysis_code": [analysis_code],
                "text": [원본 레시피]
            }
        }
        http = urllib3.PoolManager()
        response = http.request(
            "POST",
            open_api_url,
            headers={"Content-Type": "application/json; charset=UTF-8", "Authorization" : [ETRI Open api 발급 키]},
            body=json.dumps(request_json)
        )
    }

analysis_code, ETRI Open api 발급 키, api 반환 형태: (https://aiopen.etri.re.kr/guide/WiseNLU) 참고 

<br/>

### 2) KoELECTRA api

디지털 레시피 분석을 위해 사용: 개체명 인식 api

개체명 인식 type: 
* CV_INGREDIENT (재료)
* CV_SEASONING (첨가물)
* CV_STATE (상태정보)
* QT_TEMPERATURE (온도)
* QT_VOLUME (용량)
* TI_DURATION (시간)

#### api 사용 예시

    {
        KoELECTRA_api_url = "[서버주소]"
        response = http.request(
            "POST",
            KoELECTRA_api_url,
            headers={"Content-Type": "application/text; charset=UTF-8"},
            body=sentence.encode('utf-8')
        )
    }

#### api 반환 형태

    {
        ner_node = {
            "id": id,
            "text": 개체명 인식 text,
            "type": 개체명,
            "begin": 시작 위치,
            "end": 종료 위치
        }
    }
