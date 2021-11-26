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
                else:
                    self.short_word = source_word
                    self.long_word = tgt_word
                # check the type of this relation
                if self.long_word.startswith(self.short_word):
                    self.type = 'suffix'
                elif self.long_word.endswith(self.short_word):
                    self.type = 'prefix'
                elif self.long_word[0] in punctuation or self.long_word[-1] in punctuation:
                    self.type = 'punctuation'
                elif self.has_non_chinese_translate(tgt_word):
                    self.type = 'bilingual'
                else:
                    # these 2 word might be Synonym or Abbreviation
                    # we use heuristic rule to divide them
                    if len(self.short_word) <= len(self.long_word) / 2:
                        self.type = 'abbreviation'
                    # elif self.short_word[0] != self.long_word[0] or self.short_word[-1] != self.long_word[-1]:
                    #     self.type = 'abbreviation'
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


def get_has_alias_relation(alias_table):
    has_alias_relation_record = {
        'prefix': [],  # List of HasAlias
        'suffix': [],
        'abbreviation': [],
        'synonym': [],
        'punctuation': [],
        'bilingual': [],
        'multiple': [],
    }
    for entity_id, alias_table in tqdm(alias_table.items(), desc='get_has_alias_relation'):
        injective_aliases = alias_table['injective_aliases']
        surjective_aliases = alias_table['surjective_aliases']
        alias_num = len(injective_aliases) + len(surjective_aliases)
        assert alias_num > 1
        if alias_num == 2:
            for i, word in enumerate(injective_aliases):
                if len(surjective_aliases) == 1:
                    has_alias = HasAlias(entity_id, word, [surjective_aliases[0]], None)
                else:
                    has_alias = HasAlias(entity_id, word, [injective_aliases[1 - i]], None)
                has_alias_relation_record[has_alias.type].append(has_alias)
        else:
            alias_type = 'multiple'
            for i, word in enumerate(injective_aliases):
                tgt_words = injective_aliases[:i] + injective_aliases[i + 1:] + surjective_aliases
                has_alias = HasAlias(entity_id, word, tgt_words, alias_type)
                has_alias_relation_record[alias_type].append(has_alias)

    return has_alias_relation_record


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--src_file', type=str, default='mention_anchors.txt')
    parser.add_argument('--mention_file_name', type=str, default='id2mention')
    args = parser.parse_args()
    src_file_path = os.path.join(args.data_dir, args.src_file)
    mention2ids = read_mention2ids(src_file_path)
    id2mention_json_path = os.path.join(args.data_dir, "{}.json".format(args.mention_file_name))
    with open(id2mention_json_path, 'r') as json_file:
        id2mention = json.load(json_file)
        # get entity's alias.
        alias_table = get_alias_table(mention2ids, id2mention)
        has_alias_relation_record = get_has_alias_relation(alias_table)
        result_path = os.path.join(args.data_dir, "has_alias_relation_record.pkl")
        with open(result_path, 'wb') as fout:
            pickle.dump(has_alias_relation_record, fout)


if __name__ == '__main__':
    work()
