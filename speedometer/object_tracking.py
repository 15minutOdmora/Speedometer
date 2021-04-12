from speedometer.Observer import Observer, Subject
import math
from speedometer import config


def euclidian_distance(point1, point2):
    """
    :param point1:
    :param point2:
    :return:
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


class Object:
    def __init__(self, initial_frame, detection, id=-1):
        x, y, w, h, center_point = detection
        self.positions = list()  # position = [x, y, w, h, center_point]
        self.positions.append(detection)

        self.human = [100, 500]  # Min rect. surf. and max rect. surf.
        self.car = [1000, 7000]
        self.type = ""  # Once the average values are set, it's either human, car, motorcycle

        self.id = id  # Initial id is set to -1, others are set manually
        self.num_of_points = 1  # Initially there's only one point

        self.frames = list()  # List of frames the object has been seen
        self.frames.append(initial_frame)
        self.avg_frame_diff = initial_frame

        self.last_center_point = center_point
        self.center_points = list()
        self.center_points.append(center_point)

        self.sizes = list()  # list of sizes
        initial_size = w * h  # Width * Height
        self.sizes.append(initial_size)
        self.avg_size = initial_size  # Touple of width, height

    def refresh_avg_size(self):
        """ Method:
        Calculates avg. size(surface[px]) of object
        :return: avg. size
        """
        self.avg_size = round(sum(self.sizes) / len(self.sizes))
        return self.avg_size

    def refresh_avg_frame_diff(self):
        """ Method: todo Not used
        Calculates avg. frame difference(difference of consecutive frames the obj. has been seen) of object,
        optimally = 1
        :return: avg. frame diff.
        """
        self.avg_frame_diff = sum([b - a for a, b in zip(self.frames[::2], self.frames[1::2])]) / self.num_of_points
        return self.avg_frame_diff

    def refresh(self):
        """ Method:
        Refreshes avg. size and avg. frame diff. and asserts the type of object based on size.
        """
        self.refresh_avg_size()
        # self.refresh_avg_frame_diff()  # Todo Not used

        if self.human[0] <= self.avg_size <= self.human[1]:
            self.type = "Human"
        elif self.car[0] <= self.avg_size <= self.car[1]:
            self.type = "Car"

    def add_point(self, frame, detection):
        """ Method:
        Adds a point of detection to the object, method used when the detection is matched with obj.
        """
        x, y, w, h, center_point = detection
        self.num_of_points += 1
        self.frames.append(frame)
        self.last_center_point = center_point
        self.center_points.append(center_point)
        self.sizes.append(w * h)
        self.positions.append(detection)

    def frame_diff_to_last(self, frame):
        """
        :param frame: Current frame
        :return: Frame diff. between last frame of object and curr. frame
        """
        return frame - self.frames[-1]


class ObjectTracker:
    def __init__(self, min_acc_fr_dif=5, min_point_dist_fr=200):
        print("Initializing ObjectTracker...")
        self.objects = list()  # Empty list when initialized ==> list(Object(1), Object(2))
        self.obj_counter = 0  # The unique id, is never reset

        # The minimum acceptable frame diff., parameter to delete objects,
        self.min_fr_dif = min_acc_fr_dif

        # The max. acceptable diff. in point movement between frames, > clears false positives
        self.min_point_dist_fr = min_point_dist_fr

    def update(self, frame, detections=[]):
        """ Function:
        Object tracting:
        Updates the detections to objects, creates matches, adds new obj. and deletes obj.
        Uses closest euclidian dist. to track obj.
        :param frame: Current frame
        :param detections: List of detections from CarDetection().video_detection
        :return: self.objects (List of objects)
        """

        # Check frame diff. ==> remove objects if not in range, return empty list
        if detections == []:
            for obj in self.objects:
                if obj.frame_diff_to_last(frame) > self.min_fr_dif:
                    self.objects.remove(obj)
            return []

        # If no objects currently exist, create new ones, append to objects list
        if len(self.objects) == 0:
            for detection in detections:
                self.obj_counter += 1
                new_obj = Object(frame,
                                 detection,
                                 id=self.obj_counter)
                self.objects.append(new_obj)
            return self.objects

        # If objects exist, match them.
        paired = 0  # Number of objects paired
        to_be_paired = len(detections)
        # Go through existing objects first
        for obj in self.objects:
            # If all were paired
            if paired >= to_be_paired:
                self.objects.remove(obj)  # Sketchy, removes the object if all were paired todo optimize
                break

            # Calculate euclidian distances to match with closest one
            distances = list()
            for det in detections:
                distances.append(euclidian_distance(obj.last_center_point, det[4]))
            # Get index of closest point
            index_min = min(range(len(distances)), key=distances.__getitem__)

            # Check if point is near enough(< min_point_dist_fr)
            if distances[index_min] <= self.min_point_dist_fr:
                # Add detection to object
                obj.add_point(frame, detections[index_min])
                # Remove detection from detections
                del detections[index_min]
                paired += 1

            # Check if object hasn't been seen in the last frames(>min_fr_diff) ==> delete object
            if obj.frame_diff_to_last(frame) > self.min_fr_dif:
                self.objects.remove(obj)
                continue

            # Check if object hasn't been moving ==> delete the object
            # Check the last 3 points (3 is enough as objects usually move just slightly)
            if obj.num_of_points >= 4:
                if [obj.last_center_point] * 3 == obj.center_points[::-1][1:4]:
                    self.objects.remove(obj)
                    continue

            # Remaining detections get created as new objects
            for detection in detections:
                self.obj_counter += 1
                new_obj = Object(frame,
                                 detection,
                                 id=self.obj_counter)
                self.objects.append(new_obj)
                continue

        return self.objects


class ObjectTracking(Observer):
    def __init__(self):
        self._objects: list = list()

        pass

    def update(self, notification_type) -> None:
        """
        """
        pass