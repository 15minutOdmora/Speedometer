from speedometer.video import VideoPlayer

""" Testing saved videos
videos path:
"""
#  r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\"

# video = VideoPlayer("rtsp://liammislej1:nekogeslo976@192.168.64.116:554/stream2", fps=15)
# video.record("test.mp4", 10)
# video.play()




import cv2
import os
import time
# os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

# video = VideoPlayer(0, fps=15, rotate=True)
# video.play()
                                                                            # , cv2.CAP_FFMPEG
#cap = cv2.VideoCapture("rtsp://liammislej1:nekogeslo976@192.168.64.116:554/stream2")
"""fps = int(cap.get(cv2.CAP_PROP_FPS))
print(fps)
ct = 0
start = time.time()
while True:
    ct += 1
    print(ct, time.time() - start)
    ret, frame = cap.read()
    if ret is False:
        print("Frame is empty")
        break
    else:
        cv2.imshow('VIDEO', frame)
        cv2.waitKey(1)"""
