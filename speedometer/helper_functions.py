"""
File consists of helper functions used across module.
"""
import json
import math


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


def euclid_dist(point1, point2):
    """
    Calculates the Euclidean distance between two points
    :param point1: First point
    :param point2: Second Point
    :return: Distance
    """
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def mmss_to_frames(fps, m, s=0):
    """
    Converts minutes and seconds of video to frames based on fps
    :param fps: frames per second of video
    :param m: minutes
    :param s: seconds
    :return: frame number
    """
    return int((m * 60 + s) / fps)
