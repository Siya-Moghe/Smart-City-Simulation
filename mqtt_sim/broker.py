import socket
import threading
import time
import random
import json
import traceback

HOST = '0.0.0.0'
PORT = 1883

# Global Variables
cars = [{"x": 50, "y": 300}]  # List of car positions
sensor_positions = [200, 400, 600]
light_states = [0, 0, 0, 0, 0, 0]
ldr_value = 1
traffic_light_positions_y = [120, 145, 170]  # Y-coordinates for Red, Yellow, Green
traffic_states = [0, 0, 0]  # 0: GRAY/OFF, 1: ON (will map to colors)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"MQTT Broker listening on {HOST}:{PORT}")


def update_light_states():
    """Updates streetlight states based on cars' positions."""
    global light_states
    light_states = [0, 0, 0, 0, 0, 0]  # Reset
    for car in cars:
        car_x = car["x"]
        for i in range(3):
            sensor_x = sensor_positions[i]
            if sensor_x - 50 < car_x < sensor_x + 50:
                light_states[i * 2] = 1
                light_states[i * 2 + 1] = 1


def update_traffic_states():
    """Updates traffic light states based on the number of cars detected by sensors."""
    global traffic_states
    cars_on_sensors = 0
    for car in cars:
        car_x = car["x"]
        for sensor_x in sensor_positions:
            if sensor_x - 50 < car_x < sensor_x + 50:
                cars_on_sensors += 1
                break  # Count each car only once

    if cars_on_sensors == 1:
        traffic_states = [1, 0, 0]  # Red (top)
    elif cars_on_sensors == 2:
        traffic_states = [0, 1, 0]  # Yellow (middle)
    elif cars_on_sensors >= 3:
        traffic_states = [0, 0, 1]  # Green (bottom)
    else:
        traffic_states = [0, 0, 0]  # Default/Off


def handle_client(client_socket, client_address):
    global cars, ldr_value

    print(f"Accepted connection from {client_address}")
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            print(f"Received data: {data}")

            if data.startswith("GET_SENSORS"):
                update_light_states()
                update_traffic_states()
                sensor_data = {
                    "cars": cars,
                    "light_states": light_states,
                    "ldr": ldr_value,
                    "traffic_states": traffic_states,
                }
                send_message(client_socket, "sensors", json.dumps(sensor_data))

            elif data.startswith("MOVE_CAR"):
                try:
                    _, index, new_x, new_y = data.split(':')
                    index = int(index)
                    new_x = float(new_x)
                    new_y = float(new_y)
                    if 0 <= index < len(cars):
                        cars[index]["x"] = new_x
                        cars[index]["y"] = new_y
                        update_light_states()
                        update_traffic_states()
                        print(f"Car {index} moved to ({new_x}, {new_y})")
                except Exception as e:
                    print(f"Error processing MOVE_CAR: {e}")
                    traceback.print_exc()

            elif data.startswith("ADD_CAR"):
                try:
                    new_car = {"x": 50, "y": 300}
                    cars.append(new_car)
                    update_traffic_states()
                    print(f"Added new car at {new_car}")
                except Exception as e:
                    print(f"Error processing ADD_CAR: {e}")
                    traceback.print_exc()

            elif data.startswith("SET_LDR"):
                try:
                    _, ldr_new_value = data.split(':')
                    ldr_value = int(ldr_new_value)
                    print(f"LDR value set to {ldr_value}")
                except Exception as e:
                    print(f"Error processing SET_LDR: {e}")
                    traceback.print_exc()

    except ConnectionResetError:
        print(f"Client {client_address} disconnected.")
    except Exception as e:
        print(f"Error in handle_client: {e}")
        traceback.print_exc()
    finally:
        client_socket.close()


def send_message(client_socket, topic, message):
    try:
        client_socket.send(f"{topic}:{message}".encode('utf-8'))
    except Exception as e:
        print(f"Error sending message: {e}")
        traceback.print_exc()


def main():
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down the broker...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()