# contains utilities for scanning
import re

import odikon.utils as utils
import odikon.CKY as CKY

import numpy as np

# Conversion for meters
METER = {
    "IAMBS": 0,
    "ANAPESTS": 1
}

# Store breathing options
BREATHING = utils.Constant
BREATHING.SMOOTH = 0
BREATHING.ROUGH = 1
BREATHING_STRINGS = {
    BREATHING.SMOOTH: ")",
    BREATHING.ROUGH: "("
}

# Store accent options
ACCENT = utils.Constant
ACCENT.ACUTE = 0
ACCENT.GRAVE = 1
ACCENT.CIRCUM = 2
ACCENT_STRINGS = {
    ACCENT.ACUTE: "/",
    ACCENT.GRAVE: "\\",
    ACCENT.CIRCUM: "~"
}


# return an array corresponding to given feature information
def getFeatureArr(resolution=False, muteLiquid=False, epicCorreption=False,
                  internalCorreption=False, epsilonCombo=False,
                  properNameResolution=False):
    arr = np.zeros((6))
    if (resolution):
        arr[0] = 1
    if (muteLiquid):
        arr[1] = 1
    if (epicCorreption):
        arr[2] = 1
    if (internalCorreption):
        arr[3] = 1
    if (epsilonCombo):
        arr[4] = 1
    if (properNameResolution):
        arr[5] = 1

    return arr

# Constants for chart parse symbols
SYM = utils.Constant
SYM.LONG = "LONG"
SYM.SHORT = "SHORT"
SYM.UNK = "UNK"
SYM.LINE = "LINE"

SYM.IAMB_1 = "F1"
SYM.IAMB_2 = "F24"
SYM.IAMB_3 = "F35"
SYM.IAMB_6 = "F6"

# standard and the special final vv--
SYM.ANAP_S = "AS"
SYM.ANAP_P = "AP"

# Iambic Trimeter Grammar
iambGrammar = [
    (SYM.LINE, [SYM.IAMB_1, SYM.IAMB_2, SYM.IAMB_3, SYM.IAMB_2, SYM.IAMB_3, SYM.IAMB_6], getFeatureArr()),

    (SYM.IAMB_1, [SYM.LONG, SYM.LONG], getFeatureArr()),
    (SYM.IAMB_1, [SYM.SHORT, SYM.LONG], getFeatureArr()),
    (SYM.IAMB_1, [SYM.LONG, SYM.SHORT, SYM.SHORT], getFeatureArr(resolution=True)),
    (SYM.IAMB_1, [SYM.SHORT, SYM.SHORT, SYM.LONG], getFeatureArr(resolution=True)),

    (SYM.IAMB_2, [SYM.SHORT, SYM.LONG], getFeatureArr()),
    (SYM.IAMB_2, [SYM.SHORT, SYM.SHORT, SYM.SHORT], getFeatureArr(resolution=True)),
    (SYM.IAMB_2, [SYM.SHORT, SYM.SHORT, SYM.LONG], getFeatureArr(resolution=True, properNameResolution=True)),

    (SYM.IAMB_3, [SYM.LONG, SYM.LONG], getFeatureArr()),
    (SYM.IAMB_3, [SYM.SHORT, SYM.LONG], getFeatureArr()),
    (SYM.IAMB_3, [SYM.LONG, SYM.SHORT, SYM.SHORT], getFeatureArr(resolution=True)),
    (SYM.IAMB_3, [SYM.SHORT, SYM.SHORT, SYM.SHORT], getFeatureArr(resolution=True)),
    (SYM.IAMB_3, [SYM.SHORT, SYM.SHORT, SYM.LONG], getFeatureArr(resolution=True, properNameResolution=True)),

    (SYM.IAMB_6, [SYM.SHORT, SYM.LONG], getFeatureArr()),
    (SYM.IAMB_6, [SYM.SHORT, SYM.SHORT], getFeatureArr()),
]
# Anapestic Tetrameter Grammar
anapestGrammar = [
    # A | A | A | A
    (SYM.LINE, [SYM.ANAP_S, SYM.ANAP_S, SYM.ANAP_S, SYM.ANAP_S], getFeatureArr()),
    # A | A
    (SYM.LINE, [SYM.ANAP_S, SYM.ANAP_S], getFeatureArr()),
    # A | A | vv--
    (SYM.LINE, [SYM.ANAP_S, SYM.ANAP_S, SYM.ANAP_P], getFeatureArr()),

    (SYM.ANAP_S, [SYM.LONG, SYM.LONG], getFeatureArr()),
    (SYM.ANAP_S, [SYM.LONG, SYM.SHORT, SYM.SHORT], getFeatureArr()),
    (SYM.ANAP_S, [SYM.SHORT, SYM.SHORT, SYM.LONG], getFeatureArr()),

    (SYM.ANAP_P, [SYM.SHORT, SYM.SHORT, SYM.LONG, SYM.LONG], getFeatureArr()),
]

