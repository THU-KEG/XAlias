import argparse
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import pandas as pd
from src.data.discover_alias import HasAlias


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--pic_dir', type=str, default='/home/tsq/ybb/pic')
    parser.add_argument('--task', type=str, default='has_alias_distribution', choices=['has_alias_distribution'])
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


if __name__ == '__main__':
    work()
