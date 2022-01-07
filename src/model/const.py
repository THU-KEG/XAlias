patterns = {
    'ch': {
        'fill': ['也被称为<span>。', '的别名是<span>。', '的缩写为<span>。', ',简称<span>。', '也作为<span>被熟知。'],
        'generate':
            {
                # 'prefix': ['也被称为', '的别名是', '又名', '即', '的全名是', '简称'],  # List of templates
                'prefix_extend': ['，即'],
                'prefix_reduce': ['，简称'],
                # 'suffix': ['也被称为', '的别名是', '的缩写为', ',简称'],
                'suffix_extend': ['，即'],
                'suffix_reduce': ['，简称'],
                # 'abbreviation': ['也被称为', '的别名是', '的缩写为', ',简称'],
                # 'abbreviation': ['，即', ',简称'],
                'expansion': ['，即'],
                'abbreviation': ['，简称'],
                # 'synonym': ['也被称为', '的别名是', '的同义词是', ',也称'],
                # 'synonym': ['也被称为', '的别名是', '的同义词是', '，也称', '，又叫', '，即'],
                'synonym': ['的同义词是'],
                # 'punctuation': ['也被称为', '的别名是', ',简称', '，简称', '简称'],
                'punctuation': ['的别名是'],
            }
    }

}

