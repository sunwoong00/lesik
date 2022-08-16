import urllib3
import json
import os.path
import sys
import re

def chk_cooking_section(verb_list, tool_list) :
    fire_section_type_list = ['볶', '끓이', '튀기', '굽', '조리', '찌', '지지', '데우', '익히']
    fire_section_tool_list = ['냄비', '후라이팬', '프라이팬', '웍', '압력솥', '밥솥', '불판', '석쇠', '튀김기']
    for verb in verb_list:
        if verb['lemma'] in fire_section_type_list:
            return "화구존"
    for tool in tool_list:
        if tool['lemma'] in fire_section_tool_list:
            return "화구존"
    return "전처리존"

openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"

accessKey = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
analysisCode = "ner"
fileName = input("레시피 파일명을 입력하세요")
if not os.path.isfile(fileName):
    print("%s에 해당하는 파일이 존재하지 않습니다" % fileName)
    sys.exit(0)
recipeFile = open(fileName, 'r')
toolFile = open("조리도구.txt", 'r')
volumeFile = open("계량단위.txt", 'r')
verbFile = open("조리방법.txt", 'r')

originalRecipe = recipeFile.read()
volume_label_list = volumeFile.read().split("\n")
tool_label_list = toolFile.read().split("\n")
verb_label_list = verbFile.read().split("\n")

requestJson = {
    "access_key": accessKey,
    "argument": {
        "text": originalRecipe,
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

volume_type_list = ['QT_SIZE', 'QT_COUNT', 'QT_OTHERS', 'QT_WEIGHT',
                    'QT_VOLUME', 'QT_LENGTH', 'QT_PERCENTAGE']
food_type_list = ['CV_FOOD', 'CV_DRINK', 'PT_GRASS', 'PT_FRUIT', 'PT_OTHERS', 'AM_FISH']
duration_type_list = ['TI_DURATION', 'TI_OTHERS', 'TI_HOUR', 'TI_MINUTE', 'TI_SECOND']
if response.status == -1:
    print("ETRI API 서버 통신 중 에러가 발생했습니다.")

original_json = str(response.data, "utf-8")
json_object = json.loads(str(response.data, "utf-8"))
sentence_list = []
ingredient_list = []
recipe_list = []
for sentence in json_object['return_object']['sentence']:
    verb_list = []
    food_list = []
    volume_list = []
    tool_list = []
    duration_list = []
    extra_ne_list = []

    morp_dict = {morp['id']: morp for morp in sentence['morp']}
    word_dict = {word['end']: word for word in sentence['word']}

    verb_cnt = 0
    for morp in sentence['morp']:
        if morp['type'] == 'VV':
            verb_cnt += 1
            if morp['lemma'] in verb_label_list:
                verb_list.append(morp)
        else:
            if morp['lemma'] in tool_label_list:
                tool_list.append(morp)
            else:
                """for volume in volume_label_list:
                    if re.match(volume, morp['lemma'].lower()):
                        volume_list.append(morp)"""
    is_recipe = False
    for ne in sentence['NE']:
        if ne['type'] in food_type_list:
            food_list.append(ne)
        elif ne['type'] in volume_type_list:
            volume_list.append(ne)
        elif ne['type'] in duration_type_list:
            duration_list.append(ne)
        elif ne['type'] == 'QT_ORDER':
            is_recipe = True
        else:
            extra_ne_list.append(ne)

    if verb_cnt == 0 and (len(food_list) != 0 or len(volume_list) != 0):
        print("(재료)", sentence['text'])
    elif is_recipe:
        print("(", chk_cooking_section(verb_list, tool_list), ")", end=" ")
        if len(food_list) > 0:
            print("# 어떤 재료를 : ", str.join(",", list(map(lambda food: food['text'], food_list))), end=" ")
        if len(volume_list) > 0:
            print("# 얼마의 용량으로 : ", str.join(",", list(map(lambda vol: vol['text'], volume_list))), end=" ")
        if len(duration_list) > 0:
            print("# 어느 정도 시간으로 : ", str.join(",", list(map(lambda duration: duration['text'], duration_list))), end=" ")
        if len(tool_list) > 0:
            print("# 어느 조리 도구로 : ", str.join(",", list(map(lambda tool: tool['lemma'], tool_list))), end=" ")
        print("# 어떻게 : ", str.join(",", list(map(lambda verb: verb['lemma']+"다", verb_list))))
    else:
        print("(부가정보)", sentence['text'])
    