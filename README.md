<h1 align="center">𖣘AeroFlux </h1>
<h2 align="center">A Vision-Guided IoT Fan Control System for Adaptive Cooling</h2>
<div align="center">
    <img src="https://img.shields.io/github/stars/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=ffca28" alt="GitHub Repo Stars">
    <img src="https://img.shields.io/github/forks/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=00aaff" alt="GitHub Forks">
    <img src="https://img.shields.io/github/watchers/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=00e676" alt="GitHub Watchers">
</div>

<div align="center">
    <img src="https://img.shields.io/github/issues/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=ea4335" alt="GitHub Issues">
    <img src="https://img.shields.io/github/issues-pr/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=ff9100" alt="GitHub Pull Requests">
</div>

<div align="center">
    <img src="https://img.shields.io/github/last-commit/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=673ab7" alt="GitHub Last Commit">
    <img src="https://img.shields.io/github/contributors/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=388e3c" alt="GitHub Contributors">
    <img src="https://img.shields.io/github/repo-size/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=303f9f" alt="GitHub Repo Size">
</div>

<div align="center">
    <img src="https://img.shields.io/github/languages/count/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=607d8b" alt="GitHub Language Count">
    <img src="https://img.shields.io/github/languages/top/arpsn123/AeroFlux?style=for-the-badge&logo=github&logoColor=white&color=4caf50" alt="GitHub Top Language">
</div>

<div align="center">
    <img src="https://img.shields.io/badge/Maintenance-Active-brightgreen?style=for-the-badge&logo=github&logoColor=white" alt="Maintenance Status">
</div>

AeroFlux is a vision-driven adaptive airflow intelligence system built to automate IoT-enabled ceiling fan control through real-time perception, contextual state modeling, and event-aware thermal response.

Designed as a modular edge-deployed control architecture, AeroFlux transforms live visual input into cooling decisions by combining human detection, behavioral motion analysis, contextual inference, and direct UDP-based device actuation into a unified perception-to-control pipeline.

The system continuously interprets:

* Human presence and occupancy state
* Activity intensity and behavioral motion patterns
* Contextual cooling signals such as AC activation
* Temporal usage patterns influencing airflow demand

These inputs are fused into a structured decision framework that dynamically regulates fan state and speed in real time.

Unlike conventional automation systems that rely on static triggers or binary occupancy logic, AeroFlux operates as a context-aware environmental control engine where cooling behavior is treated as a continuously adaptive systems problem rather than a simple ON/OFF event.

Its architecture prioritizes:

* Real-time computer vision inference using YOLOv8x
* Motion-state estimation with environmental noise suppression
* Context-aware thermal decision logic
* UDP-native low-latency IoT control
* Hardware-safe anti-spam and state stability mechanisms

AeroFlux is engineered for edge environments where perception, inference, and control must operate with low latency, high interpretability, and direct real-world device impact.


---
## Live System Demonstration 


https://github.com/user-attachments/assets/1124d912-8ee0-4398-a0c8-c5a1f35b51a1

No-occupancy shutdown interval accelerated[2× Speed] for brevity


---


## Device Discovery — Local Network Fan IP Identification

Before AeroFlux can directly control an IoT ceiling fan through UDP, the system must first identify the fan’s local network IP address. 
Since UDP communication is LAN-targeted, accurate device IP resolution is a prerequisite for hardware-level actuation.

This process is fundamentally a **Layer 2 → Layer 3 device mapping workflow**, where the fan’s hardware identifier (MAC address) is used to discover its current network address (IP).



### Why This Is Necessary

Consumer IoT devices often receive dynamically assigned local IPs through DHCP, meaning the fan’s IP may change over time unless statically reserved.

AeroFlux communicates using:

```python id="disc1"
(FAN_IP, PORT)
```

Without the correct IP, UDP packets cannot reach the device.



## Step 1 — Identify Device MAC Address via Router Dashboard

The router acts as the authoritative DHCP allocator for all LAN devices.

Within the router’s connected devices dashboard, locate the IoT fan by:

