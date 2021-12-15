# coding: utf-8
import pickle
import random
from src.data.discover_alias import HasAlias
from src.model.const import few_shot_alias_table

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

    def gen_batch(self, required_index=False):

        all_examples = self.pure_data
        if self.shuffle:
            random.shuffle(all_examples)

        for pure_data in all_examples:
            _src_word = pure_data.src_word
            _tgt_words = pure_data.tgt_words
            if required_index:
                _entity_id = pure_data.entity_id,
                yield _entity_id, _src_word, _tgt_words
            else:
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

    def sample_alias_table(self, num, alias_data_source):
        alias_table = {}
        if alias_data_source == 'whole_dataset':
            examples = random.sample(self.pure_data, num)
            alias_num = 0
            for pure_data in examples:
                if alias_num >= num:
                    break
                src_word = pure_data.src_word
                tgt_words = pure_data.tgt_words
                alias_table[src_word] = tgt_words
                alias_num += len(tgt_words)
        else:
            # from support pool
            src_table = few_shot_alias_table[self.alias_type]
            example_keys = random.sample(src_table.keys(), num)
            alias_table = {k: src_table[k] for k in example_keys}

        return alias_table

    def get_alias_example_tables(self, src_word, args):
        alias_tables = []
        if args.alias_example_strategy == 'cluster':
            # use cluster to calculate similarity, not finished yet
            alias_table = self.sample_alias_table(src_word, args.alias_data_source)
        else:
            # randomly sample examples from whole dataset or support pool
            for i in range(args.alias_table_num):
                # use random seed to maintain reproducing ability
                random.seed(args.seed)
                alias_table = self.sample_alias_table(args.task_specific_prompt_num, args.alias_data_source)
                alias_tables.append(alias_table)
                # change seed for every table
                args.seed += 1
        return alias_tables


if __name__ == "__main__":
    # t = AliasDataset('/data/tsq/xlink/bd/has_alias_relation_record.pkl', 'prefix_extend', 'test')
    t = AliasDataset('/data/tsq/xlink/bd/purify/filter_english/pool_80/has_alias_relation_record.pkl', 'prefix_extend',
                     'test')
    # t = AliasDataset('/data/tsq/xlink/bd/purify/filter_english/pool_100/has_alias_relation_record.pkl', 'synonym',
    #                  'test')

    for _src_word, _tgt_word in t.sample(500, reverse=True):
        print(_src_word, _tgt_word)
