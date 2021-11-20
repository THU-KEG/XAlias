import argparse
import bminf
import numpy as np
from src.model.decode import beam_search

patterns = {
    'ch': {
        'fill': ['也被称为<span>。', '的别名是<span>。', '的缩写为<span>。', ',简称<span>。', '也作为<span>被熟知。'],
        'generate':
            {
                'prefix': ['也被称为', '的别名是', '又名', '即', '的全名是', '简称'],  # List of templates
                'suffix': ['也被称为', '的别名是', '的缩写为', ',简称'],
                'abbreviation': ['也被称为', '的别名是', '的缩写为', ',简称'],
                # 'synonym': ['也被称为', '的别名是', '的同义词是', ',也称'],
                'synonym': ['也被称为', '的别名是', '的同义词是', '，也称', '，又叫', '，即'],
                'punctuation': ['也被称为', '的别名是', ',简称', '，简称', '简称'],
                'bilingual': ['也被称为', '的别名是', '的译文是', ',也称'],
                'multiple': ['也被称为', '的别名是', '的缩写为', ',也称'],
            }
    }

}
few_shot_alias_table = {
    'abbreviation': {'清华大学': ['清华'], '北京理工大学': ['北理', '北理工']},
    'synonym': {'红酒': ['葡萄酒']},
    'void': {},
}

signal_arg_keys = ['max_tokens_scale', 'top_n_range']


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
                    for i in range(self.args.num_return_sequences // len(self.signal_args) + 1):
                        if len(strings) >= self.args.num_return_sequences:
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
                pattern2strings.append(strings)

        return pattern2strings
