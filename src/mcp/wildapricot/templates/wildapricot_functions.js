function wa_pull(data={}) {
  // console.log(JSON.stringify(data));
  // document.getElementById("result").innerHTML = "Processing...";
  fetch('/rpc/wildapricot/pull', {
    method: 'post',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(jsonData => {document.location.reload();})
  .catch(error => console.error('Error:', error));
}

function wa_push(data={}) {
  // console.log(JSON.stringify(data));
  // document.getElementById("result").innerHTML = "Processing...";
  fetch('/rpc/wildapricot/push', {
    method: 'post',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(jsonData => {document.location.reload();})
  .catch(error => console.error('Error:', error));
}
