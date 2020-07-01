
# module docstring and plot function doc strings will appear in GUI
"""example analysis script"""
# import modules
import json
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
import sys
# temporary solution: add app to path for importing seneca_analysis.py
sys.path.append("/Users/zacharyandalman/PycharmProjects/analysis")
import seneca_analysis
# required to get paths to data files and dictionary with data from previous measurements
old_data, paths = seneca_analysis.parse_options()


# read data from path
def read(path):
    with open(path) as file:
        data = json.load(file)
    data['x'] = [float(x) for x in data['x']]
    data['y'] = [float(y) for y in data['y']]
    return data


# linear function
def line(x, a, b):
    return a * x + b


# exponential function
def expon(x, a, b):
    return a * b ** x


# update data from previous measurements with new measurement
def update_data(old_data, new_data):
    old_data['x'] += new_data['x']
    old_data['y'] += new_data['y']
    return old_data


# do a linear fit
@seneca_analysis.plot
def linear_fit(x, y):
    """linear fit to the data"""
    x_smooth = np.linspace(min(x), max(x), 100)
    popt, pcov = curve_fit(line, x, y)
    plt.plot(x, y, 'o', color='C0')
    plt.plot(x_smooth, line(x_smooth, *popt), '--', color='C0')
    plt.title("linear fit")
    uncertainty = np.sqrt(np.diag(pcov))
    return dict(a=popt[0], a_=uncertainty[0], b=popt[1], b_=uncertainty[1])


# do an exponential fit
@seneca_analysis.plot
def exponential_fit(x, y):
    """exponential fit to the data"""
    x_smooth = np.linspace(min(x), max(x), 100)
    popt, pcov = curve_fit(expon, x, y)
    plt.plot(x, y, 'o', color='C0')
    plt.plot(x_smooth, expon(x_smooth, *popt), '--', color='C0')
    plt.title("exponential fit")
    uncertainty = np.sqrt(np.diag(pcov))
    return dict(a=popt[0], a_=uncertainty[0], b=popt[1], b_=uncertainty[1])


# plot a histogram of the x and y values
@seneca_analysis.plot
def hist(x, y):
    """histogram"""
    fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
    axs[0].hist(x, bins=20)
    axs[0].set_title("x")
    axs[1].hist(y, bins=20)
    axs[1].set_title("y")


# plots must be called inside if __name__ == "__main__"
if __name__ == "__main__":
    data = read(paths[0])
    full_data = update_data(old_data, data)
    # do plots
    linear_fit(data["x"], data["y"])
    exponential_fit(data["x"], data["y"])
    hist(full_data["x"], full_data["y"])
    # write updated data so it can be read back later
    seneca_analysis.write_data(full_data)
