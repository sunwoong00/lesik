'''
성능이 안 좋은 데이터셋 증진을 위해 특정 태그가 포함된 문장을 추출한다.
'''

f = open("wtable_test.txt", 'r')
f2 = open("state2.txt", 'w')


content = f.readlines()
for part in content:
    if "CV_STATE" in part:
        part = part[:part.find("\t")] + "\n"
        f2.write(part)


f.close()
f2.close()