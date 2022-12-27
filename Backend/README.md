## Getting Started


### Clone Repository

    $ git clone https://github.com/iiVSX/lesik.git
    
### Execute code

    1. Python 설치 및 필요한 패키지 준비
        - sudo apt-get update
        - sudo apt-get install python3-venv
        - python3 -m venv venv 을 통해 가상환경을 만든다
        - pip3 install -r requirements.txt 을 통해 필요한 패키지를 다운 받는다.
        해당 파일은 메인 폴더에 존재한다.
        - cd Backend → venv/bin/activate을 통해 가상환경을 실행 시킨다.

    2. cd Backend → python/python3 -u ./lesik.py 을 통해 코드를 실행, (http://localhost:5000/) 로 접속한다

- EC2 설정에 대한 추가 설명은 해당 링크에 있다. 
<a href="https://whoami125.notion.site/AWS-EC2-4fc2808f27664eddba10483ccaa127f6">
<img src="https://img.shields.io/badge/EC2 생성 및 보안 설정-<COLOR>"
style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>

<br/>
    
## 주요 파일 설명

* koelectra.py: 서버에서 모델이 인식한 레시피 속 개체명들을 json 형태로 뿌려주는 코드
* lesik.py: 디지털 레시피 분석 메인 코드
  - 레시피 분석 요소: 시간, 온도, 주재료, 첨가물, 설비, 도구, 조리동작(규격)
* lesik_local.py: 디지털 레시피 분석 결과를 로컬 터미널을 통해 확인할 수 있는 코드
* microRecipe.py: 디지털 레시피를 세부 분석한 결과. 문장의 행동마다 자르고, 동시 조리동작 처리를 한 
* toolmatchwithverb.py: 디지털 레시피 분석을 위해 문장마다 알맞은 도구를 찾기 위한 코드
* toolmachwithverb_microrecipe_version.py: 디지털 레시피 세부 분석을 위해 알맞은 도구를 찾기 위한 코드.

<br/>

## 파일 구조
```
Backend
├─ .cache
├─ .viminfo
├─ koelectra.py
├─ lesik.py
├─ lesik_local.py
├─ microRecipe.py
├─ README.md
├─ toolmachwithverb_microrecipe_version.py
├─ toolmatchwithverb.py
└─ venv
   ├─ bin
   └─ lib
```

## API 설명

### 1) ETRI Open api

디지털 레시피 분석을 위해 사용: 형태소 분석 API, 의미역 인식 API

* 형태소 분석 API: 형태소 분석 API는 자연어 문장에서 의미를 가진 최소 단위인 형태소(명사, 동사, 형용사, 부사, 조사, 어미 등)를 분석하는 기술이다.

* 의미역 인식 API: 의미역 인식 API는 서술어(predicate)와 논항(argument)의 관계를 기반으로 문장의 의미를 분석하는 기술로, 문장 내에서 표현된 각 서술어에 대해서 필수 논항(core argument)와 부가 논항(adverbal argument)를 인식한다.

<br/>

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

analysis_code:
* morp - 형태소 분석
* wsd - 어휘의미 분석
* wsd_poly - 어휘의미 분석
* ner - 개체명 인식
* dparse - 의존 구문 분석
* srl - 의미역 인식

<br/>

ETRI Open api 발급 키, api 반환 형태: ETRI Open api 사이트 (https://aiopen.etri.re.kr/guide/WiseNLU) 참고 

<br/>

### 2) KoELECTRA 개체명 인식 api

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
            "type": 개체명 type,
            "begin": 시작 위치,
            "end": 종료 위치
        }
    }

## API Call

