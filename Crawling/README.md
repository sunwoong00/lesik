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
$ python crawling_wtable.py 한식 sample_wtable_korean_recipe
```

### 결과
#### [우리의 식탁 크롤러 예제](https://github.com/iiVSX/lesik/tree/master/Crawling/sample_wtable_korean_recipe)
```
가리비칼국수(2~3인분)
[기본재료]
칼국수 면 2인분 (300g)
가리비 (소) 15개
미더덕 (또는 오만둥이) ½컵
감자 1개
양파 ¼개
대파 ⅓개
청양고추 2개
팽이버섯 ½봉 
멸치 새우 다시마 육수 7컵
굵은 천일염 약간
[국물 양념 재료]
국간장 ½큰술
맛술 1큰술
다진 마늘 1작은술
후춧가루 약간
[조리방법]
1. 가리비는 엷은 소금물에 담가 해감한 후 흐르는 물에 조리용 솔로 껍질을 비벼 씻고 미더덕은 깨끗이 씻어 준비해 주세요.
2. 감자는 먹기 좋은 두께로 자르고 양파는 채를 썰어주세요. 팽이버섯은 밑동을 자른 후 먹기 좋게 찢고 대파와 청양고추는 어슷하게 썰어주세요.
3. 냄비에 멸치 새우 다시마 육수를 붓고 끓기 시작하면 감자와 미더덕, 양파, 국물 양념 재료를 넣어 끓여주세요.
4. 감자가 반쯤 익으면 가리비와 칼국수 면을 넣고 3~4분 정도 끓여주세요.
5. 마지막에 대파, 팽이버섯, 청양고추를 넣고 굵은 천일염으로 간을 가감한 후 한소끔 끓인 후 불을 꺼주세요.
```


## 만개의 레시피 크롤러
##### [만개의 레시피 바로가기](https://www.10000recipe.com/chef/chef_list.html)
만개의 레시피를 크롤링 해서 조리 순서만 txt 파일 형식으로 저장합니다.

### 주요 옵션
```
$ python crawling_10000recipe.py [--recipe_url] [--folder_name]
```
<li>recipe_url: 크롤링을 진행할 만개의 레시피 쉐프/작성자의 프로필 url입니다.</li>
<li>folder_name: 크롤링 데이터를 저장할 폴더입니다.</li>

### 실행 예시
```
$ python crawling_10000recipe.py https://www.10000recipe.com/profile/recipe.html?uid=bboeonni12 sample_10000_recipe
```

### 결과
#### [만개의 레시피 크롤러 예제](https://github.com/iiVSX/lesik/blob/master/Crawling/sample_10000_recipe)
```
1. 청양 고추는 꼭지를 제거하고 씻은 후 어슷 썰고 대파는 껍질을 벗겨 씻은 후 어슷 썰어 줍니다.
2. 무는 흐르는 물에 씻은 후 적당한 크기로 썰어 줍니다.
3. 은갈치는 내장과 지느러미를 제거하고 흐르는 물에 깨끗하게 씻어 줍니다.
4. 분량의 양념장 재료 진간장, 고추장, 고춧가루, 맛술, 올리고당, 다진 마늘, 대파, 물을 넣고 양념장을 만들어 줍니다.
5. 냄비 바닥에 무를 고르게 깔고 갈치를 가지런하게 얹은 후 청양 고추와 대파를 올린 다음 양념장을 끼얹어 줍니다. 
양념장 그릇에 묻은 양념은 물을 붓고 흔들어서 부어 주었어요.
6. 가스 불에 올려 끓어오르면 불을 줄이고 간이 고루 배도록 중간 중간 양념장 국물을 끼얹어 가면서 조려 줍니다.
```
