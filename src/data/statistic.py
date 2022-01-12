import argparse
import json
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import pandas as pd
from src.data.discover_alias import HasAlias
from src.train.measure import get_avg_generate_nums
from src.model.const import jan_12_pos_result_paths


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd/purify/filter_english/pool_80/')
    parser.add_argument('--at_result_dir', type=str,
                        default='/data/tsq/xlink/bd/result/synonym/few_shot/task_specific/time_11222133')
    parser.add_argument('--pic_dir', type=str, default='/home/tsq/ybb/pic')
    parser.add_argument('--task', type=str, default='aggregate_draw_hits',
                        choices=['has_alias_distribution', 'num_return_sequences', 'aggregate_draw_hits',
                                 'aggregate_dump_features'])
    args = parser.parse_args()
    has_alias_relation_path = os.path.join(args.data_dir, 'has_alias_relation_record.pkl')

    if args.task == 'has_alias_distribution':
        with open(has_alias_relation_path, 'rb') as fin:
            has_alias_relation_record = pickle.load(fin)
            total_num = 0
            alias_types = []
            for alias_type, has_alias_list in has_alias_relation_record.items():
                for i in range(len(has_alias_list)):
                    alias_types.append(alias_type)
                print(alias_type, len(has_alias_list))
                total_num += len(has_alias_list)
            print("total num is ", total_num)
            df = pd.DataFrame({'type': alias_types})
            # draw bar picture
            g = sns.catplot(x="type", kind="count", palette="ch:.50", data=df)
            g.set_xticklabels(rotation=45)
            plt.title("Number of alias")
            save_path = os.path.join(args.pic_dir, 'number_of_alias.png')
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
    elif args.task == 'aggregate_dump_features':
        pass


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


if __name__ == '__main__':
    work()
