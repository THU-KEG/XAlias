#!/bin/bash
arr=(250 500 625 750 875)

for a in ${arr[*]}
do
  echo $a
  python -m src.data.DuEL.test --alias_source xlink --context_window $a --output_dir '/data/tsq/DuEL/filtered/xlink'
done
