import pygame
import math
import os
import neat
import pickle

pygame.init()

#--------------DISPLAY-----------------------------------------------------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
WORLD_WIDTH, WORLD_HEIGHT = 4000, 2251
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Last Lap - Model Testing")

#-----------VISUAL ELEMENTS & PARAMS---------------------------------------------------------
car_color = (255, 140, 0)
bg_color = (18, 18, 18)
sensor_color = (200, 200, 200)
asphalt_color = (0, 0, 0, 255)

car_w, car_h = 45, 20
max_speed = 250
max_accel = 600
brake_force = 4
friction = 200
max_steer_rate = math.radians(160)
steer_smoothing = 8

max_sensor_dist = 200
sensor_angles = [-math.pi/3, -math.pi/6, 0.0, math.pi/6, math.pi/3]
sensor_step = 5

#-----------HELPER FUNCTIONS & CLASSES--------------------------------------------------------
def cast_ray(origin, angle, track_surface):
    ox, oy = origin
    dx, dy = math.cos(angle), math.sin(angle)
    for d in range(0, max_sensor_dist, sensor_step):
        px = int(ox + dx * d)
        py = int(oy + dy * d)
        if px < 0 or px >= WORLD_WIDTH or py < 0 or py >= WORLD_HEIGHT:
            return d
        try:
            if track_surface.get_at((px, py))[:3] != asphalt_color[:3]:
                return d
        except IndexError:
            return d
    return max_sensor_dist

class Car:
    def __init__(self):
        self.x = 2600
        self.y = 1850
        self.angle = 0
        self.speed = 0
        self.angular_velocity = 0

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
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

    def draw(self, screen, display_scale, offset_x, offset_y):
        display_w = max(12, round(car_w * display_scale))
        display_h = max(8, round(car_h * display_scale))
        car_s = pygame.Surface((display_w, display_h), pygame.SRCALPHA)
        pygame.draw.rect(car_s, car_color, rect=(0, 0, display_w, display_h), border_radius=5)
        rotation = pygame.transform.rotate(car_s, -math.degrees(self.angle))
        car_rect = rotation.get_rect(
            center=(offset_x + self.x * display_scale, offset_y + self.y * display_scale)
        )
        screen.blit(rotation, car_rect)

def test_model(config_path, model_path, track_path):
    config = neat.config.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path
    )

    with open(model_path, "rb") as f:
        winner_genome = pickle.load(f)

    # Rebuild the network from the saved genome
    net = neat.nn.FeedForwardNetwork.create(winner_genome, config)
    car = Car()
    clock = pygame.time.Clock()

    if os.path.exists(track_path):
        track_surface = pygame.image.load(track_path).convert()
        track_surface = pygame.transform.scale(track_surface, (WORLD_WIDTH, WORLD_HEIGHT))
    else:
        print("Track image not found!")
        return

    display_scale = min(WINDOW_WIDTH / WORLD_WIDTH, WINDOW_HEIGHT / WORLD_HEIGHT)
    track_display_size = (round(WORLD_WIDTH * display_scale), round(WORLD_HEIGHT * display_scale))
    track_display = pygame.transform.scale(track_surface, track_display_size)
    offset_x = (WINDOW_WIDTH - track_display_size[0]) // 2
    offset_y = (WINDOW_HEIGHT - track_display_size[1]) // 2

    run = True
    while run:
        dt = clock.tick(60) / 1000.0
        screen.fill(bg_color)
        screen.blit(track_display, (offset_x, offset_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
        # 1. Get Sensor Data
        sensor_data = []
        for a in sensor_angles:
            d = cast_ray((car.x, car.y), car.angle + a, track_surface)
            sensor_data.append(d / max_sensor_dist)
            
            # Draw sensors dynamically
            end_world_x = car.x + math.cos(car.angle + a) * d
            end_world_y = car.y + math.sin(car.angle + a) * d
            start_screen = (offset_x + car.x * display_scale, offset_y + car.y * display_scale)
            end_screen = (offset_x + end_world_x * display_scale, offset_y + end_world_y * display_scale)
            pygame.draw.line(screen, sensor_color, start_screen, end_screen, 1)

        # 2. Get AI Output
        output = net.activate(sensor_data)
        throttle = 1.0 if output[0] > 0.5 else 0.0
        brake = 1.0 if output[1] > 0.5 else 0.0
        steer = 0.0
        if output[2] > 0.5: steer = -1.0
        if output[3] > 0.5: steer = 1.0

        car.step(throttle, brake, dt, steer)

        # 3. Check Collisions (reset car if it crashes)
        cx, cy = int(car.x), int(car.y)
        if cx < 0 or cx >= WORLD_WIDTH or cy < 0 or cy >= WORLD_HEIGHT:
            car = Car()
        else:
            try:
                if track_surface.get_at((cx, cy))[:3] != asphalt_color[:3]:
                    car = Car()
            except IndexError:
                car = Car()

        car.draw(screen, display_scale, offset_x, offset_y)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    model_path = os.path.join(local_dir, 'winner.pkl')
    track_path = os.path.join(local_dir, 'circuit.png')
    test_model(config_path, model_path, track_path)