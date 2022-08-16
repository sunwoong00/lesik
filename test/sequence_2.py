import urllib3
import json
import os.path
import sys
import re

def chk_cooking_section(verb, tool_list) :
    fire_section_type_list = ['볶', '끓이', '튀기', '굽', '조리', '찌', '지지', '데우', '익히']
    fire_section_tool_list = ['냄비', '후라이팬', '프라이팬', '웍', '압력솥', '밥솥', '불판', '석쇠', '튀김기']
    if verb['lemma'] in fire_section_type_list:
        return "화구존"
    for tool in tool_list:
        if tool['lemma'] in fire_section_tool_list:
            return "화구존"
    return "전처리존"

openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"

accessKey = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
analysisCode = "srl"
fileName = input("레시피 파일명을 입력하세요 : ")
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
    verb_helper_list = []
    food_helper_list = []

    morp_dict = {morp['id']: morp for morp in sentence['morp']}
    word_dict = {word['end']: word for word in sentence['word']}

    verb_cnt = 0
    for morp in sentence['morp']:
        if morp['type'] == 'VV':
            morp_id = morp['id'] + 1
            if morp_dict.get(morp_id) and morp_dict.get(morp_id)['type'] == 'ETM':
                if word_dict.get(morp_id):
                    food_helper_list.append(word_dict.get(morp_id))
            else:
                if morp['lemma'] in verb_label_list:
                    verb_list.append(morp)
        elif morp['type'] == 'JKB':
            verb_helper_list.append(word_dict[morp['id']])
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

    if len(verb_list) == 0 and (len(food_list) != 0 or len(volume_list) != 0):
        print("(재료)", sentence['text'])
    elif is_recipe:
        for verb in verb_list:
            if len(food_list) > 0:
                filtered_food_list = []
                for food in food_list:
                    if food['end'] < verb['id']:
                        flag = False
                        for food_helper in food_helper_list:
                            if food_helper['end'] == food['begin'] - 1:
                                filtered_food_list.append(food_helper['text'] + " " + food['text'])
                                flag = True
                        if not flag:
                            filtered_food_list.append(food['text']+"("+food['type']+")")
                if len(filtered_food_list) > 0:
                    print("# 어떤 재료를 : ", str.join(",", filtered_food_list), end=" ")
                filtered_volume_list = list(filter(lambda v: v['end'] < verb['id'], volume_list))
                if len(filtered_volume_list) > 0:
                    print("# 얼마의 용량으로 : ", str.join(",", list(map(lambda v: v['text']+"("+v['type']+")", filtered_volume_list))), end=" ")
                filtered_duration_list = list(filter(lambda d: d['end'] < verb['id'], duration_list))
                if len(filtered_duration_list) > 0:
                    print("# 어느 정도 시간으로 : ", str.join(",", list(map(lambda d: d['text']+"("+d['type']+")", filtered_duration_list))), end=" ")
                filtered_tool_list = list(filter(lambda t: t['id'] < verb['id'], tool_list))
                if len(filtered_tool_list) > 0:
                    print("# 어느 조리 도구로 : ", str.join(",", list(map(lambda t: t['lemma']+"(TOOL)", filtered_tool_list))), end=" ")
                print("# 어떻게 : ", end="")
                for verb_helper in verb_helper_list:
                    if verb_helper['end'] < verb['id']:
                        print(verb_helper['text'], end=" ")
                        verb_helper_list.remove(verb_helper)
                print(verb['lemma'] + "다(ACT)", end=" ")
                print("(", chk_cooking_section(verb, filtered_tool_list), ")")

                for food in food_list:
                    if food['end'] < verb['id'] and len(food_list) > 1:
                        food_list.remove(food)
                for volume in volume_list:
                    if volume['end'] < verb['id']:
                        volume_list.remove(volume)
                for duration in duration_list:
                    if duration['end'] < verb['id']:
                        duration_list.remove(duration)
                for tool in tool_list:
                    if tool['id'] < verb['id'] and len(tool_list) > 1:
                        tool_list.remove(tool)

    else:
        print("(부가정보)", sentence['text'])
    