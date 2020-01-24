from sympy import S, symbols, printing
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import glob
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 150
sns.set_style('white')

# Add a column to dataframe with seconds instead of a timestamp
def timestamp_to_seconds(timestamp):
    totalseconds = 0
    timestamp2 = timestamp.split(":")
    totalseconds += (int(timestamp2[1]) + (int(timestamp2[0]) * 60))
    return totalseconds

# Runs conduction heat transfer equation
def conduction(roadtemp, shell_starting_temp, size):
    roadtemp += 273 # Kelvin
    t = 1 # seconds
    k = 0.1934 # W/mK
    T1 = shell_starting_temp + 273 # Kelvin
    if size.lower() == "small": 
        d = 0.004 # m
        A = (6542 * (10**-6)) * 0.642 # m^2
    elif size.lower() == "medium":
        d = 0.0050 # m
        A = (9346 * (10**-6)) * 0.590 # m^2
    return k*A*t*((roadtemp-T1)/d) # Return J transferred in that second

# q = mcat, q in Joules
def tempraised(q, size):
    if size.lower() == "small":
        m = 22.5 # g
    elif size.lower() == "medium":
        m = 36.944 # g
    c = 1.53 # j/g/C
    return q / (m*c) # Returns temperature raised (degrees)

# Uses result from tempraised to make a list of temps
def combine(roadtemp, seconds, start, size):
    temps = [start]
    for x in range(0, seconds):
        shelltemp = temps[x]
        temps.append(shelltemp + tempraised(conduction(roadtemp, shelltemp, size), size))
    return temps

# Returns average percent error over 2 lists
def error(theoretical, experimental):
    theoretical = np.array(theoretical)
    experimental = np.array(experimental)
    differences = (experimental - theoretical) / experimental
    differences = abs(differences)
    return str(round(np.average(differences) * 100, 3))

def graphcsv(file):
    # Read initial file with data
    data = pd.read_csv("%s" % file)
    
    # Change timestamps to seconds
    data_secondslist = []
    for x in data["Timestamp"]:
        data_secondslist.append(timestamp_to_seconds(x))
    data["Seconds"] = data_secondslist
    size = data["Size"][0]
    startingtemp = data["Starting Temp"][0]

    # Set x and y parameters
    xdata = np.array(data["Seconds"])
    ydata = np.array(data["Temperature"])

    # Get the equation fitted to a 2nd order polynomial
    p = np.polyfit(xdata, ydata, 2) # Coefficients
    f = np.poly1d(p) # The equation

    # Format equation for display
    # Calculate new x and y
    x_new = np.linspace(xdata[0], xdata[-1], max(xdata)+1)
    y_new = f(x_new)
    x = symbols("x")
    poly = sum(S("{:6.6f}".format(v))*x**i for i, v in enumerate(p[::-1]))
    eq_latex = printing.latex(poly)

    # Get theoretical data from the x and y data 
    theoretical = combine(startingtemp, max(xdata), min(y_new), size)

    # Plot the experimental data
    p1 = sns.lineplot(xdata, ydata, color='cornflowerblue', label="Experimental")
    # Plot the best fit curve
    sns.lineplot(x_new, y_new, label="${}$".format(eq_latex), color='forestgreen')
    
    # Plot the theoretical data
    sns.lineplot(np.arange(len(theoretical)), theoretical, color='red', label="Theoretical")

    # Add text with the percent error
    p1.text(max(x_new) - 150, min(y_new) + 2, "Avg. % Error: " + error(theoretical, y_new), 
            horizontalalignment='left', size='medium', color='black')
    
    plt.legend(fontsize="small")
    plt.xlabel("Time Elapsed (seconds)")
    plt.ylabel("Internal Temperature (°C)")
    plt.title("%s, %s°C" % (size, startingtemp))
    plt.tight_layout
    sns.despine()
    plt.savefig("%s" % file[:-4], dpi=600)
    plt.close()
    
# Performs function on every data file
for file in glob.glob("data/*.csv"):
    graphcsv(file)
