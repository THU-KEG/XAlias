var requestUrl = "/alias";
var homeUrl = "http://103.238.162.32:5314/"; // place here the URL to the server
var raw_coref_chains;
var pormpt_alias_result;
var entity_name;
var lang;
var top_k = 5;
var alias_type2explain = {
    'prefix_extend': '前缀扩写,比如 夏宫::=彼得大帝夏宫',
    'prefix_reduce': '前缀缩写,比如 晋祠水母楼::=水母楼',
    'suffix_extend': '后缀扩写,比如 永夜城::=永夜城（短篇小说）',
    'suffix_reduce': '后缀缩写,比如 雍公馆（若水店）::=雍公馆',
    'expansion': '扩写,比如 济南十九中学::=山东省济南第十九中学',
    'abbreviation': '缩写,比如 国家国防动员委员会::=国动委',
    'synonym': '同义词,比如 波尔多红酒::=波尔多葡萄酒',
    'punctuation': '标点改写,比如 洛奇::=《洛奇》'
};

var result_alias_type2alias_res_dict = {
    "dict_alias_result": null,
    "coref_alias_result": null,
    "prompt_alias_result": null,
}

function sendRequest1(jsonObj, result_alias_type, reply_type) {
    // document.getElementById(result_alias_type).innerHTML = "waiting";
    change_timeline_node(result_alias_type, "timeline_waiting.png");
    console.log("sendRequest1");
    var data = JSON.stringify(jsonObj);
    console.log(data);
    $.ajax({
        type: "POST",
        url: requestUrl,
        dataType: "json",
        // contentType: 'application/json',
        data: data,
        // async: false,
        success: function (result) {
            console.log("jQuery success");
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("jQuery failed");
            alert(XMLHttpRequest.status);
            alert(XMLHttpRequest.readyState);
            alert(textStatus);
        },
        complete: function (xhr, status) {
            data = $.parseJSON(xhr.responseText);
            console.log(JSON.stringify(data));
            // document.getElementById(result_alias_type).textContent = JSON.stringify(data);
            var alias_res_dict = JSON.parse(data);
            fill_html_with_json(alias_res_dict, result_alias_type, reply_type);
            change_timeline_node(result_alias_type, "timeline_finish.png");
            check_ensemble_alias(alias_res_dict[reply_type], result_alias_type);
        }
    });
}

function clearAll() {
    var parent_id_list = ["dict_alias_result", "coref_alias_result", "prompt_alias_result", "ensemble_alias_result"];
    var i;
    for (i = 0; i < parent_id_list.length; i++) {
        clearAllNode(document.getElementById(parent_id_list[i]));
        change_timeline_node(parent_id_list[i], "timeline_empty.png");
    }
}

function clearAllNode(parentNode) {
    while (parentNode.firstChild) {
        var oldNode = parentNode.removeChild(parentNode.firstChild);
        oldNode = null;
    }
}

function onNameSubmit() {
    var entity = $("#entity").val();
    entity_name = entity;
    // var lang = $("input[name='lang']:checked").val();
    // var alias_type = $("#alias_type").val();
    var placeholder = $("#entity").attr("placeholder");
    if (placeholder == "输入实体词") {
        lang = "CH"
    } else {
        lang = "EN"
    }
    // lang = $("#lang").val();
    var alias_type = "all";
    // send the server the entity name:
    var clientId = 1;
    clearAll();
    // wait for 3 sources
    change_timeline_node("ensemble_alias_result", "timeline_waiting.png");
    sendRequest1({
        "clientId": clientId,
        "request_get_dict_alias": {},
        "entity": entity,
        "lang": lang,
        "type": alias_type
    }, "dict_alias_result", "reply_get_dict_alias");
    sendRequest1({
        "clientId": clientId,
        "request_get_coref_alias": {},
        "entity": entity,
        "lang": lang,
        "type": alias_type
    }, "coref_alias_result", "reply_get_coref_alias");
    sendRequest1({
        "clientId": clientId,
        "request_get_prompt_alias": {},
        "entity": entity,
        "lang": lang,
        "type": alias_type
    }, "prompt_alias_result", "reply_get_prompt_alias");
}


