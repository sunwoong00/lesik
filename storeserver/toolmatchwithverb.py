import urllib3
import json
#from kss import split_sentences
import os.path
import re

#global getmostrecenttool
#가장 최근에 이루어진 조리도구, 행동 번호를 계속해서 트레킹 하기 위해서 사용
class counttrackoftoolnum:
    getmostrecenttool = 1
###############################################################

#행동 관련된 내용을 딕셔너리로 가져오는 부분
def parse_cooking_act_dict(file_path):
    file_exists = os.path.exists(file_path)
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8')
    delim = ">"
    act_dict = {}
    act_score_dict = {}
    for line in f.readlines():
        if("[" in line):
            continue
        line = line.replace("\n", "")
        if delim in line:
            sp_line = line.split(delim)
            act_dict[sp_line[0]] = sp_line[1]
            act_score_dict[sp_line[1]] = sp_line[2]
        else:
            act_dict[line] = line
    f.close()
    return act_dict, act_score_dict
###############################################################

###행동 딕션너리에 태깅 되어 있는 번호들을 분리 작업 하기 위한 코드###
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
###############################################################

###행동 단어의 번호를 알아내서 돌려주는 함수###
def checkifexist(word, dict):
    if word in dict.keys():
        index = list(dict.keys()).index(word)
        #print(list(dict.keys()).index(word))
        #print(list(dict.values())[index])
        #print(list(dict.keys())[index])
        scorefortool = list(dict.values())[index]
        return scorefortool
###############################################################

###단어의 일부만 아니라 전체가 일치하는 확인 하기 위한 함수 예: 양파를 채썰다, 썰다 X, 채썰다 O ###
def isWordPresent(sentence, word):
    #return True
    # To break the sentence in words
    s = sentence.split(" ")
    #s = str(sentence[0])
    #print("isWordPresent", sentence, word)
    for i in s:
 
        # Comparing the current word
        # with the word to be searched
        if (word in i):
            return True
    return False
###############################################################

###단어의 일부만 아니라 전체가 일치하는 확인 하기 위한 함수 예: 양파를 채썰다, 썰다 X, 채썰다 O ###
def isActualTool(word, sentence, ingreCollectList, listofingre):
    detection = sentence.split(" ")
    #print("detection", detection)
    for checkdetect in range(len(detection)):
        if word in detection[checkdetect]:
            if (word == "타월" or word == "타올") and ("종이" in detection[checkdetect] or "키친" in detection[checkdetect]):
                return False
            #print("hi", checkdetect, ingreCollectList, detection[checkdetect])
            for ingredetect in range(len(ingreCollectList)):
                #print(ingreCollectList[ingredetect])
                if str(ingreCollectList[ingredetect]) in detection[checkdetect]:
                    #print("found error", detection[checkdetect])
                    return False
            for ingredetect in range(len(listofingre)):
                #print(listofingre[ingredetect])
                if str(listofingre[ingredetect]) in detection[checkdetect]:
                    #print("found error", detection[checkdetect])
                    return False
    return True
###############################################################

