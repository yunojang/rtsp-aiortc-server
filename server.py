import json
import os
import asyncio
import fractions
import time
from typing import Tuple

import cv2
from av import VideoFrame
from av.frame import Frame

from aiohttp import web
from aiohttp_middlewares import cors_middleware
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
# from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

ROOT = os.path.dirname(__file__)
pcs = set()

"""
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4
rtsp://admin:s1234567@10.1.1.153:554/ISAPI/streaming/channels/102
"""

DEFAULT_URL = 'rtsp://admin:s1234567@10.1.1.153:554/ISAPI/streaming/channels/102'

AUDIO_PTIME = 0.020  # 20ms audio packetization
VIDEO_CLOCK_RATE = 90000
VIDEO_PTIME = 1 / 30  # 30fps
VIDEO_TIME_BASE = fractions.Fraction(1, VIDEO_CLOCK_RATE)

class MediaStreamError(Exception):
    pass

# class VideoStreamTrack(MediaStreamTrack):
#     """
#     A dummy video track which reads green frames.
#     """

#     kind = "video"

#     _start: float
#     _timestamp: int

#     async def next_timestamp(self) -> Tuple[int, fractions.Fraction]:
#         if self.readyState != "live":
#             raise MediaStreamError

#         if hasattr(self, "_timestamp"):
#             self._timestamp += int(VIDEO_PTIME * VIDEO_CLOCK_RATE)
#             wait = self._start + (self._timestamp / VIDEO_CLOCK_RATE) - time.time()
#             await asyncio.sleep(wait)
#         else:
#             self._start = time.time()
#             self._timestamp = 0
#         return self._timestamp, VIDEO_TIME_BASE

#     async def recv(self) -> Frame:
#         """
#         Receive the next :class:`~av.video.frame.VideoFrame`.

#         The base implementation just reads a 640x480 green frame at 30fps,
#         subclass :class:`VideoStreamTrack` to provide a useful implementation.
#         """
#         pts, time_base = await self.next_timestamp()
#         cap = cv2.VideoCapture(DEFAULT_URL)
#         ret, img = cap.read()

#         # frame = VideoFrame(width=640, height=480)
#         frame = VideoFrame.from_image(Image.fromarray(img))
#         for p in frame.planes:
#             p.update(bytes(p.buffer_size))
#         frame.pts = pts
#         frame.time_base = time_base
#         return frame

class VideoStreamTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, url = DEFAULT_URL):
        super().__init__()  # don't forget this!
        self.url = url
        self.cap = cv2.VideoCapture(url)
        # self.transform = transform

    async def next_timestamp(self) -> Tuple[int, fractions.Fraction]:
      if self.readyState != "live":
          raise MediaStreamError

      if hasattr(self, "_timestamp"):
          self._timestamp += int(VIDEO_PTIME * VIDEO_CLOCK_RATE)
          wait = self._start + (self._timestamp / VIDEO_CLOCK_RATE) - time.time()
          await asyncio.sleep(wait)
      else:
          self._start = time.time()
          self._timestamp = 0
      return self._timestamp, VIDEO_TIME_BASE

    async def recv(self):
        # frame = await self.track.recv()

        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()

        # vf = VideoFrame.from_image(Image.fromarray(frame))
        vf = VideoFrame.from_ndarray(frame, format='bgr24')
        vf.pts = pts
        vf.time_base = time_base
        return vf

# def capture(url = DEFAULT_URL):
#   cap = cv2.VideoCapture(url)
#   # length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#   width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#   height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#   fps = int(cap.get(cv2.CAP_PROP_FPS))

#   codec = cv2.VideoWriter_fourcc(*'MJPG')
#   video = cv2.VideoWriter('out.avi', codec, fps, (width, height));

#   while True:
#     ret, frame = cap.read()

#     if not ret:
#       break

#     inversed = ~frame
#     video.write(inversed)
#     cv2.imshow('inversed', inversed)

#     if cv2.waitKey(10) == 27:
#       break

#   cap.release()
#   cv2.destroyAllWindows()

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("datachannel")
    def on_channel(channel):
      @channel.on('message')
      def on_message(message):
        channel.send(message)
        # pc.addTrack(VideoStreamTrack(message))

    # @pc.on("track")
    # def on_track(track):
      # print('@@on_track', track)
    pc.addTrack(VideoStreamTrack(params["url"]))

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
    app = web.Application(middlewares=[cors_middleware(allow_all=True)]);
    app.router.add_get("/", index)
    app.router.add_get("/app.js", js)
    app.router.add_post("/offer", offer);
    web.run_app(
      app, port=8889
    )