* Device name (if visible)
* Vendor/OUI

### Goal:

Extract the fan’s MAC address:

```text id="disc2"
A4:CF:12:XX:XX:XX
```


## Step 2 — Force ARP Population

By default, your laptop’s ARP cache only stores devices it has recently communicated with.

If the fan has not recently exchanged packets with your system, `arp -a` may not show it.

To solve this, AeroFlux performs a subnet-wide ping sweep to force Layer 2 discovery.


### Example:

```bat id="disc3"
for /L %i in (1,1,254) do ping 192.16X.XX.%i -n 1 >nul
```

## Step 3 — Read ARP Table

Once the subnet sweep is complete:

```bat id="disc4"
arp -a
```


### Output:

Maps:

```text id="disc5"
IP Address ↔ MAC Address
```


## Step 4 — Match MAC to Fan

Compare router-discovered MAC with ARP-discovered MAC:

```text id="disc7"
A4:CF:12:XX:XX:XX
↓
192.16X.XX.XX
```

### Result:

```python id="disc8"
FAN_IP = "192.16X.XX.XX"
```


## 01. Input Layer

The Input Layer is AeroFlux’s real-time visual acquisition subsystem, designed to transform a raw IP camera stream into a stable, low-latency perception source for all downstream modules.

It functions as the system’s sensory backbone, ensuring that detection, motion analysis, and adaptive control always operate on the most recent valid scene state.

### Functions

* Connect to IP camera / mobile webcam stream
* Capture live frames continuously
* Minimize buffering to reduce latency
* Monitor FPS and stream health
* Detect degradation or disconnects
* Recover automatically through reconnection

### Design Principle

AeroFlux prioritizes **frame freshness over passive continuity**.

Instead of relying on stale buffered frames, the system explicitly minimizes stream lag through low-buffer capture:

```python
self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```

Additional frame flushing further suppresses delayed frame buildup:

```python
for _ in range(3):
    self.cap.grab()
```

This ensures downstream inference reacts to near-current environmental state rather than outdated visual history.

### Reliability Architecture

The module continuously tracks operational health through explicit states:

```python
self.status = "OK"
self.status = "DEGRADED"
self.status = "FAILED"
```

This prevents silent camera instability from propagating into perception and control logic.

---
## 02-A. Person Detection Layer

Module 2A is AeroFlux’s primary human-presence perception engine, responsible for determining whether a person is physically present within the operational environment before any adaptive cooling logic is allowed to execute. It functions as the system’s first semantic intelligence gate, transforming raw visual input into actionable occupancy awareness. 


### Functions

* Detect human presence in real time
* Filter non-human objects from scene state
* Extract highest-confidence person instance
* Compute occupancy confidence
* Estimate spatial dominance through bounding box area ratio

### Detection Architecture

AeroFlux uses YOLOv8x as its primary detection backbone:

```python id="y9x31p"
self.model = YOLO(model_path)
```

This shifts the system from traditional binary automation toward object-aware visual intelligence.

Person filtering is explicitly constrained to COCO Class ID 0:

```python id="j31p0x"
self.PERSON_CLASS_ID = 0
```

This ensures that AeroFlux does not confuse pets, furniture, or arbitrary movement with human occupancy.

### Decision Logic

Each frame undergoes full inference, but only the most confident valid person detection is retained:

```python id="k2x0vf"
if cls == self.PERSON_CLASS_ID and conf >= self.conf_threshold:
```

This design prevents weaker or ambiguous detections from destabilizing occupancy state.

### Spatial Relevance

Beyond simple presence, AeroFlux computes bounding box dominance:

```python id="r82nfa"
area_ratio = bbox_area / frame_area
```

This enables future expansion into:

* Distance approximation
* Occupancy weighting
* Dominant subject prioritization
* Multi-zone comfort adaptation

### Performance Strategy

To preserve edge responsiveness, frame-skipping reduces unnecessary detector overload:

```python id="w7m2qd"
if frame_count % 3 == 0:
```

