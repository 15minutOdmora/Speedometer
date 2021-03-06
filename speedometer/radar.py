from speedometer.Observer import Observer
from speedometer.helper_functions import open_data_file, save_to_data_file, euclid_dist

import cv2
import os
from datetime import datetime
import csv


class VerticalLine:
    """ Class representing a vertical line """
    def __init__(self, points):
        # Points = ((x1, y1), (x1, y2))
        point1 = points[0]
        point2 = points[1]
        # Check if points have same x value, raise error if not
        if point1[0] == point2[0]:
            # Point 1 is always the upper point on screen => min. y value
            points = [point1, point2]
            y_points = [point1[1], point2[1]]
            index_min = y_points.index(min(y_points))
            index_max = y_points.index(max(y_points))
            self.point1 = tuple(points[index_min])  # These have to be tuples, cv2.line expects tuples
            self.point2 = tuple(points[index_max])
            self.x = lambda y: point1[0]  # This is a function, when line is vertical x- point is always the same
        else:
            raise ValueError("Line is not vertical, x values of points do not match.")

    def __lt__(self, point):
        """
        Less than(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] < self.x(point[1])

    def __gt__(self, point):
        """
        More than(is on right side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] > self.x(point[1])

    def __le__(self, point):
        """
        Less than equal(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] <= self.x(point[1])

    def __ge__(self, point):
        """
        More than equal(is on right side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] >= self.x(point[1])

    def __repr__(self):
        """
        Representation of object used for printing.
        :return: str
        """
        return "Vertical line at x = {}.".format(self.point1[0])

    def __iter__(self):
        """
        Making class iterable, use for converting to tuple so that it can get saved in a json file
        :return:
        """
        for point in [self.point1, self.point2]:  # Kind of weird solution
            yield point


class Line:
    """ Class representing a line """
    def __init__(self, points):
        # Points = ((x1, y1), (x1, y2))
        point1 = points[0]
        point2 = points[1]
        # Point 1 is always the upper point on screen => min. y value
        points = [point1, point2]
        y_points = [point1[1], point2[1]]
        index_min = y_points.index(min(y_points))
        index_max = y_points.index(max(y_points))
        self.point1 = tuple(points[index_min])  # These have to be tuples, cv2.line expects tuples
        self.point2 = tuple(points[index_max])
        # Create function for calculating x val. given y val. -> Inverse of y = kx + n ==> x = (y - n)/k
        # Check if the line is vertical
        if self.point1[0] == self.point2[0]:
            self.x = lambda y: self.point1[0]
            self.vertical = True
        else:
            # Calculate k
            dx, dy = self.point1[0] - self.point2[0], self.point1[1] - self.point2[1]
            self.k = dy/dx
            # Calculate n, pick point1 as ref.
            self.n = self.point1[1] - self.k * self.point1[0]
            # Create inverse function
            self.x = lambda y: int((y - self.n)/self.k)
            self.vertical = False

    def __lt__(self, point):
        """
        Less than(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] < self.x(point[1])

    def __gt__(self, point):
        """
        More than(is on right side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] > self.x(point[1])

    def __le__(self, point):
        """
        Less than equal(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] <= self.x(point[1])

    def __ge__(self, point):
        """
        More than equal(is on right side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] >= self.x(point[1])

    def __repr__(self):
        """
        Representation of object used for printing.
        :return: str
        """
        if self.vertical:
            return "Vertical line at x = {}.".format(self.point1[0])
        else:
            return "Line: y = {0}x + {1}".format(round(self.k, 2), round(self.n, 2))

    def __iter__(self):
        """
        Making class iterable, use for converting to tuple so that it can get saved in a json file
        :return:
        """
        for point in [self.point1, self.point2]:  # Kind of weird solution todo Fix
            yield point


