import argparse
import os
import json
import pickle
from tqdm import tqdm
from demo.call import contain_bad_punctuation
from src.data.DuEL.test import get_id2alias_table, evaluate


def check_fout(path):
    if os.path.exists(path):
        os.remove(path)
    fout = open(path, 'a')
    return fout


def coref_with_id(id2coref_alias, src_word, _id):
    try:
        alias_list, raw_chains = [], []
        coref_alias_list = id2coref_alias[_id]
        for coref_alias in coref_alias_list:
            coref_chain = coref_alias["coref_chain"]
            for mention in coref_chain:
                if mention["text"] != src_word:
                    has_exist = False
                    for _exist_alias in alias_list:
                        if _exist_alias["text"] == mention["text"]:
                            # frequency add 1
                            _exist_alias["score"] += 1
                            has_exist = True
                            break
                    if not has_exist and not contain_bad_punctuation(mention["text"]):
                        # init
                        alias_data = {"text": mention["text"], "score": 1}
                        alias_list.append(alias_data)

        raw_chains.extend(coref_alias_list)
        alias_list = sorted(alias_list, key=lambda k: (k.get('score')), reverse=True)
        return alias_list, raw_chains
    except KeyError:
        return [], []


def adapt(args):
    # get full entity name
    id2ent_name_pkl_path = os.path.join(args.corpus_dir, "id2ent_name.pkl")
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    output_dir = os.path.join(args.output_dir, f'ctx{args.context_window}', 'bd')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    coref_alias_path = os.path.join(output_dir, f"coref_stanford_parse_all_{args.src_text}.json")
    bd_id2coref_alias = json.load(open(coref_alias_path, 'r'))
    output_path = os.path.join(output_dir, f"standard_{args.src_text}.json")
    if args.task == 'parse':
        fout = check_fout(output_path)
    # data path
    input_path = os.path.join(args.duel_dir, f"{args.src_text}.json")
    with open(input_path, 'r') as fin:
        ent_id2corpus = json.load(fin)
        ent_ids = list(ent_id2corpus.keys())
        id2alias_table, id2subject = get_id2alias_table(args.duel_dir, args.corpus_dir, ent_ids)
        total_num = len(ent_ids)
        print(f"[0]Total entity in corpus is {total_num}")
        ent_id2result = {}
        for ent_id in tqdm(ent_ids, total=total_num, desc="parsing"):
            corpus_dicts = ent_id2corpus[ent_id]
            if args.task == 'parse':
                for corpus_dict in corpus_dicts:
                    coref_input_json = {"ID": corpus_dict["abstract_id"], "Text": "".join(corpus_dict["raw_text"])}
                    out_json = {"entity_list": corpus_dict["entity_list"], "coref_input": coref_input_json}
                    # write to json
                    fout.write(json.dumps(out_json, ensure_ascii=False))
                    fout.write("\n")
            else:
                # evaluate
                src_name = id2ent_name[ent_id]
                alias_table = id2alias_table[ent_id]
                # if len(alias_table) > 0:
                #     print("%" * 6)
                #     print(alias_table)
                alias_list, raw_chains = coref_with_id(bd_id2coref_alias, src_name, ent_id)
                # if len(alias_list) > 0:
                #     print("#" * 6)
                #     print(f"id is {ent_id}, src_name is {src_name}")
                #     print(alias_list)
                # save
                clean_alias_list = [dic['text'] for dic in alias_list]
                ent_id2result[ent_id] = {"src": src_name, "tgt": alias_table, "pred": clean_alias_list,
                                         "raw_chains": raw_chains}
        if args.task == 'evaluate':
            args.alias_source = args.src_text
            output_path = os.path.join(output_dir, f"{args.alias_source}.json")
            with open(output_path, 'w') as fout:
                json.dump(ent_id2result, fout, ensure_ascii=False, indent=4)
            fout.close()
            #  evaluate
            evaluate(args)


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--duel_dir', type=str, default='/data/tsq/DuEL/filtered')
    parser.add_argument('--corpus_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--output_dir', type=str, default='/data/tsq/DuEL/filtered/coref')
    # evaluate parameter
    parser.add_argument('--max_candidate_num', type=int, default=10)
    # sample parameter
    parser.add_argument('--context_window', type=int, default=100)
    parser.add_argument('--src_text', type=str, default='sample_entity_fill_100tokens', help="the input text from wiki")
    # task
    parser.add_argument('--task', type=str, default='parse',
                        choices=['parse', 'evaluate'])
    args = parser.parse_args()
    adapt(args)


if __name__ == '__main__':
    work()