This balances computational cost against real-time control fidelity.


---

## 02-B. Motion Intelligence Layer

While Module 2A answers the question *“Is a person present?”*, Module 2B answers the far more operationally important question:

**“How active is the person right now?”**

This module functions as AeroFlux’s behavioral intensity engine, transforming visual change over time into motion-state intelligence that directly influences adaptive fan speed scaling. 

Presence alone is insufficient for intelligent cooling. A seated user, a sleeping user, and a highly active user should not receive identical airflow behavior. Module 2B bridges this gap by quantifying physical scene dynamics into actionable thermal relevance.



###  Functions

* Measure frame-to-frame motion intensity
* Quantify physical activity through motion scoring
* Suppress environmental false positives
* Ignore ceiling fan blade interference using ROI
* Smooth motion volatility across time
* Convert raw motion into stable behavioral state



### Motion Processing Pipeline

```text
Frame
↓
ROI Extraction
↓
Grayscale Conversion
↓
Gaussian Blur
↓
Frame Differencing
↓
Thresholding
↓
Motion Pixel Quantification
↓
Normalization
↓
Temporal Smoothing
↓
Motion Score
```

### Step 1 — Region of Interest (ROI) Isolation

A critical deployment challenge emerged from real-world hardware context:
the ceiling fan itself occupies upper-frame space and generates constant motion noise.

Without suppression, the system would permanently infer HIGH activity.

AeroFlux solves this through ROI-based environmental filtering:

```python id="m2broi"
frame, roi_y_start = self.extract_roi(frame)
```

This deliberately excludes upper-frame fan motion and constrains behavioral analysis to human-relevant zones.

| Region      | Purpose                           |
| ----------- | --------------------------------- |
| Top Frame   | Ignored (ceiling fan suppression) |
| Lower Frame | Human activity analysis           |

This transforms raw motion detection into context-valid motion detection.



### Step 2 — Computational Simplification

Color information is irrelevant for motion-state estimation, so AeroFlux reduces each frame to grayscale:

```python id="m2bgray"
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
```

This lowers noise, memory, and processing cost while preserving structural motion patterns.



### Step 3 — Noise Suppression

Gaussian blur reduces:

* Compression flicker
* Sensor grain
* Minor lighting shifts
* Pixel jitter

```python id="m2bblur"
gray = cv2.GaussianBlur(gray, self.blur_size, 0)
```

This ensures motion reflects meaningful physical displacement rather than visual artifact.



### Step 4 — Temporal Differencing

Motion fundamentally requires memory.

AeroFlux compares current visual state against prior state:

```python id="m2bdelta"
frame_delta = cv2.absdiff(self.prev_gray, gray)
```

This converts static perception into temporal behavior modeling.



### Step 5 — Thresholding

Tiny changes are discarded to preserve signal quality:

```python id="m2bthresh"
thresh = cv2.threshold(...)
```

This suppresses micro-fluctuations while preserving genuine body movement.



### Step 6 — Motion Quantification

Motion is treated as normalized environmental change:

```python id="m2bscore"
raw_motion_score = motion_pixels / total_pixels
```

This produces scale-independent behavioral intensity.



### Step 7 — Temporal Stability

Raw frame motion is volatile.
AeroFlux stabilizes behavioral interpretation using rolling smoothing:

```python id="m2bsmooth"
self.motion_history = deque(maxlen=history_size)
```

This prevents fan-speed oscillation caused by second-to-second micro-motion spikes.



### Behavioral Interpretation

| Motion Score | State       |
| ------------ | ----------- |
| < Threshold  | Low / Still |
| ≥ Threshold  | Active      |

This creates a bridge between visual behavior and thermal response.

---

## 02-C. Context Trigger Layer (Remote Detection Engine)

Module 2C extends AeroFlux beyond direct perception and into contextual state inference by introducing event-triggered environmental understanding.

While Modules 2A and 2B focus on *who is present* and *how active they are*, Module 2C addresses a higher-order operational question:

**“Has the environmental cooling context changed?”**

