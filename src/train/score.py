import argparse
import os
import pickle
import random
from tqdm import tqdm
from src.data.load import AliasDataset
import bminf
from src.data.discover_alias import HasAlias
from src.data.extra_info import InfoBox
import numpy as np
from src.model.pattern import Verbalizer
from src.train.test import init_log_sub_dirs, record_result, save_test_result
from demo.params import add_decode_param, reduce_args, add_test_param


class ReScore(object):
    def __init__(self, logit, score):
        self.logit = logit
        self.score = score


class Scorer(object):
    def __init__(self, model, args, id2info_box):
        self.model = model
        self.args = args
        self.id2info_box = id2info_box

    def rescore(self, old_record, ent_id):
        r_score_dict = {'src': None, 'pred': [], 'max_attribute_num': self.args.max_attribute_num}
        src_word = old_record['src_word']
        pred_words = old_record['pred'][:self.args.candidate_num]

        if self.args.score_kind == 'ppl':
            # concat attribute with src and pred to compare their similarity
            src_score = self.calc(src_word, ent_id)
            r_score_dict['src'] = src_score
            for pred_word in pred_words:
                pred_score = self.calc(pred_word, ent_id)
                r_score_dict['pred'].append(pred_score)
        return r_score_dict

    def calc(self, word, ent_id):
        info_box = self.id2info_box[ent_id]
        attribute_dict = info_box.attribute_dict
        # fill pattern
        pattern = ''
        max_attribute_num = min(len(attribute_dict), self.args.max_attribute_num)
        _keys = random.choices(list(attribute_dict), k=max_attribute_num)
        for i, key in enumerate(_keys):
            if 0 < i < max_attribute_num - 1:
                # comma TODO (be different for english !!)
                pattern += '，'
            value = attribute_dict[key]
            _pattern = '{}的{}是{}'.format(word, key, value)
        pattern += '。'
        # use pattern to calculate score
        return ReScore(None, None)


def score_all(old_records, args, model):
    if args.test:
        data = AliasDataset(args.data_path, args.alias_type, 'test', exp_num=args.example_num)
    else:
        data = AliasDataset(args.data_path, args.alias_type, 'valid', exp_num=args.example_num)
    record_with_score_list = []
    with open(args.info_box_path, 'rb') as fin:
        id2info_box = pickle.load(fin)
    scorer = Scorer(model, args, id2info_box)
    try:
        for batch_iter, batch in tqdm(enumerate(data.gen_batch(required_index=True)), desc="Ranking",
                                      total=len(old_records)):
            if args.fast and batch_iter % 10 != 0:
                continue
            ent_id, src_word, _ = batch
            # fast or not
            if args.fast:
                idx = batch_iter // 10
            else:
                idx = batch_iter
            old_record = old_records[idx]
            assert src_word == old_record['src_word']
            # re-score here
            r_score_dict = scorer.rescore(old_record, ent_id)
            # save in tuple
            record_with_score_list.append((old_record, r_score_dict))
    except RuntimeError:
        # stop iteration raised by data
        pass
    return record_with_score_list


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record_dir', required=True)
    parser.add_argument('--candidate_num', type=int, default=20)
    # ppl score
    parser.add_argument('--score_kind', type=str, default='ppl', help="the kind of score")
    parser.add_argument('--score_calc', type=str, default='logit', choices=['logit', 'num'], help="how to calc score")
    parser.add_argument('--max_attribute_num', type=int, default=2)
    # info box
    parser.add_argument('--info_box_path', type=str, default='/data/tsq/xlink/bd/id2info_box.pkl')
    parser = add_decode_param(parser)
    parser = add_test_param(parser)
    args = parser.parse_args()
    # records will be used for calculating ppl score
    record_json_path = os.path.join(args.record_dir, 'records.pkl')
    with open(record_json_path, 'rb') as fin:
        records = pickle.load(fin)
        log_dir = os.path.join(args.record_dir, 'score')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        print("[1]Start scoring")
        if args.language == 'ch':
            np.random.seed(args.seed)
            random.seed(args.seed)
            model = bminf.models.CPM2(device=args.gpu_id)
        else:
            # hugging face
            model = None
        record_with_score_list = score_all(records, args, model)
        # save
        result_path = os.path.join(args.record_dir, '{}.pkl'.format(args.score_kind))
        with open(result_path, 'wb') as fout:
            pickle.dump(record_with_score_list, fout)
            print("[2]Save {}".format(result_path))
