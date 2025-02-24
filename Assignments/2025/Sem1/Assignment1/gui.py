import math
from vector_2d import vector_magnitude, vector_angle_radians
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.pyplot as plt
import ipywidgets as widgets
import matplotlib.animation as animation  

def convert_to_feet(metres) :
    return metres / 0.3048

def convert_to_nautical_miles(metres) :
    return metres / 1852   

def convert_to_knots(metres_per_second) :
    return metres_per_second * 1.9438444924406  

def rotate_point(point, centre, angle_radians):
    
    # Translate point back to origin
    translated_x = point[0] - centre[0]
    translated_y = point[1] - centre[1]
    
    # Rotate point
    rotated_x = translated_x * math.cos(angle_radians) - translated_y * math.sin(angle_radians)
    rotated_y = translated_x * math.sin(angle_radians) + translated_y * math.cos(angle_radians)
    
    # Translate point back to its original position
    final_x = rotated_x + centre[0]
    final_y = rotated_y + centre[1]
    
    return (final_x, final_y)

def rotate_points(points, centre, angle_radians) :
    rotated_points = []
    for point in points :
        rotated_points.append(rotate_point(point, centre, angle_radians))
    return rotated_points

class AircraftIllustration :
    
    fuselage_vertices = [(-180,60), (-160,60), (-125,10), (-70,10), (-45,25), (0,35), (10,25), (30,15), (70,10), (80,0), (82,35), (82,-35), (80,0), (70,-10), (60,-18), (-35,-25), (-175,-5), (-180,60)]    
    wing_vertices = [(-55,26), (7,28), (10,27), (11,28), (11,30), (8,32), (1,36), (-11,35), (-18,35), (-55,26)]        
    
    def __init__(self) : 
        plt.ion()
        self.fig, ax = plt.subplots()
        ax.set_xlim(-200, 200)
        ax.set_ylim(-200, 200)
        ax.set_aspect('equal')
        ax.axis('off')
     
        fuselage_path = Path(self.fuselage_vertices)
        self.fuselage = PathPatch(fuselage_path, facecolor='blue', edgecolor='black', lw=1, antialiased=True)
        ax.add_patch(self.fuselage)   
        
        wing_path = Path(self.wing_vertices)
        self.wing = PathPatch(wing_path, facecolor='red', lw=1, antialiased=True)
        ax.add_patch(self.wing)   
        
        self.wheels = ax.scatter([], [], facecolors='none', edgecolors='black', s=100, linewidth=3)  
        self.support1, = ax.plot([], [], color = 'black', zorder=0)
        self.support2, = ax.plot([], [], color = 'black', zorder=0)  
        self.elevator, = ax.plot([], [], color = 'red', linewidth = 2)
        self.air_direction, = ax.plot([], [], color='green', linewidth=2)
        self.arrow1, = ax.plot([], [], color='green', linewidth=2)
        self.arrow2, = ax.plot([], [], color='green', linewidth=2)
        
        self.ground, = ax.plot([], [], color = 'black', linewidth = 5)  
        
        self.update(0, 0, 0, (0, 0))

        self.fig.canvas.header_visible = False
        self.fig.canvas.footer_visible = False
    
    def update(self, pitch_angle_radians, altitude_metres, elevator_angle_radians, velocity):        
        self.fuselage.set_path(Path(rotate_points(self.fuselage_vertices, (0, 0), pitch_angle_radians)))    
        self.wing.set_path(Path(rotate_points(self.wing_vertices, (0, 0), pitch_angle_radians)))   

        length = vector_magnitude(velocity)*4
        (dx,dy) = rotate_point((length ,0), (0, 0), vector_angle_radians(velocity))            
        self.air_direction.set_data([0, dx], [0, dy])  

        # adjust length of arrow head
        lx = 9
        ly = 5
        if length < 20:
            lx *= (length/20)
            ly *= (length/20)
            
        arrow1 = (dx - lx, dy - ly)
        arrow2 = (dx - lx, dy + ly)   
        (dx1, dy1) = rotate_point(arrow1, (dx, dy), vector_angle_radians(velocity))
        (dx2, dy2) = rotate_point(arrow2, (dx, dy), vector_angle_radians(velocity))
        self.arrow1.set_data([dx, dx1], [dy, dy1])
        self.arrow2.set_data([dx, dx2], [dy, dy2])
        
        (x_pivot, y_pivot) = rotate_point((-170, 0), (0, 0), pitch_angle_radians)
        (x_rear, y_rear)   = rotate_point((x_pivot-30, y_pivot), (x_pivot, y_pivot), pitch_angle_radians + elevator_angle_radians*3)
        (x_front, y_front) = rotate_point((x_pivot+20, y_pivot), (x_pivot, y_pivot), pitch_angle_radians + elevator_angle_radians*3)    
        self.elevator.set_data([x_rear, x_front], [y_rear, y_front])
     
        rear_wheel = rotate_point((-15, -40), (0, 0), pitch_angle_radians)
        front_wheel = rotate_point((60, -40), (0, 0), pitch_angle_radians)
        self.wheels.set_offsets([rear_wheel, front_wheel])
    
        (top_x, top_y) = rotate_point((-10, 0), (0, 0), pitch_angle_radians)
        (bottom_x, bottom_y) = rotate_point((-15, -40), (0, 0), pitch_angle_radians)
        self.support1.set_data([top_x, bottom_x], [top_y, bottom_y])
    
        (top_x, top_y) = rotate_point((40, 0), (0, 0), pitch_angle_radians)
        (bottom_x, bottom_y) = rotate_point((60, -40), (0, 0), pitch_angle_radians)
        self.support2.set_data([top_x, bottom_x], [top_y, bottom_y])    
            
        altitude = altitude_metres * 50
        self.ground.set_data([-200, 200], [-50 - altitude, -50 - altitude])    

