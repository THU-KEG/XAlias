from stanfordnlp.server import CoreNLPClient

# export CORENLP_HOME=/data/tsq/corenlp/stanford-corenlp-4.4.0
# example text
print('---')
print('input text')
print('')
text = "Chris Manning is a nice person. Chris wrote a simple sentence. He also gives oranges to people."
print(text)

# set up the client
print('---')
print('starting up Java Stanford CoreNLP Server...')

# set up the client
with CoreNLPClient(annotators=['tokenize', 'ssplit', 'coref'],
                   timeout=30000, memory='16G') as client:
    # submit the request to the server
    ann = client.annotate(text)

    # sentence and token
    for sentence in ann.sentence:
        for token in sentence.token:
            print(token.word)

    # access the coref chain
    print('---')
    print('coref chains for the example')
    print(ann.corefChain.getRepresentativeMention())
