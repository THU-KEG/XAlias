import bminf
import sys
import numpy as np
from demo.params import get_bminf_param
from src.pattern import Verbalizer

TOKEN_SPAN = "<span>"


def fill_blank(cpm2: bminf.models.CPM2, text, kwargs: dict):
    print("Input: ", text.replace(TOKEN_SPAN, "\033[4m____\033[0m"))
    for result in cpm2.fill_blank(text, **kwargs
                                  # top_p=1.0,
                                  # top_n=5,
                                  # temperature=0.5,
                                  # frequency_penalty=0,
                                  # presence_penalty=0
                                  ):
        value = result["text"]
        text = text.replace(TOKEN_SPAN, "\033[0;32m" + value + "\033[0m", 1)
    print("Output:", text)


def generate(model: bminf.models.CPM2, text, kwargs: dict):
    print("Input: ", text)
    sys.stdout.write("Output: %s" % text)
    stoped = False
    total_len = len(text)
    while not stoped:
        if total_len > kwargs['max_tokens']:
            break
        value, stoped = model.generate(
            text, **kwargs
            # max_tokens=32,
            # top_n=5,
            # top_p=None,
            # temperature=0.85,
            # frequency_penalty=0,
            # presence_penalty=0,
        )
        text += value
        sys.stdout.write(value)
        total_len += len(value)
        sys.stdout.flush()
    sys.stdout.write("\n")


def get_input_texts(args):
    verbalizer = Verbalizer(args.language, args.task)
    return verbalizer.convert_all(args.source_word)


def main():
    print("Loading model")
    args, kwargs = get_bminf_param()
    input_texts = get_input_texts(args)
    np.random.seed(args.seed)
    cpm2_1 = bminf.models.CPM2(device=args.gpu_id)
    print("kwargs:", kwargs)
    for input_text in input_texts:
        if args.task == 'fill':
            fill_blank(cpm2_1, input_text, kwargs)
        else:
            generate(cpm2_1, input_text, kwargs)


if __name__ == "__main__":
    main()

""" results of default parameters in gpt2 style:
Input:  清华大学也被称为
Output: 清华大学也被称为“世界最美的人”。
Input:  北京大学也被称为
Output: 北京大学也被称为中国的“巴黎”，是法国的一个城市。
Input:  清华大学也被称为清
Output: 清华大学也被称为清华大学，也叫“清华大学”。
Input:  北京大学也称
Output: 北京大学也称为“最美”
"""

""" results of default parameters in Bert style:
Input:  清华大学也被称为____
Output: 清华大学也被称为“中国的夏威夷”。
Input:  北京大学也被称为____
Output: 北京大学也被称为“中国的迪士尼”
Input:  清华大学也被称为清____
Output: 清华大学也被称为清晨的雾气。
Input:  北京大学也称____
Output: 北京大学也称“我”。
"""
