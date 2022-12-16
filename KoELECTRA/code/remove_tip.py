'''
레시피에 쓰여진 tip을 제거한다.
'''

f = open('finish_seungilseunghun.txt', 'r') # tip이 포함된 레시피
f1 = open('ss_notip.txt', 'w') # tip이 제거된 레시피
recipe = f.readlines()

for i in recipe:
    if 'tip' not in i and 'Tip' not in i and 'TIP' not in i:
        f1.write(i)