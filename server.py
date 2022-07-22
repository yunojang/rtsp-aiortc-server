import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid

import cv2
from aiohttp import web
from av import VideoFrame

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
# from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

ROOT = os.path.dirname(__file__)
pcs = set()

DEFAULT_URL = 'rtsp://admin:s1234567@10.1.1.153:554/ISAPI/streaming/channels/102'

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
      print('@@on_track', track)
      pc.addTrack(track)

    # handle offer
    await pc.setRemoteDescription(offer);

    # send offer
    answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    return web.Response(
      content_type = "application/json",
      text=json.dumps(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
      ),
    )

async def index(request):
  content = open(os.path.join(ROOT, "index.html"), "r").read()
  return web.Response(content_type="text/html", text=content)

async def js(req):
  content = open(os.path.join(ROOT, "app.js"), "r").read()
  return web.Response(content_type="application/javascript", text=content)

if __name__ == "__main__":
    app = web.Application();
    app.router.add_get("/", index)
    app.router.add_get("/app.js", js)
    app.router.add_post("/offer", offer);
    web.run_app(
      app, port=8889
    )