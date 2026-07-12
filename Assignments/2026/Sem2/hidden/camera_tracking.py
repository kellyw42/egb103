import numpy as np
import spice_api
from celestial_body import earth
from vector3d import to_tuple
from .mission_render import MOON_ENCOUNTER_VECTOR

FRAME_MARGIN                = 1.4
MIN_CAMERA_DISTANCE_KM      = 30_000
MAX_CAMERA_DISTANCE_KM      = 380_000
NEAR_EARTH_SLIDE            = -0.016
NEAR_EARTH_ALT_KM           = 2_000
SPLASHDOWN_ALT_KM           = 30
EXTREMA_MIN_SEPARATION      = 30
EXTREMA_MIN_PROMINENCE_KM   = 200
MAX_GAP_FILL_ITERATIONS     = 20
GAP_FILL_MIN_SHORTFALL_KM   = 8_000
MIN_GAP_FILL_SEGMENT        = 50

_enc_unit   = None
_enc_length = None

def _init_encounter_axis():
    global _enc_unit, _enc_length
    if _enc_unit is not None:
        return
    v = np.array(MOON_ENCOUNTER_VECTOR, dtype=float)
    _enc_length = float(np.linalg.norm(v))
    _enc_unit = v / _enc_length

def slide_for_position(pos):
    _init_encounter_axis()
    projected = float(np.dot(np.asarray(pos, dtype=float), _enc_unit))
    return float(np.clip(projected / _enc_length, NEAR_EARTH_SLIDE, 1.02))

def _midpoint_slide(pos_a, pos_b):
    return slide_for_position((np.asarray(pos_a, dtype=float) + np.asarray(pos_b, dtype=float)) * 0.5)

def _local_maxima(values, min_separation=EXTREMA_MIN_SEPARATION, min_prominence=EXTREMA_MIN_PROMINENCE_KM):
    n = len(values)
    if n < 3:
        return []
    candidates = [i for i in range(1, n - 1) if values[i] > values[i - 1] and values[i] >= values[i + 1]]
    merged = []
    for idx in candidates:
        if merged and idx - merged[-1] < min_separation:
            if values[idx] > values[merged[-1]]:
                merged[-1] = idx
        else:
            merged.append(idx)
    results = []
    for idx in merged:
        w = min(min_separation, idx, n - 1 - idx)
        if w == 0:
            continue
        left_valley  = min(values[idx - w : idx])
        right_valley = min(values[idx + 1 : idx + w + 1])
        if values[idx] - min(left_valley, right_valley) >= min_prominence:
            results.append(idx)
    return results

def _local_minima(values, min_separation=EXTREMA_MIN_SEPARATION, min_prominence=EXTREMA_MIN_PROMINENCE_KM):
    return _local_maxima([-v for v in values], min_separation=min_separation, min_prominence=min_prominence)

def _find_splashdown_index(earth_distances):
    threshold = earth.radius + SPLASHDOWN_ALT_KM
    n = len(earth_distances)
    if earth_distances[-1] > threshold + 1_000:
        return None
    for i in range(n - 1, -1, -1):
        if earth_distances[i] > threshold:
            return i + 1
    return 0

def _apogees_between_perigees(outbound_perigees, earth_distances):
    apogees = []
    for j in range(len(outbound_perigees) - 1):
        start = outbound_perigees[j]
        end   = outbound_perigees[j + 1]
        if end - start < 3:
            continue
        peak_index = int(np.argmax(earth_distances[start : end + 1])) + start
        if start < peak_index < end:
            apogees.append(peak_index)
    return apogees

