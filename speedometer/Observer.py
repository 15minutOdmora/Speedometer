from __future__ import annotations
from abc import ABC, abstractmethod


class Subject(ABC):
    """
    Declares set of methods for managing subscribers
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach observer from subject
        """
        pass

    @abstractmethod
    def notify_beginning(self) -> None:
        """
        Notify all observers, at beginning of video
        """
        pass

    @abstractmethod
    def notify_mid(self) -> None:
        """
        Notify all observers, mid video
        """
        pass

    @abstractmethod
    def notify_end(self) -> None:
        """
        Notify all observers, at end of video
        """
        pass


class Observer(ABC):
    """
    Observer interface declares the update method that gets called by subjects.
    """

    @abstractmethod
    def update_beginning(self) -> None:
        """
        Receive update from subject, beginning --> when video is set to play
        video playing.
        """
        pass

    @abstractmethod
    def update_mid(self) -> None:
        """
        Receive update from subject, mid --> when video is being played
        video playing.
        """
        pass

    @abstractmethod
    def update_end(self) -> None:
        """
        Receive update from subject, end --> when video has ended playing
        video playing.
        """
        pass