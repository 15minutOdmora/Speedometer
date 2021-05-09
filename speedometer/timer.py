from speedometer.Observer import Observer
import json
import cv2
import os
from time import time
from datetime import datetime
import csv


# TODO put these two functions in a separate file
def open_data_file():
    """ Opens the saved_data.json returns the dic.
    :return: dict()
    """
    with open("saved_data.json", 'r') as glob:
        data = json.load(glob)
    return data


def save_to_data_file(dict):
    """ Saves the keys and values from dict to saved_data.json
    :param dict: dict() containing key, value pairs
    """
    with open("saved_data.json", 'r') as glob:
        data = json.load(glob)

    for key, value in dict.items():
        data[key] = value

    with open("saved_data.json", 'w') as glob:
        json.dump(data, glob)


class VerticalLine:
    """ Class representing a vertical line """
    def __init__(self, points):
        # Points = ((x1, y1), (x1, y2))
        point1 = points[0]
        point2 = points[1]
        # Check if points have same x value, raise error if not
        if point1[0] == point2[0]:
            self.point1 = tuple(point1)  # These have to be tuples, cv2.line expects tuples
            self.point2 = tuple(point2)
            self.x = point1[0]
        else:
            raise ValueError("Line is not vertical, x values of points do not match.")

    def __lt__(self, point):
        """
        Less than(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] < self.x

    def __gt__(self, point):
        """
        More than(is on right side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] > self.x

    def __le__(self, point):
        """
        Less than equal(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] <= self.x

    def __ge__(self, point):
        """
        More than equal(is on right side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] >= self.x

    def __repr__(self):
        """
        Representation of object used for printing.
        :return: str
        """
        return "Vertical line at x = {}.".format(self.x)

    def __iter__(self):
        """
        Making class iterable, use for converting to tuple so that it can get saved in a json file
        :return:
        """
        for point in [self.point1, self.point2]:  # Kind of weird solution
            yield point


