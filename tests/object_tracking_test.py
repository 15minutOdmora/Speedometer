from speedometer.video import VideoPlayer
from speedometer.timer import Timer
from speedometer.object_tracking import ObjectTracking

video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
obt = ObjectTracking(video)
video.play(start_seconds=49)

