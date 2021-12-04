import argparse
import os
import json
from tqdm import tqdm
import pickle
import re

non_zh_reg = re.compile(u'[^\u4e00-\u9fa5]')
en_reg = re.compile(u'[a-zA-Z]')
punctuation = """！？｡＂＃＄％＆＇（）＊＋－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘'‛“”„‟…‧﹏"""


class DuplicateException(Exception):
    def __init__(self, err_word):
        Exception.__init__(self, err_word)


class HasAlias(object):
    def __init__(self, entity_id, source_word, target_words, a_type=None):
        self.entity_id = entity_id
        self.src_word = source_word
        self.tgt_words = target_words
        if a_type is not None:
            self.type = a_type
        else:
            assert len(target_words) == 1
            tgt_word = target_words[0]
            if len(source_word) == len(tgt_word):
                if source_word == tgt_word:
                    raise DuplicateException(tgt_word)
                else:
                    self.type = 'synonym'
            else:
                if len(source_word) > len(tgt_word):
                    self.short_word = tgt_word
                    self.long_word = source_word
                    type_suffix = '_reduce'
                else:
                    self.short_word = source_word
                    self.long_word = tgt_word
                    type_suffix = '_extend'
                # check the type of this relation
                if self.long_word.startswith(self.short_word):
                    self.type = 'suffix' + type_suffix
                elif self.long_word.endswith(self.short_word):
                    self.type = 'prefix' + type_suffix
                elif self.long_word[0] in punctuation or self.long_word[-1] in punctuation:
                    self.type = 'punctuation'
                elif self.has_non_chinese_translate(tgt_word):
                    self.type = 'bilingual'
                else:
                    # these 2 word might be Synonym or Abbreviation
                    # we use heuristic rule to divide them
                    if self.contain_every_char():
                        # if len(self.short_word) <= len(self.long_word) / 2 and self.contain_every_char():
                        if type_suffix == '_reduce':
                            self.type = 'abbreviation'
                        else:
                            self.type = 'expansion'
                    else:
                        self.type = 'synonym'

    def has_non_chinese_translate(self, tgt_word):
        # check bilingual, the non chinese part in src and tgt word must be different
        src_obj = non_zh_reg.search(self.src_word)
        tgt_obj = non_zh_reg.search(tgt_word)
        if src_obj or tgt_obj:
            if src_obj and tgt_obj:
                if len(src_obj.groups()) != len(tgt_obj.groups()):
                    return True
                for i in range(len(src_obj.groups())):
                    if src_obj.group(i) != tgt_obj.group(i):
                        return True
                return False
            else:
                return True
        else:
            return False

    def contain_stop_ch(self, task):
        # check noise like 连锁除外 [连锁除外
        if self.src_word.startswith('['):
            return True
        else:
            for tgt_word in self.tgt_words:
                if tgt_word.startswith('['):
                    return True
        # regular expression
        if task == 'filter_non_chinese':
            reg = non_zh_reg
        else:
            reg = en_reg
        src_obj = reg.search(self.src_word)
        if src_obj:
            return True
        else:
            for tgt_word in self.tgt_words:
                tgt_obj = reg.search(tgt_word)
                if tgt_obj:
                    return True

    def contain_every_char(self):
        for char in self.short_word:
            if char not in self.long_word:
                return False
        return True


def read_mention2ids(src_file_path):
    mention2ids = {}
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        for line in tqdm(lines, total=len(lines)):
            pieces = line.strip().split('::=')
            mention = pieces[0]
            ids = pieces[1:]
            mention2ids[mention] = ids
    return mention2ids


def get_alias_table(mention2ids, id2mention):
    """
    :param mention2ids: dict
    :param id2mention: dict
    :return: dict of dict( key: 'surjective/injective_aliases', value: list of str )
    """
    alias_table = {}
    for entity_id, mentions in id2mention.items():
        if len(mentions) < 2:
            continue
        # the injective alias must not have multiple ids
        injective_aliases = []
        surjective_aliases = []
        for mention in mentions:
            if len(mention2ids[mention]) == 1:
                injective_aliases.append(mention)
            else:
                surjective_aliases.append(mention)
        if len(injective_aliases) >= 1 and len(injective_aliases) + len(surjective_aliases) > 1:
            # add surjective alias. Any injective_alias can hasAlias surjective alia. But vice is wrong
            alias_table[entity_id] = {'injective_aliases': injective_aliases,
                                      'surjective_aliases': surjective_aliases}
    return alias_table