meterGrammars = {
    "IAMBS": iambGrammar,
    "ANAPESTS": anapestGrammar
}

# Characters
GREEK_LOWER = "αβγδεζηθικλμνξοπρσςτυχφψω"
GREEK_VOWELS = "αεηιουω"
GREEK_CONSONANTS = "βγδζθκλμνξπρσςτχφψ"
GREEK_MUTES = "πκτβδγφχθ"
GREEK_LIQUIDS = "ρλμν"
GREEK_DOUBLECONS = "ζξψ"

# lines that can be skipped
skippables = {
    "ἰώ": True,
    "ἰὼἰώ": True,
    "ἰὼἰὼφίλαι": True,
    "ἰὼἰὼτύχα": True,
    "αἰαῖ": True,
    "αἰαῖαἰαῖ": True,
    "αἰαῖμάλ᾽αὖθις": True,
    "φεῦ": True,
    "φεῦφεῦ": True,
    "ἒἔ": True,
    "ἰώμοίμοι": True,
    "ναί": True,
    "ἔα": True,
    "ἔαἔα": True,
    "ὤμοιμοι": True,
    "ἆἆ": True,
    "<>": True,
    "ἔσωθεν": True,
    "ἰοὺἰού": True,
    "οἴμοι": True,
    "εἶἑν": True,
    "ἰδού": True,
    "ὠή": True,
    "πιθοῦ": True,
    "ἰώμοι": True,
    "ἰαχᾷ": True,
    "ἔβαςἔβας": True,
    "ἔχειςἔχεις": True,
    "ἄπαιςἄπαις": True,
}

# return true if this line should be skipped because it is just an exclamation
def skipLine(line):
    text = line["line_text"]
    text = re.sub(r'[\[\]\,\.\(\)）（:;—]', "", text)
    text = re.sub(r'\s+', "", text)
    if text in skippables:
        return True
    else:
        return False

# holds a greek unicode character
class Char(object):
    def __init__(self, inputChar):
        self.rawChar = inputChar

        decomp = utils.fullyDecomposeUnicodeChar(inputChar)
        self.baseChar = decomp[0]

        self.isSpace = False
        self.valid = True

        # if this is some sort of punctuation
        if not(self.baseChar in GREEK_LOWER):
            if inputChar == " ":
                self.isSpace = True
            else:
                self.valid = False

        if not(self.isSpace) and self.valid:

            self.breathing = None
            if "\u0313" in decomp:
                self.breathing = BREATHING.SMOOTH
            elif "\u0314" in decomp:
                self.breathing = BREATHING.ROUGH

            self.accent = None
            if "\u0301" in decomp:
                self.accent = ACCENT.ACUTE
            elif "\u0300" in decomp:
                self.accent = ACCENT.GRAVE
            elif "\u0342" in decomp:
                self.accent = ACCENT.CIRCUM

            self.hasIotaSubscript = False
            if "\u0345" in decomp:
                self.hasIotaSubscript = True

            self.hasDiaeresis = False
            if "\u0308" in decomp:
                self.hasDiaeresis = True

        self.d = decomp

    def __repr__(self):
        if not(self.valid):
            return "<invalid: '%s'>" % self.rawChar
        elif self.isSpace:
            return "<space>"
        else:
            s = ["<"]
            s.append(self.baseChar)

            if self.breathing != None:
                s.append(BREATHING_STRINGS[self.breathing])

            if self.accent != None:
                s.append(ACCENT_STRINGS[self.accent])

            if self.hasIotaSubscript:
                s.append("ι")

            if self.hasDiaeresis:
                s.append("¨")

            s.append(">")

            return " ".join(s)
            # for c in self.d:
            #     utils.printUnicodeChar(c)

