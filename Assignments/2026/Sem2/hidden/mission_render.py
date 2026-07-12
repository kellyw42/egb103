# Do not modify this file. 
# You don't need to understand or use anything in this file.

import math
import numpy as np
from PIL import Image, ImageDraw
import spiceypy as spice

from celestial_body import earth, moon
from vector3d import to_tuple


IMAGE_SIZE_PX = 1600
DISPLAY_SIZE_PX = 800
MAX_PIXEL = IMAGE_SIZE_PX * 2
MIN_DEPTH = 1.0

BODY_SILHOUETTE_SAMPLES = 40
BODY_BOUNDS_SAMPLES = 42

RESIZE_FILTER = Image.Resampling.BICUBIC

STAR_COUNT = 500
STAR_FIELD_SEED = 103

MOON_ENCOUNTER_VECTOR = np.array([-131871.56169895300, -343137.30362963300, -188568.92930229500], dtype=float)

EARTH_BASE_COLOUR = np.array([55.0, 105.0, 205.0])
EARTH_EDGE_COLOUR = np.array([8.0, 22.0, 70.0])
EARTH_ATMOSPHERE_COLOUR = (40, 120, 255)

MOON_DISC_COLOUR = (255, 252, 225)
MOON_EDGE_COLOUR = (215, 210, 190)
MOON_GLOW_COLOUR = (255, 240, 185)
MOON_MIN_SCREEN_RADIUS = 10
MOON_GLOW_EXTENT = 3.4
MOON_GLOW_LAYERS = 32

EARTH_EQUATOR_COLOUR = (100, 100, 100)
EARTH_MERIDIAN_COLOUR = (100, 100, 100)

TRAJECTORY_GLOW_COLOUR = (80, 110, 170)
TRAJECTORY_BACKGROUND_CORE_COLOUR = (95, 105, 130)
TRAJECTORY_BACKGROUND_GLOW_COLOUR = (35, 45, 70)

BURN_TRAJECTORY_CORE_COLOUR = (255, 205, 65)
BURN_TRAJECTORY_GLOW_COLOUR = (190, 125, 25)
BURN_TRAJECTORY_BACKGROUND_CORE_COLOUR = (155, 120, 45)
BURN_TRAJECTORY_BACKGROUND_GLOW_COLOUR = (75, 55, 25)

SPACECRAFT_CORE_COLOUR = (255, 255, 255)
SPACECRAFT_BODY_COLOUR = (220, 225, 230)
SPACECRAFT_EDGE_COLOUR = (120, 130, 145)
SPACECRAFT_BOOSTER_COLOUR = (210, 210, 215)

SPACECRAFT_PLUME_CORE_COLOUR = (255, 70, 25)
SPACECRAFT_PLUME_GLOW_COLOUR = (220, 25, 8)

SPACECRAFT_PLUME_OUTER_COLOUR = (200, 40, 20)      # diffuse outer plume (red)
SPACECRAFT_PLUME_MIDDLE_COLOUR = (255, 130, 60)    # mid plume (orange)
SPACECRAFT_PLUME_CORE_COLOUR = (255, 235, 170)     # hot core (warm white)



def normalize(vector):
    length = np.linalg.norm(vector)
    if length == 0:
        return vector
    return vector / length


def normalize_2d(x, y):
    length = math.hypot(x, y)
    if length < 1e-9:
        return x, y
    return x / length, y / length


def clamp_int(value, minimum_value, maximum_value):
    return max(minimum_value, min(maximum_value, int(value)))


def vector_length_3d(vector):
    return math.sqrt(vector[0] * vector[0] + vector[1] * vector[1] + vector[2] * vector[2])


def scale_colour(colour, factor):
    return tuple((np.array(colour) * factor).clip(0, 255).astype(int))


def unit_vector_or_none(vector):
    length = vector_length_3d(vector)
    if length < 1e-9:
        return None
    return vector / length


def orthonormal_basis(axis):
    helper_axis = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    tangent = normalize(np.cross(axis, helper_axis))
    radial = np.cross(axis, tangent)
    return tangent, radial


def compute_cone_camera(slide, camera_distance, rotation_angle):
    encounter_axis = normalize(MOON_ENCOUNTER_VECTOR)
    target_position = slide * MOON_ENCOUNTER_VECTOR
    tangent, radial = orthonormal_basis(encounter_axis)
    camera_direction = math.cos(rotation_angle) * tangent + math.sin(rotation_angle) * radial
    camera_position = target_position + camera_distance * camera_direction
    return camera_position, target_position


