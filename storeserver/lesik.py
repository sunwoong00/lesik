import json
import os.path
import random

import urllib3
from flask import Flask, render_template, request, make_response
import pymysql

import toolmatchwithverb as toolmatchwverb
import version2 as v2

# util
def insert_recipe(recipe_name, sentence, json_obj):
    sql_format = "INSERT INTO 0_sentences (recipe_name, sentence, json) VALUES('{recipe_name}', '{sentence}', '{json}')"
    conn = pymysql.connect(
        host='lesik-db.coqeactzlntd.ap-northeast-2.rds.amazonaws.com',
        port=3306,
        user='lesik',
        password='2022_lesik!',
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


def parse_tool_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    tools = []
    tool_score_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            tool_score_dict[sp_line[0]] = sp_line[1]
            tools.append(sp_line[0])
        else:
            tools.append(line)
    f.close()
    return tools, tool_score_dict


def parse_cooking_act_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    act_dict = {}
    act_score_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            act_dict[sp_line[0]] = sp_line[1]
            act_score_dict[sp_line[1]] = sp_line[2]
        else:
            act_dict[line] = line
    f.close()
    return act_dict, act_score_dict


def parse_act_to_tool_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    t_delim = ","
    act_tool_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            act_tool_dict[sp_line[0]] = sp_line[1].split(t_delim)
    f.close()
    return act_tool_dict


def parse_idiom_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    t_delim = ","
    sub_idiom_dict = {}
    for line in f.readlines():
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            sub_idiom_dict[sp_line[0]] = sp_line[1].split(t_delim)
    f.close()
    return sub_idiom_dict


def parse_parenthesis(line):
    parenthesis_arr = line.split("(")
    ingredient = parenthesis_arr[0]
    volume = parenthesis_arr[1][0:-1]

    return ingredient, volume


def find_similarity(src, dst):
    similarity = 0
    if len(src) > len(dst):
        for d in dst:
            if d in src:
                similarity += 1
    else:
        for s in src:
            if s in dst:
                similarity += 1
    return similarity


def delete_bracket(text):
    while "(" in text and ")" in text:
        start = text.find('(')
        end = text.find(')')
        if end >= len(text) - 1:
            text = text[0:start]
        else:
            text = text[0:start] + " " + text[end + 1:len(text)]
        text = text.strip()

    return text


def merge_dictionary(src_dict, dst_dict):
    for key in src_dict.keys():
        if key in dst_dict and key in ['tool', 'ingre', 'seasoning', 'volume']:
            if src_dict.get(key):
                for value in src_dict.get(key):
                    if value not in dst_dict[key]:
                        dst_dict[key].append(value)


def mod_check(node, d_ele):
    add_ingre_list = []
    mod_result = None
    for d_element in d_ele['mod']:
        mod_node = node['dependency'][int(d_element)]
        # 관형어
        if mod_node['label'] == 'VP_MOD':
            mod_result = mod_node['text']
            for mod_element in mod_node['mod']:
                if node['dependency'][int(mod_element)]['label'] == 'VP':
                    mod_result = node['dependency'][int(mod_element)]['text'] + " " + mod_result
                    break
        else:
            # 수평 관계에 있는 재료
            if mod_node['label'] == 'NP_CNJ':
                add_ingre_list.append(mod_node['text'])
    return mod_result, add_ingre_list


# 조리동작에 용량 추가
def volume_of_act(node, seq_list):
    for i in range(0, len(node['morp']) - 1):
        if node['morp'][i]['lemma'] == 'cm' or node['morp'][i]['lemma'] == '센티' or node['morp'][i]['lemma'] == '센치' or \
                node['morp'][i]['lemma'] == '등분':
            for seq in seq_list:
                if seq['start_id'] <= node['morp'][i]['id'] <= seq['end_id']:
                    seq['act'] = seq['act'] + "(" + node['morp'][i - 1]['lemma'] + node['morp'][i]['lemma'] + ")"
    return seq_list


# function
# 조건문 처리
def find_condition(node, seq_list):
    for srl in node['SRL']:
        s_arg = srl['argument']
        for s_ele in s_arg:
            if s_ele['type'] == "ARGM-CND":
                s_word_id = int(s_ele['word_id'])
                if node['dependency'][s_word_id]['label'] == 'VP':
                    act_plus_sentence = node['dependency'][s_word_id]['text']
                    mod_list = node['dependency'][s_word_id]['mod']
                    for mod in mod_list:
                        mod = int(mod)
                        if node['dependency'][mod]['label'] == 'VP_OBJ':
                            act_plus_sentence = node['dependency'][mod]['text'] + " " + act_plus_sentence
                        if node['dependency'][mod]['label'] == 'NP_SBJ':
                            act_plus_sentence = node['dependency'][mod]['text'] + " " + act_plus_sentence

                    # 방선웅 - 조건문의 동사에서 조리시퀀스가 분리되는 것을 방지
                    for i in range(0, len(seq_list)-1):
                        word = node['word'][s_word_id]
                        begin = word['begin']
                        if seq_list[i]['start_id'] <= begin <= seq_list[i]['end_id']:
                            if seq_list[i]['sentence'][-1] == "면":
                                seq_list[i+1]['act'] = "(" + act_plus_sentence + ")" + seq_list[i+1]['act']
                                seq_list[i+1]['sentence'] = seq_list[i]['sentence'] + " " + seq_list[i+1]['sentence']
                                if seq_list[i]['zone'] == "화구존":
                                    seq_list[i+1]['zone'] = "화구존"
                                del seq_list[i]
                            else:
                                seq_list[i]['act'] = "(" + act_plus_sentence + ")" + seq_list[i]['act']

    return seq_list


def find_ingredient_dependency(node, seq_list, is_srl):
    remove_seq_list = []
    ingredient_modifier_dict = {}
    for i in range(0, len(seq_list)):
        is_etm = False
        is_cooking_act = False
        for m_ele in node['morp']:
            morp_id = m_ele['id']
            morp_type = m_ele['type']
            if morp_id < seq_list[i]['start_id'] or morp_id > seq_list[i]['end_id']:
                continue
            if morp_type == 'ETM':
                is_etm = True
                if morp_id > 0:
                    prev_morp = node['morp'][int(morp_id - 1)]
                    if prev_morp['type'] == 'VV' and prev_morp['lemma'] in cooking_act_dict:
                        is_cooking_act = True
                continue
            if is_etm and morp_type == 'NNG' and m_ele['lemma'] in seq_list[i]['ingre']:
                for w_ele in node['word']:
                    etm_id = morp_id - 1
                    if w_ele['begin'] <= etm_id <= w_ele['end']:
                        modified_ingredient = w_ele['text'] + " " + m_ele['lemma']
                        for j in range(0, len(seq_list[i]['ingre'])):
                            if m_ele['lemma'] == seq_list[i]['ingre'][j]:
                                if i not in ingredient_modifier_dict:
                                    ingredient_modifier_dict[i] = {}
                                ingredient_modifier_dict[i][j] = modified_ingredient
                                if is_cooking_act and i > 0:
                                    remove_seq_list.append(seq_list[i - 1])
            is_etm = False
            is_cooking_act = False

    if is_srl:
        for d_ele in node['dependency']:
            text = d_ele['text']
            for i in range(0, len(seq_list)):
                sequence = seq_list[i]
                for j in range(0, len(sequence['ingre'])):
                    original_ingredient = sequence['ingre'][j]
                    if original_ingredient in text:
                        mod_result, additional_ingredient_list = mod_check(node, d_ele)

                        # 관형어
                        if mod_result is not None:
                            modified_ingredient = mod_result + " " + original_ingredient
                            if i not in ingredient_modifier_dict:
                                ingredient_modifier_dict[i] = {}
                            if j not in ingredient_modifier_dict[i] or len(ingredient_modifier_dict[i][j]) < len(
                                    modified_ingredient):
                                ingredient_modifier_dict[i][j] = modified_ingredient

                            # 수평적 관계에 있는 재료 (2개면 둘 다 관형어를 붙혀주고, 이외에는 관형어를 처음에만 붙혀준다)
                            if additional_ingredient_list and len(additional_ingredient_list) == 1:
                                for k in range(0, len(sequence['ingre'])):
                                    additional_ingredient = sequence['ingre'][k]

                                    # 시퀀스의 재료 리스트 중 현재 재료가 아니고 수평적 관계에 있는 재료일 때 관형어를 붙혀준다
                                    if j != k and additional_ingredient in additional_ingredient_list[0]:
                                        sequence['ingre'][k] = mod_result + " " + additional_ingredient

    for seq_id in ingredient_modifier_dict.keys():
        sequence = seq_list[seq_id]
        for ingredient_idx, modified_ingredient in ingredient_modifier_dict[seq_id].items():
            sequence['ingre'][ingredient_idx] = modified_ingredient

    for seq in remove_seq_list:
        seq_list.remove(seq)

    return seq_list


# 목적어 필수로 하는 조리 동작 처리
def find_objective(node, seq_list):
    for dep in node['dependency']:
        if 'VP' in dep['label']:
            # 추후 목적어의 해당되는 시퀀스의 조리동작에 해당하는 형태소 추출
            word_dep = node['word'][int(dep['id'])]
            start_id = word_dep['begin']
            end_id = word_dep['end']

            # 목적격 수식어 추출
            mod_list = dep['mod']
            for mod in mod_list:
                mod_dep = node['dependency'][int(mod)]
                if "OBJ" in mod_dep['label']:
                    word = node['word'][int(mod_dep['id'])]
                    end = word['end']
                    for i in range(0, len(seq_list)):
                        sequence = seq_list[i]
                        if sequence['start_id'] <= end <= sequence['end_id'] and start_id <= sequence[
                            'end_id'] <= end_id:
                            is_objective = True
                            for ingre in sequence['ingre']:
                                if ingre in word['text']:
                                    is_objective = False
                                    break
                            if is_objective:
                                for seasoning in sequence['seasoning']:
                                    if seasoning in word['text']:
                                        is_objective = False
                                        break

                            if is_objective and word['text'] != "재료를":
                                sequence['act'] = word['text'] + " " + sequence['act']
    return seq_list





# 상상코딩4
# 화구존, 전처리존 분리
def select_cooking_zone(sequence_list):
    fire_tool = ["강판","구이판","압력솥","냄비","찜기","압력솥","냄비","찜기","국자","웍","익덕션","가스레인지","가스렌지","전자레인지","전자렌지","그물국자","돌솥","뒤짚개","배기후드","베이킹 스톤","스테인리스 팬","스킬렛","튀김기","후라이팬","프라이팬","팬","밥솥"]
    preprocess_tool=["냉장고","칼","그릇","도마","볼","접시","거품기","믹싱볼","과자틀","김밥말이","제면기","피자커터","핸드블렌더","믹서기","믹서"]
    preprocess_act = ["즐기다","곁들이다","뿌리다","빚는다","주무르다","두드리다","밀다"]
    #확실한 동작 존 분리
    for i in range(0, len(sequence_list)):
        if sequence_list[i]['top_class'] == "use_fire":
            sequence_list[i]['zone'] = "화구존"
        elif sequence_list[i]['top_class'] == "prepare_ingre" or sequence_list[i]['top_class'] == "slice":  
            sequence_list[i]['zone'] = "전처리존"
        else:
            sequence_list[i]['zone'] = ""
        #전처리존 동작 딕셔너리 확인
        if sequence_list[i]['act'] in preprocess_act:
            sequence_list[i]['zone'] = "전처리존"
        # 도구 매핑   
        for tool in sequence_list[i]['tool']:
            if tool in fire_tool:
                sequence_list[i]['zone'] = "화구존"
            elif tool in preprocess_tool:
                sequence_list[i]['zone'] = "전처리존"
    #애매한 동작 2차분리
    for i in range(0, len(sequence_list)):
        if sequence_list[i]['zone']=="":
            if i == 0:
                j=i
                if i != len(sequence_list)-1:
                    while(j<len(sequence_list)-1):
                        if j==len(sequence_list)-1:
                            if sequence_list[j+1]['zone']=="":
                                sequence_list[i]['zone'] = ""
                                break
                        elif sequence_list[j+1]['zone']=="":
                            j=j+1
                        else:
                            sequence_list[i]['zone']=sequence_list[j+1]['zone']
                            break
                    if sequence_list[i]['zone'] == "":
                        for k in range(0, len(total_sequencelist)):
                            if total_sequencelist[k]['sentence'] == sequence_list[i]['sentence']:
                                while(k>0):
                                        if total_sequencelist[k-1]['zone']=="":
                                            k=k-1
                                        else:
                                            sequence_list[i]['zone']=total_sequencelist[k-1]['zone']
                                            break
                                        if k==0:
                                            sequence_list[i]['zone']="전처리존"
                                            break
                else:
                    for k in range(0, len(total_sequencelist)):
                        if total_sequencelist[k]['sentence'] == sequence_list[i]['sentence']:
                            while(k>0):
                                    if total_sequencelist[k-1]['zone']=="":
                                        k=k-1
                                    else:
                                        sequence_list[i]['zone']=total_sequencelist[k-1]['zone']
                                        break
                                    if k==0:
                                        sequence_list[i]['zone']="전처리존"
                                        break
            elif i==len(sequence_list)-1:
                sequence_list[i]['zone'] = sequence_list[i-1]['zone']
            
            else:
                sequence_list[i]['zone'] = sequence_list[i-1]['zone']
                
        if sequence_list[i]['zone'] == "":
            sequence_list[i]['zone'] = "전처리존"
        
    return sequence_list


# 전성 어미를 통한 동작 추출
def verify_etn(node, seq_list):
    remove_seq_list = []
    for morp in node['morp']:
        if morp['type'] == 'ETN':
            morp_id = int(morp['id'])
            if morp_id > 0:
                prev_morp = node['morp'][morp_id - 1]
                if prev_morp['type'] == 'VV' and prev_morp['lemma'] in cooking_act_dict:
                    for seq_id in range(0, len(seq_list)):
                        sequence = seq_list[seq_id]
                        if sequence['start_id'] <= morp_id <= sequence['end_id']:
                            remove_seq_list.append(sequence)
                            if seq_id < len(seq_list) - 1:
                                next_sequence = seq_list[seq_id + 1]
                                if next_sequence['act'] == '하':
                                    merge_dictionary(sequence, next_sequence)
                                    next_sequence['start_id'] = sequence['start_id']

    for sequence in remove_seq_list:
        seq_list.remove(sequence)

    return seq_list

# 대분류, 중분류
def classify(seq_list):
    for sequence in seq_list:
        if sequence['act'] in slice_act:
            #sequence['act'] = sequence['act']+"(대분류:slice)"
            sequence['top_class']="slice"
        elif sequence['act'] in prepare_ingre:
            #sequence['act'] = sequence['act']+"(대분류:pre_process)"
            sequence['top_class']="prepare_ingre"
        elif sequence['act'] in use_fire:
            #sequence['act'] = sequence['act']+"(대분류:use_fire)"
            sequence['top_class']="use_fire"
        elif sequence['act'] in put:
            #sequence['act'] = sequence['act']+"(대분류:put)"
            sequence['top_class']="put"
        elif sequence['act'] in make:
            #sequence['act'] = sequence['act']+"(대분류:make)"
            sequence['top_class']="make"
        elif sequence['act'] in remove:
            #sequence['act'] = sequence['act']+"(대분류:remove)"
            sequence['top_class']="remove"
        elif sequence['act'] in mix:
            #sequence['act'] = sequence['act']+"(대분류:mix)"
            sequence['top_class']="mix"
       
    return seq_list

#소분류 규격추가

def add_standard(node, seq_list):
    for sequence in seq_list:
        for ne in node['NE']:
            if ne['type'] == "QT_LENGTH" or ne['type'] == "QT_OTHERS" :
                if ne['text'] in sequence['sentence'] and "도" not in ne['text']:
                    if sequence['standard']=="":
                        sequence['standard']=ne['text']
                    else:
                        sequence['standard']=sequence['standard']+","+ne['text']
                        
            if ne['type'] == "QT_ORDER" and '등분' in ne['text']:
                if ne['text'] in sequence['sentence']:
                    if sequence['standard']=="":
                        sequence['standard']=ne['text']
                    else:
                        sequence['standard']=sequence['standard']+","+ne['text']
                        
        if sequence['top_class'] == "slice":
            for i in slice_low_class:
                if i in sequence['sentence']:
                    if sequence['ingre'] != [] and sequence['seasoning'] !=[]:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                for sea in sequence['seasoning']:
                                    if i not in sea:
                                        if i not in sequence['act']:
                                            if sequence['standard']=="":
                                                sequence['standard']=i
                                            else:
                                                sequence['standard']=sequence['standard']+","+i
                                
                    elif sequence['ingre'] != [] and sequence['seasoning'] == []:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                if i not in sequence['act']:
                                    if sequence['standard']=="":
                                        sequence['standard']=i
                                    else:
                                        sequence['standard']=sequence['standard']+","+i
                    elif sequence['ingre'] == [] and sequence['seasoning'] != []:
                        for sea in sequence['seasoning']:
                            if i not in sea:
                                if i not in sequence['act']:
                                    if sequence['standard']=="":
                                        sequence['standard']=i
                                    else:
                                        sequence['standard']=sequence['standard']+","+i
                    else:
                        if i not in sequence['act']:
                            if sequence['standard']=="":
                                sequence['standard']=i
                            else:
                                sequence['standard']=sequence['standard']+","+i
    
        if sequence['top_class'] == "use_fire":
            for i in useFire_low_class:
                if i in sequence['sentence']:
                    if sequence['ingre'] != [] and sequence['seasoning'] !=[]:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                for sea in sequence['seasoning']:
                                    if i not in sea:
                                        if sequence['standard']=="":
                                            sequence['standard']=i
                                        else:
                                            sequence['standard']=sequence['standard']+","+i
                                
                    elif sequence['ingre'] != [] and sequence['seasoning'] == []:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    elif sequence['ingre'] == [] and sequence['seasoning'] != []:
                        for sea in sequence['seasoning']:
                            if i not in sea:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    else:
                        if sequence['standard']=="":
                            sequence['standard']=i
                        else:
                            sequence['standard']=sequence['standard']+","+i
    
        if sequence['top_class'] == "put":
            for i in put_low_class:
                if i in sequence['sentence']:
                    if sequence['ingre'] != [] and sequence['seasoning'] !=[]:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                for sea in sequence['seasoning']:
                                    if i not in sea:
                                        if sequence['standard']=="":
                                            sequence['standard']=i
                                        else:
                                            sequence['standard']=sequence['standard']+","+i
                                
                    elif sequence['ingre'] != [] and sequence['seasoning'] == []:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    elif sequence['ingre'] == [] and sequence['seasoning'] != []:
                        for sea in sequence['seasoning']:
                            if i not in sea:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    else:
                        if sequence['standard']=="":
                            sequence['standard']=i
                        else:
                            sequence['standard']=sequence['standard']+","+i
    
        if sequence['top_class'] == "mix":
            for i in mix_low_class:
                if i in sequence['sentence']:
                    if sequence['ingre'] != [] and sequence['seasoning'] !=[]:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                for sea in sequence['seasoning']:
                                    if i not in sea:
                                        if sequence['standard']=="":
                                            sequence['standard']=i
                                        else:
                                            sequence['standard']=sequence['standard']+","+i
                                
                    elif sequence['ingre'] != [] and sequence['seasoning'] == []:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    elif sequence['ingre'] == [] and sequence['seasoning'] != []:
                        for sea in sequence['seasoning']:
                            if i not in sea:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    else:
                        if sequence['standard']=="":
                            sequence['standard']=i
                        else:
                            sequence['standard']=sequence['standard']+","+i
    
        if sequence['top_class'] == "make":
            for i in make_low_class:
                if i in sequence['sentence']:
                    if sequence['ingre'] != [] and sequence['seasoning'] !=[]:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                for sea in sequence['seasoning']:
                                    if i not in sea:
                                        if sequence['standard']=="":
                                            sequence['standard']=i
                                        else:
                                            sequence['standard']=sequence['standard']+","+i
                            
                    elif sequence['ingre'] != [] and sequence['seasoning'] == []:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    elif sequence['ingre'] == [] and sequence['seasoning'] != []:
                        for sea in sequence['seasoning']:
                            if i not in sea:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    else:
                        if sequence['standard']=="":
                            sequence['standard']=i
                        else:
                            sequence['standard']=sequence['standard']+","+i
                        
        if sequence['top_class'] == "prepare_ingre":
            for i in prepare_low_class:
                if i in sequence['sentence']:
                    if sequence['ingre'] != [] and sequence['seasoning'] !=[]:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                for sea in sequence['seasoning']:
                                    if i not in sea:
                                        if sequence['standard']=="":
                                            sequence['standard']=i
                                        else:
                                            sequence['standard']=sequence['standard']+","+i
                                
                    elif sequence['ingre'] != [] and sequence['seasoning'] == []:
                        for ing in sequence['ingre']:
                            if i not in ing:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    elif sequence['ingre'] == [] and sequence['seasoning'] != []:
                        for sea in sequence['seasoning']:
                            if i not in sea:
                                if sequence['standard']=="":
                                    sequence['standard']=i
                                else:
                                    sequence['standard']=sequence['standard']+","+i
                    else:
                        if sequence['standard']=="":
                            sequence['standard']=i
                        else:
                            sequence['standard']=sequence['standard']+","+i
         
    
    return seq_list
        
# remove, make 대상격 찾는 함수
def find_NP_OBJ(node, seq_list): #지은 수정됨
    
    no_plus_NP_OBJ = ['정도', '크기로', '길이로', '등에', '재료를']
    for dep in node['dependency']:
        if 'VP' in dep['label']:
            # 추후 목적어의 해당되는 시퀀스의 조리동작에 해당하는 형태소 추출
            word_dep = node['word'][int(dep['id'])]
            start_id = word_dep['begin']
            end_id = word_dep['end']

            # 목적격 수식어 추출
            mod_list = dep['mod']
            for mod in mod_list:
                mod_dep = node['dependency'][int(mod)]
                if "NP_OBJ" in mod_dep['label']:
                    word = node['word'][int(mod_dep['id'])]
                    end = word['end']
                    for i in range(0, len(seq_list)):
                        sequence = seq_list[i]
                        if sequence['top_class'] == "remove" or sequence['top_class'] == "make" or sequence['top_class'] == "prepare_ingre" or sequence['act']=="자르다":
                            if sequence['start_id'] <= end <= sequence['end_id'] and start_id <= sequence[
                                'end_id'] <= end_id:
                                is_objective = True
                                for ingre in sequence['ingre']:
                                    if word['text'] in ingre:
                                        is_objective = False
                                        break
                                    if ingre in word['text']:
                                        is_objective = False
                                        break
                                if is_objective:
                                    for seasoning in sequence['seasoning']:
                                        if word['text'] in seasoning:
                                            is_objective = False
                                            break
                                        if seasoning in word['text']:
                                            is_objective = False
                                            break
                                
                                if is_objective:
                                    if word['text'] not in no_plus_NP_OBJ:  # 선웅 수정
                                        sequence['act'] = word['text'] + " " + sequence['act']
                        
    return seq_list

# 상상코딩5
# 동사에 딸려있는 부사구까지 출력 put
def find_adverb(node, sequence_list): #지은 수정됨
    
    no_plus_adverb = ['정도', '크기로', '길이로', '등에']
    for m_ele in node['morp']:
        m_id = int(m_ele['id'])
        if m_id == 0:
            continue
        prev_morp = node['morp'][m_id - 1]
        if m_ele['type'] == 'VV' and m_ele['lemma'] in cooking_act_dict and prev_morp['type'] == "JKB" and prev_morp['lemma'] != "과":
            for i in range(0, len(sequence_list)):
                sequence = sequence_list[i]
                is_adverb = True
                if sequence['start_id'] <= m_id <= sequence['end_id'] and sequence['top_class'] == "put":   
                    for w_ele in node['word']:
                        w_begin = int(w_ele['begin'])
                        w_end = int(w_ele['end'])
                        if w_begin <= int(prev_morp['id']) <= w_end:
                            chk_morp_list = node['morp'][w_begin:w_end + 1]
                            for chk_morp in chk_morp_list:
                                for j in range(0, len(sequence['ingre'])):
                                    if chk_morp['lemma'] in sequence['ingre'][j]:
                                        sequence['ingre'].remove(sequence['ingre'][j])
                                for k in range(0, len(sequence['seasoning'])):
                                    if chk_morp['lemma'] in sequence['seasoning'][k]:
                                        sequence['seasoning'].remove(sequence['seasoning'][k])

                            if node['word'][int(w_ele['id'])]['text'] not in no_plus_adverb:
                                if is_adverb:
                                    for ingre in sequence['ingre']:
                                        if node['word'][int(w_ele['id'])]['text'] in ingre:
                                            is_adverb = False
                                            break
                                if is_adverb:
                                        for seasoning in sequence['seasoning']:
                                            if node['word'][int(w_ele['id'])]['text'] in seasoning:
                                                is_adverb = False
                                                break
                                        for s_tool in sequence_list[i]['tool']:
                                            if s_tool in node['word'][int(w_ele['id'])]['text']:
                                                is_adverb = False
                                                break
                                if is_adverb:
                                    sequence_list[i]['act'] = node['word'][int(w_ele['id'])]['text'] + " " + sequence_list[i]['act']
    
    return sequence_list


def find_idiom(node, sequence_list): #지은 수정됨
    for m_ele in node['morp']:
        m_id = int(m_ele['id'])
        if m_id == 0:
            continue
        prev_morp = node['morp'][m_id - 1]
        if m_ele['type'] == 'VV' and m_ele['lemma'] in idiom_dict.keys():
            for i in range(0, len(sequence_list)):
                sequence = sequence_list[i]
                if sequence['start_id'] <= m_id <= sequence['end_id']:
                    for w_ele in node['word']:
                        w_begin = int(w_ele['begin'])
                        w_end = int(w_ele['end'])
                        if w_begin <= int(prev_morp['id']) <= w_end:
                            sequence_list[i]['act'] = node['word'][int(w_ele['id'])]['text'] + " " + sequence_list[i]['act']
    return sequence_list

def find_omitted_ingredient(node, seq_list, ingredient_dict, mixed_dict):
    critical_type_list = ['ARG0', 'ARG1']
    for sequence in seq_list:
        if not sequence['ingre']:
            for srl in node['SRL']:
                s_arg = srl['argument']
                s_word = node['word'][int(srl['word_id'])]
                if srl['verb'] == sequence['act'] and sequence['start_id'] <= s_word['begin'] <= sequence['end_id']:
                    for s_ele in s_arg:
                        s_text = s_ele['text']
                        s_type = s_ele['type']
                        if s_type in critical_type_list:
                            for ingredient in mixed_dict.keys():
                                if ingredient in s_text and ingredient not in sequence['ingre'] and ingredient not in \
                                        sequence['seasoning']:
                                    sequence['ingre'].append(ingredient) # 박지연 대체 왜 여기로감?? 얘가 시즈닝이면 어쩌려고
    return seq_list

'''
def remove_redundant_sequence(node, seq_list):
    is_redundant = False
    del_seq_list = []
    critical_type_dict = {'NNG', 'NNP', 'VA', 'XPN', 'SP'}

    for morp in node['morp']:
        if morp['type'] == 'VV' and is_redundant is False:
            # 불필요한 조리 동작일 경우
            if morp['lemma'] in cooking_act_dict:
                continue
            next_morp_id = int(morp['id']) + 1
            if next_morp_id == len(node['morp']):
                continue

            next_morp = node['morp'][next_morp_id]
            if next_morp['type'] == 'EC':
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
                        merge_dictionary(seq_list[i - 1], seq_list[i])
                        seq_list[i]['start_id'] = seq_list[i - 1]['start_id']
                        if seq_list[i - 1] not in del_seq_list:
                            del_seq_list.append(seq_list[i - 1])
                        is_redundant = False
                        break

    # 불필요한 시퀀스 제거
    for seq in del_seq_list:
        seq_list.remove(seq)

    return seq_list
'''

def verify_coref(coref_dict, node, word_id):
    word = node['word'][word_id]['text']
    coref_keyword_list = ['밑간', '재료', '소스', '육수', '양념']
    for keyword in coref_keyword_list:
        if keyword in word:
            coref_cand_list = []
            for coref_key in coref_dict.keys():
                if coref_key == '기본재료':
                    continue
                if keyword in coref_key and coref_dict[coref_key] != {}:
                    coref_cand_list.append(coref_key)

            coref_cand = None
            if len(coref_cand_list) >= 1:
                if word_id > 0:
                    prev_word = node['word'][word_id - 1]['text']
                    max_similarity = 0.0

                    for cand in coref_cand_list:
                        comp_word = cand.replace(keyword, "").strip()
                        similarity = find_similarity(comp_word, prev_word)
                        if similarity > max_similarity:
                            coref_cand = cand

            if coref_cand is not None:
                coref_ingredient_dict = coref_dict[coref_cand]
                if coref_ingredient_dict != {}:
                    coref_dict[coref_cand] = {}
                    return coref_ingredient_dict
                return {coref_cand: ""}


def create_sequence(node, coref_dict, ingredient_dict, ingredient_type_list, mixed_dict, entity_mode, is_srl):
    # 한 문장
    seq_list = []

    # 형태소 이용한 조리 동작 추출
    prev_seq_id = -1
    for m_ele in node['morp']:
        if m_ele['type'] == 'VV' or m_ele['lemma'] == '제거':
            if m_ele['type'] == 'VV':
                act_id = int(m_ele['id'])
                if node['morp'][act_id + 1]['type'] == 'ETM' and node['morp'][act_id + 2]['lemma'] != '후':
                    continue
                act = m_ele['lemma']
            elif m_ele['lemma'] == '제거':
                act_id = int(m_ele['id']) 
                if node['morp'][act_id + 2]['type'] == 'ETM' and node['morp'][act_id + 3]['lemma'] != '후':
                    continue
                act = '제거하'
                
            # 조리 동작 판단
            if act in cooking_act_dict:
                # 레시피 시퀀스 6가지 요소
                seq_dict = {'duration': "", 'act': act, 'tool': [], 'ingre': [], 'seasoning': [], 'volume': [], 'temperature': [],
                            'zone': "", "start_id": prev_seq_id + 1, "end_id": act_id, "sentence": "", "standard":"", "top_class":""}

                
                # co-reference 및 dictionary를 통해 word에서 요소 추출
                for w_ele in node['word']:
                    if w_ele['begin'] <= prev_seq_id:
                        continue
                    if w_ele['end'] > act_id:
                        break

                    # co-reference 검증
                    sub_ingredient_dict = verify_coref(coref_dict, node, int(w_ele['id']))
                    if sub_ingredient_dict is not None:
                        for key, value in sub_ingredient_dict.items():
                            '''
                            if len(value) != 0:
                                seq_dict['seasoning'].append(key + "(" + value + ")")
                            else:'''
                            seq_dict['seasoning'].append(key)

                    # 조리 도구 판단
                    for t_ele in tool_list:
                        if t_ele in w_ele['text']:
                            seq_dict['tool'].append(t_ele)

                    # 시즈닝 판단
                    if entity_mode != 'koelectra':
                        seasoning = ""
                        for s_ele in seasoning_list:
                            if s_ele in w_ele['text']:
                                if len(s_ele) > len(seasoning):
                                    seasoning = s_ele

                        if seasoning != "" and seasoning not in seq_dict['seasoning'] and seasoning not in ingredient_dict.keys():
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
    if entity_mode == 'koelectra':
        koelectra_node = extract_ner_from_kobert(node['text'])
        for sequence in seq_list:
            seq_start_offset = len(" ".join(list(map(lambda word: word['text'],
                                                     filter(lambda word: word['begin'] < sequence['start_id'],
                                                            node['word'])))))
            seq_end_offset = len(" ".join(list(map(lambda word: word['text'],
                                                   filter(lambda word: word['begin'] <= sequence['end_id'],
                                                          node['word'])))))
            for ne in koelectra_node['NE']:
                if ne['begin'] >= seq_start_offset and ne['end'] < seq_end_offset:
                    # 시즈닝과 식자재 중복 제거
                    if ne['type'] == 'CV_INGREDIENT':
                        if ne['text'] not in sequence['ingre'] and ne['text'] not in sequence['seasoning']:
                            # 개체명 인식을 통해 추출된 재료에 종속된 재료 삭제
                            sub_ord_ingredient_list = []
                            for ingredient in sequence['ingre']:
                                if ingredient in ne['text']:
                                    sub_ord_ingredient_list.append(ingredient)

                            for ingredient in sub_ord_ingredient_list:
                                sequence['ingre'].remove(ingredient)

                            sequence['ingre'].append(ne['text'])
                    # 박지연
                    if ne['type'] == 'CV_SEASONING':
                        if ne['text'] not in sequence['seasoning'] and ne['text'] not in sequence['ingre']:
                            sequence['seasoning'].append(ne['text'])
                    if ne['type'] == 'TI_DURATION':
                        if len(sequence['duration'])!= 0:
                            if '0' <= sequence['duration'][-1] and sequence['duration'][-1] <= '9':
                                sequence['duration'] += "~" + ne['text']
                        else:
                            sequence['duration'] += ne['text']
    else:
        for sequence in seq_list:
            for ne in node['NE']:
                if ne['begin'] >= sequence['start_id'] and ne['end'] < sequence['end_id']:
                    if ne['type'] in ingredient_type_list:
                        # 시즈닝과 식자재 중복 제거
                        if ne['text'] not in sequence['ingre'] and ne['text'] not in sequence['seasoning']:
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
                    else:
                        if ne['type'] == 'TI_DURATION':
                            sequence['duration'] = ne['text']
    
    # 불필요한 시퀀스 제거 및 다음 시퀀스에 병합
    # sequence_list = remove_redundant_sequence(node, seq_list)
    sequence_list = seq_list

    if is_srl:
        # 현재 시퀀스에 누락된 재료를 보완
        sequence_list = find_omitted_ingredient(node, sequence_list, ingredient_dict, ingredient_dict)

        # 조리동작(용량)
        # sequence_list = volume_of_act(node, sequence_list)
        # 전성어미 처리
        sequence_list = verify_etn(node, sequence_list)

    for sequence in sequence_list:
        sequence['act'] = cooking_act_dict[sequence['act']]

    # 화구존/전처리존 분리
    #sequence_list = select_cooking_zone(sequence_list)

    if is_srl and entity_mode == 'koelectra':
        # 목적어를 필수로 하는 조리 동작 처리
        #sequence_list = find_objective(node, sequence_list)

        # 관형어 처리
        sequence_list = find_ingredient_dependency(node, sequence_list, is_srl)

        # 조건문 처리함수추가
        #sequence_list = find_condition(node, sequence_list)

    # sentence 찾기
    sequence_list = find_sentence(node, sequence_list)

    if entity_mode == 'koelectra':
        '''seq_start_offset = len(" ".join(list(map(lambda word: word['text'],
                                                     filter(lambda word: word['begin'] < sequence['start_id'],
                                                            node['word'])))))
        seq_end_offset = len(" ".join(list(map(lambda word: word['text'],
                                                   filter(lambda word: word['begin'] <= sequence['end_id'],
                                                          node['word'])))))'''
        # 온도 판단 - 선웅 수정
        for ne in koelectra_node['NE']:
            if ne['type'] == 'QT_TEMPERATURE':
                for sequence in seq_list:
                    if ne['text'] in sequence['sentence']:
                        sequence['temperature'] = ne['text']

        '''# 시간 판단 - 선웅 수정
        for sequence in seq_list:
            for ne in koelectra_node['NE']:
                if ne['begin'] >= seq_start_offset and ne['end'] < seq_end_offset:
                    if ne['type'] == 'TI_DURATION' and ne['text'] in sequence['sentence']:
                            if len(sequence['duration'])!= 0:
                                if '0' <= sequence['duration'][-1] and sequence['duration'][-1] <= '9':
                                    sequence['duration'] += "~" + ne['text']
                            else:
                                sequence['duration'] += ne['text']'''

    # 동사 분류
    sequence_list = classify(sequence_list)

    # 소분류 규격 추가
    sequence_list = add_standard(node, sequence_list)
    for sequence in sequence_list:
        total_sequencelist.append(sequence)
    
    # 화구존/전처리존 분리
    sequence_list = select_cooking_zone(sequence_list)

    # put, remove, make 대상격 찾는 함수
    sequence_list = find_NP_OBJ(node, sequence_list)
 
    # 동작에 딸려오는 부사구 출력
    sequence_list = find_adverb(node, sequence_list)
    # 숙어
    sequence_list = find_idiom(node, sequence_list)

    # 시퀀스 병합
    sequence_list = merge_sequence(sequence_list)
    
    # 조건문 처리함수추가
    sequence_list = find_condition(node, sequence_list)

    return sequence_list

# 조리 시퀀스 병합 (넣다와 넣다 뒤에 나오는 동사 병합) - 박지연
def merge_sequence(sequence_list):
    
    '''
    sequence example: {'duration': '', 'act': '썰다', 'tool': ['도마', '칼'], 'ingre': ['어묵', '양파', '청피망'], 'seasoning': [], 'volume': [], 
                        'temperature': [], 'zone': '전처리존', 'start_id': 0, 'end_id': 11, 'sentence': '1. 어묵과 양파, 청피망은 얇게 채 썰고', 
                        'standard': '얇게,채', 'top_class': 'slice'}
    1. 동사가 똑같으면 합침: duration, ingre, seasoning, volume, temperature를 앞쪽 시퀀스에 넣음 (도구는 그대로)
    2. 
    '''

    len_of_list = len(sequence_list)
    #print("수정 전")
    #print(sequence_list)
    for seq_idx in range(len_of_list - 1):
        # 동사가 똑같은 경우
        if sequence_list[seq_idx] and sequence_list[seq_idx + 1] and sequence_list[seq_idx]["act"] == sequence_list[seq_idx + 1]["act"]:
            if sequence_list[seq_idx + 1]["duration"] != '': # 시간 병합
                sequence_list[seq_idx]["duration"] = sequence_list[seq_idx]["duration"] + "<br>" + sequence_list[seq_idx + 1]["duration"]

            if sequence_list[seq_idx + 1]["ingre"]: # 식자재 병합
                [sequence_list[seq_idx]["ingre"].append(ingre_part) for ingre_part in sequence_list[seq_idx + 1]["ingre"]]

            if sequence_list[seq_idx + 1]["seasoning"]: # 첨가물 병합
                [sequence_list[seq_idx]["seasoning"].append(sea_part) for sea_part in sequence_list[seq_idx + 1]["seasoning"]]

            if sequence_list[seq_idx + 1]["volume"]: # 용량 병합
                [sequence_list[seq_idx]["volume"].append(vol_part) for vol_part in sequence_list[seq_idx + 1]["volume"]]

            if sequence_list[seq_idx + 1]["temperature"]: # 온도 병합
                #[sequence_list[seq_idx]["temperature"].append(tem_part) for tem_part in sequence_list[seq_idx + 1]["temperature"]]
                sequence_list[seq_idx]["temperature"] = sequence_list[seq_idx + 1]["temperature"]
                
            sequence_list[seq_idx]["end_id"] = sequence_list[seq_idx + 1]["end_id"] # end_id update
            sequence_list[seq_idx]["sentence"] = sequence_list[seq_idx]["sentence"] + " " + sequence_list[seq_idx + 1]["sentence"] # 원문 update

            if sequence_list[seq_idx + 1]["standard"] != '': # 규격 병합
                sequence_list[seq_idx]["standard"] = sequence_list[seq_idx]["standard"] + "<br>" + sequence_list[seq_idx + 1]["standard"]

            del sequence_list[seq_idx + 1] # 리스트 요소 삭제
            sequence_list.append([]) # list index out of range 방지 위해 마지막에 빈 시퀀스 삽입


        # 현 동사가 "넣다"이고, 이후 동사가 다른 동사인 경우
        if sequence_list[seq_idx] and sequence_list[seq_idx + 1] and sequence_list[seq_idx]["act"] == "넣다" and sequence_list[seq_idx]["sentence"].find("요.") == -1:
            sequence_list[seq_idx]["act"] = sequence_list[seq_idx + 1]["act"] # 뒤의 동사만 남김
            
            if sequence_list[seq_idx + 1]["tool"]: # 도구 병합
                for tool in sequence_list[seq_idx + 1]["tool"]:
                    if tool not in sequence_list[seq_idx]["tool"]:
                        sequence_list[seq_idx]["tool"].append(tool)

            if sequence_list[seq_idx + 1]["duration"] != '': # 시간 병합
                sequence_list[seq_idx]["duration"] = sequence_list[seq_idx]["duration"] + " " + sequence_list[seq_idx + 1]["duration"]

            if sequence_list[seq_idx + 1]["ingre"]: # 식자재 병합
                [sequence_list[seq_idx]["ingre"].append(ingre_part) for ingre_part in sequence_list[seq_idx + 1]["ingre"]]

            if sequence_list[seq_idx + 1]["seasoning"]: # 첨가물 병합
                [sequence_list[seq_idx]["seasoning"].append(sea_part) for sea_part in sequence_list[seq_idx + 1]["seasoning"]]

            if sequence_list[seq_idx + 1]["volume"]: # 용량 병합
                [sequence_list[seq_idx]["volume"].append(vol_part) for vol_part in sequence_list[seq_idx + 1]["volume"]]

            if sequence_list[seq_idx + 1]["temperature"]: # 온도 병합
                #[sequence_list[seq_idx]["temperature"].append(tem_part) for tem_part in sequence_list[seq_idx + 1]["temperature"]]
                sequence_list[seq_idx]["temperature"] = sequence_list[seq_idx + 1]["temperature"]
                
            if sequence_list[seq_idx + 1]["standard"] != '': # 규격 병합
                sequence_list[seq_idx]["standard"] = sequence_list[seq_idx]["standard"] + sequence_list[seq_idx + 1]["standard"]


            sequence_list[seq_idx]["zone"] = sequence_list[seq_idx + 1]["zone"] # zone update


            sequence_list[seq_idx]["end_id"] = sequence_list[seq_idx + 1]["end_id"] # end_id update

            sequence_list[seq_idx]["sentence"] = sequence_list[seq_idx]["sentence"] + " " + sequence_list[seq_idx + 1]["sentence"] # 원문 update

            sequence_list[seq_idx]["top_class"] = sequence_list[seq_idx + 1]["top_class"] # 대분류 update


            # merge 하는 시퀀스에 들어있는 재료, 첨가물이 겹칠 때 하나만 처리하게 해주는 코드 - 방선웅
            if 2 <= len(sequence_list[seq_idx]["ingre"]):
                for i in range(0, len(sequence_list[seq_idx]["ingre"])-1):
                    for j in range(i+1, len(sequence_list[seq_idx]["ingre"])):
                        if sequence_list[seq_idx]["ingre"][i] == sequence_list[seq_idx]["ingre"][j]:
                            del sequence_list[seq_idx]["ingre"][j]

            if 2 <= len(sequence_list[seq_idx]["seasoning"]):
                for i in range(0, len(sequence_list[seq_idx]["seasoning"])-1):
                    for j in range(i+1, len(sequence_list[seq_idx]["seasoning"])):
                        if sequence_list[seq_idx]["seasoning"][i] == sequence_list[seq_idx]["seasoning"][j]:
                            del sequence_list[seq_idx]["seasoning"][j]

            
            del sequence_list[seq_idx + 1] # 리스트 요소 삭제
            sequence_list.append([]) # list index out of range 방지 위해 마지막에 빈 시퀀스 삽입
    
    sequence_list = list(filter(None, sequence_list))
    #print("수정 후")
    #print(sequence_list)
    return sequence_list

def extract_ner_from_kobert(sentence):
    kobert_api_url = "http://ec2-13-209-68-59.ap-northeast-2.compute.amazonaws.com:5000"

    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        kobert_api_url,
        headers={"Content-Type": "application/text; charset=UTF-8"},
        body=sentence.encode('utf-8')
    )

    json_object = json.loads(response.data)

    return json_object


