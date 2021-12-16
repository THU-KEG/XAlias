import argparse
import os
import pickle
import random
from tqdm import tqdm
from src.data.load import AliasDataset
import bminf
import time
import cupy
from typing import List, Tuple
from src.data.discover_alias import HasAlias
from src.data.extra_info import InfoBox
import numpy as np
from demo.params import add_decode_param, reduce_args, add_test_param

SPAN_TOKEN = "<span>"


class Perplexity(object):
    def __init__(self, tokens, logits, token_probs):
        self.tokens = tokens
        self.logits = logits
        self.token_probs = token_probs

    @property
    def ppl(self):
        score = 1
        for token_prob in self.token_probs:
            score *= token_prob
        return score


class ScoreVector(object):
    def __init__(self, logits: List, ppls: List, attributes: List, patterns: List):
        self.last_token_logits = logits
        self.ppls = ppls
        # In fact we store either logit or ppl
        self.attributes = attributes
        self.patterns = patterns


class Scorer(object):
    def __init__(self, model, args, id2info_box):
        self.model = model
        self.args = args
        self.id2info_box = id2info_box

    def rescore(self, old_record, ent_id):
        score_vector_dict = {'src': None, 'pred': [], 'max_attribute_num': self.args.max_attribute_num}
        src_word = old_record['src_word']
        pred_words = old_record['pred'][:self.args.candidate_num]

        if self.args.score_kind == 'ppl':
            # concat attribute with src and pred to compare their similarity
            src_score = self.calc(src_word, ent_id)
            score_vector_dict['src'] = src_score
            for pred_word in tqdm(pred_words, total=len(pred_words)):
                pred_score = self.calc(pred_word, ent_id)
                score_vector_dict['pred'].append(pred_score)
        return score_vector_dict

    def calc(self, word, ent_id):
        info_box = self.id2info_box[ent_id]
        attribute_dict = info_box.attribute_dict
        # fill pattern and sample some attributes
        pattern = ''
        max_attribute_num = min(len(attribute_dict), self.args.max_attribute_num)
        _keys = random.choices(list(attribute_dict), k=max_attribute_num)
        sv = ScoreVector([], [], _keys, [])
        if self.args.concat_way == 'string':
            # use concat string pattern to calculate score
            for i, key in enumerate(_keys):
                if 0 < i < max_attribute_num - 1:
                    # comma  (be different for english !!)
                    pattern += '，'
                if self.args.attribute_value == 'use':
                    value = attribute_dict[key]
                    part_pattern = '{}的{}是{}'.format(word, key, value)
                    pattern += part_pattern
                else:
                    # We can not ignore the attribute value and simultaneously concat them
                    raise ValueError()
            ppl_score = self.get_ppl(pattern)
            sv.ppls.append(ppl_score)
            sv.patterns.append(pattern)
        else:
            # use distributed scores
            for key in _keys:
                if self.args.attribute_value == 'use':
                    value = attribute_dict[key]
                    _pattern = '{}的{}是{}'.format(word, key, value)
                    ppl_score = self.get_ppl(_pattern)
                    sv.ppls.append(ppl_score)
                else:
                    _pattern = '{}的{}是'.format(word, key)
                    last_token_logits = self.get_ppl(_pattern, return_last_token_logits=True)
                    sv.last_token_logits.append(last_token_logits)
                    ppl_pattern = '{}的{}'.format(word, key)
                    sv.ppls.append(self.get_ppl(ppl_pattern))
                sv.patterns.append(_pattern)
        return sv

    def get_ppl(self, input_sentence, return_last_token_logits=False):
        # <eod> must be in the set of stop words.
        if return_last_token_logits:
            ctx, sampler, _ = self.model.pre_processing(
                input_sentence + SPAN_TOKEN, [len(input_sentence)],
                self.args.max_tokens, self.args.top_n, self.args.top_p, self.args.temperature,
                self.args.frequency_penalty, self.args.presence_penalty, 189
            )
            _logits = self.model.decode_step(ctx, [self.model.tokenizer.sod_id])[0]
            logits = self.model.decode_step(ctx, [self.model.tokenizer.get_span(189)])[0]
            # softmax
            logits -= logits.max()
            logits = cupy.exp(logits)
            logits /= logits.sum()
            cpu_probs = cupy.asnumpy(logits).astype(np.float32)
            return cpu_probs
        else:
            ppl = Perplexity([], [], [])
            tokens = self.model.text_to_id(input_sentence)
            token_num = len(tokens)
            # auto-regressive decoding
            for i in range(token_num):
                # given i-1 tokens, predict token i
                prefix_tokens = tokens[:i]
                sequence = self.model.id_to_text(prefix_tokens)
                logits = self.get_ppl(sequence, return_last_token_logits=True)
                print(logits)
                idx = tokens[i]
                token_porb = logits[idx]
                print(token_porb)
                # record them
                ppl.tokens.append(tokens[i])
                ppl.logits.append(logits)
                ppl.token_probs.append(token_porb)
            return ppl


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
        for batch_iter, batch in tqdm(enumerate(data.gen_batch(required_index=True)), desc="Scoring",
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
            score_vector_dict = scorer.rescore(old_record, ent_id)
            # save in tuple
            record_with_score_list.append((old_record, score_vector_dict))
    except RuntimeError:
        # stop iteration raised by data
        pass
    return record_with_score_list


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--record_dir', required=True)
    parser.add_argument('--record_dir',
                        default='/data/tsq/xlink/bd/purify/filter_english/pool_80/result/synonym/few_shot/task_specific/time_12140900')
    parser.add_argument('--candidate_num', type=int, default=20)
    # ppl score
    parser.add_argument('--score_kind', type=str, default='ppl', help="the kind of score")
    parser.add_argument('--max_attribute_num', type=int, default=2)
    # info box
    parser.add_argument('--concat_way', type=str, default='distributed', choices=['distributed', 'string'],
                        help="how to concat different attribute")
    parser.add_argument('--attribute_value', type=str, default='use', choices=['use', 'ignore'],
                        help="how to concat different attribute")
    parser.add_argument('--info_box_path', type=str, default='/data/tsq/xlink/bd/id2info_box.pkl')
    parser = add_decode_param(parser)
    parser = add_test_param(parser)
    args = parser.parse_args()
    # records will be used for calculating ppl score
    record_json_path = os.path.join(args.record_dir, 'records.pkl')
    with open(record_json_path, 'rb') as fin:
        records = pickle.load(fin)
        log_dir = os.path.join(args.record_dir, 'score', "time_" + time.strftime("%m%d%H%M"))
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
        result_path = os.path.join(log_dir, '{}.pkl'.format(args.score_kind))
        with open(os.path.join(log_dir, 'args.txt'), 'w', encoding='utf-8') as f:
            for k, v in args.__dict__.items():
                f.write('%s: %s\n' % (k, str(v)))
        with open(result_path, 'wb') as fout:
            pickle.dump(record_with_score_list, fout)
            print("[2]Save {}".format(result_path))


if __name__ == '__main__':
    main()
