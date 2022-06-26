import bminf
import argparse
import os
import numpy as np
import json
from stanfordnlp.server import CoreNLPClient
import pickle
import WebApp.server.params as params
from src.data.DuEL.filter import add_ent_name
from tqdm import tqdm
from collections import Counter
from demo.call import prompt_with_json, coref_with_json, dict_with_json
import logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s')

ENABLE_EN_GLM = False


# load model


def get_id2alias_table(duel_dir, corpus_dir, ent_ids):
    kb_data_path = os.path.join(duel_dir, "kb.json")
    with open(kb_data_path, 'r') as fin:
        lines = fin.readlines()
        print(f"[1]Total entity in kb is {len(lines)}")
    # get full entity name
    id2ent_name_pkl_path = os.path.join(corpus_dir, "id2ent_name.pkl")
    with open(id2ent_name_pkl_path, 'rb') as fin:
        id2ent_name = pickle.load(fin)
    mention2ids_pkl_path = os.path.join(corpus_dir, "mention2ids.pkl")
    with open(mention2ids_pkl_path, 'rb') as fin:
        mention2ids = pickle.load(fin)
        mention2ids = add_ent_name(mention2ids, id2ent_name)
    id2alias_table = {}
    id2subject = {}
    for line in lines:
        record = json.loads(line.strip())
        alias_table = record["alias"]
        subject = record["subject"]
        ids = mention2ids[subject]
        assert len(ids) == 1
        ent_id = ids[0]
        assert ent_id in ent_ids
        id2alias_table[ent_id] = alias_table
        id2subject[ent_id] = subject

    return id2alias_table, id2subject


def get_alias_result(args, model, ent_id, src_word, corpus_dicts, tokenizer=None, _kwargs=None, device=None):
    if args.alias_source == 'prompt':
        client_json = {"lang": args.lang, "type": "all", "entity": src_word}
        if args.lang == "ch" and args.plm == 'cpm2':

            pred_words = prompt_with_json(model, client_json)
        else:
            pred_words = prompt_with_json(model, client_json, tokenizer, _kwargs, device)
    else:
        # coref
        pred_words = []
        if args.alias_source == 'coref':
            with CoreNLPClient(
                    properties="chinese",
                    annotators=["tokenize,ssplit,coref"],
                    endpoint="http://localhost:5114",
                    timeout=30000, memory='16G') as client:
                for corpus_dict in corpus_dicts:
                    if args.lang == "ch":
                        text = "".join(corpus_dict["raw_text"])
                    else:
                        text = " ".join(corpus_dict["raw_text"])
                    # start coref
                    coref_pred_words = []
                    ann = client.annotate(text=text, properties={"inputFormat": "text", "outputFormat": "json"})
                    for coref_chain in ann["corefs"].values():
                        has_alias = False
                        for _dict in coref_chain:
                            if _dict["text"] == src_word:
                                has_alias = True
                                break
                        if has_alias:
                            for _dict in coref_chain:
                                pred_word = _dict["text"]
                                if pred_word != src_word:
                                    coref_pred_words.append(pred_word)
                    pred_words.extend(coref_pred_words)
        else:
            # xlink
            for corpus_dict in corpus_dicts:
                entity_list = corpus_dict["entity_list"]
                for _lst in entity_list:
                    _id = _lst[0]
                    _name = _lst[1]
                    if _id == ent_id and src_word != _name:
                        pred_words.append(_name)
        # sort
        counter = Counter(pred_words)
        pred_words = [rst[0] for rst in counter.most_common()]
    return pred_words


def test_alias(args):
    # corpus
    sample_name = f"sample_{args.search_passage_with}_{args.missing_tokens_policy}_{args.context_window}tokens.json"
    sample_path = os.path.join(args.duel_dir, sample_name)
    with open(sample_path, 'r') as fin:
        ent_id2corpus = json.load(fin)
        ent_ids = ent_id2corpus.keys()
        print(f"[0]Total entity in corpus is {len(ent_ids)}")
    # data path
    id2alias_table, id2subject = get_id2alias_table(args.duel_dir, args.corpus_dir, ent_ids)
    # PLM
    if args.lang == "ch" and args.plm == 'cpm2':
        model = bminf.models.CPM2(device=params.gpu_id)
        tokenizer, _kwargs, device = None, None, None
    else:
        from src.model.GLM.generate_samples import init_glm
        model, tokenizer, _kwargs, device = init_glm(args.lang)
    # generate/discover alias using PLM/corpus
    ent_id2result = {}
    for ent_id, alias_table in tqdm(id2alias_table.items()):
        src_word = id2subject[ent_id]
        corpus_dicts = ent_id2corpus[ent_id]
        pred_words = get_alias_result(args, model, ent_id, src_word, corpus_dicts, tokenizer, _kwargs, device)
        # save
        ent_id2result[ent_id] = {"src": src_word, "tgt": alias_table, "pred": pred_words}
    # output
    output_dir = os.path.join(args.output_dir, f"{args.context_window}ctx")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, f"{args.alias_source}.json")
    with open(output_path, 'w') as fout:
        json.dump(ent_id2result, fout, ensure_ascii=False, indent=4)
    fout.close()
    #  evaluate
    evaluate(args)


