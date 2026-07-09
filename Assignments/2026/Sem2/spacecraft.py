class Spacecraft:
    """Represents the state of the spacecraft during the simulation."""
    
    def __init__(spacecraft, position=None, velocity=None, engine_mode='Off', drag_parameter=None, climb_ratio=None, engine_acceleration_magnitude=None, reentry=None):
        spacecraft.position = position
        spacecraft.velocity = velocity
        spacecraft.engine_mode = engine_mode
        spacecraft.drag_parameter = drag_parameter
        spacecraft.climb_ratio = climb_ratio
        spacecraft.engine_acceleration_magnitude = engine_acceleration_magnitude
        spacecraft.reentry = reentry

    def __repr__(spacecraft):
        return f"Spacecraft({', '.join(f'{k}={v!r}' for k, v in spacecraft.__dict__.items() if v is not None)})"