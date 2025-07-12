import math

class Pocket:
    radius =  0.051

    def __init__(pocket, name, centre_x, centre_y):
        pocket.name = name
        pocket.centre_x = centre_x
        pocket.centre_y = centre_y

    def __repr__(pocket):
        return f'Pocket({pocket.name})'      
    
    def gap_to_ball_at_future_time(pocket, ball_centre_position_x, ball_centre_position_y, future_time):
        return math.hypot(pocket.centre_x - ball_centre_position_x, pocket.centre_y - ball_centre_position_y) - Pocket.radius

    def relative_speed(pocket, ball):
        # Fixme!!!!!
        return -1

    def event_horizon(pocket, ball_rolling_time):
        return ball_rolling_time

    def resolve_collision(pocket, ball, balls):
        balls.remove(ball)

TABLE_WIDTH, TABLE_HEIGHT = 2.44, 1.22
POCKETS = [Pocket('Top Left Corner',0,0), Pocket('Top Side', TABLE_WIDTH/2, -0.02), Pocket('Bottom Left Corner', 0, TABLE_HEIGHT), Pocket('Top Right Corner', TABLE_WIDTH, 0), Pocket('Bottom Side', TABLE_WIDTH/2, TABLE_HEIGHT+0.02), Pocket('Bottom Right Corner', TABLE_WIDTH, TABLE_HEIGHT)]


def init_table_rack_balls(Ball):
    balls = []
    balls.append(Ball(0, TABLE_WIDTH * 0.2, TABLE_HEIGHT * 0.5)) # Cue ball
    rows = 5
    apex_x, apex_y = TABLE_WIDTH * 0.75, TABLE_HEIGHT * 0.5
    ball_number = 1
    for row in range(rows):
        for column in range(row + 1):
            ball_centre_x = apex_x + row * Ball.radius * math.sqrt(3)
            ball_centre_y = apex_y + (column - row / 2) * 2 * Ball.radius
            balls.append(Ball(ball_number, ball_centre_x, ball_centre_y))
            ball_number += 1
    return balls


def is_in_pocket(ball_centre_x, ball_centre_y, pocket):
    (pocket_centre_x, pocket_centre_y) = pocket
    return (ball_centre_x - pocket_centre_x)**2 + (ball_centre_y - pocket_centre_y)**2 <= (2*POCKET_RADIUS)**2


def detect_pocket_collision(ball):
    collisions = []
    for (pocket_centre_x, pocket_centre_y) in POCKETS:
        if (ball.centre_position_x - pocket_centre_x)**2 + (ball.centre_position_y - pocket_centre_y)**2 < POCKET_RADIUS**2:
            collisions.append((ball, (pocket_centre_x, pocket_centre_y)))
            break
    return collisions


def create_frame(balls):
    frame = []
    for ball in balls:
        frame.append((ball.ball_number, ball.centre_position_x, ball.centre_position_y))
    return frame


# TODO: remove this
def too_close(ball1, ball2):
    dist = math.sqrt((ball1.centre_position_x - ball2.centre_position_x)**2 + (ball1.centre_position_y - ball2.centre_position_y)**2)
    assert(dist > 0.99 * ball1.diameter)