class Radar(Observer):
    """
    Radar class calculates the speed of object, has two lines as a timing field, can save measured data to a csv file
    """
    def __init__(self, video, **kwargs):
        """
        :param video: VideoPlayer object, is needed as the class wraps all of its observers(ObjectDetectors).
        :param save: bool -> If all set settings should be saved to saved_data.json. Preset: False
        :param load: bool -> If data should be loaded from saved_data.json
        :param lines: list[list[list[], list[]], list[list[], list[]]] -> list of two lines, each line is represented
        by a list consisting of two points where each point is a list pair [x, y] -> could all be tuples.
        :param out_file: str -> Filename of csv file, if the param. is set to some string -> data gets saved to file.
        :param print_measured:  bool -> If measured objects should be printed out to the console/shell.
        """
        self.video = video
        self.cv2 = video.cv2  # Points at the same cv2 as video
        self.curr_measured = []  # List of curr. measured objects
        self.curr_measured_dict = dict()  # Currently measured objects{obj:{"start_frame": sindex, "end_frame": eindex}}
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
        self.dpp = None  # Distance Per Pixel (m/px) based on y point of frame (as per space perception)
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
            self.save_measured_data = True

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

            # Finally: Try creating VerticalLines objects, assert left and right lines, min x val. is left line
            try:
                line1, line2, distance = VerticalLine(lines[0]), VerticalLine(lines[1]), lines[2]
                vertical = True
            except ValueError:  # If this happens -> lines are not vertical, create normal lines
                line1, line2, distance = Line(lines[0]), Line(lines[1]), lines[2]
                vertical = False

            lines_ = [line1, line2]
            x_points = [line1.point1[0], line2.point1[0]]
            index_min = x_points.index(min(x_points))
            index_max = x_points.index(max(x_points))
            self.left_line = lines_[index_min]
            self.right_line = lines_[index_max]
            self.distance = distance
            self._lines = (self.left_line, self.right_line, self.distance)
            print(self.left_line, self.right_line)
            # Set the distance between lines at given y-val.(height of screen)
            if vertical:  # If lines are vertical, dpp is a constant, pixel difference can be cal. between top points
                dist_between_lines_px = self.right_line.point1[0] - self.left_line.point1[0]  # Distance in px
                self.dpp = lambda y: self.distance / dist_between_lines_px
            else:  # If not vertical, distance changes per height and is not constant
                self.dpp = lambda y: distance / (self.right_line.x(y) - self.left_line.x(y))  # Distance per pixel

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
    def save_data_filename(self, filename) -> None:
        # Check if filename alredy exists
        if os.path.exists(filename):
            self._save_data_filename = filename
            self.save_measured_data = True
        # Create file
        else:
            self._save_data_filename = filename
            self.save_measured_data = True
            with open(self._save_data_filename, mode='w', newline="") as file:
                data_file = csv.writer(file, delimiter=',')
                data_file.writerow(["id",
                                    "start_time",
                                    "end_time",
                                    "time_diff",
                                    "x_dir",
                                    "y_dir",
                                    "start_frame",
                                    "end_frame",
                                    "frame_diff",
                                    "calculated_time",
                                    "calculated_distance",
                                    "speed_mps",
                                    "speed_kmh",
                                    "avg_size"])

    def save_to_file(self, data) -> None:
        """
        Saves given data to csv file.
        :param data: dict[data_name: value, ...]
        :return: None
        """
        # Dicts. are ordered from Python 3.7 up
        data_list = data.values()
        with open(self._save_data_filename, mode='a', newline="") as file:
            data_file = csv.writer(file, delimiter=',')
            data_file.writerow(data_list)

    def calculate_data_of_timed_object(self, obj) -> None:
        """
        Method calculates final data of timed object, if print is set to true --> prints results to console/shell
        if save is set to true, passes data to above method save_to_file.
        :param obj: Object
        :return: None
        """
        # Get index of start and end from which the object was timed/measured
        start_index = obj.frames.index(self.curr_measured_dict[obj]["start_frame"])
        end_index = obj.frames.index(self.curr_measured_dict[obj]["end_frame"])
        # Get start end time calculate difference
        start_time, end_time = obj.times[start_index], obj.times[end_index]
        time_diff = end_time - start_time
        # Get direction
        x_dir, y_dir = obj.direction()
        # Get start end frame, calculate diff.
        start_frame, end_frame = obj.frames[start_index], obj.frames[end_index]
        frame_diff = end_frame - start_frame
        # Calculate time based on frame diff
        calculated_time = self.TPF * frame_diff
        if calculated_time <= 0.4:  # Prone to zero division errors otherwise, todo make dynamic
            return
        # Calculate speed in km/h and m/s
        # Get distance traveled in x-direction, calculate based on dpp
        start_center_point, end_center_point = obj.center_points[start_index], obj.center_points[end_index]
        distance_in_px = abs(start_center_point[0] - end_center_point[0]) # euclid_dist(start_center_point, end_center_point)
        avg_height = int((start_center_point[1] + end_center_point[1]) / 2)  # y - cordinate
        distance_in_m = distance_in_px * self.dpp(avg_height)  # Doing this with avg. height isn't optimal, as the dist.
        # changes with height, assuming obj. are moving horizontally this works fine
        # Calculate speed
        speed_mps = round(distance_in_m / calculated_time, 2)
        speed_kmh = round(speed_mps * 3.6, 2)
        # Create data dict.
        data = {"id": obj.id,
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "time_diff": round(time_diff, 3),
                "x_dir": x_dir,
                "y_dir": y_dir,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "frame_diff": frame_diff,
                "calculated_time": round(calculated_time, 3),
                "calculated_distance": round(distance_in_m, 3),
                "speed_mps": speed_mps,
                "speed_kmh": speed_kmh,
                "avg_size": obj.average_size()}
        # If print to console/shell
        if self.print_measured:
            time_date = datetime.utcfromtimestamp(int(end_time)).strftime("%H:%M:%S %d-%m-%y (+00:00 UTC)")
            print_str = "Object({}) timed at: {}\n  ".format(obj.id, time_date)
            for key, value in data.items():
                print_str += "{}: {}, ".format(key, value)
            print(print_str)
        if self.save_measured_data:
            self.save_to_file(data)

    def update(self) -> None:
        """  TODO currently implemented for only one object tracker, should be for more
        Receive update from subject(ObjectDetection) while video is playing, check objects position.
        Checks which objects are in timing area, once the objects exits -> calculates its data.
        :return: None
        """
        # Get first tracker object
        tracker = self.obj_trackers[0]  # todo fix --> iterate through all detectors
        # Go trough each currently detected object
        for obj in tracker.objects:
            curr_pos = obj.center_points[-1]
            # Check if object is being timed
            if obj in self.curr_measured:
                # Check if object is out of the measuring area (outside of lines)
                # If measured and out of measuring area --> passed second line
                if self.left_line <= curr_pos >= self.right_line or self.left_line > curr_pos < self.right_line:
                    self.curr_measured.remove(obj)
                    # Set end frame index of object
                    self.curr_measured_dict[obj]["end_frame"] = obj.frames[-1]
                    # Pass to calculate data
                    self.calculate_data_of_timed_object(obj)
                    # Remove from currently measured
                    del self.curr_measured_dict[obj]
            # If not tracked, check if in between lines
            else:
                # If between lines save to curr_measured
                if self.left_line >= curr_pos >= self.right_line:  # Other way around cause of __lt__, __gt__
                    # Create object in dictionary, save start frame --> frames are unique numbers(should not repeat)
                    self.curr_measured.append(obj)
                    self.curr_measured_dict[obj] = {"start_frame": obj.frames[-1]}
        # Clear objects that are being timed but are not in the tracker anymore
        for timed_obj in self.curr_measured:
            if timed_obj not in tracker.objects:
                # Remove from list and dict
                self.curr_measured.remove(timed_obj)
                del self.curr_measured_dict[timed_obj]
        # Draw lines on frames
        self.cv2.line(self.video.frame, self.left_line.point1, self.left_line.point2, (255, 0, 0), 2)
        self.cv2.line(self.video.frame, self.right_line.point1, self.right_line.point2, (255, 0, 0), 2)

    def set_distance(self, distance=None, save=False):
        """
        Opens a frame of the set video, user can then set the distance between two points, creating two vertical lines
        at each point marking the timing area. These lines act as start/end points for the timer, the input distance
        should be in meters as per real life.
        :param distance: float --> representing meters of distance between points in real life
        :param save: bool --> if the distance and points should get saved to saved_data.json
        :return: None
        """
        # Check if distance variable was already set
        # Print instructions
        instr = "\nSelect lines button controls:\nLEFT MOUSE BUTTON to select start point of line, drag and " \
                "release to draw " \
                "line\nRIGHT MOUSE BUTTON to reset/delete all drawn lines\ns BUTTON(lowercase) to save and exit\n" \
                "esc BUTTON to exit without saving to object\n\n" \
                "The last drawn line will be saved as the distance."
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
            # Determine left and right lines, min x val is left line
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

    def set_two_distances(self, distance, save=False) -> None:
        """ Todo This works but it assumes the user(me) isn't a retard which is not good
        Method opens a frame of the video, user can then select two lines that act as the same distance based on
        perspective of camera.
        :param distance: float -> distance irl. in meters
        :param save: bool -> If the lines should be saved to saved_data.json
        :return: None
        """
        # Check if distance variable was already set
        # Print instructions
        instr = "\nSelect lines button controls:\nLEFT MOUSE BUTTON to select start point of line, drag and " \
                "release to draw " \
                "line\nRIGHT MOUSE BUTTON to reset/delete all drawn lines\ns BUTTON(lowercase) to save and exit\n" \
                "esc BUTTON to exit without saving to object\n\n" \
                "The last two drawn line will be saved as " \
                "distance lines. \n"
        print(instr)

        f_line_start_points = [None]
        f_line_end_points = [None]
        s_line_start_points = [None]
        s_line_end_points = [None]

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
                # Check if first line was already set
                if f_line_start_points[0] is None:
                    f_line_start_points[0] = (x, y)
                    f_line_end_points[0] = None
                else:
                    s_line_start_points[0] = (x, y)
                    s_line_end_points[0] = None
                # start_points.append((x, y))
            # LEFT MOUSE BUTTON CLICK UP --> Set end_point and draw line
            elif event == self.cv2.EVENT_LBUTTONUP:
                if f_line_end_points[0] is None:
                    f_line_end_points[0] = (x, y)
                    # Draw line when we get 2nd point
                    self.cv2.line(frame_copy[0], f_line_start_points[0], f_line_end_points[0], (0, 255, 0), 2)
                else:
                    s_line_end_points[0] = (x, y)
                    # Draw line when we get 2nd point
                    self.cv2.line(frame_copy[0], s_line_start_points[0], s_line_end_points[0], (0, 255, 0), 2)
                    # If both lines are drawn -> draw timing lines in blue
                    self.cv2.line(frame_copy[0], f_line_start_points[0], s_line_start_points[0], (255, 0, 0), 2)
                    self.cv2.line(frame_copy[0], f_line_end_points[0], s_line_end_points[0], (255, 0, 0), 2)
                # Refresh window
                self.cv2.imshow('Select distance', frame_copy[0])

            # RIGHT MOUSE BUTTON CLICK --> reset whole image
            elif event == self.cv2.EVENT_RBUTTONDOWN:
                # Set frame to original todo make undo possible and not reset
                frame_copy[0] = frame.copy()
                f_line_start_points[0] = None
                f_line_end_points[0] = None
                s_line_start_points[0] = None
                s_line_end_points[0] = None
                self.cv2.imshow('Select distance', frame_copy[0])

        self.cv2.imshow('Select distance', frame)
        self.cv2.setMouseCallback('Select distance', on_mouse)
        key = self.cv2.waitKey(0)
        if key == 27:  # 27 = esc in ASCII table
            print("Exiting")
            cap.release()
            self.cv2.destroyAllWindows()
        elif key == 115:  # 115 = s in ASCII table
            vert1 = (f_line_start_points[0], s_line_start_points[0])
            vert2 = (f_line_end_points[0], s_line_end_points[0])
            self.lines = (vert1, vert2, distance)  # Pass to setter
            cap.release()
            self.cv2.destroyAllWindows()
            # Check if save is set to true, save to globals
            if save:
                # Right and left line are set by now by the lines setter
                data = {"lines": (tuple(self.left_line), tuple(self.right_line), self.distance)}
                save_to_data_file(data)
