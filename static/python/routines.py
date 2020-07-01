import matplotlib.pyplot as plt
from io import BytesIO
import base64

def plot(func):
    def plot_wrapper(*args, **kwargs):
        plt.clf()
        func(*args, **kwargs)
        img = BytesIO()
        plt.savefig(img)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        return plot_url
    return plot_wrapper