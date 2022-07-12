import urllib3
import json
import os.path
import re


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


def parse_idiom_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    t_delim = ","
    idiom_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            idiom_dict[sp_line[0]] = sp_line[1].split(t_delim)
    f.close()
    return idiom_dict


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


def remove_redundant_sequence(node, seq_list):
    is_redundant = False
    del_seq_list = []
    redundant_cooking_act_list = ['넣', '놓']
    critical_type_dict = {'NNG', 'VA', 'XPN', 'SP'}

    for morp in node['morp']:
        if morp['type'] == 'VV' and is_redundant == False:
            # 불필요한 조리 동작일 경우
            if morp['lemma'] in redundant_cooking_act_list:
                is_redundant = True
                continue

        if is_redundant:
            # 불필요한 조리 동작 뒤에 연결 어미가 이어질 경우
            if morp['type'] == 'EC':
                continue
            elif morp['type'] in critical_type_dict:
                is_redundant = False
                continue
            else:
                # 불필요한 조리 동작을 제외하면 가능한 경우
                morp_id = morp['id']
                for i in range(1, len(seq_list)):
                    # 현재 형태소가 포함된 시퀀스를 찾아 이전 시퀀스와 병합
                    if seq_list[i]['start_id'] <= morp_id <= seq_list[i]['end_id']:
                        merge_dictionary(seq_list[i-1], seq_list[i])
                        seq_list[i]['start_id'] = seq_list[i-1]['start_id']
                        del_seq_list.append(seq_list[i-1])
                        is_redundant = False
                        break

    # 불필요한 시퀀스 제거
    for seq in del_seq_list:
        seq_list.remove(seq)

    return seq_list


def merge_dictionary(src_dict, dst_dict):
    for key in src_dict.keys():
        if key in dst_dict and key in ['tool', 'ingre', 'seasoning', 'volume']:
            if src_dict.get(key):
                for value in src_dict.get(key):
                    if value not in dst_dict[key]:
                        dst_dict[key].append(value)


def find_omitted_ingredient(node, seq_list, ingredient_dict):
    critical_type_list = ['ARG0', 'ARG1']
    for sequence in seq_list:
        if not sequence['ingre']:
            for srl in node['SRL']:
                s_arg = srl['argument']
                if srl['verb'] == sequence['act']:
                    for s_ele in s_arg:
                        s_text = s_ele['text']
                        s_type = s_ele['type']
                        if s_type in critical_type_list:
                            for ingredient in ingredient_dict.keys():
                                if ingredient in s_text and ingredient not in sequence['ingre'] and ingredient not in sequence['seasoning']:
                                    sequence['ingre'].append(ingredient)
    return seq_list


def mod_check(node, d_ele):
    add_ingre_list = []
    mod_result = None
    for d_element in d_ele['mod']:
        mod_node = node['dependency'][int(d_element)]
        # 관형어
        if mod_node['label'] == 'VP_MOD':
            mod_result = mod_node['text']
        else:
            # 수평 관계에 있는 재료
            if mod_node['label'] == 'NP_CNJ':
                add_ingre_list.append(mod_node['text'])
    return mod_result, add_ingre_list


def find_ingredient_dependency(node, seq_list):
    for d_ele in node['dependency']:
        text = d_ele['text']
        for sequence in seq_list:
            for i in range(0, len(sequence['ingre'])):
                original_ingredient = sequence['ingre'][i]
                if original_ingredient in text:
                    mod_result, additional_ingredient_list = mod_check(node, d_ele)

                    # 관형어
                    if mod_result is not None:
                        sequence['ingre'][i] = mod_result + " " + original_ingredient

                        # 수평적 관계에 있는 재료 (2개면 둘 다 관형어를 붙혀주고, 이외에는 관형어를 처음에만 붙혀준다)
                        if additional_ingredient_list and len(additional_ingredient_list) == 1:
                            for j in range(0, len(sequence['ingre'])):
                                additional_ingredient = sequence['ingre'][j]

                                # 시퀀스의 재료 리스트 중 현재 재료가 아니고 수평적 관계에 있는 재료일 때 관형어를 붙혀준다
                                if i != j and additional_ingredient in additional_ingredient_list[0]:
                                    sequence['ingre'][j] = mod_result + " " + additional_ingredient

    return seq_list


