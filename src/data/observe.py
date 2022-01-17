import argparse
import os
import pickle
import xlwt
import xlrd
from xlutils.copy import copy
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
                print("old_rank is", get_old_rank(tgt_words, old_pred_words))
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


def get_old_rank(tgt_words, old_pred_words):
    for i, old_pred_word in enumerate(old_pred_words):
        if old_pred_word in tgt_words:
            return i
    return len(tgt_words) - 1


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


def save_xls(args, data_num, records, record_dir):
    xls_name = record_dir.split('/')[-1]
    xls_path = os.path.join(args.save_dir, '{}.xls'.format(xls_name))
    workbook = xlwt.Workbook(encoding='utf-8')
    for i in range(data_num):
        if args.record_type == 'rescore':
            record, score_vector_dict = records[i]
        else:
            record = records[i]
        # load
        tgt_words = record['tgt']
        template2pred_words = record['pred']
        template_num = len(template2pred_words)
        # write the src and golden names
        worksheet = workbook.add_sheet('Iter_{}'.format(str(record['iter'])))
        worksheet.write(0, 0, label="src_word")
        worksheet.write(1, 0, label=record['src_word'])
        worksheet.write(0, 1, label="golden_alias")
        worksheet.write(0, 3, label="validity guess")
        for k, golden_alias in enumerate(tgt_words):
            worksheet.write(k + 1, 1, label=golden_alias)
        # write the predict result
        worksheet.write(0, 2, label="pred_alias")
        row_id = 1
        for j in range(template_num):
            pred_words = template2pred_words[j]
            for pred_word in pred_words:
                worksheet.write(row_id, 2, label=pred_word)
                row_id += 1
    workbook.save(xls_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerank_dir', required=True)
    parser.add_argument('--record_dir',
                        default='/data/tsq/xlink/bd/purify/filter_english/pool_80/result/abbreviation/few_shot/task_specific/time_12140900')
    # record type is different for those re-scored record
    parser.add_argument('--record_type', type=str, default='records', choices=['records', 'rescore'],
                        help="type of record.pkl")
    # whether to save as xls for human annotation
    parser.add_argument('--save_dir', type=str, default='/home/tsq/ybb/data/human',
                        help="type of saved file")
    parser.add_argument('--save_file', type=str, default='None', choices=['None', 'xls'],
                        help="type of saved file")

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
            if args.save_file == 'None':
                observe_cases(args, data_num, old_records, rerank_records)
            elif args.save_file == 'xls':
                save_xls(args, data_num, old_records, args.record_dir)
                save_xls(args, data_num, rerank_records, args.rerank_dir)


if __name__ == '__main__':
    main()
