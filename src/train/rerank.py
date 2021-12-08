import argparse
import os
import json
import pickle
from tqdm import tqdm
from src.data.load import AliasDataset
import bminf
from src.data.discover_alias import HasAlias
import numpy as np
import shutil
from src.model.pattern import Verbalizer
from src.train.test import init_log_sub_dirs, record_result, save_test_result
from src.train.measure import hit_evaluate, get_avg_generate_nums
from demo.params import add_decode_param, reduce_args, add_test_param


def validate(old_records, verbalizer, args, log_dir):
    ref_dir, sum_dir = init_log_sub_dirs(log_dir)
    if args.test:
        data = AliasDataset(args.data_path, args.alias_type, 'test', exp_num=args.example_num)
    else:
        data = AliasDataset(args.data_path, args.alias_type, 'valid', exp_num=args.example_num)
    score = {'EM': [], 'True': []}
    records = []
    for batch_iter, batch in tqdm(enumerate(data.gen_batch()), desc="Validating", total=data.example_num):
        if args.fast and batch_iter % 10 != 0:
            continue
        src_word, tgt_words = batch
        old_record = old_records[batch_iter]
        # re-rank here
        pred_words = verbalizer.rerank(old_record['beams'])
        # None because we have record it before, so we can save some space
        pattern2beams = None
        golden = ' '.join(tgt_words)
        pred = ' '.join([i for arr in pred_words for i in arr])

        # record the result
        score, record = record_result(score, src_word, tgt_words, pred_words, ref_dir, sum_dir, golden, pred,
                                      pattern2beams, batch_iter)
        if args.extra_prompt == 'task_specific':
            record['alias_table'] = old_record['alias_table']
        records.append(record)
    return score, records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record_dir', required=True)
    parser = add_decode_param(parser)
    parser = add_decode_param(parser)
    args = parser.parse_args()
    verbalizer = Verbalizer(args.language, args.task)
    verbalizer.set_for_rerank(args)
    record_json_path = os.path.join(args.record_dir, 'records.pkl')
    reranked_dir = os.path.join(args.record_dir, 'rerank', args.rank_strategy)
    if not os.path.exists(reranked_dir):
        os.makedirs(reranked_dir)

    with open(record_json_path, 'rb') as fin:
        records = pickle.load(fin)
        scores, records = validate(records, verbalizer, args, reranked_dir)
        save_test_result(args, reranked_dir, scores, records)


if __name__ == "__main__":
    main()
