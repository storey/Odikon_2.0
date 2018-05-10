# Main file for running some example analyses using odikon.

import odikon.utils as utils
import odikon.graphUtils as graphUtils
import odikon.main as odikon

import numpy as np

# True if we want to analyze test results
RUN_TEST = True


# helper function for printing out sections
def getSectionsString(sections):
    s = []
    for sec in sections:
        s.append("  %.1f-%.1f: %s" % (sec["start"], sec["end"], sec["type"]))
    return "\n".join(s)

# helper function to check if two scans match
def scansMatch(scan1, scan2):
    if not(len(scan1) == len(scan2)):
        return False
    for i in range(len(scan1)):
        c1 = scan1[i]
        c2 = scan2[i]
        match = (c1 == c2) or ((c1 == "v" or c1=="-") and c2 == "x")

        if not(match):
            return False
    return True

# helper function to take partially completed list of sections and fill it out
def fillOutSections(correctSections):
    correctSectionsFull = []
    truthSectionIndex = 0
    currentTruthSection = None
    nextTruthSection = correctSections[0]
    inSection = False
    lastLine = -1

    for line in book.bookLines:
        lineNum = line["line_number"]


        if lineNum == nextTruthSection["start"]:
            if not(currentTruthSection == None) and currentTruthSection["type"] == "OTHER":
                currentTruthSection["end"] = lastLine
            inSection = True
            correctSectionsFull.append(currentTruthSection)
            currentTruthSection = nextTruthSection

        if not(inSection):
            inSection = True
            correctSectionsFull.append(currentTruthSection)
            currentTruthSection = {"start": lineNum, "end": -1, "type": "OTHER"}

        if (lineNum == currentTruthSection["end"]):
            truthSectionIndex += 1
            if (truthSectionIndex < len(correctSections)):
                nextTruthSection = correctSections[truthSectionIndex]
            inSection = False

        lastLine = lineNum

    if not(currentTruthSection == None) and currentTruthSection["type"] == "OTHER":
        currentTruthSection["end"] = lastLine
    correctSectionsFull.append(currentTruthSection)

    if correctSectionsFull[0] == None:
        correctSectionsFull = correctSectionsFull[1:]

    return correctSectionsFull

# given correct and guessed metrical sections in a text, evaluate the
# accuracy of the guesses.
def evaluateIdentify(correctSections, guessSections, name):
    truthSectionIndex = 0
    guessSectionIndex = 0
    currentTruthSection = correctSections[0]
    currentGuessSection = guessSections[0]

    numCorrect = 0
    numTotal = 0
    mistakes = []

    for line in book.bookLines:
        lineNum = line["line_number"]

        if not(odikon.skipLine(line)):
            numTotal += 1
            if (currentTruthSection["type"] == currentGuessSection["type"]):
                numCorrect += 1
            else:
                mistakes.append((textName, lineNum, currentGuessSection["type"], currentTruthSection["type"]))

        if (lineNum == currentTruthSection["end"]):
            truthSectionIndex += 1
            if truthSectionIndex < len(correctSections):
                currentTruthSection = correctSections[truthSectionIndex]

        if (lineNum == currentGuessSection["end"]):
            guessSectionIndex += 1
            if guessSectionIndex < len(guessSections):
                currentGuessSection = guessSections[guessSectionIndex]


    # Return line-by-line errors to be saved to a file or printed
    res = []
    accString = "%s %s %s\nAccuracy: %f%% (%d/%d)\n----" % (a, textName, name, (numCorrect*100.0/numTotal), numCorrect, numTotal)
    print(accString)
    res.append(accString)
    res.append("Guessed Sections:")
    res.append(getSectionsString(mySections))
    res.append("Correct Sections:")
    res.append(getSectionsString(correctSections))
    res.append("----")
    res.append("Mistakes:")
    for mistake in mistakes:
        res.append("%s %.1f: guess: %s, correct: %s" % mistake)
    res.append("------")

    return res

# ==== load author data
available = utils.getContent("data/texts/available.json", True)
books = []
for o in available:
    authorName = o["author"]
    a = utils.Author(authorName)

    workLocs = o["works"]
    works = []
    for w in workLocs:
        t = utils.Text("data/" + w["location"])

        for b in t.books:
            books.append(b)

bookLookup = {}
for book in books:
    name = book.textName
    author = book.author

    if not(author in bookLookup):
        bookLookup[author] = {}

    bookLookup[author][name] = book


# ==== run tests on dev and test scansions of lines
# load our dev and test files
scan_dev = utils.getContent("data/evaluation/scansion_dev.json", True)
scan_test = utils.getContent("data/evaluation/scansion_test.json", True)

scanSets = [
    [scan_dev, "Dev"],
    [scan_test, "Test"]
]

if not(RUN_TEST):
    scanSets = scanSets[:1]

# run tests and compare results to the final results
scanReport = []