def get_has_alias_relation(alias_tables, id2ent_name):
    has_alias_relation_record = {
        'prefix_extend': [],  # List of HasAlias
        'prefix_reduce': [],
        'suffix_extend': [],
        'suffix_reduce': [],
        'abbreviation': [],
        'expansion': [],
        'synonym': [],
        'punctuation': [],
        # 'bilingual': [],
    }
    no_ent_name_num = 0
    for entity_id, alias_table in tqdm(alias_tables.items(), desc='get_has_alias_relation'):
        injective_aliases = alias_table['injective_aliases']
        surjective_aliases = alias_table['surjective_aliases']
        ent_name = id2ent_name[entity_id]
        alias_num = len(injective_aliases) + len(surjective_aliases)
        assert alias_num > 1
        # use ent_name as src_name
        if ent_name not in injective_aliases:
            no_ent_name_num += 1
            continue
        has_alias_relation_dict = {k: [] for k in has_alias_relation_record.keys()}
        tgt_words = injective_aliases + surjective_aliases
        for i, word in enumerate(tgt_words):
            if word == ent_name:
                continue
            else:
                has_alias = HasAlias(entity_id, ent_name, [word], None)
                if has_alias.type != 'bilingual':
                    has_alias_relation_dict[has_alias.type].append(has_alias)
        # allocate the relations into different types
        for k, lst in has_alias_relation_dict.items():
            has_alias_num = len(lst)
            if has_alias_num == 0:
                continue
            elif has_alias_num == 1:
                has_alias_relation_record[k].append(lst[0])
            else:
                # merge tgt_words of one src_word, we have known that every _has_alias in lst only has one tgt_word
                merged_tgt_words = [_has_alias.tgt_words[0] for _has_alias in lst]
                example = lst[0]
                merged = HasAlias(example.entity_id, example.src_word, merged_tgt_words, k)
                has_alias_relation_record[k].append(merged)
        # if alias_num == 2:
        #     for i, word in enumerate(injective_aliases):
        #         if len(surjective_aliases) == 1:
        #             has_alias = HasAlias(entity_id, word, [surjective_aliases[0]], None)
        #         else:
        #             has_alias = HasAlias(entity_id, word, [injective_aliases[1 - i]], None)
        #         has_alias_relation_record[has_alias.type].append(has_alias)
        # else:
        #     alias_type = 'multiple'
        #     for i, word in enumerate(injective_aliases):
        #         tgt_words = injective_aliases[:i] + injective_aliases[i + 1:] + surjective_aliases
        #         has_alias = HasAlias(entity_id, word, tgt_words, alias_type)
        #         has_alias_relation_record[alias_type].append(has_alias)

    print("There are {} data has no ent_name in injective_aliases".format(no_ent_name_num))
    return has_alias_relation_record


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--src_file', type=str, default='mention_anchors.txt')
    parser.add_argument('--mention_file_name', type=str, default='id2mention')
    parser.add_argument('--ent_name_file_name', type=str, default='id2ent_name')
    args = parser.parse_args()
    src_file_path = os.path.join(args.data_dir, args.src_file)
    mention2ids = read_mention2ids(src_file_path)
    id2mention_json_path = os.path.join(args.data_dir, "{}.json".format(args.mention_file_name))
    id2ent_name_pkl_path = os.path.join(args.data_dir, "{}.pkl".format(args.ent_name_file_name))
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    with open(id2mention_json_path, 'r') as json_file:
        id2mention = json.load(json_file)
        # get entity's alias.
        alias_table = get_alias_table(mention2ids, id2mention)
        has_alias_relation_record = get_has_alias_relation(alias_table, id2ent_name)
        result_path = os.path.join(args.data_dir, "has_alias_relation_record.pkl")
        with open(result_path, 'wb') as fout:
            pickle.dump(has_alias_relation_record, fout)


if __name__ == '__main__':
    work()
