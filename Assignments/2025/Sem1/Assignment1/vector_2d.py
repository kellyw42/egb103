import math

def scale_vector(vector, multiplier):
    """
    Scales a 2D vector by a given multiplier.

    Parameters:
    vector (tuple): A tuple representing the vector (x, y).
    multiplier (float): The multiplier to scale the vector.

    Makes use of: None

    Returns:
    tuple: A tuple representing the scaled vector (x * multiplier, y * multiplier).
    """
    (x, y) = vector
    return (x * multiplier, y * multiplier)

def vector_from_magnitude_and_angle(magnitude, angle_in_radians):
    """
    Creates a 2D vector from a given magnitude and angle.

    Parameters:
    magnitude (float): The magnitude of the vector.
    angle_in_radians (float): The angle in radians.

    Makes use of: math.cos, math.sin
    
    Returns:
    tuple: A tuple representing the vector (x, y).
    """
    return magnitude * math.cos(angle_in_radians), magnitude * math.sin(angle_in_radians)

def vector_angle_radians(vector):
    """
    Calculates the angle of a 2D vector in radians.

    Parameters:
    vector (tuple): A tuple representing the vector (x, y).

    Makes use of: math.atan2

    Returns:
    float: The angle of the vector in radians.
    """
    (x, y) = vector
    return math.atan2(y, x)

def vector_magnitude(vector):
    """
    Calculates the magnitude of a 2D vector.

    Parameters:
    vector (tuple): A tuple representing the vector (x, y).

    Makes use of: math.hypot

    Returns:
    float: The magnitude of the vector.
    """
    (x, y) = vector
    return math.hypot(x, y)

def component_of_vector_in_direction_radians(vector, direction_angle_radians):
    """
    Calculates the component of a 2D vector in a given direction.

    Parameters:
    vector (tuple): A tuple representing the vector (x, y).
    direction_angle_radians (float): The direction angle in radians.

    Makes use of: vector_angle_radians, vector_magnitude, math.cos

    Returns:
    float: The component of the vector in the given direction.
    """
    angle_between = vector_angle_radians(vector) - direction_angle_radians
    return vector_magnitude(vector) * math.cos(angle_between)

def normalize_angle(angle):
    """
    Normalize an angle to the range (-π, π].

    Parameters:
    angle (float): The angle in radians to be normalized.

    Returns:
    float: The normalized angle in radians within the range (-π, π].
    """    
    angle = math.fmod(angle, 2 * math.pi)
    if angle > math.pi:
        angle -= 2 * math.pi

    if angle <= -math.pi:
        angle += 2 * math.pi
        
    assert -math.pi < angle <= math.pi
    return angle      