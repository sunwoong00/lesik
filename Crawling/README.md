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
$ python crawling_wtable.py 한식 wtable_korean_recipe_sample
```

### 결과
#### [우리의 식탁 크롤러 예제](https://github.com/iiVSX/lesik/blob/master/Crawling/wtable_korean_recipe/%EA%B0%80%EB%A6%AC%EB%B9%84%EC%B9%BC%EA%B5%AD%EC%88%98.txt)
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
$ python crawling_10000recipe.py https://www.10000recipe.com/profile/recipe.html?uid=bboeonni12 10000_recipe_sample
```

### 결과
#### [만개의 레시피 크롤러 예제](https://github.com/iiVSX/lesik/blob/master/Crawling/10000_recipe_sample/%EA%B0%88%EC%B9%98%EC%A1%B0%EB%A6%BC.txt)
```
1. 양파는 껍질을 벗겨 씻은 후 채 썰고 풋고추는 꼭지를 제거하고 씻은 후 어슷 썰고 맛타리버섯도 준비합니다.
2. 감자는 껍질을 벗겨 씻은 후 동글동글한 모양으로 도톰하게 썰어줍니다.
3. 분량의 양념장 재료 진간장, 고춧가루, 고추장, 올리고당, 맛술, 다진 마늘, 생강가루, 물을 넣어 고루 섞어줍니다.
4. 은갈치는 흐르는 물에 씻어줍니다.
5. 냄비에 감자를 깔고 갈치, 맛타리버섯, 양파, 풋고추를 얹어줍니다.
6. 양념장을 끼얹어 주고 물을 부은 후 가스 불에 올려 한소끔 끓으면 약 불로 줄여서 조려줍니다. 
중간 중간 양념장 국물을 끼얹어 주면서 조려 주고 양념장 국물이 자박자박해지면 불에서 내려요.
```
