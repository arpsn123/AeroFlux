from ultralytics import YOLO

class RemoteDetector:
    def __init__(
        self,
        model_path="yolov8x.pt",
        conf_threshold=0.4,
        trigger_frames=3
    ):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.trigger_frames = trigger_frames
        self.consecutive_remote_frames = 0

    def detect_remote(self, frame):

        # Safety check
        if frame is None:
            return {
                "remote_detected": False,
                "confidence": 0.0,
                "bbox": None,
                "ac_trigger": False
            }

        # Run inference
        results = self.model(frame, verbose=False)

        best_remote = None
        max_conf = 0.0

        # Parse detections
        for result in results:
            for box in result.boxes:

                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())

                # Get class name safely
                class_name = self.model.names[cls_id]

                # Detect "remote"
                if class_name == "remote" and conf >= self.conf_threshold:

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if conf > max_conf:
                        max_conf = conf
                        best_remote = (x1, y1, x2, y2)

        # Remote found
        if best_remote:

            self.consecutive_remote_frames += 1

            ac_trigger = (
                self.consecutive_remote_frames >= self.trigger_frames
            )

            return {
                "remote_detected": True,
                "confidence": max_conf,
                "bbox": best_remote,
                "ac_trigger": ac_trigger
            }

        # No remote
        self.consecutive_remote_frames = 0

        return {
            "remote_detected": False,
            "confidence": 0.0,
            "bbox": None,
            "ac_trigger": False
        }