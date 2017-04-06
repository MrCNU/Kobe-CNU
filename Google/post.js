function FBPost(text){
  var content = text;
  var content = {
  'method': 'post',
  'message': content,
  'token': token
  }
  var payload = {
    'method': 'post',
    'payload': JSON.stringify(content)
  }

  UrlFetchApp.fetch(url, payload);
}
//==========================
function poke() {
  var cuoo = UrlFetchApp.fetch(url);
}
