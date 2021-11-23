# coding: utf-8
import pickle
import random
from src.data.discover_alias import HasAlias

SOS = 2
EOS = 3


class AliasDataset:
    def __init__(self, data_path, alias_type, split, shuffle=False, fraction=1, exp_num=-1):
        __dic = {'train': 0, 'valid': 1, 'test': 2}
        self.data_split = __dic[split]

        with open(data_path, 'rb') as fin:
            self.data = pickle.load(fin)

        self.alias_type = alias_type
        self.shuffle = shuffle
        self.pure_data = self.data[self.alias_type]
        if exp_num == -1:
            self.example_num = int(len(self.pure_data) * fraction)
        else:
            self.example_num = exp_num
        self.pure_data = self.pure_data[:self.example_num]

    def gen_batch(self, required_index=None):

        all_examples = self.pure_data
        if self.shuffle:
            random.shuffle(all_examples)

        for pure_data in all_examples:
            _src_word = pure_data.src_word
            _tgt_words = pure_data.tgt_words

            yield _src_word, _tgt_words

        raise StopIteration

    def sample(self, num, reverse=False):
        if reverse:
            examples = self.pure_data[-num:]
        else:
            examples = random.sample(self.pure_data, num)
        pairs = []
        for pure_data in examples:
            if len(pairs) >= num:
                break
            src_word = pure_data.src_word
            tgt_words = pure_data.tgt_words
            for tgt_word in tgt_words:
                pairs.append((src_word, tgt_word))
        return pairs

    def sample_alias_table(self, num):
        examples = random.sample(self.pure_data, num)
        alias_table = {}
        alias_num = 0
        for pure_data in examples:
            if alias_num >= num:
                break
            src_word = pure_data.src_word
            tgt_words = pure_data.tgt_words
            alias_table[src_word] = tgt_words
            alias_num += len(tgt_words)
        return alias_table

    def get_alias_example_table(self, src_word, args):
        if args.alias_example_strategy == 'cluster':
            alias_table = self.sample_alias_table(src_word)
        else:
            # randomly sample examples
            alias_table = self.sample_alias_table(args.task_specific_prompt_num)
        return alias_table


if __name__ == "__main__":
    t = AliasDataset('/data/tsq/xlink/bd/has_alias_relation_record.pkl', 'synonym', 'test')

    for _src_word, _tgt_word in t.sample(100, reverse=True):
        print(_src_word, _tgt_word)
