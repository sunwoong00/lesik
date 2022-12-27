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
##### [우리의 식탁 바로가기](https://wtable.co.kr/recipes)
우리의 식탁 레시피를 크롤링 해서 레시피 이름, ~인분, 기본 재료, 양념 재료, 용량, 조리 순서 등을 txt 파일 형식으로 저장합니다.

### 주요 옵션
```
$ python crawling_wtable.py [--recipe_category] [--folder_name]
```
- recipe_category: 크롤링을 진행할 레시피 카테고리입니다. (한식, 중식, 분식 등)
- folder_name: 크롤링 데이터를 저장할 폴더입니다.

### 실행 예시
```
$ python crawling_wtable.py 한식 wtable_korean_recipe
```

### 결과
#### [우리의 식탁 크롤러 예제](https://github.com/iiVSX/lesik/blob/master/Crawling/wtable_korean_recipe/%EA%B0%80%EB%A6%AC%EB%B9%84%EC%B9%BC%EA%B5%AD%EC%88%98.txt)
![crawling_wtable](https://user-images.githubusercontent.com/63731797/209580009-dc4ee1f5-6650-4452-98d3-569c1cd66185.png)


## 만개의 레시피 크롤러
#### [만개의 레시피 바로가기](https://www.10000recipe.com/chef/chef_list.html)
만개의 레시피를 크롤링 해서 조리 순서만 txt 파일 형식으로 저장합니다.

### 주요 옵션
```
$ python crawling_10000recipe.py [--recipe_url] [--folder_name]
```
<li>recipe_url: 크롤링을 진행할 만개의 레시피 쉐프/작성자의 프로필 url입니다.</li>
<li>folder_name: 크롤링 데이터를 저장할 폴더입니다.</li>

### 실행 예시
```
$ python crawling_10000recipe.py https://www.10000recipe.com/profile/recipe.html?uid=bboeonni12 10000_recipe
```

### 결과
![crawling_10000recipe](https://user-images.githubusercontent.com/63731797/209580161-2e5e67bb-b9f5-46d9-9b2f-35dc29d0e4e5.png)
