# -*- coding: utf-8 -*-
import json
import os.path
import urllib3

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


def find_ingredient_dependency(node, koelectra_node, seq_list):
    '''print("koelectra_node : ", koelectra_node)
    print("seq_list : ", seq_list)
    for i in range(0, len(seq_list)):
        a=0'''
    
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
    for i in range(0, len(sequence_list)):
        if sequence_list[i]['top_class'] == "use_fire":
            sequence_list[i]['zone'] = "화구존"
        elif sequence_list[i]['top_class'] == "prepare_ingre" or sequence_list[i]['top_class'] == "slice":  
            sequence_list[i]['zone'] = "전처리존"
        else:
            sequence_list[i]['zone'] = ""
        if sequence_list[i]['act'] in preprocess_act:
            sequence_list[i]['zone'] = "전처리존"
            
        for tool in sequence_list[i]['tool']:
            if tool in fire_tool:
                sequence_list[i]['zone'] = "화구존"
            elif tool in preprocess_tool:
                sequence_list[i]['zone'] = "전처리존"
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
def find_NP_OBJ(node, seq_list):
    
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
                        if sequence['top_class'] == "remove" or sequence['top_class'] == "make" or sequence['act'] == "자르다":
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
# 동사에 딸려있는 부사구까지 출력
def find_adverb(node, sequence_list): #지은 수정됨
    
    no_plus_adverb = ['정도', '크기로', '길이로', '등에', '후에'] 
    for m_ele in node['morp']:
        m_id = int(m_ele['id'])
        if m_id == 0:
            continue
        prev_morp = node['morp'][m_id - 1]
        if m_ele['type'] == 'VV' and m_ele['lemma'] in cooking_act_dict and prev_morp['type'] == "JKB" and prev_morp['lemma'] != "과": ##*바꿈과
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

def find_idiom(node, sequence_list): #지은 수정됨 ##*고침
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
                            for dic_val in idiom_dict[m_ele['lemma']]:
                                if node['word'][int(w_ele['id'])]['text'] == dic_val:
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
    for m_ele in node['morp'] :
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
        # 가리비 칼국수 멸치, 새우, 다시마 문제

        # 조리동작(용량)
        # sequence_list = volume_of_act(node, sequence_list)
        # 전성어미 처리
        sequence_list = verify_etn(node, sequence_list)

    for sequence in sequence_list:
        sequence['act'] = cooking_act_dict[sequence['act']]

    # 화구존/전처리존 분리
    #sequence_list = select_cooking_zone(sequence_list)

        # 목적어를 필수로 하는 조리 동작 처리
        #sequence_list = find_objective(node, sequence_list)

        # 조건문 처리함수추가
        #sequence_list = find_condition(node, sequence_list)
    
    # 관형어 처리
    sequence_list = find_ingredient_dependency(node, koelectra_node, sequence_list)

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
                        sequence['temperature'].append(ne['text'])

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
        
    #total_sequencelist.append(sequence_list)
    
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
    print(json_object)

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
    #소분류 규격추가
    #sequence_list = add_standard(node, sequence_list)

    for node in remove_node_list:
        node_list.remove(node)
        
    

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

