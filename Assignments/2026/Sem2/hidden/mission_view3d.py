# Do not modify this file. 
# You don't need to understand or use anything in this file.

import math
import numpy as np
import ipywidgets as widgets
from IPython.display import display, HTML as IPHTML
from threading import Timer
from html import escape

import spice_api
from celestial_body import earth
from mission_event import convert_seconds_to_string
from vector3d import to_tuple

from hidden.mission_render import MissionRender, DISPLAY_SIZE_PX
import hidden.camera_tracking as camera_tracking



STAGE_IMAGES = [
    ("Solid Rocket Boosters (SRB)", "images/SRB.jpg"),
    ("Core Stage", "images/Core.jpg"),
    ("Interim Cryogenic Propulsion Stage (ICPS)", "images/ICPS.jpg"),
    ("Orion Service Module", "images/SM.jpg"),
    ("Orion Crew Module", "images/Crew.jpg"),
    ("Re-entry", "images/Reentry.jpg"),
    ("Drogue Chutes", "images/Drogue.jpg"),
    ("Main Chutes", "images/MainChutes.jpg"),
    ("Splashdown", "images/Splashdown.jpg")
]


def apply_mission_view3d_css():
    css = """
    <style>
    .mission-root { background-color: #000000 !important; padding: 10px !important; width: fit-content !important; overflow: visible !important; }
    .mission-main-row { background-color: #000000 !important; overflow: visible !important; }
    .mission-separator { border-top: 1px solid #555555; margin: 8px 0px 8px 0px; }
    .mission-navigation-box { background-color: #202a34 !important; border: 3px solid #b8c7d8 !important; padding: 11px !important; margin: 0px 0px 10px 0px !important; overflow: hidden !important; box-shadow: 0px 0px 12px #000000 inset !important; }
    .mission-engine-channel { height: 13px !important; margin: 0px 0px 0px 0px !important; display: flex !important; align-items: center !important; justify-content: center !important; }
    .mission-engine-idle { width: 100% !important; height: 1px !important; background-color: #333333 !important; }
    .mission-engine-active { color: #ff5533 !important; font-family: 'Courier New', monospace !important; font-size: 12px !important; line-height: 13px !important; font-weight: bold !important; letter-spacing: 1px !important; text-align: center !important; text-shadow: 0px 0px 6px #ff3300 !important; }
    .mission-controls-panel { background-color: #0b0b0b !important; border: 1px solid #333333 !important; padding: 12px !important; width: 330px !important; height: 776px !important; margin-left: 10px !important; overflow: hidden !important; }
    .mission-telemetry-panel { background-color: #0b0b0b !important; border: 1px solid #333333 !important; padding: 12px !important; width: 480px !important; height: 776px !important; margin-left: 10px !important; overflow: hidden !important; }
    .mission-section-title { color: #ffffff !important; font-family: 'Courier New', monospace !important; font-size: 13px !important; font-weight: 700 !important; margin: 0px 0px 7px 0px !important; }
    .mission-stage-title { color: #dddddd !important; font-family: 'Courier New', monospace !important; font-size: 13px !important; font-weight: 700 !important; margin: 0px 0px 8px 0px !important; }
    .mission-button button, .mission-button .jupyter-button, .mission-button .widget-button { background: #e6e6e6 !important; color: #111111 !important; border: 1px solid #ffffff !important; box-shadow: -1px -1px 1px #ffffff inset, 2px 2px 3px #000000 !important; overflow: hidden !important; font-weight: 600 !important; }
    .mission-button-active button, .mission-button-active .jupyter-button, .mission-button-active .widget-button { background: #101818 !important; color: #00ffcc !important; border: 1px solid #00ffcc !important; box-shadow: 2px 2px 4px #000000 inset !important; overflow: hidden !important; font-weight: 700 !important; }
    .mission-button-continue button, .mission-button-continue .jupyter-button, .mission-button-continue .widget-button { background: #00ee44 !important; color: #003311 !important; border: 2px solid #00ff66 !important; box-shadow: 0px 0px 14px #00ff66 !important; font-weight: 800 !important; overflow: hidden !important; }
    .mission-controls-panel label { color: #ffffff !important; }
    .mission-controls-panel .widget-label { color: #ffffff !important; }
    .mission-controls-panel .widget-radio-box label { color: #ffffff !important; }
    .mission-controls-panel .widget-checkbox label { color: #ffffff !important; }
    .telemetry-value { color: #00ffcc !important; font-family: 'Courier New', monospace !important; font-size: 15px !important; letter-spacing: 1px !important; }
    .mission-events-title { color: #dddddd !important; font-family: 'Courier New', monospace !important; font-size: 13px !important; font-weight: 700 !important; margin-bottom: 6px !important; }
    .mission-event-row { font-family: 'Courier New', monospace !important; font-size: 12.5px !important; line-height: 17px !important; white-space: nowrap !important; letter-spacing: 0px !important; }
    .mission-event-tick { display: inline-block !important; width: 18px !important; color: #00ff66 !important; font-weight: bold !important; }
    .mission-event-name { display: inline-block !important; width: 350px !important; color: #bbbbbb !important; overflow: hidden !important; text-overflow: ellipsis !important; vertical-align: bottom !important; }
    .mission-event-time { display: inline-block !important; width: 90px !important; color: #00ffcc !important; text-align: right !important; }
    .mission-event-pending { opacity: 0.38 !important; }
    </style>
    """
    display(IPHTML(css))


