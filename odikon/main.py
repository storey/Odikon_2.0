# The main portal for accessing Odikon's functions. 
import odikon.scan as scanner
import numpy as np


# given a line and a meter, attempt to scan that line
def scanLine(line, meter):
    return scanner.scanLine(line, meter)

# return true if this line should be skipped because it is just an exclamation
def skipLine(line):
    return scanner.skipLine(line)

# get a textual representation of a scansion
def getScanString(scan):
    return scanner.getScanString(scan)

# given a single line, guess the meter
def guessMeter(line):
    m, p = scanner.guessMeterWithParse(line)

    return m

# given a list of meter sections, find single lines with the
# same meter on either side and convert them to that meter.
def removeUnitRuns(runs):
    if len(runs) < 2:
        return runs

    newRuns = []
    used = np.zeros((len(runs)))

    for i in range(0, len(runs) - 2):
        if used[i] == 1:
            continue

        currentRun = runs[i]
        nextRun = runs[i+1]
        nextNextRun = runs[i+2]

        # if the next item is a unit and the on after is the same type as this one,
        # merge all three
        if nextRun["start"] == nextRun["end"] and nextNextRun["type"] == currentRun["type"]:
            used[i+1] = 1
            runs[i+2] = {"start": currentRun["start"], "end": nextNextRun["end"], "type": currentRun["type"]}
        else:
            newRuns.append(currentRun)

    if not used[len(runs)-2]:
        newRuns.append(runs[len(runs)-2])
    if not used[len(runs)-1]:
        newRuns.append(runs[len(runs)-1])

    return newRuns

# given a set of lines, guess sections of our various meters
def guessMeterSections(lines):
    lineGuesses = []
    for line in lines:
        typeGuess = guessMeter(line)
        lineGuesses.append([typeGuess, line["line_number"]])

    runs = []
    currentRun = {"type": None}
    for lg in lineGuesses:
        if (lg[0] == currentRun["type"]):
            currentRun["end"] = lg[1]
        else:
            runs.append(currentRun)
            currentRun = {"start": lg[1], "end": lg[1], "type": lg[0]}
    runs.append(currentRun)
    # remove dummy first run
    runs = runs[1:]

    runs2 = removeUnitRuns(runs)

    return runs, runs2
