import socket
import json
import time


class UDPFanController:
    def __init__(
        self,
        fan_ip,
        fan_port=0000
    ):
        self.fan_ip = fan_ip
        self.fan_port = fan_port

    def send_command(self, command):
        try:
            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            message = json.dumps(
                command
            ).encode("utf-8")

            sock.sendto(
                message,
                (self.fan_ip, self.fan_port)
            )

            sock.close()

            return True

        except Exception as e:
            print(f"[UDP ERROR] {e}")
            return False

    def send_power(self, power_on):
        command = {
            "power": bool(power_on)
        }

        return self.send_command(command)

    def send_speed(self, speed):

        speed = max(
            1,
            min(6, int(speed))
        )

        command = {
            "speed": speed
        }

        return self.send_command(command)

    def execute(self, decision_data):
        if not decision_data["send_update"]:

            return {
                "command_sent": False,
                "action": "NO_ACTION",
                "reason": "ANTI_SPAM_BLOCK"
            }
        if not decision_data["power"]:

            success = self.send_power(False)

            return {
                "command_sent": success,
                "action": "POWER_OFF",
                "reason": decision_data["reason"]
            }

        power_success = self.send_power(True)
        time.sleep(0.15)
        speed_success = self.send_speed(
            decision_data["target_speed"]
        )
        success = (
            power_success
            and speed_success
        )

        return {
            "command_sent": success,
            "action": (
                f"SET_SPEED_"
                f"{decision_data['target_speed']}"
            ),
            "reason": decision_data["reason"]
        }