function addElementSpan(parent_id, alias_mention, alias_score) {
    var parent = document.getElementById(parent_id);
    //add span
    var span = document.createElement("span");
    span.setAttribute("class", "ag-tag ag-tag--success");
    parent.appendChild(span);
    // add ag-link to span
    var ag_link = document.createElement("a");
    ag_link.setAttribute("class", "ag-link");
    // add coref_chain modal
    if (parent_id == "coref_alias_result") {
        ag_link.setAttribute("class", "ag-link ag-link-coref");
        ag_link.setAttribute("onclick", "onClickCorefChain('" + alias_mention + "');return false");
    } else if (parent_id == "prompt_alias_result") {
        ag_link.setAttribute("class", "ag-link ag-link-coref");
        ag_link.setAttribute("onclick", "onClickAlias('" + alias_mention + "');return false");
    }
    span.appendChild(ag_link);
    // add mention span to ag-link
    var mention_span = document.createElement("span");
    mention_span.innerHTML = alias_mention;
    ag_link.appendChild(mention_span);
    // add ag-divider--vertical to ag-link
    var ag_divider = document.createElement("div");
    ag_divider.setAttribute("class", "ag-divider--vertical");
    ag_link.appendChild(ag_divider);
    // add score to ag-link
    var score = document.createElement("span");
    score.innerHTML = alias_score;
    ag_link.appendChild(score);

}

function fill_html_with_json(json_data, result_alias_type, reply_type) {
    var inner_dict = json_data[reply_type];
    var alias_list = inner_dict["alias_list"];
    var j;
    var len = alias_list.length;
    if (result_alias_type == "coref_alias_result") {
        raw_coref_chains = inner_dict["raw_chains"];
    } else if (result_alias_type == "prompt_alias_result") {
        pormpt_alias_result = inner_dict;
    }
    for (j = 0; j < len; j++) {
        if (j > top_k) {
            break;
        }
        addElementSpan(result_alias_type, alias_list[j]["text"], alias_list[j]["score"]);
    }
    // add empty introduction
    if (len == 0) {
        add_empty_introduction(result_alias_type)
    }
}

function change_timeline_node(result_alias_type, new_img_name) {
    var parent_id = result_alias_type + "_timeline_node";
    var parent = document.getElementById(parent_id);
    var inner = '<img class="icon1" referrerPolicy="no-referrer" src="/static/' + new_img_name;
    parent.innerHTML = inner + '"/>';

}

function onClickCorefChain(alias_mention) {
    var raw_chains = raw_coref_chains;
    openModal();
    // fill the content with coref chain
    var i, j, m;
    var src_mention;
    var tgt_mention;
    var coref_document;
    var coref_mention_pair;
    for (i = 0; i < raw_chains.length; i++) {
        var raw_chain = raw_chains[i];
        var mention_pair = raw_chain["coref_chain"];
        for (j = 0; j < mention_pair.length; j++) {
            if (mention_pair[j]["text"] == alias_mention) {
                tgt_mention = mention_pair[j];
                // some coref_chain has 3 mentions or more
                var init_idx = (mention_pair.length + 1) % mention_pair.length;
                src_mention = mention_pair[init_idx];
                // var k;
                // for (k = 0; k < mention_pair.length; k++) {
                //     if (mention_pair[k]["text"].toLowerCase() == entity_name) {
                //         src_mention = mention_pair[k];
                //     }
                // }
                coref_document = raw_chain["document"];
                coref_mention_pair = mention_pair;
                break;
            }
        }
        if (src_mention) {
            break;
        }
    }
    // concat the document and add　<b>  to the mention
    var final_coref_text = "";
    var separator = "";
    if (lang == "EN") {
        separator = ' ';
    }
    for (i = 0; i < coref_document.length; i++) {
        var sentence = coref_document[i];
        for (j = 0; j < sentence.length; j++) {
            // if (src_mention) {
            //     final_coref_text = checkMentionSpanEnd(i, j, src_mention, final_coref_text);
            // }
            // if (tgt_mention) {
            //     final_coref_text = checkMentionSpanEnd(i, j, tgt_mention, final_coref_text);
            // }
            for (m = 0; m < coref_mention_pair.length; m++) {
                final_coref_text = checkMentionSpanEnd(i, j, coref_mention_pair[m], final_coref_text);
            }
            final_coref_text = final_coref_text + sentence[j] + separator;
        }
    }

    document.getElementById('coref_text').innerHTML = final_coref_text;
    // head line
    document.getElementById('modal_head_text').innerHTML = "Source document from Wikipedia";
}


function checkMentionSpanEnd(i, j, mention, final_coref_text) {
    if (i == mention["sentenceIndex"]) {
        if (mention["beginIndex"] == j) {
            // is Start
            // final_coref_text += "<u><b>";
            final_coref_text += "<a style=\"color:#F00\">";
        } else {
            if (mention["endIndex"] == j) {
                // is End
                // final_coref_text += "</b></u>";
                final_coref_text += "</a>";
            }
        }
    }

    return final_coref_text;
}