# 관형어 처리
def etm_merge_ingredient(node, sequence_list, ingredient_dict):
    remove_list = []
    for i in range(0, len(sequence_list)):
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
                        for j in range(0, len(sequence_list[i]['ingre'])):
                            if m_ele['lemma'] == sequence_list[i]['ingre'][j]:
                                sequence_list[i]['ingre'][j] = merge_ingre
                                remove_list.append(sequence_list[i-1])
            is_etm = False  
    for verb in sequence_list:
        if verb in remove_list:
            sequence_list.remove(verb)
            
    return sequence_list


# 전성어미 다음 '하고' 생략
def verify_etn(node, seq_list):
    for seq in seq_list:
        for j in range(0, len(node['morp'])-1):
            if node['morp'][j]['type'] == 'ETN':
                    cond_seq = None
                    for seq in seq_list:
                        if seq['start_id'] <= j-1 <= seq['end_id']:
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
def process_cond(node,seq_list):
    del_seq_list = []
    for j in range(0, len(node['morp'])-1):
        if node['morp'][j]['type'] == 'VV':
            if node['morp'][j+1]['lemma'] == "면" or node['morp'][j+1]['lemma'] == "으면":
                cond_seq = None
                for seq in seq_list:
                    if seq['start_id'] <= j <= seq['end_id']:
                        cond_seq = seq
                        continue
                    if cond_seq != None:
                        if len(cond_seq['ingre']) != 0:
                            seq['act'] =  "(" + cond_seq['ingre'][0] + ',' + node['morp'][j]['lemma']+node['morp'][j+1]['lemma']+")" + seq['act']
                        else:
                            seq['act'] = node['morp'][j]['lemma']+node['morp'][j+1]['lemma']
                        seq_list.remove(cond_seq)
                        cond_seq = None
    return seq_list


#숙어처리
def process_phrase(node,seq_list):
    for m_ele in node['morp']:
        if m_ele['type'] == 'VV':
            if m_ele['lemma'] in idiom_dict.keys():
                for w_ele in node['word']:
                    m_id = m_ele['id'] -1
                    if w_ele['begin'] <= m_id <= w_ele['end']:
                        for k in idiom_dict.values():
                            if w_ele['text'] in k:
                                for seq in seq_list:
                                    if seq['start_id'] <= m_ele['id'] <= seq['end_id']:
                                        seq['act'] = w_ele['text'] + " " +seq['act'] 

    return seq_list

  
# 조리동작에 용량 추가
def volume_of_act(node, seq_list):
    for i in range(0, len(node['morp'])-1):
        if node['morp'][i]['lemma'] == 'cm' or node['morp'][i]['lemma'] == '센티' or node['morp'][i]['lemma'] == '센치' or node['morp'][i]['lemma'] == '등분':
            for seq in seq_list:
                if seq['start_id'] <= node['morp'][i]['id'] <= seq['end_id']:
                    seq['act'] = seq['act'] + "(" + node['morp'][i-1]['lemma'] + node['morp'][i]['lemma'] + ")"
    return seq_list


def verify_coref(coref_dict, word):
    if word == '재료':
        return None, None
    for coref_key in coref_dict.keys():
        if word == coref_key or coref_key in word:
            print(coref_key, word, coref_dict[coref_key])
            return coref_key, coref_dict[coref_key]
        if word in coref_key:
            return coref_key, None
        continue
    return None, None


