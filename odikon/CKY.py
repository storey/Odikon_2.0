# Implementation of CKY, with automatic conversion of a grammar to CNF and weights included.
import copy
import uuid

import numpy as np

# ===========================================================================
# ============================= CNF Conversion ==============================
# ===========================================================================

# add memory info to a lexicon and grammar
# Memory consists of two pieces; a list of unit productions that produced
# this production, and boolean that is True if the right child is an
# extra rule created to make the current rule binary-branching
def cnfAddMemory(lex, gram):
    newLex = {}
    for key in lex:
        newLex[key] = []
        for prod in lex[key]:
            sym, weight = prod
            mem = [[], False]
            newProd = (sym, weight, mem)
            newLex[key].append(newProd)

    newGram = []
    for prod in gram:
        sym, children, weight = prod
        mem = [[], False]
        newProd = (sym, children, weight, mem)
        newGram.append(newProd)

    return newLex, newGram

# remove unitary productions
def cnfRemoveUnits(lex, gram, lexMap=None):
    # build a map from symbols to lexicon entries
    if (lexMap == None):
        lexMap = {}
        for val in lex:
            for i, prod in enumerate(lex[val]):
                sym, _, _ = prod
                if not(sym in lexMap):
                    lexMap[sym] = []
                entry = [val, i]
                lexMap[sym].append(entry)

    foundUnit = False
    newLex = []
    newGram = []
    targetUnit = None

    # iterate through the grammar looking for a unit production
    for prod in gram:
        _, children, _, _ = prod
        if not(foundUnit) and (len(children) == 1):
            foundUnit = True
            targetUnit = prod
        else:
            newGram.append(prod)

    # if there are no unit productions, we return the lexicon and grammar
    if (not(foundUnit)):
        return lex, gram

    # if there is at least one unit production, we remove the first one we find.

    # given our target unit production A->B, go through the grammar and find
    # Every production from B->?, add a production from A->?
    tsym, tchildren, tweight, tmem = targetUnit
    tchild = tchildren[0]

    for prod in gram:
        sym, children, weight, mem = prod
        if sym == tchild:
            newWeight = tweight + weight

            # we need to concatenate the child's memory, then this symbol,
            # then the parent symbols
            memChain = copy.deepcopy(mem[0])
            memChain.append(sym)
            memChain.extend(tmem[0])
            newMem = [memChain, mem[1]]

            newProd = (tsym, children, newWeight, newMem)
            newGram.append(newProd)

    # go through the lexicon and add unit productions to that where necessary
    if tchild in lexMap:
        for entry in lexMap[tchild]:
            val, index = entry
            sym, weight, mem = lex[val][index]

            newWeight = tweight + weight

            # we need to concatenate the child's memory, then this symbol,
            # then the parent symbols
            memChain = copy.deepcopy(mem[0])
            memChain.append(sym)
            memChain.extend(tmem[0])
            newMem = [memChain, mem[1]]

            newProd = (tsym, newWeight, newMem)
            newProdIndex = len(lex[val])

            lex[val].append(newProd)
            if not(tsym) in lexMap:
                lexMap[tsym] = []
            lexMap[tsym].append([val, newProdIndex])

    # recursively call this function to remove any new unit productions
    return cnfRemoveUnits(lex, newGram, lexMap)

# given a production, produce a list of productions where each has
# two children. We also keep track of how many new symbols we create.
def getTwoChildProductions(prod, newSymIndex):
    newProds = []
    sym, children, weight, mem = prod

    prefix = "&#_%d"

    lastSym = sym
    for i in range(0, len(children)-2):
        newSym = prefix % (newSymIndex + i)
        newWeight = np.zeros(weight.shape)
        if (i == 0):
            newMem = [mem[0], True]
        else:
            newMem = [[], True]
        newProd = (lastSym, [children[i], newSym], newWeight, newMem)
        newProds.append(newProd)

        lastSym = newSym

    last = (lastSym, [children[-2], children[-1]], weight, [[], False])
    newProds.append(last)

    return newProds, (newSymIndex + len(children)-2)

# remove productions with more than 2 children
def cnfRemoveLongs(gram):
    newGram = []
    newSymIndex = 0
    for prod in gram:
        sym, children, weight, mem = prod
        if len(children) > 2:
            newProds, newSymIndex = getTwoChildProductions(prod, newSymIndex)
            newGram.extend(newProds)
        else:
            newGram.append(prod)

    return newGram

