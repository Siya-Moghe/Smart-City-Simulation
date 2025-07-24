import socket
import pygame
import sys
import time
import json
import traceback

BROKER_HOST = '127.0.0.1'         #192.168.248.235
BROKER_PORT = 1883

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CAR_SIZE = 20
SENSOR_SIZE = 10
LIGHT_SIZE = 10
ROAD_COLOR = (100, 100, 100)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
DARK_ORANGE = (200, 100, 0)

cars = [{"x": 50, "y": 300}]
sensor_positions = [200, 400, 600]
light_states = [0] * 6
client_socket = None
dragging_car_index = None
ldr_value = 1
ldr_button_rect = None
add_car_button_rect = None

traffic_light_positions_y = [120, 145, 170]  # Y-coordinates for Red, Yellow, Green
traffic_states = [0] * 3  # 0: GRAY/OFF, 1: ON (will map to colors)

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Simplified Streetlight Simulation")
font = pygame.font.Font(None, 30)


def draw_road():
    pygame.draw.rect(screen, ROAD_COLOR, (0, WINDOW_HEIGHT / 3, WINDOW_WIDTH, WINDOW_HEIGHT / 3))


def draw_sensors():
    for x in sensor_positions:
        pygame.draw.rect(screen, GRAY, (x - SENSOR_SIZE / 2, WINDOW_HEIGHT / 3 + 50, SENSOR_SIZE, SENSOR_SIZE))


def draw_lights():
    light_positions = [
        (sensor_positions[0], WINDOW_HEIGHT / 3 - 20),
        (sensor_positions[0], 2 * WINDOW_HEIGHT / 3 + 20),
        (sensor_positions[1], WINDOW_HEIGHT / 3 - 20),
        (sensor_positions[1], 2 * WINDOW_HEIGHT / 3 + 20),
        (sensor_positions[2], WINDOW_HEIGHT / 3 - 20),
        (sensor_positions[2], 2 * WINDOW_HEIGHT / 3 + 20),
    ]
    for i, pos in enumerate(light_positions):
        color = GRAY
        if ldr_value == 0 and light_states[i] == 1:
            color = YELLOW
        pygame.draw.circle(screen, color, pos, LIGHT_SIZE // 2)


def draw_traffic():
    traffic_light_x = (2*WINDOW_WIDTH) / 3 + 200
    for i, y_pos in enumerate(traffic_light_positions_y):
        color = GRAY
        if traffic_states[0] == 1 and i == 0:  # Red
            color = RED
        elif traffic_states[1] == 1 and i == 1:  # Yellow
            color = YELLOW
        elif traffic_states[2] == 1 and i == 2:  # Green
            color = GREEN
        pygame.draw.circle(screen, color, (traffic_light_x, y_pos), LIGHT_SIZE // 2)


def draw_car():
    for car in cars:
        pygame.draw.rect(screen, BLUE, (car["x"], car["y"], CAR_SIZE, CAR_SIZE))


def draw_ldr_button():
    global ldr_button_rect
    ldr_button_rect = pygame.Rect(WINDOW_WIDTH / 2 - 50, 20, 100, 30)
    pygame.draw.rect(screen, ORANGE, ldr_button_rect)
    pygame.draw.rect(screen, DARK_ORANGE, (WINDOW_WIDTH / 2 - 48, 22, 96, 26), 2)
    ldr_text = font.render("LDR: " + ("DAY" if ldr_value == 1 else "NIGHT"), True, BLACK)
    screen.blit(ldr_text, ldr_text.get_rect(center=ldr_button_rect.center))


def draw_add_car_button():
    global add_car_button_rect
    add_car_button_rect = pygame.Rect(20, 20, 100, 30)
    pygame.draw.rect(screen, GREEN, add_car_button_rect)
    add_text = font.render("Add Car", True, BLACK)
    screen.blit(add_text, add_text.get_rect(center=add_car_button_rect.center))


def connect_to_broker():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((BROKER_HOST, BROKER_PORT))


def get_sensor_data():
    if client_socket:
        try:
            client_socket.send("GET_SENSORS".encode('utf-8'))
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                topic, message = data.split(':', 1)
                if topic == "sensors":
                    update_simulation(message)
        except:
            traceback.print_exc()


def move_car(index, new_x, new_y):
    if client_socket:
        try:
            client_socket.send(f"MOVE_CAR:{index}:{new_x}:{new_y}".encode('utf-8'))
        except:
            traceback.print_exc()


def add_car():
    if client_socket:
        try:
            client_socket.send("ADD_CAR".encode('utf-8'))
        except:
            traceback.print_exc()


def update_simulation(data):
    global cars, light_states, ldr_value, traffic_states
    try:
        sensor_data = json.loads(data)
        cars = sensor_data["cars"]
        light_states = sensor_data["light_states"]
        ldr_value = sensor_data["ldr"]
        traffic_states = sensor_data.get("traffic_states", [0] * 3)
    except:
        traceback.print_exc()


def toggle_ldr():
    global ldr_value
    ldr_value = 1 - ldr_value
    if client_socket:
        try:
            client_socket.send(f"SET_LDR:{ldr_value}".encode('utf-8'))
        except:
            traceback.print_exc()


def handle_events():
    global dragging_car_index
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for i, car in enumerate(cars):
                    car_rect = pygame.Rect(car["x"], car["y"], CAR_SIZE, CAR_SIZE)
                    if car_rect.collidepoint(event.pos):
                        dragging_car_index = i
                        break
                if ldr_button_rect and ldr_button_rect.collidepoint(event.pos):
                    toggle_ldr()
                elif add_car_button_rect and add_car_button_rect.collidepoint(event.pos):
                    add_car()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_car_index = None
        elif event.type == pygame.MOUSEMOTION and dragging_car_index is not None:
            new_x = event.pos[0] - CAR_SIZE / 2
            new_y = event.pos[1] - CAR_SIZE / 2
            cars[dragging_car_index]["x"] = new_x
            cars[dragging_car_index]["y"] = new_y
            move_car(dragging_car_index, new_x, new_y)
            get_sensor_data()


def game_loop():
    connect_to_broker()
    while True:
        screen.fill(BLACK)
        handle_events()
        get_sensor_data()
        draw_road()
        draw_sensors()
        draw_lights()
        draw_traffic()
        draw_car()
        draw_ldr_button()
        draw_add_car_button()
        pygame.display.flip()
        time.sleep(0.1)


if __name__ == "__main__":
    game_loop()