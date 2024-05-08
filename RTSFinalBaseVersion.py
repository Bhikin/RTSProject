import pygame
import sys
import random
import time
import math

# Initialize Pygame
pygame.init()

# Set screen dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))

# Colors
LIGHT_BLUE = (173, 216, 230)  # Low-saturated blue
WAVE_COLOR = (200, 220, 255)  # Very light blue for waves
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)  # Green for message indicator
ARROW_COLOR = (0, 0, 0)  # Black for arrows
BUTTON_COLOR = (150, 150, 150)
BUTTON_HOVER_COLOR = (200, 200, 200)
BUTTON_TEXT_COLOR = (0, 0, 0)

# Font for the timer display and button
font = pygame.font.Font(None, 36)
button_font = pygame.font.Font(None, 48)

# Boat properties
boat1_pos = [width // 2, 50]
boat2_pos = [width // 2, height - 50]
boat1_received_pos = list(boat2_pos)
boat2_received_pos = list(boat1_pos)
last_boat1_pos = list(boat2_pos)
last_boat2_pos = list(boat1_pos)
boat_speed = 0.2
boat_size = 15

# Wind properties
wind_speed = 0.45
wind_active = False
wind_duration = 0
wind_start_time = 0
wind_rect = None
wind_direction = (1, 0)  # Initial direction

# Button properties
button_width, button_height = 200, 50
button_off_rect = pygame.Rect((width - button_width) // 2 - 110, (height - button_height) // 2, button_width, button_height)
button_on_rect = pygame.Rect((width + button_width) // 2 - 90, (height - button_height) // 2, button_width, button_height)
button_off_text = button_font.render("Rollback: Off", True, BUTTON_TEXT_COLOR)
button_on_text = button_font.render("Rollback: On", True, BUTTON_TEXT_COLOR)
rollback_enabled = False
button_clicked = False

# Network properties
communication_interval = 1
network_stable_time = time.time()
network_outage = False
outage_start_time = 0
outage_duration = 0
last_communication_time = time.time()

# Timer and other properties
start_time = pygame.time.get_ticks()
timer_running = False
boats_meet = False
indicator_duration = 1
waves = []
wave_speed = 1.5
wave_lifespan = 10
boat1_indicator_time = 0
boat2_indicator_time = 0
boat1_in_wind = False
boat2_in_wind = False
boat1_in_wave = False
boat2_in_wave = False

# Function to draw the start buttons
def draw_buttons():
    mouse_pos = pygame.mouse.get_pos()
    if button_off_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR, button_off_rect)
    else:
        pygame.draw.rect(screen, BUTTON_COLOR, button_off_rect)
    if button_on_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR, button_on_rect)
    else:
        pygame.draw.rect(screen, BUTTON_COLOR, button_on_rect)
    screen.blit(button_off_text, (button_off_rect.x + (button_width - button_off_text.get_width()) // 2,
                              button_off_rect.y + (button_height - button_off_text.get_height()) // 2))
    screen.blit(button_on_text, (button_on_rect.x + (button_width - button_on_text.get_width()) // 2,
                              button_on_rect.y + (button_height - button_on_text.get_height()) // 2))

# Function to draw a rotated triangle
def draw_rotated_triangle(screen, color, position, angle):
    x, y = position
    angle_rad = math.radians(angle)
    points = [
        (x + math.cos(angle_rad) * boat_size, y + math.sin(angle_rad) * boat_size),
        (x + math.cos(angle_rad + 2 * math.pi / 3) * boat_size, y + math.sin(angle_rad + 2 * math.pi / 3) * boat_size),
        (x + math.cos(angle_rad + 4 * math.pi / 3) * boat_size, y + math.sin(angle_rad + 4 * math.pi / 3) * boat_size)
    ]
    pygame.draw.polygon(screen, color, points)

# Function to draw a hollow triangle (outline only)
def draw_hollow_triangle(screen, color, position, angle):
    x, y = position
    angle_rad = math.radians(angle)
    points = [
        (x + math.cos(angle_rad) * boat_size, y + math.sin(angle_rad) * boat_size),
        (x + math.cos(angle_rad + 2 * math.pi / 3) * boat_size, y + math.sin(angle_rad + 2 * math.pi / 3) * boat_size),
        (x + math.cos(angle_rad + 4 * math.pi / 3) * boat_size, y + math.sin(angle_rad + 4 * math.pi / 3) * boat_size)
    ]
    pygame.draw.polygon(screen, color, points, 1)

# Function to draw waves
def draw_wave(screen, x, y, width, height):
    pygame.draw.rect(screen, WAVE_COLOR, (x, y, width, height))

# Function to draw an arrow
def draw_arrow(screen, start, direction, length=30):
    angle = math.atan2(direction[1], direction[0])
    end = (start[0] + math.cos(angle) * length, start[1] + math.sin(angle) * length)
    pygame.draw.line(screen, ARROW_COLOR, start, end, 2)
    arrow_size = 8
    points = [
        (end[0], end[1]),
        (end[0] - arrow_size * math.cos(angle - math.pi / 6), end[1] - arrow_size * math.sin(angle - math.pi / 6)),
        (end[0] - arrow_size * math.cos(angle + math.pi / 6), end[1] - arrow_size * math.sin(angle + math.pi / 6))
    ]
    pygame.draw.polygon(screen, ARROW_COLOR, points)

# Function to draw a solid rectangle with optional transparency
def draw_solid_rectangle(screen, rect, color, alpha=None):
    surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    if alpha:
        surface.set_alpha(alpha)
    pygame.draw.rect(surface, color, surface.get_rect())
    screen.blit(surface, (rect.x, rect.y))

# Communication function
def communicate():
    global boat1_received_pos, boat2_received_pos, boat1_indicator_time, boat2_indicator_time, last_boat1_pos, last_boat2_pos, boat1_in_wind, boat2_in_wind, boat1_in_wave, boat2_in_wave
    if not network_outage:
        last_boat1_pos = list(boat2_pos)
        last_boat2_pos = list(boat1_pos)
        boat1_received_pos = list(boat2_pos)  # boat1 receives boat2's current position
        boat2_received_pos = list(boat1_pos)  # boat2 receives boat1's current position
        #print(f"Rollback Mode: {rollback_enabled}, Boat1 in Wind: {boat1_in_wind}, Boat1 in Wave: {boat1_in_wave}")
        boat1_indicator_time = time.time()  # Show indicator for boat1
        boat2_indicator_time = time.time()  # Show indicator for boat2

# Function to get random direction
def get_random_direction():
    directions = [
        (-1, 0),  # Left
        (1, 0),   # Right
        (0, -1),  # Up
        (0, 1),   # Down
        (-1, -1), # Up-left
        (-1, 1),  # Down-left
        (1, -1),  # Up-right
        (1, 1)    # Down-right
    ]
    return random.choice(directions)

# Function to get the direction of the closest wave within 100 pixels
def get_closest_wave_direction(wave_x, wave_y):
    closest_direction = None
    min_distance = float('inf')
    for wave in waves:
        wx, wy, _, _, _, direction = wave
        distance = math.sqrt((wave_x - wx) ** 2 + (wave_y - wy) ** 2)
        if distance <= 100 and distance < min_distance:
            closest_direction = direction
            min_distance = distance
    return closest_direction

# Normalize boat movement so diagonal movement is not faster
def normalize_movement(dx, dy, speed):
    distance = math.sqrt(dx ** 2 + dy ** 2)
    if distance == 0:
        return 0, 0
    scale = speed / distance
    return dx * scale, dy * scale

# Main game loop
running = True
while running:
    screen.fill(LIGHT_BLUE)
    
    if not button_clicked:
        draw_buttons()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_off_rect.collidepoint(event.pos):
                    rollback_enabled = False
                    button_clicked = True
                    start_time = pygame.time.get_ticks()
                    timer_running = True
                elif button_on_rect.collidepoint(event.pos):
                    rollback_enabled = True
                    button_clicked = True
                    start_time = pygame.time.get_ticks()
                    timer_running = True

        pygame.display.flip()
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    if not network_outage:
        if current_time - network_stable_time >= random.randint(6, 10):
            network_outage = True
            outage_start_time = current_time
            outage_duration = random.randint(6, 10)
    else:
        if current_time - outage_start_time >= outage_duration:
            network_outage = False
            network_stable_time = current_time

    # Activate wind gusts if none are currently active
    if not wind_active:
        if random.random() < 0.03:  # 3% chance each frame to start a wind gust
            wind_active = True
            wind_duration = random.randint(10, 30)
            wind_start_time = current_time
            gust_y = random.randint(0, height - height // 4)
            wind_rect = pygame.Rect(0, gust_y, width, height // 4)
            wind_direction = (1, 0) if random.choice([True, False]) else (-1, 0)
    else:
        if current_time - wind_start_time >= wind_duration:
            wind_active = False

    # Simulate communication between boats every second
    if not network_outage and current_time - last_communication_time >= communication_interval:
        communicate()
        last_communication_time = current_time

    # Randomly generate waves half as often
    if random.random() < 0.025:
        wave_x = random.randint(0, width)
        wave_y = random.randint(0, height)
        wave_width = random.randint(50, 150)
        wave_height = wave_width // 2

        wave_direction = get_closest_wave_direction(wave_x, wave_y)
        if wave_direction is None:
            wave_direction = get_random_direction()

        waves.append((wave_x, wave_y, wave_width, wave_height, time.time(), wave_direction))

    if not boats_meet:
        dx1 = boat1_received_pos[0] - boat1_pos[0]
        dy1 = boat1_received_pos[1] - boat1_pos[1]
        move_x1, move_y1 = normalize_movement(dx1, dy1, boat_speed)
        angle1 = math.degrees(math.atan2(dy1, dx1))

        if wind_active and wind_rect.collidepoint(boat1_pos[0], boat1_pos[1]):
            move_x1 += wind_direction[0] * wind_speed
            move_y1 += wind_direction[1] * wind_speed
            boat1_in_wind = True
        else:
            boat1_in_wind = False
        boat1_pos[0] += move_x1
        boat1_pos[1] += move_y1

        dx2 = boat2_received_pos[0] - boat2_pos[0]
        dy2 = boat2_received_pos[1] - boat2_pos[1]
        move_x2, move_y2 = normalize_movement(dx2, dy2, boat_speed)
        angle2 = math.degrees(math.atan2(dy2, dx2))

        if wind_active and wind_rect.collidepoint(boat2_pos[0], boat2_pos[1]):
            move_x2 += wind_direction[0] * wind_speed
            move_y2 += wind_direction[1] * wind_speed
            boat2_in_wind = True
        else:
            boat2_in_wind = False
        boat2_pos[0] += move_x2
        boat2_pos[1] += move_y2

        if (abs(boat1_pos[0] - boat2_pos[0]) <= boat_size and abs(boat1_pos[1] - boat2_pos[1]) <= boat_size):
            boats_meet = True
            timer_running = False

    # Move boats if hit by a wave
    waves = [wave for wave in waves if current_time - wave[4] < wave_lifespan]

    for wave in waves:
        wave_x, wave_y, wave_width, wave_height, _, wave_direction = wave

        if wave_x <= boat1_pos[0] <= wave_x + wave_width and wave_y <= boat1_pos[1] <= wave_y + wave_height:
            boat1_in_wave = True
            boat1_pos[0] += wave_direction[0] * wave_speed
            boat1_pos[1] += wave_direction[1] * wave_speed
        else:
            boat1_in_wave = False
        if wave_x <= boat2_pos[0] <= wave_x + wave_width and wave_y <= boat2_pos[1] <= wave_y + wave_height:
            boat2_in_wave = True
            boat2_pos[0] += wave_direction[0] * wave_speed
            boat2_pos[1] += wave_direction[1] * wave_speed
        else:
            boat2_in_wave = False
        draw_wave(screen, wave_x, wave_y, wave_width, wave_height)
        draw_arrow(screen, (wave_x + wave_width / 2, wave_y + wave_height / 2), wave_direction)

    draw_rotated_triangle(screen, BLUE, boat1_pos, angle1)
    draw_rotated_triangle(screen, RED, boat2_pos, angle2)

    # Drawing indicators
    if current_time - boat1_indicator_time <= indicator_duration:
        pygame.draw.circle(screen, GREEN, (int(boat1_pos[0]), int(boat1_pos[1] - boat_size - 10)), 5)
        if rollback_enabled:
            if boat1_in_wind:
                pygame.draw.circle(screen, WHITE, (int(boat1_pos[0] - 15), int(boat1_pos[1] - boat_size - 10)), 5)
                #print(f"Drawing Boat1 Wind Indicator: {boat1_in_wind}, Wave Indicator: {boat1_in_wave}")
            if boat1_in_wave:
                pygame.draw.rect(screen, BLACK, (int(boat1_pos[0] - 30), int(boat1_pos[1] - boat_size - 15), 5, 10))
                #print(f"Drawing Boat1 Wind Indicator: {boat1_in_wind}, Wave Indicator: {boat1_in_wave}")
    if current_time - boat2_indicator_time <= indicator_duration:
        pygame.draw.circle(screen, GREEN, (int(boat2_pos[0]), int(boat2_pos[1] - boat_size - 10)), 5)
        if rollback_enabled:
            if boat2_in_wind:
                #print(f"Drawing Boat2 Wind Indicator: {boat2_in_wind}, Wave Indicator: {boat2_in_wave}")
                pygame.draw.circle(screen, WHITE, (int(boat2_pos[0] - 15), int(boat2_pos[1] - boat_size - 10)), 5)
            if boat2_in_wave:
                #print(f"Drawing Boat2 Wind Indicator: {boat2_in_wind}, Wave Indicator: {boat2_in_wave}")
                pygame.draw.rect(screen, BLACK, (int(boat2_pos[0] - 30), int(boat2_pos[1] - boat_size - 15), 5, 10))
    
    if wind_active:
        draw_solid_rectangle(screen, wind_rect, WHITE, 128)

    if network_outage:
        draw_hollow_triangle(screen, BLUE, last_boat1_pos, angle1)
        draw_hollow_triangle(screen, RED, last_boat2_pos, angle2)

    if timer_running:
        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
        timer_text = font.render(f"Time: {elapsed_time:.2f} seconds", True, WHITE)
        screen.blit(timer_text, (10, 10))
    if not timer_running:
        print("Timer stopped")
        timer_text = font.render(f"Time: {elapsed_time:.2f} seconds", True, WHITE)
        screen.blit(timer_text, (10, 10))
    
    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()
sys.exit()
