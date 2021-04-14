from speedometer.Observer import Observer
from abc import abstractmethod


class ObjectTracking(Observer):
    def __init__(self, video, detection="MOG2", tracking="euclid"):
        self.video = video  # Video object acts as subject
        self.cv2 = video.cv2  # Match the cv2 module with Video object
        self.object_detector = None

        if detection == "MOG2":
            self.object_detector = self.video.cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)

        self.mask = None

    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, video_object):
        self._video = video_object
        # Attach self to subject as an observer
        self._video.attach(self)
        print(self._video)

    def update_beginning(self) -> None:
        """
        Receive update from subject, beginning --> when video is set to play
        video playing.
        """
        print("Beginning")

    def update_mid(self) -> None:
        """
        Receive update from subject, mid --> when video is being played
        video playing.
        """
        # video.roi has to be set by now
        x, y, w, h = self.video.roi
        roi = self.video.frame[y: y + h, x: x + w]
        # Apply roi to object detection
        self.mask = self.object_detector.apply(roi)
        _, self.mask = self.cv2.threshold(self.mask, 254, 255, self.cv2.THRESH_BINARY)  # BINARY

        # Find contours
        contours, _ = self.cv2.findContours(self.mask, self.cv2.RETR_TREE, self.cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = self.cv2.contourArea(contour)
            if area >= 300:
                # Get bounding rectangle
                x, y, w, h = self.cv2.boundingRect(contour)
                # Get center point
                center_point = (x + w // 2, y + h // 2)
                self.cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                self.cv2.circle(roi, center_point, 3, (0, 0, 255), 3)

        self.cv2.imshow("Mask", self.mask)

    def update_end(self) -> None:
        """
        Receive update from subject, end --> when video has ended playing
        video playing.
        """
        pass
