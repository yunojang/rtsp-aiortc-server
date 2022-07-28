const iceConnectionLog = document.getElementById('ice-connection-state'),
  iceGatheringLog = document.getElementById('ice-gathering-state'),
  signalingLog = document.getElementById('signaling-state'),
  dataChannelLog = document.getElementById('data-channel');

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

  pc = new RTCPeerConnection(config);

  pc.addEventListener('track', evt => {
    console.log(evt.streams[0])
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
  return pc.createOffer({ offerToReceiveVideo: true }).then(function (offer) {
    pc.setLocalDescription(offer);
    // console.log(pc.localDescription)
  })
    .then(function () {
      // wait for ICE gathering to complete
      return new Promise(function (resolve) {
        if (pc.iceGatheringState === 'complete') {
          resolve();
        } else {
          function checkState() {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', checkState);
              resolve();
            }
          }
          pc.addEventListener('icegatheringstatechange', checkState);
        }
      });
    }).then(function () {
      var offer = pc.localDescription;

      return fetch('/offer', {
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          url: document.getElementById('url-input').value
        }),
        headers: {
          'Content-Type': 'application/json'
        },
        method: 'POST'
      });
    }).then(function (response) {
      return response.json();
    }).then(function (answer) {
      // document.getElementById('answer-sdp').textContent = answer.sdp;
      console.log(answer)
      return pc.setRemoteDescription(answer);
    }).catch(function (e) {
      alert(e);
    });
}


function connection() {
  createPeerConnection();
  dc = pc.createDataChannel('connect')
  dc.onopen = () => {
    dataChannelLog.textContent += '-open' + '\n';
  }

  dc.onmessage = (evt) => {
    dataChannelLog.textContent += '<' + evt.data + '\n';
  }

  // navigator.mediaDevices.getUserMedia({ video: true }).then(function (stream) {
  //   stream.getTracks().forEach(function (track) {
  //     pc.addTrack(track, stream);
  //     track.enabled = !track.enabled
  //   });
  //   return negotiate();
  // }, function (err) {
  //   alert('Could not acquire media: ' + err);
  // });

  return negotiate();
}

document.querySelector('#con').addEventListener('click', connection)