def build_camera_basis(camera_position, target_position, preferred_up_direction):
    forward = normalize(target_position - camera_position)
    preferred_up = normalize(preferred_up_direction)
    camera_up = preferred_up - np.dot(preferred_up, forward) * forward
    if np.linalg.norm(camera_up) < 1e-6:
        fallback_up = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(fallback_up, forward)) > 0.95:
            fallback_up = np.array([0.0, 1.0, 0.0])
        camera_up = fallback_up - np.dot(fallback_up, forward) * forward
    camera_up = normalize(camera_up)
    camera_right = normalize(np.cross(forward, camera_up))
    camera_up = normalize(np.cross(camera_right, forward))
    return camera_right, camera_up, forward


def world_to_screen(world_position, camera_position, camera_right, camera_up, camera_forward, focal_length):
    relative = world_position - camera_position
    camera_x = relative @ camera_right
    camera_y = relative @ camera_up
    camera_z = relative @ camera_forward
    if camera_z <= MIN_DEPTH:
        return None
    screen_x = IMAGE_SIZE_PX // 2 + int(focal_length * camera_x / camera_z)
    screen_y = IMAGE_SIZE_PX // 2 - int(focal_length * camera_y / camera_z)
    return screen_x, screen_y, camera_z


def project_world_points(points, camera_position, camera_right, camera_up, camera_forward, focal_length):
    relative = points - camera_position
    camera_x = relative @ camera_right
    camera_y = relative @ camera_up
    camera_z = relative @ camera_forward
    valid = camera_z > MIN_DEPTH
    screen_x = np.zeros(len(points), dtype=np.int32)
    screen_y = np.zeros(len(points), dtype=np.int32)
    screen_x[valid] = IMAGE_SIZE_PX // 2 + (focal_length * camera_x[valid] / camera_z[valid]).astype(np.int32)
    screen_y[valid] = IMAGE_SIZE_PX // 2 - (focal_length * camera_y[valid] / camera_z[valid]).astype(np.int32)
    return screen_x, screen_y, camera_z, valid


def project_direction_to_screen(current_position, direction, camera_position, camera_right, camera_up, camera_forward, focal_length):
    relative = current_position - camera_position
    camera_x = relative @ camera_right
    camera_y = relative @ camera_up
    camera_z = relative @ camera_forward
    direction_x = direction @ camera_right
    direction_y = direction @ camera_up
    direction_z = direction @ camera_forward
    if camera_z <= MIN_DEPTH:
        return None
    screen_dx = focal_length * (direction_x * camera_z - camera_x * direction_z) / (camera_z * camera_z)
    screen_dy = -focal_length * (direction_y * camera_z - camera_y * direction_z) / (camera_z * camera_z)
    screen_length = math.hypot(screen_dx, screen_dy)
    if screen_length < 1e-6:
        return None
    return screen_dx / screen_length, screen_dy / screen_length


def world_to_camera_depth(world_position, camera_position, camera_forward):
    relative = world_position - camera_position
    return relative @ camera_forward


def projected_point_is_reasonable(screen_point):
    return abs(screen_point[0]) <= MAX_PIXEL and abs(screen_point[1]) <= MAX_PIXEL


def screen_xy_is_reasonable(screen_x, screen_y):
    return abs(screen_x) <= MAX_PIXEL and abs(screen_y) <= MAX_PIXEL


def sphere_occludes_point(camera_position, point_position, sphere_centre, sphere_radius):
    ray = point_position - camera_position
    distance_to_point = vector_length_3d(ray)
    if distance_to_point < 1e-6:
        return False
    direction = ray / distance_to_point
    origin = camera_position - sphere_centre
    quadratic_b = 2.0 * np.dot(origin, direction)
    quadratic_c = np.dot(origin, origin) - sphere_radius * sphere_radius
    discriminant = quadratic_b * quadratic_b - 4.0 * quadratic_c
    if discriminant < 0:
        return False
    sqrt_discriminant = math.sqrt(discriminant)
    intersection_1 = (-quadratic_b - sqrt_discriminant) / 2.0
    intersection_2 = (-quadratic_b + sqrt_discriminant) / 2.0
    epsilon = 1e-3
    return epsilon < intersection_1 < distance_to_point - epsilon or epsilon < intersection_2 < distance_to_point - epsilon


