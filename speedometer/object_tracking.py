from __future__ import annotations
from speedometer.Observer import Mediator, Observer

import math
import time


def euclid_dist(point1, point2):
    """
    Calculates the Euclidean distance between two points
    :param point1: First point
    :param point2: Second Point
    :return: Distance
    """
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


class Object:
    """
    Represents one object that is being tracked by the ObjectTracking object
    """
    def __init__(self, id, frame, position, bounding_rect, center_point):
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
        self.center_points = []
        self.center_points.append(center_point)
        # Times get measured in case fps doesn't match up
        self.times = []
        self.times.append(time.time())
        # Direction, gets set once the object is timed, 1 = moving right (x increasing), -1 = moving left (x decreasing)
        self._direction = None  # Todo make possible in y-cords

    def add_point(self, frame, position, bounding_rect, center_point) -> None:
        """
        Method adds a detected point to the object
        """
        self.frames.append(frame)  # Frame of detection
        self.positions.append(position)  # Position of detection
        self.bounding_rects.append(bounding_rect)  # Size at detection
        self.center_points.append(center_point)
        self.times.append(time.time())
        self.num_of_points += 1

    def average_size(self) -> float:
        """
        Function returns the average size of the object
        :return: float: average size(by surface)
        """
        return sum([rect[0] * rect[1] for rect in self.bounding_rects])/self.num_of_points

    @property
    def direction(self) -> tuple:
        """
        Fuction calculates the direction of object by the first and last points of object
        :return: tuple(x, y) => vector of direction
        """
        last_pos = self.center_points[-1]
        first_pos = self.center_points[0]
        return last_pos[0] - first_pos[0], last_pos[1] - first_pos[1]

    def average_direction(self) -> tuple:
        """
        Function returns the average direction of the object as a vector [x, y] where size matters
        :return: list: average direction [x, y] of the center point of object
        """
        x_diff, y_diff = [], []
        prev_x, prev_y = self.center_points[0]
        for i in range(1, self.num_of_points):
            curr_pos = self.center_points[i]
            # Append difference to prev. point
            x_diff.append(curr_pos[0] - prev_x)
            y_diff.append(curr_pos[1] - prev_y)
            # Set this point as previous
            x_diff, y_diff = curr_pos
        return sum(x_diff)/self.num_of_points, sum(y_diff)/self.num_of_points


class ObjectTracking(Mediator):
    """
    Acts as a mediator between the VideoPlayer object and Timer object, wraps VideoPlayer and is wrapped by Timer.
    Detects and tracks objects based on different methods that are set when initialized.
    """
    def __init__(self, video, detection="MOG2", tracking="euclid", object_parameters=None, min_frame_diff=None, max_point_distance=None):
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
        # If min frame diff(used for deleting objects) is not set, calculate it(20% of fps)
        if min_frame_diff is None: 
            self.min_frame_diff = int(self.video.fps * 0.2)
        else:
            self.min_frame_diff = min_frame_diff
        # max_point_distance is the maximum distance an object can move(in pixels) between two consecutive frames
        if max_point_distance is None:
            self.max_point_distance = 200  # Todo calculate based on frames and cap size 
        else:
            self.max_point_distance = max_point_distance
        
        self.mask = None

        # List of all detected objects
        self.objects = []
        # Number of object
        self.object_counter = 0
        self.all_detected_objects = 0  # Serves as a unique id for objects

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

    def match(self, detected_objects):
        """
        Matches detected objects with the already existing ones, deletes objects and creates new ones
        :return: None
        """
        curr_frame = self.video.frames

        if not detected_objects:  # If there are no detections, delete the ones that haven't been seen in min_frame_diff
            for obj in self.objects:
                frame_diff = curr_frame - obj.frames[-1]
                if frame_diff > self.min_frame_diff:  # If frame diff. too bif --> remove object from objects list
                    self.objects.remove(obj)
            return

        if self.object_counter == 0:  # If no current objects exist
            for detection in detected_objects:
                # Update number of objects
                self.object_counter += 1
                self.all_detected_objects += 1
                # Create new object
                new_obj = Object(self.all_detected_objects,
                                 curr_frame,
                                 detection[0:2],
                                 detection[2:4],
                                 detection[4])
                self.objects.append(new_obj)
            return

        # If objects exist, match them.
        paired = 0  # Number of objects paired
        to_be_paired = len(detected_objects)
        # Go through existing objects first
        for obj in self.objects:
            if paired >= to_be_paired:  # If all objects were already paired
                self.objects.remove(obj)
                break
            # Calculate Euclidean distances to match with closest one
            distances = list()
            for det in detected_objects:
                distances.append(euclid_dist(obj.center_points[-1], det[4]))
            # Get index of closest point
            index_min = min(range(len(distances)), key=distances.__getitem__)
            # If object is in range of the maximum point distance between two consecutive frames
            if distances[index_min] <= self.max_point_distance:
                # Add detection to object as new point
                closest_detection = detected_objects[index_min]
                pos = closest_detection[0:2]
                bound_rect = closest_detection[2:4]
                cntr_point = closest_detection[4]
                obj.add_point(curr_frame, pos, bound_rect, cntr_point)
                # Remove detection
                del detected_objects[index_min]
                paired += 1

            # Check if object hasn't been seen in the last frames(>min_fr_diff) ==> delete object
            frame_diff = curr_frame - obj.frames[-1]
            if frame_diff > self.min_frame_diff:
                self.objects.remove(obj)
                continue

            # Check if object hasn't been moving ==> delete the object
            # Check the last 3 points (3 is enough as objects usually move just slightly)
            if obj.num_of_points >= 4:
                if [obj.center_points[-1]] * 3 == obj.center_points[::-1][1:4]:
                    self.objects.remove(obj)
                    continue

            # Remaining detections get created as new objects
            for detection in detected_objects:
                self.object_counter += 1
                self.all_detected_objects += 1
                new_obj = Object(self.all_detected_objects,
                                 curr_frame,
                                 detection[0:2],
                                 detection[2:4],
                                 detection[4])
                self.objects.append(new_obj)
                continue

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

        detected_objects = []  # A list of contours that fit the parameter of size: [[x, y, w, h, center_point], ...]
        for contour in contours:
            area = self.cv2.contourArea(contour)
            if area >= self.minimum_object_size:
                # Get bounding rectangle
                x, y, w, h = self.cv2.boundingRect(contour)
                # Get center point
                center_point = (x + w // 2, y + h // 2)
                self.cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                self.cv2.circle(roi, center_point, 3, (0, 0, 255), 3)
                detected_objects.append([x, y, w, h, center_point])  # Save object to list

        self.match(detected_objects)  # Pass to match, remove or add objects to list (a tracker basically)
        print(self.objects)

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
