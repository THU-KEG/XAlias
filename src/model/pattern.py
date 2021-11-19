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
                'synonym': ['也被称为', '的别名是', '的同义词是', ',也称'],
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
                    # sample
                    for i in range(self.args.num_return_sequences):
                        np.random.seed(i * self.args.seed)
                        strings.append(self.cpm2_sample(input_text))
                pattern2strings.append(strings)

        return pattern2strings
