import math
from vector_2d import normalize_angle

class Cessna172:
    """
    A class to represent the Cessna 172 Skyhawk aircraft and its aerodynamic properties.
    Attributes:
    engine_moment_of_inertia (float): kg*m^2
    engine_max_rpm (float): 
    wing_area (float): metres^2
    wing_span (float): metres
    wing_oswald_efficency_factor (float): https://en.wikipedia.org/wiki/Oswald_efficiency_number
    wing_angle_of_incidence_radians (float): angle of wings relative to the fuselage (radians)
    wing_distance_to_centre_of_gravity (float): Distance between Centre of Gravity and Wing Aerodynamic Centre (metres)
    wing_angle_from_centre_of_gravity_radians (float): Angle from Centre of Gravity to Wing Aerodynamic Centre (radians)
    stabilizer_area (float): Horizontal stabilizer area (metres^2)
    stabilizer_span (float): metres
    stabilizer_oswald_efficency_factor (float): https://en.wikipedia.org/wiki/Oswald_efficiency_number
    stabilizer_distance_centre_of_gravity (float): Distance between Centre of Gravity and Stabilizer Aerodynamic Centre (metres)
    stabilizer_angle_from_centre_of_gravity_radians (float): Angle from Centre of Gravity to Stablizer Aerodynamic Centre (radians)
    propeller_diameter (float): metres
    propeller_gearing_ratio (float): ratio of engine RPM to propeller RPM
    drag_coefficient (float): https://en.wikipedia.org/wiki/Drag_coefficient
    cross_sectional_area (float): of front of aircraft (metres^2)
    mass (float): mass of the aircraft (kg)
    plane_moment_of_inertia (float): Moment of inertia of the entire plane (kg*m^2)
    
    These are the only attributes that can change during the simulation:
    time_elapsed (float): Number of simulated seconds since the simulation began (seconds)
    position (tuple): 2D vector representing the current position of the aircraft, where y = 0 is ground (metres)
    angular_velocity (float): current rate of rotation of the aircraft about its centre of gravity (radians per second)
    linear_velocity (tuple): 2D vector representing the current velocity of the aircraft (metres per second)
    pitch_angle_radians (float): angle of fuselage relative to forward horizon (radians)
    engine_rpm (float): current RPM of the engine
    throttle (float): current throttle setting where 0.0 means minimum idle throttle, 1.0 means 100% maximum throttle
    stabilizer_angle_radians (float): angle of the rear stabilizer where 0 is level, positive is angled downward and negative is angled upward (radians)
    """
    # Allow objects of this class to be initialized using named attributes, e.g. test_aircraft = Cessna172(throttle = 0.8, stabilizer_angle_radians = 0.1)
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Allow objects of this class to be printed in a useful format
    def __repr__(self):
        default = Cessna172() 
        attributes = []
        for attr in dir(self):
            # only print the attributes that have a non-default value
            if not attr.startswith('__') and getattr(self, attr) != getattr(default, attr):
                attributes.append(f'{attr}={getattr(self, attr)}')
        return f'Cessna172({",".join(attributes)})'
    
    @staticmethod
    def engine_torque(throttle, rpm):
        """
        Calculate the engine torque based on throttle position and RPM using the torque curve of the Lycoming IO-360-L2A engine (Peak torque 361 Nm at 2400 RPM)
        Parameters:
        throttle (float): Throttle position as a percentage (0 to 1).
        rpm (float): Engine RPM.
        Returns:
        float: Engine torque in Nm.
        """ 
        max_torque = -6.3e-5 * rpm ** 2 + 0.3 * rpm  # Peak torque 361 Nm at 2400 RPM
        percentage = 0.13022 + (1-0.13022) * throttle
        return max_torque * percentage
    
    @staticmethod
    def propeller_torque_coefficient(advance_rate):
        """
        Calculate the propeller torque coefficient based on the advance rate for the McCauley propeller.
        Parameters:
        advance_rate (float): Advance rate of the propeller.
        Returns:
        float: Propeller torque coefficient.
        """
        return -4.5e-5 * advance_rate ** 2 + 0.00018
        
    @staticmethod
    def propeller_thrust_coefficient(advance_rate):
        """
        Calculate the propeller thrust coefficient based on the advance rate for the McCauley propeller.
        Parameters:
        advance_rate (float): Advance rate of the propeller.
        Returns:
        float: Propeller thrust coefficient.
        """
        a = 0.003
        return (-a * advance_rate ** 2 + a)
    
    @staticmethod
    def wing_lift_coefficient(angle_of_attack_radians):
        """
        Calculate the lift coefficient for the wing based on the angle of attack for a NACA 2412 airfoil.
        Parameters:
        angle_of_attack_radians (float): Angle of attack in radians.
        Returns:
        float: Wing lift coefficient.
        """
        angle_of_attack_radians = normalize_angle(angle_of_attack_radians)
        # Stall if angle of attack is greater than 15 degrees
        if angle_of_attack_radians < math.radians(-15.0):
            return 0
        elif angle_of_attack_radians > math.radians(15.0):
            return 0
        else:
            return 0.3 + 0.1 * math.degrees(angle_of_attack_radians)
    
    @staticmethod
    def stabilizer_lift_coefficient(angle_of_attack_radians):
        """
        Calculate the lift coefficient for the stabilizer based on the angle of attack for a NACA 0012 airfoil.
        Parameters:
        angle_of_attack_radians (float): Angle of attack in radians.
        Returns:
        float: Stabilizer lift coefficient.
        """
        angle_of_attack_radians = normalize_angle(angle_of_attack_radians)
        # Stall if angle of attack is greater than 15 degrees
        if angle_of_attack_radians < math.radians(-15.0):
            return 0
        elif angle_of_attack_radians > math.radians(15.0):
            return 0
        else:
            return 0.08 * math.degrees(angle_of_attack_radians)
    
    engine_moment_of_inertia = 0.2 
    engine_max_rpm = 2700  # Typical max RPM for Lycoming IO-360-L2A
    wing_area = 16.2  # Square meters
    wing_span = 11.0  # Meters
    wing_oswald_efficency_factor = 0.8  # Typical value
    wing_angle_of_incidence_radians = math.radians(1.5)
    wing_distance_to_centre_of_gravity = 1.0  # Meters
    wing_angle_from_centre_of_gravity_radians = math.radians(94)  # Wing is vertically above the center of gravity
    stabilizer_area = 3.0  # Square meters
    stabilizer_span = 3.6  # Meters
    stabilizer_oswald_efficency_factor = 0.7  # Typical value
    stabilizer_distance_centre_of_gravity = 4.84  # Meters
    stabilizer_angle_from_centre_of_gravity_radians = math.radians(175)  # Rear stabilizer is directly behind the center of gravity
    propeller_diameter = 1.88  # Meters
    propeller_gearing_ratio = 1.0  # Direct drive
    drag_coefficient = 0.025  # Typical value
    cross_sectional_area = 1.5  # Square meters
    mass = 1086.0  # Kilograms (empty weight)
    plane_moment_of_inertia = 1200.0 
    
    # State variables (these are the only attributes that can change as the plane flies).
    time_elapsed = 0
    position = (0, 0)
    angular_velocity = 0
    linear_velocity = (0, 0)
    pitch_angle_radians = 0
    engine_rpm = 600
    throttle = 0
    stabilizer_angle_radians = 0