import argparse
import os
import pickle
import time
from tqdm import tqdm
from src.data.load import AliasDataset
from src.data.discover_alias import HasAlias
from src.model.pattern import Verbalizer
from src.train.test import init_log_sub_dirs, record_result, save_test_result
from demo.params import add_decode_param, add_rescore_param, add_test_param


def validate(old_records, verbalizer, args, log_dir):
    ref_dir, sum_dir = init_log_sub_dirs(log_dir)
    if args.test:
        data = AliasDataset(args.data_path, args.alias_type, 'test', exp_num=args.example_num)
    else:
        data = AliasDataset(args.data_path, args.alias_type, 'valid', exp_num=args.example_num)
    score = {'EM': [], 'True': []}
    records = []
    try:
        for batch_iter, batch in tqdm(enumerate(data.gen_batch()), desc="Ranking", total=data.example_num):
            if args.fast and batch_iter % 10 != 0:
                continue
            src_word, tgt_words = batch
            # fast or not
            if args.fast:
                idx = batch_iter // 10
            else:
                idx = batch_iter
            if args.record_type == 'rescore':
                # re-rank with new features scored by score.py
                old_record, score_vector_dict = old_records[idx]
                # dimension 1 is the number of templates
                template2pred_words = old_record['pred']
                pred_words = []
                for j, old_pred_words in enumerate(template2pred_words):
                    pred_word2sv = score_vector_dict['pred'][j]
                    candidate_num = len(pred_word2sv)
                    reranked_words = verbalizer.rerank_stings(old_pred_words[:candidate_num], pred_word2sv)
                    pred_words.append(reranked_words)
            else:
                old_record = old_records[idx]
                # re-rank here with original features like frequency
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
    except RuntimeError:
        # stop iteration raised by data
        pass
    return score, records


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--record_dir', required=True)
    parser.add_argument('--record_dir',
                        default='/data/tsq/xlink/bd/purify/filter_english/pool_80/result/abbreviation/few_shot/task_specific/time_12140900')
    # record type is different for those re-scored record
    parser.add_argument('--record_type', type=str, default='records', choices=['records', 'rescore'],
                        help="type of record.pkl")
    # grid search
    parser.add_argument('--interval', type=float, default=0.1, help="the interval used in grid search for lambda")
    parser.add_argument('--range', default=[0, 2], nargs='+', help="the range used in grid search for lambda")
    parser = add_rescore_param(parser)
    parser = add_decode_param(parser)
    parser = add_test_param(parser)
    args = parser.parse_args()
    verbalizer = Verbalizer(args.language, args.task)
    verbalizer.set_for_rerank(args)
    record_json_path = os.path.join(args.record_dir, '{}.pkl'.format(args.record_type))

    with open(record_json_path, 'rb') as fin:
        old_records = pickle.load(fin)
        if args.rank_strategy == 'prob_freq':
            # change lambda and grid search
            lower = args.range[0]
            upper = args.range[1]
            passes = int((upper - lower) / args.interval) + 1
            print("pass", passes)
            for _pass in range(passes):
                lamda = lower + _pass * args.interval
                args.freq_portion = lamda
                # create directory for this lambda
                reranked_dir = os.path.join(args.record_dir, 'rerank', args.rank_strategy,
                                            "lambda{}".format(str(lamda)))
                if not os.path.exists(reranked_dir):
                    os.makedirs(reranked_dir)
                scores, records = validate(old_records, verbalizer, args, reranked_dir)
                save_test_result(args, reranked_dir, scores, records)
        else:
            # no grid search
            reranked_dir = os.path.join(args.record_dir, 'rerank', args.rank_strategy,
                                        "time_" + time.strftime("%m%d%H%M"))
            if not os.path.exists(reranked_dir):
                os.makedirs(reranked_dir)
            scores, records = validate(old_records, verbalizer, args, reranked_dir)
            save_test_result(args, reranked_dir, scores, records)
            with open(os.path.join(reranked_dir, 'args.txt'), 'w', encoding='utf-8') as f:
                for k, v in args.__dict__.items():
                    f.write('%s: %s\n' % (k, str(v)))


if __name__ == "__main__":
    main()
