from typing import Any
import cv2
import numpy as np
import time
import requests
import msvcrt

CAR_ID: int = 1
CAR_AUTH: int = 985898


def get_camera_image(id: int) -> bytes:
    if id == 11:
        code = 983149
    elif id == 12:
        code = 378031
    else:
        assert False

    response = requests.get(
        f"http://hackathon-{id}-camera.local:50051/frame",
        headers={"Authorization": f"{code}"}
    )

    return response.content

def send_rotate(speed: float):
    put(speed, True)

def send_move(speed: float):
    put(speed, False)


def put(speed: float, flip: bool):
    _ = requests.put(
        f"http://hackathon-{CAR_ID}-car.local:5000",
        headers={"Authorization": f'{CAR_AUTH}'},
        json={"speed": speed, "flip": flip}
    )


def angle_between(v1, v2):
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

# we need to spam these for each second for car to move




# id -> marker
def fetch_recent_markers() -> dict[int, Any]:
    image_png = get_camera_image(11)
    image = cv2.imdecode(np.frombuffer(image_png, np.uint8), cv2.IMREAD_COLOR)

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    params = cv2.aruco.DetectorParameters()
    params.errorCorrectionRate = 1.0
    detector = cv2.aruco.ArucoDetector(dictionary, params)

    corners, ids, _ = detector.detectMarkers(image)

    # id -> corner
    # 11, 12, 13
    markers = {int(id): corner for id, corner in zip(ids.flatten(), corners)}

    return markers

# Hardcoded border markers for camera 11.
# Note that the last corner is not visible.
IDS = {
    13: np.array([149.5,  50.25]),  # top left
    12: np.array([518.75, 614.25]), # bottom left
    11: np.array([1157.5, 386.25]), # bottom right
}

def get_world_perspective_transform(markers):
    def get_center_point(marker):
        return np.mean(marker[0], axis=0)

    corners = []

    for id, default_center in IDS.items():
        corner_marker = markers.get(id)
        if corner_marker is None:
            corners.append(default_center)
        else:
            corners.append(get_center_point(marker=corner_marker))

    corners.append(corners[0] + (corners[2] - corners[1]))

    src = np.array(
        corners,
        dtype=np.float32
    )
    dst = np.array(
        [[0, 0], [0, 1], [1, 1], [1, 0]],
        dtype=np.float32
    )

    H_mat, _ = cv2.findHomography(src, dst)

    return H_mat

def to_world(ptransform, pixel_point):
    p = np.array([[pixel_point]], dtype=np.float32)
    return cv2.perspectiveTransform(p, ptransform)[0][0]


QUADRANT_MATCH = {
    "TL": "BR",
    "TR": "BL",
    "BR": "TL",
    "BL": "TR",
}
def get_current_quadrant() -> str:
    real_quadrant = requests.get("http://192.168.0.85:8000/goal").json()["quadrant"]
    return QUADRANT_MATCH[real_quadrant]

def rev(quad) -> str:
    return QUADRANT_MATCH[quad]

def get_car_position_and_direction(ptransform, car_marker):
    car_corners_world = np.array([to_world(ptransform, pt) for pt in car_marker[0]])

    car_direction = car_corners_world[0] - car_corners_world[3]
    car_position = np.mean(car_corners_world, axis=0)

    return car_position, car_direction

def get_car_quadrant(car_position) -> str:
    x, y = car_position
    if y < 0.5:
        if x < 0.5:
            return "TL"
        else:
            return "TR"
    else:
        if x < 0.5:
            return "BL"
        else:
            return "BR"

QUADRANT_MIDDLES = {
    "TL": [0.25, 0.25],
    "TR": [0.75, 0.25],
    "BL": [0.25, 0.75],
    "BR": [0.75, 0.75],
}

def turnpower(deg):
    max = 0.75

    m = max / 180
    return m * deg

def movepower(len):
    max = 0.25

    m = max / 1
    return m * len

def rotate_to(car_direction, target):
    cross = np.cross(car_direction, target)
    dot = np.dot(car_direction, target)
    angle = np.degrees(np.arctan2(cross, dot))

    power = turnpower(angle)

    print(car_direction)
    print(target)
    print(f"Angle to middle is: {angle}. Rotating with power: {power}")

    send_rotate(power)
    time.sleep(1)

def drive_to(car_position, target):
    dist = distance_between(car_position, target)

    power = movepower(dist)

    print(car_position)
    print(target)
    print(f"Distance to middle is: {dist}. Moving with power: {power}")

    send_move(power)
    time.sleep(1)

def distance_between(v1, v2):
    return np.linalg.norm(v2 - v1)


def main():
    while True:
        markers = fetch_recent_markers()
        ptransform = get_world_perspective_transform(markers)

        car_marker = markers.get(CAR_ID)
        if car_marker is None:
            import random
            print(f"Failed to find a car {CAR_ID}. Retrying..")
            send_rotate(random.choice([-1, 1]))
            send_move(
            continue

        car_position, car_direction = get_car_position_and_direction(ptransform, car_marker)
        car_quadrant = get_car_quadrant(car_position)
        current_quadrant = get_current_quadrant()

        if get_car_quadrant(car_position) == current_quadrant:
            print(f"Car in quadrant: {rev(car_quadrant)}. Same as current")
            continue

        print(f"Car in quadrant: {rev(car_quadrant)} moving to {rev(current_quadrant)}")

        quadrant_middle = QUADRANT_MIDDLES[current_quadrant]
        rotate_to(car_direction, quadrant_middle)
        drive_to(car_position, quadrant_middle)

        time.sleep(1)
        print()


if __name__ == "__main__":
    main()
