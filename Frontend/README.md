# Digital Recipe, Micro Recipe & Prompt - Frontend

> 레시피를 입력 받으면 디지털 레시피를 생성 및 분해하고, prompt에서 실시간으로 조리설비별 진행과정을 확인할 수 있는 서비스입니다.


## Getting Started

### How to Run

**To run server:**

```
go to http://ec2-13-209-70-137.ap-northeast-2.compute.amazonaws.com:5000/
```

## Prerequisite
```
node
npm
Jinja2==3.0.3
```


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

## Components
- main.js
  - 레시피를 입력 받아서 디지털 레시피 생성
- microrecipe.js
  - 레시피를 입력 받아서 micro recipe 생성
  - 관형어절로 이루어진 문장을 새로운 시퀀스로 생성 및 동시 동작 처리
- prompt.js
  - 입력 받은 레시피를 쿠킹 프롬프트로 변환
