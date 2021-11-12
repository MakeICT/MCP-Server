var video = document.querySelector("#videoElement");
var frontCamera = false;
var cameraCount = 0;
var resultCanvas = document.getElementById('resultCanvas');
var videoContainer = document.getElementById('videoContainer');
var resultContext = resultCanvas.getContext('2d');
var crosshairCanvas = document.getElementById('crosshairCanvas');
var crosshairContext = crosshairCanvas.getContext('2d');
var snapshotButton = document.getElementById("snap");
var retakeButton = document.getElementById("retake");
var mirrorButton = document.getElementById("mirror");
var flipButton = document.getElementById("flip");
var x,y,crop_height,crop_width = 0;

function setupCrosshair() {
  console.log(video.videoWidth, video.videoHeight);
  crosshairCanvas.width = video.videoWidth;
  crosshairCanvas.height = video.videoHeight;
  crop_width = 600;
  crop_height = 600;
  x = (video.videoWidth - crop_width) * 0.5;
  y = (video.videoHeight - crop_height) * 0.5;
  aspectRatio = video.videoWidth/video.videoHeight;

  // Adjust video and crosshair containers based on video dimensions
  console.log("aspectRatio: ", aspectRatio);
  if (Math.abs(aspectRatio - 1) < 0.1)
    videoContainer.classList = "embed-responsive embed-responsive-1by1";
  else if (Math.abs(aspectRatio - 1.3333) < 0.1)
    videoContainer.classList = "embed-responsive embed-responsive-4by3";
  else if (Math.abs(aspectRatio - 1.7777) < 0.1)
    videoContainer.classList = "embed-responsive embed-responsive-16by9";
  else if (Math.abs(aspectRatio - 2.3333) < 0.1)
    videoContainer.classList = "embed-responsive embed-responsive-21by9";
  else if (aspectRatio < 1)
    crosshairCanvas.classList.remove("w-100");
  else if (aspectRatio > 1)
    crosshairCanvas.classList.remove("h-100");

  // Draw alignment crosshair
  crosshairContext.strokeStyle = 'rgba(0, 255, 0, 0.5)';
  crosshairContext.lineWidth = 10;
  crosshairContext.beginPath();
  crosshairContext.rect(x, y, crop_width, crop_height);
  crosshairContext.stroke();
  crosshairContext.beginPath();
  crosshairContext.arc(video.videoWidth/2, video.videoHeight/2, 5, 0, 2*Math.PI);
  crosshairContext.stroke();
}

function showResult() {
  video.hidden = true;
  crosshairCanvas.hidden = true;
  resultCanvas.hidden = false;
  snapshotButton.hidden = true;
  retakeButton.hidden = false;
  resultCanvas.width  = crop_width;
  resultCanvas.height = crop_height;

  resultContext.drawImage(video, x, y, crop_width, crop_height, 0, 0, crop_width, crop_height);

  var dataURL = resultCanvas.toDataURL("image/png");
  console.log(dataURL);
}

function showCamera() {
  video.hidden = false;
  crosshairCanvas.hidden = false;
  resultCanvas.hidden = true;
  snapshotButton.hidden = false;
  retakeButton.hidden = true;
}

function setupCamera(useFrontCamera) {

  if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
    console.log("enumerateDevices() not supported.");
    return;
  }
  
  cameraCount = 0;
  // List cameras and microphones.
  navigator.mediaDevices.enumerateDevices()
  .then(function(devices) {
    console.log(devices);
    devices.forEach(function(device) {
      if (device.kind === "videoinput") {
        cameraCount++;
        console.log(cameraCount);
        console.log(device.kind + ": " + device.label +
                    " id = " + device.deviceId);
      }
    });
    if (cameraCount < 2) {
      flipButton.hidden = true;
      console.log("hiding flip button: ", cameraCount )
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
        facingMode: {ideal: useFrontCamera ? "user" : "environment"} 
      },
    }

  navigator.mediaDevices.getUserMedia(constraints)
    .then(function (stream) {
      video.srcObject = stream;
    })
    .catch(function (error) {
      console.log("Something went wrong!");
      console.log(error);
    });
  }

}
// Wait until video stream has loaded before setting up crosshair
video.addEventListener('loadedmetadata', function(){
  console.log('loadedmetadata', video.videoWidth, video.videoHeight);
  setupCrosshair();
}, false);

function releaseCamera() {
  console.log(video.srcObject.getTracks());
  // video.srcObject.getTracks()[0].stop();
  video.srcObject.getTracks().forEach(function(track) {
    track.stop();
  })
}

// Trigger photo take
document.getElementById('snap').addEventListener('click', function() {
  showResult();
});

// Retake photo
document.getElementById('retake').addEventListener('click', function() {
  showCamera();
});

// Set up camera
document.getElementById('photo_button').addEventListener('click', function() {
  setupCamera(frontCamera);
});

// Invert image
var mirrorEnabled = false;
document.getElementById('mirror').addEventListener('click', function() {
  var v = document.getElementById("videoElement");
  // mirrorButton.press
  if(!mirrorEnabled) {
    v.style.setProperty("transform", "scaleX(-1)");
  }
  else {
    v.style.setProperty("transform", "scaleX(1)");
  }
  mirrorEnabled = !mirrorEnabled;
});

// Switch camera
document.getElementById('flip').addEventListener('click', function() {
  var v = document.getElementById("videoElement");
  releaseCamera();
  frontCamera = !frontCamera;
  setupCamera(frontCamera);
});

// Close video stream when modal is hidden
$('#cameraModal').on('hidden.bs.modal', function () {
  console.log("Camera modal closed");
  releaseCamera();
});