few_shot_alias_table = {
    'prefix_extend': {
        '标致408': ['东风标致408'],
        '寒窑遗址公园': ['曲江寒窑遗址公园'],
        '滕尼斯': ['斐迪南·滕尼斯'],
        '纽黑文大学': ['美国纽黑文大学'],
        '四大名楼': ['中国四大名楼'],
        '137年': ['公元137年'],
        '大阪体育大学': ['日本大阪体育大学'],
        '江宁实验小学': ['南京市江宁实验小学'],
        '先知寺': ['麦地那先知寺'],
        '八一体育场': ['南昌八一体育场'],
    },
    'prefix_reduce': {
        '爱新觉罗·奕勋': ['奕勋'],
        '山东微山湖国家湿地公园': ['微山湖国家湿地公园'],
        '里卡多·高拉特': ['高拉特'],
        '（综漫）打工记': ['打工记'],
        '小雅·甫田': ['甫田'],
        '慧因高丽寺': ['高丽寺'],
        '台湾云林科技大学': ['云林科技大学'],
        '盐城市龙冈中学': ['龙冈中学'],
        '西安大唐健康网': ['大唐健康网'],
        '南昌百花洲小学': ['百花洲小学'],
    },
    'suffix_extend': {
        '信息隐藏': ['信息隐藏技术'],
        '实验物理': ['实验物理学'],
        '朱丽安娜': ['朱丽安娜女王'],
        '海牙': ['海牙市'],
        '米筛竹': ['米筛竹（原变种）'],
        '盐豆': ['盐豆子'],
        '混鲲': ['混鲲祖师'],
        '红提': ['红提葡萄'],
        '中西医临床医学': ['中西医临床医学专业'],
        '齐鲁证券': ['齐鲁证券有限公司'],
    },
    'suffix_reduce': {
        '中国药用植物（一）': ['中国药用植物'],
        '白花蓬子菜（变种）': ['白花蓬子菜'],
        '南尖岩风景区': ['南尖岩'],
        '桂林如家快捷酒店（火车站店）': ['桂林如家快捷酒店'],
        '世纪证券有限责任公司': ['世纪证券'],
        '净检法师': ['净检'],
        '孟加拉鸨属': ['孟加拉鸨'],
        '广南高速公路': ['广南高速'],
        '老阁村': ['老阁'],
        '精细化工工艺学（第2版）': ['精细化工工艺学'],
    },
    'abbreviation': {
        '北京航空航天大学体育馆': ['北航体育馆'],
        '津巴布韦元': ['津元'],
        '湖南省道县第二中学': ['道县二中'],
        '中国中药博览会': ['药博会'],
        '马来西亚石油公司': ['马石油'],
        '中国人民解放军江苏省军区': ['江苏军区'],
        '铁路钢轨': ['路轨'],
        '中国移动通信集团四川有限公司': ['四川移动'],
        '厦门银鹭食品集团有限公司': ['银鹭'],
        '周口西华通用机场': ['周口机场'],
    },
    'expansion': {
        '福建美术馆': ['福建省美术馆'],
        '黎塘站': ['黎塘火车站'],
        '旧金山地震': ['旧金山大地震'],
        '绍兴站': ['绍兴火车站'],
        '郑州动物园': ['郑州市动物园'],
        '风电厂': ['风力发电厂'],
        '虹湾': ['月球虹湾区'],
        '礼王府': ['礼亲王府'],
        '双溪湖风景区': ['双溪湖风景旅游区'],
        '敦煌博物馆': ['敦煌市博物馆'],
    },
    'synonym': {
        '热带雨林带': ['赤道雨林带'],
        '三古镇': ['三古乡'],
        '云南省会警察厅': ['云南警察总局'],
        '无义务原则': ['无干预原则'],
        '国际业余拳击协会': ['国际业余拳击联合会'],
        '蓝团鱼': ['绿团鱼'],
        '萍乡腊肉': ['萍乡烟熏肉'],
        '64式手枪': ['六四式手枪'],
        '多贡族': ['多贡人'],
        '赫拉特战役': ['赫拉特之战'],
    },
    'punctuation': {
        '燕北录': ['《燕北录》'],
        '海错图': ['《海错图》'],
        '“先看病后付费”制度': ['先看病后付费'],
        '“勃兰登堡”级（123型）护卫舰': ['“勃兰登堡”级护卫舰'],
        '水星号飞船': ['“水星”号飞船'],
        '打灶君': ['《打灶君》'],
        '统计月报': ['《统计月报》'],
        '民国那些事儿': ['《民国那些事儿》'],
        '2012中国（深圳）国际工业博览会（消费电子展）': ['2012中国国际工业博览会'],
        '超硬材料国家重点实验室（吉林大学）': ['吉林大学超硬材料国家重点实验室'],
    },
    'void': {},
}
"""
patterns = {
    'ch': {
        'fill': ['也被称为<span>。', '的别名是<span>。', '的缩写为<span>。', ',简称<span>。', '也作为<span>被熟知。'],
        'generate':
            {
                # 'prefix': ['也被称为', '的别名是', '又名', '即', '的全名是', '简称'],  # List of templates
                'prefix': ['又名'],  # List of templates
                # 'suffix': ['也被称为', '的别名是', '的缩写为', ',简称'],
                'suffix': [',简称'],
                # 'abbreviation': ['也被称为', '的别名是', '的缩写为', ',简称'],
                # 'abbreviation': ['，即', ',简称'],
                'abbreviation': [',简称'],
                # 'synonym': ['也被称为', '的别名是', '的同义词是', ',也称'],
                # 'synonym': ['也被称为', '的别名是', '的同义词是', '，也称', '，又叫', '，即'],
                'synonym': ['的同义词是'],
                # 'punctuation': ['也被称为', '的别名是', ',简称', '，简称', '简称'],
                'punctuation': ['的别名是'],
                'bilingual': ['也被称为', '的别名是', '的译文是', ',也称'],
                'multiple': ['也被称为', '的别名是', '的缩写为', ',也称'],
            }
    }

}
few_shot_alias_table = {
    'prefix': {
        '标致408': ['东风标致408'], '东风标致408': ['标致408'],
        '山东微山湖国家湿地公园': ['微山湖国家湿地公园'], '微山湖国家湿地公园': ['山东微山湖国家湿地公园'],
        '里卡多·高拉特': ['高拉特'], '高拉特': ['里卡多·高拉特'],
        '（高职高专）中餐烹饪美学': ['中餐烹饪美学'], '约瑟夫·霞飞': ['霞飞'],
        '碧利斯': ['台风碧利斯'], '四门拳': ['少林四门拳'],
        '454年': ['公元454年'], '公元454年': ['454年'],
        '韩国济州大学': ['济州大学'], '济州大学': ['韩国济州大学'],
        '盐城市龙冈中学': ['龙冈中学'], '龙冈中学': ['盐城市龙冈中学'],
        '大唐健康网': ['西安大唐健康网'], '西安大唐健康网': ['大唐健康网'],
        '国务院办公厅关于规范校外培训机构发展的意见': ['关于规范校外培训机构发展的意见'], '关于规范校外培训机构发展的意见': ['国务院办公厅关于规范校外培训机构发展的意见'],
    },
    'suffix': {
        '杏仁桉': ['杏仁桉树'], '杏仁桉树': ['杏仁桉'],
        '假苜蓿（原变种）': ['假苜蓿'], '中国药用植物（二十二）': ['中国药用植物'],
        '无疤者奥斯里安': ['无疤者'], '无疤者': ['无疤者奥斯里安'],
        '青山关': ['青山关景区'], '青山关景区': ['青山关'],
        '山东省地震目录(1991-2007)': ['山东省地震目录'], '苏州格林豪泰酒店（观前店）': ['苏州格林豪泰酒店'],
        '广南高速公路': ['广南高速'], '广南高速': ['广南高速公路'],
        '耦合波理论': ['耦合波'], '耦合波': ['耦合波理论'],
        '酒酿清蒸鸭子': ['酒酿清蒸鸭'], '酒酿清蒸鸭': ['酒酿清蒸鸭子'],
        '净检法师': ['净检'], '净检': ['净检法师'],
        '印度舞蹈': ['印度舞'], '印度舞': ['印度舞蹈'],
    },
    'abbreviation': {
        '北京航空航天大学体育馆': ['北航体育馆'], '北航体育馆': ['北京航空航天大学体育馆'],
        '津巴布韦元': ['津元'], '津元': ['津巴布韦元'],
        '湖南省道县第二中学': ['道县二中'], '道县二中': ['湖南省道县第二中学'],
        '含盐量测定计': ['盐度计'], '盐度计': ['含盐量测定计'],
        '中国中药博览会': ['药博会'], '药博会': ['中国中药博览会'],
        '马来西亚石油公司': ['马石油'], '马石油': ['马来西亚石油公司'],
        '中国人民解放军江苏省军区': ['江苏军区'], '江苏军区': ['中国人民解放军江苏省军区'],
        '铁路钢轨': ['路轨'], '路轨': ['铁路钢轨'],
        '中国移动通信集团四川有限公司': ['四川移动'], '四川移动': ['中国移动通信集团四川有限公司'],
        '复方白屈菜酊': ['止痛酊'], '止痛酊': ['复方白屈菜酊'],
    },
    'synonym': {
        '山西省工艺美术协会': ['山西工艺美术协会'], '山西工艺美术协会': ['山西省工艺美术协会'],
        '应城火车站': ['应城站'], '应城站': ['应城火车站'],
        '云南警察总局': ['云南省会警察厅'], '云南省会警察厅': ['云南警察总局'],
        '铜陵三中': ['铜陵市第三中学'], '铜陵市第三中学': ['铜陵三中'],
        '无义务原则': ['无干预原则'], '无干预原则': ['无义务原则'],
        '国际业余拳击协会': ['国际业余拳击联合会'], '国际业余拳击联合会': ['国际业余拳击协会'],
        '蓝团鱼': ['绿团鱼'], '绿团鱼': ['蓝团鱼'],
        '喉部肿瘤': ['喉肿瘤'], '喉肿瘤': ['喉部肿瘤'],
        'α-干扰素': ['α干扰素'], 'α干扰素': ['α-干扰素'],
        '米底人': ['米堤亚人'], '米堤亚人': ['米底人'],
    },
    'punctuation': {
        '《燕北录》': ['燕北录'], '燕北录': ['《燕北录》'],
        '《海错图》': ['海错图'], '海错图': ['《海错图》'],
        '“先看病后付费”制度': ['先看病后付费'], '先看病后付费': ['“先看病后付费”制度'],
        '“勃兰登堡”级（123型）护卫舰': ['“勃兰登堡”级护卫舰'], '《南词新谱》': ['南词新谱'],
        '水星号飞船': ['“水星”号飞船'], '“水星”号飞船': ['水星号飞船'],
        '打灶君': ['《打灶君》'], '《打灶君》': ['打灶君'],
        '统计月报': ['《统计月报》'], '《统计月报》': ['统计月报'],
        '民国那些事儿': ['《民国那些事儿》'], '《民国那些事儿》': ['民国那些事儿'],
        '2012中国（深圳）国际工业博览会（消费电子展）': ['2012中国国际工业博览会'], '《和解》': ['和解'],
        '吉林大学超硬材料国家重点实验室': ['超硬材料国家重点实验室（吉林大学）'], '超硬材料国家重点实验室（吉林大学）': ['吉林大学超硬材料国家重点实验室'],
    },
    'multiple': {
        '夏延族': ['夏延人', '夏安族'], '夏延人': ['夏延族', '夏安族'], '夏安族': ['夏延族', '夏延人'],
    },
    'void': {},
}
"""