Its primary function is to detect AC remote presence as a contextual trigger, allowing AeroFlux to infer probable AC activation and dynamically adjust fan logic accordingly. 

This transforms AeroFlux from reactive motion-based automation into a system capable of environmental state transition awareness.

###  Functions

* Detect handheld remote presence in real time
* Use visual remote appearance as an AC-state proxy
* Trigger contextual AC mode activation
* Suppress false positives through temporal confirmation
* Convert transient object detection into stateful environmental signals



### Why Remote Detection Exists

A ceiling fan alone cannot directly sense:

* AC activation
* Cooling mode transitions
* User intent regarding thermal environment

**Without external thermal sensors or smart AC integration, AeroFlux requires an indirect but deployable context signal.**

The AC remote serves as that proxy.

### System Logic:

**Remote shown → AC likely activated → Fan speed policy should shift**

This is a practical edge-engineering workaround that leverages existing visual infrastructure rather than additional hardware.


### Detection Backbone

Module 2C reuses YOLOv8x:

```python id="m2cyolo"
self.model = YOLO(model_path)
```

This avoids introducing new model classes while leveraging COCO’s pretrained `remote` category.

### Remote Filtering

```python id="m2crem"
if class_name == "remote" and conf >= self.conf_threshold:
```

This isolates remote objects from all other scene entities.



### Key Design Challenge — False Trigger Suppression

Single-frame remote detection is unreliable.

Potential false positives include:

* Phones
* Small handheld devices
* Partial object occlusion
* Detection flicker

To address this, AeroFlux uses **consecutive-frame verification**:

```python id="m2ctrig"
self.consecutive_remote_frames += 1
```

Only after multiple sequential detections does a valid AC trigger occur:

```python id="m2cvalid"
ac_trigger = (
    self.consecutive_remote_frames >= self.trigger_frames
)
```



### Trigger Architecture

| Detection Pattern         | Outcome    |
| ------------------------- | ---------- |
| Single-frame remote       | Ignored    |
| Intermittent flicker      | Ignored    |
| Sustained remote presence | AC Trigger |



### Design Insight

This transforms object detection into stateful contextual inference.

Instead of:
**“A remote exists.”**

AeroFlux interprets:
**“A probable cooling-state transition is occurring.”**


### Systems Role

Module 2C effectively acts as a bridge between:

**Visual Perception → Behavioral Context → Environmental State**

It introduces event-awareness into AeroFlux’s adaptive cooling stack.

---

## 03. Feature Aggregation Layer (Unified System State Engine)

Module 3 is AeroFlux’s state abstraction and signal unification layer—the architectural bridge that transforms fragmented low-level perception outputs into a single structured system state consumable by downstream intelligence.

At this stage, AeroFlux has already produced multiple independent signals:

* Person presence
* Motion score
* Activity intensity
* Remote visibility
* AC trigger state

Individually, these signals are useful. Collectively, without abstraction, they create control fragmentation.


###  Objective

**Raw Detection Signals → Unified Contextual State**

This is the layer where AeroFlux transitions from isolated CV outputs into systems intelligence.


### Architectural Role

Module 3 acts as AeroFlux’s internal state compiler.

It does not detect.
It does not control.
It interprets.

Its function is to normalize heterogeneous module outputs into one operational schema.


### State Transformation

```python id="m3sys"
system_state = {
    "presence_state": ...,
    "activity_level": ...,
    "remote_state": ...,
    "ac_state": ...
}
```

This creates a standardized internal language for all future modules.



### Behavioral Abstraction

Raw motion values are converted into semantic categories:

```python id="m3class"
if motion_score < 0.02:
    return "STILL"
```

This is critical because downstream systems should reason in behavioral states, not floating-point noise.


This module prevents **“spaghetti logic”** by enforcing separation between:

---

## 04. Decision Engine (Adaptive Thermal Control Core)

Module 4 is AeroFlux’s primary control intelligence layer—the subsystem where perception, context, behavioral state, and environmental policy are transformed into actionable fan-control decisions.

