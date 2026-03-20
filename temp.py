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

def draw_all_cars(markers, ptransform):
    canvas = build_world_canvas()

    for id, marker in markers.items():
        if id == 11 or id == 12 or id == 13:
            continue

        draw_car_on_canvas(canvas, id, ptransform, marker)

    return canvas

def get_car_direction_world(ptransform, car_marker_image):

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