dec_17_cwd_avu_hits_result_paths = {
    "cwd_avu_vssa_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190951/rerank/ppl/time_12211455",
    "cwd_avu_vssm_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190951/rerank/ppl/time_12211459",
    "cwd_avu_vssa_svdm_vsc_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190951/rerank/ppl/time_12220815",
    "cwd_avu_vssa_svdm_vse_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190951/rerank/ppl/time_12220821",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900",
}

dec_17_cwd_avi_hits_result_paths = {
    "cwd_avi_vssa_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12211509",
    "cwd_avi_vssa_svdmxd_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12211526",
    "cwd_avi_vssa_svdm_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12211528",
    "cwd_avi_vssa_svdmxd_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12211530",
    "cwd_avi_vssa_svdm_vsc_rbsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12220828",
    "cwd_avi_vssm_svdm_vsc_rbsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12220829",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900",
}

dec_17_cw_av_best_compare_paths = {
    "cwd_avu_vssa_svdm_vsc_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190951/rerank/ppl/time_12220815",
    "cwd_avu_vssa_svdm_vse_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190951/rerank/ppl/time_12220821",
    "cwd_avi_vssa_svdmxd_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12211526",
    "cwd_avi_vssa_svdm_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12201538/rerank/ppl/time_12211528",
    "cwu_avu": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12190946/rerank/ppl/time_12211447",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900",
}

