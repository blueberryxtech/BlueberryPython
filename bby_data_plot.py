import matplotlib.pyplot as plt
import matplotlib
matplotlib.axes.Axes.legend
matplotlib.pyplot.legend
import pandas as pd
import numpy as np
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--filename", help="filename and location of csv to plot", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.filename)

    ts = df.loc[df["path"] == "long_path"]["timestamp"].to_numpy()
    d = 0
    lt = None
    ds = list()
    for t in ts:
        if lt != None:
            d = t - lt
            ds.append(d)
        lt = t
    avg_sf = (1 / np.mean(ds) )
    print("The average sampling rate is: {}".format(avg_sf))
        
    path_tmp = "long_path"
    tmp = df.loc[df['path'] == path_tmp]
    l_c1 = tmp["c1"].to_numpy()
    l_c2 = tmp["c2"].to_numpy()
    l_c3 = tmp["c3"].to_numpy()
    path_tmp = "short_path"
    tmp = df.loc[df['path'] == path_tmp]
    s_c1 = tmp["c1"].to_numpy()
    s_c2 = tmp["c2"].to_numpy()
    s_c3 = tmp["c3"].to_numpy()

    fig, axs = plt.subplots(2,1, sharex=True)
    #plot long
    axs[0].plot(l_c1, label="740")
    axs[0].plot(l_c2, label="850")
    axs[0].plot(l_c3, label="880")
    axs[0].set_title("LONG PATH")
    legend = axs[0].legend(loc='upper left', shadow=True, fontsize='x-large')
    #plot short
    axs[1].plot(s_c1, label="740")
    axs[1].plot(s_c2, label="850")
    axs[1].plot(s_c3, label="880")
    axs[1].set_title("SHORT PATH")
    legend = axs[1].legend(loc='upper left', shadow=True, fontsize='x-large')
    plt.show()