def telemetry_line(label, value, unit="", dim=False, align="right"):
    opacity = "0.35" if dim else "1.0"
    if unit:
        return f"<div class='telemetry-value' style='opacity:{opacity}'><span style='display:inline-block; width:140px; color:#999'>{label}</span><span style='display:inline-block; width:100px; text-align:{align}'>{value}</span><span style='display:inline-block; width:50px; padding-left:8px; text-align:left; color:#99ccbb'>{unit}</span></div>"
    else:
        return f"<div class='telemetry-value' style='opacity:{opacity}'><span style='display:inline-block; width:140px; color:#999'>{label}</span><span style='display:inline-block; text-align:{align}'>{value}</span></div>"


def render_mission_events(event_entries, mission_log, current_index):
    rows = ["<div class='mission-events-title'>Mission Events</div>"]
    for event_index, event in event_entries:
        event_name = escape(event.event_name)
        if event_index <= current_index:
            event_time = convert_seconds_to_string(event.mission_elapsed_time) if event.mission_elapsed_time is not None else convert_seconds_to_string(mission_log[event_index][0] - mission_log[0][0])
            rows.append(f"<div class='mission-event-row'><span class='mission-event-tick'>✓</span><span class='mission-event-name'>{event_name}</span><span class='mission-event-time'>{event_time}</span></div>")
        else:
            rows.append(f"<div class='mission-event-row mission-event-pending'><span class='mission-event-tick'></span><span class='mission-event-name'>{event_name}</span><span class='mission-event-time'></span></div>")
    return "".join(rows)


def mission_event_kind_name(event):
    return getattr(event.event_kind, "name", str(event.event_kind))


def render_engine_bar(engine_on):
    if engine_on:
        return "<div class='mission-engine-channel'><div class='mission-engine-active'>🚀 ENGINE FIRING</div></div>"
    else:
        return "<div class='mission-engine-channel'><div class='mission-engine-idle'></div></div>"


def load_stage_images(stage_images):
    loaded_images = []
    for stage_name, image_path in stage_images:
        with open(image_path, "rb") as image_file:
            loaded_images.append({"name": stage_name, "path": image_path, "format": "jpg", "data": image_file.read()})
    return loaded_images


def stage_data_for_event_name(event_name, loaded_stage_images):
    if "SRB (Solid Rocket Booster) Separation" in event_name:
        return loaded_stage_images[1]
    if "Core Stage Separation" in event_name:
        return loaded_stage_images[2]
    if "Orion / ICPS Separation" in event_name:
        return loaded_stage_images[3]
    if "Service Module Separation" in event_name:
        return loaded_stage_images[4]
    if "Entry Interface" in event_name:
        return loaded_stage_images[5]
    if "Drogue Chute Deployment" in event_name:
        return loaded_stage_images[6]
    if "Main Parachute Deployment" in event_name:
        return loaded_stage_images[7]
    if "Splashdown" in event_name:
        return loaded_stage_images[8]
    return None


