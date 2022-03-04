function onEntityNameSubmit() {
    var entity = $("#entity").val();
    var lang = $("input[name='lang']:checked").val();
    // send the server the entity name:
    var clientId = 1;
    var type = "abbreviation";
    sendRequest({
        "clientId": clientId,
        "request_get_prompt_alias": {},
        "entity": entity,
        "lang": lang,
        "type": type
    })
}

