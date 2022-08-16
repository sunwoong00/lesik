import py_compile
import torch
from torch import nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import gluonnlp as nlp
import numpy as np
from tqdm import tqdm, tqdm_notebook
import pandas as pd
from kobert import get_tokenizer
from kobert import get_pytorch_kobert_model
from transformers import AutoTokenizer, AutoModel
from transformers.optimization import get_cosine_schedule_with_warmup
from flask import Flask, render_template, request, make_response
import warnings
import datetime
import time



warnings.simplefilter("ignore")
import konlpy
from konlpy.tag import Okt

okt = Okt()

# Setting parameters
max_len = 64
batch_size = 64
warmup_ratio = 0.1
num_epochs = 5
max_grad_norm = 1
log_interval = 200
learning_rate = 5e-5

app = Flask(__name__)


@app.route('/', methods=['POST'])
def run():
    def predict(model, device, tok, predict_sentence):

        start2 = time.time()
        data = [predict_sentence, '0']
        dataset_another = [data]

        another_test = BERTDataset(dataset_another, 0, 1, tok, max_len, True, False)
        test_dataloader = torch.utils.data.DataLoader(another_test, batch_size=batch_size, num_workers=5)

        model.eval()
        end2 = time.time()
        print("Logit 측정", format(end2 - start2))
        for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(test_dataloader):
            token_ids = token_ids.long().to(device)
            segment_ids = segment_ids.long().to(device)

            valid_length = valid_length
            label = label.long().to(device)

            start = time.time()
            out = model(token_ids, valid_length, segment_ids)
            end = time.time()

            print("모델 측정", format(end-start))


            for i in out:
                logits = i.detach().cpu().numpy()
                # print(logits, predict_sentence)
                if np.argmax(logits) == 0:
                    return "[첨가물]"
                elif np.argmax(logits) == 1:
                    return "[식자재]"
                elif np.argmax(logits) == 2:
                    return "[시간]"
                elif np.argmax(logits) == 3:
                    return "[용량]"
                elif np.argmax(logits) == 4:
                    return "[온도]"
                elif np.argmax(logits) == 5:
                    return "[순서]"
                elif np.argmax(logits) == 6:
                    return "[DEFAULT]"


    # 개체명 추출
    def recipe(model, device, tok, recipe_input):

        start2 = time.time()

        pre_ingre_dict = {
            "seasoning": [],
            "ingredient": [],
        }

        aa = recipe_input.index("1.")

        # 재료 정보 추출
        food_info = recipe_input[:aa - 1]
        food_info = food_info[food_info.find("["):]
        sliced_food_info = food_info.split("\n")

        start3 = time.time()
        # 재료만 남기기 (불필요한 정보 제거)
        for i in sliced_food_info:
            if "[" in i:
                sliced_food_info.remove(i)

        for i in sliced_food_info:
            food_ele = i.split()
            volume = food_ele[-1]
            food = i[:i.find(volume) - 1]

            result = predict(model, device, tok, food)
            if result == "[첨가물]":
                pre_ingre_dict["seasoning"].append(food + "(" + volume + ")")
            elif result == "[식자재]":
                pre_ingre_dict["ingredient"].append(food + "(" + volume + ")")
        end3 = time.time()
        print("재료만 남기기")
        print(format(end3 - start3))

        start4 = time.time()
        # 조리 방법
        recipe = recipe_input[aa:].split('\n')
        line_cnt = len(recipe)
        for i in recipe:
            if i == "":
                recipe.remove(i)
            line_cnt = len(recipe)

        ner_dict = []

        id = 0

        divide_recipe = okt.pos(recipe_input[aa:])
        len_divide_recipe = len(divide_recipe)

        for i in range(line_cnt):
            ner_dict_part = {
                "id": -1,
                "seasoning": [],
                "ingredient": [],
                "time": [],
                "volume": [],
                "temperature": []
            }

            ner_dict_part["id"] = id

            # 공백 기준 분리
            slice_cookingMethod = recipe[i].split()
            len_sliced_recipe = len(slice_cookingMethod)

            start5 = time.time()
            for j in range(len_sliced_recipe):

                start6 = time.time()
                # 토큰화
                token = okt.pos(slice_cookingMethod[j])
                end6 = time.time()
                print("#토큰화")
                print(format(end6 - start6))

                # print(token)
                len_token = len(token)

                # 튜플 리스트화
                for r in range(len_token):
                    token[r] = list(token[r])

                # 조사 앞에꺼 병합 / 조사 없으면 무시
                if token[len_token - 1][1] == "Josa" or token[len_token - 1][1] == "Punctuation":
                    for k in range(1, len_token - 1):
                        temp = token[k - 1][0] + token[k][0]
                        token.remove(token[k - 1])
                        token.remove(token[k - 1])
                        token.insert(k - 1, [0, 0])
                        token.insert(k, [temp, "Noun"])

                start7 = time.time()
                #predict
                for idx in range(len_token):
                    if token[idx][1] == 'Noun' or token[idx][1] == 'Number':
                        result = predict(model, device, tok, token[idx][0])
                        if result == "[첨가물]":
                            ner_dict_part["seasoning"].append(token[idx][0])
                        elif result == "[식자재]":
                            ner_dict_part["ingredient"].append(token[idx][0])
                        elif result == "[시간]":
                            ner_dict_part["time"].append(token[idx][0])
                        elif result == "[용량]":
                            ner_dict_part["volume"].append(token[idx][0])
                        elif result == "[온도]":
                            ner_dict_part["temperature"].append(token[idx][0])

                end7 = time.time()
                print("#predict")
                print(format(end7 - start7))

            ner_dict.append(ner_dict_part)
            id += 1
            end5 = time.time()
            print("토큰화 only")
            print(format(end5 - start5))

        end4 = time.time()
        print("#조리방법 (+토큰화)")
        print(format(end4 - start4))

        final_result = {
            "pre_ingre_dict": pre_ingre_dict,
            "ner_dict": ner_dict
        }

        end2 = time.time()
        print("func recipe time")
        print(format(end2 - start2))
        return final_result

    class BERTDataset(Dataset):
        def __init__(self, dataset, sent_idx, label_idx, bert_tokenizer, max_len,
                     pad, pair):
            transform = nlp.data.BERTSentenceTransform(
                bert_tokenizer, max_seq_length=max_len, pad=pad, pair=pair)

            self.sentences = [transform([i[sent_idx]]) for i in dataset]
            self.labels = [np.int32(i[label_idx]) for i in dataset]

        def __getitem__(self, i):
            return (self.sentences[i] + (self.labels[i],))

        def __len__(self):
            return (len(self.labels))

    class BERTClassifier(nn.Module):
        def __init__(self,
                     bert,
                     hidden_size=768,
                     num_classes=7,  ##클래스 수 조정##
                     dr_rate=None,
                     params=None):
            super(BERTClassifier, self).__init__()
            self.bert = bert
            self.dr_rate = dr_rate

            self.classifier = nn.Linear(hidden_size, num_classes)
            if dr_rate:
                self.dropout = nn.Dropout(p=dr_rate)


        def gen_attention_mask(self, token_ids, valid_length):
            attention_mask = torch.zeros_like(token_ids)
            for i, v in enumerate(valid_length):
                attention_mask[i][:v] = 1
            return attention_mask.float()

        def forward(self, token_ids, valid_length, segment_ids):
            attention_mask = self.gen_attention_mask(token_ids, valid_length)

            _, pooler = self.bert(input_ids=token_ids, token_type_ids=segment_ids.long(),
                                  attention_mask=attention_mask.float().to(token_ids.device))
            if self.dr_rate:
                out = self.dropout(pooler)
            return self.classifier(out)

    # 기본 코드
    device = torch.device("cpu")
    bertmodel, vocab = get_pytorch_kobert_model(cachedir='.cache')

    # 토큰화
    tokenizer = get_tokenizer()
    tok = nlp.data.BERTSPTokenizer(tokenizer, vocab, lower=False)

    start1 = time.time()
    # 모델 불러오기
    path = "/home/ubuntu/model/model.pt"
    model = BERTClassifier(bertmodel, dr_rate=0.5).to(device)
    model.load_state_dict(torch.load(path, map_location=device))
    model.eval()

    end1 = time.time()
    print('model time')
    print(format(end1 - start1))

    original_recipe = None
    if request.method == 'POST':
        original_recipe = request.data.decode('utf-8')

    if original_recipe is None:
        return make_response("Recipe is Blank", 406)


    return make_response(recipe(model, device, tok, original_recipe))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)