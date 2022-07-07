import json
import os.path

import urllib3
from flask import Flask, render_template, request, make_response
import pymysql


def insert_recipe(recipe_name, sentence, json_obj):
    sql_format = "INSERT INTO 0_sentences (recipe_name, sentence, json) VALUES('{recipe_name}', '{sentence}', '{json}')"
    conn = pymysql.connect(
        host='lesik-db.cvjht8t9uwzy.ap-northeast-2.rds.amazonaws.com',
        port=3306,
        user='lesik_2022',
        password='qnstjrgkwk10rodmlfptlvl!',
        db='lesik_main',
    )

    with conn:
        with conn.cursor() as cursor:
            json_obj = conn.escape_string(str(json.dumps(json_obj)))
            sentence = conn.escape_string(sentence)

            query = sql_format.format(recipe_name=recipe_name, sentence=sentence, json=json_obj)
            cursor.execute(query)
            conn.commit()


def get_list_from_file(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(os.getcwd() + "/" + file_path, 'r', encoding='utf-8')
    tmp_list = f.readlines()
    tmp_list = list(map(lambda elem: elem.replace("\n", ""), tmp_list))
    f.close()
    return tmp_list


def parse_cooking_act_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    act_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            act_dict[sp_line[0]] = sp_line[1]
        else:
            act_dict[line] = line
    f.close()
    return act_dict


def parse_act_to_tool_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    t_delim = ","
    act_to_tool_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            act_to_tool_dict[sp_line[0]] = sp_line[1].split(t_delim)
    f.close()
    return act_to_tool_dict


def parse_act_depending_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    t_delim = ","
    act_depending_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            act_depending_dict[sp_line[0]] = sp_line[1].split(t_delim)
    f.close()
    return act_depending_dict


def extract_ingredient_from_node(ingredient_type_list, volume_type_list, node):
    volume_node = None
    ingredient_list = []
    for ne in node['NE']:
        if ne['type'] in volume_type_list:
            volume_node = ne
        if ne['type'] in ingredient_type_list:
            if volume_node is not None and ne['begin'] < volume_node['end']:
                continue
            ingredient_list.append(ne)

    for word in node['word']:
        for volume in volume_list:
            if volume in word['text']:
                volume_node = word

    sub_ingredient_dict = {}
    if volume_node is not None:
        sub_ingredient_dict = {ne['text']: volume_node['text'] for ne in ingredient_list}

    return sub_ingredient_dict


def verify_pre_treated_ingredients(ingredient, pre_treated_ingredient_list):
    return ingredient in pre_treated_ingredient_list


def remove_unnecessary_verb(node, seq_list):
    flag1 = False
    flag2 = False
    del_seq_list = []
    del_type_dict = {'NNG', 'VA', 'XPN', 'SP'}
    for morp in node['morp']:
        if morp['type'] == 'VV':
            if morp['lemma'] == "넣" or morp['lemma'] == "놓":
                flag1 = True
                continue

        if flag1 and morp['type'] == 'EC':
            flag2 = True
            continue

        if flag1 and flag2 and morp['type'] not in del_type_dict:
            morp_id = morp['id']
            for i in range(1, len(seq_list)):
                if seq_list[i] is not None and seq_list[i]['start_id'] <= morp_id <= seq_list[i]['end_id']:
                    merge_dictionary(seq_list[i - 1], seq_list[i])
                    seq_list[i]['start_id'] = seq_list[i - 1]['start_id']
                    del_seq_list.append(seq_list[i - 1])
        flag1 = False
        flag2 = False

    for seq in del_seq_list:
        seq_list.remove(seq)
    return seq_list


def merge_dictionary(src_dict, dst_dict):
    for key in src_dict.keys():
        if key in dst_dict:
            if key in ['tool', 'ingre', 'seasoning', 'volume']:
                if src_dict.get(key) != []:
                    for value in src_dict.get(key):
                        dst_dict[key].append(value)
        else:
            dst_dict[key] = src_dict[key]


def find_omitted_ingredient(node, seq_list, ingredient_dict):
    for sequence in seq_list:
        seq_ing = sequence['ingre']
        seq_seas = sequence['seasoning']
        if len(seq_ing) == 0 and len(seq_seas) == 0:
            for srl in node['SRL']:
                s_arg = srl['argument']
                if srl['verb'] == sequence['act']:
                    for s_ele in s_arg:
                        s_text = s_ele['text']
                        s_type = s_ele['type']
                        if s_type == 'ARG0' or s_type == 'ARG1' or s_type == 'ARGM-MNR':
                            for ing_dict_key in ingredient_dict.keys():
                                if ing_dict_key in s_text:
                                    sequence['ingre'].append(ing_dict_key)

    return seq_list


'''
def mod_recursive(node, d_ele):
    mod_result = ""
    if d_ele['label'] == "VP_MOD":
        for mod in d_ele['mod']:
            mod_result += mod_recursive(node, node['dependency'][int(mod)])
            mod_result += " "
    return mod_result + d_ele['text']
'''


def mod_check(node, d_ele):
    add_ingre_list = []
    mod_result = None
    for d_element in d_ele['mod']:
        mod_node = node['dependency'][int(d_element)]
        if mod_node['label'] == 'VP_MOD':
            mod_result = mod_node['text']
        elif mod_node['label'] == 'NP_CNJ':
            add_ingre_list.append(mod_node['text'])
    return mod_result, add_ingre_list


def find_ing_dependency(node, seq_list):
    mod_result = None
    add_ingre_list = []
    for d_ele in node['dependency']:
        text = d_ele['text']
        for sequence in seq_list:
            for i in range(0, len(sequence['ingre'])):
                if sequence['ingre'][i] in text:
                    mod_result, add_ingre_list = mod_check(node, d_ele)
                    if mod_result is not None:
                        sequence['ingre'][i] = mod_result + " " + sequence['ingre'][i]
        if len(add_ingre_list) != 0:
            for ingre in add_ingre_list:
                for sequence in seq_list:
                    for i in range(0, len(sequence['ingre'])):
                        if sequence['ingre'][i] in ingre and mod_result is not None:
                            sequence['ingre'][i] = mod_result + " " + sequence['ingre'][i]

    return seq_list


# 관형어 처리
def etm_merge_ingredient(node, remove_unnecessary_verb_list, ingredient_dict):
    remove_list = []
    for i in range(0, len(remove_unnecessary_verb_list)):
        is_etm = False
        etm_id = -1
        for m_ele in node['morp']:
            if m_ele['type'] == 'ETM':
                is_etm = True
                continue
            if is_etm and m_ele['type'] == 'NNG' and m_ele['lemma'] in ingredient_dict:
                for w_ele in node['word']:
                    etm_id = m_ele['id'] - 1
                    if w_ele['begin'] <= etm_id <= w_ele['end']:
                        merge_ingre = w_ele['text'] + " " + m_ele['lemma']
                        for j in range(0, len(remove_unnecessary_verb_list[i]['ingre'])):
                            if m_ele['lemma'] == remove_unnecessary_verb_list[i]['ingre'][j]:
                                remove_unnecessary_verb_list[i]['ingre'][j] = merge_ingre
                                remove_list.append(remove_unnecessary_verb_list[i - 1])
            is_etm = False
    for verb in remove_unnecessary_verb_list:
        if verb in remove_list:
            remove_unnecessary_verb_list.remove(verb)

    return remove_unnecessary_verb_list


# 전성어미 다음 '하고' 생략
def verify_etn(node, seq_list):
    for seq in seq_list:
        for j in range(0, len(node['morp']) - 1):
            if node['morp'][j]['type'] == 'ETN':
                cond_seq = None
                for seq in seq_list:
                    if seq['start_id'] <= j - 1 <= seq['end_id']:
                        cond_seq = seq
                        continue
                    if seq['act'] == '하다':
                        seq_list.remove(seq)
                    cond_seq = None
    return seq_list


# 화구존, 전처리존 분리
def select_cooking_zone(sequence):
    if sequence['act'] in fire_zone:
        sequence['zone'] = "화구존"
    for tool in sequence['tool']:
        if tool in fire_tool:
            sequence['zone'] = "화구존"
    if sequence['act'] in preprocess_zone:
        sequence['zone'] = "전처리존"
    for tool in sequence['tool']:
        if tool in preprocess_tool:
            sequence['zone'] = "전처리존"
    return sequence


# 조건문 처리
def process_cond(node, seq_list):
    del_seq_list = []
    for j in range(0, len(node['morp']) - 1):
        if node['morp'][j]['type'] == 'VV':
            if node['morp'][j + 1]['lemma'] == "면" or node['morp'][j + 1]['lemma'] == "으면":
                cond_seq = None
                for seq in seq_list:
                    if seq['start_id'] <= j <= seq['end_id']:
                        cond_seq = seq
                        continue
                    if cond_seq != None:
                        if len(cond_seq['ingre']) != 0:
                            seq['act'] = "(" + cond_seq['ingre'][0] + ',' + node['morp'][j]['lemma'] + \
                                         node['morp'][j + 1]['lemma'] + ")" + seq['act']
                        else:
                            seq['act'] = node['morp'][j]['lemma'] + node['morp'][j + 1]['lemma']
                        seq_list.remove(cond_seq)
                        cond_seq = None
    return seq_list


# 숙어처리
def process_phrase(node, seq_list):
    for m_ele in node['morp']:
        if m_ele['type'] == 'VV':
            if m_ele['lemma'] in act_depending_dict.keys():
                for w_ele in node['word']:
                    m_id = m_ele['id'] - 1
                    if w_ele['begin'] <= m_id <= w_ele['end']:
                        for k in act_depending_dict.values():
                            if w_ele['text'] in k:
                                for seq in seq_list:
                                    if seq['start_id'] <= m_ele['id'] <= seq['end_id']:
                                        seq['act'] = w_ele['text'] + " " + seq['act']

    return seq_list


# 조리동작에 용량 추가
def volume_of_act(node, seq_list):
    for i in range(0, len(node['morp']) - 1):
        if node['morp'][i]['lemma'] == 'cm' or node['morp'][i]['lemma'] == '센티' or node['morp'][i]['lemma'] == '센치' or \
                node['morp'][i]['lemma'] == '등분':
            for seq in seq_list:
                if seq['start_id'] <= node['morp'][i]['id'] <= seq['end_id']:
                    seq['act'] = seq['act'] + "(" + node['morp'][i - 1]['lemma'] + node['morp'][i]['lemma'] + ")"
    return seq_list


def create_sequence(node, coreference_dict, ingredient_dict, ingredient_type_list, recipe_mode):
    # 한 문장
    seq_list = []

    # 조리 동작 한줄
    prev_seq_id = -1
    for m_ele in node['morp']:
        if m_ele['type'] == 'VV':
            act = m_ele['lemma']
            act_id = m_ele['id']
            if act in cooking_act_dict:
                # 6가지 요소
                # 이걸 line에 넣을 것
                seq_dict = {'cond': "", 'act': act, 'tool': [], 'ingre': [], 'seasoning': [], 'volume': [],
                            'zone': "", "start_id": prev_seq_id + 1, "end_id": act_id, "sentence": ""}

                # insert act
                # find and insert tool
                for w_ele in node['word']:
                    if w_ele['begin'] <= prev_seq_id:
                        continue
                    if w_ele['end'] > act_id:
                        break
                    for coref_key in coreference_dict.keys():
                        if coref_key in w_ele['text']:
                            coref_sub_dict = coreference_dict.get(coref_key)
                            for key in coref_sub_dict.keys():
                                seq_dict['seasoning'].append(key + "(" + coref_sub_dict.get(key) + ")")
                    for t_ele in tool_list:
                        if t_ele in w_ele['text']:
                            seq_dict['tool'].append(t_ele)

                    seasoning = ""
                    for s_ele in seasoning_list:
                        if s_ele in w_ele['text']:
                            if len(s_ele) > len(seasoning):
                                seasoning = s_ele

                    if seasoning != "":
                        seq_dict['seasoning'].append(seasoning)

                    ingre = ""
                    for i_ele in ingredient_dict:
                        if i_ele in w_ele['text']:
                            if len(i_ele) > len(ingre):
                                ingre = i_ele
                    if ingre != "" and ingre not in seq_dict['seasoning']:
                        seq_dict['ingre'].append(ingre)

                if len(seq_dict['tool']) == 0 and act in act_to_tool_dict:
                    seq_dict['tool'] = act_to_tool_dict[act]

                seq_list.append(seq_dict)
                prev_seq_id = act_id

    for sequence in seq_list:
        for ne in node['NE']:
            if ne['type'] in ingredient_type_list and ne['begin'] >= sequence['start_id'] and ne['end'] < sequence[
                'end_id']:
                if ne['text'] not in sequence['ingre']:

                    # 소금, 소금
                    if ne['text'] in seasoning_list:
                        break
                    sequence['ingre'].append(ne['text'])
                    # 재료에 달걀, 달걀프라이 중복 빼는 코드
                    for seq_ing in sequence['ingre']:
                        if seq_ing in ne['text'] and seq_ing is not ne['text']:
                            sequence['ingre'].remove(seq_ing)
                            break

    remove_unnecessary_verb_list = remove_unnecessary_verb(node, seq_list)

    if recipe_mode == 'srl':
        find_omitted_ingredient_list = find_omitted_ingredient(node, remove_unnecessary_verb_list, ingredient_dict)
        for sequence in find_omitted_ingredient_list:
            sequence['act'] = cooking_act_dict[sequence['act']]
        find_ing_dependency_list = find_ing_dependency(node, find_omitted_ingredient_list)

        # 조건문 처리함수추가
        process_cond_list = process_cond(node, find_ing_dependency_list)
        # 조리동작(용량)
        volume_of_act_list = volume_of_act(node, process_cond_list)
        # 전성어미 처리
        verify_etn_list = verify_etn(node, volume_of_act_list)

        for sequence in verify_etn_list:
            # 화구존/전처리존 분리
            select_cooking_zone(sequence)

        return verify_etn_list

    elif recipe_mode == 'base':
        for sequence in remove_unnecessary_verb_list:
            sequence['act'] = cooking_act_dict[sequence['act']]

        # 조건문 처리함수추가
        process_cond_list = process_cond(node, remove_unnecessary_verb_list)
        # 조리동작(용량)
        volume_of_act_list = volume_of_act(node, process_cond_list)
        # 수식어 + 재료 바꾸기
        etm_merge_ingredient_list = etm_merge_ingredient(node, volume_of_act_list, ingredient_dict)
        # 전성어미 처리
        verify_etn_list = verify_etn(node, etm_merge_ingredient_list)
        # 숙어처리
        process_phrase_list = process_phrase(node, verify_etn_list)

        for sequence in verify_etn_list:
            # 화구존/전처리존 분리
            select_cooking_zone(sequence)

        return verify_etn_list


def parse_node_section(recipe_mode, node_list):
    coreference_dict = {}
    volume_type_list = ["QT_SIZE", "QT_COUNT", "QT_OTHERS", "QT_WEIGHT", "QT_PERCENTAGE"]
    ingredient_type_list = ["CV_FOOD", "CV_DRINK", "PT_GRASS", "PT_FRUIT", "PT_OTHERS", "PT_PART", "AM_FISH",
                            "AM_OTHERS"]
    ingredient_dict = {}
    sequence_list = []
    is_ingredient = True
    sub_type = None
    remove_node_list = []
    for node in node_list:
        if "[" in node['text'] and "]" in node['text']:
            sub_type = node['text'][1:-1].replace(" ", "")
            if sub_type == '조리방법':
                is_ingredient = False
            else:
                coreference_dict[sub_type] = {}
            continue
        if is_ingredient:
            sub_ingredient_dict = extract_ingredient_from_node(ingredient_type_list, volume_type_list, node)
            if sub_type is not None:
                coreference_dict[sub_type].update(sub_ingredient_dict)
            ingredient_dict.update(sub_ingredient_dict)
        else:
            # tip 부분 생략하는 조건문
            if len(node['text']) == 0 or "tip" in node['text'].lower():
                remove_node_list.append(node)
                continue
            else:
                if "(" in node['text'] and ")" in node['text']:
                    start = node['text'].find('(')
                    end = node['text'].find(')')
                    if end >= len(node['text']) - 3:  # ')'가 문장의 끝에 있을 때 단팥죽 레시피의 경우에 end = 80, len = 83으로 나온다.
                        node['text'] = node['text'][0:start]
                    else:
                        node['text'] = node['text'][0:start] + " " + node['text'][end:len(node['text'])]

                    if len(node['text']) == 0:
                        remove_node_list.append(node)
                        continue

            sequence = create_sequence(node, coreference_dict, ingredient_dict, ingredient_type_list, recipe_mode)
            for seq_dict in sequence:
                for ingre in seq_dict['ingre']:
                    if ingre in ingredient_dict:
                        seq_dict['volume'].append(ingredient_dict.get(ingre))
                sequence_list.append(seq_dict)

    for node in remove_node_list:
        node_list.remove(node)
    return sequence_list


def sentence_print(node_list, sequence_list):
    is_dir = False
    flag = False
    for node in node_list:
        if node['text'] == '[조리방법]':
            is_dir = True
            continue
        if not is_dir:
            continue

        prev_seq_id = 0
        for seq in sequence_list:
            if seq['sentence'] != "":
                continue
            start_id = seq['start_id']
            end_id = seq['end_id']
            if start_id < prev_seq_id:
                break
            for w_ele in node['word']:
                text = w_ele['text']
                begin = w_ele['begin']
                if start_id <= begin <= end_id:
                    if flag == True and start_id == begin:
                        seq['sentence'] += " ) "
                    seq['sentence'] += text
                    if begin != end_id:
                        seq['sentence'] += " "
                '''elif begin < start_id and prev_seq_id < begin:
                    if flag == False:
                        seq['sentence'] += "( " + text
                        flag = True
                        break
                    seq['sentence'] += " " + text'''

            prev_seq_id = seq['end_id']

    # 후 ~~ 처리하는 코드
    for seq in sequence_list:
        if seq['sentence'][0] == "후" and seq['sentence'][1] == " ":
            seq['sentence'] = seq['sentence'][2:len(seq['sentence'])]

    return sequence_list


app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route("/recipe", methods=['POST'])
def recipe():
    recipe_mode = 'base'
    original_recipe = None
    if request.method == 'POST':
        original_recipe = request.form.get("recipe")
        recipe_mode = request.form.get("recipe_mode")

    if original_recipe is None:
        return make_response("Recipe is Blank", 406)

    # static params
    open_api_url = "http://aiopen.etri.re.kr:8000/WiseNLU"
    access_key = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
    analysis_code = "SRL"

    # get cooking component list & dictionary from files
    global seasoning_list, volume_list, time_list, temperature_list, cooking_act_dict, act_to_tool_dict, tool_list, fire_tool, fire_zone, preprocess_tool, preprocess_zone, act_depending_dict
    seasoning_list = get_list_from_file("labeling/seasoning.txt")
    volume_list = get_list_from_file("labeling/volume.txt")
    time_list = get_list_from_file("labeling/time.txt")
    temperature_list = get_list_from_file("labeling/temperature.txt")
    cooking_act_dict = parse_cooking_act_dict("labeling/cooking_act.txt")
    act_to_tool_dict = parse_act_to_tool_dict("labeling/act_to_tool.txt")
    tool_list = get_list_from_file("labeling/tool.txt")
    fire_zone = get_list_from_file("labeling/fire_zone.txt")
    preprocess_zone = get_list_from_file("labeling/preprocess_zone.txt")
    fire_tool = get_list_from_file("labeling/fire_tool.txt")
    preprocess_tool = get_list_from_file("labeling/preprocess_tool.txt")
    act_depending_dict = parse_act_depending_dict("labeling/act_depending.txt")


    # ETRI open api
    requestJson = {
        "access_key": access_key,
        "argument": {
            "text": original_recipe,
            "analysis_code": analysis_code
        }
    }

    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        open_api_url,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        body=json.dumps(requestJson)
    )

    json_object = json.loads(response.data)
    node_list = json_object.get("return_object").get("sentence")
    sequence_list = parse_node_section(recipe_mode, node_list)
    sequence_list = sentence_print(node_list, sequence_list)

    response = json.dumps(sequence_list, ensure_ascii=False)
    return make_response(response)


@app.route("/save", methods=['POST'])
def save():
    if request.method == 'POST':
        data = request.form.get("data")
        if data is not None:
            json_object = json.loads(data)
            for obj in json_object:
                insert_recipe("", obj.get("sentence"), obj)
            return make_response("Success", 200)

    return make_response("Error while storing recipe", 406)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)