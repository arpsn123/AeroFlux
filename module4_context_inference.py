from datetime import datetime


class ContextInferencer:
    def __init__(self):
        pass

    def time_based_ac_check(self):
        """
        Hard AC schedule:
        Afternoon: 3 PM – 7 PM
        Night: 12 AM – 4 AM
        """

        current_hour = datetime.now().hour

        # Afternoon AC block
        if 15 <= current_hour < 19:
            return True

        # Night AC block
        elif 0 <= current_hour < 4:
            return True

        return False

    def infer(self, system_state):

        occupancy_context = (
            "OCCUPIED"
            if system_state["presence_state"] == "PRESENT"
            else "UNOCCUPIED"
        )


        ac_active = (
            system_state["ac_state"] == "AC_ON"
            or self.time_based_ac_check()
        )

        ac_context = (
            "AC_ON"
            if ac_active
            else "AC_OFF"
        )


        if occupancy_context == "UNOCCUPIED":
            comfort_context = "EMPTY_ROOM"

        elif ac_context == "AC_ON":
            comfort_context = "AC_COOLING"

        else:
            comfort_context = "NORMAL_COOLING"

        context_state = {
            "occupancy_context": occupancy_context,
            "ac_context": ac_context,
            "comfort_context": comfort_context
        }

        return context_state