import cv2
import time
from module1_input import CameraInput
from module2a_person_detection import PersonDetector
from module2b_motion_detection import MotionDetector
from module2c_remote_detection import RemoteDetector
from module3_feature_aggregation import FeatureAggregator
from module5_decision_engine import DecisionEngine
from module6_udp_controller import UDPFanController

STREAM_URL = "http://XXX.XXX.XX.XX:XXXX/video"
MODEL_PATH = "yolov8x.pt"
DETECTION_INTERVAL = 3

camera = CameraInput(STREAM_URL)
person_detector = PersonDetector(
    model_path=MODEL_PATH,
    conf_threshold=0.5
)
motion_detector = MotionDetector(
    blur_size=(21, 21),
    threshold_value=25,
    motion_threshold=0.02,
    history_size=5
)
remote_detector = RemoteDetector(
    model_path=MODEL_PATH,
    conf_threshold=0.4,
    trigger_frames=3
)
feature_aggregator = FeatureAggregator()
decision_engine = DecisionEngine()
udp_controller = UDPFanController(
    fan_ip="XXX.XXX.XX.XX"
)
ENABLE_UDP = True

if not camera.connect():
    print("[MAIN] Camera connection failed")
    exit()

frame_width = 640
frame_height = 480
fps_record = 20.0
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video_writer = cv2.VideoWriter(
    r"E:\404_Found\Vision-Based_Adaptive_Comfort_Cooling_System_with_Context_Inference\Recorded_Results\Annotated_Live_Feed.mp4",
    fourcc,
    fps_record,
    (frame_width, frame_height))


print("[MAIN] Pipeline started (Module 1 + Module 2A)")
print("[MAIN] Press 'q' to quit")


frame_count = 0

last_person_data = {
    "person_present": False,
    "confidence": 0.0,
    "bbox": None,
    "area_ratio": 0.0
}
AC_MODE = False


while True:

    frame, ts = camera.get_frame()

    if frame is None:
        continue

    frame_count += 1

    if frame_count % DETECTION_INTERVAL == 0:
        last_person_data = person_detector.detect_person(frame)

    motion_data = motion_detector.compute_motion(frame)

    roi_y = motion_data["roi_y_start"]
    cv2.line(
        frame,
        (0, roi_y),
        (frame.shape[1], roi_y),
        (0, 255, 255),
        2
    )
    cv2.putText(
        frame,
        "ROI START (Fan Ignored Above)",
        (10, roi_y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (0, 255, 255),
        2
    )

    remote_data = remote_detector.detect_remote(frame)

    # AC Trigger
    if remote_data["ac_trigger"]:
        AC_MODE = True

    system_state = feature_aggregator.aggregate(
        person_data=last_person_data,
        motion_data=motion_data,
        remote_data=remote_data,
        AC_MODE=AC_MODE
    )

    if last_person_data["person_present"]:

        x1, y1, x2, y2 = last_person_data["bbox"]

        # Draw bounding box
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # Confidence label
        label = f"Person {last_person_data['confidence']:.2f}"

        cv2.putText(
            frame,
            label,
            (x1, max(30, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # Area ratio
        cv2.putText(
            frame,
            f"Area: {last_person_data['area_ratio']:.3f}",
            (x1, min(frame.shape[0] - 10, y2 + 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

    else:
        cv2.putText(
            frame,
            "No Person Detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    motion_score = motion_data["motion_score"]
    motion_pixels = motion_data["motion_pixels"]
    motion_detected = motion_data["motion_detected"]

    # Motion state label
    if motion_detected:
        motion_label = f"Motion: {motion_score:.3f} | ACTIVE"
        motion_color = (255, 0, 255)   # Purple
    else:
        motion_label = f"Motion: {motion_score:.3f} | STILL"
        motion_color = (200, 200, 200)  # Gray

    decision_data = decision_engine.decide(
        system_state
    )

    # Display motion score
    cv2.putText(
        frame,
        motion_label,
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        motion_color,
        2
    )

    # Display raw motion pixels
    cv2.putText(
        frame,
        f"Motion Pixels: {motion_pixels}",
        (20, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    if remote_data["remote_detected"]:

        x1, y1, x2, y2 = remote_data["bbox"]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 165, 0),
            2
        )

        cv2.putText(
            frame,
            f"Remote {remote_data['confidence']:.2f}",
            (x1, max(30, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 165, 0),
            2
        )

    # Presence
    cv2.putText(
        frame,
        f"Presence: {system_state['presence_state']}",
        (410, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )

    # Activity
    cv2.putText(
        frame,
        f"Activity: {system_state['activity_level']} ({system_state['motion_score']:.3f})",
        (410, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 0, 255),
        2
    )
    # Remote
    cv2.putText(
        frame,
        f"Remote: {system_state['remote_state']}",
        (410, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 165, 0),
        2
    )

    power_text = (
        "ON"
        if decision_data["power"]
        else "OFF"
    )

    power_color = (
        (0, 255, 0)
        if decision_data["power"]
        else (0, 0, 255)
    )

    cv2.putText(
        frame,
        f"Power: {power_text}",
        (410, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        power_color,
        2
    )

    # Target Speed
    cv2.putText(
        frame,
        f"Target Speed: {decision_data['target_speed']}",
        (410, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    # Reason
    cv2.putText(
        frame,
        f"Reason: {decision_data['reason']}",
        (410, 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 255),
        2
    )

    # UDP Send Status
    udp_text = (
        "SEND"
        if decision_data["send_update"]
        else "HOLD"
    )

    udp_color = (
        (0, 165, 255)
        if decision_data["send_update"]
        else (150, 150, 150)
    )

    cv2.putText(
        frame,
        f"UDP Action: {udp_text}",
        (410, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        udp_color,
        2
    )

    ac_label = "AC MODE: ON" if AC_MODE else "AC MODE: OFF"
    ac_color = (255, 0, 0) if AC_MODE else (100, 100, 100)

    cv2.putText(
        frame,
        ac_label,
        (10, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        ac_color,
        2
    )

    fps = camera.get_fps()
    status = camera.get_status()

    cv2.putText(
        frame,
        f"FPS: {fps:.2f}",
        (20, frame.shape[0] - 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Status: {status}",
        (20, frame.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # decision_data = decision_engine.decide(
    #     system_state)

    if ENABLE_UDP:
        udp_result = udp_controller.execute(
            decision_data
        )
        cv2.putText(
        frame,
        f"UDP: {udp_result['action']}",
        (410, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 165, 0),
        2
    )



    cv2.imshow("Vision-Based Adaptive Cooling System", frame)
    video_writer.write(frame)
    

    key = cv2.waitKey(1)

    if key == ord("q"):
        print("[MAIN] Exiting...")
        break

    time.sleep(0.02)


if camera.cap:
    camera.cap.release()

video_writer.release()
cv2.destroyAllWindows()

