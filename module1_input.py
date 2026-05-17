import cv2
import time  # timestamps + delays
# deque --> efficient fixed-size buffer (for FPS)
from collections import deque


class CameraInput:  # using class for the Total Encapsulation;
    def __init__(self, stream_url):  # __init__(constructor) ---> runs when object is created
        # s---> stores camera URL(mobile http stream)
        self.stream_url = stream_url

        self.cap = None  # ---> placeholder for video capture object

        self.last_frame_time = 0  # used to detect camera freeze/timeout

        # ---> System health indicator : INIT(initialization) / OK / DEGRADED / FAILED
        self.status = "INIT"

        # maxlen = 30 ---> stores last 30 FPS values in the buffer; the buffer ---> is deque = double endded queue, allows to insertion and deletion from the rear + front t O(1)
        self.fps_buffer = deque(maxlen=30)
        # this line : auto removes old values;

        self.prev_time = time.time()  # this is for calculating the FPS;

    def connect(self):  # establishig connection to the camera;

        print("[INPUT] Connecting to camera...")

        # open video stream, internaly create decoder + starts pulling frames;
        self.cap = cv2.VideoCapture(self.stream_url)

        # adjust the number of frames(1) stored in the internal buffer; 1 ---> to reduce lag (only keep the newest frame)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # gives camera time to initialize, otherwise error(NO STREAM)
        time.sleep(1)

        if not self.cap.isOpened():
            self.status = "FAILED"  # make the status FAILED;
            print("[INPUT] Failed to connect")
            return False

        self.status = "OK"
        print("[INPUT] Connected")
        return True

    def reconnect(self):  # handles recovery;
        print("[INPUT] Reconnecting...")
        if self.cap:
            self.cap.release()  # release the capture object if captured anything, and reconnect later;
        time.sleep(2)
        return self.connect()

    def get_frame(self): # this is returing 2 things : frame and time;
        
        if self.cap is None or not self.cap.isOpened():
            if not self.reconnect():
                return None, None
            
        for _ in range(3):
            # grab the next frame 'without' decoding it; ---> very fast as no cpu involved;
            self.cap.grab()
            # .retrieve() ---> decodes and returns the frame grabbed by the last grab() call ---> slower as cpu intersive

        # read() ---> executes .grab() then .retrieve() in one go.
        ret, frame = self.cap.read()
        # ret = success flag
        # frame = actual image in form of numpy array

        if not ret or frame is None:
            self.status = "DEGRADED"  # not fully dead but broken;
            print("[INPUT] Frame read failed")
            self.reconnect()
            return None, None

        now = time.time()
        self.last_frame_time = now
        # marks last successful frame time ---> used to detect faliure later;

        # FPS calculation
        dt = now - self.prev_time
        self.prev_time = now
        if dt > 0:
            self.fps_buffer.append(1.0 / dt)

        return frame, now

    def get_fps(self):
        if len(self.fps_buffer) == 0: # avoid divide by 0 error;
            return 0
        return sum(self.fps_buffer) / len(self.fps_buffer) # returning the average fps of last 30 frames;

    def get_status(self):
        # if no frame for 3 sec continuosly ---> FAILED
        if time.time() - self.last_frame_time > 3:
            return "FAILED"
        return self.status 



if __name__ == "__main__":
    STREAM_URL = "http://XXX.XXX.XX.XX:XXXX/video"  
    cam = CameraInput(STREAM_URL) # object created;

    if not cam.connect():
        exit()

    print("[INPUT] Starting stream... Press 'q' to quit")

    while True:
        frame, ts = cam.get_frame()

        if frame is None:
            continue

        # getting basic info(metrics);
        fps = cam.get_fps()
        status = cam.get_status()

        
        # .putText() ---> insert the text of the info in the video window;
        cv2.putText( 
            frame,
            f"FPS: {fps:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Status: {status}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        cv2.imshow("Camera Feed", frame) # show the feed in a openCV native WINDOW;

        #  a standard way in OpenCV to handle keyboard interrupts;
        key = cv2.waitKey(1) 
        if key == ord("q"): 
            print("[INPUT] Exiting...")
            break

        # optional throttle (avoid CPU spike)
        time.sleep(0.05)

    cam.cap.release()
    cv2.destroyAllWindows()
