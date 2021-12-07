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

function printBadgeSVG(svg) {
  var ifr = document.createElement('iframe');
  ifr.width = 600;
  ifr.height = 600;

  ifr.onload = function () {
    // console.log("Loaded!");
    ifr.hidden = true;
    var print_style = document.createElement('style');
    var styles = 
    `@media print {
      *{
        margin: 0;
        padding:0;
      }
      @page {
        size: 2.12in 3.38in;
        position: absolute;
        top:0px;bottom:0;right:0;left:0;
        margin: 0;
      }
      html {
        width: 100%;
        height: 100%;
      }
      svg {
        position: absolute;
        bottom:0;
      } 
    }";`
    
    print_style.appendChild(document.createTextNode(styles));
    ifr.contentDocument.head.appendChild(print_style);
    $(svg).clone().appendTo(ifr.contentDocument.body);
    ifr.contentWindow.onafterprint = function() {
      ifr.parentElement.removeChild(ifr);
    }
    ifr.contentWindow.print();
  }
  document.body.appendChild(ifr);
}

async function scanBadge(resultFieldId) {
    console.log("User clicked scan button");
    console.log(resultFieldId);
    resultField = document.getElementById(resultFieldId);
    resultField.value = "<< Scan Badge Now >>";

    try {
      const ndef = new NDEFReader();
      await ndef.scan();
      console.log("> Scan started");
      
      ndef.addEventListener("readingerror", () => {
        console.log("Argh! Cannot read data from the NFC tag. Try another one?");
        resultField.value = "!! Read Error: Try Again !!";
      });
      
      ndef.addEventListener("reading", ({ message, serialNumber }) => {
        console.log(`> Serial Number: ${serialNumber}`);
        console.log(`> Records: (${message.records.length})`);
        resultField.value = serialNumber.split(':').join('').padStart(16, '0');

        // ndef.removeEventListener(this);
    });
    } catch (error) {
      console.log("Argh! " + error);
      resultField.value = "!! Not Supported !!";
    }
}