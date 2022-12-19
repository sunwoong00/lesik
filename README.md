# 래식: AI 기반 디지털 레시피 자동 생성화

<img src="https://drive.google.com/uc?export=view&id=12ogQey6rqwke_tgX9q2ydozusaihkGYa" alt="drawing" style="width:1280px;"/>

음식 레시피들은 조리하는 데 있어 개인의 해석에 따라 다르게 조리하여 동일한 결과가 나오지 않을 수 있다. 이를 해결하기 위해 디지털 레시피 자동 생성 솔루션을 개발하였다.

---

### 기능

- 디지털 레시피 자동 생성
- 프롬프트 간편화
- Micro Recipe (레시피 분해)

---

### 소프트웨어 아키텍처 구조

<img src="https://drive.google.com/uc?export=view&id=13CTT-zNg8VPJFbfhxuC4eXAENDyJYeMF" alt="drawing" style="width:900px;"/>

---

### 코드 실행 로직

1. 레시피를 입력 받는다
2. 조리동작을 추출한다
    - EtriOpenAPI를 통해 동사(VV)를 분별, 이후 딕션너리를 통해 단순 동사인지 조리동작에 해당하는 동사인지 판단 → 조리동작을 기준으로 sequences 분리 <a href="https://github.com/iiVSX/lesik/tree/master/Backend#readme">
    <img src="https://img.shields.io/badge/로직 방법 설명-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>
3. 레시피 구성 요소들을 추출한다
    - 개체명 인식을 통해 식재료, 용량, 첨가물, 온도, 시간을 추출한다
    - 학습시킨 KoELECTRA를 사용하여 개체명 인식을 진행하고 추가적으로 Rule-based을 통해 발견하지 못한 요소들을 딕션너리를 통해 찾아낸다 <a href="https://github.com/iiVSX/lesik/blob/master/KoELECTRA/model_README.md">
    <img src="https://img.shields.io/badge/KoELECTRA 학습 방법 설명-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>
4. 레시피 부가 요소 추출한다
    - Rule-Based를 통해 해당 조리 문장에 알맞은 조리도구를 찾아낸다 <a href="https://github.com/iiVSX/lesik/tree/master/Backend#readme">
    <img src="https://img.shields.io/badge/로직 방법 설명-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/></a>

---

### 코드 실행 방법

1. 필요한 패키지 준비
    - pip install -r requirements.txt 을 통해 필요한 패키지를 다운 받는다
    - cd Backend → venv/bin/activate을 통해 가상환경을 실행 시킨다
2. cd Backend → python -u ./lesik.py 을 통해 코드를 실행, [http://localhost:5000/](http://localhost:5000/) 로 접속한다

---

### 개발자들  (ㄱ-ㄴ-ㄷ)

**김하종** - Rule-based, 조리도구/조리대 인식, 사이트 구축

**박지연** - 레시피 정보 추출, 딥러닝 기반 개체명 인식기 성능 개선

**방선웅** - 의미역 기반 관계 추출, 용량 인식, 사이트 관리

**서유정** - Rule-based, 조리동작인식사전 구축, 조리규격, 조리설비 인식

**송지은** - Recipe Crawling, 개체명 인식, Prompt UI

**이현민** - Rule-based, 일반 문장 분해, 동시처리 재료 분해

### 멘토

박희선 - 성균관대학교 산학협력 및 지도 교수

---

### 관련 외부 링크

<a href="https://docs.google.com/presentation/d/1eMl0jOE0LA6ZvWR7yKkrVwtqXevlYt39/edit#slide=id.p1">
    <img src="https://img.shields.io/badge/발표자료 파워포인트-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>


<a href="https://github.com/iiVSX/lesik/blob/master/KoELECTRA/model_README.md">
    <img src="https://img.shields.io/badge/KoELECTRA Readme-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>


<a href="https://github.com/iiVSX/lesik/blob/master/Crawling/crawling_README.md">
    <img src="https://img.shields.io/badge/Crawling Readme-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>


<a href="https://github.com/iiVSX/lesik/tree/master/Backend#readme">
    <img src="https://img.shields.io/badge/Backend Readme-<COLOR>"
        style="height : auto; margin-left : 8px; margin-right : 8px;"/>
</a>
