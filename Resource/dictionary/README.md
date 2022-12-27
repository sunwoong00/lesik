# Dictionary

> Rule-based 모델에서 사용하는 딕셔너리들입니다.


## 파일 구조

```
.
├── README.md
├── lowclass_dict
│   ├── make_low.txt
│   ├── mix_low.txt
│   ├── prepare_low.txt
│   ├── put_low.txt
│   ├── remove_low.txt
│   ├── slice_low.txt
│   └── useFire_low.txt
├── topclass_dict
│   ├── make_act.txt
│   ├── mix_act.txt
│   ├── prepare_act.txt
│   ├── put_act.txt
│   ├── remove_act.txt
│   ├── slice_act.txt
│   └── useFire_act.txt
├── act_to_tool.txt
├── cooking_act.txt
├── idiom.txt
├── seasoning.txt
├── tool.txt
└── volume.txt
   
```

## Components
- lowclass_dict
  - add_standard 함수에서 사용하는 소분류 딕셔너리
  - make, mix, prepare_ingre, put, remove, slice, useFire 7개의 대분류에 해당하는 소분류 딕셔너리
  '''
  예) slice_low.txt
  어슷
  큐브모양으로
  '''
- topclass_dict
  - classify 함수에서 사용하는 대분류 딕셔너리
  - make, mix, prepare_ingre, put, remove, slice, useFire 7개의 대분류 딕셔너리
  '''
  예) slice_act.txt
  썰다
  슬라이스하다
  '''
- act_to_tool.txt
  - 조리동작과 도구 매칭 딕셔너리
  - create_sequence 함수 내에서 조리도구가 명시 되어 있지 않을 때, 조리 행위에서 도구 유추할때 사용
  '''
  예)
  썰>도마,칼
  볶>주걱
  '''
- cooking_act.txt
  - 동사(VV)가 조리동작인지 인식하기 위한 조리동작 딕셔너리
  - VV>동사원형>3:메인도구 매칭함수>1:도구-동작 매칭함수
  '''
  예)
  끓이>끓이다>3>1
  볶>볶다>3>1
  '''
- idiom.txt
  - '모양을 내다', '밑간을 하다' 와 같은 동사 딕셔너리
  - fine_idiom 숙어처리함수에서 사용 
  '''
  예)
  내>향을,칼집을,토막을,즙을,모양을,구멍을,국물을
  하>밑간을,깍둑썰기,나박썰기,냉장보관,간을,반죽을
  '''
- seasoning.txt
  - ETRI 버전에서 사용하는 첨가물 딕셔너리
  '''
  예)
  소금
  설탕
  '''
- tool.txt
  - 메인 조리도구 딕셔너리
  - create_sequence 함수 내에서 조리도구 판단할때 사용
  - >0,1 : 사용하는 도구
  - >2 : 기계류
  - >3 : 화구 관련
  - >4 : 담는 도구 관련
  '''
  예)
  싱크대>0
  도마, 칼>1
  '''
- volume.txt
  - ETRI 버전에서 사용하는 용량 딕셔너리
  '''
  예)
  쪽
  알
  '''
