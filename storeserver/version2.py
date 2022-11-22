import urllib3
import json
import os.path
import random
from jamo import h2j, j2hcj
import toolmatchwithverb as toolmatchwverb
from flask import Flask, jsonify, render_template, request, make_response
from datetime import date
from io import StringIO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
SECRETS_PATH = os.path.join(ROOT_DIR, '래식/lesik_ver2/secrets.json')

secrets = json.loads(open(SECRETS_PATH).read())

###################Etri##########################################
open_api_url = "http://aiopen.etri.re.kr:8000/WiseNLU"            
access_key = str(secrets["access_key"])        
analysis_code = "SRL"                                           
#################################################################

#global getmostrecenttool
class counttrackoftoolnum:
    getmostrecenttool = 1

def get_list_from_file(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(os.getcwd() + "/" + file_path, 'r', encoding='utf-8')
    tmp_list = f.readlines()
    tmp_list = list(map(lambda elem: elem.replace("\n", ""), tmp_list))
    f.close()
    return tmp_list

###Etri 쓰는 코드 >> 먼저 전체 텍스트를 돌려야함.
###Etri 쓰는 코드 >> 먼저 전체 텍스트를 돌려야함.
def get_etri(text):
    requestJson = {
        "access_key": access_key,
        "argument": {
            "text": text,
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
    json_object = json.loads(str(response.data ,"utf-8"))
    return json_object

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

def before_sequencing(list):
    remove_set = {'\n'}
    list = [i for i in list if i not in remove_set]
    new_list = []
    nnew_list = []
    for sent in list:
        if sent[0].isdigit() == True:
            new_list.append(sent[3:len(sent)-1])
    
    for sent in new_list:
        nnew_list.extend(sent.split(". "))
    return nnew_list

def before_ingre(list):
    remove_set = {'\n'}
    new_list = []

    list = [i for i in list if i not in remove_set]

    for ingre in list:
        temp = ingre.split(" ")
        ntemp = temp[0:len(temp)-1]
        new_list.append(' '.join(s for s in ntemp))

    return new_list

def list_clean(list):

    for value in list:
        if value == "":
            list.remove("")
    for idx in range(len(list)):
        list[idx] = list[idx].replace(u'\xa0', u' ')
    return list

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

def create_sequence(node_list):
    seq_list = []
    for node in node_list:
        prev_seq_id = -1
        for s_ele in node['WSD']:
            if s_ele['type'] == 'VV':
                act_id = int(s_ele['id'])
                if node['WSD'][act_id + 1]['type'] == 'ETM' and node['WSD'][act_id + 2]['text'] != '후':
                    continue
                act = s_ele['text']
                # print(act_id , act)
                # print("11111111111111")
                if act in cooking_act_dict:
                    # print(act)
                    for w_ele in node['word']:
                        if w_ele['begin'] <= s_ele['begin'] and s_ele['end'] <= w_ele['end']:
                            act_id = w_ele['end']
                    seq_dict = {'duration': "", 'act': act, 'tool': [], 'ingre': [], 'seasoning': [], 'volume': [], 'temperature': [],
                                'zone': "", "start_id": prev_seq_id + 1, "end_id": act_id, "act_id" : act_id, "sentence": "", "standard":"", "top_class":""}
                    seq_list.append(seq_dict)
                    prev_seq_id = act_id
    for node in node_list:
        find_sentence(node, seq_list)

    seq_list = adj_edit(seq_list)
    generalize(seq_list)
    # print(seq_list)
    ## 관형어 처리해야하는 부분
    return(seq_list)

def adj_edit(sequence_list):
    slice = ["나누다","썰다","채썰다","슬라이스", "다이스", "가르다", "다지다","자르다","쪼개다","가르다","뜯다","찢다","부수다","으깨다","내다","갈다"]
    put = ["깔다","붙이다","채우다","끼얹다","담그다","얹다","붓다","덮다","두르다","감싸다","곁들이다","뿌리다","올리다","입히다","풀다","넣다", "첨가하다", "담다"]
    nn_list = []
    way = ""
    what = ""
    to = ""
    for value in sequence_list:
        temps = []
        n_list = []
        t_list = []
        begin = 0
        temp = get_etri(value['sentence'])['return_object']['sentence'][0]
        for val in temp['word']:
            begin = val['begin']
            for val2 in temp['WSD']:
                if begin == val2['begin'] and val2['type'] == "VV" and val['id'] < len(value['sentence'].split())-2:
                    try:
                        cooking_act_dict[val2['text']]
                        break_po = 0
                        for idx in range(int(val['id'] + 1),len(value['sentence'].split())):
                            for val3 in temp['WSD']:
                                if temp['word'][idx]['begin'] == val3['begin']:
                                    if "NN" in val3['type']:
                                        for val4 in temp['WSD']:
                                            if temp['word'][idx]['end'] == val4['end']:

                                                if cooking_act_dict[val2['text']] in slice:
                                                    for srl in temp['SRL']:
                                                        try:
                                                            if srl['verb'] == val2['text']:
                                                                for arg in srl['argument']:
                                                                    try:
                                                                        if arg['type'] == "ARGM-MNR":
                                                                            way = arg['text']
                                                                    except:
                                                                        pass
                                                        except:
                                                            pass
                                                
                                                elif cooking_act_dict[val2['text']] in put:
                                                    for srl in temp['SRL']:
                                                        try:
                                                            if srl['verb'] == val2['text']:
                                                                for arg in srl['argument']:
                                                                    try:
                                                                        if arg['type'] == "ARG1":
                                                                            what = arg['text']
                                                                        elif arg['type'] == "ARG2" or arg['type'] == "ARG0":
                                                                            to = arg['text']
                                                                    except:
                                                                        pass
                                                        except:
                                                            pass

                                                if (val4['type'] != "SP" and val4['text'] != "와" and val4['text'] != "과") or cooking_act_dict[val2['text']] in put:
                                                    if(cooking_act_dict[val2['text']] in put):
                                                        if val2['text'] not in n_list:
                                                            n_list.append(val2['text'])
                                                        n_list.append(to + '에')
                                                        if len(j2hcj(h2j(what[-1]))) == 3:
                                                            n_list.append(what + '을')
                                                        else:
                                                            n_list.append(what + '를')
                                                    else:
                                                        if val2['text'] not in n_list:
                                                            n_list.append(val2['text'])
                                                        if len(j2hcj(h2j(val3['text'][-1]))) == 3:
                                                            n_list.append(val3['text'] + '을')
                                                        else:
                                                            n_list.append(val3['text'] + '를')
                                                        if cooking_act_dict[val2['text']] in slice:
                                                            if way != "" and way not in n_list:
                                                                n_list.append(way)
                                                    break_po = 1
                                                    temps.append(n_list)
                                                    n_list = []
                                                    break
                                                else:
                                                    if "NN" not in temp['WSD'][temp['WSD'].index(val4) + 1]['type']:
                                                        break_po = 1
                                                    if val['text'] not in n_list:
                                                        n_list.append(val2['text'])                                                
                                                    if len(j2hcj(h2j(val3['text'][-1]))) == 3:
                                                        n_list.append(val3['text'] + '을')
                                                    else:
                                                        n_list.append(val3['text'] + '를')
                                                    if cooking_act_dict[val2['text']] in slice:
                                                        if way != "" and way not in n_list:
                                                            n_list.append(way)
                                                    temps.append(n_list)
                                                    n_list = []
                                                    continue
                                            if break_po == 1:
                                                break
                                if break_po == 1:
                                    break
                    except:
                        pass
        try:
            for lists in temps:
                asd =[]
                asd.extend(lists[1:])
                asd.append(lists[0])
                t_list.append(asd)
        except:
            pass
            print()
        for lists in t_list:
            result = ' '.join(s for s in lists)
            temp = {'duration': "", 'act': lists[-1], 'tool': [], 'ingre': [], 'seasoning': [], 'volume': [], 'temperature': [],'zone': "", "start_id": 0, "end_id": 0, "act_id" : 0, "sentence": result, "standard":"", "top_class":""}
            nn_list.append(temp)
        nn_list.append(value)
    return nn_list

# def same_time(sequence_list):
#     nn_list = []
#     for value in sequence_list:



def generalize(sequence_list):
    for seq in sequence_list:
        act = cooking_act_dict[seq['act']]
        if "(" in seq['sentence']:
            continue
        temp = seq['sentence'].split()
        temp[-1] = act
        result = ' '.join(s for s in temp)
        sequence_list[sequence_list.index(seq)]['sentence'] = result
    return 0


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
        for w_ele in node['word']:
            text = w_ele['text']
            begin = w_ele['begin']
            end = w_ele['end']
            if start_id <= begin <= end_id:
                word_list.append(text)
            # else:
            #     if end_id < end:
            #         if next_seq_id < end_id or end < next_seq_id:
            #             word_list.append(text)

        sequence_list[i]['sentence'] = " ".join(word_list)
        sequence_list[i]['sentence'] = delete_bracket(sequence_list[i]['sentence'])
        prev_seq_id = sequence_list[i]['end_id']

    return sequence_list

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

def divide_tool_num_text(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    tool_dict_main = {}
    tool_dict_sub = {}
    check_sub = 0
    for line in f.readlines():
        if("[" in line):
            check_sub = 1
            continue

        if(check_sub == 1):
            line = line.replace("\n", "")
            if delim in line:
                sp_line = line.split(delim)
                tool_dict_sub[sp_line[0]] = sp_line[1]
            else:
                tool_dict_sub[line] = line
        elif(check_sub == 0):
            line = line.replace("\n", "")
            if delim in line:
                sp_line = line.split(delim)
                tool_dict_main[sp_line[0]] = sp_line[1]
            else:
                tool_dict_main[line] = line
    f.close()
    return tool_dict_main, tool_dict_sub

def make_dict(list):
    dict = []
    for i in range(len(list)):        
        dict.append({'tool' : '', 'seq': list[i], 'time': ''})
    return dict

def finalresult(data):
    #print("hi")

    global cooking_act_dict, act_score_dict , tool_match_main_dic, tool_match_sub_dic, newcooking_act_dict, newact_score_dict
    cooking_act_dict, act_score_dict = parse_cooking_act_dict("labeling/cooking_act.txt")
    newcooking_act_dict, newact_score_dict = parse_cooking_act_dict("hajong/action_number.txt")    
    tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("hajong/tool_number.txt")
    # list = text.split(". ")
    data = str(data)
    #data.encode('utf-8')
    f = StringIO(data)
    lines = f.readlines()
    #print(lines)
    lines = [i.replace('\r','') for i in lines]
    #print(lines)
    ingreCollectList = []
    #print(lines)
    for readingre in lines:
        if("[기본 재료]" in readingre):
            #print("found 기본재료")
            continue
        elif("[기본재료]" in readingre):
            #print("found 기본재료")
            continue
        elif("[" in readingre):
            #print("found stop [", readingre)
            break
        else:
            #print(readingre)
            #print("hihihi")
            ingreSentenceSplit = str(readingre).split(" ")
            #print(ingreSentenceSplit)
            ingreCollectList.append(ingreSentenceSplit[0])
        #print(readingre)

    print("ingreCollectList", ingreCollectList)

    index1 = lines.index("[조리방법]\n")
    seq = lines[index1 + 1: len(lines)]


    indexes = []
    seq_list = []
    seq = before_sequencing(seq)
    list = list_clean(seq)
    result = ' '.join(s for s in list)
    
    node_list = get_etri(result).get("return_object").get("sentence")
    # print(node_list)
    seq_list = create_sequence(node_list)
    matchtoolwithactionresult, actionzone = toolmatchwverb.matchresult(seq_list, ingreCollectList)
    print(matchtoolwithactionresult)
    # C:\Users\hajon\OneDrive\성균관\산학협력프로젝트\래식\lesik_ver2\static\recipe\ko\가지 솥밥.txt
    for i in range(len(seq_list)):
        seq_list[i]["tool"] = matchtoolwithactionresult[i]
        seq_list[i]["zone"] = actionzone[i]

    returndict = {"hi" : []}
    returndict["hi"] = seq_list
    print(returndict)
    return returndict
    #return seq_list