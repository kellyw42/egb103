import spice_api

class CelestialBody:
    """Represents a celestial body with key physical properties used in simulation."""
    
    def __init__(self, name):
        # Standard gravitational parameter (mu = G * M), in km^3/s^2
        self.gravitational_parameter = float(spice_api.get_gravitational_parameter(name))
        
        # Mean radius of the body, in kilometres
        self.radius = float(spice_api.get_mean_radius(name))

# Predefined celestial bodies used throughout the assignment
earth = CelestialBody("Earth")
moon = CelestialBody("Moon")
