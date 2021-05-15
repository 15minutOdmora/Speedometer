"""
Speedometer: A Python package for measuring the speed of objects captured in a still camera video, uses cv2.
"""
__title__ = "speedometer"
__author__ = "Liam Mislej"
__license__ = "MIT Licence"
__js__ = None
__js_url__ = None

from .object_tracking import ObjectTracking
from .radar import Radar
from .video import VideoPlayer