# convert all productions to have a left and right child rather than
# a list of two children
def cnfFlattenChildren(gram):
    newGram = []
    newSymIndex = 0
    for prod in gram:
        sym, children, weight, mem = prod

        if not(len(children) == 2):
            raise "More than two children in %s" % str(prod)
        newProd = sym, children[0], children[1], weight, mem
        newGram.append(newProd)

    return newGram

# Convert a grammar to CNF form
def convertGrammarToCNF(lex, gram):
    lex, gram = cnfAddMemory(lex, gram)
    lex, gram = cnfRemoveUnits(lex, gram)
    gram = cnfRemoveLongs(gram)
    gram = cnfFlattenChildren(gram)

    return lex, gram


# ===========================================================================
# ============================= CKY Calculation =============================
# ===========================================================================

# create an empty CKY chart
# N is size
def createEmpty(N):
    arr = []
    for i in range(N):
        subArr = []
        for j in range(N):
            subArr.append([])
        arr.append(subArr)
    return arr

# initialize the first cells based on the lexicon
def initFromLex(chart, tokens, lex):
    for i, t in enumerate(tokens):
        if not(t in lex):
            raise "%s not in lexicon" % t
        for l in lex[t]:
            # symbol, start, end, memory, weight vector, id
            entryID = uuid.uuid4()
            entry = (l[0], i, i+1, l[2], l[1], entryID)
            chart[i][i].append(entry)
    return chart

# initialize cells with a map
def initFromSpans(chart, lexSpans, interiorSpans):
    # case where we are on the diagonal of the chart
    for span in lexSpans:
        sym, start, end, mem, weight = span
        entryID = uuid.uuid4()
        newSpan = (sym, start, end, mem, weight, entryID)
        chart[start][start].append(newSpan)

    # if we aren't on the diagonal, setup is a little more complicated
    for span in interiorSpans:
        if len(span) == 5:
            sym, start, end, mem, weight = span
            entryID = uuid.uuid4()
            entry = (sym, "", "", -1, [], [], mem, weight, entryID)
        else:
            sym, start, split, end, leftInfo, rightInfo, mem, weight = span
            leftSym, leftWeight = leftInfo
            rightSym, rightWeight = rightInfo
            entryID = uuid.uuid4()
            entry = (sym, leftSym, rightSym, split, leftWeight, rightWeight, mem, weight, entryID)
        row = start
        col = end - 1
        chart[row][col].append(entry)
    return chart


# Convert a grammar in list form to a grammar in map form
def convertGrammarToMap(gram):
    gramMap = {}
    for production in gram:
        a, b, c, vec, mem = production
        if (b in gramMap) and (c in gramMap[b]):
            gramMap[b][c].append([a, vec, mem])
        else:
            if not(b in gramMap):
                gramMap[b] = {}
            gramMap[b][c] = [[a, vec, mem]]
    return gramMap

# run CKY upwards on a chart
def runUpwards(chart, gram):
    gramMap = convertGrammarToMap(gram)

    N = len(chart)
    # i goes across the top row
    for i in range(1, N):
        # j goes down the rows
        for j in range(0, N-i):
            myCol = i + j
            myRow = j
            # we need to check each possible combination of split
            for k in range(0, i):
                # for this combination, get how far left and how far down
                # then grab the items at each
                left = i - k
                down = k + 1

                rawLeftItems = chart[myRow][myCol - left]
                rawDownItems = chart[myRow + down][myCol]
                leftItems = rawLeftItems
                downItems = rawDownItems

                # for each pair of items, if they are part of a production
                # in the grammar, add a new entry
                for leftItem in leftItems:
                    for downItem in downItems:
                        b = leftItem[0]
                        c = downItem[0]
                        if b in gramMap:
                            if c in gramMap[b]:
                                for possible in gramMap[b][c]:
                                    pSym, pVec, pMem = possible
                                    weightVec = leftItem[-2] + downItem[-2] + pVec
                                    split = myCol - left + 1
                                    entryID = uuid.uuid4()
                                    entry = (pSym, b, c, split, leftItem[-1], downItem[-1], pMem, weightVec, entryID)
                                    chart[myRow][myCol].append(entry)

    return chart

