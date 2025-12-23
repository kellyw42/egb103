from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap
import math
import enum
from IPython.display import display

class Direction(enum.IntEnum):
    REST = 0
    EAST = 1
    NORTH = 2
    WEST = 3
    SOUTH = 4
    NORTHEAST = 5
    NORTHWEST = 6
    SOUTHWEST = 7
    SOUTHEAST = 8

    def __str__(self) -> str:
        return self.name
        

def zoom_in(distribution):
    W = len(distribution)
    scale = (W-1)//8    
    return [row[scale:scale*3+1] for row in distribution[scale*2:scale*6+1]]


    
def setup_speed_plot(distribution, zoom, ax, colour_map):
    if zoom:
        distribution = zoom_in(distribution)

    W, H = len(distribution), len(distribution[0])
    scale = (W-1)//8

    quiver_scale = 6 / scale if scale > 0 else 1
    quiver_skip = scale // 5
    if quiver_skip < 1:
        quiver_skip = 1

    speed_grid, vx_grid, vy_grid = compute_speed_fields(distribution)

    im_speed = ax.imshow(speed_grid, cmap=colour_map, origin='lower', interpolation='nearest', extent=[0, W, 0, H], vmin=0, vmax=0.1)

    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Speed + Velocity Vectors (solids in black)")

    for x in range(W):
        for y in range(H):
            if distribution[x][y] is None:
                ax.add_patch(Rectangle((x, y), 1, 1, facecolor='black', edgecolor='black', linewidth=0.5))

    Xc, Yc, U0, V0 = [], [], [], []
    for y in range(0, H, quiver_skip):
        rowX, rowY, rowU, rowV = [], [], [], []
        for x in range(0, W, quiver_skip):
            rowX.append(x + 0.5)
            rowY.append(y + 0.5)
            rowU.append(vx_grid[y][x])
            rowV.append(vy_grid[y][x])

        Xc.append(rowX); Yc.append(rowY)
        U0.append(rowU); V0.append(rowV)

    quiver = ax.quiver(Xc, Yc, U0, V0, color='black', pivot='mid', width=0.002, angles='xy', scale_units='xy', scale=quiver_scale, headwidth=4, headlength=6)

    def update(new_distribution):
        if zoom:
            new_distribution = zoom_in(new_distribution)
                
        speed_grid, vx_grid, vy_grid  = compute_speed_fields(new_distribution)
        im_speed.set_data(speed_grid)
        im_speed.set_clim(vmin=0, vmax=0.1) # WAK WAK!!!

        U_ds, V_ds = [], []
        for y in range(0, H, quiver_skip):
            rowU, rowV = [], []
            for x in range(0, W, quiver_skip):
                rowU.append(vx_grid[y][x])
                rowV.append(vy_grid[y][x])

            U_ds.append(rowU)
            V_ds.append(rowV)
        quiver.set_UVC(U_ds, V_ds)

    return update


def compute_speed_fields(distribution):
    W, H = len(distribution), len(distribution[0])    
    speed_grid = [[0.0 for x in range(W)] for y in range(H)]
    vx_grid    = [[0.0 for x in range(W)] for y in range(H)]
    vy_grid    = [[0.0 for x in range(W)] for y in range(H)]

    for x in range(W):
        for y in range(H):
            cell = distribution[x][y]
            if cell is not None:
                vx, vy = compute_velocity(cell)
                speed = math.sqrt(vx*vx + vy*vy)
                speed_grid[y][x] = speed
                vx_grid[y][x]    = vx / speed if speed > 0 else 0 # normalized
                vy_grid[y][x]    = vy / speed if speed > 0 else 0 # normalized

    return speed_grid, vx_grid, vy_grid 


def animate(initial_distribution, fan_function, time_steps, fan_speed, relaxation_time, colour_map, zoom, figsize):
    update_speed = None
    
    def update(time_step, new_distribution):
        nonlocal update_speed
        if time_step == 1:
            update_speed = setup_speed_plot(new_distribution, zoom, ax_s, colour_map) 

        update_speed(new_distribution)
        
        ax_s.set_title(f"Time Step {time_step}")

        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        handle.update(fig)

    plt.ioff()
    fig, (ax_s) = plt.subplots(1, 1, figsize=figsize)
    fig.canvas.toolbar_visible = False
    fig.canvas.header_visible = False
    fig.canvas.footer_visible = False

    handle = display(fig, display_id=True)
    
    simulate(initial_distribution, fan_function, fan_speed, relaxation_time, time_steps, update)


