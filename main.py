import pygame
import math

pygame.init()

#--------------DISPLAY-----------------------------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 4000, 3000
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Last Lap")

#-----------VISUAL ELEMENTS------------------------------------------------------------------
car_color = (0, 200, 0)
bg_color = (18, 18, 18)
panel_bg = (40, 40, 40)
sensor_color = (200, 200, 200)
obst_color = (255, 60, 60)

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
def point_to_segment_dist(px, py, ax, ay, bx, by):
    vx, vy = px - ax, py - ay
    ux, uy = bx -ax, by - ay
    seg_len2 = ux*ux + uy*uy

    # If the segment is just a point
    if seg_len2 == 0:
        return math.hypot(vx, vy)

    t = max(0.0, min(1.0, (vx*ux + vy*uy) / seg_len2))
    projx = ax + t * ux
    projy = ay + t * uy
    return math.hypot(px-projx, py-projy)

def cast_ray(origin, angle, obstacle):
    ox, oy = origin
    dx, dy = math.cos(angle), math.sin(angle)

    for d in range(0, max_sensor_dist, sensor_step):
        px = ox + dx * d
        py = oy + dy * d

        if px < 0 or px > SCREEN_WIDTH or py < 0 or py > SCREEN_HEIGHT:
            return d
        for i in range(0, len(obstacle) - 1, 2):
            if point_to_segment_dist(px, py, obstacle[i][0], obstacle[i][1],obstacle[i+1][0], obstacle[i+1][1]) < 2:
                return d

    return max_sensor_dist # no collision  

class Car:
    def __init__(self):
        self.x = car_w
        self.y = car_h
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
 
    def draw(self, screen):
        car_s = pygame.Surface((car_w, car_h), pygame.SRCALPHA)
        pygame.draw.rect(car_s, car_color, rect=(0, 0, car_w, car_h), border_radius=5)
        rotation = pygame.transform.rotate(car_s, -math.degrees(self.angle))
        car_rect = rotation.get_rect(center=(self.x, self.y))
        screen.blit(rotation, car_rect)

def main():
    clock = pygame.time.Clock()
    running = True
    car = Car()
    score = 0
    high_score = 0
    game_over = False
    show_sensor = True
    obstacles = []

    while running:
        dt = clock.tick(60) / 1000.0
        screen.fill(bg_color)
        pygame.draw.rect(
            screen,
            panel_bg,
            rect=(0, SCREEN_HEIGHT - 120, SCREEN_WIDTH, 120),
        )
        car.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    show_sensor = not show_sensor

        # iNPUT MANAGEMENT
        keys = pygame.key.get_pressed()
        throttle = 0
        brake = 0
        steer = 0

        if keys[pygame.K_w]:
            throttle = 1.0
        if keys[pygame.K_s]:
            brake = 1.0
        if keys[pygame.K_a]:
            steer = -1.0
        if keys[pygame.K_d]:
         steer = 1.0

        if not game_over:
            dist = car.step(throttle, brake, dt, steer)

            if dist > 1.0:
                score += 1
                high_score = max(score, high_score)

        # Draw Sensor
        if show_sensor and not game_over:
            for a in sensor_angles:
                d = cast_ray((car.x, car.y), car.angle + a, obstacles)
                end_x = car.x + math.cos(car.angle + a) * d
                end_y = car.y + math.sin(car.angle + a) * d
                pygame.draw.line(screen, sensor_color, (car.x, car.y), (end_x, end_y), 1)
                pygame.draw.circle(
                    screen,
                    sensor_color,
                    (int(end_x), int(end_y)),
                    3,
                )


        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