def analyse_trajectory(mission_log):
    _init_encounter_axis()
    n = len(mission_log)
    earth_distances      = np.empty(n, dtype=float)
    moon_distances       = np.empty(n, dtype=float)
    moon_positions       = np.empty((n, 3), dtype=float)
    spacecraft_positions = np.empty((n, 3), dtype=float)
    for i in range(n):
        t        = mission_log[i][0]
        pos      = np.array(to_tuple(mission_log[i][1]), dtype=float)
        moon_pos = np.array(to_tuple(spice_api.moon_position(t)), dtype=float)
        earth_distances[i]      = np.linalg.norm(pos)
        moon_distances[i]       = np.linalg.norm(pos - moon_pos)
        moon_positions[i]       = moon_pos
        spacecraft_positions[i] = pos
    altitudes            = earth_distances - earth.radius
    ed_list              = list(earth_distances)
    perigee_indices      = _local_minima(ed_list)
    apogee_indices       = _local_maxima(ed_list)
    earth_moon_crossover = next((i for i in range(n) if moon_distances[i] < earth_distances[i]), n - 1)
    moon_closest         = int(np.argmin(moon_distances))
    moon_earth_crossover = next((i for i in range(earth_moon_crossover, n) if earth_distances[i] < moon_distances[i]), None)
    splashdown_index     = _find_splashdown_index(ed_list)
    outbound_perigees    = [i for i in perigee_indices if i < earth_moon_crossover]
    tli_index            = outbound_perigees[-1] if outbound_perigees else earth_moon_crossover
    pre_tli_apogees      = _apogees_between_perigees(outbound_perigees, earth_distances)
    return_end           = splashdown_index if splashdown_index is not None else n
    return_start         = moon_earth_crossover if moon_earth_crossover is not None else n
    return_apogees       = [i for i in apogee_indices  if return_start < i < return_end]
    return_perigees      = [i for i in perigee_indices if return_start < i < return_end]
    return {
        'n':                     n,
        'earth_distances':       earth_distances,
        'moon_distances':        moon_distances,
        'moon_positions':        moon_positions,
        'spacecraft_positions':  spacecraft_positions,
        'altitudes':             altitudes,
        'apogee_indices':        apogee_indices,
        'perigee_indices':       perigee_indices,
        'pre_tli_apogees':       pre_tli_apogees,
        'outbound_perigees':     outbound_perigees,
        'tli_index':             tli_index,
        'earth_moon_crossover':  earth_moon_crossover,
        'moon_closest':          moon_closest,
        'moon_earth_crossover':  moon_earth_crossover,
        'return_apogees':        return_apogees,
        'return_perigees':       return_perigees,
        'splashdown_index':      splashdown_index,
    }

def _camera_distance_for(target_pos, *positions):
    max_d = max(float(np.linalg.norm(np.asarray(p, dtype=float) - np.asarray(target_pos, dtype=float))) for p in positions)
    return int(np.clip(FRAME_MARGIN * max_d, MIN_CAMERA_DISTANCE_KM, MAX_CAMERA_DISTANCE_KM))

def _camera_params_at(index, analysis, mission_log, mode='auto', force_slide=None):
    spacecraft_pos = analysis['spacecraft_positions'][index]
    moon_pos       = analysis['moon_positions'][index]
    earth_pos      = np.zeros(3, dtype=float)
    altitude_km    = float(analysis['altitudes'][index])
    moon_dominated = analysis['moon_distances'][index] < analysis['earth_distances'][index]
    enc            = np.array(MOON_ENCOUNTER_VECTOR, dtype=float)
    if force_slide is not None:
        slide      = force_slide
        target_pos = enc * slide
        dist       = _camera_distance_for(target_pos, spacecraft_pos, earth_pos)
    elif altitude_km < NEAR_EARTH_ALT_KM:
        slide      = NEAR_EARTH_SLIDE
        target_pos = enc * slide
        dist       = _camera_distance_for(target_pos, spacecraft_pos, earth_pos)
    elif mode == 'earth_to_moon':
        slide      = _midpoint_slide(earth_pos, spacecraft_pos)
        target_pos = enc * slide
        dist       = _camera_distance_for(target_pos, spacecraft_pos, earth_pos, moon_pos)
    elif mode == 'moon_to_earth':
        slide      = _midpoint_slide(spacecraft_pos, moon_pos)
        target_pos = enc * slide
        dist       = _camera_distance_for(target_pos, spacecraft_pos, moon_pos, earth_pos)
    elif moon_dominated or mode == 'moon':
        slide      = _midpoint_slide(spacecraft_pos, moon_pos)
        target_pos = enc * slide
        dist       = _camera_distance_for(target_pos, spacecraft_pos, moon_pos)
    else:
        slide      = _midpoint_slide(earth_pos, spacecraft_pos)
        target_pos = enc * slide
        dist       = _camera_distance_for(target_pos, spacecraft_pos, earth_pos)
    return slide, dist

def _gap_fill_dist_at(index, interp_slide, analysis):
    enc            = np.array(MOON_ENCOUNTER_VECTOR, dtype=float)
    spacecraft_pos = analysis['spacecraft_positions'][index]
    moon_pos       = analysis['moon_positions'][index]
    earth_pos      = np.zeros(3, dtype=float)
    moon_dominated = analysis['moon_distances'][index] < analysis['earth_distances'][index]
    target_pos     = enc * interp_slide
    hero_pos       = moon_pos if moon_dominated else earth_pos
    return interp_slide, _camera_distance_for(target_pos, spacecraft_pos, hero_pos)

def _enforce_monotone_zoom_out(kf_dict, tli_index):
    max_dist = MIN_CAMERA_DISTANCE_KM
    result   = {}
    for t in sorted(kf_dict.keys()):
        s, z = kf_dict[t]
        if t <= tli_index:
            z        = max(z, max_dist)
            max_dist = z
        result[t] = (s, z)
    return result

