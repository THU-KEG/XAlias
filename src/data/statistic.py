import argparse
import json
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import pandas as pd
from xlrd import open_workbook
from src.data.discover_alias import HasAlias
from src.train.measure import get_avg_generate_nums
from src.model.const import jan_12_pos_result_paths

en2ch = {
    "prefix_extend": "增加前缀",
    "prefix_reduce": "去除前缀",
    "suffix_extend": "增加后缀",
    "suffix_reduce": "去除后缀",
    "abbreviation": "缩写",
    "expansion": "扩写",
    "synonym": "同义短语",
    "punctuation": "增加标点",
}


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd/purify/filter_english/pool_80/')
    parser.add_argument('--at_result_dir', type=str,
                        default='/data/tsq/xlink/bd/result/synonym/few_shot/task_specific/time_11222133')
    parser.add_argument('--pic_dir', type=str, default='/home/tsq/ybb/pic')
    # human data
    parser.add_argument('--xls_path', type=str, default='/home/tsq/ybb/data/human/time_01121646.xls')
    parser.add_argument('--sheet_num', type=int, default=140)
    parser.add_argument('--annotate_k', type=int, default=20)
    # task
    parser.add_argument('--task', type=str, default='human_acc',
                        choices=['has_alias_distribution', 'num_return_sequences', 'aggregate_draw_hits',
                                 'aggregate_dump_features', 'human_acc'])
    args = parser.parse_args()
    has_alias_relation_path = os.path.join(args.data_dir, 'has_alias_relation_record.pkl')

    if args.task == 'has_alias_distribution':
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
        plt.rcParams['axes.unicode_minus'] = False  # 解决无法显示符号的问题
        sns.set(font='SimHei', font_scale=0.8)  # 解决Seaborn中文显示问题

        with open(has_alias_relation_path, 'rb') as fin:
            has_alias_relation_record = pickle.load(fin)
            total_num = 0
            alias_types = []
            type2num = {}
            for alias_type, has_alias_list in has_alias_relation_record.items():
                for i in range(len(has_alias_list)):
                    # alias_types.append(en2ch[alias_type])
                    alias_types.append(alias_type)
                print(alias_type, len(has_alias_list))
                total_num += len(has_alias_list)
                type2num[alias_type] = len(has_alias_list)
            print("total num is ", total_num)
            df = pd.DataFrame({'type': alias_types})
            # draw bar picture
            g = sns.catplot(x="type", kind="count", palette="ch:.50", data=df)
            g.set_xticklabels(rotation=45)
            g.fig.set_size_inches(10, 8)
            g.fig.subplots_adjust(top=0.81, right=0.86)
            # 在柱状图的上面显示各个类别的数量
            i = 0
            for _alias_type, num in type2num.items():
                # 在柱状图上绘制该类别的数量
                g.ax.text(1 * i - 0.15, num, '{}'.format(num))
                i += 1

            plt.title("Number of alias")
            save_path = os.path.join(args.pic_dir, 'number_of_alias_enx.png')
            plt.savefig(save_path, bbox_inches='tight')
    elif args.task == 'num_return_sequences':
        record_json_path = os.path.join(args.at_result_dir, 'records.json')
        with open(record_json_path, 'r') as f:
            records = json.load(f)
            avg_predict_nums = get_avg_generate_nums(records)
            print("Data from: ", args.at_result_dir)
            print("avg predict_word_num for each pattern:", avg_predict_nums)
            print("avg_num:", sum(avg_predict_nums) / len(avg_predict_nums))
    elif args.task == 'aggregate_draw_hits':
        for pic_name, hits_path_dict in jan_12_pos_result_paths.items():
            draw_hits(args, pic_name, hits_path_dict)
    elif args.task == 'human_acc':
        read_xls(args)


def draw_hits(args, pic_name, hits_path_dict):
    save_path = os.path.join(args.pic_dir, pic_name)
    hits_value_dict = {"setting": [], "hits": [], "@k": []}
    for experiment_name, hits_dir in hits_path_dict.items():
        hits_path = os.path.join(hits_dir, "hits.json")
        with open(hits_path, 'r') as json_file:
            hits = json.load(json_file)
            for i, key in enumerate(hits.keys()):
                if i > 60:
                    break
                value = hits[key]
                k = int(key[5:])
                hits_value = float(value)
                hits_value_dict["setting"].append(experiment_name)
                hits_value_dict["@k"].append(k)
                hits_value_dict["hits"].append(hits_value)

    hits_data = pd.DataFrame(hits_value_dict)
    sns.lineplot(x="@k", y="hits", hue="setting", markers="o", data=hits_data)
    plt.savefig(save_path, bbox_inches='tight')
    plt.close('all')


def read_xls(args):
    read_book = open_workbook(args.xls_path)
    valid_alias_list = []
    for i in range(args.sheet_num):
        sheet = read_book.sheet_by_index(i)
        valid_alias_num = 0
        for j in range(1, 1 + args.annotate_k):
            value = sheet.cell(j, 3).value
            print("i,j", i, j)
            print(value)
            valid_alias_num += int(value)
        valid_alias_list.append(valid_alias_num)
    print(valid_alias_list)
    average_alias_num = sum(valid_alias_list) / len(valid_alias_list)
    print("alias_num@{} is {}".format(str(args.annotate_k), str(average_alias_num)))
    zero_num = valid_alias_list.count(0)
    hits = (len(valid_alias_list) - zero_num) / len(valid_alias_list)
    print("hits@{} is {}".format(str(args.annotate_k), str(hits)))


if __name__ == '__main__':
    work()
