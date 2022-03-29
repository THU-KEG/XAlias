var requestUrl = "/alias";
var homeUrl = "http://103.238.162.32:5314/"; // place here the URL to the server

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


function addElementSpan(parent_id, alias_mention, alias_score) {
    var parent = document.getElementById(parent_id);
    //add span
    var span = document.createElement("span");
    span.setAttribute("class", "ag-tag ag-tag--success");
    parent.appendChild(span);
    // add ag-link to span
    var ag_link = document.createElement("a");
    ag_link.setAttribute("class", "ag-link");
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
    for (j = 0; j < len; j++) {
        if (j > 5) {
            break;
        }
        addElementSpan(result_alias_type, alias_list[j], j);
    }
}

function change_timeline_node(result_alias_type, new_img_name) {
    var parent_id = result_alias_type + "_timeline_node";
    var parent = document.getElementById(parent_id);
    var inner = '<img className="icon1" referrerPolicy="no-referrer" src=' + new_img_name;
    parent.innerHTML = inner + '/>';

}