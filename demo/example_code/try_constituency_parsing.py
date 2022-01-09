import stanfordnlp

nlp = stanfordnlp.Pipeline(processors='tokenize,mwt,pos')
doc = nlp("Barack Obama was born in Hawaii.")
print(*[f'word: {word.text+" "}\tupos: {word.upos}\txpos: {word.xpos}' for sent in doc.sentences for word in sent.words], sep='\n')

"""
word: Barack 	upos: PROPN	xpos: NNP
word: Obama 	upos: PROPN	xpos: NNP
word: was 	upos: AUX	xpos: VBD
word: born 	upos: VERB	xpos: VBN
word: in 	upos: ADP	xpos: IN
word: Hawaii 	upos: PROPN	xpos: NNP
word: . 	upos: PUNCT	xpos: .
"""