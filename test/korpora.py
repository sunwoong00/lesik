import os

from Korpora import Korpora
import kss
import ray
import kss
from itertools import chain
from sklearn.model_selection import train_test_split

ray.init()

@ray.remote
def split_sentences(corpus):
    splited_sentences = []

    for sentences in corpus:
        sentences = sentences.replace("'", "")
        sentences = sentences.replace("\"", "")
        sentences = sentences.split("\n")

        for sentence in sentences:
            splited_sentences.extend(kss.split_sentences(sentence))
    return splited_sentences

def chunker_list(seq, size):
    return (seq[i::size] for i in range(size))

# root_dir에 말뭉치 경로를 입력
modu_ne = Korpora.load("modu_ne")

splited_sentences = []
corpus = modu_ne.get_all_texts()

# 프로세스 개수
process_num = 30

# 프로세스 개수만큼 corpus 분리
sentences_chunk = list(chunker_list(corpus, process_num))

# ray를 이용해 멀티프로세싱
futures = [split_sentences.remote(sentences_chunk[i]) for i in range(process_num)]

# 결과를 1-d로 합치기
results = ray.get(futures)
results = list(chain.from_iterable(results))

test_size = int(len(results) * 0.1)
train, val = train_test_split(results, test_size=test_size, random_state=111)
train, test = train_test_split(train, test_size=test_size, random_state=111)


def write_dataset(file_name, dataset):
    with open(
            os.path.join("data/nikl_newspaper", file_name), mode="w", encoding="utf-8"
    ) as f:
        for data in dataset:
            f.write(data)


write_dataset("train.txt", train)
write_dataset("val.txt", val)
write_dataset("test.txt", test)

class Preprocessor:
    def __init__(self, max_len: int):
        self.tokenizer = KoBertTokenizer.from_pretrained("monologg/kobert")
        self.max_len = max_len
        self.pad_token_id = 0

    def get_input_features(
            self, sentence: List[str], tags: List[str]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """문장과 띄어쓰기 tagging에 대해 feature로 변환한다.

        Args:
            sentence: 문장
            tags: 띄어쓰기 tagging

        Returns:
            feature를 리턴한다.
            input_ids, attention_mask, token_type_ids, slot_labels
        """

        input_tokens = []
        slot_label_ids = []

        # tokenize
        for word, tag in zip(sentence, tags):
            tokens = self.tokenizer.tokenize(word)

            if len(tokens) == 0:
                tokens = self.tokenizer.unk_token

            input_tokens.extend(tokens)

            for i in range(len(tokens)):
                if i == 0:
                    slot_label_ids.extend([tag])
                else:
                    slot_label_ids.extend([self.pad_token_id])

        # max_len보다 길이가 길면 뒤에 자르기
        if len(input_tokens) > self.max_len - 2:
            input_tokens = input_tokens[: self.max_len - 2]
            slot_label_ids = slot_label_ids[: self.max_len - 2]

        # cls, sep 추가
        input_tokens = (
                [self.tokenizer.cls_token] + input_tokens + [self.tokenizer.sep_token]
        )
        slot_label_ids = [self.pad_token_id] + slot_label_ids + [self.pad_token_id]

        # token을 id로 변환
        input_ids = self.tokenizer.convert_tokens_to_ids(input_tokens)

        attention_mask = [1] * len(input_ids)
        token_type_ids = [0] * len(input_ids)

        # padding
        pad_len = self.max_len - len(input_tokens)
        input_ids = input_ids + ([self.tokenizer.pad_token_id] * pad_len)
        slot_label_ids = slot_label_ids + ([self.pad_token_id] * pad_len)
        attention_mask = attention_mask + ([0] * pad_len)
        token_type_ids = token_type_ids + ([0] * pad_len)

        input_ids = torch.tensor(input_ids, dtype=torch.long)
        attention_mask = torch.tensor(attention_mask, dtype=torch.long)
        token_type_ids = torch.tensor(token_type_ids, dtype=torch.long)
        slot_label_ids = torch.tensor(slot_label_ids, dtype=torch.long)

        return input_ids, attention_mask, token_type_ids, slot_label_ids