import cv2
import math
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


def has_full_obj(circle):
    if circle == None:
        return False
    (x,y), radius = circle
    if x - radius < 0 or x + radius > width:
        return False
    if y - radius < 0 or y + radius > height:
        return False
    return True
          

video = cv2.VideoCapture("{}.mp4".format(video_name))
fps = video.get(cv2.CAP_PROP_FPS)
width  = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
size = (width, height)
    
success, img = video.read()
frames = []
obj_arrs = []
circles = []


# create images from video
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


# create video
if True:
    print("Creating avi video...")
    out_format = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter("{}_processed.avi".format(video_name), out_format, fps, size)
    out_slow = cv2.VideoWriter("{}_processed_slow.avi".format(video_name), out_format, fps / 8, size)
    for f in frames:
        out.write(f)
        out_slow.write(f)
    out.release()
    out_slow.release()


# add disc tracking to frames
print("Disc tracking...")

for img in frames:
    img_bw = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(img_bw, 127, 255, cv2.THRESH_BINARY)
    contour, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    try:
        circles.append(cv2.minEnclosingCircle(contour[-1]))
    except Exception:
        circles.append(None)

frames_with_obj = [i for i in range(len(circles)) if has_full_obj(circles[i])]


# velocity calcs
feet_per_pixel = img_width_feet / width

first_frame = frames_with_obj[0]
last_frame = frames_with_obj[-1]
movement_frames = last_frame - first_frame

x_movement = (circles[last_frame][0][0] - circles[first_frame][0][0])
y_movement = (circles[last_frame][0][1] - circles[first_frame][0][1])

total_movement = math.sqrt((x_movement ** 2) + (y_movement ** 2))
total_velocity = total_movement / movement_frames

pixels_per_second = total_velocity * fps
feet_per_second = pixels_per_second * feet_per_pixel

# see images with disc tracking
if True:
    for i in frames_with_obj:
        (x,y), radius = circles[i]
        center = (int(x), int(y))
        radius = int(radius)
        img = cv2.circle(cv2.imread("frames/frame_{}.jpg".format(i)), center, radius, green, 2)
        cv2.imshow("Disc Tracking", img)
        cv2.waitKey()
    cv2.destroyAllWindows()