# holds a Greek phoneme
class Phoneme(object):
    def __init__(self, inputChars):
        if len(inputChars) == 2:
            ic1 = inputChars[0]
            ic2 = inputChars[1]

            self.rawChar = ic1.rawChar + ic2.rawChar

            self.baseChar = ic1.baseChar + ic2.baseChar

            self.isSpace = False

            self.breathing = ic2.breathing

            self.accent = ic2.accent

            self.hasIotaSubscript = False

            self.hasDiaeresis = False

            self.isDiphthong = True
        else:
            ic = inputChars[0]

            self.rawChar = ic.rawChar

            self.baseChar = ic.baseChar

            self.isSpace = ic.isSpace
            if not(self.isSpace):
                self.breathing = ic.breathing

                self.accent = ic.accent

                self.hasIotaSubscript = ic.hasIotaSubscript

                self.hasDiaeresis = ic.hasDiaeresis

                self.isDiphthong = False

        # true if this is a vowel and the next vowel is long
        self.nextMaybeShort = False


        self.afterSpace = False
        self.beforeSpace = False

        # number of vowels to the right before we reach a space
        self.vowelsToSpace = -1

    # return true if this is a vowel
    def isVowel(self):
        return len(self.baseChar) == 2 or self.baseChar in GREEK_VOWELS

    # return true if this is a consonant
    def isConsonant(self):
        return len(self.baseChar) == 1 and self.baseChar in GREEK_CONSONANTS

    # true if the vowel is definitely long
    # definitely long if this is a diphthong, eta, omega, has a circumflex,
    # or has a iota subscript
    def isLongVowel(self):
        return ((len(self.baseChar) == 2) or (self.baseChar == "η")
            or (self.baseChar == "ω") or (self.accent == ACCENT.CIRCUM)
            or (self.hasIotaSubscript))

    # true if the vowel is definitely short
    # definitely short if this is an epsilon, omicron, or
    # has an acute accent in penultimate position before a short
    def isShortVowel(self):
        return ((self.baseChar == "ε") or (self.baseChar == "ο") or
          (self.vowelsToSpace == 1 and self.accent == ACCENT.ACUTE and self.nextMaybeShort))

    def __repr__(self):
        if self.isSpace:
            return "<space>"
        else:
            s = ["<"]
            if self.afterSpace:
                s.append("_")

            s.append(self.baseChar)

            if self.breathing != None:
                s.append(BREATHING_STRINGS[self.breathing])

            if self.accent != None:
                s.append(ACCENT_STRINGS[self.accent])

            if self.hasIotaSubscript:
                s.append("ι")

            if self.hasDiaeresis:
                s.append("¨")

            if self.beforeSpace:
                s.append("_")

            s.append(">")

            return " ".join(s)
            # for c in self.d:
            #     utils.printUnicodeChar(c)


# ===========================================================================
# ================================ Segmenting ===============================
# ===========================================================================

# given two characters, determine if they form a diphthong
def formDiphthong(c1, c2):
    if c2 == None:
        return False

    if c1.isSpace or c2.isSpace:
        return False

    c1Base = c1.baseChar
    c2Base = c2.baseChar

    # if this is a valid diphthong combo
    if (c1Base in "αεο" and c2Base in "ι") or (c1Base in "αεοηω" and c2Base in "υ"):
        # if the first character has an accent or breathing, or second
        # character has a diaeresis
        if (c1.accent == None) and (c1.breathing == None) and not(c2.hasDiaeresis):
            return True
    return False

