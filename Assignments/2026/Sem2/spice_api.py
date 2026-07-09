import spiceypy as spice
from vector3d import Vector3D, to_tuple
import numpy as np
from ambiance import Atmosphere



# Load SPICE kernels (NASA ephemeris data)
# These provide planetary positions, constants, and time conversions

spice.furnsh("kernels/naif0012.tls")                # Leapseconds (needed for utc_to_ephemeris_time)
spice.furnsh("kernels/pck00010.tpc")                # Radius and orientation data (needed for celestial bodies, radius)
spice.furnsh("kernels/gm_de440.tpc")                # Gravitational parameters (needed for celestial bodies, gm)
spice.furnsh("kernels/earth_latest_high_prec.bpc")  # Earth orientation (needed for earth_position_and_velocity)
spice.furnsh("kernels/de440s.bsp")                  # Planetary ephemeris (needed for moon_position)


# Convert a UTC time string to SPICE ephemeris time (seconds since J2000).
def utc_to_ephemeris_time(utc_time):    
    return int(spice.utc2et(utc_time))


# Convert ephemeris time to a UTC time string.
def ephemeris_time_to_utc_string(ephemeris_time):
    return spice.et2utc(ephemeris_time, "ISOC", 0)

 
# Return mean radius of a celestial body (km)   
def get_mean_radius(body_name):
    _, radii = spice.bodvrd(body_name, "RADII", 3)
    return sum(radii) / 3.0


# Return gravitational parameter (mu) of a body (km^3/s^2)
def get_gravitational_parameter(body_name):
    _,gm = spice.bodvrd(body_name, "GM", 1)
    return gm[0]  


# Return Moon position in J2000 frame at given time    
def moon_position(ephemeris_time):
    state, _ = spice.spkezr("301", ephemeris_time, "J2000", "NONE", "399")
    return Vector3D(state[0], state[1], state[2])


# Return atmospheric velocity at a position due to Earth's rotation
def atmosphere_rotation_velocity(position_vector, ephemeris_time):
    earth_fixed_position_vector = spice.mxv(spice.pxform("J2000", "ITRF93", ephemeris_time), to_tuple(position_vector))
    earth_fixed_atmosphere_state_vector = np.hstack((earth_fixed_position_vector, [0.0, 0.0, 0.0]))
    inertial_frame_atmosphere_state_vector = spice.mxvg(spice.sxform("ITRF93", "J2000", ephemeris_time), earth_fixed_atmosphere_state_vector)
    return Vector3D(inertial_frame_atmosphere_state_vector[3], inertial_frame_atmosphere_state_vector[4], inertial_frame_atmosphere_state_vector[5])



# Return position (km) and velocity (km/s) of a point on Earth's surface
def earth_position_and_velocity(latitude_deg, longitude_deg, ephemeris_time):
    latitude_rad = np.radians(latitude_deg)
    longitude_rad = np.radians(longitude_deg)
    radius = float(get_mean_radius('Earth'))
    x = radius * np.cos(latitude_rad) * np.cos(longitude_rad)
    y = radius * np.cos(latitude_rad) * np.sin(longitude_rad)
    z = radius * np.sin(latitude_rad)
    position_vector = Vector3D(*spice.mxv(spice.pxform("ITRF93", "J2000", ephemeris_time), [x, y, z]))
    velocity_vector = atmosphere_rotation_velocity(position_vector, ephemeris_time)
    return position_vector, velocity_vector 


# Return atmospheric density at given altitude (kg/m^3)
def air_density(altitude_kilometres):   
    if altitude_kilometres > 200:
        return 0
    if altitude_kilometres <= 80:
        if altitude_kilometres < 0:
            altitude_kilometres = 0
        return float(Atmosphere(altitude_kilometres * 1000).density[0])
    base_index = int(altitude_kilometres - 80)
    altitude_lower = 80 + base_index
    altitude_upper = altitude_lower + 1
    density_lower = standard_densities[base_index]
    density_upper = standard_densities[base_index + 1]
    interpolation_fraction = (altitude_kilometres - altitude_lower) / (altitude_upper - altitude_lower)
    return density_lower + interpolation_fraction * (density_upper - density_lower)