def hit_evaluate(_results, num_return_sequences):
    hits = []
    results = list(_results)
    num_q = len(results)
    print(f"num_q is {num_q}")
    for q in range(num_q):
        # print(f"results[q] is {results[q]}")
        tgt_words = results[q]["tgt"]
        pred_words = results[q]["pred"]
        has_answers_q = [True if pred_word in tgt_words else False for pred_word in pred_words]
        pred_words_num = len(pred_words)
        hits_q = [1] * pred_words_num
        for i, h in enumerate(has_answers_q):
            if h:
                break
            else:
                hits_q[i] = 0
        # Note: pred_words_num may be <= num_return_sequences
        if pred_words_num < num_return_sequences:
            if len(hits_q) > 0:
                if hits_q[-1] == 0:
                    hits_q += [0] * (num_return_sequences - pred_words_num)
                else:
                    hits_q += [1] * (num_return_sequences - pred_words_num)
            else:
                hits_q += [0] * (num_return_sequences - pred_words_num)
        hits.append(hits_q)

    result_hits = np.array(hits)
    result_np = result_hits.mean(0)
    result = result_np.tolist()

    # print("{} in {} question has no answer".format(no_ans_question_num, num_q))
    return {"hits@" + str(i): v * 100 for i, v in enumerate(result)}


def evaluate(args):
    output_dir = os.path.join(args.output_dir, f"{args.context_window}ctx")
    input_path = os.path.join(output_dir, f"{args.alias_source}.json")
    if not os.path.exists(input_path):
        output_dir = os.path.join(args.output_dir, f"ctx{args.context_window}", "bd")
        input_path = os.path.join(output_dir, f"{args.alias_source}.json")
    with open(input_path, 'r') as fin:
        ent_id2result = json.load(fin)
    results = ent_id2result.values()
    data_num = len(results)
    score = {'EM': 0, 'True': 0, "hits": {}}
    for result in results:
        # truncate
        if args.alias_source == 'prompt':
            pred_lst = []
            for _lst in result["pred"].values():
                for __lst in _lst:
                    pred_lst.extend(__lst)
            # sort
            counter = Counter(pred_lst)
            pred_words = [rst[0] for rst in counter.most_common()]
            # remove src_name
            final_words = []
            for word in pred_words:
                if result["src"] != word:
                    final_words.append(word)
            result["pred"] = final_words
        result["pred"] = result["pred"][:args.max_candidate_num]
        # calculate EM and True and hits
        best_EM = 0
        best_True = 0
        for pred_word in result["pred"]:
            for tgt_word in result["tgt"]:
                if tgt_word == pred_word:
                    best_EM = 1
                if tgt_word in pred_word:
                    best_True = 1
        score["EM"] += best_EM
        score["True"] += best_True
    score["EM"] /= data_num
    score["True"] /= data_num
    score["hits"] = hit_evaluate(results, args.max_candidate_num)
    score["results"] = list(results)
    with open(os.path.join(output_dir, f'{args.alias_source}_score.json'), 'w', encoding='utf-8') as f_hits:
        f_hits.write(json.dumps(score, ensure_ascii=False, indent=4))


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--duel_dir', type=str, default='/data/tsq/DuEL/filtered')
    parser.add_argument('--corpus_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--output_dir', type=str, default='/data/tsq/DuEL/filtered')

    # dump parameter
    parser.add_argument('--search_passage_with', type=str, default='entity',
                        choices=['entity', 'aliases'])
    # sample parameter
    parser.add_argument('--context_window', type=int, default=100)
    parser.add_argument('--missing_tokens_policy', type=str, default='fill',
                        choices=['fill', 'ignore'])
    # evaluate parameter
    parser.add_argument('--max_candidate_num', type=int, default=10)
    # task
    parser.add_argument('--lang', type=str, default='ch',
                        choices=['ch', 'en'])
    parser.add_argument('--plm', type=str, default='cpm2',
                        choices=['cpm2', 'glm'])
    parser.add_argument('--alias_source', type=str, default='prompt',
                        choices=['prompt', 'coref', 'xlink'])
    parser.add_argument('--task', type=str, default='test',
                        choices=['test', 'evaluate'])
    args = parser.parse_args()
    if args.task == 'test':
        test_alias(args)
    elif args.task == 'evaluate':
        evaluate(args)


if __name__ == '__main__':
    work()
