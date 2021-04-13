from speedometer.Observer import Observer
from abc import abstractmethod


class ObjectTracking(Observer):
    def __init__(self, video):
        self._video = video  # Video object acts as subject

    def update(self, notification_type) -> None:
        """
        Receive update from subject.
        """
        pass

    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, video_object):
        self._video = video_object
        # Attach self to subject as an observer
        self._video.attach(self)
        print(self._video)