# run CKY filter on a chart
def filterChart(chart, root):
    N = len(chart)

    if (N == 0):
        return chart

    # create a new chart that things will be copied into.
    newChart = createEmpty(N)

    # add root symbols
    for fin in chart[0][N-1]:
        sym = fin[0]
        if sym in root:
            newChart[0][N-1].append(fin)

    # go through chart backwards
    for i in range(0, N-1):
        layer = N - 1 - i
        for j in range(0, N - layer):
            row = j
            col = layer + j
            # add stuff that is a child of valid stuff in new chart
            for entry in newChart[row][col]:
                _, b, c, split, lid, did, _, _, _ = entry
                leftCol = split - 1
                downRow = split

                # get lists of entries that combined to form this
                leftEntries = chart[row][leftCol]
                downEntries = chart[downRow][col]

                # copy over valid productions into the new chart
                # leave others in the old chart
                remaining = []
                for le in leftEntries:
                    if le[-1] == lid:
                        newChart[row][leftCol].append(le)
                    else:
                        remaining.append(le)
                chart[row][leftCol] = remaining

                remaining = []
                for de in downEntries:
                    if de[-1] == did: #de[0] == c and vecMatch:
                        newChart[downRow][col].append(de)
                    else:
                        remaining.append(de)
                chart[downRow][col] = remaining



    return newChart

# print a chart
def printChart(chart):
    s = []
    for row in chart:
        s2 = []
        for items in row:
            if len(items) > 0:
                s3 = []
                for item in items:
                    s3.append(str(item[0]))# + ";" + str(item[-1])[0:3] + ";" + str(item[4])[0:3] + ";" + str(item[5])[0:3])
                s2.append(", ".join(s3))
            else:
                s2.append("")
        print("[[" + "], [".join(s2) + "]]")

    print("=======")

# get subparses starting from given location
def getSubParses(chart, row, col, sym, vec, targetID):
    sps = []

    # handle terminals
    if (row == col):
        for entry in chart[row][col]:
            a, _, _, mem, wvec, id = entry
            # only select appropriate entry at this cell
            if targetID == id:
                # if this had unit productions, recreate them
                if (len(mem[0]) > 0):
                    child = {
                        "sym": mem[0][0],
                        "vec": wvec,
                        "span": [row, row+1],
                        "children": []
                    }
                    for i in range(1, len(mem[0])):
                        child = {
                            "sym": mem[0][i],
                            "vec": wvec,
                            "span": [row, row+1],
                            "children": [child]
                        }
                    newParse = {
                        "sym": sym,
                        "vec": wvec,
                        "span": [row, row+1],
                        "children": [child]
                    }
                else: # otherwise just add this piece
                    newParse = {
                        "sym": sym,
                        "vec": wvec,
                        "span": [row, row+1],
                        "children": []
                    }
                sps.append(newParse)

        return sps

    # handle productions
    for entry in chart[row][col]:
        numAdded = 0
        a, b, c, split, lid, did, mem, wvec, id = entry
        # only examine proper entry in the chart
        if id == targetID:
            # if this entry was inserted during creation and doesn't have
            # children, don't try to analyze the children
            if (b == "" and c == ""):
                newParse = {
                    "sym": sym,
                    "vec": wvec,
                    "span": [row, col+1],
                    "children": []
                }
                sps.append(newParse)
                numAdded += 1
            elif targetID == id:
                leftCol = split - 1
                downRow = split

                # get lists of entries that combined to form this
                leftEntries = chart[row][leftCol]
                downEntries = chart[downRow][col]

                # find child productions
                validLeftParses = []
                for le in leftEntries:
                    if le[-1] == lid:
                        leftParses = getSubParses(chart, row, leftCol, le[0], le[-2], le[-1])
                        validLeftParses.extend(leftParses)

                validDownParses = []
                for de in downEntries:
                    if de[-1] == did:
                        downParses = getSubParses(chart, downRow, col, de[0], de[-2], de[-1])
                        validDownParses.extend(downParses)

                # for each combination of valid left and right children, add
                # the parse.
                for vlp in validLeftParses:
                    for vdp in validDownParses:
                        # if this was a constructed production, our actual children
                        # are the down child's children
                        if mem[1]:
                            children = [vlp]
                            children.extend(vdp["children"])
                        else:
                            children = [vlp, vdp]

                        # re-extend unitary chains
                        if (len(mem[0]) > 0):
                            child = {
                                "sym": mem[0][0],
                                "vec": wvec,
                                "span": [row, col+1],
                                "children": children
                            }
                            for i in range(1, len(mem[0])):
                                child = {
                                    "sym": mem[0][i],
                                    "vec": wvec,
                                    "span": [row, col+1],
                                    "children": [child]
                                }
                            newParse = {
                                "sym": sym,
                                "vec": wvec,
                                "span": [row, col+1],
                                "children": [child]
                            }
                        else:
                            newParse = {
                                "sym": sym,
                                "vec": wvec,
                                "span": [row, col+1],
                                "children": children
                            }
                        sps.append(newParse)
                        numAdded += 1

    return sps

