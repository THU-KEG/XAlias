import jieba

test_str = "清华大学也叫清华，北京大学的别名是北大。"
seg_list = jieba.cut(test_str, cut_all=False)
print("【精确模式】:\t" + "/ ".join(seg_list))