def create_sequence(node, coref_dict, ingredient_dict, ingredient_type_list, recipe_mode):
    # 한 문장
    seq_list = []

    # 형태소 이용한 조리 동작 추출
    prev_seq_id = -1
    for m_ele in node['morp']:
        if m_ele['type'] == 'VV':
            act_id = int(m_ele['id'])
            if node['morp'][act_id + 1]['type'] == 'ETM' and node['morp'][act_id + 2]['lemma'] != '후':
                continue
            act = m_ele['lemma']
        
            # 조리 동작 판단
            if act in cooking_act_dict:
                # 레시피 시퀀스 6가지 요소
                seq_dict = {'cond': "", 'act': act, 'tool': [], 'ingre': [], 'seasoning': [], 'volume': [],
                            'zone': "", "start_id": prev_seq_id + 1, "end_id": act_id, "sentence": ""}
                
                # co-reference 및 dictionary를 통해 word에서 요소 추출
                coref_chk_str = None
                for w_ele in node['word']:
                    if w_ele['begin'] <= prev_seq_id:
                        continue
                    if w_ele['end'] > act_id:
                        break

                    # co-reference 검증
                    if coref_chk_str is None:
                        coref_chk_str = w_ele['text']
                    partial_chk_str, sub_ingredient_dict = verify_coref(coref_dict, coref_chk_str)
                    if sub_ingredient_dict is not None:
                        for key, value in sub_ingredient_dict.items():
                            seq_dict['seasoning'].append(key + "(" + value + ")")
                        coref_chk_str = None
                    else:
                        if partial_chk_str is not None:
                            coref_chk_str += partial_chk_str

                    # 조리 도구 판단
                    for t_ele in tool_list:
                        if t_ele in w_ele['text']:
                            seq_dict['tool'].append(t_ele)

                    # 시즈닝 판단
                    seasoning = ""
                    for s_ele in seasoning_list:
                        if s_ele in w_ele['text']:
                            if len(s_ele) > len(seasoning):
                                seasoning = s_ele
                                
                    if seasoning != "":
                        seq_dict['seasoning'].append(seasoning)

                    # 식자재 판단
                    ingredient = ""
                    for i_ele in ingredient_dict:
                        if i_ele in w_ele['text']:
                            if len(i_ele) > len(ingredient):
                                ingredient = i_ele
                    if ingredient != "" and ingredient not in seq_dict['seasoning'] and ingredient not in seq_dict['ingre']:
                        seq_dict['ingre'].append(ingredient)

                # 조리 도구 명시 되어 있지 않을 때 조리 행위에서 도구 유추
                if seq_dict['tool'] == [] and act in act_to_tool_dict:
                    seq_dict['tool'] = act_to_tool_dict[act]

                seq_list.append(seq_dict)
                prev_seq_id = act_id

    # 개체명 추출을 이용한 시퀀스의 요소 보완
    for sequence in seq_list:
        for ne in node['NE']:
            if ne['type'] in ingredient_type_list and ne['begin'] >= sequence['start_id'] and ne['end'] < sequence['end_id']:
                # 시즈닝과 식자재 중복 제거
                if ne['text'] not in sequence['ingre']:
                    if ne['text'] in seasoning_list:
                        break

                    # 개체명 인식을 통해 추출된 재료에 종속된 재료 삭제
                    sub_ord_ingredient_list = []
                    for ingredient in sequence['ingre']:
                        if ingredient in ne['text']:
                            sub_ord_ingredient_list.append(ingredient)

                    for ingredient in sub_ord_ingredient_list:
                        sequence['ingre'].remove(ingredient)

                    sequence['ingre'].append(ne['text'])

    # 불필요한 시퀀스 제거 및 다음 시퀀스에 병합
    sequence_list = remove_redundant_sequence(node, seq_list)

    if recipe_mode == 'srl':
        # 현재 시퀀스에 누락된 재료를 보완
        sequence_list = find_omitted_ingredient(node, sequence_list, ingredient_dict)

        # 관형어 처리
        sequence_list = find_ingredient_dependency(node, sequence_list)
        
    #조건문 처리함수추가
    #sequence_list = process_cond(node, sequence_list)
    #조리동작(용량)
    #sequence_list = volume_of_act(node, sequence_list)
     # 수식어 + 재료 바꾸기
    #sequence_list = etm_merge_ingredient(node, sequence_list, ingredient_dict)
    # 전성어미 처리
    #sequence_list = verify_etn(node, sequence_list)
    # 숙어처리
    #sequence_list = process_phrase(node, sequence_list)

    #for sequence in sequence_list:
        # 화구존/전처리존 분리
        #select_cooking_zone(sequence)

    for sequence in sequence_list:
        sequence['act'] = cooking_act_dict[sequence['act']]

    return sequence_list


