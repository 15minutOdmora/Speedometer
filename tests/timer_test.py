from speedometer.video import VideoPlayer
from speedometer.timer import Timer
from speedometer.object_tracking import ObjectTracking


video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
# video.select_roi(save=True)
obt = ObjectTracking(video)
timer = Timer(video)
timer.set_vertical_lines()
# video.play()
pass