import seaborn as sns
import pandas as pd
import argparse
import os
import json
import matplotlib.pyplot as plt

context_windows = [100, 1000, 10000]


def get_alias_hits(args):
    hits = []
    # get xlink result
    xlink_dir = os.path.join(args.duel_dir, 'xlink')
    for context_window in context_windows:
        score_dir = os.path.join(xlink_dir, f"{context_window}ctx")
        input_path = os.path.join(score_dir, "xlink_score.json")
        xlink_score = json.load(open(input_path, 'r'))
        hits.append(xlink_score["hits"][f'hits@{args.hits - 1}'])

    # get coref result
    coref_dir = os.path.join(args.duel_dir, 'coref')
    for context_window in context_windows:
        score_dir = os.path.join(coref_dir, f"ctx{context_window}", 'bd')
        input_path = os.path.join(score_dir, f"sample_entity_fill_{context_window}tokens_score.json")
        coref_score = json.load(open(input_path, 'r'))
        hits.append(coref_score["hits"][f'hits@{args.hits - 1}'])

    # get prompt result
    prompt_dir = os.path.join(args.duel_dir, args.plm)
    for context_window in context_windows:
        # plm stays the same for different ctx_windows
        score_dir = os.path.join(prompt_dir, f'atn{args.atn}', '100ctx')
        input_path = os.path.join(score_dir, "prompt_score.json")
        prompt_score = json.load(open(input_path, 'r'))
        hits.append(prompt_score["hits"][f'hits@{args.hits - 1}'])

    return hits


def work(args):
    ctx_type_num = len(context_windows)
    x_name = 'context_window'
    y_name = f'hits@{args.hits}'
    fre_shot_led = pd.DataFrame({
        x_name: context_windows * 3,
        y_name: get_alias_hits(args),
        'alias_source': ['xlink'] * ctx_type_num + ['coref'] * ctx_type_num + ['prompt'] * ctx_type_num
    })
    pic_name = f"ctx{ctx_type_num}_{y_name}"

    f, ax = plt.subplots(figsize=(869 / 85, 513 / 85))
    if args.figure == 'histogram':
        save_path = f"/home/tsq/ybb/src/data/DuEL/histogram/{pic_name}.png"
        sns.barplot(x=x_name, y=y_name, hue="alias_source", data=fre_shot_led)
    else:
        save_path = f"/home/tsq/ybb/src/data/DuEL/lineplot/{pic_name}.png"
        sns.lineplot(x=x_name, y=y_name, hue="alias_source", data=fre_shot_led)
    plt.xticks(fontsize=20)  # x轴刻度的字体大小（文本包含在pd_data中了）
    plt.yticks(fontsize=20)  # y轴刻度的字体大小（文本包含在pd_data中了）
    plt.xlabel(x_name, fontdict={'weight': 'normal', 'size': 22})
    plt.ylabel(y_name, fontdict={'weight': 'normal', 'size': 22})
    plt.legend(title="alias_source", fontsize=14, title_fontsize=14)
    plt.show()
    plt.close()
    f.savefig(save_path, dpi=100, bbox_inches='tight')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--duel_dir', type=str, default='/data/tsq/DuEL/filtered')
    parser.add_argument('--corpus_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--output_dir', type=str, default='/data/tsq/DuEL/filtered/coref')

    # sample parameter
    parser.add_argument('--hits', type=int, default=10)

    # plm
    parser.add_argument('--plm', type=str, default='glm',
                        choices=['cpm2', 'glm'])
    parser.add_argument('--atn', type=int, default=1)
    # figure
    parser.add_argument('--figure', type=str, default='histogram',
                        choices=['histogram', 'lineplot'])
    args = parser.parse_args()
    work(args)