# 박지연 이 코드 이상함
# 기본 재료에서 재료랑 용량을 매핑하는 코드
def extract_ingredient_from_node(ingredient_type_list, volume_type_list, node):
    
    # node에 재료부분 한줄한줄(청양고추 40개)에 대한 etri 분석 결과가 들어옴
    volume_node = []
    ingredient_list = []
    sub_ingredient_dict = {}
    ingredient_text_list = []

    for ne in node['NE']:
   
        if ne['type'] in volume_type_list and len(volume_node) == 0: # 선웅 추가 (용량 1가지만 나오게)
            volume_node.append(ne)
        if ne['type'] in ingredient_type_list:
            if volume_node and ne['begin'] < volume_node[-1]['end']:
                continue
            ingredient_list.append(ne)
            ingredient_text_list.append(ne['text'])

    if not volume_node:
        if 'word' in node:
            for word in node['word']:
                for volume in volume_list:
                    if volume in word['text'] and word['text'] not in ingredient_text_list and len(volume_node) == 0: # 선웅 추가 (용량 1가지만 나오게)
                        volume_node.append(word)

    sub_ingredient_dict = {}
    if volume_node is not None:
        volume_node_list = set()
        for v_node in volume_node:
            volume_node_list.add(v_node['text'])
        sub_ingredient_dict = {ne['text']: "".join(list(map(lambda v: v, volume_node_list))) for ne in ingredient_list}

    return sub_ingredient_dict

