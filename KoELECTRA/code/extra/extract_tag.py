'''
태그별로 레이블링이 잘 됐는지 확인하기 위해 인덱스와 개체명과 태그를 추출한다.
써진 파일을 바탕으로 개체명을 확인하고, 잘못 레이블링된 것을 수정하려면 읽은 파일의 인덱스를 따라가면 된다.
'''

f = open('wtable_test.txt', 'r') # 읽을 레이블링된 파일
f1 = open('state.txt', 'w') # 쓸 파일
sliced_recipe = f.readlines()

index = 1
for step in sliced_recipe:
    step_copy = step

    while(True):
        tag_start = step.find("<")
        if tag_start == -1:
            break
        tag_end = step.find(">")
        tag_content = step[tag_start+1:tag_end].split(":") # 재료, 태그 구분

        print(index)
        if tag_content[1] == 'CV_STATE':
            f1.write(str(index) + ' ' + step[tag_start+1:tag_end] + '\n')

        step = step[:tag_start] + tag_content[0] + step[tag_end+1:] # 태그 제거한 문장 제작
    #f2.write(step_copy)
    index += 1

f.close()
f1.close()