def delete_bracket(text):

    while "(" in text and ")" in text:
        start = text.find('(')
        end = text.find(')')
        if end >= len(text) - 1:
            text = text[0:start]
        else:
            text = text[0:start] + " " + text[end+1:len(text)]
        text = text.strip()

    return text


def parse_node_section(recipe_mode, node_list):
    coref_dict = {}
    volume_type_list = ["QT_SIZE", "QT_COUNT", "QT_OTHERS", "QT_WEIGHT", "QT_PERCENTAGE"]
    ingredient_type_list = ["CV_FOOD", "CV_DRINK", "PT_GRASS", "PT_FRUIT", "PT_OTHERS", "PT_PART", "AM_FISH", "AM_OTHERS"]
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
                coref_dict[sub_type] = {}
            continue
        if is_ingredient:
            sub_ingredient_dict = extract_ingredient_from_node(ingredient_type_list, volume_type_list, node)
            if sub_type is not None:
                coref_dict[sub_type].update(sub_ingredient_dict)
            ingredient_dict.update(sub_ingredient_dict)
        else:
            node['text'] = node['text'].strip()
            # tip 부분 생략하는 조건문
            if len(node['text']) == 0 or "tip" in node['text'].lower():
                remove_node_list.append(node)
                continue
            else:
                node['text'] = delete_bracket(node['text'])

                if len(node['text']) == 0:
                    remove_node_list.append(node)
                    continue
                
            sequence = create_sequence(node, coref_dict, ingredient_dict, ingredient_type_list, recipe_mode)
            if not sequence:
                remove_node_list.append(node)

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
    for node in node_list:
        if node['text'] == '[조리방법]':
            is_dir = True
            continue
        if not is_dir:
            continue

        prev_seq_id = 0
        for i in range(0, len(sequence_list)):
            if sequence_list[i]['sentence'] != "":
                continue
            start_id = sequence_list[i]['start_id']
            end_id = sequence_list[i]['end_id']
            if start_id < prev_seq_id:
                break

            next_seq_id = 0
            if i < len(sequence_list) - 1:
                next_seq_id = sequence_list[i + 1]['start_id']

            word_list = []
            extra_word_list = []
            for w_ele in node['word']:
                text = w_ele['text']
                begin = w_ele['begin']
                end = w_ele['end']
                if start_id <= begin <= end_id:
                    word_list.append(text)
                else:
                    if end_id < end:
                        if next_seq_id < end_id or end < next_seq_id:
                            if not extra_word_list:
                                extra_word_list.append("(")
                            extra_word_list.append(text)
            
            sequence_list[i]['sentence'] = " ".join(word_list)
            sequence_list[i]['sentence'] = delete_bracket(sequence_list[i]['sentence'])
            if extra_word_list:
                extra_word_list.append(")")
                sequence_list[i]['sentence'] += " ".join(extra_word_list)
            prev_seq_id = sequence_list[i]['end_id']


    '''# 후 ~~ 처리하는 코드
    for seq in sequence_list:
        if seq['sentence'][0] == "후" and seq['sentence'][1] == " ":
            seq['sentence'] = seq['sentence'][2:len(seq['sentence'])]'''

    return sequence_list


def main():
    # static params
    open_api_url = "http://aiopen.etri.re.kr:8000/WiseNLU"
    access_key = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
    analysis_code = "SRL"

    # get cooking component list & dictionary from files
    global seasoning_list, volume_list, time_list, temperature_list, cooking_act_dict, act_to_tool_dict, tool_list, fire_tool, fire_zone, preprocess_tool, preprocess_zone, idiom_dict
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
    idiom_dict = parse_idiom_dict("labeling/idiom.txt")

    # recipe extraction
    file_path = input("레시피 파일 경로를 입력해 주세요 : ")
    f = open(file_path, 'r', encoding="utf-8")
    original_recipe = str.join("\n", f.readlines())

    recipe_mode = input("SRL 사용 여부를 입력해주세요 (1 : O, 2 : X) : ")
    if recipe_mode == '1':
        recipe_mode = 'srl'
    elif recipe_mode == '2':
        recipe_mode = 'base'
    else:
        recipe_mode = ''

    f.close()

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

    print(str(json.dumps(sequence_list, ensure_ascii=False)))


if __name__ == "__main__":
    main()
