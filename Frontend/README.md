# Digital Recipe, Micro Recipe & Prompt - Frontend

> 레시피를 입력 받으면 디지털 레시피를 생성 및 분해하고, prompt에서 실시간으로 조리설비별 진행과정을 확인할 수 있는 서비스입니다.

## Prerequisite
```
Jinja2==3.0.3
```

## Getting Started

### Clone Repository

    $ git clone https://github.com/iiVSX/lesik.git
    
### Execute code
    1. Python 설치 및 필요한 패키지 준비
        - sudo apt-get update
        - sudo apt-get install python3-venv
        - python3 -m venv venv 을 통해 가상환경을 만든다.
        - pip3 install -r requirements.txt 을 통해 필요한 패키지를 다운 받는다.
        해당 파일은 메인 폴더에 존재한다.
        - cd Backend → venv/bin/activate을 통해 가상환경을 실행 시킨다.
    2. cd Backend → python/python3 -u ./lesik.py 을 통해 코드를 실행, (http://localhost:5000/) 로 접속한다.

## 파일 구조

```
.
├── README.md
├── templates
│   ├── index.html
│   ├── manual.html
│   ├── microrecipe.html
│   └── prompt.html
└── static
    ├── css
    │   ├── microrecipe.css
    │   ├── main.css
    │   └── prompt.css
    ├── image
    │   ├── cooksup.png
    │   ├── foodi_logo.png
    │   ├── manual.png
    │   ├── refresh_btn.png
    │   └── res.jpg
    └── js
        ├── main.js
        ├── microrecipe.js
        └── prompt.js
```

## JS
- main.js
  - 레시피를 입력 받아서 디지털 레시피 생성
- microrecipe.js
  - 레시피를 입력 받아서 micro recipe 생성
  - 관형어절로 이루어진 문장을 새로운 시퀀스로 생성 및 동시 동작 처리
- prompt.js
  - 입력 받은 레시피를 쿠킹 프롬프트로 변환
