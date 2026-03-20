from typing import Any
import cv2
import numpy as np
import time
import requests

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


def angle_between(a, b):
    dot = np.dot(a, b)
    cos = np.clip(dot, -1, 1)
    return np.degrees(np.arccos(cos))


# we need to spam these for each second for car to move

W = 800
PAD = 50

def build_world_canvas():
    canvas = np.zeros((W + 2*PAD, W + 2*PAD, 3), dtype=np.uint8)

    # Draw border corners
    for pt in [[0,0],[0,1],[1,1],[1,0]]:
        cv2.circle(canvas, to_canvas(np.array(pt, dtype=np.float32)), 5, (0, 255, 255), -1)

    return canvas

def draw_car_on_canvas(canvas, car_id, car_corners_world):
    car_center_world = np.mean(car_corners_world, axis=0)
    car_direction_vector_world = car_corners_world[0] - car_corners_world[3]

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



def rotate_n_times() -> bool:
    markers = fetch_recent_markers()
    ptransform = get_world_perspective_transform(markers)

    car_marker = markers.get(CAR_ID)
    if car_marker is None:
        print(f"Failed to find a car {CAR_ID}. Retrying..")
        return False

    car_center_world = to_world(ptransform, get_center_point(car_marker))

    # Wait 2 seconds for car to rotate
    rotate_power = 0.45

    for _ in range(10):
        rotate(rotate_power)
        time.sleep(2)

        markers = fetch_recent_markers()

        car_marker_1 = markers.get(CAR_ID)
        if car_marker_1 is None:
            print(f"Failed to find a car {CAR_ID}. Retrying..")
            continue

        car_center_world_1 = to_world(ptransform, get_center_point(car_marker_1))

        car_rotate_angle = angle_between(car_center_world, car_center_world_1)
        print(f"{rotate_power} -> {car_rotate_angle}")

        car_center_world = car_center_world_1


    return True

def main():
    while True:
        success = rotate_n_times()
        if success:
            break


if __name__ == "__main__":
    main()



# 1. Fetch Image
# 2. Build world transform
# 3. Find angle to 1.1
# 4. Rotate
# 5. Find angle to 1.1
# 6. compare



# canvas = build_world_canvas()


# for id, corners in markers.items():
#     if id == 11 or id == 12 or id == 13:
#         continue

#     car_corners_world = np.array([to_world(pt) for pt in corners[0]])
#     draw_car_on_canvas(canvas, id, car_corners_world)

# cv2.imshow(f"world{i}", canvas)

# # cv2.aruco.drawDetectedMarkers(image, corners, ids)
# # cv2.imshow(f"out{i}", image)

# if i == 0:
#     time.sleep(2)
# else:
#     wait_for_key()
#     cv2.destroyAllWindows()
#     break
