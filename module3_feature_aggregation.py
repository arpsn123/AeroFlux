
'''
i need this feature_aggregator file/script as because till now i have raw module outputs, thats means my main.py has seperate signals, eg, 
Is person present?
Motion high?
AC on?
Confidence okay?
Activity state?

invidually. so later the decision engine needs to take all this signals seperately, this is workable but not at all recomendable as this is called : 'Spaghetti logic';
"Spaghetti code" is a derogatory term for source code with a tangled, complex control structure that is difficult to read, maintain, or debug.

so, this module(feature_aggregator) will convert these Multiple Low Level Signal --->into---> ONE unified system state;
This module/file/script will output something like this : 
system_state = {
    "presence_state": "PRESENT",
    "activity_level": "LOW",
    "ac_mode": True,
    "comfort_context": "RESTING_WITH_AC"
}

Now the DOWNSTREAM MODULES(FUTURE or Modules that will come after this module) will not even worry about those raw details from seperate modules, it will just use = SYSTEM STATE;

Now, this module doesnot own any data(seperate signals), as this is not a sensor, this module works as a processor or interpreter or aggregator. The main.py will supply all the signals seperately to this module and this module will aggregate them and deliver the SYSTEM_STATE;

but the aggregation will be done NOT here, but in main.py file as main.py will import alllllllll the modules and do the task there;

'''


class FeatureAggregator:
    def __init__(self):

        pass

    def classify_activity(self, motion_score):

        if motion_score < 0.02:
            return "STILL"

        elif motion_score < 0.08:
            return "LOW"

        elif motion_score < 0.20:
            return "MODERATE"

        else:
            return "HIGH"

    def aggregate(
        self,
        person_data,
        motion_data,
        remote_data,
        AC_MODE
    ):

        presence_state = (
            "PRESENT"
            if person_data["person_present"]
            else "ABSENT"
        )

        motion_score = motion_data["motion_score"]

        if presence_state == "ABSENT":
            activity_level = "NONE"
        else:
            activity_level = self.classify_activity(
                motion_score
            )

        remote_state = (
            "VISIBLE"
            if remote_data["remote_detected"]
            else "NOT_VISIBLE"
        )

        ac_state = (
            "AC_ON"
            if AC_MODE
            else "AC_OFF"
        )

        system_state = {
            "presence_state": presence_state,
            "person_confidence": person_data["confidence"],
            "motion_score": motion_score,
            "activity_level": activity_level,
            "remote_state": remote_state,
            "ac_state": ac_state
        }

        return system_state
