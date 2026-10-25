import pygame
import math
import os
import neat

pygame.init()

#--------------DISPLAY-----------------------------------------------------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
WORLD_WIDTH, WORLD_HEIGHT = 4000, 2251
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Last Lap")

#-----------VISUAL ELEMENTS------------------------------------------------------------------
car_color = (255, 140, 0) #
bg_color = (18, 18, 18)
sensor_color = (200, 200, 200)
asphalt_color = (0, 0, 0, 255) # Strict black for the track path

# ----------CAR PARAMETERS-------------------------------------------------------------------
car_w, car_h = 45, 20
max_speed = 250
max_accel = 600
brake_force = 4
friction = 200
max_steer_rate = math.radians(160)
steer_smoothing = 8

#-----------SENSOR PARAMS---------------------------------------------------------------------
max_sensor_dist = 200
sensor_angles = [-math.pi/3, -math.pi/6, 0.0, math.pi/6, math.pi/3]
sensor_step = 5
MAX_EVALUATION_TIME = 30.0

#-----------HELPER FUNCTIONS------------------------------------------------------------------
def cast_ray(origin, angle, track_surface):
    ox, oy = origin
    dx, dy = math.cos(angle), math.sin(angle)

    for d in range(0, max_sensor_dist, sensor_step):
        px = int(ox + dx * d)
        py = int(oy + dy * d)

        # Stop if ray hits the world boundaries
        if px < 0 or px >= WORLD_WIDTH or py < 0 or py >= WORLD_HEIGHT:
            return d
            
        # Stop if pixel is not the asphalt color (it hit grass/wall)
        try:
            if track_surface.get_at((px, py))[:3] != asphalt_color[:3]:
                return d
        except IndexError:
            return d

    return max_sensor_dist

class Car:
    def __init__(self):
        self.x = 2800
        self.y = 1800
        self.angle = 0
        self.speed = 0
        self.angular_velocity = 0

    #-------------PHYSICS ENGINE (CHOTA SA)------------------
    def step(self, throttle, brake, dt, steer):
        accel = throttle * max_accel
        decel = brake * brake_force * max_accel
        self.speed += (accel - decel) * dt

        if throttle < 0.1:
            self.speed -= friction * dt
            steer = 0

        self.speed = max(0, min(max_speed, self.speed))
        if throttle > 0 and brake > 0:
            steer = 0
            self.angular_velocity = 0

        target_av = steer * max_steer_rate
        self.angular_velocity += (target_av - self.angular_velocity) * min(1.0, steer_smoothing * dt)
        self.angle += self.angular_velocity * dt

        prev_x, prev_y = self.x, self.y
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

        dist = math.hypot(self.x-prev_x, self.y-prev_y)
        return dist
 
    def draw(self, screen, display_scale, offset_x, offset_y):
        display_w = max(12, round(car_w * display_scale))
        display_h = max(8, round(car_h * display_scale))
        car_s = pygame.Surface((display_w, display_h), pygame.SRCALPHA)
        pygame.draw.rect(car_s, car_color, rect=(0, 0, display_w, display_h), border_radius=5)
        rotation = pygame.transform.rotate(car_s, -math.degrees(self.angle))
        car_rect = rotation.get_rect(
            center=(
                offset_x + self.x * display_scale,
                offset_y + self.y * display_scale,
            )
        )
        screen.blit(rotation, car_rect)

def eval_genomes(genomes, config):
    nets = []
    cars = []
    ge = []

    # Initialize population
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        cars.append(Car())
        ge.append(genome)

    clock = pygame.time.Clock()
    
    # Load track mask (Keep your existing track loading logic here)
    if os.path.exists("circuit.png"):
        track_surface = pygame.image.load("circuit.png").convert()
        track_surface = pygame.transform.scale(track_surface, (WORLD_WIDTH, WORLD_HEIGHT))
    else:
        track_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        track_surface.fill((0, 255, 0))
        pygame.draw.rect(track_surface, asphalt_color, (100, 100, WORLD_WIDTH - 200, WORLD_HEIGHT - 200), 150)

    display_scale = min(WINDOW_WIDTH / WORLD_WIDTH, WINDOW_HEIGHT / WORLD_HEIGHT)
    track_display_size = (round(WORLD_WIDTH * display_scale), round(WORLD_HEIGHT * display_scale))
    track_display = pygame.transform.scale(track_surface, track_display_size)
    offset_x = (WINDOW_WIDTH - track_display_size[0]) // 2
    offset_y = (WINDOW_HEIGHT - track_display_size[1]) // 2

    run = True
    elapsed_time = 0.0
    while run and cars and elapsed_time < MAX_EVALUATION_TIME:
        dt = clock.tick(60) / 1000.0
        elapsed_time += dt
        screen.fill(bg_color)
        screen.blit(track_display, (offset_x, offset_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        cars_to_remove = []

        for i, car in enumerate(cars):
            # 1. Get Sensor Data
            sensor_data = []
            for a in sensor_angles:
                d = cast_ray((car.x, car.y), car.angle + a, track_surface)
                # Normalize distances between 0.0 and 1.0 for the neural network
                sensor_data.append(d / max_sensor_dist) 

            # 2. Get AI Output
            output = nets[i].activate(sensor_data)

            # Map 4 output nodes to Throttle, Brake, Left, Right
            throttle = 1.0 if output[0] > 0.5 else 0.0
            brake = 1.0 if output[1] > 0.5 else 0.0
            steer = 0.0
            if output[2] > 0.5: steer = -1.0
            if output[3] > 0.5: steer = 1.0

            dist = car.step(throttle, brake, dt, steer)

            # 3. Check Collisions
            cx, cy = int(car.x), int(car.y)
            crashed = False
            if cx < 0 or cx >= WORLD_WIDTH or cy < 0 or cy >= WORLD_HEIGHT:
                crashed = True
            else:
                try:
                    if track_surface.get_at((cx, cy))[:3] != asphalt_color[:3]:
                        crashed = True
                except IndexError:
                    crashed = True

            # 4. Update Fitness & Remove Crashed Cars
            if crashed:
                ge[i].fitness -= 1.0 # Slight penalty for crashing
                cars_to_remove.append(i)
            else:
                ge[i].fitness += dist / 10.0 # Reward for distance driven
                car.draw(screen, display_scale, offset_x, offset_y)

        # Remove cars safely in reverse order to prevent indexing errors
        for i in reversed(cars_to_remove):
            cars.pop(i)
            nets.pop(i)
            ge.pop(i)

        pygame.display.flip()

def run_neat(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )
    
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run for up to 50 generations
    winner = p.run(eval_genomes, 50)
    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run_neat(config_path)