def parse_node_section(entity_mode, is_srl, node_list):
    coref_dict = {}
    volume_type_list = ["QT_SIZE", "QT_COUNT", "QT_OTHERS", "QT_WEIGHT", "QT_PERCENTAGE"]
    ingredient_type_list = ["CV_FOOD", "CV_DRINK", "PT_GRASS", "PT_FRUIT", "PT_OTHERS", "PT_PART", "AM_FISH",
                            "AM_OTHERS", "CV_INGREDIENT", "CV_SEASONING"]
    ingredient_dict = {}
    mixed_dict = {}
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
            '''if entity_mode == 'koelectra': 재료,첨가물에 대한 용량 추출
                koelectra_node = extract_ner_from_kobert(node['text'])
                if koelectra_node is not None:
                    sub_ingredient_dict = extract_ingredient_from_node(ingredient_type_list, volume_type_list, koelectra_node)
                else:
                    sub_ingredient_dict = None
            else:'''
            sub_ingredient_dict = extract_ingredient_from_node(ingredient_type_list, volume_type_list, node)

            # 박지연
            # 기본 재료가 모두 식자재 딕셔너리로 들어가는 문제 해결하는 코드
            if sub_ingredient_dict:
                if sub_type:
                    coref_dict[sub_type].update(sub_ingredient_dict)
                    # sub_ingredient_dict 이상함
                    mixed_dict.update(sub_ingredient_dict)

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

            sequence = create_sequence(node, coref_dict, ingredient_dict, ingredient_type_list, mixed_dict, entity_mode, is_srl)
            if not sequence:
                remove_node_list.append(node)

            # 방선웅-----------수정중--------------
            for seq_dict in sequence:
                # 기본 재료에 나오는 식자재와 용량 매핑
                for ingre in seq_dict['ingre']:
                    if ingre in mixed_dict:
                        seq_dict['volume'].append(mixed_dict.get(ingre))
                    else:
                        flag=0
                        for mix_key, mix_value in mixed_dict.items():
                            if mix_key in ingre and not ingre.isalpha():
                                seq_dict['volume'].append(mix_value)
                                flag=1
                                break
                        if flag==0:
                            seq_dict['volume'].append('')
                
                # 기본 재료에 나오는 첨가물과 용량 매핑                    
                for seasoning in seq_dict['seasoning']:
                    if seasoning in mixed_dict:
                        seq_dict['volume'].append(mixed_dict.get(seasoning))
                    else: 
                        flag=0
                        for mix_key, mix_value in mixed_dict.items():
                            if mix_key in seasoning and not seasoning.isalpha():
                                seq_dict['volume'].append(mix_value)
                                flag=1
                                break
                        if flag==0: 
                            seq_dict['volume'].append('')

                #원문 용량 추가 - 선웅
                hasNumber = lambda stringVal: any(elem.isdigit() for elem in stringVal)
                for i in range(0, len(node['word'])):
                    flag=0
                    if seq_dict['start_id'] <= node['word'][i]['begin'] and node['word'][i]['end'] <= seq_dict['end_id']:
                        for vol_ele in volume_list:
                            if vol_ele in node['word'][i]['text'] and hasNumber(node['word'][i]['text']):
                                replace = node['word'][i]['text'].replace(",", "")
                                node['word'][i]['text'] = replace
                                for j in range(0, len(seq_dict['ingre'])):
                                    if node['word'][i-1]['text'] == seq_dict['ingre'][j]:
                                        flag=1
                                        volume_text = node['word'][i]['text'].split(vol_ele)
                                        seq_dict['volume'][j] = volume_text[0] + vol_ele
                                for j in range(0, len(seq_dict['seasoning'])):
                                    if node['word'][i-1]['text'] == seq_dict['seasoning'][j]:
                                        flag=1
                                        volume_text = node['word'][i]['text'].split(vol_ele)
                                        seq_dict['volume'][len(seq_dict['ingre']) + j] = volume_text[0] + vol_ele
                                
                                if flag == 0:
                                    for k in range(0, len(seq_dict['ingre'])):
                                        if node['word'][i-1]['text'] in seq_dict['ingre'][k]:
                                            volume_text = node['word'][i]['text'].split(vol_ele)
                                            seq_dict['volume'][k] = volume_text[0] + vol_ele
                                    for k in range(0, len(seq_dict['seasoning'])):
                                        if node['word'][i-1]['text'] in seq_dict['seasoning'][k]:
                                            volume_text = node['word'][i]['text'].split(vol_ele)
                                            seq_dict['volume'][len(seq_dict['ingre']) + k] = volume_text[0] + vol_ele

                sequence_list.append(seq_dict)

    for node in remove_node_list:
        node_list.remove(node)

    combine_logic = toolmatchwverb.matchresult(sequence_list, mixed_dict.keys())
    for kk in range(len(sequence_list)):
        sequence_list[kk]["tool"] = list(combine_logic[0][kk])
        #print(sequence_list[kk]["tool"],combine_logic[0][kk])

    #print(sequence_list)
    print(mixed_dict.keys(), ingredient_dict)
    
    return sequence_list




