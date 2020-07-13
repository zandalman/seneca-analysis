
import sys
sys.path.append("/Users/zacharyandalman/PycharmProjects/analysis")
import seneca_analysis
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
from scipy.optimize import curve_fit

seneca_analysis.app_root_path = "/Users/zacharyandalman/PycharmProjects/analysis"

def line(x, a, b):
    return a * x + b

def linear_fit(x, y):
    """linear fit to the data"""
    x_smooth = np.linspace(min(x), max(x), 100)
    popt, pcov = curve_fit(line, x, y)
    plt.plot(x, y, 'o', color='C0')
    plt.plot(x_smooth, line(x_smooth, *popt), '--', color='C0')
    plt.title("linear fit")
    plt.xlabel("x")
    plt.ylabel("y")
    uncertainty = np.sqrt(np.diag(pcov))
    return dict(a=round(popt[0], 3), a_=round(uncertainty[0], 3), b=round(popt[1], 3), b_=round(uncertainty[1], 3))

if __name__ == "__main__":
    x, y = np.random.random(3).tolist(), np.random.random(3).tolist()
    while True:
        x.append(np.random.random(1)[0])
        y.append(np.random.random(1)[0])
        data = linear_fit(x, y)
        seneca_analysis.send_current_plot("linear fit")
        seneca_analysis.send_table("fit parameters", data)
        seneca_analysis.send_image("me", "/Users/zacharyandalman/Documents/ZLA_ID_Photo.jpg")
        sleep(.1)
        seneca_analysis.end_loop()