# from speedometer import config
from speedometer.Observer import Subject, Observer
from speedometer.object_detection import ObjectDetection
from speedometer.timer import Timer
from speedometer.object_tracking import ObjectTracking

import cv2
import os


class Speedometer(Subject):
    def __init__(self, resize=None):
        self._ObjectDetection = None
        self._ObjectTracking = None
        self._Timer = None

        self.frames = 0

        self.cv2 = cv2

        self._observers: list = []

        # Given path of video, could be directory path or simple file path
        self._video_path = None
        # List of video paths
        self._videos: list = []

        # Object tracking data
        self._point_of_interest = None

        self.resize = resize

        # Video data once video is playing
        self._cap = None
        self.ret = None
        self.frame = None
        self._frame_size = None

        # Mask, contours ...
        self.mask = None

        # Region of interest
        self.roi = None

        self.first_frame = None

    def attach(self, observer: Observer) -> None:
        """
        :param observer:
        :return:
        """
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """
        :param observer:
        :return:
        """
        self._observers.remove(observer)

    def notify(self, notification_type) -> None:
        """
        Method sends this object as data to all subscribed observers
        :return:
        """
        for observer in self._observers:
            observer.update(self, notification_type)

    def notify_one(self, observer: Observer, notification_type) -> None:
        """
        Method sends self as data to specified observer Observer
        :param notification_type:
        :param observer: target Observer
        :return:
        """
        if observer is not None:
            observer.update(notification_type)
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

    @property
    def cap(self):
        return self._cap

    @cap.setter
    def cap(self, video_path):
        self._cap = self.cv2.VideoCapture(video_path)
        # Set frame size
        if self.resize is not None:
            self.frame_size = self.resize
        else:
            if self.cap is not None:
                width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Convert to int as it returns float
                height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.frame_size = (width, height)

    @cap.deleter
    def cap(self):
        self._cap.release()
        self._cap = None

    @property
    def frame_size(self):
        return self._frame_size

    @frame_size.setter
    def frame_size(self, size):
        self._frame_size = size

    def resize(self):
        pass

    def play_all(self, display_window=True):
        """
        :return:
        """
        print("Playing video/s.")
        if not self._videos:
            print("Nothing to play...")

        for vid_path in self._videos:

            # Set the capture
            self.cap = vid_path  # Todo make normal (lol)

            # Check if camera opened successfully
            if not self.cap.isOpened():
                raise ValueError("Error opening video file {}".format(vid_path))

            # Check first frame, save size
            self.ret, temp_frame = self.cap.read()
            # Save frame to object variable first_frame (used in object_detections)
            self.frame = temp_frame
            self.first_frame = temp_frame

            # Notify ObjectDetection object to setup object_detector...
            self.notify_one(self.ObjectDetection, "b")

            while self.cap.isOpened():
                self.frames += 1
                # Capture frame-by-frame
                self.ret, self.frame = self.cap.read()

                if self.resize is not None:
                    self.frame = self.cv2.resize(self.frame, self.resize, fx=0, fy=0, interpolation=self.cv2.INTER_CUBIC)

                self.notify_one(self.ObjectDetection, notification_type="m")
                print(self.frames)

                if self.ret:
                    # Display the resulting frame
                    if display_window:
                        self.cv2.imshow('Frame', self.frame)
                        self.cv2.imshow("Roi", self.roi)
                        self.cv2.imshow("Mask", self.mask)
                    # Press Q on keyboard to  exit
                    if self.cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                # Break the loop
                else:
                    break

            del self.cap


if __name__ == "__main__":
    spd = Speedometer(resize=(640, 360))
    spd.ObjectDetection = ObjectDetection(speedometer=spd, roi=[160, 280, 0, 680], typeofdetection="createBackgroundSubtractorKNN")  # roi=[160, 280, 0, 680]
    spd.video_path = r"C:\Users\Liam\PycharmProjects\CarDetection\Video\20210411_115107_tp00029.mp4"
    # spd.ObjectDetection = ObjectDetection()
    spd.play_all()

