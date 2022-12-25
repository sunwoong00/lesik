# Degital Recipe, Micro Recipe & Prompt - Frontend

> 레시피 입력에 따라 디지털레시피를 생성 및 레시피 분해하고, prompt에서 실시간으로 조리설비별 진행과정을 확인할수 있는 서비스입니다.

## 실행 화면 이미지

<img src="https://drive.google.com/file/d/1DrZqE8B0WagG3NR6_0r_yoR4w1J7mgUr/view?resourcekey" />

<br />

## Getting Started

### How to Run

**To run server:**

```shell script
go to http://ec2-13-209-70-137.ap-northeast-2.compute.amazonaws.com:5000/
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
    │   ├── new_main.css
    │   └── prompt.css
    ├── image
    │   ├── cooksup.png
    │   ├── foodi_logo.png
    │   ├── manual.png
    │   ├── refresh_btn.png
    │   └── res.jpg
    ├── js
    │   ├── main.js
    │   ├── main_backup.js
    │   ├── microrecipe.js
    │   └── prompt.js
    └── templates
        ├── index.html
        ├── index_keep.html
        ├── index_old.html
        ├── manual.html
        ├── prompt.html
        └── prompt_backup.html
```