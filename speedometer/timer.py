from speedometer.Observer import Observer
import json
import cv2
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
            self.point1 = point1
            self.point2 = point2
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
        Less than(is on left side): Compares x value of point to x value of line
        :param point: tuple(x, y)
        :return: bool
        """
        return point[0] <= self.x

    def __ge__(self, point):
        """
        More than(is on right side): Compares x value of point to x value of line
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


class Timer(Observer):
    def __init__(self, video, **kwargs):
        # start_line=None, end_line=None, distance=None, save_file=None
        self.video = video
        self.cv2 = video.cv2  # Points at the same cv2 as video
        self.curr_measured = []  # Currently measured objects
        # These get set once the lines are set through instantiating, reading from file or from set_line functions
        self.left_line = None
        self.right_line = None
        self.obj_trackers = []  # Set list for object trackers
        # Set the pointer to the object tracking object
        if not self.video.observers:  # If there is no ObjectTracker object
            print("There is no ObjectDetection set on Video.")
        else:
            # Attach self to all observers(ObjectTrackers) attached to the Video obj.
            for obj_tr in self.video.observers:
                obj_tr.attach(self)
                # Save trackers to list
                self.obj_trackers.append(obj_tr)

        """# Check args: start_line=(p1, p2), end_line=(p1, p2), distance=float(meters), save_file=filename/file path
        keys = kwargs.keys()
        if "start_line" in keys and "end_line" in keys and "distance" in keys:
            self.distance = kwargs["distance"]
            # This gets passed to the constructor, left and right lines are set there
            self.lines = (kwargs["start_line"], kwargs["end_line"])  # First passed is the start line
        # Check if lines and distance are saved in saved_data.json
        else:
            data = open_data_file()
            data_keys = data.keys()
            if "start_line" in data_keys and "end_line" in data_keys and "distance" in data_keys:
                self.lines = (data["start_line"], data["end_line"])
            else:
                self.lines = None

        if "save_file" in keys:
            save_file = kwargs["save_file"]
            date_time = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            self.save = True
            self.save_filename = save_file + "_" + date_time
            with open(self.save_filename + ".csv", mode='w') as file:
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
        else:
            self.save = False"""

        """# Start lines and end lines get made as line object if not none
        if start_line is not None and end_line is not None and distance is not None:
            # Assert if line is left or right
            start = [True, False]
            lines = [start_line[0], end_line[0]]  # x values
            index_min = min(lines, key=lines.__getitem__)
            index_max = max(lines, key=lines.__getitem__)
            self.left_line = Line(lines[index_min], start[index_min])
            self.right_line = Line(lines[index_max], start[index_max])
            self.line_direction = -1 if start_line - end_line > 0 else 1  # 1 x is increasing, -1 decreasing
            self.distance = distance
            print(self.left_line, self.right_line, self.line_direction)
        else:  # Check if lines are in saved_data.json
            data = open_data_file()
            if "start_line" in data.keys() and "end_line" in data.keys():
                # Assert if line is left or right, 
                start = [True, False]  # True is at index 0 as theres the start line below
                lines = [data["start_line"][0], data["end_line"][0]]  # x values
                index_min = min(lines, key=lines.__getitem__)
                index_max = max(lines, key=lines.__getitem__)
                self.left_line = Line(lines[index_min], start[index_min])
                self.right_line = Line(lines[index_max], start[index_max])
                self.line_direction = -1 if start_line - end_line > 0 else 1  # 1 x is increasing, -1 decreasing
                print(self.left_line, self.right_line, self.line_direction)
            if "distance" in data.keys():
                self.distance = data["distance"]"""

    def update(self) -> None:
        """  TODO currently implemented for only one object tracker, should be for more
        Receive update from subject(ObjectDetection) while video is playing.
        """
        # Get first tracker object
        tracker = self.obj_trackers[0]  # todo fix this
        # Go trough each currently detected object
        for obj in tracker.objects:
            # Last center position
            last_pos = obj.center_positions[-1]
            # Check if object is already being measured
            if obj in self.curr_measured:
                pass
            else:  # If not yet measured get object direction, and check if passed start or end line
                dir_x = 1 if obj.direction[0] > 0 else -1  # Todo make direction possible in y-cor
                # Check if object is between lines
                pass

    def set_distance(self, distance=None, save=False):
        """
        Opens a frame of the set video, can then set the distance between two points, creating two vertical lines
        at each. These lines act as start/end points for the timer, the input distance should be in meters as per
        real life.
        :param distance: float --> representing meters of distance between points in real life
        :param save: bool --> if the distance and points should get saved to saved_data.json
        :return:
        """
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
                self.cv2.imshow('Select lines', frame_copy[0])
            # RIGHT MOUSE BUTTON CLICK --> reset whole image
            elif event == self.cv2.EVENT_RBUTTONDOWN:
                # Set frame to original todo make undo possible and not reset
                frame_copy[0] = frame.copy()
                start_point[0] = None
                end_point[0] = None
                self.cv2.imshow('Select lines', frame_copy[0])

        self.cv2.imshow('Select lines', frame)
        self.cv2.setMouseCallback('Select lines', on_mouse)
        key = self.cv2.waitKey(0)
        if key == 27:  # 27 = esc in ASCII table
            print("Exiting")
        elif key == 115:  # 115 = s in ASCII table
            # Assert left and right lines, min x val is left line
            vert1 = ((start_point[0][0], 0), (start_point[0][0], height))
            vert2 = ((end_point[0][0], 0), (end_point[0][0], height))
            lines = [vert1, vert2]
            x_points = [vert1[0][0], vert2[0][0]]
            index_min = x_points.index(min(x_points))
            index_max = x_points.index(max(x_points))
            self.left_line = VerticalLine(lines[index_min])
            self.right_line = VerticalLine(lines[index_max])
            # Check if save is set to true, save to globals
            if save:
                # Todo Create save to file
                """data_dict = {
                    "left_line": start_line,
                    "right_line": end_line,
                    "distance": distance
                }
                save_to_data_file(data_dict)"""
