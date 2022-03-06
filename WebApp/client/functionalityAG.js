var requestUrl = "/alias";
var homeUrl = "http://103.238.162.32:5314/"; // place here the URL to the server

function sendRequest1(jsonObj) {
    document.getElementById("alias_result").innerHTML = "waiting";
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
            document.getElementById("alias_result").textContent = JSON.stringify(data);
        }
    });
}

function onEntityNameSubmit() {
    var entity = $("#entity").val();
    var lang = $("input[name='lang']:checked").val();
    // send the server the entity name:
    var clientId = 1;
    var type = "abbreviation";
    sendRequest1({
        "clientId": clientId,
        "request_get_prompt_alias": {},
        "entity": entity,
        "lang": lang,
        "type": type
    })
}