###조리도구/위치 매칭 함수###
def matchtoolwithaction(array, cooking_act_dict, checkaction, checktoolmain, checktoolsub, listofingre):
    keylist = []
    valuelist = []
    current_action_tool = []
    check_if_used_tool = []
    tool_used_in_sentence = ""
    tool_used_in_sentence_final_array = []
    just_test_track_if_none = []
    zone_divide = []
    keep_action_num = []
    save_previous_used_sentence = 0
    
    ###각 행동액션 번호와 매칭되는 도구를 기본설정 도구로 세팅해둔다###
    k_list = list(checktoolmain.keys())
    v_list = list(checktoolmain.values())
    subtool_k_list = list(checktoolsub.keys())
    subtool_v_list = list(checktoolsub.values())
    for current in range(5):
        current_action_tool.append("")
        check_if_used_tool.append(0)
    for current in range(len(v_list)):
        current_action_tool[int(v_list[current])] = k_list[int(current)]
    ###############################################################
    
    ###dictionary 형태에서 key 와 value를 분류해 각각 array에 저장###
    for key, value in cooking_act_dict.items():
        keylist.append(key) #이미 전처리해서 이 친구는 필요없다
        valuelist.append(value)
    ###############################################################
    #print(valuelist)
     #섞다 처럼 2가지 도구가 가능한 경우 가장 최근에 사용된 도구로 매칭
    ###각 문장을 돌려 문장에 있는 행동 번호를 돌려온다. 그 번호를 이용해 맞는 도구를 찾고 업데이트###

    if array is None:
        return

    for i in range(len(array)):
        sentences = array[i]["sentence"]
        ingreCollectList = array[i]["ingre"]
        seasoningCollect = array[i]["seasoning"]
        checkzone = array[i]["zone"]
        act = array[i]["act"]
        if_extra_tool = []
        select_if_else = 0
        check_more_than_one = 0
        check_if_tool_found = 0
        tool_used_in_sentence_final_array.append("")
        zone_divide.append("")
        just_test_track_if_none.append("")
        ###만약에 문단에 도구가 새로 등장하면 기본도구를 등장한 도구로 바꾸기###
        for checksubtool in range(len(subtool_k_list)):
            if subtool_k_list[checksubtool] in sentences:
                #print(str(subtool_k_list[checksubtool]), str(sentences))
                if(isActualTool(str(subtool_k_list[checksubtool]), str(sentences), ingreCollectList, seasoningCollect) == False):
                    #print("\n\n\n")
                    break

                if subtool_k_list[int(checksubtool)] == "냉장":
                    subtool_k_list[int(checksubtool)]  = "냉장고"
                    
                just_test_track_if_none[i] = str(subtool_k_list[checksubtool])
                current_action_tool[int(subtool_v_list[checksubtool])] = subtool_k_list[int(checksubtool)]
                #print(current_action_tool[int(subtool_v_list[checksubtool])])
                if_extra_tool.append(subtool_k_list[int(checksubtool)])
                check_if_used_tool[int(subtool_v_list[checksubtool])] = counttrackoftoolnum.getmostrecenttool
                save_previous_used_sentence = int(subtool_v_list[checksubtool])
                counttrackoftoolnum.getmostrecenttool += 1
                check_more_than_one += 1
                check_if_tool_found = 1
                #print(check_if_used_tool)
        check_knife = 0
        #if(check_more_than_one >= 2):
            #print("this is correct", sentences, if_extra_tool)  
        ###현재 저장된 도구정보로 행동과 매칭해 도구-행동 각 문단마다 진행###
        
        for k in valuelist:
            if k in act and (isWordPresent(str(act), str(k)) == True):
                if((act == "물기를 빼다" or "헹구다") and (check_if_tool_found == 0)):
                    current_action_tool[0] = "싱크대"
                    if current_action_tool[save_previous_used_sentence] != "싱크대":
                        check_if_used_tool[save_previous_used_sentence] -= 1
                    check_knife = 1
                    print(sentences)
                elif("자르다" in act):
                    current_action_tool[1] = "가위"
                    check_knife = 1
                    #print(sentences)
                #만약에 동사가 하다이면 정확히 어떤건지 잘 모름 (하다 특성상 아예 어디로 가야될지 모르기에 가장 최선은 전 문장을 따라 수정)
                if("하다" in act):
                    print("하다 is found")
                    tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                    continue
                    #print(sentences)

                ###행동의 번호를 가지고 오는 함수 및 변수###
                numbermatch = checkifexist(k, checkaction)
                #print(k)
                ###만약에 행동이 두가지의 도구가 가능한 경우 예:섞다###
                if("," in numbermatch):
                    select_if_else = 1
                    #print(check_if_used_tool)
                    #print(k)
                    ###선택중에 가장 최근에 나온 숫자를 기준으로함, 예: 섞다에서 "팬"이 먼자 나오면 check_if_used_tool 숫자가 더큼###
                    two_option = str(numbermatch).split(",")
                    maxvalue = 0
                    saveindex = 0
                    for findmax in two_option:
                        #print("checklist", check_if_used_tool[int(findmax)])
                        #print("currentmax", maxvalue)
                        #print("findmax", findmax)
                        if int(check_if_used_tool[int(findmax)]) > int(maxvalue):
                            maxvalue = int(check_if_used_tool[int(findmax)])
                            saveindex = int(findmax)

                    if(checkzone == "화구존" and (saveindex != 3) and check_if_tool_found == 0):
                        tool_used_in_sentence_final_array[i] = ""
                        continue
                    elif("칼집" in sentences and "넣다" in act):
                        #print("\n\nhi]n]n")
                        saveindex = 1
                        maxvalue = 1
                        check_if_used_tool[1] -= 1
                    #print(current_action_tool[int(two_option[0])])
                    #print(maxvalue)
                    if(maxvalue == 0):
                        saveindex = two_option[0]
                        tool_used_in_sentence = current_action_tool[int(saveindex)]
                        if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]:
                            keep_action_num.append(numbermatch)
                            tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                            if(int(saveindex) == 3):
                                zone_divide[i] += "화구"
                            else:
                                zone_divide[i] += "전처리"
                    else:
                        print(saveindex, act)
                        print(current_action_tool, check_if_used_tool)
        
                        tool_used_in_sentence = current_action_tool[int(saveindex)]
                        if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]:
                            keep_action_num.append(numbermatch)
                            tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                            if(int(saveindex) == 3):
                                zone_divide[i] += "화구"
                            else:
                                zone_divide[i] += "전처리"
                            if(check_knife == 1):
                                current_action_tool[1] = "도마, 칼"
                                #print("\nchangedback\n", current_action_tool[1], sentences[i]["sentence"])
                                check_knife = 0
                            if int(saveindex) == 1:
                                check_knife = 1
                                #print("\nkk\n")
                    ###아래 코드는 위 max와 같으나 혹시 모른 상황을 위해 백업으로 남겨둠###
                    #if(check_if_used_tool[int(two_option[0])] > check_if_used_tool[int(two_option[1])]):
                        #tool_used_in_sentence = current_action_tool[int(two_option[0])]
                        #if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]:
                            #tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                    #elif(check_if_used_tool[int(two_option[0])] < check_if_used_tool[int(two_option[1])]):
                        #tool_used_in_sentence = current_action_tool[int(two_option[1])]
                        #if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]:
                            #tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                    ###############################################################
                    check_if_used_tool[int(saveindex)] = counttrackoftoolnum.getmostrecenttool
                    save_previous_used_sentence = int(saveindex)
                    counttrackoftoolnum.getmostrecenttool += 1
                ###행동이 하나의 도구에 연결되는 경우###
                else:
                    ###가장 최근에 사용된 도구를 판단하기 위해 도구 번호에 매칭되는 인덱스 값을 올려줌. 가장 큰 숫자가 가장 최근 번호###
                    check_if_used_tool[int(numbermatch)] = counttrackoftoolnum.getmostrecenttool
                    save_previous_used_sentence = int(numbermatch)
                    counttrackoftoolnum.getmostrecenttool += 1
                    ###만약에 행동 번호가 하나인 경우는 그냥 인덱스에 도구를 추가함####
                    tool_used_in_sentence = current_action_tool[int(numbermatch)]
                    #print("check one", tool_used_in_sentence)
                    if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]:
                        keep_action_num.append(numbermatch)
                        tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                        if(int(numbermatch) == 3):
                                zone_divide[i] += "화구"
                        else:
                            zone_divide[i] += "전처리"
                        
                        if int(numbermatch) == 1:
                            check_knife = 1
                            #print("\nkk\n")
                        if(check_knife == 1):
                            current_action_tool[1] = "도마, 칼"
                            #print("\nchangedback\n", current_action_tool, sentences)
                            check_knife = 0
                            break

        if(check_more_than_one >= 2):
            for kk in range(check_more_than_one):
                if if_extra_tool[kk] not in tool_used_in_sentence_final_array[i]:
                    tool_used_in_sentence_final_array[i] += ", " + if_extra_tool[kk]
                
            if select_if_else == 1:
                #current_action_tool[int(saveindex)] = if_extra_tool[0]
                #check_if_used_tool[int(saveindex)] = counttrackoftoolnum.getmostrecenttool
                #counttrackoftoolnum.getmostrecenttool += 1
                print("test if changed", current_action_tool[int(saveindex)],if_extra_tool )
            else:
                #current_action_tool[int(numbermatch)] = if_extra_tool[0]
                #check_if_used_tool[int(numbermatch)] = counttrackoftoolnum.getmostrecenttool
                #counttrackoftoolnum.getmostrecenttool += 1
                actat = check_more_than_one
                ###############################################################

    #print("\n", tool_used_in_sentence_final_array, "\n", just_test_track_if_none, "\n")
    track_count = 0
    for i in range(len(tool_used_in_sentence_final_array)):
        if(tool_used_in_sentence_final_array[i] == ""):
            track_count += 1
            #print(track_count)
        elif(tool_used_in_sentence_final_array[i] != "" and (track_count != 0)):
            recorded_tool = tool_used_in_sentence_final_array[i]
            #print(track_count+i)
            for j in range((i-track_count), i):
                #print(tool_used_in_sentence_final_array[j])
                tool_used_in_sentence_final_array[j] = recorded_tool
            track_count = 0

    for i in range(len(tool_used_in_sentence_final_array)):
        tool_used_in_sentence_final_array[i] = list(tool_used_in_sentence_final_array[i].split("\n"))        
    #print(tool_used_in_sentence_final_array)


    return (tool_used_in_sentence_final_array, zone_divide)
    ###############################################################
    #print((checkaction))
    #for i in range(len(sentences)):
        #for j in range(len(checkaction)):
            #print()
###############################################################

############################################################################################################################################

def matchresult(array, listofingre):
    #print(array["sentence"])
    cooking_act_dict, act_score_dict = parse_cooking_act_dict("./hajong/action_number.txt")
    tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("./hajong/tool_number.txt")

    #print(listofingre)
    listofingre = list(listofingre)
    matchtoolwithactionresult = matchtoolwithaction(array, cooking_act_dict, act_score_dict, tool_match_main_dic, tool_match_sub_dic, listofingre)
    #print(matchtoolwithactionresult)
    return matchtoolwithactionresult


#cooking_act_dict, act_score_dict = parse_cooking_act_dict("./hajong/action_number.txt")
#tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("./hajong/tool_number.txt")

#print(cooking_act_dict)
#array = test.main()
#matchtoolwithactionresult = matchtoolwithaction(array, cooking_act_dict, act_score_dict, tool_match_main_dic, tool_match_sub_dic)


#print(temp_sentence_split.main())

#print(matchtoolwithactionresult)
#print(array)