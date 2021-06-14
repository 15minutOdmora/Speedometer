from speedometer.video import VideoPlayer
from speedometer.radar import Radar
from speedometer.object_tracking import ObjectTracking


video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)

#
# video.select_roi(save=True)
obt = ObjectTracking(video)
obt.maximum_object_size = 10000
obt.minimum_object_size = 500
timer = Radar(video, load=True, print_measured=True, out_file="test")
timer.set_two_distances(distance=13.85, save=True) # Bus at 1240
video.play()

