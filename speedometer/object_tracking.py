from speedometer.Observer import Mediator, Observer
from speedometer.helper_functions import euclid_dist
import time
import numpy as np


class Object:
    """
    Represents one object that is being tracked. Keeps track of positions, bounding rect. sizes,
    Unix times of detections and frame, numbers of detections.
    """
    def __init__(self, id, frame, position, bounding_rect, center_point):
        """
        :param id: int -> Unique id of object.
        :param frame: int -> Frame number of video as the object gets initialized.
        :param position: list or tuple -> Position of object as a point(x, y) as it gets initialized.
        :param bounding_rect: list or tuple -> Size of the bounding rectangle of object as a pair(width, height)
        :param center_point: list or tuple -> Center point of object as a point(x, y)
        """
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
        return int(sum([rect[0] * rect[1] for rect in self.bounding_rects])/self.num_of_points)

    def direction(self) -> tuple:
        """
        Method calculates the direction of object by the first and last center points of object.
        :return: tuple(x, y) -> where x, y are direction values, ether 1(positive), 0(not moving), -1(negative)
        """
        last_pos = self.center_points[-1]
        first_pos = self.center_points[0]
        # Readability counts or smthin
        # Set direction in x
        x_diff = last_pos[0] - first_pos[0]
        if x_diff > 0:
            x_dir = 1
        elif x_diff == 0:
            x_dir = 0
        else:
            x_dir = -1
        # Set direction in y
        y_diff = last_pos[1] - first_pos[1]
        if y_diff > 0:
            y_dir = 1
        elif y_diff == 0:
            y_dir = 0
        else:
            y_dir = -1
        return x_dir, y_dir

    def average_direction(self) -> tuple:
        """
        Method calculates the average movement vector between two consecutive points.
        :return: tuple(x, y) -> average direction in the x and y coordinates of the center point of object
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

    def __repr__(self) -> str:
        """
        Representation method of object.
        :return: str
        """
        string = "Object(id: {}, center_pos: {}, num_of_points: {})".format(self.id,
                                                                            self.center_points[-1],
                                                                            self.num_of_points)
        return string


class ObjectTracking(Mediator):
    """
    Detects and tracks objects based on different methods that are set when initialized.
    Acts as a mediator between the VideoPlayer object and Timer object, wraps VideoPlayer and is wrapped by Timer.
    """
    def __init__(self, video, bkg_subtractor="MOG2", tracking="euclid", min_frame_diff=None, max_point_distance=None, display=True,
                 minimum_object_size=0, maximum_object_size=100000):
        """
        :param video: VideoPlayer object -> Is necessary as this class wraps it.
        :param bkg_subtractor: str -> Type of background subtractor to use possible: "MOG", "MOG2"(preset), "GMG"
        :param tracking: str -> Type of object tracking to use. Possible: "euclid"(preset)
        :param object_parameters: dict -> Dict consisting of possible object size pairs object_name: [min_size, max_size]
        :param min_frame_diff: int or float -> The minimal frame number an object can stand still(preset=20% of video fps)
        :param max_point_distance: int or float -> The maximum distance(px) an object can travel between two frames
        :param display: bool -> If the mask video should be displayed at each frame. Preset: True
        """
        self._observers: list = []
        self.video = video  # Video object acts as subject
        self.cv2 = video.cv2  # Match the cv2 module with Video object
        self.bkg_subtractor = None

        # Set type of background subtraction
        if bkg_subtractor == "MOG2":
            self.bkg_subtractor = self.video.cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)
        elif bkg_subtractor == "MOG":
            self.bkg_subtractor = self.video.cv2.bgsegm.createBackgroundSubtractorMOG()
        elif bkg_subtractor == "GMG":
            self.bkg_subtractor = self.video.cv2.createBackgroundSubtractorGMG()

        # Set type of tqacking
        if tracking == "euclid":  # Euclidean distance
            self.tracking = self.euclid  # Set the method to use currently only supports this

        # Object parameters describe the category of object by size [min_avg_size, max_avg_size]
        self.minimum_object_size = minimum_object_size
        self.maximum_object_size = maximum_object_size
        # If min frame diff(used for deleting objects) is not set, calculate it(20% of fps)
        if min_frame_diff is None: 
            self.min_frame_diff = int(self.video.fps * 0.2)
        else:
            self.min_frame_diff = min_frame_diff
        # max_point_distance is the maximum distance an object can move(in pixels) between two consecutive frames
        if max_point_distance is None:
            # Assume the max_dist is at most 25% of the frame
            width = self.video.width
            self.max_point_distance = int(width * 0.25)  # Todo calculate based on frames and cap size
        else:
            self.max_point_distance = max_point_distance
        
        self.mask = None
        self.display = display

        # List of all detected objects
        self.objects = []
        # Number of object
        self.object_counter = 0
        self.all_detected_objects = 0  # Serves as a unique id for objects

        self.prev_frame = None  # todo Remove later


    @property
    def video(self):
        return self._video

    @video.setter
    def video(self, video_object) -> None:
        """
        This gets set when object is initialized
        """
        self._video = video_object
        # Attach self to subject as an observer
        self._video.attach(self)

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
        Notify all observers(timers) of frame update
        """
        for observer in self._observers:
            observer.update()

    def euclid(self, detected_objects) -> None:
        """
        Matches new detections with already tracked objects based on smallest euclidean distance,
        clears old(non moving) objects and creates new tracked objects.
        :param detected_objects: list -> List containing detected objects which are also lists[x, y, w, h, (cx, cy)]
        :return: None
        """
        curr_frame = self.video.frames
        if not detected_objects:  # If there are no detections, delete the ones that haven't been seen in min_frame_diff
            for obj in self.objects:
                frame_diff = curr_frame - obj.frames[-1]
                if frame_diff > self.min_frame_diff:  # If frame diff. too big --> remove object from objects list
                    self.objects.remove(obj)

        if len(self.objects) == 0:  # If no current objects exist, create objects from detections
            # This does the same as the above
            # Update number of objects by 1, as the enumerate starts at 0
            self.objects += list(
                map(lambda det: Object(self.all_detected_objects + det[0], curr_frame, det[1][0:2], det[1][2:4], det[1][4]),
                    enumerate(detected_objects, start=1))
            )
            self.all_detected_objects += len(detected_objects)
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
            distances = list(map(lambda det: euclid_dist(obj.center_points[-1], det[4]), detected_objects))
            # Get index of closest point
            index_min = min(range(len(distances)), key=distances.__getitem__)
            # If object is in range of the maximum point distance between two consecutive frames
            if distances[index_min] <= self.max_point_distance:
                # Add detection to object as new point
                closest_detection = detected_objects[index_min]
                # pos, bound_rect, cntr_point = closest_detection[0:2], closest_detection[2:4], closest_detection[4]
                obj.add_point(curr_frame, closest_detection[0:2], closest_detection[2:4], closest_detection[4])
                # Remove detection
                del detected_objects[index_min]
                paired += 1

            # Check if object hasn't been seen in the last frames(>min_fr_diff) ==> delete object
            if curr_frame - obj.frames[-1] > self.min_frame_diff:
                self.objects.remove(obj)
                continue

            # Check if object hasn't been moving ==> delete the object
            # Check the last 3 points (3 is enough as objects usually move just slightly)
            if obj.num_of_points >= 4 and [obj.center_points[-1]] * 3 == obj.center_points[::-1][1:4]:
                self.objects.remove(obj)
                continue

            # Remaining detections get created as new objects
            for detection in detected_objects:
                self.all_detected_objects += 1
                new_obj = Object(self.all_detected_objects,
                                 curr_frame,
                                 detection[0:2],
                                 detection[2:4],
                                 detection[4])
                self.objects.append(new_obj)

    def update(self) -> None:
        """
        Receive update from subject(VideoPlayer) at each frame when video is playing, apply roi bkg_subtractor,
        find detections, ...
        """
        # video.roi has to be set by now
        xr, yr, wr, hr = self.video.roi
        roi = self.video.frame[yr: yr + hr, xr: xr + wr]
        # Apply roi to background subtractor
        self.mask = self.bkg_subtractor.apply(roi)
        _, self.mask = self.cv2.threshold(self.mask, 254, 255, self.cv2.THRESH_BINARY)  # BINARY

        # Find contours
        contours, _ = self.cv2.findContours(self.mask, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE)
        # Other possibility
        # contours, hierarchy = self.cv2.findContours(self.mask, 1, 2)

        detected_objects = []  # A list of contours that fit the parameter of size: [[x, y, w, h, center_point], ...]
        for contour in contours:
            area = self.cv2.contourArea(contour)
            if self.maximum_object_size > area > self.minimum_object_size:
                # Get bounding rectangle
                x, y, w, h = self.cv2.boundingRect(contour)
                # Get center point, add roi values as this is only on mask which is set by roi
                self.cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                self.cv2.circle(roi, (x + w // 2, y + h // 2), 3, (0, 0, 255), 3)
                center_point = (x + xr + w // 2, y + yr + h // 2)  # add roi values for upper left corner of roi
                detected_objects.append([x, y, w, h, center_point])  # Save object to list

        self.tracking(detected_objects)  # Pass to the set tracking function
        # Notify observers (Timer)
        self.notify()
        if self.display:
            self.cv2.imshow("Mask", self.mask)

    def update1(self):  # Testing alternative
        # video.roi has to be set by now
        xr, yr, wr, hr = self.video.roi
        roi = self.video.frame[yr: yr + hr, xr: xr + wr]

        if self.prev_frame is None:
            self.prev_frame = self.cv2.cvtColor(roi, self.cv2.COLOR_BGR2GRAY)
            return
        else:
            curr_frame = self.cv2.cvtColor(roi, self.cv2.COLOR_BGR2GRAY)
            self.mask = self.cv2.absdiff(self.prev_frame, curr_frame)
            self.prev_frame = self.cv2.cvtColor(roi, self.cv2.COLOR_BGR2GRAY)

            ret, self.mask = self.cv2.threshold(self.mask, 150, 255, self.cv2.THRESH_BINARY)
            kernel = np.ones((3, 3), np.uint8)
            self.mask = self.cv2.dilate(self.mask, kernel, iterations=3)

        # Find contours
        contours, _ = self.cv2.findContours(self.mask, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE)
        # Other possibility
        # contours, hierarchy = self.cv2.findContours(self.mask, 1, 2)

        detected_objects = []  # A list of contours that fit the parameter of size: [[x, y, w, h, center_point], ...]
        for contour in contours:
            print(contour)
            area = self.cv2.contourArea(contour)
            if area > self.minimum_object_size:
                # Get bounding rectangle
                x, y, w, h = self.cv2.boundingRect(contour)
                # Get center point, add roi values as this is only on mask which is set by roi
                self.cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                self.cv2.circle(roi, (x + w // 2, y + h // 2), 3, (0, 0, 255), 3)
                center_point = (x + xr + w // 2, y + yr + h // 2)  # add roi values for upper left corner of roi
                detected_objects.append([x, y, w, h, center_point])  # Save object to list

        self.tracking(detected_objects)  # Pass to the set tracking function
        # Notify observers (Timer)
        self.notify()
        if self.display:
            self.cv2.imshow("Mask", self.mask)