function onClickAlias(alias_mention) {
    openModal();
    // fill the content with types
    var alias_list = pormpt_alias_result["alias_list"];
    var i, j;
    // concat the document and add　types
    var final_coref_text = "";
    var types = [];
    for (i = 0; i < alias_list.length; i++) {
        var alias_dict = alias_list[i];
        if (alias_mention == alias_dict["text"]) {
            types = alias_dict["types"];
            break;
        }
    }
    // display the types
    if (types.length == 1) {
        final_coref_text += "The source type of this alias mention is:<br>";
    } else {
        final_coref_text += "The source types of this alias mention are:<br>";
    }
    final_coref_text += "<ul>";
    for (j = 0; j < types.length; j++) {
        final_coref_text += "<li>";
        final_coref_text += types[j];
        final_coref_text += ":";
        final_coref_text += alias_type2explain[types[j]];
        final_coref_text += "</li>";
    }
    final_coref_text += "</ul>";
    document.getElementById('coref_text').innerHTML = final_coref_text;
    // head line
    document.getElementById('modal_head_text').innerHTML = "Explanation of alias types";
}

function openModal() {
    var coref_modal = document.getElementById('coref_modal');
    coref_modal.style.display = "block";
    // Gets the element that closes the popover
    var span = document.querySelector('.close');
    // Click (x) to close the popover
    span.onclick = function () {
        coref_modal.style.display = "none";
    }
    // Close the popover when the user clicks somewhere else
    window.onclick = function (event) {
        if (event.target == coref_modal) {
            coref_modal.style.display = "none";
        }
    }
}

function add_empty_introduction(result_alias_type) {
    document.getElementById(result_alias_type).setAttribute('class', "empty-introduction");
    document.getElementById(result_alias_type).innerText = "There is no alias result for this source.";
}


function ensemble_alias_results(dict_alias_res_dict, coref_alias_res_dict, prompt_alias_res_dict) {
    var resources = [dict_alias_res_dict, coref_alias_res_dict, prompt_alias_res_dict];
    var i, j, text, score;
    var text2freq = {};
    // count the frequency
    for (i = 0; i < resources.length; i++) {
        var res_dict = resources[i];
        var alias_list = res_dict["alias_list"];
        for (j = 0; j < alias_list.length; j++) {
            text = alias_list[j]["text"];
            score = alias_list[j]["score"];
            if (text in text2freq) {
                text2freq[text] += score;
            } else {
                text2freq[text] = score;
            }
        }
    }
    // deep copy
    var _text2freq = JSON.parse(JSON.stringify(text2freq));
    // sort
    var sorted_text2freq = Object.keys(text2freq).sort(function (a, b) {
        return text2freq[b] - text2freq[a]
    });
    // display ensemble result
    var k;
    i = 0;
    for (k in sorted_text2freq) {
        if (i > top_k) {
            break;
        }
        addElementSpan("ensemble_alias_result", sorted_text2freq[k], _text2freq[sorted_text2freq[k]]);
        i++;
    }
    change_timeline_node("ensemble_alias_result", "timeline_finish.png");
}

function check_ensemble_alias(inner_dict, result_alias_type) {
    // ensemble the results
    result_alias_type2alias_res_dict[result_alias_type] = inner_dict;
    var k;
    for (k in result_alias_type2alias_res_dict) {
        if (result_alias_type2alias_res_dict[k] == null) {
            return;
        }
    }
    var dict_alias_res_dict = result_alias_type2alias_res_dict["dict_alias_result"];
    var coref_alias_res_dict = result_alias_type2alias_res_dict["coref_alias_result"];
    var prompt_alias_res_dict = result_alias_type2alias_res_dict["prompt_alias_result"];
    ensemble_alias_results(dict_alias_res_dict, coref_alias_res_dict, prompt_alias_res_dict);

    // init again when finish
    result_alias_type2alias_res_dict = {
        "dict_alias_result": null,
        "coref_alias_result": null,
        "prompt_alias_result": null,
    }
}

function onSuggestSearch(input_entity) {
    var entity_html = document.getElementById('entity');
    entity_html.setAttribute('value', input_entity);
    onNameSubmit();
}

$('#entity').on('keypress', function (event) {

    if (event.keyCode == 13) {
        // key event is enter
        onNameSubmit();
        return false;
    }
});

//activate chinese
$(".tab_btn.ch").on('click', function () {
    $('.tab_tag').removeClass('active');
    var entity = document.getElementById('entity');
    entity.setAttribute("placeholder", "输入实体词");
});
//default english
$(".tab_btn.en").on('click', function () {
    $('.tab_tag').addClass('active');
    var entity = document.getElementById('entity');
    entity.setAttribute("placeholder", "Enter entity name");
});

