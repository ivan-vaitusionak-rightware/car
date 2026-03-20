import cv2
import numpy as np
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


# curl hackathon-11-camera.local:50051/frame --header "Authorization: 983149" --output image11.png
# curl hackathon-12-camera.local:50051/frame --header "Authorization: 378031" --output image12.png

def main():
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
    # 3, 11, 12, 13 
    markers = {int(id): corner for id, corner in zip(ids.flatten(), corners)}

    for id, corner in markers.items():
        center = np.mean(corner[0], axis=0)
        print(f"{id} -- {center}")

        pass


    center_11 = np.mean(markers[11][0], axis=0)  # shape (2,) = [x, y]
    center_12 = np.mean(markers[12][0], axis=0)
    center_13 = np.mean(markers[13][0], axis=0)
    print(center_11)
    print(center_12)
    print(center_13)
    # center_14 = np.mean(markers[14][0], axis=0)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(image, corners, ids)
        print("Found markers:", ids.flatten())
    else:
        print("No markers found")

    cv2.imshow("out", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
