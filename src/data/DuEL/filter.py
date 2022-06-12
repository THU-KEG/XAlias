import argparse
import json
import pickle
import os


def filter(args):
    kb_data_path = os.path.join(args.duel_dir, "kb.json")
    with open(kb_data_path, 'r') as fin:
        lines = fin.readlines()
        print(f"[0]Total entity is {len(lines)}")
    # get full entity name
    id2ent_name_pkl_path = os.path.join(args.corpus_dir, "id2ent_name.pkl")
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    ent_names = set(id2ent_name.values())

    # rule1: Filter entity with alias number <= min_alias_num
    res_list1 = []
    for line in lines:
        record = json.loads(line.strip())
        alias_table = record["alias"]
        if len(alias_table) > args.min_alias_num:
            res_list1.append(line)
    print(f"[1]Total entity is {len(res_list1)}")
    # rule2: Filter entity with all english aliases
    res_list2 = []
    for line in res_list1:
        record = json.loads(line.strip())
        alias_table = record["alias"]
        is_all_english = True
        for alias in alias_table:
            if not alias.encode('utf-8').isalpha():
                # e.g. bilibili站
                is_all_english = False
                break
        if not is_all_english:
            res_list2.append(line)
    print(f"[2]Total entity is {len(res_list2)}")
    # rule3: Filter entity which doesn't show up in bd corpus's KB
    res_list3 = []
    for line in res_list1:
        record = json.loads(line.strip())
        subject = record["subject"]
        if subject in ent_names:
            res_list3.append(line)
    print(f"[3]Total entity is {len(res_list3)}")
    # output
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    output_path = os.path.join(args.output_dir, "kb.json")
    with open(output_path, "w") as fout:
        fout.writelines(res_list3)


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--duel_dir', type=str, default='/data/tsq/DuEL')
    parser.add_argument('--corpus_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--output_dir', type=str, default='/data/tsq/DuEL/filtered')

    # task
    parser.add_argument('--min_alias_num', type=int, default=4)
    args = parser.parse_args()

    filter(args)


if __name__ == '__main__':
    work()
