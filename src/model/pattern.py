import argparse
import bminf
import numpy as np
from src.model.decode import beam_search
from difflib import SequenceMatcher
from src.model.const import patterns, few_shot_alias_table

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
            if v is not None:
                self.signal_args[k] = v

    def cpm2_beam_search(self, text):
        result_strings = beam_search(self.model, text, **self.kwargs)
        return result_strings

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

    def cpm2_gen_by_prompt(self, prefix_type, src_word, task_def, alias_table=None):
        input_texts = self.convert_all(prefix_type, src_word, task_def, alias_table)
        pattern2strings = []
        for input_text in input_texts:
            if self.args.task == 'fill':
                # fill_blank(model, input_text, kwargs)
                return None
            else:
                strings = []
                if 'num_beams' in self.kwargs.keys():
                    # beam search
                    strings = self.cpm2_beam_search(input_text)
                else:
                    # sample with different params
                    for i in range(self.args.num_generate_sequences // len(self.signal_args) + 1):
                        if len(strings) >= self.args.num_generate_sequences:
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
                                    self.kwargs['top_n'] = self.args.top_n - self.signal_args['top_n_range'] + tnr_order
                                # generate with new kwargs
                                strings.append(self.cpm2_sample(input_text))
                        else:
                            # only change seed
                            strings.append(self.cpm2_sample(input_text))
                processed_strings = self.process(strings)
                pattern2strings.append(processed_strings[:self.args.num_return_sequences])

        return pattern2strings

    def process(self, strings):
        # default strategy is None
        # print("[0] enter process", strings)
        if self.args.punctuation_strategy:
            strings = self.rm_punctuation(strings)
        if self.args.redundancy_strategy:
            # print("[1] Before rm_redundancy", strings)
            strings = self.rm_redundancy(strings)
            # print("[3] After rm_redundancy", strings)
        # print("[4] out process", strings)
        return strings

    def rm_punctuation(self, strings):
        tidy_strings = []
        stopped_chars = "！？，｡、＂＇（）：；\n"
        if self.args.punctuation_strategy == 'lazy':
            # only split the ， 。 \n
            separated_chars = '，。\n'
        else:
            separated_chars = stopped_chars
        for string in strings:
            striped = string.strip(stopped_chars)
            tidy_strings.append(striped)
            for separated_char in separated_chars:
                if separated_char in striped:
                    sp_words = striped.split(separated_char)
                    tidy_strings.extend(sp_words)
        return tidy_strings

    def rm_redundancy(self, strings):
        tidy_strings = []
        if self.args.redundancy_strategy == 'overlap':
            tidy_strings = strip_redundant_words(strings, self.args.max_overlap_scale)
        return tidy_strings
