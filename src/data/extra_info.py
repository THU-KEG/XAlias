import argparse
import os
import json
from tqdm import tqdm
import pickle
import re


class InfoBox(object):
    def __init__(self, entity_id, entity_word, attribute_dict):
        self.entity_id = entity_id
        self.entity_word = entity_word
        self.attribute_dict = attribute_dict


def parse_value(value_str):
    clean_v = ''
    state = 0
    for ch in value_str:
        if state == 0:
            # init state
            if ch == '[':
                state = 1
            else:
                clean_v += ch
        elif state == 1:
            if ch == '[':
                state = 2
        elif state == 2:
            if ch == '|':
                state = 3
        elif state == 3:
            # read until ]
            if ch == ']':
                state = 4
            else:
                clean_v += ch
        else:
            if ch == ']':
                state = 0
    return clean_v


def read_and_check_answer(lines, id2ent_name, id2mention):
    """
    :param lines: lines of info box
    :param id2ent_name: dict: id to entity's  full name
    :param id2mention: dict: id to entity's mentions
    :return: dict: id to info box, we make sure there is no answer leak, each attribute of info box is carefully checked
    """
    id2info_box = {}
    for line in tqdm(lines, total=len(lines)):
        id_and_attributes = line.strip('\n').split('\t\t')
        ent_id = id_and_attributes[0]
        try:
            ent_mentions = id2mention[ent_id]
            if len(ent_mentions) < 2:
                # no need to record these single entities' info boxes
                continue
            ent_name = id2ent_name[ent_id]
        except KeyError:
            # no need to record these nameless entities' info boxes
            continue
        # Entity's mentions should not be contained in info box.
        # But entity's full name can show up because our alias generation task's input is it.
        # It is ok that we use shallow copy here
        forbidden_words = ent_mentions
        try:
            forbidden_words.remove(ent_name)
        except ValueError:
            # print('ent_id', ent_id)
            # print('ent_name', ent_name)
            # print('ent_mentions', forbidden_words)
            # print('line', line)
            # no need to record these entities because their ent_name is not contained in mentions
            continue
        attributes_str = id_and_attributes[1]
        attributes_k_v_list = attributes_str.split(',')
        k_v_num = len(attributes_k_v_list) // 2
        attribute_dict = {}
        for i in range(k_v_num):
            idx = i * 2
            k = attributes_k_v_list[idx]
            value_str = attributes_k_v_list[idx + 1]
            # We assert that k is just a string which is not necessary to check
            # But we need to check v
            clean_v = parse_value(value_str)
            # check forbidden_word here
            is_bad_attribute = False
            for forbidden_word in forbidden_words:
                if forbidden_word in clean_v:
                    is_bad_attribute = True
                    break
            if not is_bad_attribute:
                attribute_dict[k] = clean_v
        info_box = InfoBox(ent_id, ent_name, attribute_dict)
        id2info_box[ent_id] = info_box
    return id2info_box


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--src_file', type=str, default='standard_infobox.txt')
    parser.add_argument('--ent_name_file_name', type=str, default='id2ent_name')
    parser.add_argument('--mention_file_name', type=str, default='id2mention')
    args = parser.parse_args()
    src_file_path = os.path.join(args.data_dir, args.src_file)
    id2mention_json_path = os.path.join(args.data_dir, "{}.json".format(args.mention_file_name))
    id2ent_name_pkl_path = os.path.join(args.data_dir, "{}.pkl".format(args.ent_name_file_name))
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    with open(id2mention_json_path, 'r') as json_file:
        id2mention = json.load(json_file)
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        print("[1]Start reading")
        id2info_box = read_and_check_answer(lines, id2ent_name, id2mention)
        result_path = os.path.join(args.data_dir, "id2info_box.pkl")
        with open(result_path, 'wb') as fout:
            pickle.dump(id2info_box, fout)
            print("[2]Save {}".format(result_path))


if __name__ == '__main__':
    work()
