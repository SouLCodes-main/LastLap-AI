import pygame
import math
import os

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

def main():
    clock = pygame.time.Clock()
    running = True
    car = Car()
    score = 0
    high_score = 0
    game_over = False
    show_sensor = True

    # Load track mask or create a dummy track if "circuit.png" is missing
    if os.path.exists("circuit.png"):
        track_surface = pygame.image.load("circuit.png").convert()
        track_surface = pygame.transform.scale(
            track_surface,
            (WORLD_WIDTH, WORLD_HEIGHT),
        )
    else:
        track_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        track_surface.fill((0, 255, 0))
        pygame.draw.rect(
            track_surface,
            asphalt_color,
            (100, 100, WORLD_WIDTH - 200, WORLD_HEIGHT - 200),
            150,
        )

    display_scale = min(
        WINDOW_WIDTH / WORLD_WIDTH,
        WINDOW_HEIGHT / WORLD_HEIGHT,
    )
    track_display_size = (
        round(WORLD_WIDTH * display_scale),
        round(WORLD_HEIGHT * display_scale),
    )
    track_display = pygame.transform.scale(track_surface, track_display_size)
    offset_x = (WINDOW_WIDTH - track_display_size[0]) // 2
    offset_y = (WINDOW_HEIGHT - track_display_size[1]) // 2

    while running:
        dt = clock.tick(60) / 1000.0

        screen.fill(bg_color)
        screen.blit(track_display, (offset_x, offset_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    show_sensor = not show_sensor
                if event.key == pygame.K_r: # Manual restart key
                    car = Car()
                    game_over = False

        # iNPUT MANAGEMENT
        keys = pygame.key.get_pressed()
        throttle = 0
        brake = 0
        steer = 0

        if keys[pygame.K_w]: throttle = 1.0
        if keys[pygame.K_s]: brake = 1.0
        if keys[pygame.K_a]: steer = -1.0
        if keys[pygame.K_d]: steer = 1.0

        if not game_over:
            dist = car.step(throttle, brake, dt, steer)
            
            # Check center pixel for track boundary collisions
            cx, cy = int(car.x), int(car.y)
            if cx < 0 or cx >= WORLD_WIDTH or cy < 0 or cy >= WORLD_HEIGHT:
                game_over = True
            else:
                try:
                    if track_surface.get_at((cx, cy))[:3] != asphalt_color[:3]:
                        game_over = True
                except IndexError:
                    game_over = True

            if dist > 1.0:
                score += 1
                high_score = max(score, high_score)

        # Draw Car
        car.draw(screen, display_scale, offset_x, offset_y)

        # Draw Sensors
        if show_sensor and not game_over:
            for a in sensor_angles:
                d = cast_ray((car.x, car.y), car.angle + a, track_surface)
                
                # Calculate world coordinates
                end_world_x = car.x + math.cos(car.angle + a) * d
                end_world_y = car.y + math.sin(car.angle + a) * d
                
                start_screen = (
                    offset_x + car.x * display_scale,
                    offset_y + car.y * display_scale,
                )
                end_screen = (
                    offset_x + end_world_x * display_scale,
                    offset_y + end_world_y * display_scale,
                )
                
                pygame.draw.line(screen, sensor_color, start_screen, end_screen, 1)
                pygame.draw.circle(
                    screen,
                    sensor_color,
                    (int(end_screen[0]), int(end_screen[1])),
                    3,
                )

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()