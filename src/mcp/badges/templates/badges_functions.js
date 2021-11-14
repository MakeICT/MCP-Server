function get_badge_svg(userId) {
  fetch('/api/user/' + userId +'/badge', {
    method: 'get',
    headers: {'Content-Type': 'application/json'},
  })
  .then(response => response.json())
  // .then(jsonData => console.log(jsonData))
  .then(jsonData => document.getElementById('badge_svg').innerHTML = jsonData.svg)
  .catch(error => console.error('Error:', error));
}

function download_badge_svg(svg_element) {
  var svgData = svg_element.outerHTML;
  var svgBlob = new Blob([svgData], {type:"image/svg+xml;charset=utf-8"});
  var svgUrl = URL.createObjectURL(svgBlob);
  var downloadLink = document.getElementById("download");
  downloadLink.href = svgUrl;
  downloadLink.download = "badge.svg";
  document.body.appendChild(downloadLink);
  downloadLink.click();
  // document.body.removeChild(downloadLink);
}

function printElement(e) {
  var ifr = document.createElement('iframe');
  ifr.style='height: 0px; width: 0px; position: absolute'
  document.body.appendChild(ifr);

  $(e).clone().appendTo(ifr.contentDocument.body);
  ifr.contentWindow.print();

  ifr.parentElement.removeChild(ifr);
}