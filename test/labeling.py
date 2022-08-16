import urllib3
import json
import os.path
import sys

openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"

accessKey = "0714b8fe-21f0-44f9-b6f9-574bf3f4524a"
analysisCode = "ner"
fileName = input("레시피 파일명을 입력하세요")
if not os.path.isfile(fileName):
    print("%s에 해당하는 파일이 존재하지 않습니다" % fileName)
    sys.exit(0)
recipeFile = open(fileName, 'r')
originalRecipe = recipeFile.read()

requestJson = {
    "access_key": accessKey,
    "argument": {
        "text": originalRecipe,
        "analysis_code": analysisCode
    }
}

http = urllib3.PoolManager()
response = http.request(
    "POST",
    openApiURL,
    headers={"Content-Type": "application/json; charset=UTF-8"},
    body=json.dumps(requestJson)
)

type_chk_list = ['QT_SIZE', 'QT_COUNT', 'QT_OTHERS', 'QT_WEIGHT', 'QT_TEMPERATURE',
                 'QT_VOLUME', 'QT_ORDER', 'QT_MAN_COUNT', 'QT_PERCENTAGE',
                 'CV_FOOD', 'CV_DRINK',
                 'PT_GRASS', 'PT_FRUIT', 'PT_OTHERS',
                 'TI_DURATION', 'AM_FISH']

if response.status == -1:
    print("ETRI API 서버 통신 중 에러가 발생했습니다.")

json_object = json.loads(str(response.data, "utf-8"))
sentence_list = []
for sentence in json_object['return_object']['sentence']:
    word_list = []
    label_dict = {}
    for token in sentence['NE']:
        if token['type'] in type_chk_list:
            label_dict[int(token['begin'])] = token
    for word in sentence['word']:
        begin_lemma = int(word['begin'])
        end_lemma = int(word['end'])
        text = str(word['text'])
        for i in range(begin_lemma, end_lemma + 1):
            if i in label_dict:
                label = label_dict[i]
                if label['end'] <= end_lemma:
                    text = text.replace(label['text'], label['text'] + "(" + label['type'] + ")")
        word_list.append(text)
    sentence_list.append(" ".join(word_list))
print("\n".join(sentence_list))
