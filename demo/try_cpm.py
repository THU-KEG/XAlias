from transformers import TextGenerationPipeline, AutoTokenizer, AutoModelWithLMHead
from demo.params import get_decode_param

TEXT = '清华大学也被称为'


def work(decode_args):
    tokenizer = AutoTokenizer.from_pretrained("TsinghuaAI/CPM-Generate")
    model = AutoModelWithLMHead.from_pretrained("TsinghuaAI/CPM-Generate")
    text_generator = TextGenerationPipeline(model, tokenizer)
    res = text_generator(TEXT, **vars(decode_args))
    topk = [dic['generated_text'] for dic in res]
    print(topk)


"""  Namespace(diversity_penalty=1.0, early_stopping=False, length_penalty=1.0, no_repeat_ngram_size=3, num_beam_groups=4, num_beams=4, num_return_sequences=4)
TEXT = '清华大学也被称为'
topk = ['清华大学也被称为“大学”。 ', '清华大学也被称为是“大学”。 ', '清华大学也被称为“中国的‘老’', '清华大学也被称为“大学”,是']
TEXT = '清华大学也被称为清'
topk = ['清华大学也被称为清朝的“府”,', '清华大学也被称为清华北大。  我想说的是,', '清华大学也被称为清华北大,但是,“清华北大是中国的', '清华大学也被称为清史第一城,是不是有点过了? ']
"""

"""Namespace(do_sample=True, num_return_sequences=4, s='sample', top_k=20, top_p=0.95)
TEXT = '清华大学也被称为'
topk = ['清华大学也被称为“清华狗”,被网友黑,我也', '清华大学也被称为“老清,不,是老”', '清华大学也被称为“中国节”。 【', '清华大学也被称为“枫叶之城”,“']
TEXT = '清华大学也被称为清'
topk = ['清华大学也被称为清朝“八旗精神”,“八旗', '清华大学也被称为清华北大。我只是觉得“清华北大”这', '清华大学也被称为清代大学。 [4] 罗', '清华大学也被称为清廷“文化院”。 [']
"""

if __name__ == '__main__':
    decode_args = get_decode_param()
    print("decode_args: ")
    print(decode_args)
    work(decode_args)
