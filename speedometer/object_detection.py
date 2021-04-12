from speedometer.Observer import Observer, Subject


class ObjectDetection(Observer):
    def __init__(self, speedometer, roi=None, typeofdetection="BackgroundSubstractorMOG2"):
        """
        :param speedometer:
        :param roi: list[y1, y2, x1, x1]  Where x, y is point of rectangle
        """
        self.som = speedometer  # spedometer object
        self.roi = roi
        if typeofdetection == "BackgroundSubstractorMOG2":
            self.object_detector_type = self.som.cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=300)  # TODO fix variables
        elif typeofdetection == "absdiff":
            self.object_detector_type = self.som.cv2.absdiff(self.som.first_frame, self.som.frame)
        elif typeofdetection == "createBackgroundSubtractorKNN":
            self.object_detector_type = self.som.cv2.createBackgroundSubtractorKNN(history=200, dist2Threshold=300)

    def update(self, notification_type) -> None:
        """
        """
        if notification_type == 'm':
            if self.roi is not None:
                # Save region of interest data
                self.som.roi = self.som.frame[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
            else:
                self.som.roi = self.som.frame
            # Apply background substractor created in notification_type 'b'
            self.som.mask = self.object_detector_type.apply(self.som.roi)
            # Remove gray pixels
            _, self.som.mask = self.som.cv2.threshold(self.som.mask,
                                                      254,
                                                      255,
                                                      self.som.cv2.THRESH_BINARY)

            self.som.contours, _ = self.som.cv2.findContours(self.som.mask,
                                                             self.som.cv2.RETR_TREE,
                                                             self.som.cv2.CHAIN_APPROX_SIMPLE)

            detections = list()
            for cnt in self.som.contours:
                # Calculate area of contours and ignore small elements
                area = self.som.cv2.contourArea(cnt)
                if area > 300:
                    # Get bounding rectangle
                    x, y, w, h = self.som.cv2.boundingRect(cnt)
                    # Get center point
                    center_point = (x + w // 2, y + h // 2)
                    self.som.cv2.rectangle(self.som.roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    self.som.cv2.circle(self.som.roi, center_point, 3, (0, 0, 255), 3)
                    # Append object size, position and center point to detections
                    detections.append([x, y, w, h, center_point])

        elif notification_type == 'b':
            # Set the speedometer mask TODO --> implement different methods
            self.object_detector_type = self.som.cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)
            return
        elif notification_type == 'a':
            return
        else:
            raise ValueError("Invalid value for notification_type, should be one of 'b', 'm', 'a'")