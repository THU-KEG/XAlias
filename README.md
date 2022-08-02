We present **XAlias**, an open-source bilingual system for NLP developers, which consists of an [online website](http://103.238.162.32:9627/), a [toolkit](https://github.com/THU-KEG/XAlias) and several API services for unsupervised alias discovery. 

Specifically, we propose a novel alias generation algorithm, which exploiting PLMs for prompting high-coverage aliases. 

We hope our efforts can facilitate the individual researchers and developers in conveniently employing alias knowledge in more downstream tasks and industrial applications.

# 1. Quick Start

The alias API is for users who need entities' alias table on open-domain settings. As for the two alias extraction sources, users can get alias table on entities that have shown up in Wikipedia or Baidu Baike.  While for the corpus-free alias generation source, there is no limit on input entity, any input entity name can get its generated alias table. The alias sources are specified by the `alias_source` key in the post request. Users can either download the code and data from our github for their customized usage or just send request to our backend API by the following scripts for directly retrieving the alias table:

```python
import json, requests
ip = "103.238.162.32"
entity="Southampton F.C."
alias_type="abbreviation"
alias_source="request_get_prompt_alias"
lang="EN"
data = json.dumps({
    'entity':entity, 
    'type':alias_type, 
    alias_source:{},
    'lang':lang
    })
url = f"https://{ip}:9627/alias"
result = requests.post(url, 
                data=data,
                verify=False
                )
print(result.json())
# {"reply_get_prompt_alias": 
# {"alias_list": 
# [{"text": "sfc", "score": 0, 
# "types": ["abbreviation"]}]}}
```

There are 3 kinds of `alias_source` key:

| alias_source             | need to specify alias_type | description                                             |
| ------------------------ | -------------------------- | ------------------------------------------------------- |
| request_get_prompt_alias | Yes                        | request for prompt-based alias generation               |
| request_get_dict_alias   | No                         | request for hyperlink discovery of alias extraction     |
| request_get_coref_alias  | No                         | request for  coreference resolution of alias extraction |

Users can customize the request according to their situations.

# 2.  Further Exploration

| link                                                         | description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [README_exp.md](https://github.com/THU-KEG/XAlias/blob/master/README_exp.md) | Preliminary experiment record                                |
| [src/](https://github.com/THU-KEG/XAlias/tree/master/src)    | Code for our alias discovery system's data curation, experiment and models |
| [WebApp/](https://github.com/THU-KEG/XAlias/tree/master/WebApp) | Code for our demo [website](http://103.238.162.32:9627/),which is based on Tornado. |