# extract parses
def getParses(chart):
    parses = []
    N = len(chart)

    if (N == 0):
        return parses

    # Get the high level entries
    topEntries = chart[0][N-1]
    # for each high level entry
    for i, entry in enumerate(topEntries):
        # Check if this is a duplicate of a previous entry
        unique = True
        sym, _, _, _, _, _, _, vec, id = entry
        for j in range(0, i):
            csym, _, _, _, _, _, _, cvec, cid = topEntries[j]
            if id == cid:
                unique = False
        # if it's not a duplicate entry, get subparses and add them to
        # the parse list.
        if unique:
            sps = getSubParses(chart, 0, N-1, sym, vec, id)
            parses.extend(sps)
    return parses


# Print a subparse
def printSubParse(sp, tab):
    print("%s%s %d-%d, (weight: %s)" % (tab, sp["sym"], sp["span"][0], sp["span"][1], str(sp["vec"])))
    for child in sp["children"]:
        printSubParse(child, tab + "  ")

# print a list of parses
def printParses(p):
    for entry in p:
        printSubParse(entry, "")

# run full CKY given a list, lexicon, and grammar
def runFull(tokens, inLex, inGram, root, printPrs=True):
    N = len(tokens)
    chart = createEmpty(N)
    lex, gram = convertGrammarToCNF(inLex, inGram)
    chart = initFromLex(chart, tokens, lex)
    chart = runUpwards(chart, gram)
    chart = filterChart(chart, root)
    if (printPrs):
        printChart(chart)
    parses = getParses(chart)

    if (printPrs):
        printParses(parses)

    return parses

# run full CKY given a list of tokens, initialization info for the char, and a grammar
def runFullCustomInit(tokens, init, inGram, root, printPrs=True):
    N = len(tokens)
    chart = createEmpty(N)

    inLex = {}
    lex, gram = convertGrammarToCNF(inLex, inGram)
    chart = initFromSpans(chart, init[0], init[1])
    chart = runUpwards(chart, gram)
    chart = filterChart(chart, root)
    if (printPrs):
        printChart(chart)
    parses = getParses(chart)

    if (printPrs):
        printParses(parses)

    return parses

