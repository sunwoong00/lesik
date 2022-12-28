# 래식: AI 기반 디지털 레시피 자동 생성화

<img src="https://drive.google.com/uc?export=view&id=12ogQey6rqwke_tgX9q2ydozusaihkGYa" alt="drawing" style="width:1000px;"/>

음식 레시피들은 조리하는 데 있어 개인의 해석에 따라 다르게 조리하여 동일한 결과가 나오지 않을 수 있다. 이를 해결하기 위해 디지털 레시피 자동 생성 솔루션을 개발하였다.

---

### Repository 설명

##### Frontend
* 디지털 레시피 분석 frontend 코드 (html, css, js)

##### Backend
* 디지털 레시피 분석 Backend 코드 (Flask)

##### Crawling
* 우리의 식탁, 만개의 레시피 크롤링 코드

##### KoELECTRA
* 레시피 개체명 인식 언어 모델: 코드(train, test), 데이터(레이블링, 학습), 모델, 레시피(한식, 중식, 양식), 토크나이저 

---

### 주요 기능

- 디지털 레시피 자동 생성
- 프롬프트 간편화
- Micro Recipe (레시피 분해)

---

### 코드 실행 로직

1. 레시피를 입력 받는다

2. 조리동작을 추출한다
    - EtriOpenAPI를 통해 동사(VV)를 분별, 이후 딕션너리를 통해 단순 동사인지 조리동작에 해당하는 동사인지 판단 → 조리동작을 기준으로 sequences 분리 <a href="https://github.com/iiVSX/lesik/tree/master/Backend#readme">
    <img src="https://img.shields.io/badge/백앤드 README-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>
        
3. 레시피 구성 요소들을 추출한다
    - 개체명 인식을 통해 식재료, 용량, 첨가물, 온도, 시간을 추출한다
    - 학습시킨 KoELECTRA를 사용하여 개체명 인식을 진행하고 추가적으로 Rule-based을 통해 발견하지 못한 요소들을 딕셔너리를 통해 찾아낸다 <a href="https://github.com/iiVSX/lesik/blob/master/KoELECTRA/README.md">
    <img src="https://img.shields.io/badge/KoELECTRA README-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>
        
4. 레시피 부가 요소 추출한다
    - Rule-Based를 통해 해당 조리 문장에 알맞은 조리도구를 찾아낸다 <a href="https://github.com/iiVSX/lesik/tree/master/Backend#readme">
    <img src="https://img.shields.io/badge/백앤드 README-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>

---
## Python 실행 필수 라이브러리 (requirements.txt)
Backend 필요 라이브러리
- PyMySQL: 데이터베이스 사용을 위해 사용한다
- jamo: microrecipe에서 이루어지는 한글 분석을 위해 사용한다
- Jinja2: Flask에서 프론트로 정보를 보낼때 사용한다
- Flask: 백앤드 API 서버를 위해 사용한다
- urllib3: 데이터 통신을 위해 사용한다

koElectra 필요 라이브러리
- torch==1.10.2
- transformers==4.25.1
- seqeval>=1.2.2
- pandas
---

### 개발자들  (ㄱ-ㄴ-ㄷ)

**김하종** - https://github.com/WhoAmI125

**박지연** - https://github.com/JIGOOOD

**방선웅** - https://github.com/sunwoongskku

**서유정** - https://github.com/hoongel1004

**송지은** - https://github.com/thdwldmszz

**이현민** - https://github.com/lhm6199

### 멘토

박희선 - 성균관대학교 산학협력 및 지도 교수

---

### 관련 링크

<a href="https://docs.google.com/presentation/d/1eMl0jOE0LA6ZvWR7yKkrVwtqXevlYt39/edit#slide=id.p1">
    <img src="https://img.shields.io/badge/발표자료 파워포인트-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>


<a href="https://github.com/iiVSX/lesik/blob/master/KoELECTRA/README.md">
    <img src="https://img.shields.io/badge/KoELECTRA Readme-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>


<a href="https://github.com/sunwoongskku/lesik/blob/master/Crawling/README.md">
    <img src="https://img.shields.io/badge/Crawling Readme-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>


<a href="https://github.com/iiVSX/lesik/tree/master/Backend#readme">
    <img src="https://img.shields.io/badge/Backend Readme-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>

<a href="https://whoami125.notion.site/AWS-EC2-4fc2808f27664eddba10483ccaa127f6">
    <img src="https://img.shields.io/badge/EC2 생성 및 보안 설정-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>
