from speedometer.video import VideoPlayer
from speedometer.radar import Radar
from speedometer.object_tracking import ObjectTracking


video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
obt = ObjectTracking(video)
timer = Radar(video, load=True, print_measured=True)
# timer.set_distance(load=True)
video.play(start_seconds=1050)
# timer.set_distance(13)
# timer.set_lines(distance=10, save=True)
# timer.set_vertical_lines(save=True)
# video.play()