This is the architectural point where AeroFlux stops being a perception system and becomes a real-time adaptive control system. 

All upstream modules answer:

* What is happening?
* Who is present?
* How active are they?
* Is AC likely active?

Module 5 answers:
**“What should the fan do right now?”**


### Core Responsibilities

* Convert `system_state` into target fan speed
* Apply motion-aware cooling logic
* Integrate AC override behavior
* Enforce time-based cooling schedules
* Prevent oscillatory speed instability
* Suppress redundant UDP command spam



### Control Architecture

```text id="m5flow"
System State
↓
Presence Check
↓
AC Context Check (Remote + Time)
↓
Motion-Based Speed Mapping
↓
Hold Logic / Stability Enforcement
↓
Anti-Spam Validation
↓
Target Fan Action
```



### Step 1 — Presence as Master Gate

```python id="m5presence"
if system_state["presence_state"] == "ABSENT":
```

If no user is present:

### Fan OFF

This prevents unnecessary cooling regardless of motion noise or false triggers.



### Step 2 — Dual AC Context Logic

AeroFlux does not rely solely on remote visibility.

It combines:

```python id="m5ac"
effective_ac = remote_ac or time_ac
```

This creates contextual persistence through:

| Trigger Type     | Purpose                       |
| ---------------- | ----------------------------- |
| Remote Detection | Explicit AC activation        |
| Time Schedule    | Behavioral routine prediction |

This hybrid strategy allows AeroFlux to model likely cooling state even when the remote is no longer visible.


### Step 3 — Motion-to-Speed Mapping

```python id="m5motion"
if activity_level == "HIGH":
    return 6
```

This converts behavioral intensity into thermal response.

| Activity Level | Fan Speed |
| -------------- | --------- |
| STILL          | Baseline  |
| LOW            | 4         |
| MODERATE       | 5         |
| HIGH           | 6         |

This is where AeroFlux transitions from occupancy automation to adaptive comfort scaling.



### Step 4 — Hold Logic (Mechanical Stability Layer)

Raw motion fluctuates constantly.
Without regulation:

### Speed 6 → 4 → 6 → 3 → 5

This would create hardware stress and poor user comfort.

AeroFlux solves this through speed persistence:

```python id="m5hold"
if proposed_speed < self.last_speed:
```

Speed increases are immediate.
Speed decreases are delayed.

This ensures:

* Rapid comfort response
* Controlled speed decay
* Reduced oscillation
* Hardware longevity



### Step 5 — Anti-UDP Spam Layer

Even if target speed remains constant, the main loop executes continuously.

Without suppression:

### `speed=6` sent every frame

AeroFlux explicitly blocks redundant transmission:

```python id="m5spam"
send_update = (target_speed != previous_speed)
```

With startup synchronization:

```python id="m5first"
if self.first_run:
```

This solves both:

* Initial state sync
* Continuous command spam

---

## 05. UDP IoT Control Layer (Direct Device Actuation Engine)

Module 5 is AeroFlux’s hardware execution layer—the subsystem responsible for converting high-level adaptive decisions into direct physical ceiling fan control.


### Why UDP Instead of Official Cloud API

Atomberg’s official developer API introduces hard operational constraints:

* 100 API calls/day
* 5 calls/second throttle
* Token lifecycle dependency
* Cloud authentication overhead

For a real-time adaptive control system running continuous perception loops, these constraints are structurally incompatible.

For this reason, AeroFlux uses direct LAN-based UDP communication.


### Core Principle:

**Decision → Packet → Device**

### Device Communication Model

AeroFlux serializes control commands into JSON payloads:

```python id="m6json"
message = json.dumps(command).encode("utf-8")
```

These are transmitted directly to the fan’s local IP:

```python id="m6udp"
sock.sendto(message, (self.fan_ip, self.fan_port))
```



### Example Commands

**Power Control**

```python id="m6power"
{"power": True}
```

**Speed Control**

```python id="m6speed"
{"speed": 6}
```


