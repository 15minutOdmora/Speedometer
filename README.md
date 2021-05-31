# Speedometer 

A Python project for tracking vehicles and measuring their approximate speeds from a still camera video feed. Using OpenCV for image manipulation.

## How it works

Lets say you have a still video of a road where cars drive by and you'd like to measure their speeds. This project simplifies some steps for doing so. For acctually measuring speeds with some accuracy we will need the measured distance(in real life) between two points on that road, that is also going to be the measuring area. 

The project consists of three main classes:
- VideoPlayer: For reading video feed, displaying and other video related settings
- ObjectTracking: For tracking objects based on different settings and video manipulations(such as background substraction)
- Radar: Calculating object speeds, saving and displaying their data, setting the measuring area and the irl distances

**Design pattern:**

The design pattern used is an Observer type with an added Mediator class. Having three types of classes: 
- Subject: Main class that notifies observers and mediators
- Mediator: Listenes to the subject class for notifications, passes them on to observers
- Observer: Waits for notifications from ether subject or mediator

In our case the VideoPlayer is the saubject emmiting notifications. The ObjectTaracking object then wraps the video player and is wrapped by the Timer object. 

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

- fps: We set this if we know the frames per second of the video, if not set it uses the cv2 method for reading the fps(prone for errors).
- roi: Region Of Interest, this is used by the ObjectTracking class and is set by a pair of points(upper left corner and bottom left corner of the roi rectangle)
- resize: Pre set to (640, 360), this is used for resizing the video, making it smaller improves the speed of object tracking
- rotate: For rotating the video frames, timer only works on objects moving horrizontaly, this is used if the video feed is capturing objects moving vertically
- display: Pre set to True, if the video feed should be displayed to the screen

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



## Example 
