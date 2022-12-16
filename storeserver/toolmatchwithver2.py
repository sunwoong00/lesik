import urllib3
import json
import os.path
import re


###############################################################
#toolmatchwithbverb와 비슷한 로직을 가지고 있기 때문에 코드 변수등 어떤 로직으로 이루어져있는지 확인하고싶으면 toolmatchwithbverb을 확인하기 바람
###############################################################

#global getmostrecenttool
#가장 최근에 이루어진 조리도구, 행동 번호를 계속해서 트레킹 하기 위해서 사용
class counttrackoftoolnum:
    getmostrecenttool = 1
    foundtoolsentence = ""
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
 
    for i in s:
 
        # Comparing the current word
        # with the word to be searched
        if (i == word):
            return True
    return False
###############################################################

###단어의 일부만 아니라 전체가 일치하는 확인 하기 위한 함수 예: 양파를 채썰다, 썰다 X, 채썰다 O ###
def isActualTool(word, sentence, ingreCollectList):
    detection = sentence.split(" ")
    #print("detection", detection)
    for checkdetect in range(len(detection)):
        if word in detection[checkdetect]:
            if (word == "타월" or word == "타올") and ("종이" in detection[checkdetect] or "키친" in detection[checkdetect]):
                return False
            elif len(word) == 1 or len(word) == 2 or len(word) == 3:
                print(word, counttrackoftoolnum.foundtoolsentence)
                if word in counttrackoftoolnum.foundtoolsentence:
                    print("found repeat")
                    return False
            #print("hi", checkdetect, ingreCollectList, detection[checkdetect])
            for ingredetect in range(len(ingreCollectList)):
                #print(ingreCollectList[ingredetect], "|", detection[checkdetect], "|", word)
                if str(ingreCollectList[ingredetect]) in detection[checkdetect]:
                    #print("found error", detection[checkdetect])
                    return False
                elif word in str(ingreCollectList[ingredetect]):
                    #print("found error", detection[checkdetect])
                    return False

    counttrackoftoolnum.foundtoolsentence += word + " "
    return True
###############################################################

