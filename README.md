# Speedometer 

A Python project for tracking vehicles and measuring their approximate speeds from a still camera video feed. Using OpenCV for image manipulation.

## How it works

Lets say you have a still video of a road where cars drive by and you'd like to measure their speeds. This project simplifies some steps for doing so. For acctually measuring speeds with some accuracy we will need the measured distance(in real life) between two points on that road, that is also going to be the measuring area. 

The project consists of three main classes:
- VideoPlayer: For reading the video feed, displaying and other video related settings
- ObjectTracking: For tracking objects based on different settings and video manipulations(such as background substractions)
- Radar: Calculating object speeds, saving and displaying their data, setting the measuring area and real life distances

**Design pattern:**

The design pattern used is an Observer type with an added Mediator class. Having three types of classes: 
- Subject: Main class that notifies observers and mediators
- Mediator: Listens to the subject class for notifications, passes them on to observers
- Observer: Waits for notifications from either subject or mediator

In our case the VideoPlayer is the subject emmiting notifications. The ObjectTaracking object then wraps the video player and is wrapped by the Timer object. 

![Picture Subject-Mediator-Observer]()

Notifications are just method calls from the subject to all observers/mediators. In our case we notify the listeners once every frame is loaded and set. 

### VideoPlayer

Video player uses the OpenCV module for reading video frames and other settings. 

We initialize the VideoPlayer by passing a video path:

```python
video = VideoPlayer(path)
```

Contrary to the variable name, the path can be the following:
- Intiger number 0 or 1 for reading video from the machine, same as on OpenCV
- String of the absulute path of the video or folder containing videos
- List consisting of strings that are absolute paths of videos
- String rtsp url path for reading live feed from camera

**Attributes:**

- fps: We set this if we know the frames per second of the video, if not set it uses the cv2 method for reading the fps(prone to errors).
- roi: Region Of Interest, this is used by the ObjectTracking class and is set by a pair of points(upper left corner and bottom left corner of the roi rectangle)
- resize: Pre-set to (640, 360), this is used for resizing the video, making it smaller improves the speed of object tracking
- rotate: For rotating the video frames, timer only works on objects moving horrizontaly, this is used if the video feed is capturing objects moving vertically
- display: Pre-set to True, if the video feed should be displayed to the screen

**Methods:**

**select_roi(kwargs)**

This method opens a video frame and you can then set the roi manually using the mouse.

kwargs consist of these possible parameters:
- frmes: At wich frame should the video be opened
- min: At wich minute should the video be opened
  - sec: At wich second should the video be opened, used with min
- save: boolean value if the selected roi should be saved to a saved_data.json file for latter use

If we save the roi, next time we initialize the VideoPlayer it automatically searches for the saved roi if it isn't set. 

**record(filename, sec, codec, fps):**

This will record the given amout of seconds and save it to a file. 

- filename: filename or path of the video to be saved, extension should match the codec
- sec: seconds of video to record
- codec: type of codec to use, preset to mp4v
- fps: the fps of the video

**play(start_seconds):**

This will play the video or connect to the live feed. If we are playing a video we can set the start seconds. 
This should be used after initializing the ObjectTracking and Timer objects. 


## Example: A week of approximate car speeds on a school road 

In this example I've set up a cheap home security cam(Tapo c100) at my neighburs balcony. The Tapo cam offers a rtsp stream wich I used. The balcony directly overlooks the road next to the apartment building I live in. The road is a school road, meaning, the speed limit is 30km/h. 

I've then downloaded the project to my Raspberry Pi 4B, and connected the Pi to the same wifi network the security camera uses. 

The setup looks like this: 

<p float="left">
  <img src="/Example/pics/tapocam.png" width="100" />
  <img src="/Example/pics/raspberrypi.png" width="200" /> 
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

