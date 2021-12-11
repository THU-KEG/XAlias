import argparse
import bminf
import numpy as np
from src.model.decode import beam_search, Beam, generate_return_beam
from difflib import SequenceMatcher
from src.model.const import patterns, few_shot_alias_table
from collections import Counter
from typing import List, Tuple

signal_arg_keys = ['max_tokens_scale', 'top_n_range']


def strip_redundant_words(words, max_overlap_scale: float):
    if max_overlap_scale == 1:
        # print("[2]max_overlap_scale is 1")
        chosen_words = list(set(words))
    else:
        chosen_words = []
        for word in words:
            flag = False
            for prev_word in chosen_words:
                s = SequenceMatcher(None, word, prev_word)
                overlap = s.find_longest_match(0, len(word), 0, len(prev_word)).size

                if overlap * max_overlap_scale >= min(len(word), len(prev_word)):
                    flag = True
                    break

            if not flag:
                chosen_words.append(word)

    return chosen_words


class Verbalizer(object):
    def __init__(self, language, task):
        """
        :param language: en / ch
        :param task: 'fill' / 'generate'
        """
        self.language = language
        self.task = task
        self.patterns = patterns[language][task]
        self.g_patterns = patterns[language]['generate']
        # cpm2 param
        self.model = None
        self.kwargs = None
        self.args = None
        self.signal_args = {}

    def convert_all(self, prefix_type, src_word, task_def=False, alias_table=None):
        if alias_table is None:
            alias_table = few_shot_alias_table[prefix_type]
        results = []
        for p_id in range(len(self.patterns[prefix_type])):
            prefix = ''
            if task_def:
                if self.language == 'ch':
                    prefix += '接下来进行别名生成，比如'
                else:
                    prefix += 'Next we will generate alias. Such as'
            if prefix_type != 'void':
                for key_word, alias_list in alias_table.items():
                    for alias in alias_list:
                        if self.language == 'ch':
                            prefix += key_word + self.g_patterns[prefix_type][p_id] + alias + '，'
                        else:
                            prefix += key_word + self.g_patterns[prefix_type][p_id] + alias + ', '
            sequence = self.convert(prefix, prefix_type, src_word, p_id)
            results.append(sequence)
        return results

    def convert(self, prefix, prefix_type, src_word, pattern_id=0):
        pattern = self.patterns[prefix_type][pattern_id]
        return prefix + src_word + pattern

    def set_cpm2(self, model: bminf.models.CPM2, kwargs: dict, args: argparse.ArgumentParser):
        self.model = model
        self.kwargs = kwargs
        self.args = args
        for k in signal_arg_keys:
            v = args.__dict__[k]
            # if k == 'alias_table_num':
            #     # default is 1, when > 1 , it provides us extra results by changing alias table
            #     if v > 1:
            #         self.signal_args[k] = v
            # else:
            # default is None
            if v is not None:
                self.signal_args[k] = v

    def set_for_rerank(self, args: argparse.ArgumentParser):
        self.args = args

    def cpm2_beam_search(self, text):
        result_strings = beam_search(self.model, text, **self.kwargs)
        return result_strings

    def cpm2_sample(self, text) -> Beam:
        stoped = False
        total_len = 0
        result_beam = None
        while not stoped:
            if total_len > self.kwargs['max_tokens']:
                break
            value, stoped = generate_return_beam(
                self.model,
                self.args.calculate_prob,
                text, **self.kwargs
            )
            value_string = value.tokens
            if result_beam:
                # merge the 2 beams
                result_beam.tokens += value_string
                result_beam.log_probs += value.log_probs
            else:
                result_beam = value
            total_len += len(value_string)
            if self.args.cpm2_concat_value_string == 'concat':
                text += value_string

        return result_beam

    def pattern_num(self, prefix_type):
        return len(self.g_patterns[prefix_type])

    def cpm2_gen_by_prompt(self, prefix_type, src_word, task_def, alias_tables=None) \
            -> Tuple[List[List[str]], List[List]]:
        pattern2beams = [[] for _ in range(self.pattern_num(prefix_type))]
        for alias_table in alias_tables:
            input_texts = self.convert_all(prefix_type, src_word, task_def, alias_table)
            for pattern_id, input_text in enumerate(input_texts):
                if self.args.task == 'fill':
                    # fill_blank(model, input_text, kwargs)
                    return [['']], [[]]
                else:
                    beams = []
                    if 'num_beams' in self.kwargs.keys():
                        # beam search
                        beams = self.cpm2_beam_search(input_text)
                    else:
                        # sample with different params
                        passes = self.args.num_generate_sequences // (len(self.signal_args) * len(alias_tables))
                        rotation_num = 1 + passes
                        for i in range(rotation_num):
                            if len(beams) >= self.args.num_generate_sequences:
                                break
                            np.random.seed(i * self.args.seed)
                            if len(self.signal_args) > 0:
                                # change args
                                for signal_arg in self.signal_args:
                                    if signal_arg == 'max_tokens_scale':
                                        l_sw = len(src_word)
                                        if i % 3 == 0:
                                            self.kwargs['max_tokens'] = int(l_sw * self.signal_args['max_tokens_scale'])
                                        elif i % 3 == 1:
                                            self.kwargs['max_tokens'] = l_sw
                                        else:
                                            self.kwargs['max_tokens'] = int(l_sw / self.signal_args['max_tokens_scale'])
                                    elif signal_arg == 'top_n_range':
                                        tnr_order = i % (2 * self.signal_args['top_n_range'])
                                        self.kwargs['top_n'] = self.args.top_n - self.signal_args[
                                            'top_n_range'] + tnr_order
                                    # generate with new kwargs
                                    new_beam = self.cpm2_sample(input_text)
                                    beams.append(new_beam)
                            else:
                                # only change seed
                                beams.append(self.cpm2_sample(input_text))
                    pattern2beams[pattern_id].extend(beams)
        # process and truncate
        final_pattern2strings = []
        for beams in pattern2beams:
            pure_strings = self.process(beams)
            final_pattern2strings.append(pure_strings[:self.args.num_return_sequences])
        return final_pattern2strings, pattern2beams

    def process(self, beams: List[Beam]) -> List[str]:
        # default strategy is None
        # print("[0] enter process", strings)
        if self.args.punctuation_strategy:
            beams = self.rm_punctuation(beams)
        if self.args.rank_strategy != 'random':
            strings = self.rank(beams)
        else:
            # don't need rank
            if self.args.redundancy_strategy:
                # print("[1] Before rm_redundancy", strings)
                strings = self.rm_redundancy(beams)
                # print("[3] After rm_redundancy", strings)
            # print("[4] out process", strings)
            else:
                strings = [b.tokens for b in beams]
        return strings

    def rm_punctuation(self, beams: List[Beam]) -> List[Beam]:
        tidy_beams = []
        stopped_chars = "！？，｡、＂＇（）：；\n"
        if self.args.punctuation_strategy == 'lazy':
            # only split the ， 。 \n
            separated_chars = '，。\n'
        else:
            separated_chars = stopped_chars
        for beam in beams:
            string = beam.tokens
            striped = string.strip(stopped_chars)
            tidy_beams.append(Beam(striped, beam.log_probs, beam.context))
            for separated_char in separated_chars:
                if separated_char in striped:
                    sp_words = striped.split(separated_char)
                    # new beam will success the prob
                    new_beams = [Beam(word, beam.log_probs, beam.context) for word in sp_words]
                    tidy_beams.extend(new_beams)
        return tidy_beams

    def rm_redundancy(self, beams: List[Beam]) -> List[str]:
        tidy_strings = []
        strings = [b.tokens for b in beams]
        if self.args.redundancy_strategy == 'overlap':
            tidy_strings = strip_redundant_words(strings, self.args.max_overlap_scale)
        return tidy_strings

    def rank(self, beams: List[Beam]) -> List[str]:
        ranked_strings = []
        strings = [b.tokens for b in beams]
        if self.args.rank_strategy == 'frequency':
            # sort by frequency of words
            counter = Counter(strings)
            ranked_string_tuples = counter.most_common(self.args.num_return_sequences)
            ranked_strings = [t[0] for t in ranked_string_tuples]
        elif self.args.rank_strategy == 'probability':
            # sort by average probability of token
            _beams = []
            str2beam_index = set()
            for beam in beams:
                string = beam.tokens
                if string not in str2beam_index:
                    # new string
                    _beams.append(beam)
                    str2beam_index.add(string)
            # However, different beams with same tokens may have different probs due to their succession
            _beams.sort(key=lambda b: b.avg_log_prob, reverse=True)
            ranked_strings = [b.tokens for b in _beams]
        elif self.args.rank_strategy == 'prob_freq':
            # sort by weighted frequency
            # weight is average probability of token
            freq_beams = []
            str2beam_index = {}
            for beam in beams:
                string = beam.tokens
                try:
                    beam_index = str2beam_index[string]
                    freq_beams[beam_index].set_freq()
                except KeyError:
                    # new string
                    str2beam_index[string] = len(freq_beams)
                    beam.set_freq(init=True)
                    freq_beams.append(beam)
            freq_beams.sort(key=lambda b: b.log_freq_add_prob, reverse=True)
            ranked_strings = [b.tokens for b in freq_beams]
        return ranked_strings

    def rerank(self, pattern2beams):
        # process and truncate
        final_pattern2strings = []
        for beams in pattern2beams:
            pure_strings = self.process(beams)
            final_pattern2strings.append(pure_strings[:self.args.num_return_sequences])
        return final_pattern2strings


"""
    def cpm2_sample(self, text):
        stoped = False
        total_len = 0
        result_string = ""
        while not stoped:
            if total_len > self.kwargs['max_tokens']:
                break
            value, stoped = self.model.generate(
                text, **self.kwargs
            )
            result_string += value
            total_len += len(value)

        return result_string
    

"""
