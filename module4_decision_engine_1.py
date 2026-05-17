'''
moving here directly from module 3, skipping module 4 for "REDUCED" complexity;

This module will take "system_state" and produce the "target_fan_speed" = what should fan do RIGHT NOW… safely(no spamming...);
Module 5 adds:
Time schedule(eg, from 4pm ---> 6pm AC MODE and 12am --->3am AC MODE) + AC override(remote detection) + Speed persistence + Cooldown + Anti-spam(if changed then keep that speed for 10mins no matter what, other wise the fan speed gonnan change every second as per motion detection, leading to FAN FAILURE)

This module does NOT send UDP. It only decides.
'''


import time
from datetime import datetime


class DecisionEngine:
    def __init__(
        self,
        baseline_speed=2,  # ---> default comfort speed when person present but still;
        ac_speed=2,  # ---> speed when AC mode active;
        hold_duration=600  # ---> minimum seconds to hold elevated speed, eg, 300sec = 5 minutes;
    ):

        self.baseline_speed = baseline_speed
        self.ac_speed = ac_speed
        self.hold_duration = hold_duration
        self.first_run = True

        # Stateful memory
        self.last_speed = 0
        self.last_speed_change_time = 0

    # manual AC Schedule : 4pm ---> 6pm, 12am --->3am;
    def check_time_based_ac(self):
        current_hour = datetime.now().hour

        if 14 <= current_hour < 18:  # 4pm ---> 6pm;
            return True

        elif 0 <= current_hour < 3:  # 12am ---> 3am;
            return True

        return False

    # convert motion_detection/activity_level into target fan speed;
    def compute_motion_speed(self, activity_level):

        if activity_level == "STILL":
            return self.baseline_speed

        elif activity_level == "LOW":
            return 4

        elif activity_level == "MODERATE":
            return 5

        elif activity_level == "HIGH":
            return 6

        return self.baseline_speed  # safety fallback to the default speed;

    def apply_hold_logic(self, proposed_speed):  # this is the anti-spam feature, as the Camera Node will detect the motion-difference/change every moment and if the speed is follows that moment by moment frequency, then the FAN will face heacy pressure and mechanical issues; thats why if motion detector reports HIGH MOTION ---> then increase the speed instantly, but if the motion drops in the next moment, the FAN will not reduce its speed instantly, it will hold the old speed(the increased one) for 5mins;

        current_time = time.time()

        if self.last_speed == 0:  # first ever speed set
            self.last_speed = proposed_speed
            self.last_speed_change_time = current_time
            return proposed_speed, "INITIAL_SET"

        if proposed_speed > self.last_speed:  # increasing the speed based on increased_motion;
            self.last_speed = proposed_speed
            self.last_speed_change_time = current_time
            return proposed_speed, "SPEED_UP"

        elif proposed_speed < self.last_speed:  # reducing the speed based on reduced_motion;

            # holding the previous speed
            if (
                current_time - self.last_speed_change_time
                < self.hold_duration
            ):
                return self.last_speed, "HOLD_ACTIVE"

            # hold expired ---> apply the proposed speed
            else:
                self.last_speed = proposed_speed
                self.last_speed_change_time = current_time

                return self.last_speed, "REEVALUATED_DROP"

        return self.last_speed, "NO_CHANGE"

    # this is the MAIN DECISION ENGINE, i/p = system_state, o/p = target_speed;
    def decide(self, system_state):
        previous_speed = self.last_speed
        if system_state["presence_state"] == "ABSENT":

            target_speed = 0
            power = False
            reason = "NO_PERSON"

        else:

            remote_ac = (
                system_state["ac_state"] == "AC_ON"
            )

            time_ac = self.check_time_based_ac()

            # because i might not explicitly show remote all night or afternoon;
            effective_ac = remote_ac or time_ac

            if effective_ac:

                target_speed = self.ac_speed
                power = True

                if remote_ac:
                    reason = "REMOTE_AC_MODE"
                else:
                    reason = "TIME_AC_MODE"

            else:  # motion detection mode decides speed;

                motion_speed = self.compute_motion_speed(
                    system_state["activity_level"]
                )

                # Apply stability logic
                target_speed, hold_reason = (
                    self.apply_hold_logic(
                        motion_speed
                    )
                )

                power = True
                reason = f"MOTION_MODE_{hold_reason}"
                

        # this is the "ANTI-UDP SPAM FEATURE", the 'apply_hold_logic' function protects the COMFORT STABILITY & SPEED OCCILATION;
        # so, even during 'apply_hold_logic', the loops runs every frame, so without this "ANTI-UDP SPAM", the system will send udp command every frame/second, eg, speed = 6....speed = 6.....speed = 6.....speed = 6 .....
        # apply_hold_logic ---> decides what should be the speed and how long to send the same speed again and again;
        # ANTI-UDP SPAM FEATURE ---> when the decision/speed is the same due to "apply_hold_logic", should i resend the UDP COMMAND again or not!!
       
        # send_update = target_speed != previous_speed
        # send_update = True
        if self.first_run:
            send_update = True
            self.first_run = False
        else:
            send_update = (target_speed != previous_speed)
        self.last_speed = target_speed

        return {
            "power": power,
            "target_speed": target_speed,
            "send_update": send_update,
            "reason": reason
        }
