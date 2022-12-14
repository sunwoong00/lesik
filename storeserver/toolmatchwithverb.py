import urllib3
import json
#from kss import split_sentences
import os.path
import re

# matchresult -> matchtoolwithaction -> 여러 확인 함수 -> matchtoolwithaction -> matchresult
#순서로 function들이 작동



#global getmostrecenttool
#가장 최근에 이루어진 조리도구, 행동 번호를 계속해서 트레킹 하기 위해서 사용
class counttrackoftoolnum:
    getmostrecenttool = 1
    foundtoolsentence = ""
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
        if("[" in line): #sub부분과 기본 부분 조리도구를 나누기 위해서 [] 부분을 파일 안에서 찾는 함수
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

#행동 관련된 내용을 딕셔너리로 가져오는 부분, action_number.txt
def parse_cooking_act_dict(file_path):
    file_exists = os.path.exists(file_path) #파일이 존재하는지 확인
    if not file_exists:
        return None
    f = open(file_path, 'r', encoding='utf-8') #존재한다면
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

###행동 단어의 번호를 알아내서 돌려주는 함수###
def checkifexist(word, dict):
    if word in dict.keys(): #조리 행동
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
    s = sentence.split(" ") #문장을 단어별로 나눈다
    #s = str(sentence[0])
    #print("isWordPresent", sentence, word)
    for i in s:
 
        # Comparing the current word
        # with the word to be searched
        if (word in i): #문장의 나눠진 단어와 우리가 찾는 단어가 실제로 존재하는 확인
            return True
    return False
###############################################################

###단어의 일부만 아니라 전체가 존재하는지 확인하고 일치 한다면 도구로 판단 예: 통깨->통 X
def isActualTool(word, sentence, ingreCollectList, listofingre):
    detection = sentence.split(" ") #문장을 " "으로 나눠서 단어 단위로 쪼갠다
    #print("detection", detection)
    for checkdetect in range(len(detection)):
        if word in detection[checkdetect]: #만약에 조리도구로 탐지된 단어가 나눠진 단어에 존재한다면 예: word:통, dectionp[checkdetect] = "통깨에"
            if (word == "타월" or word == "타올") and ("종이" in detection[checkdetect] or "키친" in detection[checkdetect]): #종이타월/종이타올, 키친타월/키친타올은 2번씩 감지되서 조리도구 칸에 키친타월, 타월 이런식으로 2번 들어가 방지하기 위한 코드
                return False #존재하지 않는다로 판단
            elif len(word) == 1 or len(word) == 2 or len(word) == 3:
                print(word, counttrackoftoolnum.foundtoolsentence)
                if word in counttrackoftoolnum.foundtoolsentence:
                    print("found repeat")
                    return False
            #print("hi", checkdetect, ingreCollectList, detection[checkdetect])
            for ingredetect in range(len(ingreCollectList)): #koElectra를 사용해서 ingredient 정보를 받아온 배열을 확인해서 일치하는 단어가 있는지 확인
                #print(ingreCollectList[ingredetect], "|", detection[checkdetect], "|", word)
                if str(ingreCollectList[ingredetect]) in detection[checkdetect]: #만약에 ingredient 정보가 나눠진 문장에 존재한다면 ingre:통깨 detection[checkdetect]: 통깨에
                    #print("found error", detection[checkdetect])
                    return False #조리도구가 아닌것으로 판단하고 거짓으로 리턴
                elif word in str(ingreCollectList[ingredetect]):
                    #print("found error", detection[checkdetect])
                    return False
            for ingredetect in range(len(listofingre)): #위와 같은 로직을 ingredient 대신에 첨가물을 사용하여 확인
                #print(listofingre[ingredetect])
                if str(listofingre[ingredetect]) in detection[checkdetect]:
                    #print("found error", detection[checkdetect])
                    return False
    counttrackoftoolnum.foundtoolsentence += word + " " #만약에 아무런 케이스를 발견하지 못했다면 발견된 조리도구를 저장
    return True
###############################################################

