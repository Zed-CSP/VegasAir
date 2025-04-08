from typing import TypedDict, Dict

class FlightStatus(TypedDict):
    hours_remaining: int
    is_active: bool

class FlightStateManager:
    def __init__(self):
        self.flight_states: Dict[int, FlightStatus] = {}

    def update_hours_remaining(self, flight_id: int, hours: int):
        if flight_id not in self.flight_states:
            self.flight_states[flight_id] = {"hours_remaining": hours, "is_active": True}
        else:
            self.flight_states[flight_id]["hours_remaining"] = hours

    def get_hours_remaining(self, flight_id: int) -> int:
        return self.flight_states.get(flight_id, {}).get("hours_remaining", 0)

    def is_flight_active(self, flight_id: int) -> bool:
        return self.flight_states.get(flight_id, {}).get("is_active", False)

    def set_flight_inactive(self, flight_id: int):
        if flight_id in self.flight_states:
            self.flight_states[flight_id]["is_active"] = False

# Global instance
flight_state_manager = FlightStateManager() 