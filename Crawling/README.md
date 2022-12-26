## 레시피 크롤러

- crawling_wtable: 우리의 식탁 크롤러
- crawling_10000recipe: 만개의 레시피 크롤러

## 환경
- Python(>=3.9)

```
$ pip install selenium
$ pip install bs4
$ pip install urllib3
```

## 우리의 식탁 크롤러
우리의 식탁 레시피를 크롤링 해서 레시피 이름, ~인분, 기본 재료, 양념 재료, 용량, 조리 순서 등을 txt 파일 형식으로 저장합니다.

#### 주요 옵션
```
recipe_category = input("카테고리를 입력해주세요: ")
folder_name = input("폴더명 입력: ")
```
<li>recipe_category: 크롤링을 진행할 레시피 카테고리입니다. (한식, 중식, 분식 등)</li>
<li>folder_name: 크롤링 데이터를 저장할 폴더입니다.</li>

#### 결과
![crawling_wtable](https://user-images.githubusercontent.com/63731797/209580009-dc4ee1f5-6650-4452-98d3-569c1cd66185.png)

## 만개의 레시피 크롤러
만개의 레시피를 크롤링 해서 조리 순서만 txt 파일 형식으로 저장합니다.

#### 주요 옵션
```
recipe_url = input("크롤링을 진행할 쉐프의 프로필 링크를 입력해주세요: ")
folder_name = input("폴더명을 입력해주세요: ")
```
<li>recipe_url: 크롤링을 진행할 만개의 레시피 쉐프/작성자의 프로필 url입니다.</li>
<li>folder_name: 크롤링 데이터를 저장할 폴더입니다.</li>

#### 결과
![crawling_10000recipe](https://user-images.githubusercontent.com/63731797/209580161-2e5e67bb-b9f5-46d9-9b2f-35dc29d0e4e5.png)