def _adaptive_gap_fill(kf_dict, analysis, mission_log):
    enc                  = np.array(MOON_ENCOUNTER_VECTOR, dtype=float)
    spacecraft_positions = analysis['spacecraft_positions']
    moon_positions       = analysis['moon_positions']
    moon_distances       = analysis['moon_distances']
    earth_distances      = analysis['earth_distances']
    tli_index            = analysis['tli_index']
    for _ in range(MAX_GAP_FILL_ITERATIONS):
        sorted_times           = sorted(kf_dict.keys())
        best_segment_t         = None
        best_segment_shortfall = GAP_FILL_MIN_SHORTFALL_KM
        for i in range(len(sorted_times) - 1):
            t0     = sorted_times[i]
            t1     = sorted_times[i + 1]
            if t1 - t0 <= MIN_GAP_FILL_SEGMENT:
                continue
            s0, z0  = kf_dict[t0]
            s1, z1  = kf_dict[t1]
            indices = np.arange(t0 + 1, t1)
            u       = (indices - t0) / (t1 - t0)
            u       = u * u * (3.0 - 2.0 * u)
            slide_i  = (1.0 - u) * s0 + u * s1
            dist_i   = (1.0 - u) * z0 + u * z1
            target_i = np.outer(slide_i, enc)
            d_craft  = np.linalg.norm(spacecraft_positions[indices] - target_i, axis=1)
            moon_dom = moon_distances[indices] < earth_distances[indices]
            hero_i   = np.where(moon_dom[:, np.newaxis], moon_positions[indices], np.zeros((len(indices), 3), dtype=float))
            d_hero   = np.linalg.norm(hero_i - target_i, axis=1)
            required      = np.clip(FRAME_MARGIN * np.maximum(d_craft, d_hero), 0, MAX_CAMERA_DISTANCE_KM)
            max_shortfall = float(np.max(required - dist_i))
            if max_shortfall > best_segment_shortfall:
                best_segment_shortfall = max_shortfall
                best_segment_t         = (t0, t1)
        if best_segment_t is None:
            break
        t0, t1    = best_segment_t
        mid_index = (t0 + t1) // 2
        if mid_index <= tli_index:
            kf_dict[mid_index] = _camera_params_at(mid_index, analysis, mission_log, force_slide=NEAR_EARTH_SLIDE)
        else:
            s0, z0       = kf_dict[t0]
            s1, _        = kf_dict[t1]
            u_mid        = (mid_index - t0) / (t1 - t0)
            u_mid        = u_mid * u_mid * (3.0 - 2.0 * u_mid)
            interp_slide = float((1.0 - u_mid) * s0 + u_mid * s1)
            kf_dict[mid_index] = _gap_fill_dist_at(mid_index, interp_slide, analysis)
    return kf_dict

def compute_keyframes(mission_log, analysis=None):
    if not mission_log:
        return [(0, NEAR_EARTH_SLIDE, MIN_CAMERA_DISTANCE_KM)]
    if analysis is None:
        analysis = analyse_trajectory(mission_log)
    time_max  = analysis['n'] - 1
    tli_index = analysis['tli_index']
    kf = {}
    kf[0] = _camera_params_at(0, analysis, mission_log, force_slide=NEAR_EARTH_SLIDE)
    if float(analysis['altitudes'][-1]) < NEAR_EARTH_ALT_KM:
        kf[time_max] = _camera_params_at(time_max, analysis, mission_log, force_slide=NEAR_EARTH_SLIDE)
    else:
        kf[time_max] = _camera_params_at(time_max, analysis, mission_log)
    for i in analysis['pre_tli_apogees']:   kf[i] = _camera_params_at(i, analysis, mission_log, force_slide=NEAR_EARTH_SLIDE)
    for i in analysis['outbound_perigees']: kf[i] = _camera_params_at(i, analysis, mission_log, force_slide=NEAR_EARTH_SLIDE)
    kf[analysis['earth_moon_crossover']] = _camera_params_at(analysis['earth_moon_crossover'], analysis, mission_log, mode='earth_to_moon')
    kf[analysis['moon_closest']]         = _camera_params_at(analysis['moon_closest'],         analysis, mission_log, mode='moon')
    if analysis['moon_earth_crossover'] is not None:
        kf[analysis['moon_earth_crossover']] = _camera_params_at(analysis['moon_earth_crossover'], analysis, mission_log, mode='moon_to_earth')
    for i in analysis['return_apogees']:  kf[i] = _camera_params_at(i, analysis, mission_log)
    for i in analysis['return_perigees']: kf[i] = _camera_params_at(i, analysis, mission_log)
    if analysis['splashdown_index'] is not None:
        kf[analysis['splashdown_index']] = _camera_params_at(analysis['splashdown_index'], analysis, mission_log, force_slide=NEAR_EARTH_SLIDE)
    kf = _enforce_monotone_zoom_out(kf, tli_index)
    kf = _adaptive_gap_fill(kf, analysis, mission_log)
    kf = _enforce_monotone_zoom_out(kf, tli_index)
    return [(t, s, z) for t, (s, z) in sorted(kf.items())]