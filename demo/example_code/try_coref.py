from stanfordnlp.server import CoreNLPClient

# export CORENLP_HOME=/data/tsq/corenlp/stanford-corenlp-4.4.0
# example text
print('---')
print('input text')
print('')
# text = "Chris Manning is a nice person. Chris wrote a simple sentence. He also gives oranges to people."
text = "习近平出生在中国。 他是中国的总统."
print(text)

# set up the client
print('---')
print('starting up Java Stanford CoreNLP Server...')

# set up the client
with CoreNLPClient(
        properties="chinese",
        annotators=['coref'],
        endpoint="http://localhost:5414",
        timeout=30000, memory='16G') as client:
    ann = client.annotate(text)

    #         properties={
    #             "annotators": "tokenize,ssplit,coref",
    #             'tokenize.language': 'zh',
    #
    #         },
    #         endpoint="http://localhost:5414",
    #         timeout=30000, memory='16G', output_format='json') as client:
    #     # submit the request to the server
    #     ann = client.annotate(text, output_format='json')
    # client = CoreNLPClient(start_server=False)
    # ann = client.annotate(text=text, properties={"inputFormat": "text", "outputFormat": "json"})
    # sentence and token
    for sentence in ann.sentence:
        for token in sentence.token:
            print(token.word)

    # access the coref chain
    print('---')
    print('coref chains for the example')
    print(ann.corefChain)
    # print(ann)
