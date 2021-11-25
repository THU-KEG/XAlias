import argparse
import json
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import pandas as pd
from src.data.discover_alias import HasAlias


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd/')
    parser.add_argument('--at_result_dir', type=str,
                        default='/data/tsq/xlink/bd/result/synonym/few_shot/task_specific/time_11222133')
    parser.add_argument('--pic_dir', type=str, default='/home/tsq/ybb/pic')
    parser.add_argument('--task', type=str, default='has_alias_distribution',
                        choices=['has_alias_distribution', 'num_return_sequences'])
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
            pattern_num = len(records[0]['pred'])
            avg_predict_nums = [0] * pattern_num
            for record in records:
                pattern2predicts = record['pred']
                for i, pattern2predict in enumerate(pattern2predicts):
                    avg_predict_nums[i] += len(pattern2predict)
            for k in range(pattern_num):
                avg_predict_nums[k] = avg_predict_nums[k] / len(records)
            print("Data from: ", args.at_result_dir)
            print("avg predict_word_num for each pattern:", avg_predict_nums)
            print("avg_num:", sum(avg_predict_nums) / len(avg_predict_nums))


if __name__ == '__main__':
    work()
