import argparse
import os
import json
from tqdm import tqdm


def check_fout(path):
    if os.path.exists(path):
        os.remove(path)
    fout = open(path, 'a')
    return fout


def adapt(args):
    output_dir = os.path.join(args.output_dir, f'ctx{args.context_window}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, f"standard_{args.src_text}.json")
    fout = check_fout(output_path)
    input_path = os.path.join(args.duel_dir, f"{args.src_text}.json")
    with open(input_path, 'r') as fin:
        ent_id2corpus = json.load(fin)
        ent_ids = list(ent_id2corpus.keys())
        total_num = len(ent_ids)
        print(f"[0]Total entity in corpus is {total_num}")
        for ent_id in tqdm(ent_ids, total=total_num, desc="parsing"):
            corpus_dicts = ent_id2corpus[ent_id]
            for corpus_dict in corpus_dicts:
                coref_input_json = {"ID": corpus_dict["abstract_id"], "Text": "".join(corpus_dict["raw_text"])}
                out_json = {"entity_list": corpus_dict["entity_list"], "coref_input": coref_input_json}
                # write to json
                fout.write(json.dumps(out_json, ensure_ascii=False))
                fout.write("\n")


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--duel_dir', type=str, default='/data/tsq/DuEL/filtered')
    parser.add_argument('--output_dir', type=str, default='/data/tsq/DuEL/filtered/coref')
    # sample parameter
    parser.add_argument('--context_window', type=int, default=100)
    parser.add_argument('--src_text', type=str, default='sample_entity_fill_100tokens', help="the input text from wiki")
    args = parser.parse_args()
    adapt(args)


if __name__ == '__main__':
    work()
