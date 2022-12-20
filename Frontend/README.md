# Anomaly Detection Simulator - Frontend

> 렌즈 데이터셋, Flex 데이터셋, SMT 데이터셋에 대한 CS-Flow 모델의 예측 결과를 실시간으로 확인할 수 있는 웹 어플리케이션입니다.  
> 데이터 예측 결과, 실제 양/불량 여부, visualization 결과를 확인할 수 있으며 미검율, 과검율, score histogram 등의 분석 결과를 제공합니다.

## Simulator 화면 이미지

<img src="https://user-images.githubusercontent.com/79344555/208611044-ac9082cc-fd9a-4ae9-adc0-d3017f7a5336.gif" />

<br />

## Prerequisite

`node` (version: 16.15.1)
<br />
`npm`  (version: 8.12.2)
<br />
`react 18` (version: 18.2.0)
<br />

`axios (API 통신)` (version: 0.27.2)

- 기본적으로 fetch가 존재하나 부족한 부분이나 안정성이 결여되어 있어서 채택함.

<br />

`Material-UI` (version: 5.10.0)

- UI library는 mui를 활용하였음.
- Styled-Components를 포함하고 있으며 emotion도 동시에 활용 가능함.
- 더불어 css-in-js 기능도 탁월함.
- 따로 설치가 필요 (아래 command 확인)

<br />

**Install Prerequisite**
```shell script
$ npm install
$ npm install @mui/material
```

<br />

## Getting Started

### Clone Repository

```shell script
$ git clone https://github.com/skku-synapse/frontend.git
$ cd frontend
```

### How to Run

**Installation:**

```
$ npm install
```

**To run in development mode:**

```shell script
$ npm start
```

**To run in production mode:**

```shell script
$ npm run build
$ sudo serve -l [포트번호] -s build
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
