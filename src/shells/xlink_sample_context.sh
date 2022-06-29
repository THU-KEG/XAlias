#!/bin/bash
arr=(50 100 1000 10000 20000)

for a in ${arr[*]}
do
  echo $a
  python -m src.data.DuEL.test --alias_source xlink --context_window $a --output_dir '/data/tsq/DuEL/filtered/xlink'
done
