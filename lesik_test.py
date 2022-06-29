from typing import final
from xmlrpc.client import FastMarshaller
import urllib3
import json
import os.path


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
    cooking_act_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            cooking_act_dict[sp_line[0]] = sp_line[1]
        else:
            cooking_act_dict[line] = line
    f.close()
    return cooking_act_dict


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
                    merge_dictionary(seq_list[i-1], seq_list[i])
                    seq_list[i]['start_id'] = seq_list[i-1]['start_id']
                    del_seq_list.append(seq_list[i-1])
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


def mod_recursive(node, d_ele):
    mod_result = ""
    for mod in d_ele['mod']:
        mod_result += mod_recursive(node, node['dependency'][int(mod)])
        mod_result += " "
    return mod_result + d_ele['text']

def mod_check(node, d_ele):
    add_ingre_list = []
    mod_result = None
    for d_element in d_ele['mod']:
        mod_node = node['dependency'][int(d_element)]
        if mod_node['label'] == 'VP_MOD':
            mod_result = mod_recursive(node, mod_node)
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

def etm_merge_ingredient(node, sequence, ingredient_dict):
    # 조리 동작 한줄
    is_etm = False
    etm_id = -1
    for m_ele in node['morp']:
        if m_ele['type'] == 'ETM':
            is_etm = True
            continue
        if is_etm and m_ele['type'] == 'NNG' and m_ele['lemma'] in ingredient_dict:
            for w_ele in node['word']:
                etm_id = m_ele['id'] - 1
                if w_ele['begin'] <= etm_id and w_ele['end'] >= etm_id:
                    merge_ingre = w_ele['text'] + " " + m_ele['lemma']
                    for i in range(0, len(sequence['ingre'])):
                        if m_ele['lemma'] == sequence['ingre'][i]:
                            sequence['ingre'][i] = merge_ingre
        is_etm = False  
            
    return sequence
    
# 화구존, 전처리존 분리             
def select_cooking_zone(sequence):
    #for sequence in seq_list:
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
 

def create_sequence(node, coreference_dict, ingredient_dict, ingredient_type_list, srl_input):
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
                seq_dict = {'cond' : "", 'act': act, 'tool': [], 'ingre': [], 'seasoning': [], 'volume': [],
                            'zone': "", "start_id" : prev_seq_id + 1, "end_id" : act_id, "sentence" : ""}
                
                # insert act
                # find and insert tool
                for w_ele in node['word']:
                    if w_ele['begin'] <= prev_seq_id:
                        continue
                    if w_ele['end'] > act_id:
                        break
                    for coref_key in coreference_dict.keys():
                        if coref_key in w_ele['text']:
                            coref_sub_dict = coreference_dict.get(coref_key);
                            for key in coref_sub_dict.keys():
                                seq_dict['seasoning'].append(key + "(" + coref_sub_dict.get(key) + ")")
                    for t_ele in tool_list:
                        if t_ele in w_ele['text']:
                            seq_dict['tool'].append(t_ele)
                    '''for s_ele in seasoning_list:
                        if s_ele in w_ele['text']:
                            seq_dict['seasoning'].append(s_ele)

                    for i_ele in ingredient_dict:
                        if i_ele in w_ele['text']:
                            seq_dict['ingre'].append(i_ele)'''

                    keep1 = ""
                    flag1 = False
                    for s_ele in seasoning_list:
                        if s_ele in w_ele['text']:
                            if len(s_ele) > len(keep1):
                                keep1 = s_ele
                                flag1 = True
                    if flag1:
                        seq_dict['ingre'].append(keep1)    
                    
                    keep2 = ""
                    flag2 = False
                    for i_ele in ingredient_dict:
                        if i_ele in w_ele['text']:
                            if len(i_ele) > len(keep2):
                                keep2 = i_ele
                                flag2 = True
                    if flag2:
                        seq_dict['ingre'].append(keep2)
                        

                if len(seq_dict['tool']) == 0 and act in act_to_tool_dict:
                    seq_dict['tool'] = act_to_tool_dict[act]

                seq_list.append(seq_dict)
                prev_seq_id = act_id
    #조건문 처리함수추가
    process_cond(node, seq_list)
    
    for sequence in seq_list:
        for ne in node['NE']:
            if ne['type'] in ingredient_type_list and ne['begin'] >= sequence['start_id'] and ne['end'] < sequence['end_id']:
                if ne['text'] not in sequence['ingre']:
                    sequence['ingre'].append(ne['text'])
    
    remove_unnecessary_verb_list = remove_unnecessary_verb(node, seq_list)

    if srl_input == '1': 
        find_omitted_ingredient_list = find_omitted_ingredient(node, remove_unnecessary_verb_list, ingredient_dict)
        for sequence in find_omitted_ingredient_list:
            sequence['act'] = cooking_act_dict[sequence['act']]
        find_ing_dependency_list = find_ing_dependency(node, find_omitted_ingredient_list)

        for sequence in find_ing_dependency_list:
            # 수식어 + 재료 바꾸기
            etm_merge_ingredient(node, sequence, ingredient_dict)
            # 화구존/전처리존 분리
            select_cooking_zone(sequence)
        
        return find_ing_dependency_list
    
    elif srl_input == '2':
        for sequence in remove_unnecessary_verb_list:
            sequence['act'] = cooking_act_dict[sequence['act']]

        for sequence in remove_unnecessary_verb_list:
            # 수식어 + 재료 바꾸기
            etm_merge_ingredient(node, sequence, ingredient_dict)
            # 화구존/전처리존 분리
            select_cooking_zone(sequence)

        return remove_unnecessary_verb_list

