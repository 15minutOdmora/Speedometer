**This README file is still in process**

# Speedometer 

A Python project for tracking vehicles and measuring their approximate speeds from a still camera video feed. Using OpenCV for image manipulation.

## Example: 10 days of approximate car speeds on a school road 

In this example I've set up a cheap home security cam(Tapo c100) at my neighburs balcony. The Tapo cam offers a rtsp stream wich I used. The balcony directly overlooks the road next to the apartment building I live in. The road is a school road, meaning, the speed limit is 30km/h. 

I've then downloaded the project to my Raspberry Pi 4B, and connected the Pi to the same wifi network the security camera uses. 

The setup looks like this: 

<p float="left">
  <img src="/Example/pics/tapocam.jpg" width="200" align="center"/>
  <img src="/Example/pics/raspberrypi.jpg" width="200" align="center"/> 
</p>

On my RPi I then created the <code>main.py</code> file, where everything is going to be set and ran. I then imported the three classes and needed and check if the stream works by passing the rtsp url and playing:

```python
# main.py file
from speedometer import VideoPlayer, ObjectTracking, Radar

rtsp_url = "MyUrlToCam"
video = VideoPlayer(rtsp_url)

video.play()
```

Displayed window from camera: 

![Pic of road from Tapo cam](/Example/pics/pic_of_road_from_tapo_cam.png)

Knowing it works I can then set the other settings. 
I know the Tapo cam records in 15 fps, and I'd like the windows to be resized to (640, 360) wich is the preset. Objects are moving horizontally so I don't need to rotate the video. 

The Region Of Interest(roi for short) is automatically set to the whole frame, but in this case we only need to look at the road. We can set the roi by using the select_roi method, this will then open a window where we can set the roi rectangle using a mouse. Setting the save parameter to True will save the roi to a json file we can use later(so we dont have to always set the roi, or write it by hand)

```python
# main.py file
from speedometer import VideoPlayer, ObjectTracking, Radar

rtsp_url = "MyUrlToCam"
video = VideoPlayer(rtsp_url, fps=15)

video.select_roi(save=True)

video.play()
```

Select roi window:

![Select roi frame](/Example/pics/select_roi_frame.png)


We can now set the ObjectTracking, initializing it by passing the video instance: 

Also configuring some limitations on objects, such as maximum size and minimum size, I know by other tests that the average size of a car is about 4000 pixels(surface so it's squared pixels) in this case. By setting this limitation we ignore all the false positive objects that are detected. 

```python
# main.py file
from speedometer import VideoPlayer, ObjectTracking, Radar

rtsp_url = "MyUrlToCam"
video = VideoPlayer(rtsp_url, fps=15)

# video.select_roi(save=True)  comment this out as it is already set

obt = ObjectTracking(video)
obt.maximum_object_size = 10000  # Maximum size of detected object in px^2
obt.minimum_object_size = 500  # # Minimum size of detected object in px^2

video.play()
```

Cars and objects now get detected, below is a frame from video of a detected object:

![Pic of road from Tapo cam w detected object](/Example/pics/detected_object.png)


By going outside I then measured the distance between the two trees shown in the picture below, which was about 13,85m. I then set the measuring area, wich is set by two lines. 
I can set the measuring are by passing two lines to the Radar class or I can use one of the methods set_distance or set_two_distances. If the camera was set in a birds view the set_distance method would be used. In my case the camera is set from the side and I used the set_two_distances method, this opens a window where we can set two lines wich represent the same distance iin real life, but different distance on screen, this is used for calculating the depth perception on camera frame. 

Initializing the Radar by passing in the video object, load is set to True so the set lines and distance(irl) are later loaded from the saved_data.json file. We set print_measured to True so it prints the data from timed objects to the console. We can pass a file name to the out_file parameter to save measured data to a csv file. 

```python
# main.py file
from speedometer import VideoPlayer, ObjectTracking, Radar

rtsp_url = "MyUrlToCam"
video = VideoPlayer(rtsp_url, fps=15)

obt = ObjectTracking(video)
obt.maximum_object_size = 10000  # Maximum size of detected object in px^2
obt.minimum_object_size = 500  # # Minimum size of detected object in px^2

timer = Radar(video, load=True, print_measured=True, out_file="test.csv")
timer.set_two_distances(distance=13.85, save=True) # if save is set to True it saves the line data to saved_data.json

video.play()
```

Setting the two lines window, where I know the upper green distance is equal to the bottom one irl:

![Pic of road from Tapo cam setting line distance](/Example/pics/set_two_lines.png)

By setting two lines, if an object travels through the bottom of the screen he would travel the same distance irl as if he would travel on the top of the screen. This removes some errors by the point of view.

Everything now works and I can run the final version of the program: 

```python
# main.py file
from speedometer import VideoPlayer, ObjectTracking, Radar
video = VideoPlayer("MyUrlToCam", fps=15)
obt = ObjectTracking(video)
obt.maximum_object_size = 10000  # Maximum size of detected object in px^2
obt.minimum_object_size = 500  # # Minimum size of detected object in px^2
timer = Radar(video, load=True, print_measured=True, out_file="test.csv")
video.play()
```

The output to console after some objects were timed looked like this:

![Ex. output to console](/Example/pics/example_output_to_console.png)

I then left the RPi running for 10 days with occasional checkups. I've only used the data from 6am to 9pm, as the camera doesn'f film at night(well it does but not well enough for object detection). The data was then cleaned, removing some dates as the wind caused the camera to move, only using data from the time frame, and removing false positives. False positives happened when larger busses passed by and as they're black and white the camera detected it as multiple objects, that data was also removed. Objects under the size of 2500 sq. pixels were also removed as those were pedestrians. At the end we are left only with the measured speed of cars.

#### Analysis

After 10 days of measuring from 6am - 9pm there was a total of 8327 measured vehicles. Measured data was filtered down to the timeframe [6am, 9pm] because of false postives happening in the dark(between the hours [9pm - 6pm]). 

**Some basic data properties:** 

![Picture of data properties](/Example/pics/basic_data_properties.png)

**If we sort the data based on speed(descending):** 

![Picture of data sorted by speed](/Example/pics/data_sorted_by_speed.png)

**Infographic displaying some basic data:**

![Infographic](/Example/pics/infographic.png)
 
