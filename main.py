import cv2
import numpy as np
import time
import requests


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
    #
    # flip, as a boolean. If true, the wheels will drive in opposite directions, causing you to turn roughly in place.
    #

    # car_id = 3
    # car_auth = 838748

    car_id = 1
    car_auth = 985898

    # curl -X PUT hackathon-1-car.local:5000  
    # --header "Content-Type: application/json"   
    # --header "Authorization: 985898"   
    # --data '{"speed":0.5,"flip":true}'

    _response = requests.put(
        f"http://hackathon-{car_id}-car.local:5000",
        headers={"Authorization": f'{car_auth}'},
        json={"speed": speed, "flip": True}
    )

# speed -1, 1
def move(speed: float):
    # speed, as a float between -1.0 (drive backwards) and 1.0 (drive forwards). Smaller values cause you to drive more slowly.
    car_auth = "838748"
    _response = requests.put(
        "http://hackathon-3-car.local:5000",
        headers={"Authorization": car_auth},
        json={"speed": speed, "flip": False}
    )

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

# curl hackathon-11-camera.local:50051/frame --header "Authorization: 983149" --output image11.png
# curl hackathon-12-camera.local:50051/frame --header "Authorization: 378031" --output image12.png

def main():
    while True:
        image_png = get_camera_image(11)
        with open("temp.png", "wb") as handle:
            handle.write(image_png)

        image = cv2.imdecode(np.frombuffer(image_png, np.uint8), cv2.IMREAD_COLOR)

        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        params = cv2.aruco.DetectorParameters()
        params.errorCorrectionRate = 1.0
        detector = cv2.aruco.ArucoDetector(dictionary, params)


        corners, ids, rejected = detector.detectMarkers(image)

        # id -> corner
        # 11, 12, 13
        markers = {int(id): corner for id, corner in zip(ids.flatten(), corners)}
        centers = {id: np.mean(corner[0], axis=0) for id, corner in markers.items()}

        for id, center in sorted(centers.items(), key=lambda item: item[1][0]):
            print(f"{id} -- {center}")

        tl = centers.get(13, np.array([149.5,  50.25]))   # top left
        bl = centers.get(12, np.array([518.75, 614.25]))  # bottom left
        br = centers.get(11, np.array([1157.5, 386.25]))  # bottom right
        tr = tl + (br - bl)
        print(f"14 -- {tr}")

        src = np.array([tl, bl, br, tr],                 dtype=np.float32)
        dst = np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.float32)

        H_mat, _ = cv2.findHomography(src, dst)
        def to_world(pixel_point):
            p = np.array([[pixel_point]], dtype=np.float32)
            return cv2.perspectiveTransform(p, H_mat)[0][0]



        canvas = build_world_canvas()

        cv2.aruco.drawDetectedMarkers(image, corners, ids)

        for id, corners in markers.items():
            if id == 11 or id == 12 or id == 13:
                continue

            car_corners_world = np.array([to_world(pt) for pt in corners[0]])
            draw_car_on_canvas(canvas, id, car_corners_world)



        cv2.imshow("world", canvas)
        cv2.imshow("out", image)

        wait_for_key()

        cv2.destroyAllWindows()



        break

if __name__ == "__main__":
    rotate(0.45)
    # main()

