"""
 opencv-contrib-python version 4.2.0.34 is needed (other versions dont work for some reason)
 OpenCV trackers are useless as they're slow aff
"""
from speedometer.Observer import Subject, Observer
from speedometer.object_tracking import ObjectTracking
from speedometer.timer import Timer

from pathlib import Path
import json

import time
import cv2
import os

"""with open("globals.json", 'w') as glob:
    data = {"roi": None}
    json.dump(data, glob)"""


def open_data_file():
    """ Opens the globals.json returns the dic.
    :return: distionary
    """
    with open("saved_data.json", 'r') as glob:
        data = json.load(glob)
    return data


def save_to_data_file(key, value):
    """ Saves key value pair to globals.json
    :param key: Key
    :param value: Value
    """
    with open("saved_data.json", 'r') as glob:
        data = json.load(glob)

    data[key] = value

    with open("saved_data.json", 'w') as glob:
        json.dump(data, glob)


def mmss_to_frames(fps, m, s=0):
    """
    Converts minutes and seconds of video to frames based on fps
    :param fps: frames per second of video
    :param m: minutes
    :param s: seconds
    :return: frame number
    """
    return int((m * 60 + s) / fps)


class VideoPlayer(Subject):
    def __init__(self, video_path, fps=None, roi=None, resize=(640, 360), rotate=False):
        self.observers: list = []

        self.cv2 = cv2
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

        # Current frames the video is on, gets reset once the video goes to the next
        self._frames = 0

        # video_path is a string when initialized, converted to a list containing file_name strings by the setter
        self.video_list = video_path

        self._fps = fps

        # Check if saved_data.json exists, otherwise create it --> load roi if exists, else set to None
        if not os.path.exists("saved_data.json"):
            with open('saved_data.json', 'w') as data_file:
                data = {"roi": None}
                json.dump(data, data_file)
            self.roi = None
        else:
            if roi is None:
                # Check if global roi variable exists
                saved_data = open_data_file()
                if saved_data["roi"] is not None:
                    self.roi = saved_data["roi"]
                else:
                    self.roi = roi

        self.resize = resize

        self.rotate = rotate

        # Gets set when video is playing
        self.frame = None
        self.ret = None
        self.current_video_name = None

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject
        """
        self.observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """
        Detach observer from subject
        """
        self.observers.remove(observer)

    def notify(self) -> None:
        """
        Notify all observers, mid video
        """
        for observer in self.observers:
            observer.update()

    @property
    def video_list(self) -> list:
        return self._video_list

    @video_list.setter
    def video_list(self, video_path):
        """ TODO Checker for file extensions so it only saves (.mp4, .wav, ...)files to list
        Set the _video_list property depending on the path, we append video path to a list if a folder path is passed.
        :param video_path: Can be file name if file is in same dir., folder path, folder name if in same dir.,
                           number(0, 1) as used by cv2, or list of the above mentioned things.
        :return: None
        """
        if isinstance(video_path, list):
            self._video_list = video_path  # if list --> Does not check list content
        elif isinstance(video_path, int):
            self._video_list = [video_path]
        elif os.path.isfile(video_path):  # if file
            self._video_list = [video_path]
        elif os.path.isdir(video_path):  # if directory
            # Append every file in folder
            temp_list = []
            for file_name in os.listdir(video_path):
                absolute_path = os.path.join(video_path, file_name)
                if os.path.isfile(absolute_path):
                    temp_list.append(absolute_path)
            self._video_list = temp_list
        elif isinstance(video_path, str):  # If string assume it's a live stream url
            self._video_list = [video_path]
        else:
            raise ValueError("Invalid path.")

    @property
    def frames(self):
        return self._frames

    @frames.setter
    def frames(self, f):
        self._frames = f

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, fps):
        if fps is None:  # If fps is set to None, read fps using cv2
            vid = cv2.VideoCapture(self.video_list[0])
            self._fps = int(vid.get(self.cv2.CAP_PROP_FPS))
        else:
            self._fps = fps

    def select_roi(self, **kwargs):
        """  TODO cv2.roi prints command description after selection, should get rid of it, fix so seconds can get passed
        Opens video with a ROI selector on given frame or time set in kwargs,
        :param kwargs: frames= or min= or min= and sec=
        :return: None
        """
        keys = kwargs.keys()
        frame_number = 0
        if "frames" in keys:
            frame_number = kwargs["frames"]
        elif "min" in keys:
            min = kwargs["min"]
            sec = 0
            if "sec" in keys:
                sec = kwargs["sec"]
            frame_number = mmss_to_frames(self.fps, min, sec)

        cap = self.cv2.VideoCapture(self.video_list[0])
        cap.set(1, frame_number)  # cv2.CAP_PROP_FRAME_COUNT
        _, frame = cap.read()
        # Resize frame so roi mathches at the end
        frame = self.cv2.resize(frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        self.cv2.imshow("Select ROI", frame)
        print("Create the selecton using mouse, to save and exit press SPACE or ENTER to cancel press C")
        self.roi = self.cv2.selectROI("Select ROI", frame)
        print(self.roi)
        if "save" in keys:
            # if set to True --> save to globals.json
            if kwargs["save"]:
                save_to_data_file("roi", self.roi)
        cap.release()
        self.cv2.destroyAllWindows()

    def play_video_test(self):
        for video_path in self.video_list:
            tracker = cv2.TrackerMOSSE_create()

            cap = self.cv2.VideoCapture(video_path)
            _, frame = cap.read()

            ok = tracker.init(frame, self.roi)

            while True:
                self.frames += 1
                ok, frame = cap.read()

                ok, bbox = tracker.update(frame)

                # Draw bounding box
                if ok:
                    # Tracking success
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.cv2.imshow("Video", frame)

                # Pressing Esc key to stop
                key = cv2.waitKey(1)
                if key == 27:
                    break

    def play(self):
        """
        Starts video, displays windows
        :return: None
        """
        for video_path in self.video_list:
            cap = self.cv2.VideoCapture(video_path)
            # Get first frames to extract size
            _, self.frame = cap.read()
            self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
            height, width, _ = self.frame.shape
            # Set roi
            if self.roi is None:
                self.roi = (0, 0, width, height)  # x, y, w, h

            while cap.isOpened():
                self.frames += 1
                self.ret, self.frame = cap.read()
                # If rotate set to true
                if self.rotate:
                    self.frame = self.cv2.rotate(self.frame, self.cv2.ROTATE_180)

                if self.frame is None:  # End of video
                    break

                # Resize frame --> faster obj. detection/tracking
                self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)

                # Notify observers
                self.notify()

                self.cv2.imshow("Video", self.frame)
                # Pressing Esc key to stop
                key = cv2.waitKey(1)
                if key == 27:
                    break

            cap.release()

    def set_fps(self):
        """
        Sets fps based on cv2.CAP_PROP_FPS
        :return: None
        """
        vid = cv2.VideoCapture(self.video_list[0])
        fps = int(vid.get(self.cv2.CAP_PROP_FPS))
        print("Read fps using cv2.CAP_PROP_FPS: ", fps)
        self.fps = fps

    def record(self, filename, sec, codec="mp4v", fps=None):
        """
        Records and saves video to given filename in current directory
        :param filename: Name of the file, extension should match the codec
        :param sec: int number of seconds to record
        :param codec: Type of codec, string based on cv2 codecs and the codecs your pc supports
        :param fps: int number of Frames Per Second, if the cv2 measured ones are incorrect
        :return: None
        """
        for video_path in self.video_list:
            cap = self.cv2.VideoCapture(video_path)
            # Get first frames to extract size
            _, self.frame = cap.read()
            self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
            height, width, _ = self.frame.shape

            # Get fps and calculate needed fps for the time period of sec
            if fps is None:  # If fps set to None, get fps by cv2
                fps = int(cap.get(self.cv2.CAP_PROP_FPS))

            total_fps = sec * fps

            # Set the video recorder
            fourcc = self.cv2.VideoWriter_fourcc(*codec)
            out = self.cv2.VideoWriter(filename, fourcc, fps, (int(width), int(height)))

            # Set variable as timer, to check if fps match
            start_time = time.time()

            # Create a frame counter
            frame_counter = 0
            while cap.isOpened() and frame_counter <= total_fps:
                frame_counter += 1  # Update frame counter at beginning

                self.ret, self.frame = cap.read()
                # If rotate set to true
                if self.rotate:
                    self.frame = self.cv2.rotate(self.frame, self.cv2.ROTATE_180)

                if self.frame is None:  # End of video
                    break

                # Resize frame --> faster obj. detection/tracking
                self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)

                # Write frame to writer
                out.write(self.frame)

                self.cv2.imshow("Frame", self.frame)

                # Pressing Esc key to stop
                key = cv2.waitKey(1)
                if key == 27:
                    break

            # End time
            end_time = time.time()

            # Release everything when finished
            cap.release()
            out.release()
            self.cv2.destroyAllWindows()

            total_time = round(end_time - start_time, 3)
            print_string = "Video saved as: {}. Total recording time: {}s should match {}s.".format(filename,
                                                                                                    total_time,
                                                                                                    sec)
            print_string += " Set fps = {}".format(fps)
            print(print_string)


if __name__ == "__main__":
    video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
    # video.select_roi(save=True)
    obt = ObjectTracking(video)
    timer = Timer(video)
    timer.set_lines(save=True)
    # video.play()
    pass