def compute_limb_geometry(sphere_centre, sphere_radius, camera_position):
    centre_to_camera = camera_position - sphere_centre
    camera_distance = vector_length_3d(centre_to_camera)
    if camera_distance <= sphere_radius:
        return None
    view_axis = centre_to_camera / camera_distance
    limb_centre_distance = sphere_radius * sphere_radius / camera_distance
    limb_centre = sphere_centre + limb_centre_distance * view_axis
    limb_radius_squared = sphere_radius * sphere_radius - limb_centre_distance * limb_centre_distance
    if limb_radius_squared <= 0:
        return None
    limb_radius = math.sqrt(limb_radius_squared)
    helper_axis = np.array([1.0, 0.0, 0.0]) if abs(view_axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    limb_axis_1 = normalize(np.cross(view_axis, helper_axis))
    limb_axis_2 = normalize(np.cross(view_axis, limb_axis_1))
    return limb_centre, limb_radius, limb_axis_1, limb_axis_2


def projected_sphere_bounds(sphere_centre, sphere_radius, camera_position, camera_right, camera_up, camera_forward, focal_length):
    limb_geometry = compute_limb_geometry(sphere_centre, sphere_radius, camera_position)
    if limb_geometry is None:
        return None
    limb_centre, limb_radius, limb_axis_1, limb_axis_2 = limb_geometry
    min_x = 10**9
    min_y = 10**9
    max_x = -10**9
    max_y = -10**9
    for sample_index in range(BODY_BOUNDS_SAMPLES):
        angle = 2.0 * math.pi * sample_index / BODY_BOUNDS_SAMPLES
        world_position = limb_centre + limb_radius * math.cos(angle) * limb_axis_1 + limb_radius * math.sin(angle) * limb_axis_2
        screen_point = world_to_screen(world_position, camera_position, camera_right, camera_up, camera_forward, focal_length)
        if screen_point is None:
            continue
        screen_x, screen_y, _ = screen_point
        min_x = min(min_x, screen_x)
        min_y = min(min_y, screen_y)
        max_x = max(max_x, screen_x)
        max_y = max(max_y, screen_y)
    if min_x > max_x:
        return None
    margin = 12
    return min_x - margin, min_y - margin, max_x + margin, max_y + margin


def projected_body_occludes_point(camera_position, point_position, screen_x, screen_y, body, bounds):
    if bounds is None:
        return False
    min_x, min_y, max_x, max_y = bounds
    if screen_x < min_x or screen_x > max_x or screen_y < min_y or screen_y > max_y:
        return False
    return sphere_occludes_point(camera_position, point_position, body["position"], body["radius"])


def scaled_points_about_centre(points, centre_x, centre_y, scale):
    return [(int(centre_x + (point[0] - centre_x) * scale), int(centre_y + (point[1] - centre_y) * scale)) for point in points]


def draw_earth_limb_glow(draw, projected_points, centre_x, centre_y, colour):
    for scale, factor, width in [(1.050, 0.10, 2), (1.030, 0.16, 2), (1.015, 0.24, 1)]:
        glow_points = scaled_points_about_centre(projected_points, centre_x, centre_y, scale)
        draw.line(glow_points + [glow_points[0]], fill=scale_colour(colour, factor), width=width)


def draw_moon_full_disc(draw, screen_x, screen_y, radius):
    visual_radius = max(int(radius), MOON_MIN_SCREEN_RADIUS)
    for layer in range(MOON_GLOW_LAYERS, 0, -1):
        progress = layer / MOON_GLOW_LAYERS
        glow_radius = int(visual_radius * (1.0 + MOON_GLOW_EXTENT * progress))
        falloff = (1.0 - progress) ** 2.4
        glow_colour = scale_colour(MOON_GLOW_COLOUR, 0.55 * falloff)
        draw.ellipse((screen_x - glow_radius, screen_y - glow_radius, screen_x + glow_radius, screen_y + glow_radius), fill=glow_colour)
    draw.ellipse((screen_x - visual_radius, screen_y - visual_radius, screen_x + visual_radius, screen_y + visual_radius), fill=MOON_DISC_COLOUR)
    draw.ellipse((screen_x - visual_radius, screen_y - visual_radius, screen_x + visual_radius, screen_y + visual_radius), outline=MOON_EDGE_COLOUR)


def draw_shaded_projected_sphere(draw, sphere_centre, sphere_radius, base_colour, edge_colour, glow_colour, camera_position, camera_right, camera_up, camera_forward, focal_length, shading_layers):
    limb_geometry = compute_limb_geometry(sphere_centre, sphere_radius, camera_position)
    if limb_geometry is None:
        return
    limb_centre, limb_radius, limb_axis_1, limb_axis_2 = limb_geometry
    projected_points = []
    for sample_index in range(BODY_SILHOUETTE_SAMPLES):
        angle = 2.0 * math.pi * sample_index / BODY_SILHOUETTE_SAMPLES
        world_position = limb_centre + limb_radius * math.cos(angle) * limb_axis_1 + limb_radius * math.sin(angle) * limb_axis_2
        screen_point = world_to_screen(world_position, camera_position, camera_right, camera_up, camera_forward, focal_length)
        if screen_point is not None:
            projected_points.append((screen_point[0], screen_point[1]))
    if len(projected_points) < 3:
        return
    centre_x = sum(point[0] for point in projected_points) / len(projected_points)
    centre_y = sum(point[1] for point in projected_points) / len(projected_points)
    draw_earth_limb_glow(draw, projected_points, centre_x, centre_y, glow_colour)
    for layer in range(shading_layers, 0, -1):
        scale = layer / shading_layers
        centre_weight = (1.0 - scale) ** 1.55
        colour = tuple((edge_colour * (1.0 - centre_weight) + base_colour * centre_weight).astype(int))
        scaled_points = scaled_points_about_centre(projected_points, centre_x, centre_y, scale)
        draw.polygon(scaled_points, fill=colour)
    draw.line(projected_points + [projected_points[0]], fill=tuple(edge_colour.astype(int)), width=1)


def draw_projected_moon(draw, moon_position, camera_position, camera_right, camera_up, camera_forward, focal_length):
    screen_point = world_to_screen(moon_position, camera_position, camera_right, camera_up, camera_forward, focal_length)
    if screen_point is None:
        return
    camera_distance = vector_length_3d(camera_position - moon_position)
    if camera_distance <= moon.radius:
        return
    screen_radius = focal_length * moon.radius / math.sqrt(camera_distance * camera_distance - moon.radius * moon.radius)
    draw_moon_full_disc(draw, screen_point[0], screen_point[1], screen_radius)


def apparent_sphere_radius_pixels(centre, radius, camera_position, focal_length):
    camera_distance = vector_length_3d(camera_position - centre)
    if camera_distance <= radius:
        return IMAGE_SIZE_PX
    return focal_length * radius / math.sqrt(camera_distance * camera_distance - radius * radius)


def choose_surface_marker_params(centre, radius, camera_position, focal_length):
    apparent_radius = apparent_sphere_radius_pixels(centre, radius, camera_position, focal_length)
    if apparent_radius < 6:
        return 0, 0, 0
    dash_size = clamp_int(apparent_radius / 22.0, 2, 20)
    target_segment_length = max(2.0, dash_size * 0.75)
    equator_samples = clamp_int(2.0 * math.pi * apparent_radius / target_segment_length, 8, 20)
    meridian_samples = clamp_int(math.pi * apparent_radius / target_segment_length, 8, 20)
    return equator_samples, meridian_samples, dash_size


def earth_fixed_surface_point(latitude_rad, longitude_rad, radius):
    x = radius * math.cos(latitude_rad) * math.cos(longitude_rad)
    y = radius * math.cos(latitude_rad) * math.sin(longitude_rad)
    z = radius * math.sin(latitude_rad)
    return np.array([x, y, z], dtype=float)


def surface_point_is_visible(world_point, centre, camera_position):
    normal = world_point - centre
    view = camera_position - world_point
    return np.dot(normal, view) > 0.0


def project_visible_surface_point(world_point, centre, camera_position, camera_right, camera_up, camera_forward, focal_length):
    if not surface_point_is_visible(world_point, centre, camera_position):
        return None
    screen_point = world_to_screen(world_point, camera_position, camera_right, camera_up, camera_forward, focal_length)
    if screen_point is None:
        return None
    return screen_point[0], screen_point[1]


def draw_solid_polyline(draw, points, colour, width=1):
    if len(points) >= 2:
        draw.line(points, fill=colour, width=width)


def draw_dashed_segment(draw, start_point, end_point, colour, accumulated_length, dash_size, width=1):
    x0, y0 = start_point
    x1, y1 = end_point
    segment_length = math.hypot(x1 - x0, y1 - y0)
    if segment_length < 1e-6:
        return accumulated_length
    pattern_length = dash_size * 2.0
    segment_position = 0.0
    while segment_position < segment_length:
        pattern_position = (accumulated_length + segment_position) % pattern_length
        if pattern_position < dash_size:
            draw_length = min(segment_length - segment_position, dash_size - pattern_position)
            t0 = segment_position / segment_length
            t1 = (segment_position + draw_length) / segment_length
            dash_start = (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
            dash_end = (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)
            draw.line([dash_start, dash_end], fill=colour, width=width)
            segment_position = segment_position + draw_length
        else:
            skip_length = min(segment_length - segment_position, pattern_length - pattern_position)
            segment_position = segment_position + skip_length
    return accumulated_length + segment_length


def draw_earth_surface_markers(draw, ephemeris_time, camera_position, camera_right, camera_up, camera_forward, focal_length):
    centre = np.array([0.0, 0.0, 0.0], dtype=float)
    radius = earth.radius
    transform = np.array(spice.pxform("ITRF93", "J2000", ephemeris_time), dtype=float)
    equator_samples, meridian_samples, dash_size = choose_surface_marker_params(centre, radius, camera_position, focal_length)
    
    for latitude_deg in range(-60, 61, 30):   # avoid poles to reduce distortion
        latitude_rad = math.radians(latitude_deg)
        parallel_points = []
        for sample_index in range(equator_samples + 1):
            longitude_rad = 2.0 * math.pi * sample_index / equator_samples  
            earth_fixed_point = earth_fixed_surface_point(latitude_rad, longitude_rad, radius)
            world_point = transform @ earth_fixed_point
            screen_point = project_visible_surface_point(world_point, centre, camera_position, camera_right, camera_up, camera_forward, focal_length)
            if screen_point is None:
                draw_solid_polyline(draw, parallel_points, EARTH_EQUATOR_COLOUR, width=1)
                parallel_points = []
                continue
            parallel_points.append(screen_point)
        draw_solid_polyline(draw, parallel_points, EARTH_EQUATOR_COLOUR, width=1)    
    
    for longitude_deg in range(0, 360, 45):
        meridian_points = []
        longitude_rad = math.radians(longitude_deg)
        for sample_index in range(meridian_samples + 1):
            latitude_rad = -0.5 * math.pi + math.pi * sample_index / meridian_samples
            earth_fixed_point = earth_fixed_surface_point(latitude_rad, longitude_rad, radius)
            world_point = transform @ earth_fixed_point
            screen_point = project_visible_surface_point(world_point, centre, camera_position, camera_right, camera_up, camera_forward, focal_length)
            if screen_point is None:
                draw_solid_polyline(draw, meridian_points, EARTH_MERIDIAN_COLOUR, width=1)
                meridian_points = []
                continue
            meridian_points.append(screen_point)
        draw_solid_polyline(draw, meridian_points, EARTH_MERIDIAN_COLOUR, width=1)


def compute_body_bounds(bodies, camera_position, camera_right, camera_up, camera_forward, focal_length):
    return [projected_sphere_bounds(body["position"], body["radius"], camera_position, camera_right, camera_up, camera_forward, focal_length) for body in bodies]


def body_occludes_projected_point(camera_position, point_position, screen_x, screen_y, bodies, body_bounds):
    for body_index, body in enumerate(bodies):
        if projected_body_occludes_point(camera_position, point_position, screen_x, screen_y, body, body_bounds[body_index]):
            return True
    return False


def project_trajectory_segments(trajectory_positions, engine_data, camera_position, camera_right, camera_up, camera_forward, focal_length, bodies, body_bounds):
    count = len(trajectory_positions)
    background_segments = []
    foreground_segments = []
    screen_x, screen_y, camera_z, valid = project_world_points(trajectory_positions, camera_position, camera_right, camera_up, camera_forward, focal_length)
    point_occluded = np.zeros(count, dtype=bool)
    for body_index, body in enumerate(bodies):
        bounds = body_bounds[body_index]
        if bounds is None:
            continue
        min_x, min_y, max_x, max_y = bounds
        candidate = valid & (screen_x >= min_x) & (screen_x <= max_x) & (screen_y >= min_y) & (screen_y <= max_y)
        candidate_indices = np.nonzero(candidate)[0]
        for point_index in candidate_indices:
            if not point_occluded[point_index] and sphere_occludes_point(camera_position, trajectory_positions[point_index], body["position"], body["radius"]):
                point_occluded[point_index] = True
    for sample_index in range(1, count):
        if not valid[sample_index - 1] or not valid[sample_index]:
            continue
        start_2d = (int(screen_x[sample_index - 1]), int(screen_y[sample_index - 1]))
        end_2d = (int(screen_x[sample_index]), int(screen_y[sample_index]))
        start_occluded = point_occluded[sample_index - 1]
        end_occluded = point_occluded[sample_index]
        engine_on = bool(engine_data[sample_index - 1] and engine_data[sample_index])
        segment = (start_2d, end_2d, engine_on)
        if not start_occluded and not end_occluded:
            foreground_segments.append(segment)
        elif not (start_occluded and end_occluded):
            background_segments.append(segment)
    return background_segments, foreground_segments


def draw_trajectory_segments(draw, segments, foreground=True):

    if not segments:
        return

    current_points = []
    current_engine_on = None
    previous_end = None

    def flush_current_points():

        if len(current_points) < 2:
            return

        if current_engine_on:
            draw.line(current_points, fill=(255, 50, 50), width=3)
        else:
            draw.line(current_points, fill=(50, 255, 50), width=1)

    for start_2d, end_2d, engine_on in segments:

        starts_new_run = current_engine_on is None or engine_on != current_engine_on or previous_end is None or start_2d != previous_end

        if starts_new_run:
            flush_current_points()
            current_points = [start_2d, end_2d]
            current_engine_on = engine_on
            previous_end = end_2d
            continue

        current_points.append(end_2d)
        previous_end = end_2d

    flush_current_points()  


def draw_bodies(draw, bodies, camera_position, camera_right, camera_up, camera_forward, focal_length):
    body_depths = [(world_to_camera_depth(body["position"], camera_position, camera_forward), body) for body in bodies]
    body_depths.sort(key=lambda item: item[0], reverse=True)
    for _, body in body_depths:
        if body["name"] == "Earth":
            draw_shaded_projected_sphere(draw, body["position"], body["radius"], EARTH_BASE_COLOUR, EARTH_EDGE_COLOUR, EARTH_ATMOSPHERE_COLOUR, camera_position, camera_right, camera_up, camera_forward, focal_length, 20)
        elif body["name"] == "Moon":
            draw_projected_moon(draw, body["position"], camera_position, camera_right, camera_up, camera_forward, focal_length)


def make_trajectory_position_array(mission_log, index):
    return np.array([to_tuple(mission_log[i][1]) for i in range(index + 1)], dtype=float)


def marker_style_for_stage(stage_data):
    stage_name = stage_data.get("name", "") if isinstance(stage_data, dict) else ""
    head_length = 14
    head_width = 8
    if "Solid Rocket Boosters" in stage_name or "SRB" in stage_name:
        return {"head_length": head_length, "head_width": head_width, "body_length": 22, "body_width": 12, "plume_length": 44, "plume_width": 0.3, "booster_hint": True}
    if "Core Stage" in stage_name:
        return {"head_length": head_length, "head_width": head_width, "body_length": 22, "body_width": 9, "plume_length": 40, "plume_width": 0.3, "booster_hint": False}
    if "ICPS" in stage_name or "Interim Cryogenic" in stage_name:
        return {"head_length": head_length, "head_width": head_width, "body_length": 5, "body_width": 8, "plume_length": 34, "plume_width": 0.3, "booster_hint": False}
    if "Service Module" in stage_name:
        return {"head_length": head_length, "head_width": head_width, "body_length": 2, "body_width": 8, "plume_length": 28, "plume_width": 0.3, "booster_hint": False}
    if "Crew Module" in stage_name:
        return {"head_length": head_length, "head_width": head_width, "body_length": 0, "body_width": 0, "plume_length": 0, "plume_width": 0, "booster_hint": False}
    return {"head_length": head_length, "head_width": head_width, "body_length": 0, "body_width": 0, "plume_length": 0, "plume_width": 0, "booster_hint": False}



def draw_plume_layer(draw, rear, px, py, nx, ny, base_width, plume_length, plume_spread, line_count, colour, line_width, start_back_offset, rng):

    if line_count <= 1:
        return

    for i in range(line_count):
        fraction = i / (line_count - 1)
        centred = fraction * 2.0 - 1.0

        # small base jitter (keeps nozzle structure but not rigid)
        jitter_base = (0.08 * base_width) * rng.uniform(-1, 1)
        base_offset = centred * base_width + jitter_base

        start = (rear[0] + nx * base_offset + px * start_back_offset, rear[1] + ny * base_offset + py * start_back_offset)

        # slight angular variation (very small)
        spread_jitter = rng.uniform(-0.08, 0.08)
        spread_offset = centred * plume_spread + spread_jitter

        dir_x = px + nx * spread_offset
        dir_y = py + ny * spread_offset

        dir_x, dir_y = normalize_2d(dir_x, dir_y)

        # length variation (important)
        length_scale = rng.uniform(0.92, 1.08)
        length = plume_length * length_scale

        end = (start[0] + dir_x * length, start[1] + dir_y * length)

        # subtle brightness jitter (NOT colour shift)
        brightness = rng.uniform(0.9, 1.1)
        jittered_colour = scale_colour(colour, brightness)

        draw.line([start, end], fill=jittered_colour, width=line_width)


def draw_plume_lines(draw, rear, ux, uy, nx, ny, head_width, plume_length, plume_width):

    px, py = -ux, -uy
    base_width = max(head_width * 0.45, 2.0)
    seed = int((abs(rear[0]) * 73856093 + abs(rear[1]) * 19349663) % (2**32))
    rng = np.random.default_rng(seed)

    def draw_layer(length_scale, spread_scale, base_scale, colour, width, count, back_offset):

        for i in range(count):
            f = i / (count - 1) if count > 1 else 0.0
            c = (f * 2.0 - 1.0) * 0.85

            base_jitter = rng.uniform(-0.07, 0.07)
            base_offset = (c + base_jitter) * base_width * base_scale

            spread_jitter = rng.uniform(-0.04, 0.04)
            spread = c * plume_width * spread_scale

            start = (rear[0] + nx * base_offset + px * back_offset, rear[1] + ny * base_offset + py * back_offset)

            dir_x = px + nx * spread
            dir_y = py + ny * spread
            dir_x, dir_y = normalize_2d(dir_x, dir_y)

            length_jitter = rng.uniform(0.93, 1.07)
            length = plume_length * length_scale * length_jitter

            end = (start[0] + dir_x * length, start[1] + dir_y * length)

            brightness = rng.uniform(0.92, 1.08)
            col = scale_colour(colour, brightness)

            draw.line([start, end], fill=col, width=width)

    draw_layer(1.00, 0.65, 1.00, SPACECRAFT_PLUME_OUTER_COLOUR, 1, 40, 2.8)
    draw_layer(0.62, 0.35, 0.65, SPACECRAFT_PLUME_MIDDLE_COLOUR, 1, 22, 2.2)
    draw_layer(0.28, 0.12, 0.30, SPACECRAFT_PLUME_CORE_COLOUR, 2, 10, 1.5)


def draw_spacecraft_marker(draw, current_position, trajectory_direction, stage_data, engine_on, camera_position, camera_right, camera_up, camera_forward, focal_length):
    current_screen = world_to_screen(current_position, camera_position, camera_right, camera_up, camera_forward, focal_length)
    if current_screen is None:
        return
    projected_direction = project_direction_to_screen(current_position, trajectory_direction, camera_position, camera_right, camera_up, camera_forward, focal_length)
    if projected_direction is None:
        return

    x = current_screen[0]
    y = current_screen[1]
    ux, uy = projected_direction
    nx, ny = -uy, ux
    style = marker_style_for_stage(stage_data)

    head_length = style["head_length"]
    head_width = style["head_width"]
    body_length = style["body_length"]
    body_width = max(style["body_width"], head_width) if body_length > 0 else 0
    plume_length = style["plume_length"]
    plume_width = style["plume_width"]
    booster_hint = style["booster_hint"]

    tip = (int(x + ux * head_length), int(y + uy * head_length))
    head_base = (x - ux * head_length * 0.35, y - uy * head_length * 0.35)
    left_head = (int(head_base[0] - nx * head_width), int(head_base[1] - ny * head_width))
    right_head = (int(head_base[0] + nx * head_width), int(head_base[1] + ny * head_width))

    if body_length > 0:
        rear = (x - ux * (head_length + body_length), y - uy * (head_length + body_length))
        left_rear = (int(rear[0] - nx * body_width), int(rear[1] - ny * body_width))
        right_rear = (int(rear[0] + nx * body_width), int(rear[1] + ny * body_width))
        vehicle_polygon = [tip, left_head, left_rear, right_rear, right_head]
    else:
        rear = head_base
        left_rear = left_head
        right_rear = right_head
        vehicle_polygon = [tip, left_head, right_head]

    if engine_on and plume_length > 0:
        draw_plume_lines(draw, rear, ux, uy, nx, ny, head_width, plume_length, plume_width)

    draw.polygon(vehicle_polygon, fill=SPACECRAFT_BODY_COLOUR if body_length > 0 else SPACECRAFT_CORE_COLOUR)
    draw.line(vehicle_polygon + [vehicle_polygon[0]], fill=SPACECRAFT_EDGE_COLOUR, width=1)

    if booster_hint and body_length > 0:
        booster_offset = body_width * 1.55
        booster_start_back = head_length * 0.25
        booster_end_back = head_length + body_length * 0.85
        left_start = (int(x - ux * booster_start_back - nx * booster_offset), int(y - uy * booster_start_back - ny * booster_offset))
        left_end = (int(x - ux * booster_end_back - nx * booster_offset), int(y - uy * booster_end_back - ny * booster_offset))
        right_start = (int(x - ux * booster_start_back + nx * booster_offset), int(y - uy * booster_start_back + ny * booster_offset))
        right_end = (int(x - ux * booster_end_back + nx * booster_offset), int(y - uy * booster_end_back + ny * booster_offset))
        draw.line([left_start, left_end], fill=SPACECRAFT_BOOSTER_COLOUR, width=2)
        draw.line([right_start, right_end], fill=SPACECRAFT_BOOSTER_COLOUR, width=2)


class MissionRender:
    def __init__(self):
        self.star_directions, self.star_brightnesses, self.star_sizes = self.generate_star_field()
        self.trajectory_cache = None
        self.trajectory_cache_id = None

    def generate_star_field(self):
        rng = np.random.default_rng(STAR_FIELD_SEED)
        directions = []
        brightnesses = []
        sizes = []
        for star_index in range(STAR_COUNT):
            direction = normalize(rng.normal(size=3))
            brightness = int(rng.uniform(200, 255))
            r = rng.random()
            size = 1 if r < 0.70 else 2 if r < 0.97 else 3
            directions.append(direction)
            brightnesses.append(brightness)
            sizes.append(size)
        return np.array(directions, dtype=float), brightnesses, sizes

    def draw_stars(self, draw, camera_right, camera_up, camera_forward, focal_length):
        camera_x = self.star_directions @ camera_right
        camera_y = self.star_directions @ camera_up
        camera_z = self.star_directions @ camera_forward
        valid = camera_z > 0.05
        screen_x = IMAGE_SIZE_PX // 2 + (focal_length * camera_x[valid] / camera_z[valid]).astype(np.int32)
        screen_y = IMAGE_SIZE_PX // 2 - (focal_length * camera_y[valid] / camera_z[valid]).astype(np.int32)
        valid_indices = np.nonzero(valid)[0]
        for local_index, star_index in enumerate(valid_indices):
            x = int(screen_x[local_index])
            y = int(screen_y[local_index])
            if x < -4 or y < -4 or x > IMAGE_SIZE_PX + 4 or y > IMAGE_SIZE_PX + 4:
                continue
            brightness = self.star_brightnesses[star_index]
            size = self.star_sizes[star_index]
            if size >= 2:
                glow = int(brightness * 0.25)
                draw.ellipse((x - size - 1, y - size - 1, x + size + 1, y + size + 1), fill=(glow, glow, glow))
            draw.ellipse((x - size, y - size, x + size, y + size), fill=(brightness, brightness, brightness))

    def render_frame(self, moon_position, trajectory_index, mission_log, engine_data, stage_data, slide, rotation_angle, camera_distance):
        image = Image.new("RGB", (IMAGE_SIZE_PX, IMAGE_SIZE_PX), "black")
        draw = ImageDraw.Draw(image)
        focal_length = IMAGE_SIZE_PX * 0.5
        camera_position, target_position = compute_cone_camera(slide, camera_distance, rotation_angle)
        camera_right, camera_up, camera_forward = build_camera_basis(camera_position, target_position, MOON_ENCOUNTER_VECTOR)
        self.draw_stars(draw, camera_right, camera_up, camera_forward, focal_length)
        ephemeris_time = mission_log[trajectory_index][0]
        earth_position = np.array([0.0, 0.0, 0.0], dtype=float)
        moon_position = np.array(to_tuple(moon_position), dtype=float)
        bodies = [{"name": "Earth", "position": earth_position, "radius": earth.radius, "colour": EARTH_BASE_COLOUR}, {"name": "Moon", "position": moon_position, "radius": moon.radius, "colour": MOON_DISC_COLOUR}]
        body_bounds = compute_body_bounds(bodies, camera_position, camera_right, camera_up, camera_forward, focal_length)
        
        if self.trajectory_cache is None or self.trajectory_cache_id != id(mission_log):
            self.trajectory_cache = np.array([to_tuple(entry[1]) for entry in mission_log], dtype=float)
            self.trajectory_cache_id = id(mission_log)
        
        trajectory_positions = self.trajectory_cache[:trajectory_index + 1]
        #trajectory_positions = make_trajectory_position_array(mission_log, trajectory_index)
        
        background_segments, foreground_segments = project_trajectory_segments(trajectory_positions, engine_data, camera_position, camera_right, camera_up, camera_forward, focal_length, bodies, body_bounds)

        draw_trajectory_segments(draw, background_segments, foreground=False)
        
        draw_bodies(draw, bodies, camera_position, camera_right, camera_up, camera_forward, focal_length)
        draw_earth_surface_markers(draw, ephemeris_time, camera_position, camera_right, camera_up, camera_forward, focal_length)
        
        draw_trajectory_segments(draw, foreground_segments, foreground=True)

        spacecraft_position = trajectory_positions[-1]
        spacecraft_velocity = np.array(to_tuple(mission_log[trajectory_index][2]), dtype=float)
        spacecraft_direction = unit_vector_or_none(spacecraft_velocity)
        spacecraft_screen = world_to_screen(spacecraft_position, camera_position, camera_right, camera_up, camera_forward, focal_length)
        engine_on = bool(engine_data[trajectory_index]) if trajectory_index < len(engine_data) else False

        if spacecraft_direction is not None and spacecraft_screen is not None and projected_point_is_reasonable(spacecraft_screen):
            spacecraft_occluded = body_occludes_projected_point(camera_position, spacecraft_position, spacecraft_screen[0], spacecraft_screen[1], bodies, body_bounds)
            if not spacecraft_occluded:
                draw_spacecraft_marker(draw, spacecraft_position, spacecraft_direction, stage_data, engine_on, camera_position, camera_right, camera_up, camera_forward, focal_length)

        image = image.resize((DISPLAY_SIZE_PX, DISPLAY_SIZE_PX), RESIZE_FILTER)
        return image