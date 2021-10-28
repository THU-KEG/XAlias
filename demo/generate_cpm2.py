import bminf
import sys
import argparse

input_text = """天空是蔚蓝色，窗外有"""

TOKEN_SPAN = "<span>"

input_1 = "北京环球度假区相关负责人介绍，北京环球影城指定单日门票将采用<span>制度，即推出淡季日、平季日、旺季日和特定日门票。<span>价格为418元，<span>价格为528元，<span>价格为638元，<span>价格为<span>元。北京环球度假区将提供90天滚动价格日历，以方便游客提前规划行程。"


def fill_blank(cpm2: bminf.models.CPM2, text):
    print("Input: ", text.replace(TOKEN_SPAN, "\033[4m____\033[0m"))
    for result in cpm2.fill_blank(text,
                                  top_p=1.0,
                                  top_n=5,
                                  temperature=0.5,
                                  frequency_penalty=0,
                                  presence_penalty=0
                                  ):
        value = result["text"]
        text = text.replace(TOKEN_SPAN, "\033[0;32m" + value + "\033[0m", 1)
    print("Output:", text)


def generate(model: bminf.models.CPM2, text):
    print("Input: ", text)
    sys.stdout.write("Output: %s" % text)
    stoped = False
    while not stoped:
        value, stoped = model.generate(
            input_sentence=text[-32:],
            max_tokens=32,
            top_n=5,
            top_p=None,
            temperature=0.85,
            frequency_penalty=0,
            presence_penalty=0,
        )
        text += value
        sys.stdout.write(value)
        sys.stdout.flush()
    sys.stdout.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', type=str, default='fill', choices=['fill', 'generate'])
    args = parser.parse_args()
    print("Loading model")
    # cpm2_1 = bminf.models.CPM2(device=1, memory_limit=6019 * 1024 * 1024)
    cpm2_1 = bminf.models.CPM2()
    if args.task == 'fill':
        fill_blank(cpm2_1, input_1)
    else:
        generate(cpm2_1, input_text)


if __name__ == "__main__":
    main()
