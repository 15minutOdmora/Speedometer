from speedometer.video import VideoPlayer
# from speedometer.radar import Radar
from speedometer.object_tracking import ObjectTracking

video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
obt = ObjectTracking(video)
video.play(start_seconds=49)