def build_stage_data_by_index(mission_log, loaded_stage_images):
    stage_data_by_index = []
    current_stage_data = loaded_stage_images[0]
    for index in range(len(mission_log)):
        event = mission_log[index][3]
        if event is not None:
            new_stage_data = stage_data_for_event_name(event.event_name, loaded_stage_images)
            if new_stage_data is not None:
                current_stage_data = new_stage_data
        stage_data_by_index.append(current_stage_data)
    return stage_data_by_index


def build_engine_data_by_index(mission_log):
    engine_data_by_index = []
    engine_on = False
    for index in range(len(mission_log)):
        event = mission_log[index][3]   
        if event is not None:
            event_name = getattr(event.event_kind, "name", str(event.event_kind))
            if event_name == "LIFTOFF" or event_name == "BURN_START":
                engine_on = True   
        engine_data_by_index.append(engine_on)
        if event is not None:
            event_name = getattr(event.event_kind, "name", str(event.event_kind))        
            if event_name == "BURN_CUTOFF":
                engine_on = False
    return engine_data_by_index
    

def next_event_index_after(event_indices, current_index):   
    for event_index in event_indices:
        if event_index > current_index:
            return event_index
    return None


def previous_event_index_before(event_indices, current_index):
    for event_index in reversed(event_indices):
        if event_index < current_index:
            return event_index
    return None