## 1) url + '/index’ [GET]
- Index 화면을 표시하기 위한 레시피 데이터를 디렉토리 안에 존재하는 레시피를 랜덤하게 불러와 표시한다
- 받은 데이터를 '' 기준으로 나누어 상단에 존재하는 텍스트 박스 안에 붙여 넣는다.
#### Response 예시 
```
{
    ['낙지 초무침(2-3인분)', '[기본 재료]', '손질 낙지 300g', '양파 ⅓개',
    '미나리 한 줌 (40g)', '청양고추 1개', '홍고추 ½개', '당근 ⅓개', '소금
    ½큰술', '[양념 재료]', '고추장 2큰술', '고춧가루 1큰술', '매실청 1큰술',
    '설탕 1큰술', '식초 3큰술', '다진 마늘 ½큰술', '참기름 ½큰술', '통깨 약간', 
    [조리방법]', '1. 양파는 채를 썰고 미나리와 당근은 5cm 길이로 먹기 좋게
    썰어주세요. 청홍고추는 어슷하게 썰어주세요.', '', '2. 볼에 양념 재료를 넣어
    섞어주세요.', '', '3. 끓는 물에 소금을 넣고 낙지를 살짝 데친 후 얼음물에 넣어
    식힌 후 체에 밭쳐 물기를 빼주세요.', '(Tip.얼음물에 넣게 되면 쫄깃함과
    탱글탱글함이 더해져요)', '', '4. 큰 볼에 손질한 야채와 낙지, 양념장을 넣어
    가볍게 버무려주세요.', '', '5. 접시에 담은 후 통깨를 뿌려 맛있게 즐겨주세요.']
}
```
## 2) url + '/microrecipe’ [GET]
- MicroRecipe(세부분석)에 표시할 레시피를 가지고 온다. 이때 가지고 오는 레시피는 Index에서 사용하고 있는 레시피 정보를 가지고 온다.
#### Response 예시 
```
1) url + '/index’ [GET] 과 비슷하다
```
## 3) url + '/microrecipe/returnjson’ [GET/POST]
- 만약에 요청이 GET인 경우 세부 분석의 결과를 바로 리턴하여 UI에 표시한다 (이미 레시피를 Index에서 전달 받은 경우)
- 만약에 요청이 POST인 경우 JSON 형태를 받아와 분석한다
- 세부 분석에 어떤 기능이 있는지는 해당 README 상단 "주요 기능"에 설명해두었다
#### Request 예시
```
data = {
    "name": "Flask Room",
    "description": 레시피 텍스트,
}

{
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": JSON.stringify(data),
}
```
#### Response 예시 
```
{
    "hi": [
        {"duration": "", "act": "썰다", "tool": "도마, 칼", "ingre": [],
        "seasoning": [], "volume": [], "temperature": [], "zone": "전처리",
        "start_id": 0, "end_id": 5, "act_id": 5, "sentence": "양파는 채를
        썰다", "standard": "", "top_class": ""}, 
        #길이만큼 반복]
}
```
## 4) url + '/recipe' [POST]
- Index에서 전달 받은 레시피와 세부 옵션을 백앤드에 전달하여 자동화 디지털 레시피를 생성하고 동시에 Index UI에 표시한다
- 이때 생성하는 레시피에는 시간, 온도, 주재료, 첨가물, 설비, 도구, 조리 동작 등의 정보가 포함되어 있다
#### Request 예시
```
{
    [
        ('recipe', '#레시피 정보'), 
        ('entity_mode', 'koelectra'), 
        ('srl_mode', 'true')
    ]
}
```
#### Response 예시 
```
3) url + '/microrecipe/returnjson’ [GET/POST] 와 비슷하다
```
## 5) url + '/prompt’ [POST]
- Index의 자동화 레시피 결과를 전처리/화구존에 따라 분류한 데이터를 Prompt쪽으로 넘기고, 동시에 결과물을 UI에 보여준다
#### Request 예시
```
{
    [
    {"duration": "", "act": "섞다", "tool": ["그릇"], "ingre": [], "seasoning": ["열무김치 국물", "생수"], "volume": ["1컵", ""], "temperature": [], "zone": "",
    "start_id": 0, "end_id": 9, 
    "sentence": "1. 열무김치 국물과 생수를 섞은", "standard": "", "top_class": "mix"}, {"duration": "", "act": "담다", "tool": ["지퍼백"], "ingre": [], "seasoning": [],
    "volume": [], "temperature": [], "zone": "", "start_id": 10, "end_id": 15, "sentence": "후 지퍼백에 담아 살얼음이 생기도록 3시간 정도 미리 얼려주세요.", "standard": "",
    "top_class": "put"}, {"duration": "", "act": "섞다", "tool": ["볼"], "ingre": [], "seasoning": ["식초", "설탕", "고추장", "고춧가루", "참기름", "통깨"], "volume": ["
    큰술", "2큰술", "1큰술", "1큰술", "1큰술", "1큰술"], "temperature": [], "zone": "전처리존", "start_id": 0, "end_id": 9, "sentence": "2. 볼에 양념 재료를 넣고 섞어주
    요.", "standard": "", "top_class": "mix"}
    ]
}
```
#### Response 예시 
```
3) 4) url + '/recipe' [POST] 와 비슷하다
```

## 6) url + '/save' [POST]
- 자동화된 레시피 정보의 JSON 형태를 사용자의 컴퓨터에 저장합니다.
#### Response 예시
```
{
    "recipe_result": [
        {
            "duration": "",
            "act": "해감하다",
            "tool": [
                ""
            ],
            "ingre": [
                "바지락"
            ],
            "seasoning": [],
            "volume": [
                "300g"
            ],
            "temperature": [],
            "zone": "",
            "start_id": 0,
            "end_id": 4,
            "sentence": "1. 바지락은 해감해서",
            "standard": "",
            "top_class": ""
        }
}
```