def find_sentence(node, sequence_list):
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

    return sequence_list


def make_recipe(original_recipe, entity_mode, is_srl):
    # static params
    open_api_url = "http://aiopen.etri.re.kr:8000/WiseNLU"
    access_key = "84666b2d-3e04-4342-890c-0db401319568"
    analysis_code = "SRL"

    # get cooking component list & dictionary from files
    global seasoning_list, volume_list, time_list, temperature_list, cooking_act_dict, act_to_tool_dict, tool_list, idiom_dict, zone_dict, total_sequencelist, slice_act, prepare_ingre, use_fire, put, mix, make, remove, make_low_class,mix_low_class,prepare_low_class,slice_low_class,useFire_low_class,put_low_class
    seasoning_list = []
    total_sequencelist = []
    if entity_mode != 'koelectra':
        seasoning_list = get_list_from_file("labeling/seasoning.txt")
    volume_list = get_list_from_file("labeling/volume.txt")
    time_list = get_list_from_file("labeling/time.txt")
    temperature_list = get_list_from_file("labeling/temperature.txt")
    cooking_act_dict, act_to_zone_dict = parse_cooking_act_dict("labeling/cooking_act.txt")
    act_to_tool_dict = parse_act_to_tool_dict("labeling/act_to_tool.txt")
    tool_list, tool_to_zone_dict = parse_tool_dict("labeling/tool.txt")
    idiom_dict = parse_idiom_dict("labeling/idiom.txt")
    
    slice_act = get_list_from_file("labeling/topclass_dict/slice_act.txt")
    prepare_ingre = get_list_from_file("labeling/topclass_dict/prepare_act.txt")
    use_fire = get_list_from_file("labeling/topclass_dict/useFire_act.txt")
    put = get_list_from_file("labeling/topclass_dict/put_act.txt")
    mix = get_list_from_file("labeling/topclass_dict/mix_act.txt")
    make = get_list_from_file("labeling/topclass_dict/make_act.txt")
    remove = get_list_from_file("labeling/topclass_dict/remove_act.txt")
    
    slice_low_class = get_list_from_file("labeling/lowclass_dict/slice_low.txt")
    prepare_low_class = get_list_from_file("labeling/lowclass_dict/prepare_low.txt")
    useFire_low_class = get_list_from_file("labeling/lowclass_dict/useFire_low.txt")
    put_low_class = get_list_from_file("labeling/lowclass_dict/put_low.txt")
    mix_low_class = get_list_from_file("labeling/lowclass_dict/mix_low.txt")
    make_low_class = get_list_from_file("labeling/lowclass_dict/make_low.txt")
    remove_low_class = get_list_from_file("labeling/lowclass_dict/remove_low.txt")

    zone_dict = {'act': act_to_zone_dict, 'tool': tool_to_zone_dict}

   # ETRI open api
    request_json = {
        "argument": {
            "analysis_code": analysis_code,
            "text": original_recipe
        }
    }

    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        open_api_url,
        headers={"Content-Type": "application/json; charset=UTF-8", "Authorization" : access_key},
        body=json.dumps(request_json)
    )

    json_object = json.loads(response.data)
    node_list = json_object.get("return_object").get("sentence")
    sequence_list = parse_node_section(entity_mode, is_srl, node_list)
    return sequence_list


