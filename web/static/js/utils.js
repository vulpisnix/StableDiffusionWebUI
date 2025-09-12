const sendGet       = async (url = '') => {
    const response = await fetch(url||document.location.href, {
        method: 'GET',
        cache: 'no-cache'
    });

    let _rawText = await response.text();
    let _jsonData = {};
    try { _jsonData = JSON.parse(_rawText) } catch (e) {}

    return {
        "ok": response.status === 200,
        "code": response.status,
        "json": _jsonData,
        "text": _rawText
    }
}
const sendPost      = async (url = '', jsonData = {}) => {
    const csrfToken = document.head.querySelector("[name~=csrf_token][content]").content;
    const form = new FormData();
    form.append("csrfmiddlewaretoken", csrfToken);
    for(let i in jsonData) form.append(i, jsonData[i]);

    const response = await fetch(url||document.location.href, {
        method: 'POST',
        cache: 'no-cache',
        body: form,
        headers: {
            'X-CSRFToken': csrfToken
        }
    });

    let _rawText = await response.text();
    let _jsonData = {};
    try { _jsonData = JSON.parse(_rawText) } catch (e) {}

    return {
        "ok": response.status === 200,
        "code": response.status,
        "json": _jsonData,
        "text": _rawText
    }
}

const isJson = (str) => {
    try {
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
}
const getQuery = (key) => {
    let query = document.location.search;
    query = query.replace('?', '');
    let splitRAW = query.split('&');
    let split = {};
    splitRAW.forEach(raw => {
        let k = raw.split("=")[0];
        let v = raw.split("=")[1];
        split[k] = v;
    });
    if(split[key] !== undefined)
        return split[key];
    else
        return "";
}