for scanSet in scanSets:
    myTests = scanSet[0]
    myName = scanSet[1]

    correctNum = 0
    totalNum = 0
    errors = []
    for test in myTests:
        a = test["author"]
        textName = test["text"]
        lineNum = test["line"]
        meter = test["meter"]
        correctScan = test["scan"]

        book = bookLookup[a][textName]
        targetLine = None
        for line in book.bookLines:
            if (line["line_number"] == lineNum):
                targetLine = line
                break

        myScan = odikon.getScanString(odikon.scanLine(targetLine, meter))

        correct = scansMatch(myScan, correctScan)

        totalNum += 1
        if (correct):
            correctNum += 1
        else:
            s = "  %s: %s line %.1f. Should be '%s', was '%s'" % (a, textName, lineNum, correctScan, myScan)
            errors.append(s)

    accString = "Accuracy: %f (%d/%d)" % ((100.0*correctNum/totalNum), correctNum, totalNum)

    scanReport.append("%s Scansion Results:" % (myName))
    scanReport.append(accString)
    scanReport.append("Errors:")
    scanReport.extend(errors)
    scanReport.append("=====")

    print(myName + " " + accString)
    print("----")

utils.safeWrite("output/scanReport.txt", "\n".join(scanReport))



# ==== guess which sections of the text are in various meters
id_dev = utils.getContent("data/evaluation/identify_dev.json", True)
id_test = utils.getContent("data/evaluation/identify_test.json", True)

idSets = [
    [id_dev, "Dev"],
    [id_test, "Test"]
]

if not(RUN_TEST):
    idSets = idSets[:1]

# report our guessed boundaries and accuracy
idReport = []

for idSet in idSets:
    myTests = idSet[0]
    myName = idSet[1]


    for test in myTests:
        a = test["author"]
        textName = test["text"]
        book = bookLookup[a][textName]

        correctSections = fillOutSections(test["sections"])

        mySections, mySections2 = odikon.guessMeterSections(book.bookLines)

        baselineSections = [{
            "start": mySections[0]["start"],
            "end": mySections[-1]["end"],
            "type": "IAMBS"
        }]
        res = evaluateIdentify(correctSections, baselineSections, "Baseline")
        idReport.extend(res)

        res = evaluateIdentify(correctSections, mySections, "No Cleanup")
        idReport.extend(res)

        res = evaluateIdentify(correctSections, mySections2, "Cleanup")
        idReport.extend(res)

    idReport.append("=====")

utils.safeWrite("output/idReport.txt", "\n".join(idReport))


# ==== Analyzing resolution in the plays of Euripides
# for each play of euripides
plays = []
for book in books:
    if (book.author == "Euripides"):

        # try to scan every line as iambs; for those that scan, calculate
        # resolution percentage
        totalTrimiters = 0
        resolvedIambs = 0
        resolvedIambsNoProper = 0

        lines = book.bookLines
        for line in lines:
            bestParse = odikon.scanLine(line, "IAMBS")
            if not(bestParse == None):
                v = bestParse['vec']
                totalTrimiters += 1
                resolvedIambs += v[0]
                resolvedIambsNoProper += v[0] - v[5]

        freq = resolvedIambs/totalTrimiters

        # save play, percentage pair
        plays.append([book.textName, freq])

# add in ground truth data from Ceadel 1941
playsGroundTruth = [
    (53.0/802),
    (150.0/936),
    (400.0/918),
    (244.0/585),
    (207.0/960),
    (181.0/920),
    (446.0/1253),
    (68.0/888),
    (228.0/984),
    (62.0/987),
    (289.0/1045),
    (354.0/816),
    (316.0/1074),
    (75.0/1037),
    (561.0/1134),
    (406.0/1164),
    (64.0/682),
    (157.0/915),
    (213.0/794)
]
for i in range(len(plays)):
    plays[i].append(playsGroundTruth[i])

# sort plays by percentage
sortedPlays = sorted(plays, key=lambda x: x[1])

# Display the results in a chart
textList = []
names = []
pcts = []
pctsGroundTruth = []
sumError = 0
for p in sortedPlays:
    pct = 100*p[1]
    pct2 = 100*p[2]
    sumError += abs((pct - pct2)/pct2)
    textList.append("%s: %.2f%%" % (p[0], pct))

    names.append(p[0])
    pcts.append(pct)
    pctsGroundTruth.append(pct2)

print("Average error compared to ground truth: %f%%" % (100.0*sumError/len(sortedPlays)))

utils.safeWrite("output/resolutionReport.txt", "\n".join(textList))



title = 'Plays Ordered by Resolution Percentage'
axLabel = 'Resolution Percentage'

# Shorten some names for display
shortNames = []
for name in names:
    if (name == "Iphigenia in Aulis"):
        shortNames.append("Aulis")
    elif (name == "Iphigenia in Tauris"):
        shortNames.append("Tauris")
    else:
        shortNames.append(name)

saveDir = "output/"
saveName = "resolutions"
saveOutput = True
graphUtils.graphPcts(pcts, pctsGroundTruth, shortNames, title, axLabel, saveDir, saveName, saveOutput)
