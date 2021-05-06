from speedometer.Observer import Observer
import json
import cv2
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


class Line:
    """ Class representing a line, has methods for checking if point is above or below line."""
    def __init__(self, points):
        # Point = [x, y]
        self.point1 = points[0]
        self.point2 = points[1]
        # Check if line is vertical
        if self.point1[0] == self.point2[0]:
            self.is_vertical = True
            self.x = None
            self.k = None
        else:
            self.is_vertical = False
            # Get slope koef.
            x_diff = self.point1[0] - self.point2[0]
            y_diff = self.point1[1] - self.point2[1]
            self.k = round(y_diff / x_diff, 4)
            # Calculate n
            n = self.point1[1] - self.k * self.point1[0]
            # Inverse of  y = kx + n  ==>  x = ...
            self.x = lambda y: round((y - n)/self.k)
            print("k {} n {}".format(self.k, n))

    def is_above(self, point):
        """ Checks if point is above line (<=), if vertical line check if on left side(inverted koor. for px)
        :param point: point [x, y]
        :return: True/False
        """
        if self.is_vertical:
            return point[0] <= self.point1[0]
        # Two cases of 'above' depending on slope of line
        else:
            if self.k > 0:
                return point[0] >= self.x(point[1])
            else:
                return point[0] <= self.x(point[1])

    def is_below(self, point):
        """ Checks if point is above line (>=), if vertical line check if on right side(inverted koor. for px)
        :param point: point [x, y]
        :return: True/False
        """

        if self.is_vertical:
            return point[0] >= self.point1[0]
        # Two cases of 'above' depending on slope of line
        else:
            if self.k > 0:
                return point[0] <= self.x(point[1])
            else:
                return point[0] >= self.x(point[1])


