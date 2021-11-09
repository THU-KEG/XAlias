patterns = {
    'ch': {
        'fill': ['也被称为<span>。', '的别名是<span>。', '的缩写为<span>。', ',简称<span>。', '也作为<span>被熟知。'],
        'generate': ['也被称为', '的别名是', '的缩写为', ',简称']
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

    def convert_all(self, prefix_type, src_word):
        alias_table = few_shot_alias_table[prefix_type]
        results = []
        for p_id in range(len(self.patterns)):
            prefix = ''
            if prefix_type != 'void':
                for key_word, alias_list in alias_table.items():
                    for alias in alias_list:
                        if self.language == 'ch':
                            prefix += key_word + self.g_patterns[p_id] + alias + '，'
                        else:
                            prefix += key_word + self.g_patterns[p_id] + alias + ', '
            sequence = self.convert(prefix, src_word, p_id)
            results.append(sequence)
        return results

    def convert(self, prefix, src_word, pattern_id=0):
        pattern = self.patterns[pattern_id]
        return prefix + src_word + pattern
