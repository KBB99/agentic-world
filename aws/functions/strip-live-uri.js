// CloudFront Function: strip '/live' prefix from request URI
function handler(event) {
  var request = event.request;
  var uri = request.uri || '/';
  // If requesting the live root, map to the default manifest
  if (uri === '/live' || uri === '/live/') {
    request.uri = '/index.m3u8';
    return request;
  }
  if (uri.indexOf('/live/') === 0) {
    request.uri = uri.substring(5); // remove '/live'
  }
  return request;
}