###조리도구/위치 매칭을 위한 메인 함수###
def matchtoolwithaction(array, cooking_act_dict, checkaction, checktoolmain, checktoolsub, listofingre):
    keylist = [] #cookingact.txt 추출 이후 행동 원 형태 저장을 위한 배열 "썰, 갈"
    valuelist = [] #cookingact.txt 이후 행동 다듬은 형태 저장을 위한 배열 "썰다, 갈다"
    current_action_tool = [] #현재 사용 도구를 저장하기 위한 배열, 총 5가지 번호:0,1,2,3,4가 존재, 그리고 그 번호에 해당하는 사용된 도구를 넣음 ("","","오븐","","")
    check_if_used_tool = [] #번호 0,1,2,3,4를 0으로 세팅해두고 가장 최근에 사용된 번호에 해당하는 도구의 배열 숫자를 증가시킴 (0,0,1,0,0)
    tool_used_in_sentence = "" #문장에서 사용된 도구를 저장
    tool_used_in_sentence_final_array = [] #문장에서 사용된 도구를 string -> array 로 변환
    just_test_track_if_none = [] 
    zone_divide = [] #존 나누기 함수, 하지만 더 이상 사용 X
    keep_action_num = []
    save_previous_used_sentence = 0
    
    ###각 행동액션 번호와 매칭되는 도구를 기본설정 도구로 세팅해둔다###
    k_list = list(checktoolmain.keys()) #tool_number.txt의 기본 조리도구의 이름을 뽑아낸다 싱크대, 도마 칼, 믹서기, 팬, 그릇
    v_list = list(checktoolmain.values()) #tool_number.txt의 기본 조리도구의 번호를 뽑아낸다 0,1,2,3,4
    subtool_k_list = list(checktoolsub.keys()) #tool_number.txt의 sub 조리도구의 이름을 뽑아낸다
    subtool_v_list = list(checktoolsub.values()) #tool_number.txt의 sub 조리도구의 번호를 뽑아낸다
    for current in range(5): #총 5개의 번호가 존재하기 때문에 loop을 5번 돌린다
        current_action_tool.append("") #현재 조리도구가 존재하지 않기 때문에 우선 공백처리
        check_if_used_tool.append(0) #현재 조리도구가 존재하지 않아서 트래킹 숫자가 없어서 각 번호마다 0처리
    for current in range(len(v_list)):
        current_action_tool[int(v_list[current])] = k_list[int(current)] #각 조기도구 번호 배열에 k_list(기본 조리도구 이름)을 저장해둔다
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

    for i in range(len(array)): #array의 길이 (전달 받은 문장들의 길이)만큼 loop 실행
        sentences = array[i]["sentence"] #배열속 문장을 sentences라는 변수에 저장
        ingreCollectList = array[i]["ingre"] #문장 순서에 일치하는 재료
        seasoningCollect = array[i]["seasoning"] #문장 순서에 일치하는 시즈닝
        checkzone = array[i]["zone"] #문장 순서에 일치하는 존구역
        act = array[i]["act"] #문장 순서에 일치하는 행동
        if_extra_tool = [] #만약에 하나 이상의 도구가 사용된다면 저장하는 배열
        select_if_else = 0 
        check_more_than_one = 0 #도구가 하나 이상인지 확인하는 변수, 만약에 1이라면 하나 이상인걸로 판단
        check_if_tool_found = 0 #문장속에서 도구가 발견되었는지 확인하는 변수, 1이면 발견
        tool_used_in_sentence_final_array.append("") #129~번째줄 변수 선언 부분 확인
        zone_divide.append("")  #129~번째줄 변수 선언 부분 확인
        just_test_track_if_none.append("")  #129~번째줄 변수 선언 부분 확인
        ###만약에 문단에 도구가 새로 등장하면 기본도구를 등장한 도구로 바꾸기###
        for checksubtool in range(len(subtool_k_list)): #tool_number에 존재하는 subtool 숫자만큼 돌리기
            if subtool_k_list[checksubtool] in sentences.replace(",", " "): #만약에 조리도구가 문장에서 발견된다면
                #print(str(subtool_k_list[checksubtool]), str(sentences), check_if_tool_found)
                if(isActualTool(str(subtool_k_list[checksubtool]), str(sentences), ingreCollectList, seasoningCollect) == False): #실제로 조리도구인지 판단하는 함수
                    #print("\n\n\n")
                    continue #만약에 조리도구가 아니라면 무시
                #print("checktool", str(subtool_k_list[checksubtool]), str(sentences).replace(",", " "), check_if_tool_found)
                if subtool_k_list[int(checksubtool)] == "냉장": #만약에 조리도구가 냉장이면 냉장고로 변경
                    subtool_k_list[int(checksubtool)]  = "냉장고"
                    
                just_test_track_if_none[i] = str(subtool_k_list[checksubtool])
                current_action_tool[int(subtool_v_list[checksubtool])] = subtool_k_list[int(checksubtool)] #발견된 조리도구의 번호를 찾고 그 번호에 일치하는 위치에 current_action_tool 저장
                #print(current_action_tool[int(subtool_v_list[checksubtool])])
                if_extra_tool.append(subtool_k_list[int(checksubtool)]) #만약에 하나 이상의 조리도구가 존재한다면 그 조리도구를 if_extra_tool에 보관
                check_if_used_tool[int(subtool_v_list[checksubtool])] = counttrackoftoolnum.getmostrecenttool #가장 최근에 사용된 조리도구를 트래킹에 해당 인덱스의 숫자를 증가
                save_previous_used_sentence = int(subtool_v_list[checksubtool]) #현재 문장을 다음에 사용 가능하게 저장
                counttrackoftoolnum.getmostrecenttool += 1 #저장 이후 트래킹 숫자를 증가
                check_more_than_one += 1 #하나 이상의 조리도구임으로 숫자를 증가
                check_if_tool_found = 1 #조리도구가 발견된것이 맞음으로 1로 설정
                #print(check_if_used_tool)
        check_knife = 0
        if(check_more_than_one >= 2): #점검용 출력문, 실제 코드에는 영향 X
            print("this is correct", sentences, if_extra_tool)  
        ###현재 저장된 도구정보로 행동과 매칭해 도구-행동 각 문단마다 진행###
        
        for k in valuelist: #129~번째열 함수 선언 부분 확인, 행동 길이만큼 loop
            if k in act and (isWordPresent(str(act), str(k)) == True): #만약에 행동 딕션너리에 해당하는 동사, 그리고 전달 받은 array에서 동사가 서로 일치한다면
                #print("whynotwor", k, act)
                if((act == "물기를 빼다" or "헹구다") and (check_if_tool_found == 0)): #만약에 물기를 빼다, 헹구다 같은 특별한 동작인 경우
                    current_action_tool[0] = "싱크대" #싱크대가 해당하는 0번째 인덱스에 직접 배정
                    if current_action_tool[save_previous_used_sentence] != "싱크대":
                        check_if_used_tool[save_previous_used_sentence] -= 1 #인덱스를 일부로 증가 X, 직접 배정 같은 경우 트레킹 숫자가 꼬이지 않게 증가 없이 진행
                    check_knife = 1 #check_knife를 1로 설정, 이는 인덱스 1번 같은 경우 따로 언급 없는 경우 도마,칼로 기본조리도구를 유지하기 위해서 사용
                    print(sentences)
                elif("자르다" in act): #만약에 자르다가 행동인 경우
                    if check_if_tool_found == 1: #자르다 사용할때 특정 조리도구가 언급되었는지 확인, 만약에 언급되었다면 직접 배정을 하지 않음
                        pass
                    else: #만약에 자르다가 존재하고 조리도구가 발견되지 않았더라면 
                        current_action_tool[1] = "가위" #가위로 해당하는 인덱스에 조리도구를 직접 배정 
                        check_knife = 1 #check_knife를 1로 설정, 이는 인덱스 1번 같은 경우 따로 언급 없는 경우 도마,칼로 기본조리도구를 유지하기 위해서 사용
                        #print("자르다", sentences, check_if_tool_found)
                #만약에 동사가 하다이면 정확히 어떤건지 잘 모름 (하다 특성상 아예 어디로 가야될지 모르기에 가장 최선은 전 문장을 따라 수정)
                if("하다" in act):
                    print("하다 is found")
                    if("밑동" in sentences and "제거" in act): #만약에 하다 전에 밑동 제거가 나온다면
                        #print("\n\nhi]n]n\n\n")
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    elif("슬라이스" in act): #위 밑동, 제거 예시와 같음. 조금더 코드 간편화를 위해 if-elif을 합쳐도 무관 X
                        #print("\n\nhi]n]n")
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    else: #이외 모든 경우가 아니라면 하다는 판단이 안되는 상태
                        tool_used_in_sentence_final_array[i] += tool_used_in_sentence #저번 문장에서 사용했던 조리도구를 그대로 사용
                        check_knife = 1 #check_knife를 1로 설정, 이는 인덱스 1번 같은 경우 따로 언급 없는 경우 도마,칼로 기본조리도구를 유지하기 위해서 사용
                        break
                    #print(sentences)
                #print("whynotwor", k, act, check_if_used_tool, current_action_tool)
                ###행동의 번호를 가지고 오는 함수 및 변수###
                numbermatch = checkifexist(k, checkaction)
                #print(k)
                ###만약에 행동이 두가지의 도구가 가능한 경우 예:섞다###
                if("," in numbermatch): #만약에 조리행동이 한가지 이상의 조리도구와 매칭이 가능한 경우
                    select_if_else = 1 
                    #print(check_if_used_tool)
                    #print(k)
                    ###선택중에 가장 최근에 나온 숫자를 기준으로함, 예: 섞다에서 "팬"이 먼자 나오면 check_if_used_tool 숫자가 더큼###
                    two_option = str(numbermatch).split(",") #옵션들을 분리
                    maxvalue = 0 #값을 우선 0으로 설정
                    saveindex = 0 
                    for findmax in two_option: #옵션중에서 가장 최근 사용된 조리도구 인덱스를 찾기 위한 for
                        #print("checklist", check_if_used_tool[int(findmax)])
                        #print("currentmax", maxvalue)
                        #print("findmax", findmax)
                        if int(check_if_used_tool[int(findmax)]) > int(maxvalue): #check_if_used_tool에 저장된 트레킹 값을 비교 만약에 해당 인덱스의 트래킹 값이 maxvalue보다 크다면
                            maxvalue = int(check_if_used_tool[int(findmax)]) #멕스 벨류를 현재 check_if_used_tool의 트레킹 값으로 저장
                            saveindex = int(findmax) #saveindex를 현재 check_if_used_tool의 인덱스로 저장
                    #이는 화구존에 3번 인덱스 조리도구(팬, 냄비)등이 아닌 4번류(그릇) 또는 다른 조리도구가 나오는것을 방지 하기 위한 if문
                    #만약에 조리도구가 따로 언급이 없는 경우 그전 문장을 따라가는게 기본 설정이라(다른 설정으론느 추후 문장 따라가기) 전처리->화구로 변경한 경우 화구류 조리도구가 아닌 경우 바꾸기 위해서 설정
                    if(checkzone == "화구존" and (saveindex != 3) and check_if_tool_found == 0): #만약에 해당 문장의 존이 화구존이고 saveindex가 3이 아니고 문장속에서 도구가 발견이 되지 않은 경우
                        tool_used_in_sentence_final_array[i] = "" #현재 조리도구 저장해둔것을 초기화
                        continue
                    if("밑동" in sentences and "제거" in act): #만약에 하다 전에 밑동 제거가 나온다면
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    elif("슬라이스" in act):
                        saveindex = 1 #이와 관련된 조리행동은 인덱스1에 해당하기 때문에 추후 사용을 위해서 인덱스 접근을 위해 1로 설정
                        maxvalue = 1 #위와 같음
                        check_if_used_tool[1] -= 1 #직접배정이라 따로 트래킹 숫자를 증가 X
                    elif("칼집" in sentences and "넣다" in act): #넣다 라는 행동은 냄비에 넣다 그릇에 넣다등의 행동으로 이루어지는데 "칼집을 넣다"라는 특정 숙어?가 존재
                        #만약에 칼집을 넣다 인 경우, 조리도구를 도마,칼로 배정 그리고 인덱스 값을 직접 배정이라 증가시키지 않음
                        #print("\n\nhi]n]n")
                        saveindex = 1
                        maxvalue = 1
                        check_if_used_tool[1] -= 1
                    #print(current_action_tool[int(two_option[0])])
                    #print(maxvalue)
                    
                    if(maxvalue == 0): #만약에 맥스 밸류가 0이라면 첫문장이라 트래킹값이 다 똑같은 경우, for current in range(5): 140번대 코드 확인
                        print("maxiszero")
                        saveindex = two_option[0]
                        tool_used_in_sentence = current_action_tool[int(saveindex)] #해당 조리행동의 첫번째 조리 인덱르로 배정 예:4,3,2->4 | 3,2,1 -> 3
                        if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]: #만약에 발견된 조리도구가 현재조리도구 저장 array에 저장되어 있지 않다면 (중복 방지)
                            keep_action_num.append(numbermatch) #조리행동 인덱스를 저장
                            tool_used_in_sentence_final_array[i] += tool_used_in_sentence #결과값 리턴을 위한 어레이에 조리도구를 추가
                            if(int(saveindex) == 3): #아래 존 코드는 더이상 사용 하는것이 아니라 오류를 제거하고 지워도 됌
                                zone_divide[i] += "화구"
                            else:
                                zone_divide[i] += "전처리"
                            check_knife = 1
                    else: #만약에 트래킹 값이 다른 경우
                        print("test", saveindex, act)
                        print(current_action_tool, check_if_used_tool)
        
                        tool_used_in_sentence = current_action_tool[int(saveindex)] #tool_used 문장에 현재 사용되고 있는 조리도구를 저장
                        if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]: #만약에 발견된 조리도구가 현재조리도구 저장 array에 저장되어 있지 않다면 (중복 방지)
                            keep_action_num.append(numbermatch) #조리행동 인덱스를 저장 
                            tool_used_in_sentence_final_array[i] += tool_used_in_sentence #결과값 리턴을 위한 어레이에 조리도구를 추가
                            if(int(saveindex) == 3): #아래 존 찾는 코드는 무시
                                zone_divide[i] += "화구"
                            else:
                                zone_divide[i] += "전처리"
                            if(check_knife == 1): #만약에 check_knife이 1이라면 1번 인덱스 조리도구가 다른 조리도구로 변경되어서 사용됐다는것으로 판단
                                current_action_tool[1] = "도마, 칼" #다시 도마,칼로 배정
                                #print("\nchangedback\n", current_action_tool[1], sentences[i]["sentence"])
                                check_knife = 0 #값을 0으로 리셋
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
                    check_if_used_tool[int(saveindex)] = counttrackoftoolnum.getmostrecenttool #가장 최근에 사용된 조리도구 인덱스에 현재 트래킹값을 저장
                    save_previous_used_sentence = int(saveindex) #현재 문장의 조리도구 인덱스를 저장
                    counttrackoftoolnum.getmostrecenttool += 1 #다음 문장을 위해 트래킹값을 증가
                ###행동이 하나의 도구에 연결되는 경우###
                else: #만약에 행동이 여러 조리도구가 아닌 하나의 인덱스를 가지고 있는 경우 예:볶>볶다>3
                    ###가장 최근에 사용된 도구를 판단하기 위해 도구 번호에 매칭되는 인덱스 값을 올려줌. 가장 큰 숫자가 가장 최근 번호###
                    check_if_used_tool[int(numbermatch)] = counttrackoftoolnum.getmostrecenttool #가장 최근에 사용된 조리도구 인덱스에 현재 트래킹값을 저장
                    save_previous_used_sentence = int(numbermatch) #현재 문장의 조리도구 인덱스를 저장
                    counttrackoftoolnum.getmostrecenttool += 1 #다음 문장을 위해 트래킹값을 증가
                    ###만약에 행동 번호가 하나인 경우는 그냥 인덱스에 도구를 추가함####
                    tool_used_in_sentence = current_action_tool[int(numbermatch)] #tool_used 문장에 현재 사용되고 있는 조리도구를 저장
                    #print("check one", tool_used_in_sentence)
                    if tool_used_in_sentence not in tool_used_in_sentence_final_array[i]: #만약에 발견된 조리도구가 현재조리도구 저장 array에 저장되어 있지 않다면 (중복 방지)
                        keep_action_num.append(numbermatch) #조리행동 인덱스를 저장 
                        tool_used_in_sentence_final_array[i] += tool_used_in_sentence #결과값 리턴을 위한 어레이에 조리도구를 추가
                        if(int(numbermatch) == 3): #아래 존 코드 if else는 무시
                                zone_divide[i] += "화구"
                        else:
                            zone_divide[i] += "전처리"
                        
                        if int(numbermatch) == 1:
                            check_knife = 1
                            #print("\nkk\n")
                        if(check_knife == 1): #만약에 check_knife이 1이라면 1번 인덱스 조리도구가 다른 조리도구로 변경되어서 사용됐다는것으로 판단
                            current_action_tool[1] = "도마, 칼" #다시 도마,칼로 배정
                            #print("\nchangedback\n", current_action_tool, sentences)
                            check_knife = 0 #값을 0으로 리셋
                            break
        
        counttrackoftoolnum.foundtoolsentence = ""

        if(check_more_than_one >= 2): #만약에 조리도구가 1개 이상이라면
            for kk in range(check_more_than_one):
                if if_extra_tool[kk] not in tool_used_in_sentence_final_array[i]: #조리도구가 중복으로 들어가는 확인
                    tool_used_in_sentence_final_array[i] += ", " + if_extra_tool[kk] #아닌 경우 하나 이상의 조리도구에서 새로 발견된 조리도구를 저장 배열에 추가
                
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
    for i in range(len(tool_used_in_sentence_final_array)): #만약에 문장 내내 해당 조리도구 인덱스의 조리행동/조리도구가 발견디 안된 경우
        if(tool_used_in_sentence_final_array[i] == ""):
            track_count += 1
            #print(track_count)
        elif(tool_used_in_sentence_final_array[i] != "" and (track_count != 0)):
            recorded_tool = tool_used_in_sentence_final_array[i] #이후에 나오는 문장에서 조리도구를 찾기
            #print(track_count+i)
            for j in range((i-track_count), i):
                #print(tool_used_in_sentence_final_array[j])
                tool_used_in_sentence_final_array[j] = recorded_tool #비어있는 문장에 조리도구를 추가
            track_count = 0

    for i in range(len(tool_used_in_sentence_final_array)):
        tool_used_in_sentence_final_array[i] = list(tool_used_in_sentence_final_array[i].split("\n"))        
    #print(tool_used_in_sentence_final_array)


    return (tool_used_in_sentence_final_array, zone_divide) #결과값을 리셋
    ###############################################################
    #print((checkaction))
    #for i in range(len(sentences)):
        #for j in range(len(checkaction)):
            #print()