class Timer(Observer):
    def __init__(self, video, **kwargs):
        self.video = video
        self.cv2 = video.cv2  # Points at the same cv2 as video
        self.curr_measured = []  # Currently measured objects(are between set lines)
        self.obj_trackers = []  # Set list for object trackers
        # Get video FPS, and calculate constants
        self.FPS = self.video.fps  # Should always be set (fr/s)
        self.TPF = 1 / self.FPS  # Time Per Frame in seconds (s/fr)
        # Set the pointer to the object tracking object
        if not self.video.observers:  # If there is no ObjectTracker object
            print("There is no ObjectDetection set on Video.")
        else:
            # Attach self to all observers(ObjectTrackers) attached to the Video obj.
            for obj_tr in self.video.observers:
                obj_tr.attach(self)
                # Save trackers to list
                self.obj_trackers.append(obj_tr)
        # This get set when lines are set in the property.setter
        self._lines = None
        self.left_line = None
        self.right_line = None
        self.distance = None
        self.DPP = None  # Distance Per Pixel (m/px)
        # Check kwargs
        keys = kwargs.keys()
        # If save is set to True
        self.save = False
        if "save" in keys:  # For saving parameters in saved_data.json used in lines setter
            if kwargs["save"]:
                self.save = True
        # If load set to True
        if "load" in keys:
            if kwargs["load"]:
                # Load data from saved_data
                data = open_data_file()
                data_keys = data.keys()
                if "lines" in data_keys:
                    self.lines = data["lines"]
                else:
                    self.lines = None
                pass
        # If load is not set, get variables from paramaters
        else:
            if "lines" in keys:
                self.lines = kwargs["lines"]
            else:
                self.lines = None

        # Save file gets set in setter along with save_measured_data
        self._save_data_filename = None
        self.save_measured_data = False
        if "out_file" in keys:  # For saving actual data in a csv file
            filename = kwargs["out_file"]
            # Check if filename has csv extension
            if not filename.endswith(".csv"):
                filename += ".csv"
                self.save_data_filename = filename
            self.save_data_filename = filename

        self.print_measured = False  # Used to print object data when object is measured
        # If print measured is set to true
        if "print_measured" in keys:
            if kwargs["print_measured"]:
                self.print_measured = True

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, lines):
        """
        :param lines: Tuple(Line1, Line2, distance)
        :return: None
        """
        if lines is None:
            print("WARNING: No lines are set. Set them before this turns out in an error.")
            return
        try:
            line1, line2, distance = lines[0], lines[1], lines[2]
            # Check if types match
            if not (isinstance(line1, tuple) or isinstance(line1, list)):
                raise ValueError("Value for line1 is not a tuple or a list.")
            if not (isinstance(line2, tuple) or isinstance(line2, list)):
                raise ValueError("Value for line2 is not a tuple or a list.")
            if not(isinstance(distance, float) or isinstance(distance, int)):
                raise ValueError("Value for variable distance is not a float or int.")

            # Finally: Create VerticalLines objects, assert left and right lines, min x val. is left line
            line1, line2, distance = VerticalLine(lines[0]), VerticalLine(lines[1]), lines[2]
            lines_ = [line1, line2]
            x_points = [line1.x, line2.x]
            index_min = x_points.index(min(x_points))
            index_max = x_points.index(max(x_points))
            self.left_line = lines_[index_min]
            self.right_line = lines_[index_max]
            self.distance = distance
            self._lines = (self.left_line, self.right_line, self.distance)
            print(self.left_line, self.right_line)
            # Calculate DPP
            dist_between_lines = self.right_line.x - self.left_line.x # Distance in px
            self.DPP = self.distance / dist_between_lines

            # Save data settings to saved_data.json
            if self.save:
                data = {"lines": (tuple(self.left_line), tuple(self.right_line), self.distance)}
                save_to_data_file(data)

        except IndexError:
            error = "Missing value, the lines variable is a tuple consisting of 3 values: (line1, line2, distance). " \
                    "Check that you are not missing one."
            raise IndexError(error)

    @property
    def save_data_filename(self):
        return self._save_data_filename

    @save_data_filename.setter
    def save_data_filename(self, filename):
        # Check if filename alredy exists
        if os.path.exists(filename):
            self._save_data_filename = filename
            self.save_measured_data = True
        # Create file
        else:
            self._save_data_filename = filename
            self.save_measured_data = True
            with open(self._save_data_filename, mode='w') as file:
                data_file = csv.writer(file, delimiter=',')
                data_file.writerow(["id",
                                    "start_time",
                                    "end_time",
                                    "time_diff",
                                    "direction",
                                    "frames",
                                    "calculated_time",
                                    "speed_mps",
                                    "speed_kmh"])

    def save_to_file(self, data):
        """ Todo function calculates speed, direction and other data, saves to file"""
        pass

    def calculate_data_of_timed_object(self, obj):
        """ Todo Calculate data of object """
        print("Object Finished: ", obj)
        pass

    def update(self) -> None:
        """  TODO currently implemented for only one object tracker, should be for more
        Receive update from subject(ObjectDetection) while video is playing, assert objects position.
        Checks which objects are in timing area, once the objects exits calculates its data.
        """
        # Get first tracker object
        tracker = self.obj_trackers[0]  # todo fix --> iterate through all detectors
        # Go trough each currently detected object
        for obj in tracker.objects:
            curr_pos = obj.center_points[-1]  # Current center position
            # Check if object is being timed
            if obj in self.curr_measured:
                # Check if object is out of the measuring area (outside of lines)
                # If measured and out of measuring area --> passed second line
                if self.left_line < curr_pos > self.right_line or self.left_line > curr_pos < self.right_line:
                    # Pass to calculate data
                    self.calculate_data_of_timed_object(obj)
                    # Remove from currently measured
                    self.curr_measured.remove(obj)
            # If not tracked, check if in between lines
            else:
                # If between lines save to curr_measured
                if self.left_line > curr_pos > self.right_line:  # Other way around cause of __lt__, __gt__
                    self.curr_measured.append(obj)
        # Clear objects that are being timed but are not in the tracker anymore
        for timed_obj in self.curr_measured:
            if timed_obj not in tracker.objects:
                self.curr_measured.remove(timed_obj)
        print("_____________________________________________________________________________________")
        print("Tracker objects: ", tracker.objects)
        print("Timer objects:   ", self.curr_measured)
        # Draw lines
        self.cv2.line(self.video.frame, self.left_line.point1, self.left_line.point2, (255, 0, 0), 2)
        self.cv2.line(self.video.frame, self.right_line.point1, self.right_line.point2, (255, 0, 0), 2)

    def set_distance(self, distance=None, save=False):
        """
        Opens a frame of the set video, can then set the distance between two points, creating two vertical lines
        at each. These lines act as start/end points for the timer, the input distance should be in meters as per
        real life.
        :param distance: float --> representing meters of distance between points in real life
        :param save: bool --> if the distance and points should get saved to saved_data.json
        :return:
        """
        # Check if distance variable was already set
        # Print instructions
        instr = "\nSelect lines button controls:\nLEFT MOUSE BUTTON to select start point of line, drag and " \
                "release to draw " \
                "line\nRIGHT MOUSE BUTTON to reset/delete all drawn lines\ns BUTTON(lowercase) to save and exit\n" \
                "esc BUTTON to exit without saving to object\n\n" \
                "The last two drawn line will be saved as " \
                "start and end lines. \nFirst line drawn is start line(colored green) second is end line" \
                "(colored red)."
        print(instr)

        start_point = [None]
        end_point = [None]

        # Get one frame of video
        cap = self.cv2.VideoCapture(self.video.video_list[0])
        _, frame = cap.read()
        # Resize frame so roi matches at the end
        frame = self.cv2.resize(frame, self.video.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        _, height = self.video.resize
        # todo fix this utter disgrace of a solution
        frame_copy = [frame.copy()]  # Single cell dirty trick, you can't change this var. inside bottom fun. otherwise

        def on_mouse(event, x, y, flags, params):
            """
            Method for on_mouse click events when setting the line
            :return: None
            """
            # LEFT MOUSE BUTTON CLICK UP --> Set start_point
            if event == self.cv2.EVENT_LBUTTONDOWN:
                start_point[0] = (x, y)
            # LEFT MOUSE BUTTON CLICK UP --> Set end_point and draw line
            elif event == self.cv2.EVENT_LBUTTONUP:
                end_point[0] = (x, y)
                # Draw line when we get 2nd point
                self.cv2.line(frame_copy[0], start_point[0], end_point[0], (0, 255, 0), 2)
                # Draw vertical lines at each side
                vert1 = ((start_point[0][0], 0), (start_point[0][0], height))
                vert2 = ((end_point[0][0], 0), (end_point[0][0], height))
                self.cv2.line(frame_copy[0], vert1[0], vert1[1], (255, 0, 0), 2)
                self.cv2.line(frame_copy[0], vert2[0], vert2[1], (255, 0, 0), 2)
                # Refresh window
                self.cv2.imshow('Select distance', frame_copy[0])
            # RIGHT MOUSE BUTTON CLICK --> reset whole image
            elif event == self.cv2.EVENT_RBUTTONDOWN:
                # Set frame to original todo make undo possible and not reset
                frame_copy[0] = frame.copy()
                start_point[0] = None
                end_point[0] = None
                self.cv2.imshow('Select distance', frame_copy[0])

        self.cv2.imshow('Select distance', frame)
        self.cv2.setMouseCallback('Select distance', on_mouse)
        key = self.cv2.waitKey(0)
        if key == 27:  # 27 = esc in ASCII table
            print("Exiting")
            cap.release()
            self.cv2.destroyAllWindows()
        elif key == 115:  # 115 = s in ASCII table
            # Assert left and right lines, min x val is left line
            vert1 = ((start_point[0][0], 0), (start_point[0][0], height))
            vert2 = ((end_point[0][0], 0), (end_point[0][0], height))
            self.lines = (vert1, vert2, distance)  # Pass to setter
            cap.release()
            self.cv2.destroyAllWindows()
            # Check if save is set to true, save to globals
            if save:
                # Right and left line are set by now by the lines setter
                data = {"lines": (tuple(self.left_line), tuple(self.right_line), self.distance)}
                save_to_data_file(data)

    def move_line(self):
        """ Todo Make function to move lines """
        pass
