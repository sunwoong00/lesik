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
├── package-lock.json
├── package.json
├── public
│   ├── favicon.ico
│   ├── index.html
│   ├── logo.png
│   ├── logo192.png
│   ├── logo512.png
│   ├── manifest.json
│   └── robots.txt
└── src
    ├── App.css
    ├── App.js
    ├── App.test.js
    ├── components
    │   ├── Analysis.js
    │   ├── Circlar.js
    │   ├── Contents.js
    │   ├── DatasetSelector.js
    │   ├── Header.js
    │   ├── Line.js
    │   ├── ModelSelector.js
    │   ├── Test.js
    │   └── Visualization.js
    ├── index.css
    ├── index.js
    ├── reportWebVitals.js
    ├── setupTests.js
    └── theme.js
```

<br />

- [App.js](https://github.com/skku-synapse/frontend/blob/main/src/App.js) : root 파일
- 컴포넌트 파일 : frontend/components/ 하위 파일

## Components

- **[ModelSelector.js](https://github.com/skku-synapse/frontend/blob/main/src/components/ModelSelector.js)**
  - Deep Learning 모델을 선택할 수 있는 컴포넌트
  - 현재는 CS-Flow 로 고정되어 있음

<br />

- **[DatasetSelector.js](https://github.com/skku-synapse/frontend/blob/main/src/components/DatasetSelector.js)**
  - Lens, Flex, SMT 데이터 중 하나를 선택하는 컴포넌트

<br />

- **[Line.js](https://github.com/skku-synapse/frontend/blob/main/src/components/Line.js)**
  - Model evaluation 시작 시 progress bar를 제공하는 컴포넌트

<br />

- **[Test.js](https://github.com/skku-synapse/frontend/blob/main/src/components/Test.js)**
  - Test 시작, 중지를 컨트롤하는 버튼 컴포넌트
  - Test가 시작되면 Line 컴포넌트가 작동하여 progress bar 제공

<br />

- **[Visulization.js](https://github.com/skku-synapse/frontend/blob/main/src/components/Visulization.js)**
  - 모델의 예측 결과와 실제 정상/비정상 여부를 이미지로 제공하는 컴포넌트
  - image border가 빨간색 : 예측이 잘못 되었음을 표시
  - 빨간색 채워진 박스 : 실제 비정상
  - 초록색 채워진 박스 : 실제 정상

<br />

- **[Analysis.js](https://github.com/skku-synapse/frontend/blob/main/src/components/Analysis.js)**
  - 예측 결과 표, CS-Flow score histogram 이미지를 API로 제공받아 표시하는 컴포넌트
