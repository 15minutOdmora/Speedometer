"""
 opencv-contrib-python version 4.2.0.34 is needed (other versions dont work for some reason)
 OpenCV trackers are useless as they're slow aff
"""
from speedometer.Observer import Subject, Observer
from speedometer.helper_functions import open_data_file, save_to_data_file, mmss_to_frames

import json
import time
import cv2
import os


class VideoPlayer(Subject):
    """
    VideoPlayer class plays set videos in video_path using cv2, has methods for setting roi, recording certain parts of
    videos, ...
    """
    def __init__(self, video_path, fps=None, roi=None, resize=(640, 360), rotate=None, display=True):
        """
        :param video_path: str or list -> Video to be played, can be: rtsp url, video path or folder path, in case of
        folder path, the player will play each file in the directory.
        :param fps: int -> Frames Per Second of camera. If None -> gets set by reading it from camera/video.
        :param roi: tuple(tuple, tuple) -> Pair of points defining the upper left corner and bottom left corner of the
        Region Of Interest.
        :param resize: tuple(width, height) -> The size the window should be resized to. Preset: (640, 360).
        :param rotate: str -> If image needs to be rotated, possible: '90c'(90degrees clockwise),
        '90cc'(90 degrees counterclockwise), '180'(180 degrees).
        :param display: bool -> If the video frame should be displayed.
        """
        self.observers: list = []
        self.cv2 = cv2
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        # Current frames the video is on, gets reset once the video goes to the next
        self._frames = 0
        # video_path is a string when initialized, converted to a list containing file_name strings by the setter
        self.video_list = video_path
        self._fps = fps
        self.width = None
        self.height = None
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
        self.width, self.height = self.resize
        self.display = display
        self._rotate = rotate
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
        """
        Setter for fps, if fps is none, reads fps from video/camera.
        :param fps: int
        :return: None
        """
        if fps is None:  # If fps is set to None, read fps using cv2
            vid = cv2.VideoCapture(self.video_list[0])
            self._fps = int(vid.get(self.cv2.CAP_PROP_FPS))
        else:
            self._fps = fps

    @property
    def rotate(self):
        return self._rotate

    @rotate.setter
    def rotate(self, degrees):
        """
        Setter for rotate sets the rotation of image.
        :param degrees: str
        :return: None
        """
        possible_rotations = {"90c": self.cv2.ROTATE_90_CLOCKWISE,
                              "90cc": self.cv2.ROTATE_90_COUNTERCLOCKWISE,
                              "180": self.cv2.ROTATE_180}
        if degrees is None:
            self._rotate = None
        elif degrees in possible_rotations.keys():
            self._rotate = possible_rotations[degrees]
        else:
            raise ValueError("Rotation degrees set incorrectly. Should be one of: None, '90c', '90cc', '180'")

    def select_roi(self, **kwargs):
        """  TODO cv2.roi prints command description after selection, should get rid of it, fix so seconds can get passed
        Opens video with a ROI selector on given frame or time set in kwargs, saves the selection to saved_data.json
        :param kwargs: int frames=, int min=, int min= and int sec=
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
                save_to_data_file({"roi": self.roi})
        cap.release()
        self.cv2.destroyAllWindows()

    def play(self, start_seconds=None):
        """
        Starts video, displays windows if set to true.
        :return: None
        """
        for video_path in self.video_list:
            cap = self.cv2.VideoCapture(video_path)
            # Get first frames to extract size
            _, self.frame = cap.read()
            # Check if start_seconds is set, open at that second
            if start_seconds is not None:
                # Calculate frame
                frame_to_start = start_seconds * self.fps
                # Set video at that frame
                cap.set(1, frame_to_start - 1)

            # If rotate is set -> rotate image
            if self.rotate is not None:
                self.frame = self.cv2.rotate(self.frame, self.rotate)
            # Resize frame and get dimensions
            self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
            height, width, _ = self.frame.shape
            # Set roi
            if self.roi is None:
                self.roi = (0, 0, width, height)  # x, y, w, h

            while cap.isOpened():
                self.frames += 1
                self.ret, self.frame = cap.read()

                if not self.ret:
                    # Re initialize cap
                    cap = self.cv2.VideoCapture(video_path)
                    self.frames += 1
                    print("Frame skipped ...")
                    continue

                # If rotate is set -> rotate image
                if self.rotate is not None:
                    self.frame = self.cv2.rotate(self.frame, self.rotate)

                if self.frame is None:  # End of video
                    break

                # Resize frame --> faster obj. detection/tracking
                self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)

                # Notify observers
                self.notify()
                # Display windows if set to true
                if self.display:
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
        :param filename: str -> Name of the file, extension should match the codec
        :param sec: int -> Number of seconds to record
        :param codec: str -> Type of codec, string based on cv2 codecs and the codecs your pc supports
        :param fps: int -> Number of Frames Per Second, if the cv2 measured ones are incorrect
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
    pass