# Run some tests for CKY
if __name__ == "__main__":
    # test 1
    tokens = list("aabb")
    # Memory contains list of unitary subproductions from lowest to highest
    # and whether this is was split in two
    # lexicon contains entries and weight vectors

    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 1]))]
    }
    gram = [
        ("S1", ["S"], np.array([0, 0])),
        ("S", ["AP", "S", "B"], np.array([0, 0])),
        ("S", ["AP", "B"], np.array([0, 0])),
        ("AP", ["A1"], np.array([0, 0])),
        ("A1", ["A"], np.array([0, 0])),
    ]
    root = ["S1"]
    parses = runFull(tokens, lex, gram, root)

    print("========")

    # test 2 productions with more than two children 
    tokens = list("abcd")
    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 0]))],
        "c": [("C", np.array([0, 0]))],
        "d": [("D", np.array([0, 0]))],
        "e": [("E", np.array([0, 0]))],
        "f": [("F", np.array([0, 0]))],
        "g": [("G", np.array([0, 0]))],
        "h": [("H", np.array([0, 0]))]
    }
    gram = [
        ("S", ["A", "B", "C", "D"], np.array([0, 0])),
        ("S", ["E", "F", "G", "H"], np.array([0, 0]))
    ]
    root = ["S"]
    parses = runFull(tokens, lex, gram, root)

    print("========")

    tokens = list("efgh")

    parses = runFull(tokens, lex, gram, root)

    print("========")

    # test 3: test unit -> split
    tokens = list("abc")
    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 0]))],
        "c": [("C", np.array([0, 0]))]
    }
    gram = [
        ("S", ["A", "B", "C"], np.array([0, 0])),
        ("S1", ["S"], np.array([0, 0])),
        ("S2", ["S1"], np.array([0, 0]))
    ]
    root = ["S2"]
    parses = runFull(tokens, lex, gram, root)

    print("========")

    # test 4: test split -> unit (middle)
    tokens = list("abcd")
    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 0]))],
        "c": [("C", np.array([0, 0]))],
        "d": [("D", np.array([0, 0]))]
    }
    gram = [
        ("S", ["A", "B4", "C", "D"], np.array([0, 0])),
        ("B4", ["B3"], np.array([0, 0])),
        ("B3", ["B2"], np.array([0, 0])),
        ("B2", ["B1"], np.array([0, 0])),
        ("B1", ["B"], np.array([0, 0]))
    ]
    root = ["S"]
    parses = runFull(tokens, lex, gram, root)

    print("========")

    # test 5: test split -> unit (end)
    tokens = list("abcd")
    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 0]))],
        "c": [("C", np.array([0, 0]))],
        "d": [("D", np.array([0, 0]))]
    }
    gram = [
        ("S", ["A", "B", "C", "D4"], np.array([0, 0])),
        ("D4", ["D3"], np.array([0, 0])),
        ("D3", ["D2"], np.array([0, 0])),
        ("D2", ["D1"], np.array([0, 0])),
        ("D1", ["D"], np.array([0, 0]))
    ]
    root = ["S"]
    parses = runFull(tokens, lex, gram, root)

    print("========")

    # test 6: inserting at the bottom level
    tokens = list("abcd")
    # sym, start, end, weight = span
    lexInit = [
        ("A", 0, 1, [["A1"], False], np.array([0, 0])),
        ("B", 1, 2, [[], False], np.array([0, 0])),
        ("C", 2, 3, [[], False], np.array([0, 0])),
        ("D", 3, 4, [[], False], np.array([0, 0])),
    ]
    interiorInit = []
    init = [lexInit, interiorInit]
    gram = [
        ("S", ["A", "B", "C", "D"], np.array([0, 0]))
    ]
    root = ["S"]
    parses = runFullCustomInit(tokens, init, gram, root)

    print("========")

    # test 7: inserting into the interior (simple)
    tokens = list("abcd")
    # sym, start, end, weight = span
    lexInit = []
    # sym, start, end, mem, weight = span
    interiorInit = [
        ("AB", 0, 2, [[], False], np.array([0, 0])),
        ("CD", 2, 4, [[], False], np.array([0, 0]))
    ]
    init = [lexInit, interiorInit]
    gram = [
        ("S", ["AB", "CD"], np.array([0, 0]))
    ]
    root = ["S"]
    parses = runFullCustomInit(tokens, init, gram, root)

    print("========")



    # test 8: inserting into the interior (complex)
    # need to update init so that it can take IDs
    # tokens = list("abcd")
    # # sym, start, end, weight = span
    # lexInit = [
    #     ("A", 0, 1, [["A1"], False], np.array([0, 0])),
    #     ("B", 1, 2, [[], False], np.array([1, 0])),
    #     ("C", 2, 3, [[], False], np.array([0, 1])),
    #     ("D", 3, 4, [[], False], np.array([0, 0])),
    # ]
    # # sym, start, split, end, leftInfo, rightInfo, mem, weight = span
    # #   sym, weight = info
    # interiorInit = [
    #     ("AB", 0, 1, 2,
    #         ["A", np.array([0, 0])],
    #         ["B", np.array([1, 0])],
    #         [[], False], np.array([1, 0])),
    #     ("CD", 2, 3, 4,
    #         ["C", np.array([0, 1])],
    #         ["D", np.array([0, 0])],
    #         [[], False], np.array([0, 1]))
    # ]
    # init = [lexInit, interiorInit]
    # gram = [
    #     ("S", ["AB", "CD"], np.array([0, 0]))
    # ]
    # root = ["S"]
    # parses = runFullCustomInit(tokens, init, gram, root)

    print("========")

    # test 9: ambiguity
    tokens = list("abcd")
    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 0]))],
        "c": [("C", np.array([0, 0]))],
        "d": [("D", np.array([0, 0]))]
    }
    gram = [
        ("S", ["A", "B", "C", "D"], np.array([0, 0])),
        ("S", ["AB", "CD"], np.array([0, 0])),
        ("AB", ["A", "B"], np.array([1, 0])),
        ("CD", ["C", "D"], np.array([0, 0])),
        ("S", ["ABC", "D"], np.array([0, 1])),
        ("ABC", ["A", "B", "C"], np.array([0, 0])),
    ]
    root = ["S"]
    parses = runFull(tokens, lex, gram, root)

    print("========")

    # test 9: deep ambiguity
    tokens = list("abcdd")
    lex = {
        "a": [("A", np.array([0, 0]))],
        "b": [("B", np.array([0, 0]))],
        "c": [("C", np.array([0, 0]))],
        "d": [("D1", np.array([0, 0])), ("D2", np.array([0, 0]))]
    }
    gram = [
        ("S", ["A", "B", "C", "D"], np.array([0, 0])),
        ("D", ["D1", "D1"], np.array([0, 0])),
        ("D", ["D1", "D2"], np.array([0, 0])),
    ]
    root = ["S"]
    parses = runFull(tokens, lex, gram, root)

    print("========")