class GUIFlightSimulator() :

    def __init__(self, aircraft_model, simulate_multiple_time_steps, steps_per_iteration, delta_time) :
        self.aircraft_model = aircraft_model
        self.simulate_multiple_time_steps = simulate_multiple_time_steps
        self.steps_per_iteration = steps_per_iteration
        self.delta_time = delta_time
        self.illustration = AircraftIllustration()
        self.create_cockpit()    
        self.restart_simulation(None) # create the plane

    def create_cockpit(self) :
        self.initiate_button = widgets.Button(description="Enable Play", disabled=False)
        self.play_button = widgets.Button(description="Play", disabled=True)
        self.pause_button = widgets.Button(description="Pause", disabled=True)
        self.step_button = widgets.Button(description="Single Step", disabled=False)
        self.restart_button = widgets.Button(description="Restart", disabled=False)

        self.test_button = widgets.Button(description="Log Text", disabled=False)
        
        self.timestep_widget = widgets.Text(description="Time Elapsed:", disabled=True)
        self.altitude_widget = widgets.Text(description="Altimeter:", disabled=True)
        self.distance_widget = widgets.Text(description="Distance Travelled:", disabled=True, description_width='initial')
        self.airspeed_widget = widgets.Text(description="Airspeed:", disabled=True);
        self.vertical_speed_widget = widgets.Text(description="Vertical Speed:", disabled=True)
        self.pitch_angle_widget = widgets.Text(description="Attitude:", disabled=True)
        self.engine_rpm_widget = widgets.Text(description="Tachometer:", disabled=True)
        
        self.throttle_slider = widgets.FloatSlider(value=0, min=0, max=1, step=0.001, description='Throttle:', continuous_update=True, readout_format='.1%', 
                                                   orientation='vertical', layout=widgets.Layout(height='400px'))
        self.elevator_slider = widgets.FloatSlider(value=0, min=-16, max=16, step=0.1, description='Elevators:', continuous_update=True, readout_format='.1', 
                                                   orientation='vertical', layout=widgets.Layout(height='400px'))
    
        self.throttle_slider.observe(self.on_throttle_change, names='value')
        self.elevator_slider.observe(self.on_elevator_change, names='value')
        
        self.initiate_button.on_click(self.initiate_simulation)
        self.play_button.on_click(self.play_simulation)
        self.pause_button.on_click(self.pause_simulation)
        self.step_button.on_click(self.step_simulation)
        self.restart_button.on_click(self.restart_simulation)


        self.test_button.on_click(self.log_test)

        instruments = [self.timestep_widget, self.altitude_widget, self.distance_widget, self.airspeed_widget, self.vertical_speed_widget, self.pitch_angle_widget, self.engine_rpm_widget]

        for instrument in instruments :
            instrument.style.description_width = '120px'
            instrument.layout.width = '300px'
        
        self.grid = widgets.HBox([
            widgets.VBox([self.initiate_button, self.play_button, self.pause_button, self.step_button, self.restart_button, self.test_button]), 
            self.throttle_slider,
            self.elevator_slider,
            widgets.VBox(instruments),
            self.illustration.fig.canvas
        ])

        display(self.grid)        
    
    def update_display(self) :
        self.illustration.update(self.aircraft.pitch_angle_radians, self.aircraft.position[1], self.aircraft.stabilizer_angle_radians, self.aircraft.linear_velocity)        
        self.update_instruments()
    
    def step_simulation(self, frame):
        self.simulate_multiple_time_steps(self.aircraft, self.steps_per_iteration, self.delta_time)
        self.update_display()
    
    def initiate_simulation(self, input):  
        self.ani = animation.FuncAnimation(self.illustration.fig, self.step_simulation, frames=range(100), blit=False, interval=200, cache_frame_data=False, repeat=True)     
        self.pause_simulation(None)
        
        self.initiate_button.disabled = True
        self.play_button.disabled = False
        self.step_button.disabled = False
        self.restart_button.disabled = False     
    
    def play_simulation(self, input):
        self.update_display()
        self.ani.event_source.start()     

        self.play_button.disabled = False
        self.pause_button.disabled = False
        self.step_button.disabled = True
        self.restart_button.disabled = True
        
    def pause_simulation(self, input):
        self.ani.event_source.stop()  

        self.play_button.disabled = False
        self.pause_button.disabled = False
        self.step_button.disabled = False
        self.restart_button.disabled = False      
        
    def restart_simulation(self, input):
        self.aircraft = self.aircraft_model() # create a new plane of this model
        self.aircraft.time_elapsed = 0
        self.throttle_slider.value = self.aircraft.throttle
        self.elevator_slider.value = math.degrees(self.aircraft.stabilizer_angle_radians)
        self.update_display()  

    def log_test(self, input):
        default = self.aircraft_model() 
        attributes = []
        self.aircraft.time_elapsed = int(self.aircraft.time_elapsed * 1000) / 1000.0
        for attr in dir(self.aircraft) :
            if not attr.startswith('__') and getattr(self.aircraft, attr) != getattr(default, attr) :
                attributes.append(f'{attr}={getattr(self.aircraft, attr)}')
        with open('tests.txt', 'a') as file :
            print(f'{self.aircraft.__class__.__name__}({",".join(attributes)})', file=file)

    def on_throttle_change(self, change):
        self.aircraft.throttle = change['new']

    def on_elevator_change(self, change):
        self.aircraft.stabilizer_angle_radians = math.radians(change['new'])       

    def update_instruments(self) :
        self.timestep_widget.value = f"{self.aircraft.time_elapsed:0.3f} seconds"
        self.altitude_widget.value = f"{convert_to_feet(self.aircraft.position[1]):.0f} feet"
        self.distance_widget.value = f"{convert_to_nautical_miles(self.aircraft.position[0]):0.2f} nautical miles"
        self.airspeed_widget.value = f"{convert_to_knots(vector_magnitude(self.aircraft.linear_velocity)):.0f} knots"
        self.vertical_speed_widget.value = f"{60*convert_to_feet(self.aircraft.linear_velocity[1]):+.0f} feet per minute"
        self.pitch_angle_widget.value = f"{math.degrees(self.aircraft.pitch_angle_radians):+.0f} degrees"
        self.engine_rpm_widget.value = f"{self.aircraft.engine_rpm:.0f} rpm"    

def simulate(aircraft_model, simulate_multiple_time_steps, steps_per_iteration, delta_time) :
    sim = GUIFlightSimulator(aircraft_model, simulate_multiple_time_steps, steps_per_iteration, delta_time)