app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    recipe_dir = "static/recipe/ko"
    recipe_list = os.listdir(recipe_dir)
    recipe_idx = random.randrange(0, len(recipe_dir))
    recipe_text_list = get_list_from_file(recipe_dir + "/" + recipe_list[recipe_idx])
    return render_template("index.html", recipe="\n".join(recipe_text_list))


@app.route('/prompt', methods=['POST'])
def prompt():
    recipe_json = None
    if request.method == 'POST':
        recipe_json = request.form.get("recipe")
    return render_template("prompt.html", recipe=recipe_json)

@app.route('/refresh')
def refresh():
    recipe_dir = "static/recipe/korean/test"
    recipe_list = os.listdir(recipe_dir)
    recipe_title = random.choice(recipe_list)
    recipe_text_list = get_list_from_file(recipe_dir + "/" + recipe_title)
    return make_response("\n".join(recipe_text_list))


@app.route("/recipe", methods=['POST'])
def recipe():
    is_srl = False
    entity_mode = "etri"
    original_recipe = None
    if request.method == 'POST':
        original_recipe = request.form.get("recipe")
        entity_mode = request.form.get("entity_mode")
        is_srl = request.form.get("srl_mode")

    if original_recipe is None:
        return make_response("Recipe is Blank", 406)

    sequence_list = make_recipe(original_recipe, entity_mode, is_srl)

    if not sequence_list:
        return make_response("레시피 분석에 실패했습니다", 406)

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

@app.route('/version2', methods=["GET"])
def version2():
    recipe_dir = "static/recipe/ko"
    recipe_list = os.listdir(recipe_dir)
    recipe_idx = random.randrange(0, len(recipe_dir))
    recipe_text_list = get_list_from_file(recipe_dir + "/" + recipe_list[recipe_idx])
    return render_template("version2.html", recipe="\n".join(recipe_text_list))

@app.route('/version2/refresh')
def version2refresh():
    recipe_dir = "static/recipe/ko"
    recipe_list = os.listdir(recipe_dir)
    recipe_title = random.choice(recipe_list)
    recipe_text_list = get_list_from_file(recipe_dir + "/" + recipe_title)
    return make_response({"refresh": "\n".join(recipe_text_list)})

@app.route('/version2/returnjson', methods=["POST", "GET"])
def root():
    original_recipe = None
    if request.method == 'POST':
        original_recipe = request.get_json()
        #print(original_recipe)
    #print(original_recipe["description"])
    if original_recipe is None:
        return make_response("Recipe is Blank", 406)
    #print(original_recipe)
    resultdata = v2.finalresult(original_recipe["description"])
    thisis = json.dumps(resultdata, ensure_ascii=False)
    return thisis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)