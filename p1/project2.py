# -*- coding:utf-8 -*-
from typing import List, Any

import urllib3
import json
import string

# 언어 분석 기술 문어/구어 중 한가지만 선택해 사용
# 언어 분석 기술(문어)
openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"
accessKey = "98d0c72b-695f-4820-a254-ec68b6897089"
analysisCode = "ner"
text = ""

fire_zone = ['끓', '데워', '볶']
fire_zone_list = []
pre_process_zone = ['걸러', '두르', '넣고', '빼고', '찢', '잘라', '재우.', '썰']
pre_process_zon_list = []


def labeling(i):
    requestJson = {
        "access_key": accessKey,
        "argument": {
            "text": text,
            "analysis_code": analysisCode
        }
    }
    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        openApiURL,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        body=json.dumps(requestJson)
    )

    food_type = ['CV_FOOD', 'CV_DRINK', 'PT_GRASS', 'PT_FRUIT']
    add = ['기름', '간', '핏물', '물', '건미역', '미역', '밑간']
    util = ['냄비', '팬', '체','후라이팬','전자레인지','']
    behavior = ['재우', '썰', '두르', '볶', '넣', '끓이', '넣', '꺼', '조절하', '즐기', '헹구', '사용하', '자르', '빼'
        , '찢', '거르', '하', '담가', ]
    temp = ['중불', '강불', '약불', '중약불', '중강불', '찬물','뜨거운 물','따뜻한 물','약한 불','강한 불']
    size = ['큰''작은', '적당한']
    quantity = ['g', 'mg', 'ml', 'l', '쪽', '알', '컵']
    time = ['분', '초', '시간']
    s_list = []
    main_list = []

    json_load = json.loads(response.data)
    json_sent = json_load.get("return_object").get("sentence")
    for i in json_sent:
        # 식자재, 음식명, 시간
        for wsd in i["WSD"]:
            if wsd["type"] == 'NNG':
                for ne in i["NE"]:
                    # 음식 추가
                    if ne["begin"] == wsd["begin"] and ne['type'] in food_type:
                        for word in i["word"]:
                            if word['begin'] == wsd['begin']:
                                s_list.append(word["text"])
            # 용량 추가
            if wsd["text"] in quantity:
                for word in i["word"]:
                    if word['end'] == wsd['end'] or word['end'] == wsd['end'] + 1:
                        s_list.append(word["text"])
            # 시간 추가
            if wsd["text"] in time:
                for word in i["word"]:
                    if word['end'] == wsd['end']:
                        s_list.append(word["text"])

            # 조리도구 추가
            if wsd["text"] in util:
                for word in i["word"]:
                    if word['begin'] == wsd['begin']:
                        s_list.append(word["text"])
            # add 추가
            if wsd["text"] in add:
                for word in i["word"]:
                    if word['begin'] == wsd['begin']:
                        s_list.append(word["text"])
            # temp 추가
            if wsd["text"] in temp:
                for word in i["word"]:
                    if word['begin'] == wsd['begin']:
                        s_list.append(word["text"])
            # size 추가
            if wsd["text"] in size:
                for word in i["word"]:
                    if word['begin'] == wsd['begin']:
                        s_list.append(word["text"])

            # 마지막에 동사 추가
            elif wsd["type"] == "VV":
                for word in i["word"]:
                    if word['begin'] == wsd['begin'] and wsd['text'] in behavior:
                        s_list.append(word["text"])
                        main_list.append(s_list.copy())
                        s_list.clear()

        print(main_list)
        '''
        for i in main_list:
            string = ' '.join(i)
            for j in fire_zone:
                if j in string:
                    fire_zone_list.append(string)
        '''


# 파일 입력 받기
f = open("C:/Users/82105/Desktop/미역국.txt", 'rt', encoding='UTF8')
lines = []
lines_2 = []
lines = f.readlines()

index = lines.index("[조리방법]\n")
max = len(lines)
k = 1
print("조리 시퀀스")
for i in lines[index + 1: max]:
    text = i
    print(k)
    labeling(text)
    k = k + 1

# 화구존, 전처리존 분리
for i in lines[index + 1: max]:
    result = i[3:len(i)]
    split_list = result.split(',')
    for i in split_list:
        for j in fire_zone:
            if j in i:
                fire_zone_list.append(i)
        for j in pre_process_zone:
            if j in i:
                pre_process_zon_list.append(i)
print("\n")
print("화구존:")
k=1
for i in fire_zone_list:
    print(k, end=". ")
    print(i)
    k=k+1
k=1
print("전처리존:")
for i in pre_process_zon_list:
    if i not in fire_zone_list:
        print(k, end=". ")
        print(i)
        k = k + 1

