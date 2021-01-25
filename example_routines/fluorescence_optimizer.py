# -*- coding: utf-8 -*-

import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
import time
from random import randint
from matplotlib.animation import FuncAnimation
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import Axes3D
import statistics
from pymba import Vimba, VimbaException
from _display_frame import display_frame

# Import seneca analysis
import sys
sys.path.append("/Users/zacharyandalman/PycharmProjects/analysis")
import seneca_analysis

# Set analysis app root path
seneca_analysis.app_root_path = "/Users/zacharyandalman/PycharmProjects/analysis"

class Analyze():
    def __init__(self, img, region, background=""):
        self.img = img
        if background:
            self.background = background
            self.img = self.img - self.background
        self.region = region
        self.ROI = self.img[region['left_bottom'][1]:region['left_bottom'][1] + region['height'],
                   region['left_bottom'][0]:region['left_bottom'][0] + region['width']]
        self.total = np.sum(self.ROI)

    def display_image(self, figure):
        ax1 = fig.add_subplot(223)
        ax1.imshow(self.img, interpolation='none', cmap=plt.get_cmap('bwr'))
        ax1.set_title("Full image")
        ax1.set_autoscale_on(False)
        rectangle = plt.Rectangle(self.region['left_bottom'],
                                  self.region['width'],
                                  self.region['height'],
                                  edgecolor="green", facecolor='none')
        ax1.add_patch(rectangle)

        ax2 = fig.add_subplot(224)
        ax2.imshow(self.ROI, interpolation='none', cmap=plt.get_cmap('bwr'))
        ax2.set_title("Region of interest")
        ax2.set_autoscale_on(False)


def capture_image():
    with Vimba() as vimba:
        camera = vimba.camera(0)
        camera.open()

        camera.arm('SingleFrame')

        # capture a single frame, more than once if desired
        try:
            data = camera.acquire_frame()
            # display_frame(data, 0)
            camera.disarm()
            camera.close()
            # print("Image captured.")
            return data
        except VimbaException as e:
            # rearm camera upon frame timeout
            if e.error_code == VimbaException.ERR_TIMEOUT:
                print(e)
                camera.disarm()
                camera.arm('SingleFrame')
            else:
                raise


def get_bool(prompt):
    response = input(prompt)
    if response.lower() == "y":
        return True
    elif response.lower() == "n":
        return False
    else:
        print("Invalid input please enter 'Y' or 'N'!")
        raise KeyError


def test_image():
    img_path = 'fluorescence.jpg'
    return cv2.imread(img_path, 0)


if __name__ == '__main__':
    ROI_settings = {"left_bottom": (515, 350),
                    "height": 150,
                    "width": 200
                    }
    most_recent = 10  # number of most recent images to calculate maximum
    while True:
        question = "Please prepare the background image. Is it ready to go? (Y/N) \n"
        camera_ready = get_bool(question)

        if camera_ready == True:
            print("Background ready!")
            background = test_image()
            break
        else:
            print("Ignoring background.")
            break

    print("Fluorescence optimizer initiated.")
    fig = plt.figure()
    counts = []
    # Initialize analysis object
    analysis = seneca_analysis.Analysis()
    while True:
        testdata = np.random.normal(randint(100, 200), randint(20, 50), 321) + test_image().sum(axis=0)
        plt.clf()
        capture = capture_image()
        image = capture.buffer_data_numpy()
        test = Analyze(image, ROI_settings)
        test.display_image(fig)

        counts.append(test.total)

        if np.array(counts).size > 100:
            counts.pop(0)

        xaxis = np.arange(0., np.array(counts).size, 1)
        ax1 = fig.add_subplot(211)
        ax1.plot(xaxis, np.array(counts), 'b-')
        avg_count = statistics.mean(counts[-most_recent:])
        results = "3D MOT count: {} (last {} images)".format(avg_count, most_recent)
        ax1.set_title(results,
                      fontdict={'fontsize': 40,
                                'fontweight': 'medium'
                                }
                      )
        # Send current figure to analysis app
        analysis.plot("fluorescence optimizer")
        plt.pause(0.01)
        # Send plots to analysis app
        analysis.send()
    # End analysis
    analysis.end()