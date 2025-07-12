import pool_table
import time
import code_analyser
import math
import ipywidgets as widgets
from PIL import Image, ImageDraw, ImageFont

PIXELS_PER_METRE = 400 # pixels per metre
LARGER_SCALE = 4

class GUIPoolSimulator:

    def strike(self, event):
        self.strike_button.disabled = True
        self.retry_button.disable = True
        self.replay_button.disable = True
        
        max_power = 5
        time_delta =  0.01
        
        # set velocity of cue ball based on aim angle and power
        self.balls[0].velocity_x = math.cos(self.aim_angle()) * self.power.value * max_power
        self.balls[0].velocity_y = math.sin(self.aim_angle()) * self.power.value * max_power

        self.frames = self.create_animation(self.balls, time_delta)
        self.animate()
        if self.balls[0].ball_number != 0:
            self.replace_cue_ball()
        self.display_aim_line()
        
        self.restart_button.disabled = False
        self.strike_button.disabled = False
        self.retry_button.disabled = False
        self.replay_button.disabled = False

    def aim_angle(self):
        return self.angle.value * 2 * math.pi / 4000
    
    def scaler(self, super_sampling = 1):
        scale = PIXELS_PER_METRE * super_sampling 
        border = 0.08 * scale
        def scale_points(*points):
            return tuple(border + point * scale for point in points)
        return scale_points

    def refresh_image(self):
        self.image_widget.value = self.image._repr_png_()
        self.image_widget.width = self.image.width
        self.image_widget.height = self.image.height

    def animate(self):
        for frame in self.frames: # Only display every 10th frame when playing at regular speed
            self.draw_table(frame, 1) # Don't do super sampling during animation to improve performance
        # once animation is finished, redraw final frame using higher resolution.
        self.draw_table(self.frames[-1], LARGER_SCALE)

    def display_aim_line(self):
        angle = self.aim_angle()
        scale_points = self.scaler(LARGER_SCALE)
        large_copy = self.large_image.copy()
        draw = ImageDraw.Draw(large_copy)
        cue_ball = self.balls[0]
        draw.line(scale_points(cue_ball.centre_position_x, cue_ball.centre_position_y, 
                               cue_ball.centre_position_x + math.cos(angle)*1000, cue_ball.centre_position_y + math.sin(angle)*1000),
                  fill='red', width=LARGER_SCALE)
        self.image = large_copy.resize((int(self.large_image.width/LARGER_SCALE), int(self.large_image.height/LARGER_SCALE)), Image.LANCZOS)
        self.refresh_image()

    def aim_angle_changed(self, event):
        self.display_aim_line()

    def overlaps_other_balls(self, centre_position_x, centre_position_y):
        for other_ball in self.balls:
            if (centre_position_x - other_ball.centre_position_x)**2 + (centre_position_y - other_ball.centre_position_y)**2 <= self.Ball.diameter**2:
                return True
        return False
    
    def restart(self, event):
        self.restart_button.disabled = True
        self.replay_button.disabled = True
        self.retry_button.disable = True
        self.balls = pool_table.init_table_rack_balls(self.Ball)
        self.draw_table(pool_table.create_frame(self.balls), LARGER_SCALE)
        self.angle.value = 0
        self.power.value = 1
        self.display_aim_line()
    
    def replace_cue_ball(self):
        centre_position_x, centre_position_y = (pool_table.TABLE_WIDTH * 0.2, pool_table.TABLE_HEIGHT * 0.5)
        while self.overlaps_other_balls(centre_position_x, centre_position_y):
            centre_position_x -= 0.01
        self.balls.insert(0, self.Ball(0, centre_position_x, centre_position_y))
        self.draw_table(pool_table.create_frame(self.balls), LARGER_SCALE)

    def replay(self, event):
        self.strike_button.disabled = True
        self.retry_button.disable = True
        self.replay_button.disable = True
        self.animate()
        self.display_aim_line()
        self.restart_button.disabled = False
        self.strike_button.disabled = False
        self.retry_button.disabled = False
        self.replay_button.disabled = False

    def retry(self, event):
        self.balls.clear()
        for (ball_number, centre_position_x, centre_position_y) in self.frames[0]:
            self.balls.append(self.Ball(ball_number, centre_position_x, centre_position_y))
        self.draw_table(pool_table.create_frame(self.balls), LARGER_SCALE)
        self.display_aim_line()

    ball_colors = [ (255,255,255), (255,255,0), (0,0,153), (200,0,0), (102,0,102), (255,102,0), (0,153,0), (153,0,51), 
                    (0,0,0), (255,255,0), (0,0,153), (200,0,0), (102,0,102), (255,102,0), (0,153,0), (153,0,51)]

    def draw_table(self, frame, super_sampling = 1):
        scale = PIXELS_PER_METRE * super_sampling
        font = ImageFont.load_default(13 * super_sampling)
        border = 0.08 * scale
        image_width  = int(pool_table.TABLE_WIDTH * scale + 2 * border)
        image_height = int(pool_table.TABLE_HEIGHT * scale + 2 * border)
        scale_points = self.scaler(super_sampling)
        self.large_image = Image.new('RGB', (image_width, image_height), 'white')
        draw = ImageDraw.Draw(self.large_image)
        border_colour = "#4c3525"
        # draw borders
        draw.line((border, border/2, image_width-border, border/2), fill=border_colour, width=int(border))
        draw.line((border, image_height - border/2, image_width-border, image_height - border/2), fill=border_colour, width=int(border))
        draw.line((border/2, border, border/2, image_height-border), fill=border_colour, width=int(border))
        draw.line((image_width - border/2, border, image_width - border/2, image_height-border), fill=border_colour, width=int(border))
        # draw corner of borders
        draw.ellipse((0, 0, 2*border, 2*border), fill=border_colour)
        draw.ellipse((image_width-2*border, 0, image_width, 2*border), fill=border_colour)
        draw.ellipse((0, image_height-2*border, 2*border, image_height), fill=border_colour)
        draw.ellipse((image_width-2*border, image_height-2*border, image_width, image_height), fill=border_colour)
        # draw green cloth
        draw.rectangle(scale_points(0, 0, pool_table.TABLE_WIDTH, pool_table.TABLE_HEIGHT), fill='green')
        # draw pockets
        for pocket in pool_table.POCKETS:
            draw.ellipse(scale_points(pocket.centre_x-pocket.radius, pocket.centre_y-pocket.radius,
                                      pocket.centre_x+pocket.radius, pocket.centre_y+pocket.radius), 
                         fill=(50,50,50))
        # draw balls
        for ball_number,ball_centre_position_x, ball_centre_position_y in frame:
            draw.ellipse(scale_points(ball_centre_position_x-self.Ball.radius, ball_centre_position_y-self.Ball.radius,
                                      ball_centre_position_x+self.Ball.radius, ball_centre_position_y+self.Ball.radius),
                         fill=self.ball_colors[ball_number%16])
            darkness = sum(self.ball_colors[ball_number%16])/3
            w = len(str(ball_number))
            if ball_number:
                draw.text(scale_points(ball_centre_position_x - (self.Ball.radius*0.85 if w > 1 else self.Ball.radius*0.4), ball_centre_position_y - self.Ball.radius*0.75),
                          str(ball_number), 'white' if darkness < 128 else 'black', font)
        if super_sampling == 1:
            self.image = self.large_image
        else:
            self.image = self.large_image.resize((int(image_width/super_sampling), int(image_height/super_sampling)), Image.LANCZOS)
        self.refresh_image()

    def create_gui(self):
        self.image_widget = widgets.Image()
        self.angle = widgets.IntSlider(value= 0, min=-4000, max=4000, description='Aim Angle:', readout=False)
        self.angle.layout.width = '100%'
        self.angle.observe(self.aim_angle_changed, names='value')
        self.power = widgets.FloatSlider(value=1, min=0.01, max=1, step=0.01, description='Power:',  readout_format='.0%')
        self.power.layout.width = '100%'
        self.restart_button = widgets.Button(description="Restart Game", disabled=True)
        self.restart_button.on_click(self.restart)    
        self.strike_button = widgets.Button(description="Shoot")
        self.strike_button.on_click(self.strike)
        self.replay_button = widgets.Button(description="Replay Shot", disabled=True)
        self.replay_button.on_click(self.replay)
        self.retry_button = widgets.Button(description="Retry Shot", disabled=True)
        self.retry_button.on_click(self.retry)
        display(widgets.VBox([self.angle, self.power, widgets.HBox([self.restart_button, self.strike_button, self.replay_button, self.retry_button]), self.image_widget]))

def play(create_animation, Ball):
    if code_analyser.all_correct:
        gui = GUIPoolSimulator()
        gui.create_animation = create_animation
        gui.Ball = Ball
        gui.create_gui()
        gui.restart(None)
    else:
        print("Sorry, you can't play until all of your functions are working correctly.")

def show(balls, Ball):
    gui = GUIPoolSimulator()
    gui.Ball = Ball
    gui.balls = balls
    gui.create_gui()
    gui.draw_table(pool_table.create_frame(balls), LARGER_SCALE)