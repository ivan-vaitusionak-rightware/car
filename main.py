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

W = 800
PAD = 50

def build_world_canvas():
    canvas = np.zeros((W + 2*PAD, W + 2*PAD, 3), dtype=np.uint8)

    # Draw border corners
    for pt in [[0,0],[0,1],[1,1],[1,0]]:
        cv2.circle(canvas, to_canvas(np.array(pt, dtype=np.float32)), 5, (0, 255, 255), -1)

    return canvas

def draw_car_on_canvas(canvas, car_id, ptransform, car_marker):
    car_corners_world = np.array([to_world(ptransform, pt) for pt in car_marker[0]])
    car_center_world = np.mean(car_corners_world, axis=0)
    car_direction_vector_world = car_corners_world[0] - car_corners_world[3]

    if car_id == CAR_ID:
        print(car_direction_vector_world)
        print()

    # Car is a circle
    car_pt = to_canvas(car_center_world)
    cv2.circle(canvas, car_pt, 8, (0, 0, 255), -1)

    cv2.putText(
        canvas,
        str(car_id),
        (car_pt[0] + 10, car_pt[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        1
    )

    # Direction vector
    car_arrow_end = car_center_world + car_direction_vector_world * 2.1
    cv2.arrowedLine(canvas, car_pt, to_canvas(car_arrow_end), (0, 0, 255), 2)



def to_canvas(world_point):
    return (int(world_point[0] * W + PAD), int(world_point[1] * W + PAD))

def wait_for_key():
    while True:
        if cv2.waitKey(100) != -1:
            break


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


# marker -> point
def get_center_point(marker):
    return np.mean(marker[0], axis=0)

# Hardcoded border markers for camera 11.
# Note that the last corner is not visible.
IDS = {
    13: np.array([149.5,  50.25]),  # top left
    12: np.array([518.75, 614.25]), # bottom left
    11: np.array([1157.5, 386.25]), # bottom right
}

def get_world_perspective_transform(markers):
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


def draw_all_cars(markers, ptransform):
    canvas = build_world_canvas()

    for id, marker in markers.items():
        if id == 11 or id == 12 or id == 13:
            continue

        draw_car_on_canvas(canvas, id, ptransform, marker)

    return canvas

def get_car_direction_world(ptransform, car_marker_image):
    car_corners_world = np.array([to_world(ptransform, pt) for pt in car_marker_image[0]])
    car_direction_vector_world = car_corners_world[0] - car_corners_world[3]

    return car_direction_vector_world


def rotate_n_times() -> bool:
    markers = fetch_recent_markers()
    ptransform = get_world_perspective_transform(markers)

    car_marker = markers.get(CAR_ID)
    if car_marker is None:
        print(f"Failed to find a car {CAR_ID}. Retrying..")
        return False

    car_direction = get_car_direction_world(ptransform, car_marker)

    # Wait 2 seconds for car to rotate
    rotate_power = 0.45

    for i in range(10):
        print("Move car, press any button")
        wait_for_keypress()

        # rotate(rotate_power)
        # time.sleep(2)

        markers = fetch_recent_markers()

        car_marker_1 = markers.get(CAR_ID)
        if car_marker_1 is None:
            print(f"Failed to find a car {CAR_ID}. Retrying..")
            continue

        car_direction_1 = get_car_direction_world(ptransform, car_marker_1)

        car_rotate_angle = angle_between(car_direction, car_direction_1)
        print(f"{rotate_power} -> {car_rotate_angle} | {car_direction} {car_direction_1}")

        car_direction = car_direction_1

        canvas = draw_all_cars(markers, ptransform)
        cv2.imshow(f"world{i}", canvas)
        cv2.waitKey(1)

    return True

def get_current_quadrant() -> str:
    # @TODO
    return "TL"

def get_car_position_and_direction():
    pass

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


def rotate_to_quadrant(car_direction, quadrant: str):
    QUADRANT_MIDDLES = {
        "TL": [0.25, 0.25],
        "TR": [0.25, 0.75],
        "BL": [0.75, 0.25],
        "BR": [0.75, 0.75],
    }
    quadrant_middle = QUADRANT_MIDDLES[quadrant]

    angle = angle_between(car_direction, quadrant_middle)



def main():
    while True:
        time.sleep(1)

        markers = fetch_recent_markers()
        ptransform = get_world_perspective_transform(markers)

        car_marker = markers.get(CAR_ID)
        if car_marker is None:
            print(f"Failed to find a car {CAR_ID}. Retrying..")
            continue


        car_position, car_direction = get_car_position_and_direction(ptransform, car_marker_1)

        if get_car_quadrant(car_position) == get_current_quadrant():
            continue



        # rotate to quadrant
        # drive to quadrant


if __name__ == "__main__":
    main()



# 1. Fetch Image
# 2. Build world transform
# 3. Find angle to 1.1
# 4. Rotate
# 5. Find angle to 1.1
# 6. compare







# # cv2.aruco.drawDetectedMarkers(image, corners, ids)
# # cv2.imshow(f"out{i}", image)

# if i == 0:
#     time.sleep(2)
# else:
#     break


fetch_recent_markers()
