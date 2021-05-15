from speedometer import VideoPlayer, ObjectTracking

video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
obt = ObjectTracking(video)
video.play(start_seconds=49)

