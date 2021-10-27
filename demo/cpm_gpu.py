from transformers import TextGenerationPipeline, AutoTokenizer, AutoModelForCausalLM

DEVICE = 'cuda'

tokenizer = AutoTokenizer.from_pretrained("TsinghuaAI/CPM-Generate")

model = AutoModelForCausalLM.from_pretrained("TsinghuaAI/CPM-Generate")
device_map = {0: [0, 1, 2, 3, 4, 5, 6, 7],
              1: [8, 9, 10, 11, 12, 13, 14, 15],
              2: [16, 17, 18, 19, 20, 21, 22, 23],
              4: [24, 25, 26, 27, 28, 29, 30, 31]}

model.parallelize(device_map)

input_context = "清华大学也被称为"
# get tokens of words that should not be generated
# bad_words_ids = [tokenizer(bad_word, add_prefix_space=True).input_ids for bad_word in ["idiot", "stupid", "shut up"]]
# encode input context
input_ids = tokenizer(input_context, return_tensors="pt").input_ids
# generate sequences without allowing bad_words to be generated
outputs = model.generate(input_ids=input_ids.to(DEVICE), max_length=20, do_sample=True, bad_words_ids=None)
print("Generated:", tokenizer.decode(outputs[0], skip_special_tokens=True))

# input_context = "清华大学"
# encode input context
# input_ids = tokenizer(input_context, return_tensors="pt").input_ids
# generate candidates using sampling
# outputs = model.generate(input_ids=input_ids, max_length=20, top_p=0.9, do_sample=True)
# print("Generated:", tokenizer.batch_decode(outputs, skip_special_tokens=True))
