import cv2
import math
import numpy as np
import queue
import time


blue = [255, 0, 0]
green = [0, 255, 0]
red = [0, 0, 255]

pink_disc_color = [131, 83, 193]
green_disc_color = [143, 196, 133]


class Pixel:
    def __init__(self, color, comparison_color, x, y, tolerance=10):
        self.color = tuple(color)
        self.comparison_color = comparison_color
        self.x = x
        self.y = y
        self.coord = (y, x)
        self.tolerance = tolerance

    def get_color_diff(self):
        total = 0
        for i in range(3):
            total += abs(int(self.color[i]) - int(self.comparison_color[i]))
        return total

    def is_similar(self):
        for i in range(3):
            if abs(int(self.color[i]) - int(self.comparison_color[i])) > self.tolerance:
                return False
        return True


class ObjectFinder:
    q = queue.Queue()
    checked = []

    def __init__(self, img, color, granularity=4, tolerance=10):
        self.img = img
        self.img_h, self.img_w, self.channels = img.shape
        self.color = color
        self.granularity = granularity
        self.tolerance = tolerance
        self.start_tolerance = tolerance * 2

    def add_all_adjacent(self, pixel):
        diff_range = [0, self.granularity, -self.granularity]
        for i in diff_range:
            new_y = pixel.y + i
            for j in diff_range:
                new_x = pixel.x + j
                new_coord = (new_y, new_x)
                if new_coord not in self.checked and abs(new_x) < self.img_w and abs(new_y) < self.img_h:
                    new_color = self.img[new_y, new_x][:3]
                    self.q.put(Pixel(new_color, pixel.color,
                                     new_x, new_y, self.tolerance))
                    self.checked.append(new_coord)

    def get_most_similar(self, x_range, y_range):
        for i in range(y_range):
            for j in range(x_range):
                p = Pixel(self.img[i, j], self.color,
                          i, j, self.start_tolerance)
                if p.is_similar():
                    return p.coord
        return None

    def get_disc_coords(self):
        try:
            y, x = self.get_most_similar(self.img_w, self.img_h)
        except Exception:
            return []
        color = self.img[y, x][:3]
        self.q.put(Pixel(color, color, x, y, self.tolerance))
        disc_coords = []
        while not self.q.empty():
            p = self.q.get()
            if p.is_similar():
                disc_coords.append(p.coord)
                self.add_all_adjacent(p)
        return disc_coords


granularity = 10
threshold = 10
draw_color = blue


def draw_on_image(img, coords, draw_color, granularity):
    if granularity > 2:
        for y, x in coords:
            for i in range(int(math.log(granularity, 2))):
                for j in [0, 1, -1]:
                    for k in [0, 1, -1]:
                        try:
                            img[y+(i+1)*j, x+(i+1)*k] = draw_color
                        except Exception:
                            pass
    else:
        for y, x in coords:
            img[y, x] = draw_color


img = cv2.imread('disc_green.jpg')

o = ObjectFinder(img, green_disc_color, granularity, threshold)
disc_coords = o.get_disc_coords()

b, g, r = [], [], []
for y, x in disc_coords:
    color = img[y, x]
    b.append(color[0])
    g.append(color[1])
    r.append(color[2])

img_result = img.copy()
draw_on_image(img_result, disc_coords, draw_color, granularity)

cv2.imshow('disc', img_result)
   
