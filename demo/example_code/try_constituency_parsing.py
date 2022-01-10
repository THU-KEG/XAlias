import stanfordnlp

# lang = 'en'
lang = 'zh'
# test_str = "Barack Obama was born in Hawaii."
# test_str = "清华大学也叫清华，北京大学的别名是北大。"
test_str = "北京作家协会"
nlp = stanfordnlp.Pipeline(lang=lang, processors='tokenize,mwt,pos')
doc = nlp(test_str)
print(*[f'word: {word.text + " "}\tupos: {word.upos}\txpos: {word.xpos}' for sent in doc.sentences for word in
        sent.words], sep='\n')
print("No2########")
test_str = "清华大学也叫清华，北京大学的别名是北大。"
doc = nlp(test_str)
print(*[f'word: {word.text + " "}\tupos: {word.upos}\txpos: {word.xpos}' for sent in doc.sentences for word in
        sent.words], sep='\n')
POS_list = [word.upos for sent in doc.sentences for word in sent.words]
print(POS_list)
"""
word: Barack 	upos: PROPN	xpos: NNP
word: Obama 	upos: PROPN	xpos: NNP
word: was 	upos: AUX	xpos: VBD
word: born 	upos: VERB	xpos: VBN
word: in 	upos: ADP	xpos: IN
word: Hawaii 	upos: PROPN	xpos: NNP
word: . 	upos: PUNCT	xpos: .
"""

""" 没有句号的结果
word: 清华 	upos: PROPN	xpos: NNP
word: 大学 	upos: NOUN	xpos: NN
word: 也 	upos: ADV	xpos: RB
word: 叫 	upos: VERB	xpos: VV
word: 清 	upos: PROPN	xpos: NNP
word: 华 	upos: PROPN	xpos: NNP
word: ， 	upos: CCONJ	xpos: CC
word: 北京 	upos: PROPN	xpos: NNP
word: 大学 	upos: NOUN	xpos: NN
word: 的 	upos: PART	xpos: DEC
word: 别名 	upos: NOUN	xpos: NN
word: 是 	upos: AUX	xpos: VC
word: 北 	upos: NOUN	xpos: NN
word: 大 	upos: PUNCT	xpos: .
"""

"""有句号
word: 清华 	upos: PROPN	xpos: NNP
word: 大学 	upos: NOUN	xpos: NN
word: 也 	upos: ADV	xpos: RB
word: 叫 	upos: VERB	xpos: VV
word: 清 	upos: PROPN	xpos: NNP
word: 华 	upos: PROPN	xpos: NNP
word: ， 	upos: CCONJ	xpos: CC
word: 北京 	upos: PROPN	xpos: NNP
word: 大学 	upos: NOUN	xpos: NN
word: 的 	upos: PART	xpos: DEC
word: 别名 	upos: NOUN	xpos: NN
word: 是 	upos: AUX	xpos: VC
word: 北大 	upos: PROPN	xpos: NNP
word: 。 	upos: PUNCT	xpos: .
"""
