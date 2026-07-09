import math

class Vector3D:
    """Represents a 3D vector with x, y, z components."""    
    def __init__(self, x, y, z):
        self._x = x
        self._y = y
        self._z = z

    def __repr__(self):
        return f"Vector3D({self._x},{self._y},{self._z})"


# Return the sum of one or more vectors.
def vector_add(*vectors):
    x = 0.0
    y = 0.0
    z = 0.0
    for vector in vectors:
        x += vector._x
        y += vector._y
        z += vector._z
    return Vector3D(x, y, z)


# Return the difference of two vectors.
def vector_subtract(vector_a, vector_b): 
    return Vector3D(vector_a._x - vector_b._x, vector_a._y - vector_b._y, vector_a._z - vector_b._z)


# Return a vector scaled by a scalar.
def vector_scale(scale_factor, vector): 
    return Vector3D(vector._x * scale_factor, vector._y * scale_factor, vector._z * scale_factor)


# Return the magnitude of a vector.
def vector_magnitude(vector): 
    return math.sqrt(vector._x**2 + vector._y**2 + vector._z**2)


# Return the zero vector.
def zero_vector():
    return Vector3D(0, 0, 0)

     
# Return the unit vector in the direction of v.
def unit_vector(vector):
    magnitude = vector_magnitude(vector)
    if magnitude == 0:
        return zero_vector()
    else:
        return Vector3D(vector._x/magnitude, vector._y/magnitude, vector._z/magnitude)


# Return the vector as a tuple (x, y, z).
def to_tuple(vector):
    return (vector._x, vector._y, vector._z)
    