# get a list of Chars (representations of greek characters) from the line text
def extractChars(line):
    chars = []
    for c in line:
        char = Char(c)
        chars.append(char)
    chars = list(filter(lambda x: x.valid, chars))
    return chars

# given a list of characters, combine diphthongs and remove spaces to get
# phonemes
def charsToPhonemes(chars):
    phonemes = []
    i = 0
    while i < len(chars):
        char = chars[i]
        if i == len(chars) - 1:
            next = None
        else:
            next = chars[i+1]
        comb = formDiphthong(char, next)

        if (comb):
            p = Phoneme([char, next])
            i += 1
        else:
            p = Phoneme([char])

        phonemes.append(p)
        i += 1

    nonSpacePhonemes = []
    for i, p in enumerate(phonemes):
        if not(p.isSpace):
            if i > 0 and phonemes[i-1].isSpace:
                p.afterSpace = True
            if i < len(phonemes) - 1 and phonemes[i+1].isSpace:
                p.beforeSpace = True
            nonSpacePhonemes.append(p)

    return nonSpacePhonemes

# given a list of phonemes, group them into groups of vowels and consonants
def phonsToVowCons(phons):
    cvSegs = []
    currentCons = []

    for phon in phons:
        if phon.isConsonant():
            currentCons.append(phon)
        elif phon.isVowel():
            cvSegs.append({
                "c": currentCons,
                "v": phon
            })
            currentCons = []

    if len(currentCons) > 0:
        cvSegs.append({
            "c": currentCons,
            "v": None
        })

    if (len(cvSegs) > 0):
        vcSegs = [{
            "v": None,
            "c": cvSegs[0]["c"]
        }]

        # reformat to v followed by c
        for i, seg in enumerate(cvSegs):
            # if the last syllable is just a vowel, properly add it
            if i == len(cvSegs) - 1:
                if not(seg["v"] == None):
                    vcSegs.append({
                        "v": seg["v"],
                        "c": []
                    })
            else:
                vcSegs.append({
                    "v": seg["v"],
                    "c": cvSegs[i+1]["c"]
                })
        # count the number of vowels until a space
        inds = list(range(len(vcSegs)))
        inds.reverse()
        toSpaceCount = 0
        for k, ind in enumerate(inds):
            seg = vcSegs[ind]
            vow = seg["v"]
            if not(vow == None):
                if (vow.beforeSpace):
                    toSpaceCount = 0
                vow.vowelsToSpace = toSpaceCount
                toSpaceCount += 1

            # if this is not the first item, get info about whether the next
            # item is potentially short.
            if not(k == 0) and not(vow == None):
                next = vcSegs[inds[k-1]]["v"]
                if not(next == None):
                    vow.nextMaybeShort = not(next.isLongVowel())

    else:
        vcSegs = []

    return vcSegs


# given a line, segment it into constituent parts
# also return a list of characters being examined
def segmentLine(lineObj):
    line = lineObj["line_text"].lower()
    # print(line)
    chars = extractChars(line)
    noSpaceChars = filter(lambda x: (x.valid and not(x.isSpace)), chars)
    outwardChars = list(map(lambda x: x.rawChar, noSpaceChars))
    # for char in chars:
    #     print(char)
    phonemes = charsToPhonemes(chars)
    # for phon in phonemes:
    #     print(phon)
    vcSegments = phonsToVowCons(phonemes)

    # for seg in vcSegments:
    #     print(" v: %s" % str(seg["v"]), end=" ")
    #     print("  c: ", end="")
    #     for phon in seg["c"]:
    #         print(phon, end="; ")
    #     print("\n---")
    #
    # print("===")

    return vcSegments, outwardChars

# ===========================================================================
# ============================ Span Calculation =============================
# ===========================================================================