class Timer(Observer):
    def __init__(self, video, start_line=None, end_line=None, distance=None):
        self.video = video
        # Points at the same cv2 as video
        self.cv2 = video.cv2
        # Set the pointer to the object tracking object
        if not self.video.observers:  # If there is no ObjectTracker object
            print("There is no ObjectDetection set on Video")
        else:
            # Attach self to all observers(ObjectTrackers) attached to the Video obj.
            for obj_tr in self.video.observers:
                obj_tr.attach(self)

        # Start lines and end lines get made as line object if not none
        if start_line is not None and end_line is not None and distance is not None:
            self.start_line = Line(start_line)
            self.end_line = Line(end_line)
            self.distance = distance
        else:  # Check if lines are in saved_data.json
            data = open_data_file()
            if "start_line" in data.keys() and "end_line" in data.keys():
                self.start_line = Line(data["start_line"])
                self.end_line = Line(data["end_line"])
            if "distance" in data.keys():
                self.distance = data["distance"]

    def update(self) -> None:
        """
        Receive update from subject(ObjectDetection) while video is playing.
        """

        pass

    def set_lines(self, distance=None, save=False):
        """
        Function opens a frame of the current video to set the start and end lines with mouse
        Everything is done on a copy of the opened frame so it can be reset
        TODO make undo work and not reset
        If save is set to true --> lines get saved to globals.json
        """
        # Print instructions
        instr = "\nSelect lines button controls:\nLEFT MOUSE BUTTON to select start point of line, drag and " \
                "release to draw " \
                "line\nRIGHT MOUSE BUTTON to reset/delete all drawn lines\ns BUTTON(lowercase) to save and exit\n" \
                "esc BUTTON to exit without saving\n\n" \
                "The last two drawn lines will be saved as " \
                "start and end lines. \nFirst line drawn is start line(colored green) second is end line" \
                "(colored red)."
        print(instr)

        start_point = []
        end_point = []

        # Get one frame of video
        cap = self.cv2.VideoCapture(self.video.video_list[0])
        _, frame = cap.read()
        # Resize frame so roi matches at the end
        frame = self.cv2.resize(frame, self.video.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        # todo fix this utter disgrace of a solution
        frame_copy = [frame.copy()]  # Single cell dirty trick, you can't change this var. inside bottom fun. otherwise

        def on_mouse(event, x, y, flags, params):
            """
            Method for on_mouse click events when setting the line
            :return: None
            """
            # LEFT MOUSE BUTTON CLICK UP --> Set start_point
            if event == self.cv2.EVENT_LBUTTONDOWN:
                start_point.append((x, y))
            # LEFT MOUSE BUTTON CLICK UP --> Set end_point and draw line
            elif event == self.cv2.EVENT_LBUTTONUP:
                end_point.append((x, y))
                # Set color based on consecutive number of line
                if len(end_point) % 2 == 0:
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)
                #
                # Draw line when we get 2nd point
                self.cv2.line(frame_copy[0], start_point[-1], end_point[-1], color, 2)
                # Refresh window
                self.cv2.imshow('Select lines', frame_copy[0])
            # RIGHT MOUSE BUTTON CLICK --> reset whole image
            elif event == self.cv2.EVENT_RBUTTONDOWN:
                # Set frame to original todo make undo possible and not reset
                frame_copy[0] = frame.copy()
                start_point.clear()
                end_point.clear()
                self.cv2.imshow('Select lines', frame_copy[0])

        self.cv2.imshow('Select lines', frame)
        self.cv2.setMouseCallback('Select lines', on_mouse)
        key = self.cv2.waitKey(0)
        if key == 27:  # 27 = esc in ASCII table
            print("Exiting")
        elif key == 115:  # 115 = s in ASCII table
            start_line = (tuple(start_point[-2]), tuple(end_point[-2]))
            end_line = (tuple(start_point[-1]), tuple(end_point[-1]))
            self.start_line = Line(start_line)
            self.end_line = Line(end_line)
            print("Start line: {}\nEnd line: {}".format(start_line, end_line))
            # Check if save is set to true, save to globals
            if save:
                data_dict = {
                    "start_line": start_line,
                    "end_line": end_line,
                    "distance": distance
                }
                save_to_data_file(data_dict)

    def set_vertical_lines(self, distance=None, save=False):
        """
                Function opens a frame of the current video to set the start and end lines with mouse
                Everything is done on a copy of the opened frame so it can be reset
                TODO make undo work and not reset
                If save is set to true --> lines get saved to globals.json
                """
        # Print instructions
        instr = "\nSelect vertical lines button controls:\nLEFT MOUSE BUTTON to select start point of line, drag and " \
                "release to draw " \
                "line\nRIGHT MOUSE BUTTON to reset/delete all drawn lines\ns BUTTON(lowercase) to save and exit\n" \
                "Esc BUTTON to exit without saving\n\n" \
                "The last two drawn lines will be saved as " \
                "start and end lines. \nFirst line drawn is start line(colored green) second is end line" \
                "(colored red).\nIf the drawn lines aren't fully vertical, they get set vertical based on the middle " \
                "x point of drawn line"
        print(instr)

        start_point = []
        end_point = []

        # Get one frame of video
        cap = self.cv2.VideoCapture(self.video.video_list[0])
        _, frame = cap.read()
        # Resize frame so roi matches at the end
        frame = self.cv2.resize(frame, self.video.resize, fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        # todo fix this utter disgrace of a solution
        frame_copy = [frame.copy()]  # Single cell dirty trick, you can't change this var. inside bottom fun. otherwise

        def on_mouse(event, x, y, flags, params):
            """
            Method for on_mouse click events when setting the line
            :return: None
            """
            # LEFT MOUSE BUTTON CLICK UP --> Set start_point
            if event == self.cv2.EVENT_LBUTTONDOWN:
                start_point.append((x, y))
            # LEFT MOUSE BUTTON CLICK UP --> Set end_point and draw line
            elif event == self.cv2.EVENT_LBUTTONUP:
                end_point.append((x, y))
                # Set color based on consecutive number of line
                if len(end_point) % 2 == 0:
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)
                # Make vertical
                middle_x_val = int((start_point[-1][0] + end_point[-1][0]) / 2)
                start_point[-1] = (middle_x_val, start_point[-1][1])
                end_point[-1] = (middle_x_val, end_point[-1][1])
                # Draw line when we get 2nd point
                self.cv2.line(frame_copy[0], start_point[-1], end_point[-1], color, 2)
                # Refresh window
                self.cv2.imshow('Select lines', frame_copy[0])
            # RIGHT MOUSE BUTTON CLICK --> reset whole image
            elif event == self.cv2.EVENT_RBUTTONDOWN:
                # Set frame to original todo make undo possible and not reset
                frame_copy[0] = frame.copy()
                start_point.clear()
                end_point.clear()
                self.cv2.imshow('Select lines', frame_copy[0])

        self.cv2.imshow('Select lines', frame)
        self.cv2.setMouseCallback('Select lines', on_mouse)
        key = self.cv2.waitKey(0)
        if key == 27:  # 27 = esc in ASCII table
            print("Exiting")
        elif key == 115:  # 115 = s in ASCII table
            start_line = (tuple(start_point[-2]), tuple(end_point[-2]))
            end_line = (tuple(start_point[-1]), tuple(end_point[-1]))
            self.start_line = Line(start_line)
            self.end_line = Line(end_line)
            print("Start line: {}\nEnd line: {}".format(start_line, end_line))
            # Check if save is set to true, save to globals
            if save:
                data_dict = {
                    "start_line": start_line,
                    "end_line": end_line,
                    "distance": distance
                }
                save_to_data_file(data_dict)
