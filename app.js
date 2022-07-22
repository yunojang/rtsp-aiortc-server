const iceConnectionLog = document.getElementById('ice-connection-state'),
  iceGatheringLog = document.getElementById('ice-gathering-state'),
  signalingLog = document.getElementById('signaling-state');

let pc;
let dc;
let stream;

function createPeerConnection() {
  // use stun?
  const config = {};
  config.iceServers = [{
    urls: ["stun:stun.l.google.com:19302",
      "stun:stun1.l.google.com:19302",
      "stun:stun2.l.google.com:19302",
      "stun:stun3.l.google.com:19302",
      "stun:stun4.l.google.com:19302",]
  }]

  pc = new RTCPeerConnection({});

  pc.addEventListener('track', evt => {
    console.log(evt)
    console.log(evt.streams[0]);
    if (evt.track.kind == 'video') {
      document.getElementById('peer').srcObject = evt.streams[0];
    } else {
      document.getElementById('audio').srcObject = evt.streams[0];
    }
  })

  pc.addEventListener('icegatheringstatechange', function () {
    iceGatheringLog.textContent += ' -> ' + pc.iceGatheringState;
  }, false);
  iceGatheringLog.textContent = pc.iceGatheringState;

  pc.addEventListener('iceconnectionstatechange', function () {
    iceConnectionLog.textContent += ' -> ' + pc.iceConnectionState;
  }, false);
  iceConnectionLog.textContent = pc.iceConnectionState;

  pc.addEventListener('signalingstatechange', function () {
    signalingLog.textContent += ' -> ' + pc.signalingState;
  }, false);
  signalingLog.textContent = pc.signalingState;

  return pc;
}

function negotiate() {
  return pc.createOffer()
    .then((offer) => {
      pc.setLocalDescription(offer);
      return fetch('/offer', {
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          url: document.querySelector('#url-input').value
        }),
        headers: {
          'Content-Type': 'application/json'
        },
        method: 'POST'
      })
    }).then(response => response.json()).then((answer) => {
      pc.setRemoteDescription(answer)
    })
}

async function connection() {
  createPeerConnection();
  dc = pc.createDataChannel('only-connect')

  stream = await navigator.mediaDevices.getUserMedia({ video: true });

  return negotiate();
}

document.querySelector('#con').addEventListener('click', connection)

async function start() {
  document.querySelector('#camera').srcObject = stream;
  pc.addTrack(stream.getTracks()[0], stream)
}
document.querySelector('#start').addEventListener('click', start)