# true if this phoneme is a mute
def isMute(con):
    return con.baseChar in GREEK_MUTES

# true if this phoneme is a liquid
def isLiquid(con):
    return con.baseChar in GREEK_LIQUIDS


# return true if this set of characters is a mute/liquid pair
def isMuteLiquid(cons):
    if (len(cons) == 2):
        if isMute(cons[0]) and isLiquid(cons[1]):
            return True
    return False


# potentially combine the current vowel with a previous epsilon
def epsilonCombo(prev, vow, lastSCI, end):
    sylSpans = []
    if (not(prev == None) and len(prev["c"]) == 0 and prev["v"].baseChar == "ε"
        and not(prev["v"].beforeSpace) and ((vow.baseChar in "αοω") or vow.baseChar == "οι" or vow.baseChar == "ου")):
        for prev_start, _ in lastSCI:
            span = (SYM.LONG, prev_start, end, [[], False], getFeatureArr(epsilonCombo=True))
            sylSpans.append(span)
    return sylSpans

# given information, return the spans for a closed syllable version
def getClosedSylSpans(start, cont, seg, prev, lastSCI, isLast, muteLiquid=False):
    sylSpans = []
    vow = seg["v"]

    # last span needs to include all final consonants
    if isLast:
        end = cont + len(vow.baseChar) + len(seg["c"])
        nextCont = end
    else:
        end = cont + len(vow.baseChar) + 1
        nextCont = end + len(seg["c"]) - 1

    span = (SYM.LONG, start, end, [[], False], getFeatureArr(muteLiquid=muteLiquid))
    sylSpans.append(span)

    # add the epsilon combo version
    sylSpans.extend(epsilonCombo(prev, vow, lastSCI, end))

    nextSC = [(end, nextCont)]
    return sylSpans, nextSC

# given information, return spans for an open syllable version
def getOpenSylSpans(start, cont, seg, prev, lastSCI, isLast):
    sylSpans = []
    vow = seg["v"]
    cons = seg["c"]
    numCons = len(seg["c"])

    # last span needs to include all final consonants
    if isLast:
        end = cont + len(vow.baseChar) + numCons
        nextCont = end
    else:
        end = cont + len(vow.baseChar)
        nextCont = end + numCons

    # if this is followed by a double consonant, it is long
    if (numCons > 0 and cons[0].baseChar in GREEK_DOUBLECONS):
        span = (SYM.LONG, start, end, [[], False], getFeatureArr())
        sylSpans.append(span)
    else: # else
        definitelyLong = vow.isLongVowel()
        definitelyShort = vow.isShortVowel()
        # if this vowel is a diphthong or definitely long
        if (definitelyLong):
            # this syllable is long
            span = (SYM.LONG, start, end, [[], False], getFeatureArr())
            sylSpans.append(span)

            # it could be short if there is epic correption
            if (numCons == 0 and vow.beforeSpace):
                span = (SYM.SHORT, start, end, [[], False], getFeatureArr(epicCorreption=True))
                sylSpans.append(span)
            elif (numCons == 0 and not(isLast)): # or internal correption
                span = (SYM.SHORT, start, end, [[], False], getFeatureArr(internalCorreption=True))
                sylSpans.append(span)
        elif (definitelyShort): # if this vowel is definitely short
            span = (SYM.SHORT, start, end, [[], False], getFeatureArr())
            sylSpans.append(span)
        else: # could be long or short, so we add both
            span = (SYM.SHORT, start, end, [[], False], getFeatureArr())
            sylSpans.append(span)
            span = (SYM.LONG, start, end, [[], False], getFeatureArr())
            sylSpans.append(span)

    # add the epsilon combo version
    sylSpans.extend(epsilonCombo(prev, vow, lastSCI, end))

    nextSC = [(end, nextCont)]
    return sylSpans, nextSC

