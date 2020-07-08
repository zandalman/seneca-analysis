
import sys
sys.path.append("/Users/zacharyandalman/PycharmProjects/analysis")
import seneca_analysis
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
from scipy.optimize import curve_fit

def line(x, a, b):
    return a * x + b

@seneca_analysis.plot()
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
    return dict(a=popt[0], a_=uncertainty[0], b=popt[1], b_=uncertainty[1])

if __name__ == "__main__":
    x, y = np.random.random(3).tolist(), np.random.random(3).tolist()
    while True:
        x.append(np.random.random(1)[0])
        y.append(np.random.random(1)[0])
        linear_fit(x, y)
        sleep(.1)