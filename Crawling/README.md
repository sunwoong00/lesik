# 크롤링 설명
## 레시피 크롤러
<li>crawling_wtable: 우리의 식탁 크롤러</li>
<li>crawling_10000recipe: 만개의 레시피 크롤러</li>

## 우리의 식탁 크롤러

###### crawling_wtable.py 이용해서 크롤링을 진행한 예시
<img width="70%" src="https://user-images.githubusercontent.com/63731797/208463522-5093071b-c96f-4d6b-b7d7-480b0b88324b.png"
/>

##### - 레시피 이름, ~인분, 기본재료, 양념재료, 조리 방법 등 추출
<p>1. 크롤링을 진행할 카테고리 입력 (ex.메인요리, 한식, 양식 등) (line 61)</p>
<p>2. 디렉토리 생성 후 디렉토리 이름 입력 (line 32)</p>
<p>3. crawling_wtable.py 실행</p>

## 10000개의 레시피 크롤러

###### crawling_10000table.py 이용해서 크롤링을 진행한 예시
<img width="70%" src="https://user-images.githubusercontent.com/63731797/208465233-2fdcb83b-5b77-499b-850a-6e66ff13be2e.png"/>

##### - 레시피 조리방법 추출
<p>1. 크롤링을 진행할 쉐프/작성자의 프로필 링크 입력 (line 35)</p>
<p>2. 디렉토리 생성 후 디렉토리 이름 입력 (line 12)</p>
<p>3. crawling_10000recipe.py 실행</p>
