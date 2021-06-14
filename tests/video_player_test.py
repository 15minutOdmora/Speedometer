from speedometer.video import VideoPlayer

video = VideoPlayer("rtsp://username:password@192.168.64.116:554/stream2", fps=15)
video.record("test.mp4", 10)
video.play()