def main():
    # static params
    open_api_url = "http://aiopen.etri.re.kr:8000/WiseNLU"
    access_key = "84666b2d-3e04-4342-890c-0db401319568"
    # access_key = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
    analysis_code = "SRL"

    # recipe extraction
    file_path = input("레시피 파일 경로를 입력해 주세요 : ")
    f = open(file_path, 'r', encoding="utf-8")
    original_recipe = str.join("\n", f.readlines())

    entity_mode = input("개체명 인식 모드를 선택해 주세요 (1 : ETRI, 2 : ko-BERT) : ")
    is_srl = input("SRL on/off를 선택해 주세요 (1 : OFF, 2 : ON) : ")
    if entity_mode == '1':
        entity_mode = 'etri'
    else:
        entity_mode = 'koelectra'

    if is_srl == '1':
        is_srl = False
    else:
        is_srl = True

    f.close()

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
    '''
    request_json = {
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
        body=json.dumps(request_json)
    )

    json_object = json.loads(response.data)
    '''
    node_list = [{'id': 0.0, 'reserve_str': '', 'text': '두릅 소고기 말이(2~3인분)', 'morp': [{'id': 0.0, 'lemma': '두릅', 'type': 'NNG', 'position': 0.0, 'weight': 0.010684}, {'id': 1.0, 'lemma': '소', 'type': 'NNG', 'position': 7.0, 'weight': 0.118895}, {'id': 2.0, 'lemma': '고기', 'type': 'NNG', 'position': 10.0, 'weight': 0.118895}, {'id': 3.0, 'lemma': '말', 'type': 'NNG', 'position': 17.0, 'weight': 0.0685449}, {'id': 4.0, 'lemma': '이', 'type': 'JKS', 'position': 20.0, 'weight': 0.0276097}, {'id': 5.0, 'lemma': '(', 'type': 'SS', 'position': 23.0, 'weight': 1.0}, {'id': 6.0, 'lemma': '2', 'type': 'SN', 'position': 24.0, 'weight': 1.0}, {'id': 7.0, 'lemma': '~', 'type': 'SO', 'position': 25.0, 'weight': 1.0}, {'id': 8.0, 'lemma': '3', 'type': 'SN', 'position': 26.0, 'weight': 1.0}, {'id': 9.0, 'lemma': '인분', 'type': 'NNB', 'position': 27.0, 'weight': 0.0429448}, {'id': 10.0, 'lemma': ')', 'type': 'SS', 'position': 33.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '두릅', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 0.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 7.0, 'begin': 1.0, 'end': 2.0}, {'id': 2.0, 'text': '말', 'type': 'NNG', 'scode': '01', 'weight': 2.41527, 'position': 17.0, 'begin': 3.0, 'end': 3.0}, {'id': 3.0, 'text': '이', 'type': 'JKS', 'scode': '00', 'weight': 1.0, 'position': 20.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': '(', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 23.0, 'begin': 5.0, 'end': 5.0}, {'id': 5.0, 'text': '2', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 24.0, 'begin': 6.0, 'end': 6.0}, {'id': 6.0, 'text': '~', 'type': 'SO', 'scode': '00', 'weight': 1.0, 'position': 25.0, 'begin': 7.0, 'end': 7.0}, {'id': 7.0, 'text': '3', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 26.0, 'begin': 8.0, 'end': 8.0}, {'id': 8.0, 'text': '인분', 'type': 'NNB', 'scode': '00', 'weight': 0.0, 'position': 27.0, 'begin': 9.0, 'end': 9.0}, {'id': 9.0, 'text': ')', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 33.0, 'begin': 10.0, 'end': 10.0}], 'word': [{'id': 0.0, 'text': '두릅', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '소고기', 'type': '', 'begin': 1.0, 'end': 2.0}, {'id': 2.0, 'text': '말이(2~3인분)', 'type': '', 'begin': 3.0, 'end': 10.0}], 'NE': [{'id': 0.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 1.0, 'end': 2.0, 'weight': 0.432878, 'common_noun': 0.0}, {'id': 1.0, 'text': '2~3인분', 'type': 'DT_DURATION', 'begin': 6.0, 'end': 9.0, 'weight': 0.224722, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '두릅', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.573022}, {'id': 1.0, 'text': '소고기', 'head': 2.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.638905}, {'id': 2.0, 'text': '말이(2~3인분)', 'head': -1.0, 'label': 'NP', 'mod': [1.0], 'weight': 0.210507}], 'SRL': []}, {'id': 1.0, 'reserve_str': '', 'text': '[기본 재료]', 'morp': [{'id': 0.0, 'lemma': '[', 'type': 'SS', 'position': 34.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '기본', 'type': 'NNG', 'position': 35.0, 'weight': 0.0513602}, {'id': 2.0, 'lemma': '재료', 'type': 'NNG', 'position': 42.0, 'weight': 0.0858271}, {'id': 3.0, 'lemma': ']', 'type': 'SS', 'position': 48.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '[', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 34.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '기본', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 35.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 42.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': ']', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 48.0, 'begin': 3.0, 'end': 3.0}], 'word': [{'id': 0.0, 'text': '[기본', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '재료]', 'type': '', 'begin': 2.0, 'end': 3.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '[기본', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.571806}, {'id': 1.0, 'text': '재료]', 'head': -1.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.391532}], 'SRL': []}, {'id': 2.0, 'reserve_str': '', 'text': '두릅 10~15개', 'morp': [{'id': 0.0, 'lemma': '두릅', 'type': 'NNG', 'position': 49.0, 'weight': 0.0129948}, {'id': 1.0, 'lemma': '10', 'type': 'SN', 'position': 56.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '~', 'type': 'SO', 'position': 58.0, 'weight': 1.0}, {'id': 3.0, 'lemma': '15', 'type': 'SN', 'position': 59.0, 'weight': 1.0}, {'id': 4.0, 'lemma': '개', 'type': 'NNB', 'position': 61.0, 'weight': 0.137763}], 'WSD': [{'id': 0.0, 'text': '두릅', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 49.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '10', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 56.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '~', 'type': 'SO', 'scode': '00', 'weight': 1.0, 'position': 58.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': '15', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 59.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '개', 'type': 'NNB', 'scode': '10', 'weight': 1.0, 'position': 61.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '두릅', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '10~15개', 'type': '', 'begin': 1.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '10~15개', 'type': 'QT_COUNT', 'begin': 1.0, 'end': 4.0, 'weight': 0.64102, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '두릅', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.686614}, {'id': 1.0, 'text': '10~15개', 'head': -1.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.413527}], 'SRL': []}, {'id': 3.0, 'reserve_str': '', 'text': '소고기 (불고기감) 200g', 'morp': [{'id': 0.0, 'lemma': '소', 'type': 'NNG', 'position': 64.0, 'weight': 0.121732}, {'id': 1.0, 'lemma': '고기', 'type': 'NNG', 'position': 67.0, 'weight': 0.121732}, {'id': 2.0, 'lemma': '(', 'type': 'SS', 'position': 74.0, 'weight': 1.0}, {'id': 3.0, 'lemma': '불', 'type': 'NNG', 'position': 75.0, 'weight': 0.0734341}, {'id': 4.0, 'lemma': '고기', 'type': 'NNG', 'position': 78.0, 'weight': 0.0734341}, {'id': 5.0, 'lemma': '감', 'type': 'NNG', 'position': 84.0, 'weight': 0.0220383}, {'id': 6.0, 'lemma': ')', 'type': 'SS', 'position': 87.0, 'weight': 1.0}, {'id': 7.0, 'lemma': '200', 'type': 'SN', 'position': 89.0, 'weight': 1.0}, {'id': 8.0, 'lemma': 'g', 'type': 'SL', 'position': 92.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 64.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '(', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 74.0, 'begin': 2.0, 'end': 2.0}, {'id': 2.0, 'text': '불고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 75.0, 'begin': 3.0, 'end': 4.0}, {'id': 3.0, 'text': '감', 'type': 'NNG', 'scode': '12', 'weight': 1.0, 'position': 84.0, 'begin': 5.0, 'end': 5.0}, {'id': 4.0, 'text': ')', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 87.0, 'begin': 6.0, 'end': 6.0}, {'id': 5.0, 'text': '200', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 89.0, 'begin': 7.0, 'end': 7.0}, {'id': 6.0, 'text': 'g', 'type': 'SL', 'scode': '00', 'weight': 1.0, 'position': 92.0, 'begin': 8.0, 'end': 8.0}], 'word': [{'id': 0.0, 'text': '소고기', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '(불고기감)', 'type': '', 'begin': 2.0, 'end': 6.0}, {'id': 2.0, 'text': '200g', 'type': '', 'begin': 7.0, 'end': 8.0}], 'NE': [{'id': 0.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 1.0, 'weight': 0.580257, 'common_noun': 0.0}, {'id': 1.0, 'text': '불고기감', 'type': 'CV_FOOD', 'begin': 3.0, 'end': 5.0, 'weight': 0.532597, 'common_noun': 0.0}, {'id': 2.0, 'text': '200g', 'type': 'QT_WEIGHT', 'begin': 7.0, 'end': 8.0, 'weight': 0.431111, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '소고기', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.754879}, {'id': 1.0, 'text': '(불고기감)', 'head': 2.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.520449}, {'id': 2.0, 'text': '200g', 'head': -1.0, 'label': 'NP', 'mod': [1.0], 'weight': 0.20953}], 'SRL': []}, {'id': 4.0, 'reserve_str': '', 'text': '식용유 약간 ', 'morp': [{'id': 0.0, 'lemma': '식용', 'type': 'NNG', 'position': 93.0, 'weight': 0.0929285}, {'id': 1.0, 'lemma': '유', 'type': 'XSN', 'position': 99.0, 'weight': 0.0929285}, {'id': 2.0, 'lemma': '약간', 'type': 'MAG', 'position': 103.0, 'weight': 0.0900746}], 'WSD': [{'id': 0.0, 'text': '식용유', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 93.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 103.0, 'begin': 2.0, 'end': 2.0}], 'word': [{'id': 0.0, 'text': '식용유', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': '', 'begin': 2.0, 'end': 2.0}], 'NE': [{'id': 0.0, 'text': '식용유', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 1.0, 'weight': 0.535096, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '식용유', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.0126237}, {'id': 1.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [0.0], 'weight': 0.0086947}], 'SRL': []}, {'id': 5.0, 'reserve_str': '', 'text': '전분 1큰술 ', 'morp': [{'id': 0.0, 'lemma': '전분', 'type': 'NNG', 'position': 110.0, 'weight': 0.0556995}, {'id': 1.0, 'lemma': '1', 'type': 'SN', 'position': 117.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '크', 'type': 'VA', 'position': 118.0, 'weight': 0.0638202}, {'id': 3.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 118.0, 'weight': 0.0638202}, {'id': 4.0, 'lemma': '술', 'type': 'NNB', 'position': 121.0, 'weight': 0.0204532}], 'WSD': [{'id': 0.0, 'text': '전분', 'type': 'NNG', 'scode': '05', 'weight': 1.0, 'position': 110.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 117.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '크', 'type': 'VA', 'scode': '01', 'weight': 1.0, 'position': 118.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 118.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '술', 'type': 'NNB', 'scode': '06', 'weight': 2.0, 'position': 121.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '전분', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '1큰술', 'type': '', 'begin': 1.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '전분', 'type': 'MT_CHEMICAL', 'begin': 0.0, 'end': 0.0, 'weight': 0.38267, 'common_noun': 0.0}, {'id': 1.0, 'text': '1큰술', 'type': 'QT_COUNT', 'begin': 1.0, 'end': 4.0, 'weight': 0.390765, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '전분', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.296307}, {'id': 1.0, 'text': '1큰술', 'head': -1.0, 'label': 'VP', 'mod': [0.0], 'weight': 0.09255}], 'SRL': [{'verb': '크', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.182176, 'argument': [{'type': 'ARG1', 'word_id': 0.0, 'text': '전분', 'weight': 0.182176}]}]}, {'id': 6.0, 'reserve_str': '', 'text': '통깨 약간 ', 'morp': [{'id': 0.0, 'lemma': '통', 'type': 'XPN', 'position': 125.0, 'weight': 0.0344306}, {'id': 1.0, 'lemma': '깨', 'type': 'NNG', 'position': 128.0, 'weight': 0.0344306}, {'id': 2.0, 'lemma': '약간', 'type': 'MAG', 'position': 132.0, 'weight': 0.0855791}], 'WSD': [{'id': 0.0, 'text': '통깨', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 125.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 132.0, 'begin': 2.0, 'end': 2.0}], 'word': [{'id': 0.0, 'text': '통깨', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': '', 'begin': 2.0, 'end': 2.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '통깨', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.226622}, {'id': 1.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [0.0], 'weight': 0.143436}], 'SRL': []}, {'id': 7.0, 'reserve_str': '', 'text': '소금 약간 ', 'morp': [{'id': 0.0, 'lemma': '소금', 'type': 'NNG', 'position': 139.0, 'weight': 0.0635835}, {'id': 1.0, 'lemma': '약간', 'type': 'MAG', 'position': 146.0, 'weight': 0.0929389}], 'WSD': [{'id': 0.0, 'text': '소금', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 139.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 146.0, 'begin': 1.0, 'end': 1.0}], 'word': [{'id': 0.0, 'text': '소금', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '약간', 'type': '', 'begin': 1.0, 'end': 1.0}], 'NE': [{'id': 0.0, 'text': '소금', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 0.0, 'weight': 0.366623, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '소금', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.307912}, {'id': 1.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [0.0], 'weight': 0.193228}], 'SRL': []}, {'id': 8.0, 'reserve_str': '', 'text': '[소고기 밑간 재료]', 'morp': [{'id': 0.0, 'lemma': '[', 'type': 'SS', 'position': 153.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '소', 'type': 'NNG', 'position': 154.0, 'weight': 0.101859}, {'id': 2.0, 'lemma': '고기', 'type': 'NNG', 'position': 157.0, 'weight': 0.101859}, {'id': 3.0, 'lemma': '밑', 'type': 'NNG', 'position': 164.0, 'weight': 0.0529491}, {'id': 4.0, 'lemma': '간', 'type': 'NNG', 'position': 167.0, 'weight': 0.0529491}, {'id': 5.0, 'lemma': '재료', 'type': 'NNG', 'position': 171.0, 'weight': 0.0832803}, {'id': 6.0, 'lemma': ']', 'type': 'SS', 'position': 177.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '[', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 153.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 154.0, 'begin': 1.0, 'end': 2.0}, {'id': 2.0, 'text': '밑간', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 164.0, 'begin': 3.0, 'end': 4.0}, {'id': 3.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 171.0, 'begin': 5.0, 'end': 5.0}, {'id': 4.0, 'text': ']', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 177.0, 'begin': 6.0, 'end': 6.0}], 'word': [{'id': 0.0, 'text': '[소고기', 'type': '', 'begin': 0.0, 'end': 2.0}, {'id': 1.0, 'text': '밑간', 'type': '', 'begin': 3.0, 'end': 4.0}, {'id': 2.0, 'text': '재료]', 'type': '', 'begin': 5.0, 'end': 6.0}], 'NE': [{'id': 0.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 1.0, 'end': 2.0, 'weight': 0.411392, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '[소고기', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.678903}, {'id': 1.0, 'text': '밑간', 'head': 2.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.549596}, {'id': 2.0, 'text': '재료]', 'head': -1.0, 'label': 'NP', 'mod': [1.0], 'weight': 0.16942}], 'SRL': []}, {'id': 9.0, 'reserve_str': '', 'text': '후춧가루 약간 ', 'morp': [{'id': 0.0, 'lemma': '후춧', 'type': 'NNG', 'position': 178.0, 'weight': 0.0615344}, {'id': 1.0, 'lemma': '가루', 'type': 'NNG', 'position': 184.0, 'weight': 0.0615344}, {'id': 2.0, 'lemma': '약간', 'type': 'MAG', 'position': 191.0, 'weight': 0.0913337}], 'WSD': [{'id': 0.0, 'text': '후춧가루', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 178.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 191.0, 'begin': 2.0, 'end': 2.0}], 'word': [{'id': 0.0, 'text': '후춧가루', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': '', 'begin': 2.0, 'end': 2.0}], 'NE': [{'id': 0.0, 'text': '후춧가루', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 1.0, 'weight': 0.334659, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '후춧가루', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.0630878}, {'id': 1.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [0.0], 'weight': 0.0413452}], 'SRL': []}, {'id': 10.0, 'reserve_str': '', 'text': '청주 1큰술 ', 'morp': [{'id': 0.0, 'lemma': '청주', 'type': 'NNP', 'position': 198.0, 'weight': 0.102435}, {'id': 1.0, 'lemma': '1', 'type': 'SN', 'position': 205.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '크', 'type': 'VA', 'position': 206.0, 'weight': 0.0622881}, {'id': 3.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 206.0, 'weight': 0.0622881}, {'id': 4.0, 'lemma': '술', 'type': 'NNB', 'position': 209.0, 'weight': 0.0210408}], 'WSD': [{'id': 0.0, 'text': '청주', 'type': 'NNP', 'scode': '02', 'weight': 1.0, 'position': 198.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 205.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '크', 'type': 'VA', 'scode': '01', 'weight': 1.0, 'position': 206.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 206.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '술', 'type': 'NNB', 'scode': '06', 'weight': 2.0, 'position': 209.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '청주', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '1큰술', 'type': '', 'begin': 1.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '청주', 'type': 'LCP_CITY', 'begin': 0.0, 'end': 0.0, 'weight': 0.325665, 'common_noun': 0.0}, {'id': 1.0, 'text': '1큰술', 'type': 'QT_COUNT', 'begin': 1.0, 'end': 4.0, 'weight': 0.356836, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '청주', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.257079}, {'id': 1.0, 'text': '1큰술', 'head': -1.0, 'label': 'VP', 'mod': [0.0], 'weight': 0.0154172}], 'SRL': [{'verb': '크', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.0, 'argument': []}]}, {'id': 11.0, 'reserve_str': '', 'text': '소금 약간 ', 'morp': [{'id': 0.0, 'lemma': '소금', 'type': 'NNG', 'position': 213.0, 'weight': 0.0635835}, {'id': 1.0, 'lemma': '약간', 'type': 'MAG', 'position': 220.0, 'weight': 0.0929389}], 'WSD': [{'id': 0.0, 'text': '소금', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 213.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 220.0, 'begin': 1.0, 'end': 1.0}], 'word': [{'id': 0.0, 'text': '소금', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '약간', 'type': '', 'begin': 1.0, 'end': 1.0}], 'NE': [{'id': 0.0, 'text': '소금', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 0.0, 'weight': 0.366623, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '소금', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.307912}, {'id': 1.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [0.0], 'weight': 0.193228}], 'SRL': []}, {'id': 12.0, 'reserve_str': '', 'text': '[양념 재료]', 'morp': [{'id': 0.0, 'lemma': '[', 'type': 'SS', 'position': 227.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '양념', 'type': 'NNG', 'position': 228.0, 'weight': 0.0426151}, {'id': 2.0, 'lemma': '재료', 'type': 'NNG', 'position': 235.0, 'weight': 0.0763783}, {'id': 3.0, 'lemma': ']', 'type': 'SS', 'position': 241.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '[', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 227.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '양념', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 228.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 235.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': ']', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 241.0, 'begin': 3.0, 'end': 3.0}], 'word': [{'id': 0.0, 'text': '[양념', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '재료]', 'type': '', 'begin': 2.0, 'end': 3.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '[양념', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.58892}, {'id': 1.0, 'text': '재료]', 'head': -1.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.417974}], 'SRL': []}, {'id': 13.0, 'reserve_str': '', 'text': '간장 1큰술 ', 'morp': [{'id': 0.0, 'lemma': '간장', 'type': 'NNG', 'position': 242.0, 'weight': 0.145671}, {'id': 1.0, 'lemma': '1', 'type': 'SN', 'position': 249.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '크', 'type': 'VA', 'position': 250.0, 'weight': 0.0654276}, {'id': 3.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 250.0, 'weight': 0.0654276}, {'id': 4.0, 'lemma': '술', 'type': 'NNB', 'position': 253.0, 'weight': 0.0215692}], 'WSD': [{'id': 0.0, 'text': '간장', 'type': 'NNG', 'scode': '01', 'weight': 1.0, 'position': 242.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 249.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '크', 'type': 'VA', 'scode': '01', 'weight': 1.0, 'position': 250.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 250.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '술', 'type': 'NNB', 'scode': '06', 'weight': 3.0, 'position': 253.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '간장', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '1큰술', 'type': '', 'begin': 1.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '간장', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 0.0, 'weight': 0.285037, 'common_noun': 0.0}, {'id': 1.0, 'text': '1큰술', 'type': 'QT_COUNT', 'begin': 1.0, 'end': 4.0, 'weight': 0.371629, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '간장', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.253606}, {'id': 1.0, 'text': '1큰술', 'head': -1.0, 'label': 'VP', 'mod': [0.0], 'weight': 0.0801574}], 'SRL': [{'verb': '크', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.183288, 'argument': [{'type': 'ARG1', 'word_id': 0.0, 'text': '간장', 'weight': 0.183288}]}]}, {'id': 14.0, 'reserve_str': '', 'text': '맛술 1큰술 ', 'morp': [{'id': 0.0, 'lemma': '맛', 'type': 'NNG', 'position': 257.0, 'weight': 0.0445316}, {'id': 1.0, 'lemma': '술', 'type': 'NNG', 'position': 260.0, 'weight': 0.0445316}, {'id': 2.0, 'lemma': '1', 'type': 'SN', 'position': 264.0, 'weight': 1.0}, {'id': 3.0, 'lemma': '크', 'type': 'VA', 'position': 265.0, 'weight': 0.0638202}, {'id': 4.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 265.0, 'weight': 0.0638202}, {'id': 5.0, 'lemma': '술', 'type': 'NNB', 'position': 268.0, 'weight': 0.0204532}], 'WSD': [{'id': 0.0, 'text': '맛술', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 257.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 264.0, 'begin': 2.0, 'end': 2.0}, {'id': 2.0, 'text': '크', 'type': 'VA', 'scode': '01', 'weight': 3.2, 'position': 265.0, 'begin': 3.0, 'end': 3.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 265.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': '술', 'type': 'NNB', 'scode': '06', 'weight': 3.0, 'position': 268.0, 'begin': 5.0, 'end': 5.0}], 'word': [{'id': 0.0, 'text': '맛술', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '1큰술', 'type': '', 'begin': 2.0, 'end': 5.0}], 'NE': [{'id': 0.0, 'text': '1큰술', 'type': 'QT_COUNT', 'begin': 2.0, 'end': 5.0, 'weight': 0.35649, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '맛술', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.379797}, {'id': 1.0, 'text': '1큰술', 'head': -1.0, 'label': 'VP', 'mod': [0.0], 'weight': 0.0840983}], 'SRL': [{'verb': '크', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.122918, 'argument': [{'type': 'ARG1', 'word_id': 0.0, 'text': '맛술', 'weight': 0.122918}]}]}, {'id': 15.0, 'reserve_str': '', 'text': '올리고당 2큰술 ', 'morp': [{'id': 0.0, 'lemma': '올리고당', 'type': 'NNP', 'position': 272.0, 'weight': 0.0178827}, {'id': 1.0, 'lemma': '2', 'type': 'SN', 'position': 285.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '크', 'type': 'VA', 'position': 286.0, 'weight': 0.0740942}, {'id': 3.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 286.0, 'weight': 0.0740942}, {'id': 4.0, 'lemma': '술', 'type': 'NNB', 'position': 289.0, 'weight': 0.021555}], 'WSD': [{'id': 0.0, 'text': '올리고당', 'type': 'NNP', 'scode': '00', 'weight': 0.0, 'position': 272.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '2', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 285.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '크', 'type': 'VA', 'scode': '01', 'weight': 1.0, 'position': 286.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 286.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '술', 'type': 'NNB', 'scode': '06', 'weight': 2.0, 'position': 289.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '올리고당', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '2큰술', 'type': '', 'begin': 1.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '올리고당', 'type': 'MT_CHEMICAL', 'begin': 0.0, 'end': 0.0, 'weight': 0.15697, 'common_noun': 0.0}, {'id': 1.0, 'text': '2큰술', 'type': 'QT_COUNT', 'begin': 1.0, 'end': 4.0, 'weight': 0.30939, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '올리고당', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.113007}, {'id': 1.0, 'text': '2큰술', 'head': -1.0, 'label': 'VP', 'mod': [0.0], 'weight': 0.00597868}], 'SRL': [{'verb': '크', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.0, 'argument': []}]}, {'id': 16.0, 'reserve_str': '', 'text': '물 4큰술 ', 'morp': [{'id': 0.0, 'lemma': '물', 'type': 'NNG', 'position': 293.0, 'weight': 0.0956921}, {'id': 1.0, 'lemma': '4', 'type': 'SN', 'position': 297.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '크', 'type': 'VA', 'position': 298.0, 'weight': 0.0521556}, {'id': 3.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 298.0, 'weight': 0.0521556}, {'id': 4.0, 'lemma': '술', 'type': 'NNB', 'position': 301.0, 'weight': 0.016572}], 'WSD': [{'id': 0.0, 'text': '물', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 293.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '4', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 297.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '크', 'type': 'VA', 'scode': '01', 'weight': 2.2, 'position': 298.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 298.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '술', 'type': 'NNB', 'scode': '06', 'weight': 2.0, 'position': 301.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '물', 'type': '', 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '4큰술', 'type': '', 'begin': 1.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '4큰술', 'type': 'QT_COUNT', 'begin': 1.0, 'end': 4.0, 'weight': 0.310413, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '물', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.267482}, {'id': 1.0, 'text': '4큰술', 'head': -1.0, 'label': 'VP', 'mod': [0.0], 'weight': 0.104321}], 'SRL': [{'verb': '크', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.176052, 'argument': [{'type': 'ARG1', 'word_id': 0.0, 'text': '물', 'weight': 0.176052}]}]}, {'id': 17.0, 'reserve_str': '', 'text': '참기름 1작은술 ', 'morp': [{'id': 0.0, 'lemma': '참', 'type': 'XPN', 'position': 305.0, 'weight': 0.0828879}, {'id': 1.0, 'lemma': '기름', 'type': 'NNG', 'position': 308.0, 'weight': 0.0828879}, {'id': 2.0, 'lemma': '1', 'type': 'SN', 'position': 315.0, 'weight': 1.0}, {'id': 3.0, 'lemma': '작', 'type': 'NNB', 'position': 316.0, 'weight': 0.0418903}, {'id': 4.0, 'lemma': '은술', 'type': 'JX', 'position': 319.0, 'weight': 0.0166622}], 'WSD': [{'id': 0.0, 'text': '참기름', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 305.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 315.0, 'begin': 2.0, 'end': 2.0}, {'id': 2.0, 'text': '작', 'type': 'NNB', 'scode': '03', 'weight': 1.0, 'position': 316.0, 'begin': 3.0, 'end': 3.0}, {'id': 3.0, 'text': '은술', 'type': 'JX', 'scode': '00', 'weight': 1.0, 'position': 319.0, 'begin': 4.0, 'end': 4.0}], 'word': [{'id': 0.0, 'text': '참기름', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '1작은술', 'type': '', 'begin': 2.0, 'end': 4.0}], 'NE': [{'id': 0.0, 'text': '참기름', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 1.0, 'weight': 0.282397, 'common_noun': 0.0}, {'id': 1.0, 'text': '1작', 'type': 'QT_COUNT', 'begin': 2.0, 'end': 3.0, 'weight': 0.461456, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '참기름', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.582685}, {'id': 1.0, 'text': '1작은술', 'head': -1.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.156214}], 'SRL': []}, {'id': 18.0, 'reserve_str': '', 'text': '후춧가루 약간 ', 'morp': [{'id': 0.0, 'lemma': '후춧', 'type': 'NNG', 'position': 326.0, 'weight': 0.0615344}, {'id': 1.0, 'lemma': '가루', 'type': 'NNG', 'position': 332.0, 'weight': 0.0615344}, {'id': 2.0, 'lemma': '약간', 'type': 'MAG', 'position': 339.0, 'weight': 0.0913337}], 'WSD': [{'id': 0.0, 'text': '후춧가루', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 326.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 339.0, 'begin': 2.0, 'end': 2.0}], 'word': [{'id': 0.0, 'text': '후춧가루', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '약간', 'type': '', 'begin': 2.0, 'end': 2.0}], 'NE': [{'id': 0.0, 'text': '후춧가루', 'type': 'CV_FOOD', 'begin': 0.0, 'end': 1.0, 'weight': 0.334659, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '후춧가루', 'head': 1.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.0630878}, {'id': 1.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [0.0], 'weight': 0.0413452}], 'SRL': []}, {'id': 19.0, 'reserve_str': '', 'text': '[고명 재료]', 'morp': [{'id': 0.0, 'lemma': '[', 'type': 'SS', 'position': 346.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '고명', 'type': 'NNG', 'position': 347.0, 'weight': 0.0385053}, {'id': 2.0, 'lemma': '재료', 'type': 'NNG', 'position': 354.0, 'weight': 0.0846429}, {'id': 3.0, 'lemma': ']', 'type': 'SS', 'position': 360.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '[', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 346.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '고명', 'type': 'NNG', 'scode': '01', 'weight': 1.0, 'position': 347.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 1.0, 'position': 354.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': ']', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 360.0, 'begin': 3.0, 'end': 3.0}], 'word': [{'id': 0.0, 'text': '[고명', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '재료]', 'type': '', 'begin': 2.0, 'end': 3.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '[고명', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.561475}, {'id': 1.0, 'text': '재료]', 'head': -1.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.389156}], 'SRL': []}, {'id': 20.0, 'reserve_str': '', 'text': '실고추 (생략가능) 약간 ', 'morp': [{'id': 0.0, 'lemma': '실', 'type': 'XPN', 'position': 361.0, 'weight': 0.0385706}, {'id': 1.0, 'lemma': '고추', 'type': 'NNG', 'position': 364.0, 'weight': 0.0385706}, {'id': 2.0, 'lemma': '(', 'type': 'SS', 'position': 371.0, 'weight': 1.0}, {'id': 3.0, 'lemma': '생략', 'type': 'NNG', 'position': 372.0, 'weight': 0.053508}, {'id': 4.0, 'lemma': '가능', 'type': 'NNG', 'position': 378.0, 'weight': 0.0426015}, {'id': 5.0, 'lemma': ')', 'type': 'SS', 'position': 384.0, 'weight': 1.0}, {'id': 6.0, 'lemma': '약간', 'type': 'MAG', 'position': 386.0, 'weight': 0.0980461}], 'WSD': [{'id': 0.0, 'text': '실고추', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 361.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '(', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 371.0, 'begin': 2.0, 'end': 2.0}, {'id': 2.0, 'text': '생략', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 372.0, 'begin': 3.0, 'end': 3.0}, {'id': 3.0, 'text': '가능', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 378.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': ')', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 384.0, 'begin': 5.0, 'end': 5.0}, {'id': 5.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 386.0, 'begin': 6.0, 'end': 6.0}], 'word': [{'id': 0.0, 'text': '실고추', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '(생략가능)', 'type': '', 'begin': 2.0, 'end': 5.0}, {'id': 2.0, 'text': '약간', 'type': '', 'begin': 6.0, 'end': 6.0}], 'NE': [{'id': 0.0, 'text': '고추', 'type': 'PT_GRASS', 'begin': 1.0, 'end': 1.0, 'weight': 0.335932, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '실고추', 'head': 1.0, 'label': 'NP', 'mod': [], 'weight': 0.538307}, {'id': 1.0, 'text': '(생략가능)', 'head': 2.0, 'label': 'NP', 'mod': [0.0], 'weight': 0.248256}, {'id': 2.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [1.0], 'weight': 0.0912365}], 'SRL': []}, {'id': 21.0, 'reserve_str': '', 'text': '쪽파 (생략 가능) 약간 ', 'morp': [{'id': 0.0, 'lemma': '쪽', 'type': 'XPN', 'position': 393.0, 'weight': 0.0364051}, {'id': 1.0, 'lemma': '파', 'type': 'NNG', 'position': 396.0, 'weight': 0.0364051}, {'id': 2.0, 'lemma': '(', 'type': 'SS', 'position': 400.0, 'weight': 1.0}, {'id': 3.0, 'lemma': '생략', 'type': 'NNG', 'position': 401.0, 'weight': 0.0358373}, {'id': 4.0, 'lemma': '가능', 'type': 'NNG', 'position': 408.0, 'weight': 0.0986824}, {'id': 5.0, 'lemma': ')', 'type': 'SS', 'position': 414.0, 'weight': 1.0}, {'id': 6.0, 'lemma': '약간', 'type': 'MAG', 'position': 416.0, 'weight': 0.0980461}], 'WSD': [{'id': 0.0, 'text': '쪽파', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 393.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '(', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 400.0, 'begin': 2.0, 'end': 2.0}, {'id': 2.0, 'text': '생략', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 401.0, 'begin': 3.0, 'end': 3.0}, {'id': 3.0, 'text': '가능', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 408.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': ')', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 414.0, 'begin': 5.0, 'end': 5.0}, {'id': 5.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 416.0, 'begin': 6.0, 'end': 6.0}], 'word': [{'id': 0.0, 'text': '쪽파', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '(생략', 'type': '', 'begin': 2.0, 'end': 3.0}, {'id': 2.0, 'text': '가능)', 'type': '', 'begin': 4.0, 'end': 5.0}, {'id': 3.0, 'text': '약간', 'type': '', 'begin': 6.0, 'end': 6.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '쪽파', 'head': 2.0, 'label': 'NP', 'mod': [], 'weight': 0.11322}, {'id': 1.0, 'text': '(생략', 'head': 2.0, 'label': 'NP', 'mod': [], 'weight': 0.641634}, {'id': 2.0, 'text': '가능)', 'head': 3.0, 'label': 'NP', 'mod': [0.0, 1.0], 'weight': 0.0800495}, {'id': 3.0, 'text': '약간', 'head': -1.0, 'label': 'AP', 'mod': [2.0], 'weight': 0.00412811}], 'SRL': []}, {'id': 22.0, 'reserve_str': '', 'text': '[조리방법]', 'morp': [{'id': 0.0, 'lemma': '[', 'type': 'SS', 'position': 423.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '조리', 'type': 'NNG', 'position': 424.0, 'weight': 0.0290155}, {'id': 2.0, 'lemma': '방법', 'type': 'NNG', 'position': 430.0, 'weight': 0.0429922}, {'id': 3.0, 'lemma': ']', 'type': 'SS', 'position': 436.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '[', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 423.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '조리', 'type': 'NNG', 'scode': '09', 'weight': 2.0, 'position': 424.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '방법', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 430.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': ']', 'type': 'SS', 'scode': '00', 'weight': 1.0, 'position': 436.0, 'begin': 3.0, 'end': 3.0}], 'word': [{'id': 0.0, 'text': '[조리방법]', 'type': '', 'begin': 0.0, 'end': 3.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '[조리방법]', 'head': -1.0, 'label': 'NP', 'mod': [], 'weight': 0.751647}], 'SRL': []}, {'id': 23.0, 'reserve_str': '', 'text': '1. 두릅은 밑동을 잘라내고 겉껍질을 제거해주세요.', 'morp': [{'id': 0.0, 'lemma': '1', 'type': 'SN', 'position': 437.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '.', 'type': 'SF', 'position': 438.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '두릅', 'type': 'NNP', 'position': 440.0, 'weight': 0.025015}, {'id': 3.0, 'lemma': '은', 'type': 'JX', 'position': 446.0, 'weight': 0.0859489}, {'id': 4.0, 'lemma': '밑', 'type': 'NNG', 'position': 450.0, 'weight': 0.102546}, {'id': 5.0, 'lemma': '동', 'type': 'NNG', 'position': 453.0, 'weight': 0.102546}, {'id': 6.0, 'lemma': '을', 'type': 'JKO', 'position': 456.0, 'weight': 0.113796}, {'id': 7.0, 'lemma': '자르', 'type': 'VV', 'position': 460.0, 'weight': 0.0765217}, {'id': 8.0, 'lemma': '어', 'type': 'EC', 'position': 463.0, 'weight': 0.0765217}, {'id': 9.0, 'lemma': '내', 'type': 'VX', 'position': 466.0, 'weight': 0.0336913}, {'id': 10.0, 'lemma': '고', 'type': 'EC', 'position': 469.0, 'weight': 0.0806441}, {'id': 11.0, 'lemma': '겉', 'type': 'NNG', 'position': 473.0, 'weight': 0.1095}, {'id': 12.0, 'lemma': '껍질', 'type': 'NNG', 'position': 476.0, 'weight': 0.1095}, {'id': 13.0, 'lemma': '을', 'type': 'JKO', 'position': 482.0, 'weight': 0.132922}, {'id': 14.0, 'lemma': '제거', 'type': 'NNG', 'position': 486.0, 'weight': 0.0246133}, {'id': 15.0, 'lemma': '하', 'type': 'XSV', 'position': 492.0, 'weight': 0.0246133}, {'id': 16.0, 'lemma': '어', 'type': 'EC', 'position': 492.0, 'weight': 0.0224962}, {'id': 17.0, 'lemma': '주', 'type': 'VX', 'position': 495.0, 'weight': 0.118588}, {'id': 18.0, 'lemma': '세요', 'type': 'EF', 'position': 498.0, 'weight': 0.0516668}, {'id': 19.0, 'lemma': '.', 'type': 'SF', 'position': 504.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 437.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 438.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '두릅', 'type': 'NNP', 'scode': '00', 'weight': 0.0, 'position': 440.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': '은', 'type': 'JX', 'scode': '00', 'weight': 1.0, 'position': 446.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '밑동', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 450.0, 'begin': 4.0, 'end': 5.0}, {'id': 5.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 456.0, 'begin': 6.0, 'end': 6.0}, {'id': 6.0, 'text': '자르', 'type': 'VV', 'scode': '01', 'weight': 4.4, 'position': 460.0, 'begin': 7.0, 'end': 7.0}, {'id': 7.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 463.0, 'begin': 8.0, 'end': 8.0}, {'id': 8.0, 'text': '내', 'type': 'VX', 'scode': '02', 'weight': 10.8, 'position': 466.0, 'begin': 9.0, 'end': 9.0}, {'id': 9.0, 'text': '고', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 469.0, 'begin': 10.0, 'end': 10.0}, {'id': 10.0, 'text': '겉껍질', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 473.0, 'begin': 11.0, 'end': 12.0}, {'id': 11.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 482.0, 'begin': 13.0, 'end': 13.0}, {'id': 12.0, 'text': '제거하', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 486.0, 'begin': 14.0, 'end': 15.0}, {'id': 13.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 492.0, 'begin': 16.0, 'end': 16.0}, {'id': 14.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 8.6, 'position': 495.0, 'begin': 17.0, 'end': 17.0}, {'id': 15.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 498.0, 'begin': 18.0, 'end': 18.0}, {'id': 16.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 504.0, 'begin': 19.0, 'end': 19.0}], 'word': [{'id': 0.0, 'text': '1.', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '두릅은', 'type': '', 'begin': 2.0, 'end': 3.0}, {'id': 2.0, 'text': '밑동을', 'type': '', 'begin': 4.0, 'end': 6.0}, {'id': 3.0, 'text': '잘라내고', 'type': '', 'begin': 7.0, 'end': 10.0}, {'id': 4.0, 'text': '겉껍질을', 'type': '', 'begin': 11.0, 'end': 13.0}, {'id': 5.0, 'text': '제거해주세요.', 'type': '', 'begin': 14.0, 'end': 19.0}], 'NE': [{'id': 0.0, 'text': '1', 'type': 'QT_ORDER', 'begin': 0.0, 'end': 0.0, 'weight': 0.53577, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '1.', 'head': 3.0, 'label': 'NP', 'mod': [], 'weight': 0.412506}, {'id': 1.0, 'text': '두릅은', 'head': 3.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.702982}, {'id': 2.0, 'text': '밑동을', 'head': 3.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.688341}, {'id': 3.0, 'text': '잘라내고', 'head': 5.0, 'label': 'VP', 'mod': [0.0, 1.0, 2.0], 'weight': 0.854821}, {'id': 4.0, 'text': '겉껍질을', 'head': 5.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.721487}, {'id': 5.0, 'text': '제거해주세요.', 'head': -1.0, 'label': 'VP', 'mod': [3.0, 4.0], 'weight': 0.0943969}], 'SRL': [{'verb': '자르', 'sense': 1.0, 'word_id': 3.0, 'weight': 0.145522, 'argument': [{'type': 'ARG0', 'word_id': 1.0, 'text': '두릅', 'weight': 0.0995467}, {'type': 'ARG1', 'word_id': 2.0, 'text': '밑동', 'weight': 0.191496}]}, {'verb': '제거', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.122523, 'argument': [{'type': 'ARG0', 'word_id': 1.0, 'text': '두릅', 'weight': 0.101308}, {'type': 'ARG1', 'word_id': 4.0, 'text': '겉껍질', 'weight': 0.143737}]}]}, {'id': 24.0, 'reserve_str': '', 'text': ' 줄기의 잔가시를 제거한 후 물에 씻어 주세요.', 'morp': [{'id': 0.0, 'lemma': '줄기', 'type': 'NNG', 'position': 506.0, 'weight': 0.0532858}, {'id': 1.0, 'lemma': '의', 'type': 'JKG', 'position': 512.0, 'weight': 0.115722}, {'id': 2.0, 'lemma': '잔', 'type': 'XPN', 'position': 516.0, 'weight': 0.0347591}, {'id': 3.0, 'lemma': '가시', 'type': 'NNG', 'position': 519.0, 'weight': 0.0347591}, {'id': 4.0, 'lemma': '를', 'type': 'JKO', 'position': 525.0, 'weight': 0.142548}, {'id': 5.0, 'lemma': '제거', 'type': 'NNG', 'position': 529.0, 'weight': 0.0902371}, {'id': 6.0, 'lemma': '하', 'type': 'XSV', 'position': 535.0, 'weight': 0.0902371}, {'id': 7.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 535.0, 'weight': 0.145137}, {'id': 8.0, 'lemma': '후', 'type': 'NNG', 'position': 539.0, 'weight': 0.159141}, {'id': 9.0, 'lemma': '물', 'type': 'NNG', 'position': 543.0, 'weight': 0.115737}, {'id': 10.0, 'lemma': '에', 'type': 'JKB', 'position': 546.0, 'weight': 0.139712}, {'id': 11.0, 'lemma': '씻', 'type': 'VV', 'position': 550.0, 'weight': 0.145688}, {'id': 12.0, 'lemma': '어', 'type': 'EC', 'position': 553.0, 'weight': 0.167604}, {'id': 13.0, 'lemma': '주', 'type': 'VX', 'position': 557.0, 'weight': 0.103185}, {'id': 14.0, 'lemma': '세요', 'type': 'EF', 'position': 560.0, 'weight': 0.0661811}, {'id': 15.0, 'lemma': '.', 'type': 'SF', 'position': 566.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '줄기', 'type': 'NNG', 'scode': '01', 'weight': 3.2, 'position': 506.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '의', 'type': 'JKG', 'scode': '00', 'weight': 1.0, 'position': 512.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '잔가시', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 516.0, 'begin': 2.0, 'end': 3.0}, {'id': 3.0, 'text': '를', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 525.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': '제거하', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 529.0, 'begin': 5.0, 'end': 6.0}, {'id': 5.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 535.0, 'begin': 7.0, 'end': 7.0}, {'id': 6.0, 'text': '후', 'type': 'NNG', 'scode': '08', 'weight': 6.6, 'position': 539.0, 'begin': 8.0, 'end': 8.0}, {'id': 7.0, 'text': '물', 'type': 'NNG', 'scode': '01', 'weight': 6.6, 'position': 543.0, 'begin': 9.0, 'end': 9.0}, {'id': 8.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 546.0, 'begin': 10.0, 'end': 10.0}, {'id': 9.0, 'text': '씻', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 550.0, 'begin': 11.0, 'end': 11.0}, {'id': 10.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 553.0, 'begin': 12.0, 'end': 12.0}, {'id': 11.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 4.4, 'position': 557.0, 'begin': 13.0, 'end': 13.0}, {'id': 12.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 560.0, 'begin': 14.0, 'end': 14.0}, {'id': 13.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 566.0, 'begin': 15.0, 'end': 15.0}], 'word': [{'id': 0.0, 'text': '줄기의', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '잔가시를', 'type': '', 'begin': 2.0, 'end': 4.0}, {'id': 2.0, 'text': '제거한', 'type': '', 'begin': 5.0, 'end': 7.0}, {'id': 3.0, 'text': '후', 'type': '', 'begin': 8.0, 'end': 8.0}, {'id': 4.0, 'text': '물에', 'type': '', 'begin': 9.0, 'end': 10.0}, {'id': 5.0, 'text': '씻어', 'type': '', 'begin': 11.0, 'end': 12.0}, {'id': 6.0, 'text': '주세요.', 'type': '', 'begin': 13.0, 'end': 15.0}], 'NE': [{'id': 0.0, 'text': '줄기', 'type': 'PT_PART', 'begin': 0.0, 'end': 0.0, 'weight': 0.33735, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '줄기의', 'head': 1.0, 'label': 'NP_MOD', 'mod': [], 'weight': 0.673194}, {'id': 1.0, 'text': '잔가시를', 'head': 2.0, 'label': 'NP_OBJ', 'mod': [0.0], 'weight': 0.705527}, {'id': 2.0, 'text': '제거한', 'head': 3.0, 'label': 'VP_MOD', 'mod': [1.0], 'weight': 0.665213}, {'id': 3.0, 'text': '후', 'head': 5.0, 'label': 'NP_AJT', 'mod': [2.0], 'weight': 0.765286}, {'id': 4.0, 'text': '물에', 'head': 5.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.653483}, {'id': 5.0, 'text': '씻어', 'head': 6.0, 'label': 'VP', 'mod': [3.0, 4.0], 'weight': 0.634207}, {'id': 6.0, 'text': '주세요.', 'head': -1.0, 'label': 'VP', 'mod': [5.0], 'weight': 0.0830124}], 'SRL': [{'verb': '제거', 'sense': 1.0, 'word_id': 2.0, 'weight': 0.217203, 'argument': [{'type': 'ARG1', 'word_id': 1.0, 'text': '줄기의 잔가시', 'weight': 0.217203}]}, {'verb': '씻', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.195717, 'argument': [{'type': 'ARGM-TMP', 'word_id': 3.0, 'text': '줄기의 잔가시를 제거한 후', 'weight': 0.181398}, {'type': 'ARG2', 'word_id': 4.0, 'text': '물', 'weight': 0.159985}, {'type': 'AUX', 'word_id': 6.0, 'text': '주세요.', 'weight': 0.245768}]}]}, {'id': 25.0, 'reserve_str': '', 'text': '2. 소고기는 키친타월에 올려 핏물을 제거한 후 밑간 재료를 골고루 발라주세요.', 'morp': [{'id': 0.0, 'lemma': '2', 'type': 'SN', 'position': 567.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '.', 'type': 'SF', 'position': 568.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '소', 'type': 'NNG', 'position': 570.0, 'weight': 0.164577}, {'id': 3.0, 'lemma': '고기', 'type': 'NNG', 'position': 573.0, 'weight': 0.164577}, {'id': 4.0, 'lemma': '는', 'type': 'JX', 'position': 579.0, 'weight': 0.114091}, {'id': 5.0, 'lemma': '키친', 'type': 'NNG', 'position': 583.0, 'weight': 0.0429978}, {'id': 6.0, 'lemma': '타월', 'type': 'NNG', 'position': 589.0, 'weight': 0.0429978}, {'id': 7.0, 'lemma': '에', 'type': 'JKB', 'position': 595.0, 'weight': 0.108246}, {'id': 8.0, 'lemma': '올리', 'type': 'VV', 'position': 599.0, 'weight': 0.0813366}, {'id': 9.0, 'lemma': '어', 'type': 'EC', 'position': 602.0, 'weight': 0.0619387}, {'id': 10.0, 'lemma': '핏', 'type': 'NNG', 'position': 606.0, 'weight': 0.053537}, {'id': 11.0, 'lemma': '물', 'type': 'NNG', 'position': 609.0, 'weight': 0.053537}, {'id': 12.0, 'lemma': '을', 'type': 'JKO', 'position': 612.0, 'weight': 0.120339}, {'id': 13.0, 'lemma': '제거', 'type': 'NNG', 'position': 616.0, 'weight': 0.0868941}, {'id': 14.0, 'lemma': '하', 'type': 'XSV', 'position': 622.0, 'weight': 0.0868941}, {'id': 15.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 622.0, 'weight': 0.143414}, {'id': 16.0, 'lemma': '후', 'type': 'NNG', 'position': 626.0, 'weight': 0.227223}, {'id': 17.0, 'lemma': '밑', 'type': 'NNG', 'position': 630.0, 'weight': 0.0495757}, {'id': 18.0, 'lemma': '간', 'type': 'NNG', 'position': 633.0, 'weight': 0.0495757}, {'id': 19.0, 'lemma': '재료', 'type': 'NNG', 'position': 637.0, 'weight': 0.152764}, {'id': 20.0, 'lemma': '를', 'type': 'JKO', 'position': 643.0, 'weight': 0.145479}, {'id': 21.0, 'lemma': '골고루', 'type': 'MAG', 'position': 647.0, 'weight': 0.0388956}, {'id': 22.0, 'lemma': '바르', 'type': 'VV', 'position': 657.0, 'weight': 0.0390272}, {'id': 23.0, 'lemma': '어', 'type': 'EC', 'position': 660.0, 'weight': 0.0390272}, {'id': 24.0, 'lemma': '주', 'type': 'VX', 'position': 663.0, 'weight': 0.0490521}, {'id': 25.0, 'lemma': '세요', 'type': 'EF', 'position': 666.0, 'weight': 0.0532041}, {'id': 26.0, 'lemma': '.', 'type': 'SF', 'position': 672.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '2', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 567.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 568.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 570.0, 'begin': 2.0, 'end': 3.0}, {'id': 3.0, 'text': '는', 'type': 'JX', 'scode': '00', 'weight': 1.0, 'position': 579.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': '키친타월', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 583.0, 'begin': 5.0, 'end': 6.0}, {'id': 5.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 595.0, 'begin': 7.0, 'end': 7.0}, {'id': 6.0, 'text': '올리', 'type': 'VV', 'scode': '01', 'weight': 6.6, 'position': 599.0, 'begin': 8.0, 'end': 8.0}, {'id': 7.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 602.0, 'begin': 9.0, 'end': 9.0}, {'id': 8.0, 'text': '핏물', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 606.0, 'begin': 10.0, 'end': 11.0}, {'id': 9.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 612.0, 'begin': 12.0, 'end': 12.0}, {'id': 10.0, 'text': '제거하', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 616.0, 'begin': 13.0, 'end': 14.0}, {'id': 11.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 622.0, 'begin': 15.0, 'end': 15.0}, {'id': 12.0, 'text': '후', 'type': 'NNG', 'scode': '08', 'weight': 9.8, 'position': 626.0, 'begin': 16.0, 'end': 16.0}, {'id': 13.0, 'text': '밑간', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 630.0, 'begin': 17.0, 'end': 18.0}, {'id': 14.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 6.6, 'position': 637.0, 'begin': 19.0, 'end': 19.0}, {'id': 15.0, 'text': '를', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 643.0, 'begin': 20.0, 'end': 20.0}, {'id': 16.0, 'text': '골고루', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 647.0, 'begin': 21.0, 'end': 21.0}, {'id': 17.0, 'text': '바르', 'type': 'VV', 'scode': '01', 'weight': 3.2, 'position': 657.0, 'begin': 22.0, 'end': 22.0}, {'id': 18.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 660.0, 'begin': 23.0, 'end': 23.0}, {'id': 19.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 6.4, 'position': 663.0, 'begin': 24.0, 'end': 24.0}, {'id': 20.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 666.0, 'begin': 25.0, 'end': 25.0}, {'id': 21.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 672.0, 'begin': 26.0, 'end': 26.0}], 'word': [{'id': 0.0, 'text': '2.', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '소고기는', 'type': '', 'begin': 2.0, 'end': 4.0}, {'id': 2.0, 'text': '키친타월에', 'type': '', 'begin': 5.0, 'end': 7.0}, {'id': 3.0, 'text': '올려', 'type': '', 'begin': 8.0, 'end': 9.0}, {'id': 4.0, 'text': '핏물을', 'type': '', 'begin': 10.0, 'end': 12.0}, {'id': 5.0, 'text': '제거한', 'type': '', 'begin': 13.0, 'end': 15.0}, {'id': 6.0, 'text': '후', 'type': '', 'begin': 16.0, 'end': 16.0}, {'id': 7.0, 'text': '밑간', 'type': '', 'begin': 17.0, 'end': 18.0}, {'id': 8.0, 'text': '재료를', 'type': '', 'begin': 19.0, 'end': 20.0}, {'id': 9.0, 'text': '골고루', 'type': '', 'begin': 21.0, 'end': 21.0}, {'id': 10.0, 'text': '발라주세요.', 'type': '', 'begin': 22.0, 'end': 26.0}], 'NE': [{'id': 0.0, 'text': '2', 'type': 'QT_ORDER', 'begin': 0.0, 'end': 0.0, 'weight': 0.401698, 'common_noun': 0.0}, {'id': 1.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 2.0, 'end': 3.0, 'weight': 0.806924, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '2.', 'head': 10.0, 'label': 'NP', 'mod': [], 'weight': 0.592559}, {'id': 1.0, 'text': '소고기는', 'head': 10.0, 'label': 'NP_SBJ', 'mod': [], 'weight': 0.513995}, {'id': 2.0, 'text': '키친타월에', 'head': 3.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.749094}, {'id': 3.0, 'text': '올려', 'head': 5.0, 'label': 'VP', 'mod': [2.0], 'weight': 0.78154}, {'id': 4.0, 'text': '핏물을', 'head': 5.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.78231}, {'id': 5.0, 'text': '제거한', 'head': 6.0, 'label': 'VP_MOD', 'mod': [3.0, 4.0], 'weight': 0.597485}, {'id': 6.0, 'text': '후', 'head': 10.0, 'label': 'NP_AJT', 'mod': [5.0], 'weight': 0.61119}, {'id': 7.0, 'text': '밑간', 'head': 8.0, 'label': 'NP', 'mod': [], 'weight': 0.426222}, {'id': 8.0, 'text': '재료를', 'head': 10.0, 'label': 'NP_OBJ', 'mod': [7.0], 'weight': 0.7487}, {'id': 9.0, 'text': '골고루', 'head': 10.0, 'label': 'AP', 'mod': [], 'weight': 0.597675}, {'id': 10.0, 'text': '발라주세요.', 'head': -1.0, 'label': 'VP', 'mod': [0.0, 1.0, 6.0, 8.0, 9.0], 'weight': 0.00808558}], 'SRL': [{'verb': '올리', 'sense': 3.0, 'word_id': 3.0, 'weight': 0.124467, 'argument': [{'type': 'ARG1', 'word_id': 1.0, 'text': '소고기', 'weight': 0.12624}, {'type': 'ARG2', 'word_id': 2.0, 'text': '키친타월', 'weight': 0.122694}]}, {'verb': '제거', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.131298, 'argument': [{'type': 'ARGM-CAU', 'word_id': 3.0, 'text': '키친타월에 올려', 'weight': 0.0752099}, {'type': 'ARG1', 'word_id': 4.0, 'text': '핏물', 'weight': 0.187385}]}, {'verb': '바르', 'sense': 2.0, 'word_id': 10.0, 'weight': 0.187634, 'argument': [{'type': 'ARG1', 'word_id': 1.0, 'text': '소고기', 'weight': 0.146118}, {'type': 'ARGM-TMP', 'word_id': 6.0, 'text': '키친타월에 올려 핏물을 제거한 후', 'weight': 0.271361}, {'type': 'ARGM-MNR', 'word_id': 9.0, 'text': '골고루', 'weight': 0.12457}]}]}, {'id': 26.0, 'reserve_str': '', 'text': ' 양념재료는 잘 섞어주세요.', 'morp': [{'id': 0.0, 'lemma': '양념', 'type': 'NNG', 'position': 674.0, 'weight': 0.0502978}, {'id': 1.0, 'lemma': '재료', 'type': 'NNG', 'position': 680.0, 'weight': 0.0421576}, {'id': 2.0, 'lemma': '는', 'type': 'JX', 'position': 686.0, 'weight': 0.116572}, {'id': 3.0, 'lemma': '잘', 'type': 'MAG', 'position': 690.0, 'weight': 0.132121}, {'id': 4.0, 'lemma': '섞', 'type': 'VV', 'position': 694.0, 'weight': 0.147978}, {'id': 5.0, 'lemma': '어', 'type': 'EC', 'position': 697.0, 'weight': 0.0651954}, {'id': 6.0, 'lemma': '주', 'type': 'VX', 'position': 700.0, 'weight': 0.0773608}, {'id': 7.0, 'lemma': '세요', 'type': 'EF', 'position': 703.0, 'weight': 0.0529728}, {'id': 8.0, 'lemma': '.', 'type': 'SF', 'position': 709.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '양념', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 674.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 4.4, 'position': 680.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '는', 'type': 'JX', 'scode': '00', 'weight': 1.0, 'position': 686.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': '잘', 'type': 'MAG', 'scode': '02', 'weight': 6.6, 'position': 690.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '섞', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 694.0, 'begin': 4.0, 'end': 4.0}, {'id': 5.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 697.0, 'begin': 5.0, 'end': 5.0}, {'id': 6.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 5.4, 'position': 700.0, 'begin': 6.0, 'end': 6.0}, {'id': 7.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 703.0, 'begin': 7.0, 'end': 7.0}, {'id': 8.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 709.0, 'begin': 8.0, 'end': 8.0}], 'word': [{'id': 0.0, 'text': '양념재료는', 'type': '', 'begin': 0.0, 'end': 2.0}, {'id': 1.0, 'text': '잘', 'type': '', 'begin': 3.0, 'end': 3.0}, {'id': 2.0, 'text': '섞어주세요.', 'type': '', 'begin': 4.0, 'end': 8.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '양념재료는', 'head': 2.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.3988}, {'id': 1.0, 'text': '잘', 'head': 2.0, 'label': 'AP', 'mod': [], 'weight': 0.589199}, {'id': 2.0, 'text': '섞어주세요.', 'head': -1.0, 'label': 'VP', 'mod': [0.0, 1.0], 'weight': 0.195135}], 'SRL': [{'verb': '섞', 'sense': 1.0, 'word_id': 2.0, 'weight': 0.14705, 'argument': [{'type': 'ARG1', 'word_id': 0.0, 'text': '양념재료', 'weight': 0.168846}, {'type': 'ARGM-ADV', 'word_id': 1.0, 'text': '잘', 'weight': 1.0}]}]}, {'id': 27.0, 'reserve_str': '', 'text': '3. 끓는 물에 소금 1작은술을 넣고 두릅을 줄기 부터 넣어 30초 정도 데쳐주세요.', 'morp': [{'id': 0.0, 'lemma': '3', 'type': 'SN', 'position': 710.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '.', 'type': 'SF', 'position': 711.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '끓', 'type': 'VV', 'position': 713.0, 'weight': 0.0781721}, {'id': 3.0, 'lemma': '는', 'type': 'ETM', 'position': 716.0, 'weight': 0.0761764}, {'id': 4.0, 'lemma': '물', 'type': 'NNG', 'position': 720.0, 'weight': 0.130575}, {'id': 5.0, 'lemma': '에', 'type': 'JKB', 'position': 723.0, 'weight': 0.126001}, {'id': 6.0, 'lemma': '소금', 'type': 'NNG', 'position': 727.0, 'weight': 0.0934802}, {'id': 7.0, 'lemma': '1', 'type': 'SN', 'position': 734.0, 'weight': 1.0}, {'id': 8.0, 'lemma': '작', 'type': 'NNB', 'position': 735.0, 'weight': 0.0478919}, {'id': 9.0, 'lemma': '은술', 'type': 'NNG', 'position': 738.0, 'weight': 0.0218495}, {'id': 10.0, 'lemma': '을', 'type': 'JKO', 'position': 744.0, 'weight': 0.119173}, {'id': 11.0, 'lemma': '넣', 'type': 'VV', 'position': 748.0, 'weight': 0.174588}, {'id': 12.0, 'lemma': '고', 'type': 'EC', 'position': 751.0, 'weight': 0.0799936}, {'id': 13.0, 'lemma': '두릅', 'type': 'NNG', 'position': 755.0, 'weight': 0.0173814}, {'id': 14.0, 'lemma': '을', 'type': 'JKO', 'position': 761.0, 'weight': 0.0881678}, {'id': 15.0, 'lemma': '줄기', 'type': 'NNG', 'position': 765.0, 'weight': 0.0398563}, {'id': 16.0, 'lemma': '부터', 'type': 'JX', 'position': 772.0, 'weight': 0.0643803}, {'id': 17.0, 'lemma': '넣', 'type': 'VV', 'position': 779.0, 'weight': 0.13336}, {'id': 18.0, 'lemma': '어', 'type': 'EC', 'position': 782.0, 'weight': 0.0966149}, {'id': 19.0, 'lemma': '30', 'type': 'SN', 'position': 786.0, 'weight': 1.0}, {'id': 20.0, 'lemma': '초', 'type': 'NNB', 'position': 788.0, 'weight': 0.137592}, {'id': 21.0, 'lemma': '정도', 'type': 'NNG', 'position': 792.0, 'weight': 0.132158}, {'id': 22.0, 'lemma': '데치', 'type': 'VV', 'position': 799.0, 'weight': 0.0470423}, {'id': 23.0, 'lemma': '어', 'type': 'EC', 'position': 802.0, 'weight': 0.0417929}, {'id': 24.0, 'lemma': '주', 'type': 'VX', 'position': 805.0, 'weight': 0.0671018}, {'id': 25.0, 'lemma': '세요', 'type': 'EF', 'position': 808.0, 'weight': 0.0560795}, {'id': 26.0, 'lemma': '.', 'type': 'SF', 'position': 814.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '3', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 710.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 711.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '끓', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 713.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': '는', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 716.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '물', 'type': 'NNG', 'scode': '01', 'weight': 4.4, 'position': 720.0, 'begin': 4.0, 'end': 4.0}, {'id': 5.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 723.0, 'begin': 5.0, 'end': 5.0}, {'id': 6.0, 'text': '소금', 'type': 'NNG', 'scode': '01', 'weight': 4.4, 'position': 727.0, 'begin': 6.0, 'end': 6.0}, {'id': 7.0, 'text': '1', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 734.0, 'begin': 7.0, 'end': 7.0}, {'id': 8.0, 'text': '작', 'type': 'NNB', 'scode': '03', 'weight': 1.0, 'position': 735.0, 'begin': 8.0, 'end': 8.0}, {'id': 9.0, 'text': '은술', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 738.0, 'begin': 9.0, 'end': 9.0}, {'id': 10.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 744.0, 'begin': 10.0, 'end': 10.0}, {'id': 11.0, 'text': '넣', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 748.0, 'begin': 11.0, 'end': 11.0}, {'id': 12.0, 'text': '고', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 751.0, 'begin': 12.0, 'end': 12.0}, {'id': 13.0, 'text': '두릅', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 755.0, 'begin': 13.0, 'end': 13.0}, {'id': 14.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 761.0, 'begin': 14.0, 'end': 14.0}, {'id': 15.0, 'text': '줄기', 'type': 'NNG', 'scode': '01', 'weight': 4.4, 'position': 765.0, 'begin': 15.0, 'end': 15.0}, {'id': 16.0, 'text': '부터', 'type': 'JX', 'scode': '00', 'weight': 1.0, 'position': 772.0, 'begin': 16.0, 'end': 16.0}, {'id': 17.0, 'text': '넣', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 779.0, 'begin': 17.0, 'end': 17.0}, {'id': 18.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 782.0, 'begin': 18.0, 'end': 18.0}, {'id': 19.0, 'text': '30', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 786.0, 'begin': 19.0, 'end': 19.0}, {'id': 20.0, 'text': '초', 'type': 'NNB', 'scode': '07', 'weight': 6.6, 'position': 788.0, 'begin': 20.0, 'end': 20.0}, {'id': 21.0, 'text': '정도', 'type': 'NNG', 'scode': '11', 'weight': 2.2, 'position': 792.0, 'begin': 21.0, 'end': 21.0}, {'id': 22.0, 'text': '데치', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 799.0, 'begin': 22.0, 'end': 22.0}, {'id': 23.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 802.0, 'begin': 23.0, 'end': 23.0}, {'id': 24.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 2.2, 'position': 805.0, 'begin': 24.0, 'end': 24.0}, {'id': 25.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 808.0, 'begin': 25.0, 'end': 25.0}, {'id': 26.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 814.0, 'begin': 26.0, 'end': 26.0}], 'word': [{'id': 0.0, 'text': '3.', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '끓는', 'type': '', 'begin': 2.0, 'end': 3.0}, {'id': 2.0, 'text': '물에', 'type': '', 'begin': 4.0, 'end': 5.0}, {'id': 3.0, 'text': '소금', 'type': '', 'begin': 6.0, 'end': 6.0}, {'id': 4.0, 'text': '1작은술을', 'type': '', 'begin': 7.0, 'end': 10.0}, {'id': 5.0, 'text': '넣고', 'type': '', 'begin': 11.0, 'end': 12.0}, {'id': 6.0, 'text': '두릅을', 'type': '', 'begin': 13.0, 'end': 14.0}, {'id': 7.0, 'text': '줄기', 'type': '', 'begin': 15.0, 'end': 15.0}, {'id': 8.0, 'text': '부터', 'type': '', 'begin': 16.0, 'end': 16.0}, {'id': 9.0, 'text': '넣어', 'type': '', 'begin': 17.0, 'end': 18.0}, {'id': 10.0, 'text': '30초', 'type': '', 'begin': 19.0, 'end': 20.0}, {'id': 11.0, 'text': '정도', 'type': '', 'begin': 21.0, 'end': 21.0}, {'id': 12.0, 'text': '데쳐주세요.', 'type': '', 'begin': 22.0, 'end': 26.0}], 'NE': [{'id': 0.0, 'text': '3', 'type': 'QT_ORDER', 'begin': 0.0, 'end': 0.0, 'weight': 0.401411, 'common_noun': 0.0}, {'id': 1.0, 'text': '소금', 'type': 'CV_FOOD', 'begin': 6.0, 'end': 6.0, 'weight': 0.405394, 'common_noun': 0.0}, {'id': 2.0, 'text': '1작은술', 'type': 'QT_COUNT', 'begin': 7.0, 'end': 9.0, 'weight': 0.355993, 'common_noun': 0.0}, {'id': 3.0, 'text': '두릅', 'type': 'CV_FOOD', 'begin': 13.0, 'end': 13.0, 'weight': 0.175213, 'common_noun': 0.0}, {'id': 4.0, 'text': '줄기', 'type': 'PT_PART', 'begin': 15.0, 'end': 15.0, 'weight': 0.414738, 'common_noun': 0.0}, {'id': 5.0, 'text': '30초', 'type': 'TI_DURATION', 'begin': 19.0, 'end': 20.0, 'weight': 0.662647, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '3.', 'head': 9.0, 'label': 'NP', 'mod': [], 'weight': 0.363272}, {'id': 1.0, 'text': '끓는', 'head': 2.0, 'label': 'VP_MOD', 'mod': [], 'weight': 0.654177}, {'id': 2.0, 'text': '물에', 'head': 5.0, 'label': 'NP_AJT', 'mod': [1.0], 'weight': 0.679185}, {'id': 3.0, 'text': '소금', 'head': 4.0, 'label': 'NP', 'mod': [], 'weight': 0.49383}, {'id': 4.0, 'text': '1작은술을', 'head': 5.0, 'label': 'NP_OBJ', 'mod': [3.0], 'weight': 0.706173}, {'id': 5.0, 'text': '넣고', 'head': 9.0, 'label': 'VP', 'mod': [2.0, 4.0], 'weight': 0.811488}, {'id': 6.0, 'text': '두릅을', 'head': 9.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.837437}, {'id': 7.0, 'text': '줄기', 'head': 8.0, 'label': 'NP', 'mod': [], 'weight': 0.529268}, {'id': 8.0, 'text': '부터', 'head': 9.0, 'label': 'NP_AJT', 'mod': [7.0], 'weight': 0.230481}, {'id': 9.0, 'text': '넣어', 'head': 12.0, 'label': 'VP', 'mod': [0.0, 5.0, 6.0, 8.0], 'weight': 0.757326}, {'id': 10.0, 'text': '30초', 'head': 11.0, 'label': 'NP', 'mod': [], 'weight': 0.302855}, {'id': 11.0, 'text': '정도', 'head': 12.0, 'label': 'NP_OBJ', 'mod': [10.0], 'weight': 0.145572}, {'id': 12.0, 'text': '데쳐주세요.', 'head': -1.0, 'label': 'VP', 'mod': [9.0, 11.0], 'weight': 0.000129947}], 'SRL': [{'verb': '끓', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.186394, 'argument': [{'type': 'ARG1', 'word_id': 2.0, 'text': '끓는 물', 'weight': 0.186394}]}, {'verb': '넣', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.170702, 'argument': [{'type': 'ARG2', 'word_id': 2.0, 'text': '끓는 물', 'weight': 0.119901}, {'type': 'ARG1', 'word_id': 4.0, 'text': '소금 1작은술', 'weight': 0.221503}]}, {'verb': '넣', 'sense': 1.0, 'word_id': 9.0, 'weight': 0.14637, 'argument': [{'type': 'ARG1', 'word_id': 6.0, 'text': '두릅', 'weight': 0.21585}, {'type': 'ARGM-TMP', 'word_id': 8.0, 'text': '줄기', 'weight': 0.0768895}]}, {'verb': '데치', 'sense': 1.0, 'word_id': 12.0, 'weight': 0.109366, 'argument': [{'type': 'ARGM-CAU', 'word_id': 9.0, 'text': '3. 끓는 물에 소금 1작은술을 넣고 두릅을 줄기 부터 넣어', 'weight': 0.0784574}, {'type': 'ARG1', 'word_id': 11.0, 'text': '30초 정도', 'weight': 0.140274}]}]}, {'id': 28.0, 'reserve_str': '', 'text': ' 데친 두릅은 찬물에 헹궈 채반에서 물기를 빼주세요.', 'morp': [{'id': 0.0, 'lemma': '데치', 'type': 'VV', 'position': 816.0, 'weight': 0.0421285}, {'id': 1.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 819.0, 'weight': 0.039801}, {'id': 2.0, 'lemma': '두', 'type': 'MM', 'position': 823.0, 'weight': 0.0451494}, {'id': 3.0, 'lemma': '릅', 'type': 'NNB', 'position': 826.0, 'weight': 0.0141194}, {'id': 4.0, 'lemma': '은', 'type': 'JX', 'position': 829.0, 'weight': 0.0837374}, {'id': 5.0, 'lemma': '찬물', 'type': 'NNG', 'position': 833.0, 'weight': 0.0812395}, {'id': 6.0, 'lemma': '에', 'type': 'JKB', 'position': 839.0, 'weight': 0.130799}, {'id': 7.0, 'lemma': '헹구', 'type': 'VV', 'position': 843.0, 'weight': 0.0443824}, {'id': 8.0, 'lemma': '어', 'type': 'EC', 'position': 846.0, 'weight': 0.0284386}, {'id': 9.0, 'lemma': '채', 'type': 'NNG', 'position': 850.0, 'weight': 0.0594392}, {'id': 10.0, 'lemma': '반', 'type': 'NNG', 'position': 853.0, 'weight': 0.0594392}, {'id': 11.0, 'lemma': '에서', 'type': 'JKB', 'position': 856.0, 'weight': 0.106741}, {'id': 12.0, 'lemma': '물', 'type': 'NNG', 'position': 863.0, 'weight': 0.0964948}, {'id': 13.0, 'lemma': '기', 'type': 'NNG', 'position': 866.0, 'weight': 0.0964948}, {'id': 14.0, 'lemma': '를', 'type': 'JKO', 'position': 869.0, 'weight': 0.155042}, {'id': 15.0, 'lemma': '빼', 'type': 'VV', 'position': 873.0, 'weight': 0.0859466}, {'id': 16.0, 'lemma': '어', 'type': 'EC', 'position': 876.0, 'weight': 0.0859466}, {'id': 17.0, 'lemma': '주', 'type': 'VX', 'position': 876.0, 'weight': 0.0763668}, {'id': 18.0, 'lemma': '세요', 'type': 'EF', 'position': 879.0, 'weight': 0.0536685}, {'id': 19.0, 'lemma': '.', 'type': 'SF', 'position': 885.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '데치', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 816.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 819.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '두', 'type': 'MM', 'scode': '01', 'weight': 2.2, 'position': 823.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': '릅', 'type': 'NNB', 'scode': '00', 'weight': 0.0, 'position': 826.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '은', 'type': 'JX', 'scode': '00', 'weight': 1.0, 'position': 829.0, 'begin': 4.0, 'end': 4.0}, {'id': 5.0, 'text': '찬물', 'type': 'NNG', 'scode': '01', 'weight': 4.4, 'position': 833.0, 'begin': 5.0, 'end': 5.0}, {'id': 6.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 839.0, 'begin': 6.0, 'end': 6.0}, {'id': 7.0, 'text': '헹구', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 843.0, 'begin': 7.0, 'end': 7.0}, {'id': 8.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 846.0, 'begin': 8.0, 'end': 8.0}, {'id': 9.0, 'text': '채반', 'type': 'NNG', 'scode': '02', 'weight': 2.2, 'position': 850.0, 'begin': 9.0, 'end': 10.0}, {'id': 10.0, 'text': '에서', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 856.0, 'begin': 11.0, 'end': 11.0}, {'id': 11.0, 'text': '물기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 863.0, 'begin': 12.0, 'end': 13.0}, {'id': 12.0, 'text': '를', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 869.0, 'begin': 14.0, 'end': 14.0}, {'id': 13.0, 'text': '빼', 'type': 'VV', 'scode': '01', 'weight': 5.2, 'position': 873.0, 'begin': 15.0, 'end': 15.0}, {'id': 14.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 876.0, 'begin': 16.0, 'end': 16.0}, {'id': 15.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 8.6, 'position': 876.0, 'begin': 17.0, 'end': 17.0}, {'id': 16.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 879.0, 'begin': 18.0, 'end': 18.0}, {'id': 17.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 885.0, 'begin': 19.0, 'end': 19.0}], 'word': [{'id': 0.0, 'text': '데친', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '두릅은', 'type': '', 'begin': 2.0, 'end': 4.0}, {'id': 2.0, 'text': '찬물에', 'type': '', 'begin': 5.0, 'end': 6.0}, {'id': 3.0, 'text': '헹궈', 'type': '', 'begin': 7.0, 'end': 8.0}, {'id': 4.0, 'text': '채반에서', 'type': '', 'begin': 9.0, 'end': 11.0}, {'id': 5.0, 'text': '물기를', 'type': '', 'begin': 12.0, 'end': 14.0}, {'id': 6.0, 'text': '빼주세요.', 'type': '', 'begin': 15.0, 'end': 19.0}], 'NE': [], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '데친', 'head': 1.0, 'label': 'VP_MOD', 'mod': [], 'weight': 0.536125}, {'id': 1.0, 'text': '두릅은', 'head': 3.0, 'label': 'NP_SBJ', 'mod': [0.0], 'weight': 0.113278}, {'id': 2.0, 'text': '찬물에', 'head': 3.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.629638}, {'id': 3.0, 'text': '헹궈', 'head': 6.0, 'label': 'VP', 'mod': [1.0, 2.0], 'weight': 0.765393}, {'id': 4.0, 'text': '채반에서', 'head': 6.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.687546}, {'id': 5.0, 'text': '물기를', 'head': 6.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.647648}, {'id': 6.0, 'text': '빼주세요.', 'head': -1.0, 'label': 'VP', 'mod': [3.0, 4.0, 5.0], 'weight': 0.0109442}], 'SRL': [{'verb': '데치', 'sense': 1.0, 'word_id': 0.0, 'weight': 0.145148, 'argument': [{'type': 'ARG1', 'word_id': 1.0, 'text': '데친 두릅', 'weight': 0.145148}]}, {'verb': '헹구', 'sense': 1.0, 'word_id': 3.0, 'weight': 0.119032, 'argument': [{'type': 'ARG1', 'word_id': 1.0, 'text': '데친 두릅', 'weight': 0.0909066}, {'type': 'ARG2', 'word_id': 2.0, 'text': '찬물', 'weight': 0.147158}]}, {'verb': '빼', 'sense': 1.0, 'word_id': 6.0, 'weight': 0.117427, 'argument': [{'type': 'ARG0', 'word_id': 1.0, 'text': '데친 두릅', 'weight': 0.0881957}, {'type': 'ARGM-MNR', 'word_id': 3.0, 'text': '찬물에 헹궈', 'weight': 0.0804435}, {'type': 'ARGM-LOC', 'word_id': 4.0, 'text': '채반', 'weight': 0.112066}, {'type': 'ARG1', 'word_id': 5.0, 'text': '물기', 'weight': 0.189003}]}]}, {'id': 29.0, 'reserve_str': '', 'text': '4. 소고기에 전분을 약간 뿌린 후 데친 두릅을 넣어 돌돌 말아주세요.', 'morp': [{'id': 0.0, 'lemma': '4', 'type': 'SN', 'position': 886.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '.', 'type': 'SF', 'position': 887.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '소', 'type': 'NNG', 'position': 889.0, 'weight': 0.169676}, {'id': 3.0, 'lemma': '고기', 'type': 'NNG', 'position': 892.0, 'weight': 0.169676}, {'id': 4.0, 'lemma': '에', 'type': 'JKB', 'position': 898.0, 'weight': 0.0630354}, {'id': 5.0, 'lemma': '전분', 'type': 'NNG', 'position': 902.0, 'weight': 0.0713451}, {'id': 6.0, 'lemma': '을', 'type': 'JKO', 'position': 908.0, 'weight': 0.118611}, {'id': 7.0, 'lemma': '약간', 'type': 'MAG', 'position': 912.0, 'weight': 0.0865197}, {'id': 8.0, 'lemma': '뿌리', 'type': 'VV', 'position': 919.0, 'weight': 0.107763}, {'id': 9.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 922.0, 'weight': 0.101926}, {'id': 10.0, 'lemma': '후', 'type': 'NNG', 'position': 926.0, 'weight': 0.159302}, {'id': 11.0, 'lemma': '데치', 'type': 'VV', 'position': 930.0, 'weight': 0.045366}, {'id': 12.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 933.0, 'weight': 0.0449159}, {'id': 13.0, 'lemma': '두릅', 'type': 'NNG', 'position': 937.0, 'weight': 0.021397}, {'id': 14.0, 'lemma': '을', 'type': 'JKO', 'position': 943.0, 'weight': 0.108032}, {'id': 15.0, 'lemma': '넣', 'type': 'VV', 'position': 947.0, 'weight': 0.163322}, {'id': 16.0, 'lemma': '어', 'type': 'EC', 'position': 950.0, 'weight': 0.10579}, {'id': 17.0, 'lemma': '돌돌', 'type': 'MAG', 'position': 954.0, 'weight': 0.0383601}, {'id': 18.0, 'lemma': '말', 'type': 'VV', 'position': 961.0, 'weight': 0.0897062}, {'id': 19.0, 'lemma': '어', 'type': 'EC', 'position': 964.0, 'weight': 0.0500702}, {'id': 20.0, 'lemma': '주', 'type': 'VX', 'position': 967.0, 'weight': 0.0598539}, {'id': 21.0, 'lemma': '세요', 'type': 'EF', 'position': 970.0, 'weight': 0.0526535}, {'id': 22.0, 'lemma': '.', 'type': 'SF', 'position': 976.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '4', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 886.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 887.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 889.0, 'begin': 2.0, 'end': 3.0}, {'id': 3.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 898.0, 'begin': 4.0, 'end': 4.0}, {'id': 4.0, 'text': '전분', 'type': 'NNG', 'scode': '05', 'weight': 1.0, 'position': 902.0, 'begin': 5.0, 'end': 5.0}, {'id': 5.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 908.0, 'begin': 6.0, 'end': 6.0}, {'id': 6.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 912.0, 'begin': 7.0, 'end': 7.0}, {'id': 7.0, 'text': '뿌리', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 919.0, 'begin': 8.0, 'end': 8.0}, {'id': 8.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 922.0, 'begin': 9.0, 'end': 9.0}, {'id': 9.0, 'text': '후', 'type': 'NNG', 'scode': '08', 'weight': 3.2, 'position': 926.0, 'begin': 10.0, 'end': 10.0}, {'id': 10.0, 'text': '데치', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 930.0, 'begin': 11.0, 'end': 11.0}, {'id': 11.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 933.0, 'begin': 12.0, 'end': 12.0}, {'id': 12.0, 'text': '두릅', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 937.0, 'begin': 13.0, 'end': 13.0}, {'id': 13.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 943.0, 'begin': 14.0, 'end': 14.0}, {'id': 14.0, 'text': '넣', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 947.0, 'begin': 15.0, 'end': 15.0}, {'id': 15.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 950.0, 'begin': 16.0, 'end': 16.0}, {'id': 16.0, 'text': '돌돌', 'type': 'MAG', 'scode': '01', 'weight': 4.4, 'position': 954.0, 'begin': 17.0, 'end': 17.0}, {'id': 17.0, 'text': '말', 'type': 'VV', 'scode': '01', 'weight': 5.29316, 'position': 961.0, 'begin': 18.0, 'end': 18.0}, {'id': 18.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 964.0, 'begin': 19.0, 'end': 19.0}, {'id': 19.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 4.2, 'position': 967.0, 'begin': 20.0, 'end': 20.0}, {'id': 20.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 970.0, 'begin': 21.0, 'end': 21.0}, {'id': 21.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 976.0, 'begin': 22.0, 'end': 22.0}], 'word': [{'id': 0.0, 'text': '4.', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '소고기에', 'type': '', 'begin': 2.0, 'end': 4.0}, {'id': 2.0, 'text': '전분을', 'type': '', 'begin': 5.0, 'end': 6.0}, {'id': 3.0, 'text': '약간', 'type': '', 'begin': 7.0, 'end': 7.0}, {'id': 4.0, 'text': '뿌린', 'type': '', 'begin': 8.0, 'end': 9.0}, {'id': 5.0, 'text': '후', 'type': '', 'begin': 10.0, 'end': 10.0}, {'id': 6.0, 'text': '데친', 'type': '', 'begin': 11.0, 'end': 12.0}, {'id': 7.0, 'text': '두릅을', 'type': '', 'begin': 13.0, 'end': 14.0}, {'id': 8.0, 'text': '넣어', 'type': '', 'begin': 15.0, 'end': 16.0}, {'id': 9.0, 'text': '돌돌', 'type': '', 'begin': 17.0, 'end': 17.0}, {'id': 10.0, 'text': '말아주세요.', 'type': '', 'begin': 18.0, 'end': 22.0}], 'NE': [{'id': 0.0, 'text': '4', 'type': 'QT_ORDER', 'begin': 0.0, 'end': 0.0, 'weight': 0.392097, 'common_noun': 0.0}, {'id': 1.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 2.0, 'end': 3.0, 'weight': 0.649317, 'common_noun': 0.0}, {'id': 2.0, 'text': '전분', 'type': 'MT_CHEMICAL', 'begin': 5.0, 'end': 5.0, 'weight': 0.349707, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '4.', 'head': 8.0, 'label': 'NP', 'mod': [], 'weight': 0.519032}, {'id': 1.0, 'text': '소고기에', 'head': 4.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.489894}, {'id': 2.0, 'text': '전분을', 'head': 4.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.676134}, {'id': 3.0, 'text': '약간', 'head': 4.0, 'label': 'AP', 'mod': [], 'weight': 0.699552}, {'id': 4.0, 'text': '뿌린', 'head': 5.0, 'label': 'VP_MOD', 'mod': [1.0, 2.0, 3.0], 'weight': 0.746956}, {'id': 5.0, 'text': '후', 'head': 8.0, 'label': 'NP_AJT', 'mod': [4.0], 'weight': 0.777598}, {'id': 6.0, 'text': '데친', 'head': 7.0, 'label': 'VP_MOD', 'mod': [], 'weight': 0.641045}, {'id': 7.0, 'text': '두릅을', 'head': 8.0, 'label': 'NP_OBJ', 'mod': [6.0], 'weight': 0.720109}, {'id': 8.0, 'text': '넣어', 'head': 10.0, 'label': 'VP', 'mod': [0.0, 5.0, 7.0], 'weight': 0.713419}, {'id': 9.0, 'text': '돌돌', 'head': 10.0, 'label': 'AP', 'mod': [], 'weight': 0.406125}, {'id': 10.0, 'text': '말아주세요.', 'head': -1.0, 'label': 'VP', 'mod': [8.0, 9.0], 'weight': 0.00804591}], 'SRL': [{'verb': '뿌리', 'sense': 1.0, 'word_id': 4.0, 'weight': 0.156836, 'argument': [{'type': 'ARG2', 'word_id': 1.0, 'text': '소고기', 'weight': 0.131738}, {'type': 'ARG1', 'word_id': 2.0, 'text': '전분', 'weight': 0.242343}, {'type': 'ARGM-EXT', 'word_id': 3.0, 'text': '약간', 'weight': 0.0964268}]}, {'verb': '데치', 'sense': 1.0, 'word_id': 6.0, 'weight': 0.130351, 'argument': [{'type': 'ARGM-TMP', 'word_id': 5.0, 'text': '소고기에 전분을 약간 뿌린 후', 'weight': 0.102828}, {'type': 'ARG1', 'word_id': 7.0, 'text': '데친 두릅', 'weight': 0.157874}]}, {'verb': '넣', 'sense': 1.0, 'word_id': 8.0, 'weight': 0.193144, 'argument': [{'type': 'ARGM-TMP', 'word_id': 5.0, 'text': '소고기에 전분을 약간 뿌린 후', 'weight': 0.170855}, {'type': 'ARG1', 'word_id': 7.0, 'text': '데친 두릅', 'weight': 0.215434}]}, {'verb': '말', 'sense': 1.0, 'word_id': 10.0, 'weight': 0.0849244, 'argument': [{'type': 'ARGM-MNR', 'word_id': 8.0, 'text': '4. 소고기에 전분을 약간 뿌린 후 데친 두릅을 넣어', 'weight': 0.0780574}, {'type': 'ARGM-MNR', 'word_id': 9.0, 'text': '돌돌', 'weight': 0.0917914}]}]}, {'id': 30.0, 'reserve_str': '', 'text': '5. 달군 팬에 기름을 약간 두른 후 소고기의 이음새 부분이 아래로 가도록 올려 노릇하게 구워주세요.6.', 'morp': [{'id': 0.0, 'lemma': '5', 'type': 'SN', 'position': 977.0, 'weight': 1.0}, {'id': 1.0, 'lemma': '.', 'type': 'SF', 'position': 978.0, 'weight': 1.0}, {'id': 2.0, 'lemma': '달구', 'type': 'VV', 'position': 980.0, 'weight': 0.0287797}, {'id': 3.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 983.0, 'weight': 0.0213165}, {'id': 4.0, 'lemma': '팬', 'type': 'NNG', 'position': 987.0, 'weight': 0.0908409}, {'id': 5.0, 'lemma': '에', 'type': 'JKB', 'position': 990.0, 'weight': 0.097713}, {'id': 6.0, 'lemma': '기름', 'type': 'NNG', 'position': 994.0, 'weight': 0.0692809}, {'id': 7.0, 'lemma': '을', 'type': 'JKO', 'position': 1000.0, 'weight': 0.113421}, {'id': 8.0, 'lemma': '약간', 'type': 'MAG', 'position': 1004.0, 'weight': 0.0832138}, {'id': 9.0, 'lemma': '두르', 'type': 'VV', 'position': 1011.0, 'weight': 0.083886}, {'id': 10.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 1014.0, 'weight': 0.0725675}, {'id': 11.0, 'lemma': '후', 'type': 'NNG', 'position': 1018.0, 'weight': 0.204586}, {'id': 12.0, 'lemma': '소', 'type': 'NNG', 'position': 1022.0, 'weight': 0.163013}, {'id': 13.0, 'lemma': '고기', 'type': 'NNG', 'position': 1025.0, 'weight': 0.163013}, {'id': 14.0, 'lemma': '의', 'type': 'JKG', 'position': 1031.0, 'weight': 0.10891}, {'id': 15.0, 'lemma': '이음', 'type': 'NNG', 'position': 1035.0, 'weight': 0.0697036}, {'id': 16.0, 'lemma': '새', 'type': 'NNG', 'position': 1041.0, 'weight': 0.0697036}, {'id': 17.0, 'lemma': '부분', 'type': 'NNG', 'position': 1045.0, 'weight': 0.117956}, {'id': 18.0, 'lemma': '이', 'type': 'JKS', 'position': 1051.0, 'weight': 0.0665937}, {'id': 19.0, 'lemma': '아래', 'type': 'NNG', 'position': 1055.0, 'weight': 0.115649}, {'id': 20.0, 'lemma': '로', 'type': 'JKB', 'position': 1061.0, 'weight': 0.131994}, {'id': 21.0, 'lemma': '가', 'type': 'VV', 'position': 1065.0, 'weight': 0.104125}, {'id': 22.0, 'lemma': '도록', 'type': 'EC', 'position': 1068.0, 'weight': 0.0896441}, {'id': 23.0, 'lemma': '올리', 'type': 'VV', 'position': 1075.0, 'weight': 0.0710019}, {'id': 24.0, 'lemma': '어', 'type': 'EC', 'position': 1078.0, 'weight': 0.0557948}, {'id': 25.0, 'lemma': '노릇하', 'type': 'VA', 'position': 1082.0, 'weight': 0.0389012}, {'id': 26.0, 'lemma': '게', 'type': 'EC', 'position': 1091.0, 'weight': 0.10945}, {'id': 27.0, 'lemma': '굽', 'type': 'VV', 'position': 1095.0, 'weight': 0.0465484}, {'id': 28.0, 'lemma': '어', 'type': 'EC', 'position': 1098.0, 'weight': 0.0465484}, {'id': 29.0, 'lemma': '주', 'type': 'VX', 'position': 1101.0, 'weight': 0.0675275}, {'id': 30.0, 'lemma': '세요', 'type': 'EF', 'position': 1104.0, 'weight': 0.0363166}, {'id': 31.0, 'lemma': '.', 'type': 'SP', 'position': 1110.0, 'weight': 1.0}, {'id': 32.0, 'lemma': '6', 'type': 'SN', 'position': 1111.0, 'weight': 1.0}, {'id': 33.0, 'lemma': '.', 'type': 'SF', 'position': 1112.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '5', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 977.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 978.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '달구', 'type': 'VV', 'scode': '01', 'weight': 3.2, 'position': 980.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 983.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': '팬', 'type': 'NNG', 'scode': '03', 'weight': 2.0, 'position': 987.0, 'begin': 4.0, 'end': 4.0}, {'id': 5.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 990.0, 'begin': 5.0, 'end': 5.0}, {'id': 6.0, 'text': '기름', 'type': 'NNG', 'scode': '01', 'weight': 5.4, 'position': 994.0, 'begin': 6.0, 'end': 6.0}, {'id': 7.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 1000.0, 'begin': 7.0, 'end': 7.0}, {'id': 8.0, 'text': '약간', 'type': 'MAG', 'scode': '00', 'weight': 0.0, 'position': 1004.0, 'begin': 8.0, 'end': 8.0}, {'id': 9.0, 'text': '두르', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 1011.0, 'begin': 9.0, 'end': 9.0}, {'id': 10.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 1014.0, 'begin': 10.0, 'end': 10.0}, {'id': 11.0, 'text': '후', 'type': 'NNG', 'scode': '08', 'weight': 5.2, 'position': 1018.0, 'begin': 11.0, 'end': 11.0}, {'id': 12.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1022.0, 'begin': 12.0, 'end': 13.0}, {'id': 13.0, 'text': '의', 'type': 'JKG', 'scode': '00', 'weight': 1.0, 'position': 1031.0, 'begin': 14.0, 'end': 14.0}, {'id': 14.0, 'text': '이음새', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1035.0, 'begin': 15.0, 'end': 16.0}, {'id': 15.0, 'text': '부분', 'type': 'NNG', 'scode': '01', 'weight': 12.0, 'position': 1045.0, 'begin': 17.0, 'end': 17.0}, {'id': 16.0, 'text': '이', 'type': 'JKS', 'scode': '00', 'weight': 1.0, 'position': 1051.0, 'begin': 18.0, 'end': 18.0}, {'id': 17.0, 'text': '아래', 'type': 'NNG', 'scode': '01', 'weight': 7.6, 'position': 1055.0, 'begin': 19.0, 'end': 19.0}, {'id': 18.0, 'text': '로', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 1061.0, 'begin': 20.0, 'end': 20.0}, {'id': 19.0, 'text': '가', 'type': 'VV', 'scode': '01', 'weight': 6.6, 'position': 1065.0, 'begin': 21.0, 'end': 21.0}, {'id': 20.0, 'text': '도록', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1068.0, 'begin': 22.0, 'end': 22.0}, {'id': 21.0, 'text': '올리', 'type': 'VV', 'scode': '01', 'weight': 6.6, 'position': 1075.0, 'begin': 23.0, 'end': 23.0}, {'id': 22.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1078.0, 'begin': 24.0, 'end': 24.0}, {'id': 23.0, 'text': '노릇하', 'type': 'VA', 'scode': '00', 'weight': 0.0, 'position': 1082.0, 'begin': 25.0, 'end': 25.0}, {'id': 24.0, 'text': '게', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1091.0, 'begin': 26.0, 'end': 26.0}, {'id': 25.0, 'text': '굽', 'type': 'VV', 'scode': '01', 'weight': 3.2, 'position': 1095.0, 'begin': 27.0, 'end': 27.0}, {'id': 26.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1098.0, 'begin': 28.0, 'end': 28.0}, {'id': 27.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 4.2, 'position': 1101.0, 'begin': 29.0, 'end': 29.0}, {'id': 28.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 1104.0, 'begin': 30.0, 'end': 30.0}, {'id': 29.0, 'text': '.', 'type': 'SP', 'scode': '00', 'weight': 1.0, 'position': 1110.0, 'begin': 31.0, 'end': 31.0}, {'id': 30.0, 'text': '6', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 1111.0, 'begin': 32.0, 'end': 32.0}, {'id': 31.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 1112.0, 'begin': 33.0, 'end': 33.0}], 'word': [{'id': 0.0, 'text': '5.', 'type': '', 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': '달군', 'type': '', 'begin': 2.0, 'end': 3.0}, {'id': 2.0, 'text': '팬에', 'type': '', 'begin': 4.0, 'end': 5.0}, {'id': 3.0, 'text': '기름을', 'type': '', 'begin': 6.0, 'end': 7.0}, {'id': 4.0, 'text': '약간', 'type': '', 'begin': 8.0, 'end': 8.0}, {'id': 5.0, 'text': '두른', 'type': '', 'begin': 9.0, 'end': 10.0}, {'id': 6.0, 'text': '후', 'type': '', 'begin': 11.0, 'end': 11.0}, {'id': 7.0, 'text': '소고기의', 'type': '', 'begin': 12.0, 'end': 14.0}, {'id': 8.0, 'text': '이음새', 'type': '', 'begin': 15.0, 'end': 16.0}, {'id': 9.0, 'text': '부분이', 'type': '', 'begin': 17.0, 'end': 18.0}, {'id': 10.0, 'text': '아래로', 'type': '', 'begin': 19.0, 'end': 20.0}, {'id': 11.0, 'text': '가도록', 'type': '', 'begin': 21.0, 'end': 22.0}, {'id': 12.0, 'text': '올려', 'type': '', 'begin': 23.0, 'end': 24.0}, {'id': 13.0, 'text': '노릇하게', 'type': '', 'begin': 25.0, 'end': 26.0}, {'id': 14.0, 'text': '구워주세요.6.', 'type': '', 'begin': 27.0, 'end': 33.0}], 'NE': [{'id': 0.0, 'text': '5', 'type': 'QT_ORDER', 'begin': 0.0, 'end': 0.0, 'weight': 0.38393, 'common_noun': 0.0}, {'id': 1.0, 'text': '팬', 'type': 'CV_POSITION', 'begin': 4.0, 'end': 4.0, 'weight': 0.395026, 'common_noun': 0.0}, {'id': 2.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 12.0, 'end': 13.0, 'weight': 0.516632, 'common_noun': 0.0}, {'id': 3.0, 'text': '6', 'type': 'QT_ORDER', 'begin': 32.0, 'end': 32.0, 'weight': 0.149254, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '5.', 'head': 14.0, 'label': 'NP', 'mod': [], 'weight': 0.495505}, {'id': 1.0, 'text': '달군', 'head': 2.0, 'label': 'VP_MOD', 'mod': [], 'weight': 0.684337}, {'id': 2.0, 'text': '팬에', 'head': 5.0, 'label': 'NP_AJT', 'mod': [1.0], 'weight': 0.431171}, {'id': 3.0, 'text': '기름을', 'head': 5.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.710806}, {'id': 4.0, 'text': '약간', 'head': 5.0, 'label': 'AP', 'mod': [], 'weight': 0.77122}, {'id': 5.0, 'text': '두른', 'head': 6.0, 'label': 'VP_MOD', 'mod': [2.0, 3.0, 4.0], 'weight': 0.811435}, {'id': 6.0, 'text': '후', 'head': 11.0, 'label': 'NP_AJT', 'mod': [5.0], 'weight': 0.603671}, {'id': 7.0, 'text': '소고기의', 'head': 9.0, 'label': 'NP_MOD', 'mod': [], 'weight': 0.637993}, {'id': 8.0, 'text': '이음새', 'head': 9.0, 'label': 'NP', 'mod': [], 'weight': 0.561289}, {'id': 9.0, 'text': '부분이', 'head': 11.0, 'label': 'NP_SBJ', 'mod': [7.0, 8.0], 'weight': 0.763175}, {'id': 10.0, 'text': '아래로', 'head': 11.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.757876}, {'id': 11.0, 'text': '가도록', 'head': 12.0, 'label': 'VP', 'mod': [6.0, 9.0, 10.0], 'weight': 0.806612}, {'id': 12.0, 'text': '올려', 'head': 14.0, 'label': 'VP', 'mod': [11.0], 'weight': 0.793431}, {'id': 13.0, 'text': '노릇하게', 'head': 14.0, 'label': 'VP_AJT', 'mod': [], 'weight': 0.398413}, {'id': 14.0, 'text': '구워주세요.6.', 'head': -1.0, 'label': 'VP', 'mod': [0.0, 12.0, 13.0], 'weight': 3.6924e-05}], 'SRL': [{'verb': '달구', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.250282, 'argument': [{'type': 'ARG1', 'word_id': 2.0, 'text': '달군 팬', 'weight': 0.250282}]}, {'verb': '두르', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.132895, 'argument': [{'type': 'ARG2', 'word_id': 2.0, 'text': '달군 팬', 'weight': 0.10508}, {'type': 'ARG1', 'word_id': 3.0, 'text': '기름', 'weight': 0.192548}, {'type': 'ARGM-EXT', 'word_id': 4.0, 'text': '약간', 'weight': 0.101056}]}, {'verb': '가', 'sense': 1.0, 'word_id': 11.0, 'weight': 0.166579, 'argument': [{'type': 'ARGM-TMP', 'word_id': 6.0, 'text': '달군 팬에 기름을 약간 두른 후', 'weight': 0.194992}, {'type': 'ARG1', 'word_id': 9.0, 'text': '소고기의 이음새 부분', 'weight': 0.125233}, {'type': 'ARG3', 'word_id': 10.0, 'text': '아래', 'weight': 0.179512}]}, {'verb': '올리', 'sense': 1.0, 'word_id': 12.0, 'weight': 0.103398, 'argument': [{'type': 'ARGM-TMP', 'word_id': 6.0, 'text': '달군 팬에 기름을 약간 두른 후', 'weight': 0.149589}, {'type': 'ARG1', 'word_id': 9.0, 'text': '소고기의 이음새 부분', 'weight': 0.0900913}, {'type': 'ARGM-PRP', 'word_id': 11.0, 'text': '아래로 가도록', 'weight': 0.0705124}]}, {'verb': '굽', 'sense': 1.0, 'word_id': 14.0, 'weight': 0.107169, 'argument': [{'type': 'ARGM-MNR', 'word_id': 12.0, 'text': '달군 팬에 기름을 약간 두른 후 소고기의 이음새 부분이 아래로 가도록 올려', 'weight': 0.107169}]}]}, {'id': 31.0, 'reserve_str': '', 'text': ' 두릅을 구운 팬에 양념 재료를 넣고 끓어오르면 구워둔 두릅 소고기 말이를 넣어 졸여주세요.7.', 'morp': [{'id': 0.0, 'lemma': '두', 'type': 'MM', 'position': 1114.0, 'weight': 0.048562}, {'id': 1.0, 'lemma': '릅', 'type': 'NNB', 'position': 1117.0, 'weight': 0.0186281}, {'id': 2.0, 'lemma': '을', 'type': 'JKO', 'position': 1120.0, 'weight': 0.100832}, {'id': 3.0, 'lemma': '굽', 'type': 'VV', 'position': 1124.0, 'weight': 0.0904365}, {'id': 4.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 1127.0, 'weight': 0.0904365}, {'id': 5.0, 'lemma': '팬', 'type': 'NNG', 'position': 1131.0, 'weight': 0.12015}, {'id': 6.0, 'lemma': '에', 'type': 'JKB', 'position': 1134.0, 'weight': 0.114084}, {'id': 7.0, 'lemma': '양념', 'type': 'NNG', 'position': 1138.0, 'weight': 0.0699427}, {'id': 8.0, 'lemma': '재료', 'type': 'NNG', 'position': 1145.0, 'weight': 0.157827}, {'id': 9.0, 'lemma': '를', 'type': 'JKO', 'position': 1151.0, 'weight': 0.157945}, {'id': 10.0, 'lemma': '넣', 'type': 'VV', 'position': 1155.0, 'weight': 0.181728}, {'id': 11.0, 'lemma': '고', 'type': 'EC', 'position': 1158.0, 'weight': 0.0802044}, {'id': 12.0, 'lemma': '끓어오르', 'type': 'VV', 'position': 1162.0, 'weight': 0.0693323}, {'id': 13.0, 'lemma': '면', 'type': 'EC', 'position': 1174.0, 'weight': 0.122277}, {'id': 14.0, 'lemma': '굽', 'type': 'VV', 'position': 1178.0, 'weight': 0.0446381}, {'id': 15.0, 'lemma': '어', 'type': 'EC', 'position': 1181.0, 'weight': 0.0446381}, {'id': 16.0, 'lemma': '두', 'type': 'VX', 'position': 1184.0, 'weight': 0.0446381}, {'id': 17.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 1184.0, 'weight': 0.0446381}, {'id': 18.0, 'lemma': '두릅', 'type': 'NNG', 'position': 1188.0, 'weight': 0.0140022}, {'id': 19.0, 'lemma': '소', 'type': 'NNG', 'position': 1195.0, 'weight': 0.119402}, {'id': 20.0, 'lemma': '고기', 'type': 'NNG', 'position': 1198.0, 'weight': 0.119402}, {'id': 21.0, 'lemma': '말', 'type': 'NNG', 'position': 1205.0, 'weight': 0.0550367}, {'id': 22.0, 'lemma': '이', 'type': 'NNG', 'position': 1208.0, 'weight': 0.0550367}, {'id': 23.0, 'lemma': '를', 'type': 'JKO', 'position': 1211.0, 'weight': 0.165753}, {'id': 24.0, 'lemma': '넣', 'type': 'VV', 'position': 1215.0, 'weight': 0.169636}, {'id': 25.0, 'lemma': '어', 'type': 'EC', 'position': 1218.0, 'weight': 0.108825}, {'id': 26.0, 'lemma': '졸이', 'type': 'VV', 'position': 1222.0, 'weight': 0.0461033}, {'id': 27.0, 'lemma': '어', 'type': 'EC', 'position': 1225.0, 'weight': 0.0283177}, {'id': 28.0, 'lemma': '주', 'type': 'VX', 'position': 1228.0, 'weight': 0.0569394}, {'id': 29.0, 'lemma': '세요', 'type': 'EF', 'position': 1231.0, 'weight': 0.0369564}, {'id': 30.0, 'lemma': '.', 'type': 'SP', 'position': 1237.0, 'weight': 1.0}, {'id': 31.0, 'lemma': '7', 'type': 'SN', 'position': 1238.0, 'weight': 1.0}, {'id': 32.0, 'lemma': '.', 'type': 'SF', 'position': 1239.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '두', 'type': 'MM', 'scode': '01', 'weight': 2.2, 'position': 1114.0, 'begin': 0.0, 'end': 0.0}, {'id': 1.0, 'text': '릅', 'type': 'NNB', 'scode': '00', 'weight': 0.0, 'position': 1117.0, 'begin': 1.0, 'end': 1.0}, {'id': 2.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 1120.0, 'begin': 2.0, 'end': 2.0}, {'id': 3.0, 'text': '굽', 'type': 'VV', 'scode': '01', 'weight': 4.3, 'position': 1124.0, 'begin': 3.0, 'end': 3.0}, {'id': 4.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 1127.0, 'begin': 4.0, 'end': 4.0}, {'id': 5.0, 'text': '팬', 'type': 'NNG', 'scode': '03', 'weight': 1.0, 'position': 1131.0, 'begin': 5.0, 'end': 5.0}, {'id': 6.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 1134.0, 'begin': 6.0, 'end': 6.0}, {'id': 7.0, 'text': '양념', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1138.0, 'begin': 7.0, 'end': 7.0}, {'id': 8.0, 'text': '재료', 'type': 'NNG', 'scode': '01', 'weight': 4.4, 'position': 1145.0, 'begin': 8.0, 'end': 8.0}, {'id': 9.0, 'text': '를', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 1151.0, 'begin': 9.0, 'end': 9.0}, {'id': 10.0, 'text': '넣', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 1155.0, 'begin': 10.0, 'end': 10.0}, {'id': 11.0, 'text': '고', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1158.0, 'begin': 11.0, 'end': 11.0}, {'id': 12.0, 'text': '끓어오르', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 1162.0, 'begin': 12.0, 'end': 12.0}, {'id': 13.0, 'text': '면', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1174.0, 'begin': 13.0, 'end': 13.0}, {'id': 14.0, 'text': '굽', 'type': 'VV', 'scode': '01', 'weight': 4.4, 'position': 1178.0, 'begin': 14.0, 'end': 14.0}, {'id': 15.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1181.0, 'begin': 15.0, 'end': 15.0}, {'id': 16.0, 'text': '두', 'type': 'VX', 'scode': '01', 'weight': 4.2, 'position': 1184.0, 'begin': 16.0, 'end': 16.0}, {'id': 17.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 1184.0, 'begin': 17.0, 'end': 17.0}, {'id': 18.0, 'text': '두릅', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1188.0, 'begin': 18.0, 'end': 18.0}, {'id': 19.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1195.0, 'begin': 19.0, 'end': 20.0}, {'id': 20.0, 'text': '말이', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1205.0, 'begin': 21.0, 'end': 22.0}, {'id': 21.0, 'text': '를', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 1211.0, 'begin': 23.0, 'end': 23.0}, {'id': 22.0, 'text': '넣', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 1215.0, 'begin': 24.0, 'end': 24.0}, {'id': 23.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1218.0, 'begin': 25.0, 'end': 25.0}, {'id': 24.0, 'text': '졸이', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 1222.0, 'begin': 26.0, 'end': 26.0}, {'id': 25.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1225.0, 'begin': 27.0, 'end': 27.0}, {'id': 26.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 6.4, 'position': 1228.0, 'begin': 28.0, 'end': 28.0}, {'id': 27.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 1231.0, 'begin': 29.0, 'end': 29.0}, {'id': 28.0, 'text': '.', 'type': 'SP', 'scode': '00', 'weight': 1.0, 'position': 1237.0, 'begin': 30.0, 'end': 30.0}, {'id': 29.0, 'text': '7', 'type': 'SN', 'scode': '00', 'weight': 1.0, 'position': 1238.0, 'begin': 31.0, 'end': 31.0}, {'id': 30.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 1239.0, 'begin': 32.0, 'end': 32.0}], 'word': [{'id': 0.0, 'text': '두릅을', 'type': '', 'begin': 0.0, 'end': 2.0}, {'id': 1.0, 'text': '구운', 'type': '', 'begin': 3.0, 'end': 4.0}, {'id': 2.0, 'text': '팬에', 'type': '', 'begin': 5.0, 'end': 6.0}, {'id': 3.0, 'text': '양념', 'type': '', 'begin': 7.0, 'end': 7.0}, {'id': 4.0, 'text': '재료를', 'type': '', 'begin': 8.0, 'end': 9.0}, {'id': 5.0, 'text': '넣고', 'type': '', 'begin': 10.0, 'end': 11.0}, {'id': 6.0, 'text': '끓어오르면', 'type': '', 'begin': 12.0, 'end': 13.0}, {'id': 7.0, 'text': '구워둔', 'type': '', 'begin': 14.0, 'end': 17.0}, {'id': 8.0, 'text': '두릅', 'type': '', 'begin': 18.0, 'end': 18.0}, {'id': 9.0, 'text': '소고기', 'type': '', 'begin': 19.0, 'end': 20.0}, {'id': 10.0, 'text': '말이를', 'type': '', 'begin': 21.0, 'end': 23.0}, {'id': 11.0, 'text': '넣어', 'type': '', 'begin': 24.0, 'end': 25.0}, {'id': 12.0, 'text': '졸여주세요.7.', 'type': '', 'begin': 26.0, 'end': 32.0}], 'NE': [{'id': 0.0, 'text': '팬', 'type': 'CV_POSITION', 'begin': 5.0, 'end': 5.0, 'weight': 0.535099, 'common_noun': 0.0}, {'id': 1.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 19.0, 'end': 20.0, 'weight': 0.412951, 'common_noun': 0.0}, {'id': 2.0, 'text': '7', 'type': 'QT_ORDER', 'begin': 31.0, 'end': 31.0, 'weight': 0.149244, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '두릅을', 'head': 1.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.786302}, {'id': 1.0, 'text': '구운', 'head': 2.0, 'label': 'VP_MOD', 'mod': [0.0], 'weight': 0.546401}, {'id': 2.0, 'text': '팬에', 'head': 5.0, 'label': 'NP_AJT', 'mod': [1.0], 'weight': 0.804714}, {'id': 3.0, 'text': '양념', 'head': 4.0, 'label': 'NP', 'mod': [], 'weight': 0.607574}, {'id': 4.0, 'text': '재료를', 'head': 5.0, 'label': 'NP_OBJ', 'mod': [3.0], 'weight': 0.660004}, {'id': 5.0, 'text': '넣고', 'head': 6.0, 'label': 'VP', 'mod': [2.0, 4.0], 'weight': 0.850263}, {'id': 6.0, 'text': '끓어오르면', 'head': 11.0, 'label': 'VP', 'mod': [5.0], 'weight': 0.712741}, {'id': 7.0, 'text': '구워둔', 'head': 10.0, 'label': 'VP_MOD', 'mod': [], 'weight': 0.599075}, {'id': 8.0, 'text': '두릅', 'head': 9.0, 'label': 'NP', 'mod': [], 'weight': 0.182217}, {'id': 9.0, 'text': '소고기', 'head': 10.0, 'label': 'NP', 'mod': [8.0], 'weight': 0.451375}, {'id': 10.0, 'text': '말이를', 'head': 11.0, 'label': 'NP_OBJ', 'mod': [7.0, 9.0], 'weight': 0.756562}, {'id': 11.0, 'text': '넣어', 'head': 12.0, 'label': 'VP', 'mod': [6.0, 10.0], 'weight': 0.699029}, {'id': 12.0, 'text': '졸여주세요.7.', 'head': -1.0, 'label': 'VP', 'mod': [11.0], 'weight': 0.000307527}], 'SRL': [{'verb': '굽', 'sense': 1.0, 'word_id': 1.0, 'weight': 0.107489, 'argument': [{'type': 'ARG1', 'word_id': 0.0, 'text': '두릅', 'weight': 0.0979521}, {'type': 'ARG0', 'word_id': 2.0, 'text': '팬', 'weight': 0.117026}]}, {'verb': '넣', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.177562, 'argument': [{'type': 'ARG2', 'word_id': 2.0, 'text': '팬', 'weight': 0.116194}, {'type': 'ARG1', 'word_id': 4.0, 'text': '양념 재료', 'weight': 0.238929}]}, {'verb': '끓어오르', 'sense': 1.0, 'word_id': 6.0, 'weight': 0.0, 'argument': []}, {'verb': '굽', 'sense': 1.0, 'word_id': 7.0, 'weight': 0.271985, 'argument': [{'type': 'ARG1', 'word_id': 10.0, 'text': '구워둔 두릅 소고기 말이', 'weight': 0.271985}]}, {'verb': '넣', 'sense': 1.0, 'word_id': 11.0, 'weight': 0.155779, 'argument': [{'type': 'ARGM-CND', 'word_id': 6.0, 'text': '두릅을 구운 팬에 양념 재료를 넣고 끓어오르면', 'weight': 0.095847}, {'type': 'ARG1', 'word_id': 10.0, 'text': '구워둔 두릅 소고기 말이', 'weight': 0.215711}]}, {'verb': '졸이', 'sense': 1.0, 'word_id': 12.0, 'weight': 0.111562, 'argument': [{'type': 'ARGM-MNR', 'word_id': 11.0, 'text': '두릅을 구운 팬에 양념 재료를 넣고 끓어오르면 구워둔 두릅 소고기 말이를 넣어', 'weight': 0.111562}]}]}, {'id': 32.0, 'reserve_str': '', 'text': ' 완성된 두릅 소고기 말이를 접시에 담고 고명을 올려 장식한 후 맛있게 즐겨주세요.', 'morp': [{'id': 0.0, 'lemma': '완성', 'type': 'NNG', 'position': 1241.0, 'weight': 0.0687054}, {'id': 1.0, 'lemma': '되', 'type': 'XSV', 'position': 1247.0, 'weight': 0.0687054}, {'id': 2.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 1247.0, 'weight': 0.0754069}, {'id': 3.0, 'lemma': '두릅', 'type': 'NNG', 'position': 1251.0, 'weight': 0.0156373}, {'id': 4.0, 'lemma': '소', 'type': 'NNG', 'position': 1258.0, 'weight': 0.119149}, {'id': 5.0, 'lemma': '고기', 'type': 'NNG', 'position': 1261.0, 'weight': 0.119149}, {'id': 6.0, 'lemma': '말', 'type': 'NNG', 'position': 1268.0, 'weight': 0.0476991}, {'id': 7.0, 'lemma': '이', 'type': 'NNG', 'position': 1271.0, 'weight': 0.0476991}, {'id': 8.0, 'lemma': '를', 'type': 'JKO', 'position': 1274.0, 'weight': 0.151936}, {'id': 9.0, 'lemma': '접시', 'type': 'NNG', 'position': 1278.0, 'weight': 0.103902}, {'id': 10.0, 'lemma': '에', 'type': 'JKB', 'position': 1284.0, 'weight': 0.102209}, {'id': 11.0, 'lemma': '담', 'type': 'VV', 'position': 1288.0, 'weight': 0.117627}, {'id': 12.0, 'lemma': '고', 'type': 'EC', 'position': 1291.0, 'weight': 0.0691471}, {'id': 13.0, 'lemma': '고명', 'type': 'NNG', 'position': 1295.0, 'weight': 0.0919433}, {'id': 14.0, 'lemma': '을', 'type': 'JKO', 'position': 1301.0, 'weight': 0.164932}, {'id': 15.0, 'lemma': '올리', 'type': 'VV', 'position': 1305.0, 'weight': 0.0808777}, {'id': 16.0, 'lemma': '어', 'type': 'EC', 'position': 1308.0, 'weight': 0.059419}, {'id': 17.0, 'lemma': '장식', 'type': 'NNG', 'position': 1312.0, 'weight': 0.104946}, {'id': 18.0, 'lemma': '하', 'type': 'XSV', 'position': 1318.0, 'weight': 0.104946}, {'id': 19.0, 'lemma': 'ㄴ', 'type': 'ETM', 'position': 1318.0, 'weight': 0.138753}, {'id': 20.0, 'lemma': '후', 'type': 'NNG', 'position': 1322.0, 'weight': 0.201418}, {'id': 21.0, 'lemma': '맛있', 'type': 'VA', 'position': 1326.0, 'weight': 0.0597995}, {'id': 22.0, 'lemma': '게', 'type': 'EC', 'position': 1332.0, 'weight': 0.0796194}, {'id': 23.0, 'lemma': '즐기', 'type': 'VV', 'position': 1336.0, 'weight': 0.0772869}, {'id': 24.0, 'lemma': '어', 'type': 'EC', 'position': 1339.0, 'weight': 0.0573602}, {'id': 25.0, 'lemma': '주', 'type': 'VX', 'position': 1342.0, 'weight': 0.0485782}, {'id': 26.0, 'lemma': '세요', 'type': 'EF', 'position': 1345.0, 'weight': 0.0536735}, {'id': 27.0, 'lemma': '.', 'type': 'SF', 'position': 1351.0, 'weight': 1.0}], 'WSD': [{'id': 0.0, 'text': '완성되', 'type': 'VV', 'scode': '00', 'weight': 0.0, 'position': 1241.0, 'begin': 0.0, 'end': 1.0}, {'id': 1.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 1247.0, 'begin': 2.0, 'end': 2.0}, {'id': 2.0, 'text': '두릅', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1251.0, 'begin': 3.0, 'end': 3.0}, {'id': 3.0, 'text': '소고기', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1258.0, 'begin': 4.0, 'end': 5.0}, {'id': 4.0, 'text': '말이', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1268.0, 'begin': 6.0, 'end': 7.0}, {'id': 5.0, 'text': '를', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 1274.0, 'begin': 8.0, 'end': 8.0}, {'id': 6.0, 'text': '접시', 'type': 'NNG', 'scode': '00', 'weight': 0.0, 'position': 1278.0, 'begin': 9.0, 'end': 9.0}, {'id': 7.0, 'text': '에', 'type': 'JKB', 'scode': '00', 'weight': 1.0, 'position': 1284.0, 'begin': 10.0, 'end': 10.0}, {'id': 8.0, 'text': '담', 'type': 'VV', 'scode': '01', 'weight': 9.8, 'position': 1288.0, 'begin': 11.0, 'end': 11.0}, {'id': 9.0, 'text': '고', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1291.0, 'begin': 12.0, 'end': 12.0}, {'id': 10.0, 'text': '고명', 'type': 'NNG', 'scode': '01', 'weight': 2.2, 'position': 1295.0, 'begin': 13.0, 'end': 13.0}, {'id': 11.0, 'text': '을', 'type': 'JKO', 'scode': '00', 'weight': 1.0, 'position': 1301.0, 'begin': 14.0, 'end': 14.0}, {'id': 12.0, 'text': '올리', 'type': 'VV', 'scode': '01', 'weight': 6.6, 'position': 1305.0, 'begin': 15.0, 'end': 15.0}, {'id': 13.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1308.0, 'begin': 16.0, 'end': 16.0}, {'id': 14.0, 'text': '장식하', 'type': 'VV', 'scode': '03', 'weight': 2.2, 'position': 1312.0, 'begin': 17.0, 'end': 18.0}, {'id': 15.0, 'text': 'ㄴ', 'type': 'ETM', 'scode': '00', 'weight': 1.0, 'position': 1318.0, 'begin': 19.0, 'end': 19.0}, {'id': 16.0, 'text': '후', 'type': 'NNG', 'scode': '08', 'weight': 3.2, 'position': 1322.0, 'begin': 20.0, 'end': 20.0}, {'id': 17.0, 'text': '맛있', 'type': 'VA', 'scode': '00', 'weight': 0.0, 'position': 1326.0, 'begin': 21.0, 'end': 21.0}, {'id': 18.0, 'text': '게', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1332.0, 'begin': 22.0, 'end': 22.0}, {'id': 19.0, 'text': '즐기', 'type': 'VV', 'scode': '01', 'weight': 1.0, 'position': 1336.0, 'begin': 23.0, 'end': 23.0}, {'id': 20.0, 'text': '어', 'type': 'EC', 'scode': '00', 'weight': 1.0, 'position': 1339.0, 'begin': 24.0, 'end': 24.0}, {'id': 21.0, 'text': '주', 'type': 'VX', 'scode': '01', 'weight': 5.2, 'position': 1342.0, 'begin': 25.0, 'end': 25.0}, {'id': 22.0, 'text': '세요', 'type': 'EF', 'scode': '00', 'weight': 1.0, 'position': 1345.0, 'begin': 26.0, 'end': 26.0}, {'id': 23.0, 'text': '.', 'type': 'SF', 'scode': '00', 'weight': 1.0, 'position': 1351.0, 'begin': 27.0, 'end': 27.0}], 'word': [{'id': 0.0, 'text': '완성된', 'type': '', 'begin': 0.0, 'end': 2.0}, {'id': 1.0, 'text': '두릅', 'type': '', 'begin': 3.0, 'end': 3.0}, {'id': 2.0, 'text': '소고기', 'type': '', 'begin': 4.0, 'end': 5.0}, {'id': 3.0, 'text': '말이를', 'type': '', 'begin': 6.0, 'end': 8.0}, {'id': 4.0, 'text': '접시에', 'type': '', 'begin': 9.0, 'end': 10.0}, {'id': 5.0, 'text': '담고', 'type': '', 'begin': 11.0, 'end': 12.0}, {'id': 6.0, 'text': '고명을', 'type': '', 'begin': 13.0, 'end': 14.0}, {'id': 7.0, 'text': '올려', 'type': '', 'begin': 15.0, 'end': 16.0}, {'id': 8.0, 'text': '장식한', 'type': '', 'begin': 17.0, 'end': 19.0}, {'id': 9.0, 'text': '후', 'type': '', 'begin': 20.0, 'end': 20.0}, {'id': 10.0, 'text': '맛있게', 'type': '', 'begin': 21.0, 'end': 22.0}, {'id': 11.0, 'text': '즐겨주세요.', 'type': '', 'begin': 23.0, 'end': 27.0}], 'NE': [{'id': 0.0, 'text': '소고기', 'type': 'CV_FOOD', 'begin': 4.0, 'end': 5.0, 'weight': 0.412953, 'common_noun': 0.0}], 'NE_Link': [], 'dependency': [{'id': 0.0, 'text': '완성된', 'head': 3.0, 'label': 'VP_MOD', 'mod': [], 'weight': 0.657186}, {'id': 1.0, 'text': '두릅', 'head': 2.0, 'label': 'NP', 'mod': [], 'weight': 0.422012}, {'id': 2.0, 'text': '소고기', 'head': 3.0, 'label': 'NP', 'mod': [1.0], 'weight': 0.501779}, {'id': 3.0, 'text': '말이를', 'head': 5.0, 'label': 'NP_OBJ', 'mod': [0.0, 2.0], 'weight': 0.722585}, {'id': 4.0, 'text': '접시에', 'head': 5.0, 'label': 'NP_AJT', 'mod': [], 'weight': 0.615259}, {'id': 5.0, 'text': '담고', 'head': 7.0, 'label': 'VP', 'mod': [3.0, 4.0], 'weight': 0.673191}, {'id': 6.0, 'text': '고명을', 'head': 7.0, 'label': 'NP_OBJ', 'mod': [], 'weight': 0.815286}, {'id': 7.0, 'text': '올려', 'head': 8.0, 'label': 'VP', 'mod': [5.0, 6.0], 'weight': 0.724438}, {'id': 8.0, 'text': '장식한', 'head': 9.0, 'label': 'VP_MOD', 'mod': [7.0], 'weight': 0.608074}, {'id': 9.0, 'text': '후', 'head': 11.0, 'label': 'NP_AJT', 'mod': [8.0], 'weight': 0.518633}, {'id': 10.0, 'text': '맛있게', 'head': 11.0, 'label': 'VP_AJT', 'mod': [], 'weight': 0.544686}, {'id': 11.0, 'text': '즐겨주세요.', 'head': -1.0, 'label': 'VP', 'mod': [9.0, 10.0], 'weight': 0.00334696}], 'SRL': [{'verb': '완성', 'sense': 1.0, 'word_id': 0.0, 'weight': 0.301484, 'argument': [{'type': 'ARG1', 'word_id': 3.0, 'text': '완성된 두릅 소고기 말이', 'weight': 0.301484}]}, {'verb': '담', 'sense': 1.0, 'word_id': 5.0, 'weight': 0.20766, 'argument': [{'type': 'ARG1', 'word_id': 3.0, 'text': '완성된 두릅 소고기 말이', 'weight': 0.273164}, {'type': 'ARG2', 'word_id': 4.0, 'text': '접시', 'weight': 0.142156}]}, {'verb': '올리', 'sense': 3.0, 'word_id': 7.0, 'weight': 0.20606, 'argument': [{'type': 'ARG1', 'word_id': 6.0, 'text': '고명', 'weight': 0.20606}]}, {'verb': '장식', 'sense': 1.0, 'word_id': 8.0, 'weight': 0.113554, 'argument': [{'type': 'ARGM-MNR', 'word_id': 7.0, 'text': '완성된 두릅 소고기 말이를 접시에 담고 고명을 올려', 'weight': 0.113554}]}, {'verb': '즐기', 'sense': 1.0, 'word_id': 11.0, 'weight': 0.25955, 'argument': [{'type': 'ARGM-TMP', 'word_id': 9.0, 'text': '완성된 두릅 소고기 말이를 접시에 담고 고명을 올려 장식한 후', 'weight': 0.25955}]}]}]

    sequence_list = parse_node_section(entity_mode, is_srl, node_list)

    print(str(json.dumps(sequence_list, ensure_ascii=False)))
    #print("\n")
    #print(json_object)

if __name__ == "__main__":
    main()