# Precomputed density values for altitudes above 80 km
standard_densities = [
     1.845788586788023e-05,
     1.5750689550102798e-05,
     1.3469060503298388e-05,
     1.1535101260076398e-05,
     9.887251783444224e-06,
     8.476664863421586e-06,
     7.264421560436254e-06,
     6.2192805456181925e-06,
     5.315973988682923e-06,
     4.533889221690801e-06,
     3.856021066894755e-06,
     3.2735938475525472e-06,
     2.7773628517024918e-06,
     2.3540376332675805e-06,
     1.992706529563293e-06,
     1.6843162029545056e-06,
     1.4212819223757833e-06,
     1.197186406898254e-06,
     1.0065651849799906e-06,
     8.447262302979652e-07,
     7.076202450662095e-07,
     5.917726184634375e-07,
     4.942547207065218e-07,
     4.124534598304308e-07,
     3.440366640461434e-07,
     2.869495574486791e-07,
     2.394039313458052e-07,
     1.998577516815203e-07,
     1.6699337379577628e-07,
     1.396920481511188e-07,
     1.1701034452471504e-07,
     9.816367452231134e-08,
     8.251748084830979e-08,
     6.953614928306706e-08,
     5.876595920994987e-08,
     4.982647183737754e-08,
     4.2401111954859516e-08,
     3.6228037458840845e-08,
     3.109168389414663e-08,
     2.681517941027778e-08,
     2.325375092482318e-08,
     2.028905043971463e-08,
     1.7824348219619424e-08,
     1.5780511120055962e-08,
     1.4079230226116124e-08,
     1.2628813550463747e-08,
     1.137808336437729e-08,
     1.029304641519957e-08,
     9.346514673325146e-09,
     8.51656789535582e-09,
     7.78538211676505e-09,
     7.138354796154545e-09,
     6.563435572815024e-09,
     6.050621781383825e-09,
     5.59155166612868e-09,
     5.179200179838972e-09,
     4.8076307379574246e-09,
     4.47180337204145e-09,
     4.167423295342587e-09,
     3.890801458794613e-09,
     3.6387735047327396e-09,
     3.40859385161707e-09,
     3.197891951245424e-09,
     3.004600346301345e-09,
     2.8269129259683723e-09,
     2.663248510614835e-09,
     2.5122182112369273e-09,
     2.372596119570858e-09,
     2.2433004343014318e-09,
     2.1233699243339288e-09,
     2.0119521604300417e-09,
     1.9082884161747415e-09,
     1.8116999012107726e-09,
     1.7215798786551773e-09,
     1.6373825628690497e-09,
     1.5586195667438574e-09,
     1.4848497986719167e-09,
     1.4156760208550168e-09,
     1.3507375218324569e-09,
     1.2897088952357194e-09,
     1.2322945996956491e-09,
     1.1780847408715545e-09,
     1.1271288347103336e-09,
     1.0790491833390092e-09,
     1.0336426159440748e-09,
     9.907219489235786e-10,
     9.501176512216603e-10,
     9.116723487245793e-10,
     8.752428226621589e-10,
     8.40695790760293e-10,
     8.079106827985072e-10,
     7.767742005171385e-10,
     7.471834262418042e-10,
     7.190418815916644e-10,
     6.9226124832511e-10,
     6.667590368714116e-10,
     6.424595300202895e-10,
     6.192918955427729e-10,
     5.971902972135013e-10,
     5.760934507215154e-10,
     5.559449567371644e-10,
     5.366916910887198e-10,
     5.18284026806981e-10,
     5.006756675918211e-10,
     4.838239253679433e-10,
     4.676881104614949e-10,
     4.522306695786682e-10,
     4.374162143605531e-10,
     4.232117434277427e-10,
     4.0958597624651816e-10,
     3.965098527292099e-10,
     3.8395600587826095e-10,
     3.718986785195e-10,
     3.603135845242633e-10,
     3.4917793656497054e-10,
     3.38470335092822e-10,
     3.281704075153158e-10,
     3.182590579964284e-10,
     3.0871843970103896e-10,
     2.995313719278414e-10,
     2.906817841985543e-10]    