# 레시피 개체명 인식 언어 모델(recipe-ner-koelectra)

## **모델 소개**

<img width="100%" src="https://user-images.githubusercontent.com/100189169/209672916-c65b7c5b-d7fe-4cd4-895a-a2c374b2e39e.png"/>

**recipe-ner-koelectra**는 KoELECTRA 모델을 기반으로 만들어진 레시피에 특화된 언어 모델입니다. pre-trained 모델로 [monologg/koelectra-base-v2-discriminator](https://huggingface.co/monologg/koelectra-small-v2-discriminator)를 사용했습니다.

pre-trained 모델에 국어 국립원 모두의 말뭉치의 “개체명 분석 말뭉치 2021”(신문, 구어 약 600만 어절)를 학습 시켜 파인 튜닝의 기반이 될 모델을 만들었습니다. 말뭉치 학습 모델에 우리의 식탁과 만개의 레시피 사이트에서 각각 한식 레시피 482개, 2171개를 파인 튜닝 하여 **recipe-ner-koelectra**를 만들었습니다.

### Model

| Model | Layers | Embedding Size | Hidden Size | # heads |
| --- | --- | --- | --- | --- |
| recipe-ner-koelectra | 12 | 128 | 256 | 4 |

### **Vocabulary**

| Model | Vocal Len | do_lower_case |
| --- | --- | --- |
| recipe-ner-koelectra | 33200 | False |

### **Data**

- 국어 국립원 모두의 말뭉치 “개체명 분석 말뭉치 2021”(신문, 구어 약 600만 어절)
- 우리의 식탁 한식 레시피 482개
- 만개의 레시피 한식 레시피 2171개
- Train : Test = 5393 : 1348 (문장)

### **Pretraining Details**

| Model | Max Len | Train Batch Size | Valid Batch Size | Epochs | Learning Rate | Max Grad Norm |
| --- | --- | --- | --- | --- | --- | --- |
| recipe-ner-koelectra | 256 | 16 | 16 | 72 | 1e-06 | 10 |

### Performance

|  | precision | recall | f1-score |
| --- | --- | --- | --- |
| CV_INGREDIENT | 0.91 | 0.96 | 0.93 |
| CV_SEASONING | 0.89 | 0.93 | 0.91 |
| CV_STATE | 0.87 | 0.94 | 0.90 |
| QT_TEMPERATURE | 0.96 | 0.99 | 0.97 |
| QT_VOLUME | 0.91 | 0.94 | 0.93 |
| TI_DURATION | 0.97 | 0.98 | 0.98 |
- **Test Loss**: 0.11209947447507428
- **Test Accuracy**: 0.972023737294939

## 파일 구조

파일 구조는 다음과 같습니다.

1. **code**
    1. **extra**
        1. **extract_tag**: 태그별로 레이블링이 잘 됐는지 확인하기 위해 인덱스와 개체명과 태그를 추출합니다.
        2. **remove_tip**: 레시피에 포함된 tip 문장을 제거합니다.
            
            ```
            3. 불린 표고는 잘게 썰어주세요. 쪽파는 송송 썰어주세요. 볼에 양념 재료와 잘게 썬 표고를 넣고 섞어주세요. 
            (tip. 표고버섯 4~5개에 물 2컵을 넣고 하루 정도 불려 준비해주세요) <- tip 문장을 제거합니다.
            ```
            
        3. **to_high_performance**: 성능이 안 좋은 데이터셋 증진을 위해 특정 태그가 포함된 문장을 추출합니다.
    2. **fine_tuning**: 기존 모델에 데이터를 추가하여 파인 튜닝 합니다.
    3. **make_recipe_dataset**: 레이블링된 데이터를 학습 데이터로 변환합니다.
    4. **predict_or_tag**: 레시피 데이터를 1차 태깅하거나, 어떤 문장에 대한 모델의 예측 결과를 확인합니다.
    5. **test_model**: 모델의 성능을 평가합니다.
    6. **train_per_epoch**: pre-trained 모델을 만듭니다.
2. **data**
    1. **labeling**: 최종적으로 학습한 train, test recipe dataset을 레이블링한 파일이 있습니다.
    2. **train**: 최종 학습에 사용한 train, test dataset과 우리의 식탁 train, test dataset이 있습니다.
3. **model**: 말뭉치를 학습한 model과 recipe-ner-koelectra의 model이 있습니다.
4. **recipe**: 중식, 한식, 양식 데이터가 있습니다.
    1. **korean**
        1. **labeled**: 레이블링된 레시피 데이터입니다. 만개의 레시피와 우리의 식탁의 레시피가 있습니다. 우리의 식탁의 origin에는 2022.7월에 크롤링한 레시피가, plus에는 2022.11월에 크롤링한 레시피가 있습니다.
        2. **original**: 순수한 레시피 데이터입니다. 이후 정보는 labeled와 동일합니다.
5. **tokenizer**: 말뭉치를 학습한 tokenizer와 recipe-ner-koelectra의 tokenizer가 있습니다.

```
KoELECTRA
 ┣ code
 ┃ ┣ extra
 ┃ ┃ ┣ extract_tag.py
 ┃ ┃ ┣ remove_tip.py
 ┃ ┃ ┗ to_high_performance.py
 ┃ ┣ fine_tuning.ipynb
 ┃ ┣ make_recipe_dataset.ipynb
 ┃ ┣ predict_or_tag.ipynb
 ┃ ┣ test_model.ipynb
 ┃ ┗ train_per_epoch.ipynb
 ┣ data
 ┃ ┣ labeling
 ┃ ┃ ┣ final_test.txt
 ┃ ┃ ┗ final_train.txt
 ┃ ┗ train
 ┃ ┃ ┣ final_test_dataset.tsv
 ┃ ┃ ┣ final_train_dataset.tsv
 ┃ ┃ ┣ wtable_test.tsv
 ┃ ┃ ┗ wtable_train.tsv
 ┣ model
 ┃ ┣ CorpusTrained
 ┃ ┃ ┣ config.json
 ┃ ┃ ┣ model.pt
 ┃ ┃ ┗ pytorch_model.bin
 ┃ ┗ RecipeFinetuning
 ┃ ┃ ┣ config.json
 ┃ ┃ ┣ model.pt
 ┃ ┃ ┗ pytorch_model.bin
 ┣ recipe
 ┃ ┣ chinese
 ┃ ┃ ┣ XO 소스 해물 볶음밥.txt
 ┃ ┃ ┣ ...
 ┃ ┣ korean
 ┃ ┃ ┣ labeled
 ┃ ┃ ┃ ┣ 10000
 ┃ ┃ ┃ ┃ ┣ kimjju.txt
 ┃ ┃ ┃ ┃ ┣ poolhyangi.txt
 ┃ ┃ ┃ ┃ ┣ seungilseunghun.txt
 ┃ ┃ ┃ ┃ ┗ yejib.txt
 ┃ ┃ ┃ ┗ wtable
 ┃ ┃ ┃ ┃ ┣ origin
 ┃ ┃ ┃ ┃ ┃ ┣ test
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ 김치볶음밥.txt
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┃ ┗ train
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ 가리비칼국수.txt
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┗ plus
 ┃ ┃ ┃ ┃ ┃ ┣ test
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ 겨자채 보쌈.txt
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┗ original
 ┃ ┃ ┃ ┣ 10000
 ┃ ┃ ┃ ┃ ┣ 10000_kimjju
 ┃ ┃ ┃ ┃ ┃ ┣ [추석음식] 삼색나물, 시금치•콩나물•고사리나물.txt
 ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┣ 10000_poolhyangi
 ┃ ┃ ┃ ┃ ┃ ┣ [꼬막무침] 새콤달콤 쫄깃쫄깃한 반찬 꼬막무침, 꼬막무침만드는 법, 꼬막삶는 법, 꼬막요리.txt
 ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┣ 10000_seungilseunghun
 ┃ ┃ ┃ ┃ ┃ ┣ [HACCP 인증 제품 활용] 검은콩 돼지고기 비지찌개!!!.txt
 ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┣ 10000_yejib
 ┃ ┃ ┃ ┃ ┃ ┣ 10분 레시피♪ 촉촉한 청경채볶음.txt
 ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┗ wtable
 ┃ ┃ ┃ ┃ ┣ origin
 ┃ ┃ ┃ ┃ ┃ ┣ test
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ 김치볶음밥.txt
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┃ ┗ train
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ 가리비칼국수.txt
 ┃ ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┃ ┃ ┃ ┗ plus
 ┃ ┃ ┃ ┃ ┃ ┣ 가지 냉국 .txt
 ┃ ┃ ┃ ┃ ┃ ┣ ...
 ┃ ┗ western
 ┃ ┃ ┣ BOLT샌드위치.txt
 ┃ ┃ ┣ ...
 ┣ tokenizer
 ┃ ┣ CorpusTrained
 ┃ ┃ ┣ special_tokens_map.json
 ┃ ┃ ┣ tokenizer.json
 ┃ ┃ ┣ tokenizer_config.json
 ┃ ┃ ┗ vocab.txt
 ┃ ┗ RecipeFinetuning
 ┃ ┃ ┣ special_tokens_map.json
 ┃ ┃ ┣ tokenizer.json
 ┃ ┃ ┣ tokenizer_config.json
 ┃ ┃ ┗ vocab.txt
 ┗ README.md
```

## **How To Use**

### 1. **Requirements**

```jsx
torch==1.10.2
transformers==4.25.1
seqeval>=1.2.2
pandas
```

### 2. transformers 라이브러리

recipe-ner-koelectra 모델은 [Hugging Face](https://huggingface.co/JIGOOOD/recipe-ner-koelectra-small)에 업로드 되어 있어 쉽게 사용할 수 있습니다.

```python
from transformers import ElectraForTokenClassification, ElectraTokenizerFast

model = ElectraForTokenClassification.from_pretrained("JIGOOOD/recipe-ner-koelectra-small")
tokenizer = ElectraTokenizerFast.from_pretrained("JIGOOOD/recipe-ner-koelectra-small")
```

### 3. 직접 다운로드

Hugging Face를 사용하지 않고, 직접 모델을 사용하려면 아래 링크를 통해 다운로드할 수 있습니다.

| model | tokenizer |
| --- | --- |
| https://github.com/iiVSX/lesik/tree/master/KoELECTRA/model/RecipeFinetuning | https://github.com/iiVSX/lesik/tree/master/KoELECTRA/tokenizer/RecipeFinetuning |

model과 tokenizer를 저장한 폴더 경로를 아래 load 함수의 각각 model_directory, tokenizer_directory에 넣고, load 함수를 부르면, 해당 경로의 model과 tokenizer를 사용할 수 있습니다.

```python
def load(epoch):
    model_directory = '모델 폴더를 저장한 경로를 붙여 넣어주세요'
    model = ElectraForTokenClassification.from_pretrained(model_directory, num_labels=len(labels_to_ids))

    model.to(device)
    
    tokenizer_directory = '토크나이저 폴더를 저장한 경로를 붙여 넣어주세요'
    tokenizer = ElectraTokenizerFast.from_pretrained(tokenizer_directory)
    
    return model, tokenizer
```

## Reference

- [KoELECTRA](https://towardsdatascience.com/named-entity-recognition-with-bert-in-pytorch-a454405e0b6a)
- [모두의 말뭉치](https://corpus.korean.go.kr/)
- [우리의 식탁](https://wtable.co.kr/store)
- [만개의 레시피](https://www.10000recipe.com/)
