var requestUrl = "/alias";
var homeUrl = "http://103.238.162.32:5314/"; // place here the URL to the server
var raw_coref_chains;

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
            fill_html_with_json(JSON.parse(data), result_alias_type, reply_type);
            change_timeline_node(result_alias_type, "timeline_finish.png");
        }
    });
}

function clearAll() {
    var parent_id_list = ["dict_alias_result", "coref_alias_result", "prompt_alias_result"];
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
    // var lang = $("input[name='lang']:checked").val();
    // var alias_type = $("#alias_type").val();
    var lang = "ch";
    var alias_type = "all";
    // send the server the entity name:
    var clientId = 1;
    clearAll();
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


function addElementSpan(inner_dict, parent_id, alias_mention, alias_score) {
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
    }
    for (j = 0; j < len; j++) {
        if (j > 5) {
            break;
        }
        addElementSpan(inner_dict, result_alias_type, alias_list[j], j);
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
    // fill the content with coref chain
    var i, j;
    var src_mention;
    var tgt_mention;
    var coref_document;
    for (i = 0; i < raw_chains.length; i++) {
        var raw_chain = raw_chains[i];
        var mention_pair = raw_chain["coref_chain"];
        for (j = 0; j < mention_pair.length; j++) {
            if (mention_pair[j]["text"] == alias_mention) {
                src_mention = mention_pair[1 - j];
                tgt_mention = mention_pair[j];
                coref_document = raw_chain["document"];
                break;
            }
        }
        if (src_mention) {
            break;
        }
    }
    // concat the document and add　<b>  to the mention
    var final_coref_text = "";
    for (i = 0; i < coref_document.length; i++) {
        var sentence = coref_document[i];
        for (j = 0; j < sentence.length; j++) {
            final_coref_text = checkMentionSpanEnd(i, j, src_mention, final_coref_text);
            final_coref_text = checkMentionSpanEnd(i, j, tgt_mention, final_coref_text);
            final_coref_text = final_coref_text + sentence[j];
        }
    }

    document.getElementById('coref_text').innerHTML = final_coref_text;
}


function checkMentionSpanEnd(i, j, mention, final_coref_text) {
    if (i == mention["sentenceIndex"]) {
        if (mention["beginIndex"] == j) {
            // is Start
            final_coref_text += "<b>";
        } else {
            if (mention["endIndex"] == j) {
                // is End
                final_coref_text += "</b>";
            }
        }
    }

    return final_coref_text;
}