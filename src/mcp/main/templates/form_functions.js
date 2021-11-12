const file_field = {
  video: document.getElementById("videoElement"),
  frontCamera: false,
  cameraCount: 0,
  resultCanvas: document.getElementById('resultCanvas'),
  crosshairCanvas: document.getElementById('crosshairCanvas'),
  videoContainer: document.getElementById('videoContainer'),
  cameraModalButton: document.getElementById("photo_button"),
  snapshotButton: document.getElementById("snap"),
  retakeButton: document.getElementById("retake"),
  mirrorButton: document.getElementById("mirror"),
  flipButton: document.getElementById("flip"),
  x:0,
  y:0,
  crop_height: 600,
  crop_width: 600,
};

// let fileFieldInst = new file_field();

function setupCrosshair(ff) {
  var crosshairContext = ff.crosshairCanvas.getContext('2d');
  console.log(ff.video.videoWidth, ff.video.videoHeight);
  ff.crosshairCanvas.width = ff.video.videoWidth;
  ff.crosshairCanvas.height = ff.video.videoHeight;
  ff.x = (ff.video.videoWidth - ff.crop_width) * 0.5;
  ff.y = (ff.video.videoHeight - ff.crop_height) * 0.5;
  aspectRatio = ff.video.videoWidth/ff.video.videoHeight;

  // Adjust video and crosshair containers based on video dimensions
  console.log("aspectRatio: ", aspectRatio);
  if (Math.abs(aspectRatio - 1) < 0.1) {
    ff.videoContainer.classList.add("embed-responsive-1by1");
  }
  else if (Math.abs(aspectRatio - 1.3333) < 0.1) {
    ff.videoContainer.classList.add("embed-responsive-4by3");
  }
  else if (Math.abs(aspectRatio - 1.7777) < 0.1) {
    ff.videoContainer.classList.add("embed-responsive-16by9");
  }
  else if (Math.abs(aspectRatio - 2.3333) < 0.1) {
    ff.videoContainer.classList.add("embed-responsive-21by9");
  }
  else {
    ff.videoContainer.classList.add("embed-responsive-1by1");
    if (aspectRatio < 1)
      ff.crosshairCanvas.classList.remove("w-100");
    else if (aspectRatio > 1)
      ff.crosshairCanvas.classList.remove("h-100");
  }

  // Draw alignment crosshair
  console.log(ff.x, ff.y, ff.crop_width, ff.crop_height)
  crosshairContext.strokeStyle = 'rgba(0, 255, 0, 0.5)';
  crosshairContext.lineWidth = 10;
  crosshairContext.beginPath();
  crosshairContext.rect(ff.x, ff.y, ff.crop_width, ff.crop_height);
  crosshairContext.stroke();
  crosshairContext.beginPath();
  crosshairContext.arc(ff.video.videoWidth/2, ff.video.videoHeight/2, 5, 0, 2*Math.PI);
  crosshairContext.stroke();
}

function showResult(ff) {
  var resultContext = ff.resultCanvas.getContext('2d');

  ff.video.hidden = true;
  ff.crosshairCanvas.hidden = true;
  ff.resultCanvas.hidden = false;
  ff.snapshotButton.hidden = true;
  ff.retakeButton.hidden = false;
  ff.resultCanvas.width  = ff.crop_width;
  ff.resultCanvas.height = ff.crop_height;

  resultContext.drawImage(ff.video, ff.x, ff.y, ff.crop_width, ff.crop_height, 0, 0, ff.crop_width, ff.crop_height);

  var dataURL = ff.resultCanvas.toDataURL("image/png");
  // console.log(dataURL);s
}

function showCamera(ff) {
  ff.video.hidden = false;
  ff.crosshairCanvas.hidden = false;
  ff.resultCanvas.hidden = true;
  ff.snapshotButton.hidden = false;
  ff.retakeButton.hidden = true;
}

function setupCamera(ff) {

  if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
    console.log("enumerateDevices() not supported.");
    return;
  }
  
  ff.cameraCount = 0;
  // List cameras and microphones.
  navigator.mediaDevices.enumerateDevices()
  .then(function(devices) {
    console.log(devices);
    devices.forEach(function(device) {
      if (device.kind === "videoinput") {
        ff.cameraCount++;
        console.log(ff.cameraCount);
        console.log(device.kind + ": " + device.label +
                    " id = " + device.deviceId);
      }
    });
    if (ff.cameraCount < 2) {
      ff.flipButton.hidden = true;
      console.log("hiding flip button: ", ff.cameraCount )
    }
  })
  .catch(function(err) {
    console.log(err.name + ": " + err.message);
  });
  
  
  let supports = navigator.mediaDevices.getSupportedConstraints();
  console.log(supports);
  if (!supports["width"] || !supports["height"] || !supports["frameRate"] || !supports["facingMode"]) {
    console.log("ERROR!");
  } 

  if (navigator.mediaDevices.getUserMedia) {
    var constraints = {
      audio: false,
      video: { 
        width: 1280, 
        height: 960, 
        facingMode: {ideal: ff.frontCamera ? "user" : "environment"} 
      },
    }

  navigator.mediaDevices.getUserMedia(constraints)
    .then(function (stream) {
      ff.video.srcObject = stream;
    })
    .catch(function (error) {
      console.log("Something went wrong!");
      console.log(error);
    });
  }

}
// Wait until video stream has loaded before setting up crosshair
file_field.video.addEventListener('loadedmetadata', function(){
  console.log('loadedmetadata', file_field.video.videoWidth, file_field.video.videoHeight);
  setupCrosshair(file_field);
}, false);

function releaseCamera(ff) {
  console.log(ff.video.srcObject.getTracks());
  // ff.video.srcObject.getTracks()[0].stop();
  ff.video.srcObject.getTracks().forEach(function(track) {
    track.stop();
  })
}

// Trigger photo take
file_field.snapshotButton.addEventListener('click', function() {
  showResult(file_field);
});

file_field.crosshairCanvas.addEventListener('click', function() {
  showResult(file_field);
});

// Retake photo
file_field.retakeButton.addEventListener('click', function() {
  showCamera(file_field);
});
file_field.resultCanvas.addEventListener('click', function() {
  showCamera(file_field);
});

// Set up camera
file_field.cameraModalButton.addEventListener('click', function() {
  setupCamera(file_field);
});

// Invert image
var mirrorEnabled = false;
file_field.mirrorButton.addEventListener('click', function() {
  if(!mirrorEnabled) {
    file_field.video.style.setProperty("transform", "scaleX(-1)");
  }
  else {
    file_field.video.style.setProperty("transform", "scaleX(1)");
  }
  mirrorEnabled = !mirrorEnabled;
});

// Switch camera
file_field.flipButton.addEventListener('click', function() {
  releaseCamera(file_field);
  file_field.frontCamera = !file_field.frontCamera;
  setupCamera(file_field);
});

// Close video stream when modal is hidden
$('#cameraModal').on('hidden.bs.modal', function () {
  console.log("Camera modal closed");
  releaseCamera(file_field);
});

function syncFilename(fileFieldId) {
  var doc = document.getElementById(fileFieldId).files[0].name;
  document.getElementById(fileFieldId + '_fn').innerHTML = doc;
}