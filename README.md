README

This is the repository for our unsupervised alias generation task.

We utilize pretrained language model(e.g. GPT2) to generate possible mentions for a word.

Here are the packages:

- demo
  - You can try out some examples here.
- src





# Interesting Result

## Reproduction

Using the **same parameters** may get **different outputs:**(2021/10/29) 

![](./pic/20211029162058.png)

I think this is caused by our decoding strategy which is sampling. If we set the random seed, it will generate the same output:(2021/11/2) 

![](./pic/20211102141853.png)

## Try different patterns

Here is the result of different patterns:

![](./pic/20211102145239.png)

## Reverse `xlink` table

We reverse the entity linking relations and get the map between  the entity id and mentions (See `README` under `src`).

Here are some types which frequently appear in the result:

| Type            | example                                                      | Noise |
| --------------- | ------------------------------------------------------------ | ----- |
| Bilingual alias | bdi13132852::=纽约大学::=美国纽约大学::=new york university::=nyu | NO    |
| Prefix alias    | bdi3680860::=移动定制手机::=中国移动定制机<br/>bdi8362196::=夏宫::=彼得大帝夏宫 | NO    |
| Suffix alias    | bdi17597962::=永夜城::=永夜城（短篇小说）<br/>bdi4004751::=北京大北宾馆::=北京大北宾馆（大望路店） | NO    |
| Abbreviation    | bdi18479549::=国动委::=国家国防动员委员会                    | NO    |
| Synonym         | bdi4049370::=波尔多红酒::=波尔多葡萄酒                       | NO    |
| One to all      | bdi14804606::=万达广场::=厦门湖里万达广场<br/>bdi14805470::=万达广场::=苏州万达广场<br/>bdi14805482::=万达广场::=莆田万达广场 | YES   |
| Punctuation     | bdi4611038::=洛奇::=《洛奇》                                 | YES   |

