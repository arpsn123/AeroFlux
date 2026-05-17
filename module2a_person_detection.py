import cv2
import time
from ultralytics import YOLO


class PersonDetector:
    def __init__(self, model_path="yolov8x.pt", conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.PERSON_CLASS_ID = 0 # COCO class ID = 0 --> PERSON;

    def detect_person(self, frame): # takes one frame and returns detection 
        # shape gives : height, width, channel, we only need h and w, thats why [:2];
        frame_h, frame_w = frame.shape[:2] 

        results = self.model(frame, verbose=False) # running inference;
        # this internaly do : 
        # Resize + Normalize + Forward pass + NMS (Non-Max Suppression) + Return boxes
        # verbose=False ---> no SPAM CONSOLE LOGS(if any)

        best_person = None # store best bounding box
        max_conf = 0 # track highest confidence

        # Parse detections
        for result in results: # YOLOv8x may return multiple result batches
            
            for box in result.boxes: # each detected object ---> one box
                
                cls = int(box.cls[0].item()) # ---> class ID
                conf = float(box.conf[0].item())

 
                if cls == self.PERSON_CLASS_ID and conf >= self.conf_threshold: # filters only persons and that too having conf score larger than 50%
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0]) # co-ordinates of the BB; eg, [Top, left, Bottom, right] 

                    if conf > max_conf:
                        max_conf = conf
                        best_person = (x1, y1, x2, y2)

        if best_person:
            x1, y1, x2, y2 = best_person # best_person = co-ordinates of the best BB;

            # BB area ratio and info;
            bbox_area = (x2 - x1) * (y2 - y1)
            frame_area = frame_w * frame_h
            area_ratio = bbox_area / frame_area

            return {
                "person_present": True,
                "confidence": max_conf,
                "bbox": best_person, 
                "area_ratio": area_ratio
            }

        # NO PERSON DETECTED
        return {
            "person_present": False,
            "confidence": 0.0,
            "bbox": None,
            "area_ratio": 0.0
        }




if __name__ == "__main__":
    STREAM_URL = "http://XXX.XXX.XX.XX:XXXX/video"   # CHANGE THIS

    cap = cv2.VideoCapture(STREAM_URL)

    detector = PersonDetector(
        model_path="yolov8x.pt",   # Later swap to yolov8x.pt
        conf_threshold=0.5
    )

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Frame read failed")
            break

        frame_count += 1

        # Optional frame skipping for performance
        if frame_count % 3 == 0:
            detection = detector.detect_person(frame)

            if detection["person_present"]:
                x1, y1, x2, y2 = detection["bbox"]

                # Draw box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Label
                label = f"Person {detection['confidence']:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 255, 0), 2)

                # Area ratio
                cv2.putText(frame,
                            f"Area: {detection['area_ratio']:.3f}",
                            (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 0), 2)

            else:
                cv2.putText(frame, "No Person Detected",
                            (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            2)

        cv2.imshow("Module 2A - Person Detection", frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            print("[2A] Exiting...")
            break

        time.sleep(0.02)

    cap.release()
