import pygame
import math

pygame.init()

#--------------DISPLAY-------------------------------------
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Last Lap")

#-----------VISUAL ELEMENTS--------------------------------
car_color = (0, 200, 0)
bg_color = (18, 18, 18)
panel_bg = (40, 40, 40)
sensor_color = (200, 200, 200)
obst_color = (255, 60, 60)

# ----------CAR PARAMETERS---------------------------------
car_w, car_h = 45, 20
max_speed = 250
max_accel = 600
brake_force = 4
friction = 200
max_steer_rate = math.radians(160)
steer_smoothing = 8

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

    while running:
        dt = clock.tick(60) / 1000.0
        screen.fill(bg_color)
        pygame.draw.rect(screen, panel_bg, rect=(0, 600, 800, 120))
        car.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
