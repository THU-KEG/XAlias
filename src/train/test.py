import argparse
import os
import json
import shutil
from tqdm import tqdm
from src.data.load import AliasDataset
import bminf
from src.data.discover_alias import HasAlias
import numpy as np
import time
from src.model.pattern import Verbalizer
from demo.params import add_decode_param, reduce_args


def validate(data, model, device, log_dir, args, cpm2_kwargs, fast=True):
    # model.eval()
    # torch.cuda.empty_cache()
    ref_dir = os.path.join(log_dir, 'ref')
    sum_dir = os.path.join(log_dir, 'sum')

    if os.path.isdir(ref_dir):
        shutil.rmtree(ref_dir)
    os.mkdir(ref_dir)
    if os.path.isdir(sum_dir):
        shutil.rmtree(sum_dir)
    os.mkdir(sum_dir)

    score = {'EM': [], 'True': []}
    records = []
    # with torch.no_grad():
    try:
        verbalizer = Verbalizer(args.language, args.task)
        verbalizer.set_cpm2(model, cpm2_kwargs, args)
        for batch_iter, batch in tqdm(enumerate(data.gen_batch()), desc="Validating", total=data.example_num):
            if fast and batch_iter % 10 != 0:
                continue
            src_word, tgt_words = batch
            # generate by PLM
            if args.extra_prompt == 'task_specific':
                alias_table = data.sample_alias_table(args.task_specific_prompt_num)
                pred_words = verbalizer.cpm2_gen_by_prompt(data.alias_type, src_word, args.task_definition, alias_table)
            else:
                alias_table = None
                pred_words = verbalizer.cpm2_gen_by_prompt(data.alias_type, src_word, False, alias_table)
            golden = ' '.join(tgt_words)
            pred = ' '.join([i for arr in pred_words for i in arr])

            # record the result
            score, record = record_result(score, src_word, tgt_words, pred_words, ref_dir, sum_dir, golden, pred,
                                          batch_iter)
            if args.extra_prompt == 'task_specific':
                record['alias_table'] = alias_table
            records.append(record)
    except RuntimeError:
        pass
    return score, records


def record_result(score, src_word, tgt_words, pred_words, ref_dir, sum_dir, golden, pred, batch_iter):
    # update True and EM
    num_pattern = len(pred_words)
    nums_exact_match = [0] * num_pattern
    nums_ture = [0] * num_pattern
    for tgt_word in tgt_words:
        for i, pred_word_list in enumerate(pred_words):
            for pred_word in pred_word_list:
                # each pred_word correspond to a pattern's decode result
                if tgt_word == pred_word:
                    nums_exact_match[i] = 1
                if tgt_word in pred_word or pred_word in tgt_word:
                    nums_ture[i] = 1
    score['EM'].append(nums_exact_match)
    score['True'].append(nums_ture)
    # write
    with open(os.path.join(ref_dir, "%d_reference.txt" % batch_iter), 'w') as f:
        f.write(golden)
    with open(os.path.join(sum_dir, "%d_decoded.txt" % batch_iter), 'w') as f:
        f.write(pred)
    best_em = 0 if sum(nums_exact_match) == 0 else 1
    best_true = 0 if sum(nums_ture) == 0 else 1
    record = {'iter': batch_iter, 'src_word': src_word, 'golden': golden, 'pred': pred, 'EM': nums_exact_match,
              'True': nums_ture, 'best_EM': best_em, 'best_True': best_true}
    return score, record


def vis_scores(scores):
    recall_keys = {'rouge_1_recall', 'rouge_2_recall', 'rouge_l_recall', 'rouge_su4_recall'}
    f_keys = {'rouge_1_f_score', 'rouge_2_f_score', 'rouge_l_f_score'}
    if type(list(scores.values())[0]) == dict:
        for n in scores:
            if n == 'all':
                scores[n] = {k: scores[n][k] for k in f_keys}
            else:
                scores[n] = {k: scores[n][k] for k in recall_keys}
    else:
        scores = {k: scores[k] for k in f_keys}
    return json.dumps(scores, indent=4)


def work(args, cpm2_kwargs):
    device = 'cuda'
    if args.language == 'ch':
        np.random.seed(args.seed)
        model = bminf.models.CPM2(device=args.gpu_id)
    else:
        # huggingface
        model = None
    print("kwargs:", cpm2_kwargs)
    if args.test:
        data = AliasDataset(args.data_path, args.alias_type, 'test', exp_num=args.example_num)
    else:
        data = AliasDataset(args.data_path, args.alias_type, 'valid', exp_num=args.example_num)

    log_dir = os.path.join(args.result_dir, args.alias_type, args.learning, args.extra_prompt,
                           "time_" + time.strftime("%m%d%H%M"))
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    else:
        print('log dir %s exists, be careful that we will overwrite it' % log_dir)

    scores, records = validate(data, model, device, log_dir, args, cpm2_kwargs, fast=args.fast)

    # save the result
    with open(os.path.join(log_dir, 'records.json'), 'w', encoding='utf-8') as fr:
        fr.write(json.dumps(records, ensure_ascii=False, indent=4))

    with open(os.path.join(log_dir, 'scores.txt'), 'w', encoding='utf-8') as f:
        for k, v in args.__dict__.items():
            f.write('%s: %s\n' % (k, str(v)))
        avg_scores = {}
        for k, scores in scores.items():
            data_num = len(scores)  # scores is a list of list
            avg_p2s = [0] * len(scores[0])  # For avg_p2s, id is pattern's order, s is score
            for score_list in scores:
                for i, score in enumerate(score_list):
                    avg_p2s[i] += score
            avg_p2s = [score / data_num for score in avg_p2s]
            avg_scores[k] = avg_p2s
            avg_scores[k + "_sum"] = sum(avg_p2s)
        # record the best score
        avg_best_em = 0
        avg_best_true = 0
        for record in records:
            avg_best_em += record['best_EM']
            avg_best_true += record['best_True']
        avg_best_em /= len(records)
        avg_best_true /= len(records)
        avg_scores['best_EM'] = avg_best_em
        avg_scores['best_True'] = avg_best_true
        f.write(json.dumps(avg_scores, ensure_ascii=False, indent=4))
    # vis = vis_scores(scores)
    # print(vis)


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--ckpt', required=True)
    # data param
    parser.add_argument('--test', action="store_true")
    parser.add_argument('--fast', action="store_true")
    parser.add_argument('--example_num', type=int, default=-1)
    parser.add_argument('--alias_type', default='synonym',
                        choices=['prefix', 'suffix', 'abbreviation', 'synonym', 'punctuation', 'bilingual', 'multiple'])
    parser.add_argument('--result_dir', default='/data/tsq/xlink/bd/result')
    parser.add_argument('--data_path', default='/data/tsq/xlink/bd/has_alias_relation_record.pkl')

    # Whether to use data
    parser.add_argument('--learning', type=str, default='few_shot',
                        choices=['zero_shot', 'few_shot'])
    # few_shot
    parser.add_argument('--extra_prompt', type=str, default='task_specific',
                        choices=['task_specific', 'prefix_tuning'])
    parser.add_argument('--task_specific_prompt_num', type=int, default=4)
    parser.add_argument('--task_definition', action="store_true")
    parser = add_decode_param(parser)
    args = parser.parse_args()
    cpm2_kwargs = reduce_args(args)

    work(args, cpm2_kwargs)


if __name__ == "__main__":
    main()
