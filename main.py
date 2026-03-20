from typing import Any
import cv2
import numpy as np
import time
import requests
import msvcrt

CAR_ID: int = 1
CAR_AUTH: int = 985898

# car_id = 3
# car_auth = 838748


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

def rotate(speed: float):
    put(speed, True)

def move(speed: float):
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


def get_current_quadrant() -> str:
    # @TODO
    return "TL"

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
    "TR": [0.25, 0.75],
    "BL": [0.75, 0.25],
    "BR": [0.75, 0.75],
}

def rotate_to(car_direction, quadrant_angle):
    angle = angle_between(car_direction, quadrant_angle)
    # TODO
    pass

def drive_to(car_position, quadrant_position):
    # TODO
    pass

def main():
    while True:
        markers = fetch_recent_markers()
        ptransform = get_world_perspective_transform(markers)

        car_marker = markers.get(CAR_ID)
        if car_marker is None:
            print(f"Failed to find a car {CAR_ID}. Retrying..")
            continue

        car_position, car_direction = get_car_position_and_direction(ptransform, car_marker)

        current_quadrant = get_current_quadrant()
        if get_car_quadrant(car_position) == current_quadrant:
            continue

        quadrant_middle = QUADRANT_MIDDLES[current_quadrant]
        rotate_to(car_direction, quadrant_middle)
        drive_to(car_position, quadrant_middle)

        time.sleep(1)


if __name__ == "__main__":
    main()
