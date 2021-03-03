import cv2
import numpy as np


blue = (255, 0, 0)
green = (0, 255, 0)
red = (0, 0, 255)

lower_green = (60, 140, 90)
upper_green = (150, 255, 200)

img_width_feet = 2.25

video_name = "throw_2"


def extract_object_arr(img, lower_color, upper_color):
    mask = cv2.inRange(img, lower_color, upper_color)
    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    sizes = stats[1:, -1]
    nb_components = nb_components - 1
    min_size = 2000
    obj_arr = np.zeros((output.shape))
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            obj_arr[output == i + 1] = 255
    return obj_arr


def get_object_img(img, obj_arr):
    refined_mask = cv2.inRange(obj_arr, 255, 255)
    return cv2.bitwise_and(img, img, mask=refined_mask)


def has_obj(obj_arr):
    max_y, max_x = obj_arr.shape
    for y in range(max_y):
        if max(obj_arr[y]) != 0:
            return True
    return False


def has_partial_object(obj_arr):
    max_y, max_x = obj_arr.shape
    for y in range(max_y):
        if obj_arr[y, width-1] > 0 or obj_arr[y, 0] > 0:
            return True
    return False


def get_obj_diameter(obj_arr):
    o = obj_arr.transpose()
    max_y, max_x = o.shape
    obj_start, obj_end = 0, max_y
    start_acquired = False
    for y in range(max_y):
        if max(o[y]) > 0 and not start_acquired:
            obj_start = y
            start_acquired = True
        elif max(o[y]) == 0 and start_acquired:
            obj_end = y
            break
    return obj_end - obj_start
          

video = cv2.VideoCapture("{}.mp4".format(video_name))
fps = video.get(cv2.CAP_PROP_FPS)
width  = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
size = (width, height)
    
success, img = video.read()
frames = []
obj_arrs = []

print("Creating images...")

count = 0
while success:
    obj_arr = extract_object_arr(img, lower_green, upper_green)
    img_refined = get_object_img(img, obj_arr)
    cv2.imwrite("frames/frame_{}.jpg".format(count), img_refined)
    cv2.imwrite("frames_original/frame_{}.jpg".format(count), img)
    
    frames.append(img_refined)
    obj_arrs.append(obj_arr)
    success, img = video.read()
    count += 1

print("Creating avi video...")

out_format = cv2.VideoWriter_fourcc(*'DIVX')
out = cv2.VideoWriter("{}_processed.avi".format(video_name), out_format, fps, size)
out_slow = cv2.VideoWriter("{}_processed_slow.avi".format(video_name), out_format, fps / 8, size)
for f in frames:
    out.write(f)
    out_slow.write(f)
out.release()
out_slow.release()

print("Projecting flight path...")

frames_with_obj = []
for i in range(len(obj_arrs)):
    if has_obj(obj_arrs[i]):
        frames_with_obj.append(i)

full_img_frames = [i for i in frames_with_obj if not has_partial_object(obj_arrs[i])]

first_partial_width = get_obj_diameter(obj_arrs[min(frames_with_obj)])
last_partial_width = get_obj_diameter(obj_arrs[max(frames_with_obj)])
obj_width = get_obj_diameter(obj_arrs[full_img_frames[0]])
movement_frames = max(frames_with_obj) - min(frames_with_obj)

# forward-moving velocity (configured for right-to-left)
x_movement_pixels = width + obj_width - first_partial_width - last_partial_width
x_pixels_per_frame = x_movement_pixels / movement_frames
x_pixels_per_second = x_pixels_per_frame * fps
x_feet_per_second = x_pixels_per_second / width * img_width_feet

# side-moving velocity (up is negative, down is positive)
first_partial_y_min, last_partial_y_min = height, height
first_partial_y_max, last_partial_y_max = 0, 0
for y in range(height):
    if obj_arrs[min(frames_with_obj)][y, width-1] != 0:
        first_partial_y_min = min(first_partial_y_min, y)
        first_partial_y_max = max(first_partial_y_max, y)
    if obj_arrs[max(frames_with_obj)][y, 0] != 0:
        last_partial_y_min = min(last_partial_y_min, y)
        last_partial_y_max = max(last_partial_y_max, y)

first_partial_y_center = (first_partial_y_max + first_partial_y_min) // 2
last_partial_y_center = (last_partial_y_max + last_partial_y_min) // 2

y_movement_pixels = last_partial_y_center - first_partial_y_center
y_pixels_per_frame = y_movement_pixels / movement_frames
y_pixels_per_second = y_pixels_per_frame * fps
y_feet_per_second = y_pixels_per_second / width * img_width_feet

#########
if False:
    img = cv2.imread("frames/frame_20.jpg")
    img_bw = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(img_bw, 127, 255, cv2.THRESH_BINARY)
    contours, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    try:
        c = contours[-1]
        (x,y), radius = cv2.minEnclosingCircle(c)
        center = (int(x), int(y))
        radius = int(radius)
        img = cv2.circle(img, center, radius, green, 2)
    except IndexError:
        pass
    cv2.imshow('img', img)
