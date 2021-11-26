import argparse
import os
import json
from tqdm import tqdm
import pickle
import re
from src.data.discover_alias import HasAlias
from src.model.const import few_shot_alias_table


def _filter(has_alias_relation_record: dict, task: str):
    new_data = {}
    for alias_type, has_alias_list in has_alias_relation_record.items():
        if alias_type == 'bilingual':
            # we do not filter the bilingual type aliases
            new_data[alias_type] = has_alias_list
            continue
        cleaned_list = []
        for has_alias in tqdm(has_alias_list):
            if has_alias.contain_stop_ch(task):
                continue
            else:
                cleaned_list.append(has_alias)
        new_data[alias_type] = cleaned_list

    return new_data


def _filter_stop_words(has_alias_relation_record: dict):
    new_data = {}
    filtered_num = 0
    for alias_type, has_alias_list in has_alias_relation_record.items():
        if alias_type == 'bilingual' or alias_type == 'multiple':
            # we do not filter the bilingual and multiple type aliases
            new_data[alias_type] = has_alias_list
            continue
        stop_src_words = list(few_shot_alias_table[alias_type].keys())
        cleaned_list = []
        for has_alias in tqdm(has_alias_list):
            if has_alias.src_word in stop_src_words:
                filtered_num += 1
                continue
            else:
                cleaned_list.append(has_alias)
        new_data[alias_type] = cleaned_list
    print("[1] Filter stop words data: ", filtered_num)
    return new_data, filtered_num


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--data_name', type=str, default='has_alias_relation_record.pkl')
    parser.add_argument('--new_data_dir', type=str, default='/data/tsq/xlink/bd/purify')
    parser.add_argument('--task', type=str, default='filter_english',
                        choices=['filter_english', 'filter_non_chinese'])
    parser.add_argument('--stop_words', type=str, default='pool',
                        choices=['none', 'pool'])
    parser.add_argument('--new_data_name', type=str, default='has_alias_relation_record.pkl')
    args = parser.parse_args()
    # path
    data_path = os.path.join(args.data_dir, args.data_name)
    new_data_dir = os.path.join(args.new_data_dir, args.task)

    # load data
    with open(data_path, 'rb') as fin:
        data = pickle.load(fin)
        # filter english or non chinese
        if args.task == 'filter_english' or args.task == 'filter_non_chinese':
            new_data_dict = _filter(data, args.task)
        else:
            new_data_dict = data
        # filter stop words
        if args.stop_words != 'none':
            new_data_dict, filtered_num = _filter_stop_words(new_data_dict)
            new_data_dir = os.path.join(new_data_dir, '{}_{}'.format(args.stop_words, filtered_num))
        # save
        if not os.path.exists(new_data_dir):
            os.makedirs(new_data_dir)
        result_path = os.path.join(new_data_dir, args.new_data_name)
        with open(result_path, 'wb') as fout:
            pickle.dump(new_data_dict, fout)


if __name__ == '__main__':
    work()
