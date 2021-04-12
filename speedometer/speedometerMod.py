from abc import ABC, abstractmethod

from speedometer.Observer import Subject, Observer
from speedometer.object_detection import ObjectDetection
from speedometer.timer import Timer
from speedometer.object_tracking import ObjectTracking

import cv2
import os


class Speedometer(Subject):
    def __init__(self):
        self._ObjectDetection = None
        self._ObjectTracking = None
        self._Timer = None

        # Given path of video, could be directory path or simple file path
        self._video_path = None
        # List of video paths
        self._videos: list = []

    def attach(self, observer: Observer) -> None:
        """
        :param observer:
        :return:
        """
        pass

    def detach(self, observer: Observer) -> None:
        """
        :param observer:
        :return:
        """
        pass

    def notify(self) -> None:
        """
        :return:
        """
        pass

    def notify_one(self, observer: Observer) -> None:
        """
        :param observer:
        :return:
        """
        pass

    @property
    def ObjectDetection(self):
        return self._ObjectDetection

    @ObjectDetection.setter
    def ObjectDetection(self, obj_det: ObjectDetection):
        if isinstance(obj_det, ObjectDetection):
            self._ObjectDetection = obj_det
        else:
            raise TypeError("Invalid object type, expected <ObjectDetection>")

    @ObjectDetection.deleter
    def ObjectDetection(self):
        self._ObjectDetection = None

    @property
    def ObjectTracking(self):
        return self._ObjectDetection

    @ObjectTracking.setter
    def ObjectTracking(self, obj_track: ObjectTracking):
        if isinstance(obj_track, ObjectTracking):
            self._ObjectTracking = obj_track
        else:
            raise TypeError("Invalid object type, expected <ObjectTracking>")

    @ObjectTracking.deleter
    def ObjectTracking(self):
        self._ObjectTracking = None

    @property
    def Timer(self):
        return self._Timer

    @Timer.setter
    def Timer(self, timer: Timer):
        if isinstance(timer, Timer):
            self._Timer = Timer
        else:
            raise TypeError("Invalid object type, expected <Timer>")

    @Timer.deleter
    def Timer(self):
        self._Timer = None

    @property
    def video_path(self):
        return self._video_path

    @video_path.setter
    def video_path(self, vid_path):
        self._video_path = vid_path
        if os.path.isfile(vid_path):
            lis = list()
            lis.append(vid_path)
            self._videos = lis
        elif os.path.isdir(vid_path):
            videos = [os.path.join(vid_path, video) for video in os.listdir(vid_path)]
            if len(videos) == 0:
                raise ValueError("Directory is empty.")
            self._videos = videos
        else:
            self._video_path = None
            raise ValueError("Path {} is not a file path or a folder path.".format(vid_path))

    @video_path.deleter
    def video_path(self):
        self._video_path = None
        self._videos = []

    def play(self):
        print("Playing video/s.")
        if not self._videos:
            print("Nothing to play...")
        for vid_path in self._videos:
            # Set the capture
            cap = cv2.VideoCapture(vid_path)

            # Check if camera opened successfully
            if not cap.isOpened():
                raise ValueError("Error opening video file {}".format(vid_path))

            while cap.isOpened():
                # Capture frame-by-frame
                ret, frame = cap.read()
                if ret:
                    # Display the resulting frame
                    cv2.imshow('Frame', frame)
                    # Press Q on keyboard to  exit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                # Break the loop
                else:
                    break


if __name__ == "__main__":
    spd = Speedometer()
    spd.video_path = r"C:\Users\Liam\PycharmProjects\CarDetection\Video\20210411_115107_tp00029.mp4"
    print(spd._videos)
    spd.play()