dec_17_hits_result_paths = {
    "distributed_use_value": dec_17_cwd_avu_hits_result_paths,
    "distributed_ignore_value": dec_17_cwd_avi_hits_result_paths,
    "compare_best_score": dec_17_cw_av_best_compare_paths
}

dec_27_cwd_avu_hits_result_paths = {
    "cwd_avu_vssa_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250920/rerank/ppl/time_12261044",
    "cwd_avu_vssm_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250920/rerank/ppl/time_12261046",
    "cwd_avu_vssa_svdm_vsc_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250920/rerank/ppl/time_12261012",
    "cwd_avu_vssa_svdm_vse_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250920/rerank/ppl/time_12261013",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/hits_60",
}

dec_27_cwd_avi_hits_result_paths = {
    "cwd_avi_vssa_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261013",
    "cwd_avi_vssa_svdmxd_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261014",
    "cwd_avi_vssa_svdm_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261015",
    "cwd_avi_vssa_svdmxd_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261016",
    "cwd_avi_vssa_svdm_vsc_rbsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261018",
    "cwd_avi_vssm_svdm_vsc_rbsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261019",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/hits_60",
}

dec_27_cw_av_best_compare_paths = {
    "cwd_avu_vssa_svdm_vsc_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250920/rerank/ppl/time_12261012",
    "cwd_avu_vssa_svdm_vse_rbs": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250920/rerank/ppl/time_12261013",
    "cwd_avi_vssa_svdmxd_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261014",
    "cwd_avi_vssa_svdm_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250921/rerank/ppl/time_12261015",
    "cwu_avu": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12250919/rerank/ppl/time_12261044",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/hits_60",
}

dec_27_hits_result_paths = {
    "distributed_use_value": dec_27_cwd_avu_hits_result_paths,
    "distributed_ignore_value": dec_27_cwd_avi_hits_result_paths,
    "compare_best_score": dec_27_cw_av_best_compare_paths
}

dec_30_cwd_avi_hits_result_paths = {
    "cwd_avi_vssa_svdm_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12261132/rerank/ppl/time_12301608",
    "cwd_avi_vssa_svdmxd_vsc": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12261132/rerank/ppl/time_12301609",
    "cwd_avi_vssa_svdm_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12261132/rerank/ppl/time_12301610",
    "cwd_avi_vssa_svdmxd_vse": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/score/time_12261132/rerank/ppl/time_12301614",
    "frequency": "/data/tsq/xlink/bd/purify/filter_english/pool_80/result/expansion/few_shot/task_specific/time_12140900/",
}
dec_30_hits_result_paths = {
    "distributed_ignore_value": dec_30_cwd_avi_hits_result_paths,
}
