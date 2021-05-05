from __future__ import annotations
from speedometer.Observer import Mediator, Observer


class Object:
    """
    Represents one object that is being tracked by the ObjectTracking object
    """
    def __init__(self, id, frame, position, bounding_rect):
        self.id = id
        self.num_of_points = 1  # Number of points (adds one when initialized)
        # List off all center positions of object (center of rectangle)
        self.positions = []  # [[x1, y1], ...] upper left corner positions of bounding rect
        self.positions.append(position)
        # List of all bounding rectangles sizes
        self.bounding_rects = []  # [[w1, h1], ...]
        self.bounding_rects.append(bounding_rect)
        # List of frame counter the object was seen
        self.frames = []  # [int_1, ...]
        self.frames.append(frame)
        # Calculate center position and save to list
        center_pos = [position[0] + bounding_rect[0]/2, position[1] + bounding_rect[1]/2]
        self.center_positions = []
        self.center_positions.append(center_pos)

    def add_point(self, frame, position, bounding_rect) -> None:
        """
        Method adds a detected point to the object
        """
        self.frames.append(frame)  # Frame of detection
        self.positions.append(position)  # Position of detection
        self.bounding_rects.append(bounding_rect)  # Size at detection
        self.center_positions.append([position[0] + bounding_rect[0]/2, position[1] + bounding_rect[1]/2])
        self.num_of_points += 1

    def average_size(self) -> float:
        """
        Function returns the average size of the object
        :return: float: average size(by surface)
        """
        return sum([rect[0] * rect[1] for rect in self.bounding_rects])/self.num_of_points

    def average_direction(self) -> list:
        """
        Function returns the average direction of the object as a vector [x, y] where size matters
        :return: list: average direction [x, y] of the center point of object
        """
        x_diff, y_diff = [], []
        prev_x, prev_y = self.center_positions[0]
        for i in range(1, self.num_of_points):
            curr_pos = self.center_positions[i]
            # Append difference to prev. point
            x_diff.append(curr_pos[0] - prev_x)
            y_diff.append(curr_pos[1] - prev_y)
            # Set this point as previous
            x_diff, y_diff = curr_pos
        return [sum(x_diff)/self.num_of_points, sum(y_diff)/self.num_of_points]


class ObjectTracking(Mediator):
    """
    Acts as a mediator between the VideoPlayer object and Timer object, wraps VideoPlayer and is wrapped by Timer.
    Detects and tracks objects based on different methods that are set when initialized.
    """
    def __init__(self, video, detection="MOG2", tracking="euclid", object_parameters=None):
        self._observers: list = []
        self.video = video  # Video object acts as subject
        self.cv2 = video.cv2  # Match the cv2 module with Video object
        self.object_detector = None

        # Set type of detection todo add personal one
        if detection == "MOG2":
            self.object_detector = self.video.cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)
        # Object parameters describe the category of object by size [min_avg_size, max_avg_size]
        if object_parameters is None:
            self.object_parameters = {"human": [300, 600], "cyclist": [601, 750], "car": [750, 2500], "bus": [2500, 4000]}
            self.minimum_object_size = 300
        else:
            self.object_parameters = object_parameters
            self.minimum_object_size = min([size[0] for size in self.object_parameters.values()])
        self.mask = None
        # List of all detected objects
        self.objects = []

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject
        """
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """
        Detach observer from subject
        """
        self._observers.remove(observer)

    def notify(self) -> None:
        """
        Notify all observers, mid video
        """
        for observer in self._observers:
            observer.update()

    def update(self) -> None:
        """
        Receive update from subject(VideoPlayer)
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
            if area >= self.minimum_object_size:
                # Get bounding rectangle
                x, y, w, h = self.cv2.boundingRect(contour)
                # Get center point
                center_point = (x + w // 2, y + h // 2)
                self.cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                self.cv2.circle(roi, center_point, 3, (0, 0, 255), 3)

        # Notify observers (Timer)
        self.notify()

        self.cv2.imshow("Mask", self.mask)

    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, video_object):
        """ This gets set when object is initialized """
        self._video = video_object
        # Attach self to subject as an observer
        self._video.attach(self)
        print(self._video)
