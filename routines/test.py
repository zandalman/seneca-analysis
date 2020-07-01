"""example analysis script one"""
import json
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
import sys

sys.path.append("/Users/zacharyandalman/PycharmProjects/analysis")
import seneca_analysis

old_data, paths = seneca_analysis.parse_options()

def read(path):
    with open(path) as file:
        data = json.load(file)
    data['x'] = [float(x) for x in data['x']]
    data['y'] = [float(y) for y in data['y']]
    return data

def line(x, a, b):
    return a * x + b

def expon(x, a, b):
    return a * b ** x

def update_data(old_data, new_data):
    old_data['x'] += new_data['x']
    old_data['y'] += new_data['y']
    return old_data

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

@seneca_analysis.plot
def hist(x, y):
    """histogram"""
    fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
    axs[0].hist(x, bins=20)
    axs[1].hist(y, bins=20)

if __name__ == "__main__":
    data = read(paths[0])
    full_data = update_data(old_data, data)
    linear_fit(data["x"], data["y"])
    exponential_fit(data["x"], data["y"])
    hist(full_data["x"], full_data["y"])
    seneca_analysis.write_data(full_data)