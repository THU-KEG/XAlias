import argparse
import os
import pickle
from src.model.decode import beam_search, Beam, generate_return_beam
from difflib import SequenceMatcher
from src.model.const import patterns, few_shot_alias_table


def observe_cases(args, data_num, old_records, rerank_records):
    for i in range(data_num):
        if args.record_type == 'rescore':
            old_record, old_score_vector_dict = old_records[i]
            rerank_record, rerank_score_vector_dict = rerank_records[i]
        else:
            old_record = old_records[i]
            rerank_record = rerank_records[i]
        # compare these 2 pred_words
        tgt_words = old_record['tgt']
        old_template2pred_words = old_record['pred']
        rerank_template2pred_words = rerank_record['pred']
        assert len(old_template2pred_words) == len(rerank_template2pred_words)
        template_num = len(old_template2pred_words)
        for j in range(template_num):
            old_pred_words = old_template2pred_words[j]
            rerank_pred_words = rerank_template2pred_words[j]
            if exact_match(tgt_words, old_pred_words) and not exact_match(tgt_words, rerank_pred_words):
                print("Bad case")
                print("Src_word:")
                print(old_record['src_word'])
                print("Filtered wrong tgt_words:")
                print(tgt_words)
                print("-" * 6)
            elif exact_match(tgt_words, old_pred_words) and exact_match(tgt_words, rerank_pred_words) \
                    and ahead(tgt_words, old_pred_words, rerank_pred_words):
                print("Good case")
                print("Src_word:")
                print(old_record['src_word'])
                print("Tgt_words:")
                print(tgt_words)
                print("#" * 6)


def exact_match(tgt_words, pred_words):
    for tgt_word in tgt_words:
        if tgt_word in pred_words:
            return True
    return False


def ahead(tgt_words, old_pred_words, rerank_pred_words):
    old_rank = len(old_pred_words)
    for i, old_pred_word in enumerate(old_pred_words):
        if old_pred_word in tgt_words:
            old_rank = i
            break
    new_rank = len(rerank_pred_words)
    for i, rerank_pred_word in enumerate(rerank_pred_words):
        if rerank_pred_word in tgt_words:
            new_rank = i
            break
    if new_rank < old_rank:
        print("old_rank is {}, new_rank is {}".format(str(old_rank), str(new_rank)))
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerank_dir', required=True)
    parser.add_argument('--record_dir',
                        default='/data/tsq/xlink/bd/purify/filter_english/pool_80/result/abbreviation/few_shot/task_specific/time_12140900')
    # record type is different for those re-scored record
    parser.add_argument('--record_type', type=str, default='records', choices=['records', 'rescore'],
                        help="type of record.pkl")

    args = parser.parse_args()
    if args.record_type == 'records':
        origin_record_path = os.path.join(args.record_dir, '{}.pkl'.format(args.record_type))
        rerank_record_path = os.path.join(args.rerank_dir, '{}.pkl'.format(args.record_type))
    else:
        origin_record_path = os.path.join(args.record_dir, '{}.pkl'.format(args.score_kind))
        rerank_record_path = os.path.join(args.rerank_dir, '{}.pkl'.format(args.score_kind))
    # load
    with open(origin_record_path, 'rb') as fin1:
        with open(rerank_record_path, 'rb') as fin2:
            old_records = pickle.load(fin1)
            rerank_records = pickle.load(fin2)
            assert len(old_records) == len(rerank_records)
            data_num = len(old_records)
            observe_cases(args, data_num, old_records, rerank_records)


if __name__ == '__main__':
    main()
