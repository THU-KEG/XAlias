In src package,  we provide the code which performs our main functions.



# data

In data package, there are some python scripts that help us build the dataset.

## reverse_table

This script can reverse the original `entity linking` dataset to our `alias mapping` dataset:

```
python -m src.data.reverse_table --data_dir XX --src_file mention_anchors.txt
```

We will generate 3 result files under `data_dir`  which store the map between `mention` and `entity_id`:

- `id2mention.json`
- `id2mention.txt`
  - stores all the mentions and their ids.
- `id2mention_multi.txt`
  - only stores the mentions with **multiple** ids.

# model

## pattern

This file contains our manual designed templates and the `Verbalizer`.

## decode

This is the implementation of `beam search` for `CPM2` model.