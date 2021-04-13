"""
 opencv-contrib-python version 4.2.0.34 is needed (other versions dont work for some reason)
 OpenCV trackers are useless as they're slow aff
"""
from speedometer.Observer import Subject, Observer
from speedometer.object_tracking import ObjectTracking
from abc import ABC, abstractmethod

import cv2
import os


def mmss_to_frames(fps, m, s=0):
    """
    Converts minutes and seconds of video to frames based on fps
    :param fps: frames per second of video
    :param m: minutes
    :param s: seconds
    :return: frame number
    """
    return int((m * 60 + s)/fps)


class VideoPlayer(Subject):
    def __init__(self, video_path, fps, roi=None):
        self._observers: list = []

        self.cv2 = cv2
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

        # Current frames the video is on, gets reset once the video goes to the next
        self._frames = 0

        # video_path is a string when initialized, converted to a list containing file_name strings by the setter
        self.video_list = video_path
        self.fps = fps

        self.roi = roi  # Region of interest

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject
        """
        pass

    def detach(self, observer: Observer) -> None:
        """
        Detach observer from subject
        """
        pass

    def notify(self, notification_type) -> None:
        """
        Notify all observers
        """
        pass

    def notify_one(self, observer: Observer) -> None:
        """
        Notify one observer
        """
        pass

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
        else:
            raise ValueError("Invalid path.")

    @property
    def frames(self):
        return self._frames

    @frames.setter
    def frames(self, f):
        self._frames = f

    def select_roi(self, **kwargs):
        """  TODO cv2.roi prints command description after selection, should get rid of it
        Opens video with a ROI selector on given frame or time set in kwargs,
        :param kwargs: frames= or min=, or min= and sec=
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
        self.cv2.imshow("Frame", frame)
        print("Create the selecton using mouse, to save and exit press SPACE or ENTER to cancel press C")
        self.roi = self.cv2.selectROI("Frame", frame)
        print(self.roi)

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
                self.cv2.imshow("Frame", frame)

                # Pressing Esc key to stop
                key = cv2.waitKey(1)
                if key == 27:
                    break


if __name__ == "__main__":
    video = VideoPlayer(r"C:\Users\Liam\PycharmProjects\CarDetection\Video\\", fps=15)
    obt = ObjectTracking(video)

