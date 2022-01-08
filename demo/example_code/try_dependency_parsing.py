from stanfordcorenlp import StanfordCoreNLP

zh_model = StanfordCoreNLP(r'stanford-corenlp-full-2018-02-27', lang='zh')
s_zh = '我爱自然语言处理技术！'
dep_zh = zh_model.dependency_parse(s_zh)
print("zh output is", dep_zh)
# [('ROOT', 0, 4), ('nsubj', 4, 1), ('advmod', 4, 2), ('nsubj', 4, 3), ('dobj', 4, 5), ('punct', 4, 6)]
eng_model = StanfordCoreNLP(r'stanford-corenlp-full-2018-02-27')
s_eng = 'I love natural language processing technology!'
dep_eng = eng_model.dependency_parse(s_eng)
print("english output is", dep_eng)
# [('ROOT', 0, 2), ('nsubj', 2, 1), ('amod', 6, 3), ('compound', 6, 4), ('compound', 6, 5), ('dobj', 2, 6), ('punct', 2, 7)]