def block1(W):
    s = W/8
    def obstacle(x, y):
        return 0 <= y < 2*s and 3*s <= x < 5*s  
    return obstacle


def block2(W):
    s = W/8
    def obstacle(x, y):
        return s <= y < 3*s and 3*s <= x < 5*s  
    return obstacle


def circle(W):
    s = W/8
    centre_x = 4*s
    centre_y = 2*s
    def obstacle(x, y):
        return (x-centre_x)*(x-centre_x) + (y-centre_y)*(y-centre_y) <= s*s
    return obstacle


def image_model(image_name):
    def scaled_image(W):
        img = Image.open(image_name)
        H = W//2
        img_resized = img.resize((W, H), Image.BILINEAR)
        img_g = img_resized.convert("L")
        img_bw = img_g.point(lambda v: 0 if v < 128 else 255, mode="1")
    
        def obstacle_function(x, y):
            if 0 <= x < W and 0 <= y < H:
                return img_bw.getpixel((x,H-y)) == 0
            else:
                return False
            
        return obstacle_function
    return scaled_image


def is_outside_circle(x, y, centre_x, centre_y, radius):
    return math.hypot(x - centre_x, y - centre_y) > radius 

    
def in_manifold(x, y, scale):
    if x < scale:
        if y < scale * 2:
            if is_outside_circle(x, y, 1*scale, 1*scale, scale):
                return True
        else:
            if is_outside_circle(x, y, 1*scale, 3*scale, scale):
                return True
    elif x >= scale * 7:
        if y < scale * 2:
            if is_outside_circle(x, y, 7*scale, 1*scale, scale):            
                return True
        else:
            if is_outside_circle(x, y, 7*scale, 3*scale, scale):   
                return True
    return False


def create_wind_tunnel(scale, scalable_model):
# provided    
    width = 8*scale + 1
    height = 4*scale + 1
    
    model = scalable_model(4*scale) if scalable_model else None
    
    def is_fan_cell(x, y):
        return x == 2*scale and (scale < y < 3*scale)
    
    def is_obstacle_cell(x, y):
        # outside the boundary
        if not (0 <= x < width and 0 <= y < height): 
            return True

        # wind tunnel floor and ceiling
        if (y == scale or y == 3*scale) and (2*scale <= x <= 6*scale): 
            return True
    
        if in_manifold(x, y, scale):
            return True
        else:
            if model:
                return model(x-2*scale, y-scale)
            else:
                return False

    return width, height, is_fan_cell, is_obstacle_cell

def initialize_distribution(width, height, obstacle_function, pressure=1.0):
    distribution = []
    for x in range(width):
        column = []
        for y in range(height):
            if obstacle_function(x, y):
                column.append(None)
            else:
                cell = []
                for direction in Direction:
                    cell.append(zero_velocity_equilibrium(direction) * pressure)
                column.append(cell)
        distribution.append(column)
    return distribution


def create_from_scaled_model(scale, scalable_model):
# provided    
    width, height, is_fan_cell_function, obstacles = create_wind_tunnel(scale, scalable_model)
    initial_distribution = initialize_distribution(width, height, obstacles)  
    return initial_distribution, is_fan_cell_function


def create_animator(compute_velocity_function, zero_velocity_equilibrium_function, simulate_function, working, colour_map, figsize):
    global compute_velocity, zero_velocity_equilibrium, simulate
    compute_velocity = compute_velocity_function
    zero_velocity_equilibrium = zero_velocity_equilibrium_function
    simulate = simulate_function

    def animate_scaled_model(scale, scalable_model, time_steps, zoom, fan_speed, relaxation_time):
        initial_distribution, is_fan_cell_function = create_from_scaled_model(scale, scalable_model)
        animate(initial_distribution, is_fan_cell_function, zoom=zoom, time_steps=time_steps, fan_speed=fan_speed, relaxation_time=relaxation_time, colour_map=colour_map, figsize=figsize) 

    def not_working(scale, scalable_model, time_steps, zoom, fan_speed, relaxation_time):
        print('You need function simulate to be working correctly before trying to create an animated simulation.')
    
    if working:   
        print('Animator successfully created')
        return animate_scaled_model
    else:
        print('You need function simulate to be working correctly before trying to create an animated simulation.')
        return not_working