import math
from vector_2d import normalize_angle

#aircraft_dict = {}

#with open('test_aircraft.txt', 'r') as file :
#    num = 0
#    for line in file:
#        test_src = line.strip()
#        aircraft_dict[test_src] = num
#        num += 1

class TecnamP92:
    """
    A class to represent the Tecnam P92 aircraft and its aerodynamic properties.

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
        angular_velocity (float): # current rate of rotation of the aircraft about its centre of gravity (radians per second)
        linear_velocity (tuple): 2D vector representing the current velocity of the aircraft (metres per second)
        pitch_angle_radians (float): angle of fuselage relative to forward horizon (radians)
        engine_rpm (float): current RPM of the engine
        throttle (float): current throttle setting  where 0.0 means minimum idle throttle, 1.0 means 100% maximum throttle
        stabilizer_angle_radians (float): angle of the rear stabilizer where 0 is level, positive is angled downward and negative is angled upward (radians)
    """

    # Allow objects of this class to be initialized using named attributes, e.g. test_aircraft = TechnamP92(throttle = 0.8, stabilizer_angle_radians = 0.1)
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    # Allow objects of this class to be printed in a useful format
    def __repr__(self):
        default = TecnamP92() 
        attributes = []
        for attr in dir(self) :
            # only print the attributes that have a non default value
            if not attr.startswith('__') and getattr(self, attr) != getattr(default, attr) :
                attributes.append(f'{attr}={getattr(self, attr)}')
        return  f'TecnamP92({",".join(attributes)})'
            
    @staticmethod
    def engine_torque(throttle, rpm):
        """
        Calculate the engine torque based on throttle position and RPM using the torque curve of the Rotax912 engine.

        Parameters:
        throttle (float): Throttle position as a percentage (0 to 1).
        rpm (float): Engine RPM.

        Returns:
        float: Engine torque in Nm.
        """
        max_torque = -4.921e-6 * rpm ** 2 + 0.05 * rpm  # peak of 128 Nm @ 5100 rpm
        percentage = 0.13022 + (1-0.13022) * throttle
        return max_torque * percentage

    @staticmethod
    def propeller_torque_coefficient(advance_rate):
        """
        Calculate the propeller torque coefficient based on the advance rate for the GT Tonini propeller.

        Parameters:
        advance_rate (float): Advance rate of the propeller.

        Returns:
        float: Propeller torque coefficient.
        """
        return (-1e-4 * advance_rate ** 2 + 0.0005203) / 1.74

    @staticmethod
    def propeller_thrust_coefficient(advance_rate):
        """
        Calculate the propeller thrust coefficient based on the advance rate for the GT Tonini propeller.

        Parameters:
        advance_rate (float): Advance rate of the propeller.

        Returns:
        float: Propeller thrust coefficient.
        """
        return (-0.0025 * advance_rate ** 2 + 0.0025) * 1.74

    @staticmethod
    def wing_lift_coefficient(angle_of_attack_radians):
        """
        Calculate the lift coefficient for the wing based on the angle of attack for a modified Gottingen 398 airfoil.

        Parameters:
        angle_of_attack_radians (float): Angle of attack in radians.

        Returns:
        float: Wing lift coefficient.
        """
        angle_of_attack_radians = normalize_angle(angle_of_attack_radians)

        # Stall if angle of attack is greater than 16 degrees
        if angle_of_attack_radians < math.radians(-16.0):
            return 0
        elif angle_of_attack_radians > math.radians(16.0):
            return 0
        else:
            return 0.4 + 0.08 * math.degrees(angle_of_attack_radians)

    @staticmethod
    def stabilizer_lift_coefficient(angle_of_attack_radians):
        """
        Calculate the lift coefficient for the stabilizer based on the angle of attack for a modified NACA 0012 airfoil.

        Parameters:
        angle_of_attack_radians (float): Angle of attack in radians.

        Returns:
        float: Stabilizer lift coefficient.
        """
        angle_of_attack_radians = normalize_angle(angle_of_attack_radians)

        # Stall if angle of attack is greater than 16 degrees
        if angle_of_attack_radians < math.radians(-16.0):
            return 0
        elif angle_of_attack_radians > math.radians(16.0):
            return 0
        else:
            return 0.1 * math.degrees(angle_of_attack_radians)

    engine_moment_of_inertia = 0.1
    engine_max_rpm = 5800   
    wing_area = 12.2
    wing_span = 9.3
    wing_oswald_efficency_factor = 0.8
    wing_angle_of_incidence_radians = math.radians(2)
    wing_distance_to_centre_of_gravity = 0.54
    wing_angle_from_centre_of_gravity_radians = math.radians(90) # wing is vertically above the centre of gravity
    stabilizer_area = 1.97
    stabilizer_span = 2.9
    stabilizer_oswald_efficency_factor = 0.6
    stabilizer_distance_centre_of_gravity = 4
    stabilizer_angle_from_centre_of_gravity_radians = math.radians(180) # rear stabilizer is directly behind the centre of gravity
    propeller_diameter = 1.74
    propeller_gearing_ratio = 2.43 # ratio of 2.43:1 (engine turns at a fixed rate faster than the propeller)
    drag_coefficient = 0.03
    cross_sectional_area = 1.2
    mass = 600.0
    plane_moment_of_inertia = 1000.0

    # State variables (there are the only attributes that can change as the plane flys).
    time_elapsed = 0
    position = (0, 0)
    angular_velocity = 0
    linear_velocity = (0, 0)
    pitch_angle_radians = 0
    engine_rpm = 1000
    throttle = 0
    stabilizer_angle_radians = 0