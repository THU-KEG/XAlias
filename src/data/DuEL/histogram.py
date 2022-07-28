import seaborn as sns
import pandas as pd
import argparse
import os
import json
import matplotlib.pyplot as plt

context_windows = [100, 250, 500, 625, 750, 875, 1000]


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

    # get ensemble result
    prompt_dir = os.path.join(args.duel_dir, args.plm)
    for context_window in context_windows:
        score_dir = os.path.join(prompt_dir, f'atn{args.atn}', '100ctx', f"ensemble{context_window}")
        input_path = os.path.join(score_dir, "ensemble_score.json")
        ensemble_score = json.load(open(input_path, 'r'))
        hits.append(ensemble_score["hits"][f'hits@{args.hits - 1}'])

    return hits


def draw_sum(args):
    ctx_type_num = len(context_windows)
    x_name = 'context_window'
    y_name = f'hits@{args.hits}'
    fre_shot_led = pd.DataFrame({
        x_name: context_windows * 4,
        y_name: get_alias_hits(args),
        'alias_source': ['hyperlink'] * ctx_type_num + ['coref'] * ctx_type_num + ['prompt'] * ctx_type_num + [
            'ensemble'] * ctx_type_num
    })
    pic_name = f"{args.plm}_atn{args.atn}_ctx{ctx_type_num}_{y_name}"

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


def correct_check(_result, tgt_lst):
    res_lst = []
    for res in _result[:10]:
        if res in tgt_lst:
            res_lst.append(res)
    return res_lst


def get_contribution(task):
    xlink_path = "/data/tsq/DuEL/filtered/xlink/20000ctx/xlink_score.json"
    xlink_result_list = json.load(open(xlink_path, 'r'))["results"]
    coref_path = "/data/tsq/DuEL/filtered/coref/ctx20000/bd/sample_entity_fill_20000tokens_score.json"
    coref_result_list = json.load(open(coref_path, 'r'))["results"]
    prompt_path = "/data/tsq/DuEL/filtered/glm/atn4/100ctx/prompt_score.json"
    prompt_result_list = json.load(open(prompt_path, 'r'))["results"]
    # result
    tgt_num2correct_list = {}
    for i, xlink_result in enumerate(xlink_result_list):
        tgt_lst = xlink_result["tgt"]
        tgt_num = len(tgt_lst)
        extraction_right_lst = correct_check(xlink_result["pred"], tgt_lst)
        coref_pred_lst = correct_check(coref_result_list[i]["pred"], tgt_lst)
        for coref_pred in coref_pred_lst:
            if coref_pred not in extraction_right_lst:
                extraction_right_lst.append(coref_pred)

        # compare to generation result
        prompt_pred_lst = correct_check(prompt_result_list[i]["pred"], tgt_lst)
        num_distinct_gen = 0
        for prompt_pred in prompt_pred_lst:
            if task == 'no_distinct':
                num_distinct_gen += 1
            else:
                # only distinct count
                if prompt_pred not in extraction_right_lst:
                    num_distinct_gen += 1
        # compute num_right_ext
        num_right_ext = len(extraction_right_lst)
        if task != 'no_distinct':
            # only distinct count
            num_overlap = 0
            for prompt_pred in prompt_pred_lst:
                if prompt_pred in extraction_right_lst:
                    num_overlap += 1
            num_right_ext -= num_overlap
        # append
        correct_list = [num_right_ext, num_distinct_gen]
        try:
            tgt_num2correct_list[tgt_num].append(correct_list)
        except KeyError:
            tgt_num2correct_list[tgt_num] = [correct_list]
    # count average
    tgt_num2num_right_ext = {}
    tgt_num2num_distinct_gen = {}
    for k, correct_lists in tgt_num2correct_list.items():
        total_ext = 0
        total_gen = 0
        for correct_list in correct_lists:
            total_ext += correct_list[0]
            total_gen += correct_list[1]
        tgt_num2num_right_ext[k] = total_ext / len(correct_lists)
        tgt_num2num_distinct_gen[k] = total_gen / len(correct_lists)
    sorted_data_ext = sorted(tgt_num2num_right_ext.items(), key=lambda x: x[0])
    sorted_data_gen = sorted(tgt_num2num_distinct_gen.items(), key=lambda x: x[0])
    print(sorted_data_ext)
    print("#" * 10)
    print(sorted_data_gen)
    return sorted_data_ext, sorted_data_gen


def draw_contribution(args):
    sorted_data_ext, sorted_data_gen = get_contribution(args.task)
    label_nums = []
    correct_alias_nums = []
    x_num = len(sorted_data_ext)
    for tuple_ext in sorted_data_ext:
        label_nums.append(tuple_ext[0])
        correct_alias_nums.append(tuple_ext[1])
    for tuple_gen in sorted_data_gen:
        correct_alias_nums.append(tuple_gen[1])
    x_name = 'label_num'
    if args.task == 'no_distinct':
        y_name = 'correct_num'
    else:
        y_name = 'distinct_correct_num'
    sorted_data = pd.DataFrame({
        x_name: label_nums * 2,
        y_name: correct_alias_nums,
        'alias_source': ['extraction'] * x_num + ['generation'] * x_num
    })
    print(sorted_data)
    pic_name = f"{args.plm}_atn{args.atn}_{y_name}"
    f, ax = plt.subplots(figsize=(869 / 85, 513 / 85))
    if args.figure == 'histogram':
        save_path = f"/home/tsq/ybb/src/data/DuEL/histogram/{pic_name}.png"
        sns.barplot(x=x_name, y=y_name, hue="alias_source", data=sorted_data)
    else:
        save_path = f"/home/tsq/ybb/src/data/DuEL/lineplot/{pic_name}.png"
        sns.lineplot(x=x_name, y=y_name, hue="alias_source", data=sorted_data)
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
    parser.add_argument('--task', type=str, default='sum',
                        choices=['contribution', 'no_distinct', 'sum'])
    parser.add_argument('--figure', type=str, default='histogram',
                        choices=['histogram', 'lineplot'])
    args = parser.parse_args()
    if args.task == 'sum':
        draw_sum(args)
    else:
        draw_contribution(args)