###조리도구/위치 매칭 함수###
def matchtoolwithaction(sentences, cooking_act_dict, checkaction, checktoolmain, checktoolsub, ingreCollectList):
    
    keylist = [] #cookingact.txt 추출 이후 행동 원 형태 저장을 위한 배열 "썰, 갈"
    valuelist = [] #cookingact.txt 이후 행동 다듬은 형태 저장을 위한 배열 "썰다, 갈다"
    current_action_tool = [] #현재 사용 도구를 저장하기 위한 배열, 총 5가지 번호:0,1,2,3,4가 존재, 그리고 그 번호에 해당하는 사용된 도구를 넣음 ("","","오븐","","")
    check_if_used_tool = [] #번호 0,1,2,3,4를 0으로 세팅해두고 가장 최근에 사용된 번호에 해당하는 도구의 배열 숫자를 증가시킴 (0,0,1,0,0)
    tool_used_in_sentence = "" #문장에서 사용된 도구를 저장
    tool_used_in_sentence_final_array = [] #문장에서 사용된 도구를 string -> array 로 변환
    just_test_track_if_none = [] 
    zone_divide = [] #존 나누기 함수, 하지만 더 이상 사용 X
    keep_action_num = []
    actRecordArray = []
    save_previous_used_sentence = 0
    remember_actNum_for_adding = [] #마지막 부분에 화구존이고 도구 인덱스가 3번이 아닌 경우에 뒷문장에서 도구가 발견된 경우에 그 도구로 지정을 하기 위해 동작 인덱스 번호를 기록해두는 배열
    
    
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

    if sentences is None:
        return

    for i in range(len(sentences)):
        if_extra_tool = []
        select_if_else = 0
        check_more_than_one = 0
        tool_used_in_sentence_final_array.append("")
        zone_divide.append("")
        just_test_track_if_none.append("")
        check_if_tool_found = 0
        remember_actNum_for_adding.append("") #260-270번쨰줄 도구 찾기 로직을 위해 공백 처리
        actRecordArray.append("") #위와 같음
        ###만약에 문단에 도구가 새로 등장하면 기본도구를 등장한 도구로 바꾸기###
        for checksubtool in range(len(subtool_k_list)):
            if subtool_k_list[checksubtool] in sentences[i]["sentence"]:
                print("subtool_k_list", str(subtool_k_list[checksubtool]), str(sentences[i]["sentence"]))
                if(isActualTool(str(subtool_k_list[checksubtool]), str(sentences[i]["sentence"]), ingreCollectList) == False):
                    print("\n\n\n")
                    break
                    
               #만약에 도구가 채인 경우에 "얇에 채를 썰다" 또는 "채에 담아주세요", 동작 채 또는 도구 채 2가지 경우가 존재, 이를 위해 판단하기 위한 if문
                if((str(subtool_k_list[checksubtool]) == "채") and ("채 썰다" in sentences[i]["sentence"] or "채썰다" in sentences[i]["sentence"])): #만약에 도구가 채를 감지하고, 동작 부분에 채썰다 동작이 있는 경우
                    continue #조리도구가 아닌것으로 판단하고 무시
                print("act", sentences[i]["sentence"])
                if subtool_k_list[int(checksubtool)] == "냉장": #만약에 조리도구가 냉장이면 냉장고로 변경
                    subtool_k_list[int(checksubtool)]  = "냉장고"
                    
                just_test_track_if_none[i] = str(subtool_k_list[checksubtool])
                current_action_tool[int(subtool_v_list[checksubtool])] = subtool_k_list[int(checksubtool)]
                #print(current_action_tool[int(subtool_v_list[checksubtool])])
                if_extra_tool.append(subtool_k_list[int(checksubtool)])
                save_previous_used_sentence = int(subtool_v_list[checksubtool])
                check_if_used_tool[int(subtool_v_list[checksubtool])] = counttrackoftoolnum.getmostrecenttool
                counttrackoftoolnum.getmostrecenttool += 1
                check_more_than_one += 1
                check_if_tool_found = 1
                #print(check_if_used_tool)
        check_knife = 0
        if(check_more_than_one >= 2):
            print("this is correct", sentences[i]["sentence"], if_extra_tool)  
        ###현재 저장된 도구정보로 행동과 매칭해 도구-행동 각 문단마다 진행###
        for k in valuelist:

            if k in sentences[i]["sentence"] and (isWordPresent(str(sentences[i]["sentence"]), str(k)) == True):

                if("물기를 빼다" in sentences[i]["sentence"] and (check_if_tool_found == 0)):
                    current_action_tool[1] = "싱크대"
                    if current_action_tool[save_previous_used_sentence] != "싱크대":
                        check_if_used_tool[save_previous_used_sentence] = -1
                    check_knife = 1
                    print(sentences)
                elif("자르다" in sentences[i]["sentence"]):
                    current_action_tool[1] = "가위"
                    check_knife = 1
                    #print(sentences)
                if("하다" in sentences[i]["sentence"]):
                    #print("하다 is found")
                    if("밑동" in sentences and "제거" in sentences[i]["sentence"]): #만약에 하다 전에 밑동 제거가 나온다면
                        #print("\n\nhi]n]n\n\n")
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    elif("슬라이스" in sentences[i]["sentence"]): #위 밑동, 제거 예시와 같음. 조금더 코드 간편화를 위해 if-elif을 합쳐도 무관 X
                        #print("\n\nhi]n]n")
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    else: #이외 모든 경우가 아니라면 하다는 판단이 안되는 상태
                        tool_used_in_sentence_final_array[i] += tool_used_in_sentence #저번 문장에서 사용했던 조리도구를 그대로 사용
                        check_knife = 1 #check_knife를 1로 설정, 이는 인덱스 1번 같은 경우 따로 언급 없는 경우 도마,칼로 기본조리도구를 유지하기 위해서 사용
                        break

                ###행동의 번호를 가지고 오는 함수 및 변수###
                numbermatch = checkifexist(k, checkaction)
                #print(checkaction)
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

                    if("밑동" in sentences and "제거" in sentences[i]["sentence"]): #만약에 하다 전에 밑동 제거가 나온다면
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    elif("슬라이스" in sentences[i]["sentence"]):
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    elif("칼집" in sentences and "넣다" in sentences[i]["sentence"]): #넣다 라는 행동은 냄비에 넣다 그릇에 넣다등의 행동으로 이루어지는데 "칼집을 넣다"라는 특정 숙어?가 존재
                        #만약에 칼집을 넣다 인 경우, 조리도구를 도마,칼로 배정 그리고 인덱스 값을 직접 배정이라 증가시키지 않음
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
                        #print(maxvalue)
                        #print(current_action_tool)
        
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
                                print("\nchangedback\n", current_action_tool[1], sentences[i]["sentence"])
                                check_knife = 0
                            if int(saveindex) == 1:
                                check_knife = 1
                                print("\nkk\n")
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
                    counttrackoftoolnum.getmostrecenttool += 1
                ###행동이 하나의 도구에 연결되는 경우###
                else:
                    ###가장 최근에 사용된 도구를 판단하기 위해 도구 번호에 매칭되는 인덱스 값을 올려줌. 가장 큰 숫자가 가장 최근 번호###
                    check_if_used_tool[int(numbermatch)] = counttrackoftoolnum.getmostrecenttool
                    counttrackoftoolnum.getmostrecenttool += 1
                    ###만약에 행동 번호가 하나인 경우는 그냥 인덱스에 도구를 추가함####
                    tool_used_in_sentence = current_action_tool[int(numbermatch)]
                    if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]:
                        keep_action_num.append(numbermatch)
                        tool_used_in_sentence_final_array[i] += tool_used_in_sentence
                        if(int(numbermatch) == 3):
                                zone_divide[i] += "화구"
                        else:
                            zone_divide[i] += "전처리"
                        
                        if int(numbermatch) == 1:
                            check_knife = 1
                            print("\nkk\n")
                        if(check_knife == 1):
                            current_action_tool[1] = "도마, 칼"
                            print("\nchangedback\n", current_action_tool, sentences[i]["sentence"])
                            check_knife = 0
                            break
        
        counttrackoftoolnum.foundtoolsentence = ""
        
        if(check_more_than_one >= 2):
            for kk in range(check_more_than_one):
                if if_extra_tool[kk] not in tool_used_in_sentence_final_array[i]:
                    tool_used_in_sentence_final_array[i] += ", " + if_extra_tool[kk]
                
            if select_if_else == 1:
                current_action_tool[int(saveindex)] = if_extra_tool[0]
                print("test if changed", current_action_tool[int(saveindex)],if_extra_tool[0] )
            else:
                current_action_tool[int(numbermatch)] = if_extra_tool[0]
                ###############################################################

    print("\n", tool_used_in_sentence_final_array, "\n", just_test_track_if_none, "\n")
    track_count = 0
    for i in range(len(tool_used_in_sentence_final_array)): #만약에 문장 내내 해당 조리도구 인덱스의 조리행동/조리도구가 발견디 안된 경우
        if(tool_used_in_sentence_final_array[i] == ""):
            track_count += 1
            #print(track_count)
        elif(tool_used_in_sentence_final_array[i] != "" and (track_count != 0)):
            recorded_tool = tool_used_in_sentence_final_array[i] #이후에 나오는 문장에서 조리도구를 찾기
            #print(track_count+i)
            for j in range((i-track_count), i):
                for checktool in range(len(subtool_v_list)): #도구 숫자만큼 for 룹
                    if recorded_tool in subtool_k_list[checktool]: #만약에 비어있는 도구칸을 채울 도구가 도구딕션너리에서 발견된단다면
                        print(subtool_v_list[checktool], actRecordArray[j], recorded_tool, subtool_k_list[checktool])
                        if(str(subtool_v_list[checktool].split(",")[0]) in str(actRecordArray[j])): #만약에 발견된 도구와 행동 동작이 매칭한다면 채우기
                            tool_used_in_sentence_final_array[j] = recorded_tool #비어있는 문장에 조리도구를 추가
                        else: #만약에 발견된 도구가 행동 동작 인덱스 번호를 충족하지 못한다면 그냥 그 동작이 해당되는 기본 인덱스의 도구로 채우기
                            tool_used_in_sentence_final_array[j] = current_action_tool[int(actRecordArray[j].split(",")[0])]

                #print(tool_used_in_sentence_final_array[j], array[j]["act"])
            track_count = 0
    print(tool_used_in_sentence_final_array)


    return (tool_used_in_sentence_final_array, zone_divide)
    ###############################################################
    #print((checkaction))
    #for i in range(len(sentences)):
        #for j in range(len(checkaction)):
            #print()
###############################################################

############################################################################################################################################

def matchresult(array, ingreCollectList):
    cooking_act_dict, act_score_dict = parse_cooking_act_dict("./hajong/action_number.txt")
    tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("./labeling/tool.txt")

    #print(cooking_act_dict)
    matchtoolwithactionresult = matchtoolwithaction(array, cooking_act_dict, act_score_dict, tool_match_main_dic, tool_match_sub_dic, ingreCollectList)
    return matchtoolwithactionresult


#cooking_act_dict, act_score_dict = parse_cooking_act_dict("./hajong/action_number.txt")
#tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("./hajong/tool_number.txt")

#print(cooking_act_dict)
#array = test.main()
#matchtoolwithactionresult = matchtoolwithaction(array, cooking_act_dict, act_score_dict, tool_match_main_dic, tool_match_sub_dic)


#print(temp_sentence_split.main())

#print(matchtoolwithactionresult)
#print(array)