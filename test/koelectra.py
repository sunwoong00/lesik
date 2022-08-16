import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import ElectraTokenizerFast, ElectraConfig, ElectraForTokenClassification
from flask import Flask, request, make_response


def load():
    model_directory = '/home/ubuntu/model'
    pre_trained_model = ElectraForTokenClassification.from_pretrained(model_directory, num_labels=len(labels_to_ids), local_files_only=True)
    pre_trained_model.to(device)

    tokenizer_directory = '/home/ubuntu/tokenizer'
    pre_trained_tokenizer = ElectraTokenizerFast.from_pretrained(tokenizer_directory, local_files_only=True)
    return pre_trained_model, pre_trained_tokenizer


def predict(sentence):
    inputs = tokenizer(sentence,
                       return_offsets_mapping=True,
                       padding='max_length',
                       truncation=True,
                       max_length=MAX_LEN,
                       return_tensors="pt")

    # move to gpu
    ids = inputs["input_ids"].to(device)
    mask = inputs["attention_mask"].to(device)
    mapping = inputs['offset_mapping'].to(device)
    # forward pass
    outputs = model(ids, attention_mask=mask)
    logits = outputs[0]

    active_logits = logits.view(-1, model.config.num_labels)  # shape (batch_size * seq_len, num_labels)
    flattened_predictions = torch.argmax(active_logits,
                                         axis=1)  # shape (batch_size*seq_len,) - predictions at the token level

    tokens = tokenizer.convert_ids_to_tokens(ids.squeeze().tolist())
    token_predictions = [ids_to_labels[i] for i in flattened_predictions.cpu().numpy()]

    #word_prediction = []
    token_prediction = []
    # prev_word_ids = None
    # prev_token_pred = None
    # for token_pred, word_idx in zip(wp_preds, inputs.word_ids()):
    #     if prev_word_ids is not None and prev_word_ids == word_idx and token_pred[1] == 'O' and prev_token_pred is not None:
    #         word_prediction.append({token_pred[0]: prev_token_pred})
    #     # only predictions on first word pieces are important
    #     else:
    #         if token_pred[0] not in ['[CLS]', '[UNK]', '[PAD]', '[SEP]']:
    #             word_prediction.append({token_pred[0]: token_pred[1]})
    #             prev_word_ids = word_idx
    #             prev_token_pred = token_pred[1]

    token_dict = {}
    volume_type_list = ["QT_SIZE", "QT_COUNT", "QT_OTHERS", "QT_WEIGHT", "QT_PERCENTAGE"]
    ingredient_type_list = ["CV_FOOD", "CV_DRINK", "PT_GRASS", "PT_FRUIT", "PT_OTHERS", "PT_PART", "AM_FISH",
                            "AM_OTHERS", "CV_INGREDIENT", "CV_SEASONING"]

    for token, pred, mapping, word_idx in zip(tokens, token_predictions, mapping.squeeze().tolist(), inputs.word_ids()):
        # only predictions on first word pieces are important
        if token not in ['[CLS]', '[UNK]', '[PAD]', '[SEP]'] and not(mapping[0] == 0 and mapping[1] == 0):
            if token_dict and token_dict['word_idx'] != word_idx:
                ne = (token_dict['token'].replace("#", ""), token_dict['pred'], token_dict['mapping'])
                token_prediction.append(ne)
                token_dict = {}
                continue

            if pred in ['QT_TEMPERATURE', 'TI_DURATION'] or pred in volume_type_list or pred in ingredient_type_list:
                if not token_dict:
                    token_dict = {'pred': pred, 'token': token, 'mapping': mapping, 'word_idx': word_idx}
                    continue

                if token_dict['pred'] == pred or ((pred in volume_type_list or pred in ['TI_DURATION', 'QT_TEMPERATURE']) and token_dict['pred'] in volume_type_list):
                    for i in range(token_dict['mapping'][1], mapping[0]):
                        token_dict['token'] += " "
                    token_dict['mapping'][1] = mapping[1]
                    token_dict['token'] += token.replace("#", "")

    if token_dict:
        ne = (token_dict['token'].replace("#", ""), token_dict['pred'], token_dict['mapping'])
        token_prediction.append(ne)
    return token_prediction


app = Flask(__name__)


@app.route('/', methods=['POST'])
def recipe():
    sentence = None
    if request.method == 'POST':
        sentence = request.data.decode('utf-8')

    if sentence is None:
        return make_response("Recipe is Blank", 406)

    response = []
    token_pred_list = predict(sentence)
    for token_id, token_pred in enumerate(token_pred_list):
        ner_node = {
            "id": token_id,
            "text": token_pred[0],
            "type": token_pred[1],
            "begin": token_pred[2][0],
            "end": token_pred[2][1]
        }

        response.append(ner_node)
    print(response)
    return make_response({"NE": response})