class MissionView3D:

    def __init__(self, mission_log):
        self.mission_log = mission_log
        self.renderer = MissionRender()
        self.playing = False
        self.paused_at_event = False
        self.play_timer = None
        self.play_direction = 1
        self.last_play_direction = 1
        self.play_target_index = None
        self.current_stage_data = None
        self.time_max = len(mission_log) - 1
        apply_mission_view3d_css()
        self.prepare_data()
        self.create_widgets()
        self.create_layout()
        self.register_callbacks()
        self.set_playback_button_descriptions_and_styles()
        if self.time_max >= 0:
            self.set_time(0)

    def prepare_data(self):
        self.event_entries = [(index, self.mission_log[index][3]) for index in range(len(self.mission_log)) if self.mission_log[index][3] is not None]
        self.event_indices = [index for index in range(len(self.mission_log)) if self.mission_log[index][3] is not None]
        self.engine_data_by_index = build_engine_data_by_index(self.mission_log)        
        self.loaded_stage_images = load_stage_images(STAGE_IMAGES)
        self.stage_data_by_index = build_stage_data_by_index(self.mission_log, self.loaded_stage_images)
        #self.camera_keyframes = [(0, -0.016, 30000), (155, -0.016, 30000), (362, 0.07, 37000), (844, 0.09, 48000), (1500, -0.02, 48000), (1782, 0.07, 48000), (3197, 0.50, 228000), (7231, 1.00, 30000), (11152, 0.50, 228000), (12381, 0.16, 98000), (12833, 0.07, 46000), (self.time_max, -0.02, 30000)]
        #self.camera_keyframes = [(0, -0.016, 30000), (155, -0.016, 50000), (886, -0.016, 100000), (1500, -0.016, 100000), (1782, 0.07, 48000), (3197, 0.50, 228000), (7231, 1.00, 30000), (11152, 0.50, 228000), (12381, 0.16, 98000), (12833, 0.07, 46000), (self.time_max, -0.02, 30000)]
        self.camera_keyframes = camera_tracking.compute_keyframes(self.mission_log)
        

    def create_widgets(self):
        self.image_widget = widgets.Image(layout=widgets.Layout(width=f"{DISPLAY_SIZE_PX}px", height=f"{DISPLAY_SIZE_PX}px"))
        self.rotate = widgets.FloatSlider(value=0, min=-math.pi, max=math.pi, step=0.01, readout=False, layout=widgets.Layout(width="285px"))
        self.jump_start_button = widgets.Button(description="|< Start", tooltip="Jump to start", layout=widgets.Layout(width="140px", height="30px", overflow="hidden"))
        self.jump_end_button = widgets.Button(description="End >|", tooltip="Jump to end", layout=widgets.Layout(width="140px", height="30px", overflow="hidden"))
        self.rewind_button = widgets.Button(description="◀ Rewind", tooltip="Rewind / Continue rewinding", layout=widgets.Layout(width="140px", height="30px", overflow="hidden"))
        self.play_button = widgets.Button(description="▶ Play", tooltip="Play / Pause / Continue forward", layout=widgets.Layout(width="140px", height="30px", overflow="hidden"))
        self.speed_selector = widgets.RadioButtons(options=[("×1", 1), ("×10", 10), ("×100", 100)], value=1, layout=widgets.Layout(width="130px", overflow="hidden"))
        self.pause_at_event = widgets.Checkbox(value=False, description="Pause at next event", indent=False, layout=widgets.Layout(width="220px", overflow="hidden"))
        self.stage_label = widgets.HTML()
        self.vehicle_image = widgets.Image(format="jpg", layout=widgets.Layout(width="100%", height="270px", margin="8px 0px 0px 0px", border="1px solid #111111", object_fit="contain", object_position="center center"))
        self.time_value_widget = widgets.HTML()
        self.elapsed_value_widget = widgets.HTML()
        self.engine_bar = widgets.HTML()
        self.alt_row = widgets.HTML()
        self.speed_row = widgets.HTML()
        self.airspeed_row = widgets.HTML()
        self.events_widget = widgets.HTML()
        self.separator_1 = widgets.HTML("<div class='mission-separator'></div>")
        self.separator_2 = widgets.HTML("<div class='mission-separator'></div>")
        for button in [self.jump_start_button, self.jump_end_button, self.rewind_button, self.play_button]:
            button.add_class("mission-button")
        self.rotate.style = {"handle_color": "#5aa9ff"}

    def create_layout(self):
        self.navigation_title = widgets.HTML("<div class='mission-section-title'>Navigation</div>")
        self.transport_row_1 = widgets.HBox([self.jump_start_button, self.jump_end_button], layout=widgets.Layout(align_items="center", justify_content="space-between", height="34px", margin="0px 0px 4px 0px", overflow="hidden"))
        self.transport_row_2 = widgets.HBox([self.rewind_button, self.play_button], layout=widgets.Layout(align_items="center", justify_content="space-between", height="34px", margin="0px 0px 8px 0px", overflow="hidden"))
        self.speed_title = widgets.HTML("<div class='mission-section-title'>Playback Speed</div>")
        self.rotate_title = widgets.HTML("<div class='mission-section-title'>Rotate View</div>")
        self.rotate_row = widgets.HBox([self.rotate], layout=widgets.Layout(align_items="center", height="36px", margin="0px 0px 0px 0px", overflow="hidden"))
        self.navigation_box = widgets.VBox([self.navigation_title, self.transport_row_1, self.transport_row_2, self.speed_title, self.speed_selector, self.pause_at_event, widgets.HTML("<div class='mission-separator'></div>"), self.rotate_title, self.rotate_row], layout=widgets.Layout(overflow="hidden"))
        self.navigation_box.add_class("mission-navigation-box")
        self.controls_panel = widgets.VBox([self.navigation_box, self.stage_label, self.vehicle_image], layout=widgets.Layout(overflow="hidden"))
        self.controls_panel.add_class("mission-controls-panel")
        self.telemetry_panel = widgets.VBox([self.time_value_widget, self.elapsed_value_widget, self.engine_bar, self.alt_row, self.speed_row, self.airspeed_row, self.separator_1, self.events_widget, self.separator_2], layout=widgets.Layout(overflow="hidden"))
        self.telemetry_panel.add_class("mission-telemetry-panel")
        self.main_row = widgets.HBox([self.image_widget, self.controls_panel, self.telemetry_panel], layout=widgets.Layout(align_items="flex-start", overflow="visible"))
        self.main_row.add_class("mission-main-row")
        self.root = widgets.VBox([self.main_row], layout=widgets.Layout(overflow="visible"))
        self.root.add_class("mission-root")

    def register_callbacks(self):
        self.jump_start_button.on_click(self.jump_to_start)
        self.jump_end_button.on_click(self.jump_to_end)
        self.rewind_button.on_click(self.rewind)
        self.play_button.on_click(self.toggle_play)
        self.pause_at_event.observe(self.on_pause_at_event_changed, names="value")
        self.rotate.observe(self.update, names="value")

    def smoothstep(self, u):
        return u * u * (3.0 - 2.0 * u)

    def interpolate_keyframes(self, index):
        for keyframe_index in range(len(self.camera_keyframes) - 1):
            t0, s0, z0 = self.camera_keyframes[keyframe_index]
            t1, s1, z1 = self.camera_keyframes[keyframe_index + 1]
            if t0 <= index <= t1:
                if t1 == t0:
                    return s0, z0
                u = (index - t0) / (t1 - t0)
                u = self.smoothstep(u)
                slide_value = (1.0 - u) * s0 + u * s1
                zoom_value = int((1.0 - u) * z0 + u * z1)
                return slide_value, zoom_value
        return self.camera_keyframes[-1][1], self.camera_keyframes[-1][2]

    def reset_button_visual(self, button):
        button.remove_class("mission-button-active")
        button.remove_class("mission-button-continue")
        button.button_style = ""
        button.style.button_color = None

    def clear_transport_styles(self):
        self.reset_button_visual(self.rewind_button)
        self.reset_button_visual(self.play_button)

    def set_playback_button_descriptions_and_styles(self):
        self.clear_transport_styles()
        if self.playing:
            self.play_button.description = "⏸ Pause"
            self.play_button.add_class("mission-button-active")
            if self.play_direction < 0:
                self.rewind_button.description = "◀ Rewind"
                self.rewind_button.add_class("mission-button-active")
            else:
                self.rewind_button.description = "◀ Rewind"
        elif self.paused_at_event and self.last_play_direction < 0:
            self.rewind_button.description = "◀ Continue"
            self.rewind_button.add_class("mission-button-continue")
            self.rewind_button.button_style = "success"
            self.rewind_button.style.button_color = "#00ee44"
            self.play_button.description = "▶ Play"
        elif self.paused_at_event:
            self.play_button.description = "▶ Continue"
            self.play_button.add_class("mission-button-continue")
            self.play_button.button_style = "success"
            self.play_button.style.button_color = "#00ee44"
            self.rewind_button.description = "◀ Rewind"
        else:
            self.rewind_button.description = "◀ Rewind"
            self.play_button.description = "▶ Play"

    def set_pause_target_from_current_position(self):
        if not self.pause_at_event.value:
            self.play_target_index = None
        elif self.play_direction > 0:
            self.play_target_index = next_event_index_after(self.event_indices, self.time)
        else:
            self.play_target_index = previous_event_index_before(self.event_indices, self.time)

    def stop_playback(self, paused_by_event=False):
        self.playing = False
        self.paused_at_event = paused_by_event
        self.play_target_index = None
        if self.play_timer is not None:
            self.play_timer.cancel()
            self.play_timer = None
        self.set_playback_button_descriptions_and_styles()

    def start_playback(self, direction):
        if self.play_timer is not None:
            self.play_timer.cancel()
            self.play_timer = None
        self.playing = True
        self.paused_at_event = False
        self.play_direction = direction
        self.last_play_direction = direction
        self.set_pause_target_from_current_position()
        self.set_playback_button_descriptions_and_styles()
        self.step_play()

    def set_time(self, value):
        self.time = max(0, min(self.time_max, int(value)))
        self.update()

    def step_play(self):
        if not self.playing:
            return
        if self.pause_at_event.value and self.play_target_index is None:
            self.set_pause_target_from_current_position()
        if self.play_direction > 0 and self.time >= self.time_max:
            self.stop_playback(False)
            return
        if self.play_direction < 0 and self.time <= 0:
            self.stop_playback(False)
            return
        step = self.speed_selector.value * self.play_direction
        proposed_value = self.time + step
        if self.play_target_index is not None and self.play_direction > 0 and proposed_value >= self.play_target_index:
            self.set_time(self.play_target_index)
            self.stop_playback(True)
            return
        if self.play_target_index is not None and self.play_direction < 0 and proposed_value <= self.play_target_index:
            self.set_time(self.play_target_index)
            self.stop_playback(True)
            return
        self.set_time(proposed_value)
        if self.play_direction > 0 and self.time >= self.time_max:
            self.stop_playback(False)
            return
        if self.play_direction < 0 and self.time <= 0:
            self.stop_playback(False)
            return
           
        self.play_timer = Timer(0.03, self.step_play)
        self.play_timer.start()

    def on_pause_at_event_changed(self, change):
        if self.playing:
            self.set_pause_target_from_current_position()
        elif not self.pause_at_event.value and self.paused_at_event:
            self.paused_at_event = False
            self.set_playback_button_descriptions_and_styles()

    def jump_to_start(self, button):
        self.stop_playback(False)
        self.set_time(0)

    def jump_to_end(self, button):
        self.stop_playback(False)
        self.set_time(self.time_max)

    def toggle_play(self, button):
        if self.playing:
            self.stop_playback(False)
        elif self.paused_at_event and self.last_play_direction > 0:
            self.start_playback(1)
        else:
            self.start_playback(1)

    def rewind(self, button):
        if self.paused_at_event and self.last_play_direction < 0:
            self.start_playback(-1)
        else:
            self.start_playback(-1)

    def update(self, change=None):
        index = self.time

        engine_on = self.engine_data_by_index[index]
        stage_data = self.stage_data_by_index[index]
        
        ephemeris_time = self.mission_log[index][0]
        spacecraft_position_vec = self.mission_log[index][1]
        spacecraft_velocity_vec = self.mission_log[index][2]
        spacecraft_position = np.array(to_tuple(spacecraft_position_vec), dtype=float)
        spacecraft_velocity = np.array(to_tuple(spacecraft_velocity_vec), dtype=float)
        auto_slide, auto_zoom = self.interpolate_keyframes(index)

        image = self.renderer.render_frame(spice_api.moon_position(ephemeris_time), index, self.mission_log, self.engine_data_by_index, stage_data, slide=auto_slide, rotation_angle=self.rotate.value + 0.016, camera_distance=auto_zoom)
        self.image_widget.value = image._repr_png_()
        
        start_time = self.mission_log[0][0]
        elapsed = convert_seconds_to_string(ephemeris_time - start_time)
        utc = spice_api.ephemeris_time_to_utc_string(ephemeris_time)
        altitude = np.linalg.norm(spacecraft_position) - earth.radius
        speed = np.linalg.norm(spacecraft_velocity)
        atmospheric_velocity = spice_api.atmosphere_rotation_velocity(spacecraft_position_vec, ephemeris_time)
        relative_velocity = spacecraft_velocity - np.array(to_tuple(atmospheric_velocity), dtype=float)

        if altitude < 150:
            airspeed = np.linalg.norm(relative_velocity) * 1000
            self.airspeed_row.value = telemetry_line("Airspeed:", f"{airspeed:5.2f}", "m/s")
        else:
            self.airspeed_row.value = telemetry_line("Airspeed:", "", "m/s", dim=True)
        if stage_data is not self.current_stage_data:
            self.vehicle_image.format = stage_data["format"]
            self.vehicle_image.value = stage_data["data"]
            self.current_stage_data = stage_data
        self.stage_label.value = f"<div class='mission-stage-title'>{escape(stage_data['name'])}</div>"
        self.time_value_widget.value = telemetry_line("UTC Time:", f"{utc} ({index})", align="left")
        self.elapsed_value_widget.value = telemetry_line("Elapsed Time:", f"{elapsed}", align="left")
        self.engine_bar.value = render_engine_bar(engine_on)
        self.alt_row.value = telemetry_line("Altitude:", f"{altitude:,.1f}", "km")
        self.speed_row.value = telemetry_line("Speed:", f"{speed:5.2f}", "km/s")
        
        self.events_widget.value = render_mission_events(self.event_entries, self.mission_log, index)
        
    def display(self):
        display(self.root)


def mission_view3D(mission_log):
    if mission_log:
        viewer = MissionView3D(mission_log)
        viewer.display()
        return viewer
    else:
        print('Mission log contains no entries')