###############################################################

############################################################################################################################################

def matchresult(array, listofingre): #lesik.py에서 호출하는 함수
    #print(array["sentence"])
    cooking_act_dict, act_score_dict = parse_cooking_act_dict("./hajong/action_number.txt") #딕션너리 위치 불러오기
    tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("./hajong/tool_number.txt") #딕션너리 위치 불러오기

    #print(listofingre)
    listofingre = list(listofingre) #lesik.py에서 koElectra를 활용하여 저장한 ingredient, seasoning 값
    matchtoolwithactionresult = matchtoolwithaction(array, cooking_act_dict, act_score_dict, tool_match_main_dic, tool_match_sub_dic, listofingre)
    #print(matchtoolwithactionresult)
    return matchtoolwithactionresult #발견된 조리도구를 리턴


#cooking_act_dict, act_score_dict = parse_cooking_act_dict("./hajong/action_number.txt")
#tool_match_main_dic, tool_match_sub_dic = divide_tool_num_text("./hajong/tool_number.txt")

#print(cooking_act_dict)
#array = test.main()
#matchtoolwithactionresult = matchtoolwithaction(array, cooking_act_dict, act_score_dict, tool_match_main_dic, tool_match_sub_dic)


#print(temp_sentence_split.main())

#print(matchtoolwithactionresult)
#print(array)