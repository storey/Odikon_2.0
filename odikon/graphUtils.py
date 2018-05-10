# -*- coding: utf-8 -*-
# Code for getting the various results

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import odikon.utils as utils

# Given two datasets, graph them as bar charts.
# Optionally save the output in a specified location
# adapted from matplotlib code
def graphPcts(data, data2, tickLabels, title, axLabel, saveDir, saveName, saveOutput):
    ind = np.arange(len(data))  # the x locations for the groups
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects = ax.bar(ind, data, width, label="System Output")
    rects2 = ax.bar(ind + width, data2, width, label="Ceadel 1941")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel(axLabel)
    ax.set_title(title)

    plt.xticks(ind + (width/2), tickLabels, rotation="vertical", fontsize=8)

    # display bar's heights
    def autolabel(rects, xpos='center'):
        xpos = xpos.lower()  # normalize the case of the parameter
        ha = {'center': 'center', 'right': 'left', 'left': 'right'}
        offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

        for rect in rects:
            height = rect.get_height()
            barText = "%.2f" % height
            ax.text(rect.get_x() + rect.get_width()*offset[xpos], 1.01*height,
                    barText, ha=ha[xpos], va='bottom', fontsize=6)


    autolabel(rects, "center")
    autolabel(rects2, "center")

    ax.legend()

    if saveOutput:
        fig.set_size_inches((11.), (8.5))
        filename = saveDir + saveName + ".pdf"
        utils.check_and_create_path(filename)
        pp = PdfPages(filename)
        pp.savefig()
        pp.close()
    else:
        plt.show()
    plt.close()