# given two spans, are they functionally equivalent?
def spansEqual(sp, sp2):
    l1, s1, e1, mem1, vec1 = sp
    l2, s2, e2, mem2, vec2 = sp2

    lEq = l1 == l2
    sEq = s1 == s2
    eEq = e1 == e2
    # TODO: could check memory

    vecEq = np.all(vec1 == vec2)

    return (lEq and sEq and eEq and vecEq)

# given a list of vowel-consonant segments, return a list of spans
# for the chart
def getSpans(segs):
    spans = []

    if len(segs) == 0:
        return spans

    # store a set pairs where the pair represents the start of the next
    # span to create and the character that one is continuing from
    startContinueIndices = [(0, 0)]

    startSeg = 0
    if segs[0]["v"] == None:
        startContinueIndices = [(0, len(segs[0]["c"]))]
        startSeg = 1

    # example span ("AB", 0, 2, [[], False], np.array([0, 0]))
    lastSCI = None
    for i, seg in enumerate(segs[startSeg:]):
        isLast = i == len(segs)-1-startSeg
        nextSCI = []
        if i > 0 and not(segs[i-1+startSeg]["v"] == None):
            prev = segs[i-1+startSeg]
        else:
            prev = None

        for sc in startContinueIndices:
            start, cont = sc
            if (isMuteLiquid(seg["c"])):
                # this is followed by a mute/liquid pair, so
                # run both setups
                sylSpans, nextSCI = getOpenSylSpans(start, cont, seg, prev, lastSCI, isLast)
                spans.extend(sylSpans)

                sylSpans2, nextSCI2 = getClosedSylSpans(start, cont, seg, prev, lastSCI, isLast, muteLiquid=True)

                # avoid double counting
                for sp2 in sylSpans2:
                    uniq = True
                    for sp in sylSpans:
                        if spansEqual(sp, sp2):
                            uniq = False
                    if uniq:
                        spans.append(sp2)

                nextSCI.extend(nextSCI2)
            elif (isLast and len(seg["c"]) > 0):
                # special handling for the final syllable
                sylSpans, nextSCI = getOpenSylSpans(start, cont, seg, prev, lastSCI, isLast)
                spans.extend(sylSpans)
                sylSpans2, nextSCI = getClosedSylSpans(start, cont, seg, prev, lastSCI, isLast)

                # avoid double counting
                for sp2 in sylSpans2:
                    uniq = True
                    for sp in sylSpans:
                        if spansEqual(sp, sp2):
                            uniq = False
                    if uniq:
                        spans.append(sp2)
            elif len(seg["c"]) > 1:
                # if the this is followed by multiple consonants,
                # we steal the next consonant
                sylSpans, nextSCI = getClosedSylSpans(start, cont, seg, prev, lastSCI, isLast)
                spans.extend(sylSpans)
            else:
                # followed by a single cononsonant, so this is an open syllable,
                # no consonant stealing
                sylSpans, nextSCI = getOpenSylSpans(start, cont, seg, prev, lastSCI, isLast)
                spans.extend(sylSpans)
        lastSCI = startContinueIndices
        startContinueIndices = nextSCI

    # print("Spans:")
    # for span in spans:
    #     print("  " + str(span))
    #
    # print("========")

    return spans

# given tokens,  input spans and meter, get the parses for the line
def getParses(tokens, spans, meter):
    lexInit = []
    interiorInit = []
    for span in spans:
        _, start, end, _, _ = span
        if (start + 1 == end):
            lexInit.append(span)
        else:
            interiorInit.append(span)

    init = [lexInit, interiorInit]
    root = [SYM.LINE]

    gram = meterGrammars[meter]
    parses = CKY.runFullCustomInit(tokens, init, gram, root, printPrs=False)

    # print("." + ".".join(tokens) + ".")
    # print(" ".join(list(map(lambda x: str(x)[-1], range(len(tokens)+1)))))
    # print("---")
    # print("=============")
    # print("=============")

    return parses


