"""another example analysis script"""

import matplotlib.pyplot as plt
import json
import sys
sys.path.append("/Users/zacharyandalman/PycharmProjects/analysis")
import seneca_analysis

old_data, paths = seneca_analysis.parse_options()

def read(paths):
    new_cpu_data = []
    for path in paths:
        with open(path) as file:
            data = json.load(file)
        new_cpu_data += [float(x) for x in data['cpu']]
    return new_cpu_data

def update_data(old_data, new_cpu_data):
    old_data['cpu'] += new_cpu_data
    return old_data

@seneca_analysis.plot
def cpu_percentage(cpu):
    x = range(len(cpu))
    plt.plot(x, cpu)
    plt.xlim(max(0, len(cpu) - 50), len(cpu) + 50)
    plt.ylabel("cpu percentage")

if __name__ == "__main__":
    new_cpu_data = read(paths)
    full_data = update_data(old_data, new_cpu_data)
    cpu_percentage(full_data["cpu"])
    seneca_analysis.write_data(full_data)