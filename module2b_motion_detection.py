'''
Frame
  ↓
Grayscale ---> motion doesnot need the color, it reduces to noise + computation;
  ↓
Gaussian Blur ---> smooth JPEG(frame) noise + flicker + tiny random changes;
  ↓
Frame Difference ---> abs(current - previous) ---> measures what changed
  ↓
Threshold ---> ignore micro-changes; eg, ignore tiny brightness change, but keep the movement;
  ↓
Motion Pixel Count ---> how many meaningful pixels changed ?????? eg, 2-3 pixels changed = NO         MOVEMENT, 20K pixels changed = major movement;
  ↓
Normalize
  ↓
motion_score


# one thing that is included is the ROI = Region Of Interest, as my video is gonna capture the moving fan too, and if i dont reject the upper portion of each frame or crop the interested area the always the motion detection engine will show HIGH-MOVEMENT for the moving FAN motion ;
eg, 
----------------------  <--- top ignored
XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXX
======================  <--- ROI starts
Analyze below only
'''

# motion Capture -->-> requires 'MEMORY', without memory ---> NO time comparison

import cv2  # grayscale conversion + blur + frame differencing + thresholding
# 'Motion History Smoothing' ---> best as automatically dropping older values;
from collections import deque


class MotionDetector:
    def __init__(
        self,
        # Gaussian blur kernel size ---> eg, large blur ---> less noiseless sensitivity; Small blur ---> more sensitivitymore false positives
        blur_size=(21, 21),
        threshold_value=25,  # ---> pixel difference cutoff
        # ---> final decision boundary, any motion greater than 2% = counted;
        motion_threshold=0.02,
        history_size=5,  # ---> smooth over last 5 frames
        min_area=500,  # --->  minimum contour area to count as real motion
        # % of frame height to IGNORE from top, eg, 0.35 = ignore 35% from the top;
        roi_start_ratio=0.35
    ):

        self.min_area = min_area
        self.roi_start_ratio = roi_start_ratio

        # previous processed frame
        self.prev_gray = None  # none ---> for the 1st run NO PREVIOUS frame;

        # Blur kernel
        self.blur_size = blur_size

        # Binary threshold for frame difference
        self.threshold_value = threshold_value

        # Final motion decision threshold
        self.motion_threshold = motion_threshold

        # Motion smoothing history
        # using DEQUE DS to rolling memory frame;
        self.motion_history = deque(maxlen=history_size)

    def extract_roi(self, frame):
        height = frame.shape[0]
        roi_y_start = int(
            height * self.roi_start_ratio
        )
        roi_frame = frame[
            roi_y_start:,
            :
        ]
        return roi_frame, roi_y_start

    def compute_motion(self, frame):

        if frame is None:
            return {
                "motion_score": 0.0,
                "motion_pixels": 0,
                "motion_detected": False
            }
        frame, roi_y_start = self.extract_roi(frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, self.blur_size, 0)

        if self.prev_gray is None:  # 1st frame initialization;
            self.prev_gray = gray
            return {
                "motion_score": 0.0,
                "motion_pixels": 0,
                "motion_detected": False,
                "roi_y_start": roi_y_start
            }

        # ---> frame difference
        frame_delta = cv2.absdiff(self.prev_gray, gray)

        # Update previous frame
        # now, as the 1st frame differnce done, updating the previous frame to present frame;
        self.prev_gray = gray

        thresh = cv2.threshold(
            frame_delta,
            self.threshold_value,
            255,
            cv2.THRESH_BINARY
        )[1]

        motion_pixels = cv2.countNonZero(thresh)  # count changed pixels
        # normalization ---> convert raw motion to [0,1]
        total_pixels = thresh.shape[0] * thresh.shape[1]
        # standardized percentage change of pixels; eg, 0.03 = 3% scene changed;
        raw_motion_score = motion_pixels / total_pixels

        self.motion_history.append(raw_motion_score)  # store latest score;
        smoothed_motion_score = (
            sum(self.motion_history) / len(self.motion_history))  # average recent history;

        # convert continuous ---> actionable, using threshold;
        motion_detected = smoothed_motion_score >= self.motion_threshold
        # eg,0.01 ---> False, 0.08 ---> True;

        return {
            "motion_score": smoothed_motion_score,
            "motion_pixels": motion_pixels,
            "motion_detected": motion_detected,  # binary control flag;
            "roi_y_start": roi_y_start
        }