def parse_node_section(node_list, srl_input):
    coreference_dict = {}
    volume_type_list = ["QT_SIZE", "QT_COUNT", "QT_OTHERS", "QT_WEIGHT", "QT_PERCENTAGE"]
    ingredient_type_list = ["CV_FOOD", "CV_DRINK", "PT_GRASS", "PT_FRUIT", "PT_OTHERS", "AM_FISH", "AM_OTHERS"]
    ingredient_dict = {}
    sequence_list = []
    is_ingredient = True
    sub_type = None
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
            sequence = create_sequence(node, coreference_dict, ingredient_dict, ingredient_type_list, srl_input)
            for seq_dict in sequence:
                for ingre in seq_dict['ingre']:
                    if ingre in ingredient_dict:
                        seq_dict['volume'].append(ingredient_dict.get(ingre))
                sequence_list.append(seq_dict)
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
                if start_id <= begin and begin <= end_id:
                    seq['sentence'] += text
                    if begin != end_id:
                        seq['sentence'] += " "
            prev_seq_id = seq['end_id']


    # 후 ~~ 처리하는 코드
    for seq in sequence_list:
        if seq['sentence'][0] == "후" and seq['sentence'][1] == " ":
            seq['sentence'] = seq['sentence'][2:len(seq['sentence'])]
            


    print(str(json.dumps(sequence_list, ensure_ascii=False)))

# 조건문 처리
def process_cond(node,seq_list):
    del_seq_list = []
    i=0
    for j in range(0, len(node['morp'])-1):
        if node['morp'][j]['type'] == 'VV':
            i=i+1
            if node['morp'][j+1]['lemma'] == "면" or node['morp'][j+1]['lemma'] == "으면":
                merge_dictionary(seq_list[i-1], seq_list[i])
                seq_list[i]['cond'] = node['morp'][j]['lemma']
                del_seq_list.append(seq_list[i-1])
                seq_list[i]['cond'] = node['morp'][j]['lemma']+node['morp'][j+1]['lemma']
                             
    for seq in del_seq_list:
        seq_list.remove(seq)
          
    return seq_list

def main():
    # static params
    open_api_url = "http://aiopen.etri.re.kr:8000/WiseNLU"
    access_key = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
    analysis_code = "SRL"

    # get cooking component list & dictionary from files
    global seasoning_list, volume_list, time_list, temperature_list, cooking_act_dict, act_to_tool_dict, tool_list, fire_tool, fire_zone, preprocess_tool, preprocess_zone
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

    # recipe extraction
    file_path = input("레시피 파일 경로를 입력해 주세요 : ")
    f = open(file_path, 'r', encoding="utf-8")
    original_recipe = str.join("\n", f.readlines())

    srl_input = input("SRL 사용 여부를 입력해주세요 (1 : O, 2 : X) : ")
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
    sequence_list = parse_node_section(node_list, srl_input)

    sentence_print(node_list, sequence_list)

if __name__ == "__main__":
    main()
