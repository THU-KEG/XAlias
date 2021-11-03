patterns = {
    'ch': {
        'fill': ['也被称为<span>。', '的别名是<span>。', '的缩写为<span>。', ',简称<span>。', '也作为<span>被熟知。'],
        'generate': ['也被称为', '的别名是', '的缩写为', ',简称']
    }

}


class Verbalizer():
    def __init__(self, language, task):
        """
        :param language: en / ch
        :param task: 'fill' / 'generate'
        """
        self.language = language
        self.task = task
        self.patterns = patterns[language][task]

    def convert_all(self, prefix):
        results = [self.convert(prefix, p_id) for p_id in range(len(self.patterns))]
        return results

    def convert(self, prefix, pattern_id=0):
        pattern = self.patterns[pattern_id]
        return prefix + pattern
