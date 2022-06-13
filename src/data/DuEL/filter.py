import argparse
import json
import pickle
import jieba
import os
from tqdm import tqdm
from demo.coref.resolution import parse_xlink_text, restrict_length

LANG = 'ch'


def add_ent_name(mention2ids, id2ent_name):
    for ent_id, ent_name in id2ent_name.items():
        try:
            if ent_id not in mention2ids[ent_name]:
                mention2ids[ent_name].append(ent_id)
        except KeyError:
            mention2ids[ent_name] = [ent_id]
    return mention2ids


def filter_kb(args):
    kb_data_path = os.path.join(args.duel_dir, "kb.json")
    with open(kb_data_path, 'r') as fin:
        lines = fin.readlines()
        print(f"[0]Total entity is {len(lines)}")
    # get full entity name
    id2ent_name_pkl_path = os.path.join(args.corpus_dir, "id2ent_name.pkl")
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    ent_names = set(id2ent_name.values())
    mention2ids_pkl_path = os.path.join(args.corpus_dir, "mention2ids.pkl")
    with open(mention2ids_pkl_path, 'rb') as fin:
        mention2ids = pickle.load(fin)
        mention2ids = add_ent_name(mention2ids, id2ent_name)

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
        has_chinese = False
        for alias in alias_table:
            for uchar in alias:
                if u'\u4e00' <= uchar <= u'\u9fff':
                    # e.g. bilibili站
                    has_chinese = True
                    break
            if has_chinese:
                break
        if has_chinese:
            res_list2.append(line)
    print(f"[2]Total entity is {len(res_list2)}")
    # rule3: Filter entity which doesn't show up in bd corpus's KB
    res_list3 = []
    for line in res_list2:
        record = json.loads(line.strip())
        subject = record["subject"]
        if subject in ent_names:
            res_list3.append(line)
    print(f"[3]Total entity is {len(res_list3)}")
    # rule4: Filter entity which has conflict name with other entities
    res_list4 = []
    for line in res_list3:
        record = json.loads(line.strip())
        subject = record["subject"]
        if len(mention2ids[subject]) == 1:
            res_list4.append(line)
    print(f"[4]Total entity is {len(res_list4)}")
    # output
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    output_path = os.path.join(args.output_dir, "kb.json")
    with open(output_path, "w") as fout:
        fout.writelines(res_list4)


def is_contain_entity(ent_id2corpus, _id, entity_list):
    if _id in ent_id2corpus.keys():
        return True
    for ent_id_and_name in entity_list:
        if ent_id_and_name[0] in ent_id2corpus.keys():
            return True
    return False


def get_cut(raw_text):
    if LANG == 'ch':
        seg = jieba.lcut(raw_text)
    else:
        seg = raw_text.strip().split()
    return seg, len(seg)


def dump(args):
    kb_data_path = os.path.join(args.duel_dir, "kb.json")
    with open(kb_data_path, 'r') as fin:
        lines = fin.readlines()
        print(f"[0]Total entity is {len(lines)}")
    src_file_path = os.path.join(args.corpus_dir, "standard_abstract.txt")
    # output
    result_name = f"dump_passage_with_{args.search_passage_with}.json"
    output_path = os.path.join(args.output_dir, result_name)
    # get full entity name
    id2ent_name_pkl_path = os.path.join(args.corpus_dir, "id2ent_name.pkl")
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    mention2ids_pkl_path = os.path.join(args.corpus_dir, "mention2ids.pkl")
    with open(mention2ids_pkl_path, 'rb') as fin:
        mention2ids = pickle.load(fin)
        mention2ids = add_ent_name(mention2ids, id2ent_name)
    # dump passages with entity showed up
    ent_id2corpus = {}
    for line in lines:
        record = json.loads(line.strip())
        subject = record["subject"]
        ent_id = mention2ids[subject][0]
        ent_id2corpus[ent_id] = []
    # read corpus
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        total_num = len(lines)
    for line in tqdm(lines, total=total_num):
        id_and_txt = line.split('\t\t')
        _id = id_and_txt[0]
        _text = restrict_length(id_and_txt[1])
        raw_text, entity_list = parse_xlink_text(_text)
        seg_lst, length = get_cut(raw_text)
        corpus_dict = {
            "abstract_id": _id,
            "abstract": line,
            "raw_text_len": length,
            "raw_text": seg_lst,
            "entity_list": entity_list
        }
        # append corpus to those entities showed up in corpus
        candidate_id_list = [_id] + [entity[0] for entity in entity_list]
        for candidate_id in candidate_id_list:
            if candidate_id in ent_id2corpus.keys():
                ent_id2corpus[candidate_id].append(corpus_dict)

    # output
    with open(output_path, 'w') as fout:
        json.dump(ent_id2corpus, fout, ensure_ascii=False, indent=4)
    fout.close()