if __name__ == "__main__":
    MAX_LEN = 256
    device = 'cpu'
    unique_labels = {'OGG_EDUCATION', 'MT_ELEMENT', 'AFW_OTHER_PRODUCTS', 'MT_ROCK', 'TI_OTHERS', 'PS_NAME', 'CV_BUILDING_TYPE', 'AM_REPTILIA', 'OGG_FOOD', 'AF_MUSICAL_INSTRUMENT', 'QT_WEIGHT', 'AF_BUILDING', 'AFA_MUSIC', 'CV_SPORTS_INST', 'QT_ORDER', 'TM_COLOR', 'LCG_MOUNTAIN', 'QT_MAN_COUNT', 'PS_CHARACTER', 'AM_OTHERS', 'OGG_LIBRARY', 'TMM_DISEASE', 'OGG_MEDICINE', 'LCG_ISLAND', 'TI_MINUTE', 'MT_CHEMICAL', 'TM_CELL_TISSUE_ORGAN', 'QT_OTHERS', 'CV_TRIBE', 'QT_TEMPERATURE', 'PT_FLOWER', 'OGG_POLITICS', 'DT_WEEK', 'FD_ART', 'AM_AMPHIBIA', 'FD_MEDICINE', 'AF_CULTURAL_ASSET', 'AF_TRANSPORT', 'EV_SPORTS', 'LCG_CONTINENT', 'PT_TREE', 'TMI_SERVICE', 'AM_MAMMALIA', 'TM_SPORTS', 'CV_INGREDIENT', 'OGG_HOTEL', 'QT_PHONE', 'QT_COUNT', 'CV_LANGUAGE', 'CV_FUNDS', 'CV_CURRENCY', 'FD_OTHERS', 'LCG_RIVER', 'LCP_CAPITALCITY', 'LC_OTHERS', 'QT_SIZE', 'TM_CLIMATE', 'TM_SHAPE', 'CV_POLICY', 'EV_ACTIVITY', 'TR_ART', 'QT_ADDRESS', 'OGG_RELIGION', 'CV_POSITION', 'FD_HUMANITIES', 'CV_CULTURE', 'QT_SPORTS', 'QT_ALBUM', 'CV_ART', 'CV_FOOD', 'CV_LAW', 'OGG_MILITARY', 'DT_DAY', 'FD_SOCIAL_SCIENCE', 'LCP_PROVINCE', 'CV_CLOTHING', 'TI_HOUR', 'DT_DYNASTY', 'DT_SEASON', 'FD_SCIENCE', 'TMI_HW', 'OGG_SPORTS', 'TR_OTHERS', 'TM_DIRECTION', 'TMI_SITE', 'QT_LENGTH', 'MT_METAL', 'LCG_OCEAN', 'DT_OTHERS', 'LCP_COUNTY', 'TMIG_GENRE', 'OGG_ECONOMY', 'TMI_SW', 'CV_SPORTS_POSITION', 'AFA_DOCUMENT', 'PT_OTHERS', 'AFA_ART_CRAFT', 'EV_OTHERS', 'TMI_EMAIL', 'QT_PRICE', 'EV_FESTIVAL', 'TI_SECOND', 'CV_TAX', 'O', 'QT_VOLUME', 'AF_WEAPON', 'LCG_BAY', 'OGG_SCIENCE', 'PT_FRUIT', 'CV_OCCUPATION', 'QT_CHANNEL', 'OGG_ART', 'AM_INSECT', 'CV_FOOD_STYLE', 'QT_PERCENTAGE', 'OGG_LAW', 'TR_SCIENCE', 'CV_RELATION', 'AM_PART', 'QT_AGE', 'TMI_MODEL', 'AM_BIRD', 'OGG_OTHERS', 'CV_SPORTS', 'DT_YEAR', 'LCP_COUNTRY', 'AFA_VIDEO', 'DT_GEOAGE', 'TI_DURATION', 'AM_TYPE', 'CV_SEASONING', 'AM_FISH', 'CV_PRIZE', 'PS_PET', 'AFW_SERVICE_PRODUCTS', 'TMI_PROJECT', 'CV_DRINK', 'LC_SPACE', 'LCP_CITY', 'EV_WAR_REVOLUTION', 'AFA_PERFORMANCE', 'QT_SPEED', 'PT_GRASS', 'DT_MONTH', 'PT_PART', 'OGG_MEDIA', 'PT_TYPE', 'TMM_DRUG', 'AF_ROAD', 'DT_DURATION', 'TR_MEDICINE', 'TR_HUMANITIES'}
    # unique_labels = {'OGG_MEDICINE', 'CV_FOOD_STYLE', 'QT_TEMPERATURE', 'TI_MINUTE', 'QT_PHONE', 'CV_RELATION',
    #                  'FD_SOCIAL_SCIENCE', 'TM_SHAPE', 'LCG_OCEAN', 'AF_MUSICAL_INSTRUMENT', 'EV_WAR_REVOLUTION',
    #                  'FD_OTHERS', 'QT_PERCENTAGE', 'AFW_SERVICE_PRODUCTS', 'EV_OTHERS', 'AM_OTHERS', 'TR_MEDICINE',
    #                  'CV_SPORTS_INST', 'TM_CLIMATE', 'TR_HUMANITIES', 'LCP_COUNTY', 'QT_SPORTS', 'FD_HUMANITIES',
    #                  'TM_SPORTS', 'DT_OTHERS', 'TMI_HW', 'FD_MEDICINE', 'TR_ART', 'TR_SCIENCE', 'PS_NAME',
    #                  'TI_DURATION', 'LCP_CAPITALCITY', 'QT_OTHERS', 'CV_TRIBE', 'AM_MAMMALIA', 'AFA_VIDEO', 'OGG_FOOD',
    #                  'OGG_ART', 'PS_PET', 'TMI_PROJECT', 'OGG_LIBRARY', 'PS_CHARACTER', 'PT_OTHERS', 'TI_SECOND',
    #                  'TMI_EMAIL', 'DT_DYNASTY', 'MT_CHEMICAL', 'EV_FESTIVAL', 'CV_POLICY', 'AM_TYPE', 'QT_VOLUME',
    #                  'LCG_MOUNTAIN', 'FD_SCIENCE', 'LCP_CITY', 'TM_DIRECTION', 'LCP_COUNTRY', 'CV_ART',
    #                  'TM_CELL_TISSUE_ORGAN', 'CV_TAX', 'AM_REPTILIA', 'DT_GEOAGE', 'PT_TYPE', 'OGG_SPORTS', 'TM_COLOR',
    #                  'OGG_MEDIA', 'CV_POSITION', 'EV_ACTIVITY', 'CV_LANGUAGE', 'QT_LENGTH', 'CV_FOOD', 'DT_DAY',
    #                  'PT_GRASS', 'OGG_RELIGION', 'AFA_MUSIC', 'OGG_ECONOMY', 'QT_ADDRESS', 'LCG_BAY', 'O', 'DT_SEASON',
    #                  'TMI_SERVICE', 'QT_WEIGHT', 'QT_AGE', 'LCP_PROVINCE', 'CV_SPORTS', 'CV_FUNDS', 'AF_ROAD',
    #                  'LCG_RIVER', 'CV_CULTURE', 'PT_FLOWER', 'CV_OCCUPATION', 'AF_WEAPON', 'AM_BIRD', 'TR_OTHERS',
    #                  'AF_CULTURAL_ASSET', 'QT_CHANNEL', 'AF_TRANSPORT', 'OGG_POLITICS', 'AFA_ART_CRAFT', 'AM_FISH',
    #                  'CV_CURRENCY', 'EV_SPORTS', 'PT_TREE', 'LC_OTHERS', 'AFW_OTHER_PRODUCTS', 'LCG_ISLAND',
    #                  'AM_INSECT', 'CV_DRINK', 'OGG_EDUCATION', 'OGG_OTHERS', 'TI_HOUR', 'OGG_LAW', 'TMI_SW', 'MT_METAL',
    #                  'DT_WEEK', 'MT_ROCK', 'DT_DURATION', 'AFA_PERFORMANCE', 'TMM_DISEASE', 'OGG_HOTEL', 'QT_PRICE',
    #                  'LC_SPACE', 'DT_YEAR', 'QT_SIZE', 'FD_ART', 'DT_MONTH', 'CV_CLOTHING', 'CV_BUILDING_TYPE',
    #                  'CV_LAW', 'QT_ORDER', 'OGG_MILITARY', 'AM_AMPHIBIA', 'QT_COUNT', 'PT_PART', 'TMI_SITE',
    #                  'QT_MAN_COUNT', 'MT_ELEMENT', 'TMM_DRUG', 'TMI_MODEL', 'QT_ALBUM', 'TMIG_GENRE', 'AM_PART',
    #                  'CV_PRIZE', 'OGG_SCIENCE', 'LCG_CONTINENT', 'AF_BUILDING', 'TR_SOCIAL_SCIENCE', 'PT_FRUIT',
    #                  'TI_OTHERS', 'AFA_DOCUMENT', 'QT_SPEED', 'CV_SPORTS_POSITION'}

    # Map each label into its id representation and vice versa
    labels_to_ids = {k: v for v, k in enumerate(sorted(unique_labels))}
    ids_to_labels = {v: k for v, k in enumerate(sorted(unique_labels))}

    labels_to_ids['CV_ACT'] = 152
    ids_to_labels[152] = 'CV_ACT'

    model, tokenizer = load()
    app.run(host='0.0.0.0', port=5000)

