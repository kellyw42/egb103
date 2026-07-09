from enum import Enum, auto

class EventKind(Enum):
    """Enumeration of mission event types."""
    LIFTOFF = auto()
    SEPARATION = auto()
    BURN_START = auto()
    BURN_CUTOFF = auto()
    DEPLOYMENT = auto()
    ENTRY = auto()
    LANDING = auto()

    def __repr__(self):
        return f"EventKind.{self.name}"


class MissionEvent:
    """Represents a single mission event and its associated parameters."""
    
    def __init__(event, event_kind, event_name, mission_elapsed_time=None, drag_parameter=None, engine_acceleration_magnitude=None, altitude=None, climb_ratio=None, launch_location=None):
        event.event_kind = event_kind
        event.event_name = event_name
        event.mission_elapsed_time = mission_elapsed_time
        event.altitude = altitude
        event.launch_location = launch_location
        event.drag_parameter = drag_parameter
        event.engine_acceleration_magnitude = engine_acceleration_magnitude
        event.climb_ratio = climb_ratio

    def __repr__(event):
        return f"MissionEvent({', '.join(f'{k}={v!r}' for k, v in event.__dict__.items() if v is not None)})" 


def convert_to_seconds(time_string):
    """Convert a mission elapsed time string (e.g. '+0d 01:01:05') to seconds."""
    sign = 1 if time_string[0] == '+' else -1
    days, time_part = time_string[1:].split('d ')
    hours, minutes, seconds = time_part.split(':')
    return sign * (int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60 + int(seconds))


def convert_seconds_to_string(mission_elapsed_time):
    """Convert mission elapsed time in seconds to a formatted string."""
    sign = "+" if mission_elapsed_time >= 0 else "-"
    t = abs(mission_elapsed_time)
    d = int(t // 86400)
    h = int((t % 86400) // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return f"{sign}{d}d {h:02d}:{m:02d}:{s:02d}"