# given a list of possible parses, return the index of the best one
# 0: resolution
# 1: muteLiquid
# 2: epicCorreption
# 3: internalCorreption
# 4: epsilonCombo
def pickBestParse(parses):
    # for parse in parses:
    #     print(parse['vec'])
    # print("--")

    # return first parse with no specialties, if it exists
    for i, parse in enumerate(parses):
        vec = parse['vec']
        if (np.sum(vec) == 0):
            return i

    # return first parse with only regular resolution and no epsilon combination, if it exists
    for i, parse in enumerate(parses):
        vec = parse['vec']
        if (np.sum(vec) - (vec[0]-vec[5]) + vec[4] == 0):
            return i

    sums = np.zeros((len(parses)))
    sumsPNRes = np.zeros((len(parses)))
    for i, parse in enumerate(parses):
        vec = parse['vec']
        vecSum = np.sum(vec)
        if not(vec[5]):
            sums[i] = vecSum
        sumsPNRes[i] = vecSum

    # return the parse with the least stuff going
    # with on, without proper name only resolution if possible
    if not(np.sum(sums) == 0):
        minIndex = np.argmin(sums)
        return minIndex
    else:
        minIndex = np.argmin(sumsPNRes)
        return minIndex

# parsesTests = []
# parsesTests.append([
#     {'id': 1, 'vec': np.array([0, 0, 0, 0, 0])},
#     {'id': 2, 'vec': np.array([0, 0, 0, 0, 0])}
# ])
# parsesTests.append([
#     {'id': 1, 'vec': np.array([1, 0, 0, 1, 0])},
#     {'id': 2, 'vec': np.array([0, 0, 0, 0, 0])}
# ])
# parsesTests.append([
#     {'id': 1, 'vec': np.array([1, 0, 1, 0, 0])},
#     {'id': 2, 'vec': np.array([1, 0, 0, 0, 1])},
#     {'id': 3, 'vec': np.array([3, 0, 0, 0, 0])}
# ])
# parsesTests.append([
#     {'id': 1, 'vec': np.array([1, 0, 1, 0, 3])},
#     {'id': 2, 'vec': np.array([1, 2, 0, 0, 1])},
#     {'id': 3, 'vec': np.array([3, 0, 5, 0, 1])},
#     {'id': 4, 'vec': np.array([1, 2, 0, 2, 0])}
# ])
# for parsesT in parsesTests:
#     print(pickBestParse(parsesT))
# print("---")

# get the string for a single foot
def printFoot(sp):
    s = []
    for child in sp['children']:
        sym = child['sym']
        if sym == SYM.LONG:
            s.append("-")
        if sym == SYM.SHORT:
            s.append("v")

    return "".join(s)

# convert a scansion parse into a string
def getScanString(parse):
    if parse == None:
        return ""
    s = []
    for child in parse['children']:
        s.append(printFoot(child))
    return "|".join(s)


# given a line and a meter, attempt to scan that line
def scanLine(line, meter, printSpans=False):
    # line = {"line_text": "ετρε οι πης"}
    segmented, keyChars = segmentLine(line)
    spans = getSpans(segmented)

    parses = getParses(keyChars, spans, meter)

    if printSpans:
        print("." + ".".join(keyChars) + ".")
        print(" ".join(list(map(lambda x: str(int(x/10)), range(len(keyChars)+1)))))
        print(" ".join(list(map(lambda x: str(x)[-1], range(len(keyChars)+1)))))
        print("---")

        print("Spans:")
        for span in spans:
            print("  " + str(span))
        print("----")

        CKY.printParses(parses)
        print("----")



    if (len(parses) == 0):
        return None

    bestParse = parses[pickBestParse(parses)]

    return bestParse

# return the best guess for a meter and a parse
def guessMeterWithParse(line):
    i = scanLine(line, "IAMBS")
    a = scanLine(line, "ANAPESTS")

    if i == None and a == None:
        return "OTHER", None
    elif a == None:
        return "IAMBS", i
    elif i == None:
        return "ANAPESTS", a

    betterParse = pickBestParse([i, a])
    if betterParse == 0:
        return "IAMBS", i
    else:
        return "ANAPESTS", a