def count_passage_num(ent_id2corpus):
    num_count = {}
    for _lst in ent_id2corpus.values():
        passage_num = len(_lst)
        try:
            num_count[passage_num] += 1
        except KeyError:
            num_count[passage_num] = 1
    # output
    num_count = sorted(num_count.items(), key=lambda item: item[0])
    _passage_num = 0
    for k, v in num_count:
        _passage_num += k * v
        # print(f"{v} entities has {k} passages")
    avg_passage_num = _passage_num / len(ent_id2corpus.keys())
    print(f"Average passage_num is {avg_passage_num}")


def sample(args):
    dump_name = f"dump_passage_with_{args.search_passage_with}.json"
    kb_data_path = os.path.join(args.duel_dir, dump_name)
    with open(kb_data_path, 'r') as fin:
        ent_id2corpus = json.load(fin)
        print(f"[0]Total entity is {len(ent_id2corpus.keys())}")
        count_passage_num(ent_id2corpus)
    # output path
    result_name = f"sample_{args.search_passage_with}_{args.missing_tokens_policy}_{args.context_window}tokens.json"
    output_path = os.path.join(args.output_dir, result_name)
    # sample from ent_id2corpus
    final_ent_id2corpus = {}
    for ent_id, _lst in ent_id2corpus.items():
        final_ent_id2corpus[ent_id] = []
        sorted_lst = sorted(_lst, key=lambda dic: dic["raw_text_len"])
        total_token_num = 0
        for corpus_dict in sorted_lst:
            if total_token_num < args.context_window:
                if corpus_dict["raw_text_len"] + total_token_num < args.context_window:
                    final_ent_id2corpus[ent_id].append(corpus_dict)
                    total_token_num += corpus_dict["raw_text_len"]
                else:
                    if args.missing_tokens_policy == 'fill':
                        missing_tokens_num = args.context_window - total_token_num
                        corpus_dict["raw_text"] = corpus_dict["raw_text"][:missing_tokens_num]
                        final_ent_id2corpus[ent_id].append(corpus_dict)
                    else:
                        break
            else:
                break

    # output
    count_passage_num(final_ent_id2corpus)
    with open(output_path, 'w') as fout:
        json.dump(final_ent_id2corpus, fout, ensure_ascii=False, indent=4)
    fout.close()


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--duel_dir', type=str, default='/data/tsq/DuEL')
    parser.add_argument('--corpus_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--output_dir', type=str, default='/data/tsq/DuEL/filtered')

    # task
    parser.add_argument('--min_alias_num', type=int, default=4)
    parser.add_argument('--task', type=str, default='filter',
                        choices=['filter', 'dump', 'sample'])
    # dump parameter
    parser.add_argument('--search_passage_with', type=str, default='entity',
                        choices=['entity', 'aliases'])
    # sample parameter
    parser.add_argument('--context_window', type=int, default=100)
    parser.add_argument('--missing_tokens_policy', type=str, default='fill',
                        choices=['fill', 'ignore'])

    args = parser.parse_args()
    if args.task == 'filter':
        filter_kb(args)
    elif args.task == 'dump':
        dump(args)
    elif args.task == 'sample':
        sample(args)


if __name__ == '__main__':
    work()
