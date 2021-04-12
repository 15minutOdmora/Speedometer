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

    @abstractmethod
    def notify(self, notification_type) -> None:
        """
        Notify all observers
        """
        pass

    @abstractmethod
    def notify_one(self, observer: Observer, notification_type) -> None:
        """
        Notify one observer
        """
        pass


class Observer(ABC):
    """
    Observer interface declares the update method that gets called by subjects.
    """

    @abstractmethod
    def update(self, notification_type) -> None:
        """
        Receive update from subject.
        notification_type: 'b'(before), 'm'(mid), 'a'(after), represents when the notifcation was sent regarding
        video playing.
        """