# -*- coding: utf-8 -*-
# utility functions that are shared by our different tools
import urllib3
from socket import error as socketError
import xml.etree.ElementTree as ET
import os
import re
import json
import sys
import copy
import errno
import unicodedata


class Constant:
    pass

# store an author
class Author:
    def __init__(self, name):
        self.authorName = name
        self.works = []

        # list of this author's tokens
        self.allTokens = []

        # raw frequency of tokens
        self.tokenFreqs = None
        # total number of tokens for this author
        self.totalTokenCount = None

        # feature data associated with this author
        self.featureData = None
        self.unNormalizedFeatureData = None

    # add a work to this author's list of works
    def addWork(self, work):
        self.works.append(work)

    # download and save all of this author's works
    def downloadAndSaveWorks(self, path, downloadedWorks, oldAuthorWorksList, verbose):
        # ignore already downloaded works
        worksToDownload = []
        for work in self.works:
            if not(work.textName in downloadedWorks):
                worksToDownload.append(work)

        # count the number of texts
        numTexts = len(worksToDownload)


        res = oldAuthorWorksList
        for i in range(len(worksToDownload)):
            work = worksToDownload[i]
            print("    %s. %.2f%% (%d/%d)" % (work.textName, (100*(i+1)/numTexts), (i+1), numTexts))
            try:
                res.append(work.downloadAndSaveText(path, self.authorName, verbose))
            except:
                print("    Work failed to download.")

        print("%s Done." % self.authorName)
        return {
            "author": self.authorName,
            "works": res
        }

    def __str__(self):
        return ("%s (%d works)." %(self.authorName, len(self.works)))

# store information needed to download a text
class TextSpec:
    def __init__(self, name, id, books, infix, cardList):
        self.textName = name
        self.textPerseusID = id
        self.numBooks = books
        self.infix = infix
        self.cardList = cardList
        if (len(cardList["suffixes"]) == 0):
            self.downloadFromCards = False
        else:
            self.downloadFromCards = True
        self.loaded = False
        self.books = []

    # convert from name into a proper filename
    def getTextFname(self):
        r = self.textName.replace(" ", "_")
        return r

    # download this text from Perseus and save it.
    def downloadAndSaveText(self, path, author, verbose):
        saveLoc = path + author + "-" + self.getTextFname() + ".json"
        allBooks = []
        urlBase = "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A" + self.textPerseusID + self.infix
        if(self.downloadFromCards):
            if self.cardList["multi"]:
                for s in self.cardList["suffixes"]:
                    bookNum = s["bookNum"]
                    bookPieces = []
                    for c in s["suffs"]:
                        url = urlBase + s["infix2"] + str(c)
                        if (verbose):
                            print(url)
                        xml = get_TEI_XML(url, False)
                        bookPieces.append(xml)
                    bookText = " ".join(bookPieces)
                    if (verbose):
                        print(bookText)
                    allBooks.append({
                        "bookNumber": bookNum,
                        "bookText": bookText
                    })
            else:
                bookNum = 1
                bookPieces = []
                for c in self.cardList["suffixes"]:
                    url = urlBase + str(c)
                    if (verbose):
                        print(url)
                    xml = get_TEI_XML(url, False)
                    bookPieces.append(xml)
                bookText = " ".join(bookPieces)
                if (verbose):
                    print(bookText)
                allBooks.append({
                    "bookNumber": bookNum,
                    "bookText": bookText
                })
        else:
            for b in range(self.numBooks):
                bookNum = b + 1
                if (bookNum == 8 and author == "Aelian" and self.textName == "De Natura Animalium"):
                    continue
                url = urlBase + str(bookNum)
                if (verbose):
                    print(url)
                xml = get_TEI_XML(url, False)
                #print(xml)
                bookText = xml
                if (verbose):
                    print(bookText)
                allBooks.append({
                    "bookNumber": bookNum,
                    "bookText": bookText
                })
        self.loaded = True

        textObj = {
            "name": self.textName,
            "author": author,
            "numBooks": self.numBooks,
            "booksRaw": allBooks
        }
        safeWrite(saveLoc, textObj, True)

        return {
            "name": self.textName,
            "location": saveLoc
        }

# an object for storing a book
class Book:
    def __init__(self, raw, name, author):
        self.textName = name
        self.author = author
        self.bookNumber = raw["bookNumber"]
        self.bookLines = raw["bookLines"]
        self.numTokens = None

        self.feature_data = None
        self.unNormalizedFeatureData = None

    def getShortName(self):
        cutoff = 5
        tName = self.textName.lower().replace("the ", "").replace("de ", "").replace("on ", "").replace("against ", "")
        return "%s.%s.%s" % (self.author[0:cutoff], tName[0:cutoff], str(self.bookNumber))

    def __str__(self):
        return ("%s: %s book %s." %(self.author, self.textName, self.bookNumber))

# an object for storing a tex still in XML format
class XMLText:
    # takes the filename of a json object created by TextSpec
    def __init__(self, fname):
        t = getContent(fname, True)
        self.textName = t["name"]
        self.author = t["author"]
        self.numBooks = t["numBooks"]
        self.booksRaw = t["booksRaw"]

    def convertFromXML(self):
        convertedBooks = []
        i = 0
        for b in self.booksRaw:
            i += 1
            debugString = "%s %s %d" % (self.author, self.textName, i)
            lines = parse_TEI_lines(b["bookText"], self.textName, self.author, i)

            for line in lines:
                ltext = line["line_text"]
                line["line_text"] = removePunct(ltext, debugString)

            b["bookLines"] = lines
            # remove book text
            b.pop("bookText")
            convertedBooks.append(b)

        textObj = {
            "name": self.textName,
            "author": self.author,
            "numBooks": self.numBooks,
            "booksRaw": convertedBooks
        }
        return textObj

# an object for storing a text
class Text:
    # takes the filename of a json object created by TextSpec
    def __init__(self, fname):
        t = getContent(fname, True)
        self.textName = t["name"]
        self.author = t["author"]
        self.numBooks = t["numBooks"]
        self.books = []

        booksRaw = t["booksRaw"]
        for b in booksRaw:
            self.books.append(Book(b, self.textName, self.author))


# ==============================================================================
# ======================== General Utility Functions ===========================
# ==============================================================================

# check if the given file path exists, and if not create it.
# based on Krumelur's answer to
# http://stackoverflow.com/questions/12517451/python-automatically-creating-directories-with-file-output
def check_and_create_path(filename):
    if (not os.path.exists(os.path.dirname(filename))):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

# write content to the file at filename. Make the directory path to the given
# file if it does not exist.
def safeWrite(filename, content, dumpJSON=False):
    check_and_create_path(filename)
    out_file = open(filename, "w")
    if dumpJSON:
        content = json.dumps(content)
    out_file.write(content)
    out_file.close()

# get the content from a given file by reading it
# parseJSON is true if we should parse the contents as JSON first
def getContent(inFileName, parseJSON):
    inFile = open(inFileName, 'r')
    inContents = inFile.read()
    inFile.close()
    if parseJSON:
        return json.loads(inContents)
    else:
        return inContents


# ==============================================================================
# ======================== Text Preprocessing Functions ========================
# ==============================================================================


# unicode helper functions
def isCompatiblityChar(c):
    # from wikipedia
    return c in ["<initial>", "<medial>", "<final>", "<isolated>", "<wide>", "<narrow>", "<small>", "<square>", "<vertical>", "<circle>", "<noBreak>", "<fraction>", "<sub>", "<super>", "<compat>"]

def fullyDecomposeUnicodeChar(uChar):
    arr = unicodedata.decomposition(uChar).split(" ")
    # ignore compatibility stuff
    if (len(arr) >= 1 and isCompatiblityChar(arr[0])):
        arr = arr[1:]
    if (len(arr) == 1 and arr[0] == ''):
        arr = [uChar]
    else:
        for j in range(len(arr)):
            c = chr(int(arr[j], base=16))
            if (j == 0):
                arr[j] = fullyDecomposeUnicodeChar(c)
            else:
                arr[j] = c
    # for char in arr:
    #     print(i, unicodedata.name(char))
    return "".join(arr)

def fullyDecomposeUnicodeString(uStr):
    result = ""
    for i, c in enumerate(uStr):
        result += fullyDecomposeUnicodeChar(c)
    return result


def printUnicodeChar(c):
    print(("\'%s\'" % c), '\\u%04x' % ord(c), unicodedata.category(c), end=" ")
    try:
        print(unicodedata.name(c))
    except Exception as inst:
        print("NO NAME")

# remove punctuation
def removePunct(text, debugString):
    text = re.sub(r'\[p\. [\d]+\]', ' ', text) # no page nums
    text = re.sub(r'\%5,', ',', text) # %5,
    text = re.sub(r'\#\d*', ' ', text) # remove # signs
    text = re.sub(r'(\%(5|2|14))|[\*\u005e_]', ' ', text) # replace with spaces
    text = re.sub(r'(\&lt;|[\u00ab])', '<', text) # remove &lt;
    text = re.sub(r'(\&gt;|[\u00bb])', '>', text) # remove &gt;
    text = re.sub(r'(\&amp;)', '&', text) # remove &amp;
    text = re.sub(r'[@&\$\%\ufffd\u00b4\u00a8\u0060\u00bd]', '', text) # replace "replacement character", floating acute, diaresis, ½ with nothing
    text = re.sub(r'[\u2026]', '...', text) # replace ellipses
    text = re.sub(r'\u00e6', 'αε', text) # replace ae
    text = re.sub(r'\u0323\u0323\u0313\s', '.\'', text) # fix end quote issue
    text = re.sub(r'\u0323\u0323\u0313', '\u0313', text) # remove double under dot issues
    text = re.sub(r'\u0375\s', ', ', text) # fix end quote issue
    text = re.sub(r'[\u201c\u201d]', '"', text) # normalize quotes
    text = re.sub(r'（', ' (', text) # fix start paren issue
    text = re.sub(r'）', ') ', text) # fix end paren issue
    text = re.sub(r'[\u3008\u2329]', ' <', text) # left bracket
    text = re.sub(r'[\u3009\u232a]', '> ', text) # right bracket
    text = re.sub(r'[—\u2010]', '> ', text) # normalize dashes
    text = re.sub(r'\u1fe4(᾽)?([,:])\s', 'ρ\u1fbd\1 ', text) # remove final rho problems
    text = re.sub(r'\u1fe4(᾽)?\s', 'ρ\u1fbd ', text) # remove final rho problems
    text = re.sub(r'([ΒΓΔΖΘΚΛΜΝΞΠΡΣΤΦΧΨβγδζθκλμνξπρσςτφχψ])[\u0313\u0314\u1fbf]', '\1\u1fbd', text) # fix reverse comma issue
    text = re.sub(r'[\u00a7]+ \d+', ' ', text) # fix rho breathing issue
    text = re.sub(r'([\d\.\,;:\"\s])\u1fbf([\d\.\,;:\"\s])', '\1\'\2', text) # fix end quote as breathing
    text = re.sub(r'\u1fbe', ',', text) # fix comma as iota subscript
    text = re.sub(r'{', '(', text) # curly to paren
    text = re.sub(r'}', ')', text) # curly to paren
    text = re.sub(r'ā', 'α', text) # replace macron a
    text = re.sub(r'ü', 'υ', text) # replace umlaut u
    text = re.sub(r'\[?[¯˘×]+[\s¯˘×!]*\]?', ' ', text) # remove length notation

    text = re.sub(r'ς\d+(^\s)', 'σ\1', text) # remove digits with sigma
    text = re.sub(r'\d+-\d+', ' ', text) # remove digits in range
    text = re.sub(r'\d+', ' ', text) # remove digits

    text = re.sub(r'\s[῾‘\u2018\u2019]', ' \'', text) # fix start quote issue
    text = re.sub(r'\s(\':)?[\'<]‘', ' \"', text) # fix different start quote issue
    text = re.sub(r'‘[᾽>][,>]?\s', '\" ', text) # fix different end quote issue


    #
    # matches = re.finditer(r'[\s\S]{5}(a)[\s\S]{5}', text)
    # firstMatch = True
    # for m in matches:
    #     if (firstMatch):
    #         firstMatch = False
    #         print(debugString)
    #     print("<{%s}>" % m.group(0))

    # specific for our concerns

    text = re.sub(r'-[\s]*\n', '', text) # no words split over lines
    text = re.sub(r'-', ' ', text) # replace dashes with spaces
    text = re.sub(r'[,\.\[\]\(\)†<>:;¯⟦⟧\"\'!]', '', text) # no punct
    text = re.sub(r'[\s]+', ' ', text) # unify spaces
    return text


# given the name of a text and the line number, make
# adjustments as necessary
# TODO (future); the following should be able to be automated:
#   - feu, aiai, etc being a "fake" line
#   - line swaps where the numbers are given to us
#   - 969a that are given to us
#   - remove final dashes
#   - also, manual but meaningful to combine halflines where necesary

def getNextLineNum(textName, authorName, lineNum):

    # remaining errors are fine
    if (textName == "Agamemnon"):
        map = {
            1017: 1020,
            1202: 1204, # 2 line swap
            1204: 1203,
            1203: 1205,
            1409: 1409.5,
            1429: 1429.5,
            1529: 1529.5,
            1573: 1573.5,
            1595: 1595.5
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Eumenides"):
        map = {
            347: 350,
            362: 365,
            367: 354.5,
            354.5: 355.5,
            355.5: 356.5,
            356.5: 357.5,
            357.5: 358.5,
            358.5: 359.5,
            359.5: 368,
            380: 372.5,
            372.5: 373.5,
            373.5: 374.5,
            374.5: 375.5,
            375.5: 376.5,
            376.5: 381,
            755: 755.5,
        }
        if lineNum in map:
            return map[lineNum]
    # 195 stuff is fine
    elif (textName == "Libation Bearers"):
        map = {
            83: 83.5,
            124: 124.5,
            194: 194.5,
            226: 228,
            228: 227,
            227: 230,
            230: 229,
            229: 231,
            599: 599.5,
            640: 643,
            880: 880.5,
            951: 942.5,
            942.5: 943.5,
            943.5: 944.5,
            944.5: 945.5,
            945.5: 953,
            972: 962.5,
            962.5: 963.5,
            963.5: 964.5,
            964.5: 973,
            1008: 1008.5,
            1019: 1019.5,
            1039: 1041,
            1041: 1040,
            1040: 1042,
            1047: 1047.5
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Persians"):
        map = {
            886: 889,
            889: 889.5,
            909: 909.5,
            1010: 1012,
            1012: 1011,
            1011: 1013,
            1070: 1070.5
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Prometheus Bound"):
        map = {
            128: 128.5,
            134: 130.5,
            130.5: 135,
            143: 143.5,
            146: 146.5,
            147: 147.5,
            199: 199.5,
            343: 343.5,
            527: 530,
            531: 535,
            557: 560,
            566: 566.5,
            580: 580.5,
            581: 581.5,
            598: 598.5,
            906: 906.5,
            979: 979.5
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Seven Against Thebes"):
        map = {
            112: 115,
            117: 120,
            132: 135,
            136: 140,
            158: 158.5,
            345: 345.5,
            474: 474.5,
            517: 519,
            519: 518,
            518: 520,
            655: 655.5,
            827: 830,
            832: 832.5,
            833: 833.5,
            906: 906.5,
            959: 959.5,
            966: 966.5,
            980: 980.5,
            1059: 1059.5
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Suppliant Women"):
        map = {
            154: 154.5,
            175: 162.5,
            162.5: 163.5,
            163.5: 164.5,
            164.5: 165.5,
            165.5: 166.5,
            166.5: 167.5,
            167.5: 176,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Alcestis"):
        map = {
            94: 94.5,
            143: 146,
            149: 144,
            145: 150,
            204: 204.5,
            214: 214.5,
            227: 227.5,
            228: 228.5,
            256: 256.5,
            263: 263.5,
            276: 276.5,
            390: 390.5,
            391: 391.33,
            391.33: 391.67,
            391.67: 392,
            401: 401.5,
            407: 410,
            411: 411.5,
            412: 412.5,
            461: 461.5,
            465: 465.5,
            471: 471.5,
            475: 475.5,
            536: 536.5, # feu
            718: 718.5, # feu
            819: 819.5,
            861: 861.5,
            862: 862.5,
            872: 872.5,
            873: 873.5,
            874: 874.33,
            874.33: 874.67,
            874.67: 875,
            875: 875.5,
            889: 889.5, # aiai
            890: 890.5, # e e
            892: 892.5, # feu feu
            893: 893.5, # io moi moi
            894: 894.5,
            932: 935,
            987: 990,
            997: 1000,
            1101: 1101.5, # feu
            1119: 1119.33,
            1119.33: 1119.67,
            1119.67: 1120
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Andromache"):
        map = {
            69: 73,
            73: 70,
            72: 74,
            195: 199,
            200: 196,
            198: 201,
            203: 203.5,
            241: 241.33,
            241.33: 241.67,
            241.67: 242,
            364: 364.5,
            472: 475,
            530: 530.5,
            585: 585.5, # nai
            645: 647,
            647: 646,
            646: 648,
            767: 770,
            776: 780,
            786: 790,
            895: 895.5, # ea
            1012: 1015,
            1070: 1070.5, #wmoi moi
            1076: 1076.5,
            1202: 1205,
            1225: 1225.5, # iw iw
            1235: 1254,
            1254: 1236,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Bacchae"):
        map = {
            67: 67.5,
            73: 73.5,
            74: 74.5,
            86: 86.5,
            88: 88.5,
            145: 145.5,
            160: 164,
            166: 169,
            188: 188.5,
            385: 385.5,
            401: 401.5,
            576: 576.5, #iw
            595: 595.5, # a a
            846: 848,
            848: 847,
            847: 849,
            872: 872.5,
            892: 892.5,
            906: 906.5,
            966: 966.5,
            967: 967.5,
            968: 968.5,
            969: 969.5,
            970: 970.5,
            1010: 1013,
            1168: 1168.5,
            1175: 1175.5,
            1176: 1176.5,
            1181: 1181.25,
            1181.25: 1181.5,
            1181.5: 1181.75,
            1181.75: 1182,
            1184: 1184.5,
            1193: 1193.5,
            1195: 1195.5,
            1197: 1197.25,
            1197.25: 1197.5,
            1197.5: 1197.75,
            1197.75: 1198,
            1371: 1371.5,
            1372: 1372.5,
            1379: 1379.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Cyclops"):
        map = {
            146: 146.33,
            146.33: 146.67,
            146.67: 147,
            153: 153.5,
            154: 154.5,
            261: 261.5,
            301: 301.5,
            321: 321.5,
            359: 359.5,
            367: 370,
            371: 373,
            373: 372,
            372: 374,
            385: 392,
            392: 386,
            391: 393,
            397: 399,
            399: 398,
            398: 400,
            546: 546.5,
            561: 561.5,
            558: 558.5,
            568: 568.5,
            569: 569.5,
            612: 615,
            616: 616.5,
            625: 625.5,
            640: 640.5,
            656: 656.5, # iw iw
            669: 669.5,
            671: 671.5,
            672: 672.5,
            673: 673.5,
            674: 674.5,
            675: 675.5,
            680: 680.5,
            681: 681.5,
            682: 682.5,
            683: 683.5,
            684: 684.5,
            685: 685.5,
            686: 686.5,
            689: 689.5
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Electra" and authorName == "Euripides"):
        map = {
            140: 140.5,
            160: 160.5,
            167: 167.5,
            191: 191.5,
            262: 262.5, # feu
            281: 281.5, # feu
            366: 366.5, # feu
            463: 463.5,
            472: 472.5,
            556: 556.5, #ea
            578: 578.5,
            580: 580.5,
            581: 581.5,
            681: 683,
            683: 682,
            682: 684,
            693: 693.5,
            699: 699.5,
            713: 713.5,
            721: 721.5,
            747: 747.5, # ea ea
            968: 968.5, # feu
            988: 988.5, # iw
            1152: 1155,
            1181: 1181.5,
            1337: 1340,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Hecuba"):
        map = {
            54: 54.5, # feu
            77: 80,
            177: 177.5, # iw
            206: 206.5,
            706: 709,
            864: 864.5, # fue
            911: 911.5,
            921: 921.5,
            929: 929.5,
            939: 939.5,
            955: 955.5, #feu
            1035: 1035.5,
            1070: 1070.5, # a a
            1095: 1098,
            1102: 1105,
            1115: 1115.5, # ea
            1127: 1127.5,
            1283: 1283.5,
            1284: 1284.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Helen"):
        map = {
            98: 98.5, # nai
            173: 173.5,
            174: 174.5,
            178: 178.5,
            184: 184.5,
            187: 187.5,
            189: 189.5,
            210: 210.5,
            211: 211.5, # aiai aiai
            226: 226.5,
            231: 231.5,
            236: 236.5,
            241: 241.5,
            248: 248.5,
            249: 249.5,
            352: 352.5,
            356: 356.5,
            362: 362.5,
            366: 366.5,
            680: 680.5,
            681: 681.5,
            685: 685.5,
            1108: 1108.5,
            1111: 1111.5,
            1123: 1123.5,
            1126: 1126.5,
            1176: 1176.5, # ea
            1291: 1293,
            1293: 1292,
            1292: 1294,
            1318: 1318.5,
            1338: 1338.5,
            1476: 1476.5,
            1514: 1514.5,
            1630: 1630.5,
            1631: 1631.5,
            1632: 1632.5,
            1633: 1633.5,
            1634: 1634.5,
            1635: 1635.5,
            1636: 1636.5,
            1637: 1637.5,
            1638: 1638.5,
            1639: 1639.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Heracleidae"):
        map = {
            2: 2.5,
            149: 149.5,
            217: 217.33, # < >
            217.33: 217.67,
            217.67: 218,
            311: 311.5,
            320: 320.5,
            401: 403,
            409: 402,
            402: 410,
            661: 661.5, # < >
            683: 688,
            690: 687,
            687: 684,
            686: 691,
            717: 717.5, # feu
            739: 739.5, # feu
            805: 805.33, # < >
            805.33: 805.67,
            805.67: 806,
            947: 950,
            952: 948,
            949: 953,
            962: 962.5,
            969: 969.5, # a line
            970: 970.5, #a line
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Heracles"):
        map = {
            86: 88,
            89: 87,
            87: 90,
            111: 111.5,
            121: 121.5,
            125: 127,
            127: 126,
            126: 128,
            217: 217.5, # feu
            350: 350.5,
            365: 365.5,
            410: 410.5,
            427: 427.5,
            460: 460.5, # feu
            513: 513.5, # ea
            531: 531.5,
            628: 628.5, # a
            741: 744,
            752: 752.5,
            757: 757.5,
            764: 764.5,
            771: 771.5,
            772: 772.5, # theoi theoi
            791: 791.5,
            808: 808.5,
            873: 875,
            893: 893.5,
            896: 896.5,
            909: 909.5,
            911: 911.5,
            913: 913.5,
            914: 914.5,
            1008: 1010,
            1010: 1009,
            1009: 1011,
            1049: 1049.5,
            1051: 1051.5,
            1052: 1052.5,
            1054: 1054.5,
            1066: 1066.5,
            1067: 1067.5,
            1068: 1068.5,
            1069: 1069.5,
            1171: 1171.5, # ea
            1197: 1197.5,
            1396: 1396.5, # feu
            1417: 1417.5,
            1418: 1418.5,
            1419: 1419.5,
            1420: 1420.25,
            1420.25: 1420.50,
            1420.50: 1420.75,
            1420.75: 1421,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Hippolytus"):
        map = {
            103: 106,
            107: 104,
            105: 108,
            207: 207.5, # aiai
            310: 310.33,
            310.33: 310.67,
            310.67: 311,
            344: 344.5, # feu
            351: 351.5,
            362: 362.5,
            532: 535,
            542: 545,
            582: 585,
            668: 668.5,
            669: 669.5,
            724: 724.5,
            734: 734.5,
            744: 744.5,
            757: 760,
            772: 775,
            776: 776.33, # eswthen
            776.33: 776.67, # iou iou
            776.67: 777,
            808: 825,
            825: 810,
            812: 812.5,
            824: 826,
            856: 856.5, # ea ea
            1077: 1077.5, # feu
            1102: 1105,
            1107: 1110,
            1112: 1115,
            1117: 1120,
            1122: 1125,
            1132: 1135,
            1265: 1267,
            1267: 1266,
            1266: 1268,
            1312: 1312.5, #oimoi
            1325: 1325.5,
            1384: 1384.5, #iw moi moi
            1385: 1385.5,
            1386: 1386.5,
            1390: 1390.5, # ea
            1414: 1414.5, # feu
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Ion"):
        map = {
            151: 151.5,
            153: 153.5, # ea ea
            170: 170.5, # ea ea
            189: 189.5,
            217: 217.5,
            220: 220.5,
            221: 221.5,
            222: 222.5,
            223: 223.5,
            231: 231.5,
            233: 233.5,
            235: 235.5,
            240: 240.5, # ea
            275: 275.5, #eien
            330: 330.5, # feu
            501: 501.5,
            508: 510,
            530: 530.5,
            531: 531.5,
            532: 532.5,
            533: 533.5,
            534: 534.5,
            535: 535.5,
            536: 536.5,
            537: 537.5,
            538: 538.5,
            539: 539.5,
            540: 540.5,
            541: 541.5,
            542: 542.5,
            543: 543.5,
            544: 544.5,
            545: 545.5,
            546: 546.5,
            547: 547.5,
            548: 548.5,
            549: 549.5,
            550: 550.5,
            551: 551.5,
            552: 552.5,
            553: 553.5,
            554: 554.5,
            555: 555.5,
            556: 556.5,
            557: 557.5,
            558: 558.5,
            559: 559.5,
            560: 560.5,
            561: 561.5,
            562: 562.5,
            685: 688,
            741: 741.5, # idou
            763: 763.33,
            763.33: 763.67,
            763.67: 764,
            764: 764.5,
            766: 766.5,
            767: 767.5,
            768: 768.5,
            803: 803.5,
            907: 907.5, # wh
            960: 960.5, # feu
            1255: 1255.5,
            1256: 1256.5,
            1257: 1257.5,
            1258: 1258.5,
            1311: 1311.5, # feu
            1423: 1423.5, #  idou
            1452: 1452.5,
            1453: 1453.5,
            1454: 1454.5,
            1472: 1472.5,
            1478: 1478.5,
            1481: 1481.5,
            1482: 1482.5,
            1496: 1496.5,
            1515: 1515.5, # feu
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Iphigenia in Aulis"):
        map = {
            114: 1,
            2: 2.5,
            3: 3.33,
            3.33: 3.67,
            3.67: 4,
            16: 16.5,
            48: 115,
            140: 140.5,
            148: 148.5,
            226: 229,
            310: 310.5,
            317: 317.5, # ea
            394: 394.5,
            414: 414.5,
            643: 643.5, # ea
            665: 665.5, # feu
            710: 710.5, # feu
            738: 738.5, # pithou
            783: 783.5,
            976: 976.5, # feu
            1082: 1082.5,
            1123: 1123.5, # feu
            1131: 1131.5, # ea
            1132: 1132.5,
            1138: 1138.5,
            1185: 1185.5, # eien
            1286: 1289,
            1297: 1299,
            1313: 1313.5,
            1341: 1341.5,
            1342: 1342.5,
            1345: 1345.5,
            1346: 1346.5,
            1347: 1347.5,
            1348: 1348.5,
            1349: 1349.5,
            1350: 1350.5,
            1351: 1351.5,
            1352: 1352.5,
            1353: 1353.5,
            1354: 1354.5,
            1355: 1355.5,
            1356: 1356.5,
            1357: 1357.5,
            1358: 1358.5,
            1359: 1359.5,
            1360: 1360.5,
            1361: 1361.5,
            1362: 1362.5,
            1363: 1363.5,
            1364: 1364.5,
            1365: 1365.5,
            1366: 1366.5,
            1367: 1367.5,
            1368: 1368.5,
            1459: 1459.5,
            1460: 1460.5,
            1464: 1464.5,
            1465: 1465.5,
            1466: 1466.5,
            1510: 1510.5, # iw iw
            1537: 1537.5,
            1601: 1601.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Iphigenia in Tauris"):
        map = {
            150: 150.5,
            291: 291.5,
            439: 439.5,
            467: 467.5, # eien
            471: 471.5, # feu
            558: 558.5, # feu
            626: 626.5, # feu
            642: 644,
            741: 741.5, # nai
            779: 779.5,
            780: 780.5, # w theoi
            865: 867,
            867: 866,
            866: 868,
            875: 878,
            887: 890,
            891: 894,
            1156: 1156.5,
            1203: 1203.5,
            1204: 1204.5,
            1205: 1205.5,
            1206: 1206.5,
            1207: 1207.5,
            1208: 1208.5,
            1209: 1209.5,
            1210: 1210.5,
            1211: 1211.5,
            1212: 1212.5,
            1213: 1213.5,
            1215: 1215.5,
            1216: 1216.5,
            1217: 1217.5,
            1218: 1218.5,
            1219: 1219.5,
            1220: 1220.5,
            1221: 1221.5,
            1241: 1241.5,
            1246: 1246.5,
            1251: 1254,
            1270: 1270.5,
            1271: 1271.5,
            1277: 1280,
            1282: 1284,
            1308: 1308.5, # feu
            1441: 1441.5,
            1469: 1469.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Medea"):
        map = {
            10: 10.33,
            10.33: 10.67,
            10.67: 11,
            96: 96.5, # iw
            110: 110.5, # aiai
            143: 143.5, # aiai
            156: 156.5,
            181: 181.5,
            182: 182.5,
            209: 209.5,
            212: 214,
            292: 292.5, # feu feu
            365: 365.5,
            417: 420,
            432: 435,
            436: 436.5,
            627: 630,
            637: 640,
            827: 830,
            832: 835,
            837: 840,
            842: 845,
            925: 929,
            931: 926,
            928: 932,
            1007: 1007.5, # aiai
            1008: 1008.5, # aiai mal authis
            1055: 1055.5, # a a
            1103: 1103.5,
            1270: 1270.5, # iw moi
            1270.5: 1273,
            1274: 1271,
            1272: 1275,
            1277: 1280,
            1316: 1316.5,
            1397: 1397.5,
            1398: 1398.5,
            1402: 1402.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Orestes"):
        map = {
            148: 148.5,
            173: 173.5,
            175: 178,
            182: 185,
            194: 194.5,
            197: 200,
            201: 204,
            274: 274.5, # a a
            276: 276.5, # ea
            338: 340,
            340: 339,
            339: 341,
            774: 774.5,
            775: 775.5,
            776: 776.5,
            777: 777.5,
            778: 778.5,
            779: 779.5,
            780: 780.5,
            781: 781.5,
            781.5: 783,
            783: 783.5,
            783.5: 782,
            782: 782.5,
            782.5: 784,
            784: 784.5,
            785: 785.5,
            786: 786.5,
            787: 787.5,
            788: 788.5,
            789: 789.5,
            790: 790.5,
            791: 791.5,
            792: 792.5,
            793: 793.5,
            794: 794.5,
            795: 795.5,
            796: 796.5,
            797: 797.5,
            798: 798.5,
            982: 982.5,
            983: 983.5,
            984: 984.5,
            991: 991.5,
            1004: 1004.5,
            1013: 1013.5,
            1051: 1051.5, # feu
            1155: 1155.5, # feu
            1235: 1235.5,
            1236: 1236.5,
            1238: 1238.5,
            1262: 1265,
            1281: 1284,
            1292: 1295,
            1346: 1346.5,
            1347: 1347.5,
            1353: 1353.5, # iw iw filai
            1386: 1386.5,
            1400: 1400.5,
            1407: 1407.5,
            1446: 1446.5,
            1448: 1448.5,
            1455: 1455.5,
            1458: 1458.5,
            1460: 1460.5,
            1461: 1461.5,
            1465: 1465.5,
            1469: 1469.5,
            1472: 1472.5,
            1473: 1473.5, # iaxa
            1474: 1474.5,
            1482: 1482.5,
            1488: 1488.5,
            1491: 1491.5,
            1492: 1492.5,
            1493: 1493.5,
            1494: 1494.5,
            1496: 1496.5,
            1499: 1499.5,
            1525: 1525.33,
            1525.33: 1525.67,
            1525.67: 1526,
            1526: 1526.5,
            1537: 1537.5, # iw iw tuxa
            1545: 1545.5,
            1598: 1598.5,
            1600: 1600.5,
            1601: 1601.5,
            1602: 1602.5,
            1603: 1603.5,
            1604: 1604.5,
            1605: 1605.5,
            1606: 1606.5,
            1607: 1607.5,
            1608: 1608.5,
            1609: 1609.5,
            1610: 1610.5,
            1611: 1611.5,
            1612: 1612.5,
            1613: 1613.5,
            1614: 1614.5,
            1615: 1615.5,
            1616: 1616.5,
            1617: 1617.5,
            1679: 1679.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Phoenissae"):
        map = {
            123: 123.5,
            133: 133.5,
            161: 161.5,
            171: 171.5,
            181: 181.5, # iw
            204: 204.5, # this is not an actually problem, seems to be on perseus.
            306: 306.5,
            603: 603.5,
            604: 604.5,
            605: 605.5,
            606: 606.5,
            607: 607.5,
            608: 608.5,
            609: 609.5,
            610: 610.5,
            611: 611.5,
            612: 612.5,
            613: 613.5,
            614: 614.5,
            615: 615.5,
            616: 616.5,
            617: 617.5,
            618: 618.5,
            619: 619.5,
            620: 620.5,
            621: 621.5,
            622: 622.5,
            623: 623.5,
            624: 624.5,
            666: 669,
            669: 668,
            668: 667,
            667: 670,
            790: 790.5,
            795: 795.5,
            806: 806.5,
            896: 896.5,
            897: 897.5,
            980: 980.5,
            981: 981.5,
            982: 982.5,
            983: 983.5,
            984: 984.5,
            985: 985.5,
            1019: 1019.5, # ebas ebas
            1020: 1020.5,
            1035: 1035.5,
            1043: 1043.5,
            1045: 1045.5,
            1060: 1060.5,
            1273: 1273.5,
            1274: 1274.5,
            1275: 1275.5,
            1276: 1276.5,
            1277: 1277.5,
            1278: 1278.5,
            1538: 1538.5,
            1560: 1560.5, # aiai
            1561: 1561.5,
            1567: 1567.5,
            1606: 1606.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Rhesus"):
        map = {
            15: 15.5,
            16: 16.5,
            17: 17.5,
            18: 18.5,
            333: 336,
            338: 334,
            335: 339,
            369: 369.5,
            376: 376.5,
            377: 377.5,
            573: 573.5, # ea
            685: 685.5,
            686: 686.5,
            687: 687.33,
            687.33: 687.67,
            687.67: 688,
            688: 688.33,
            688.33: 688.67,
            688.67: 689,
            689: 689.5,
            730: 730.5, # iw iw
            733: 733.5, # iw iw,
            798: 798.5, # a a
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Suppliants"):
        map = {
            64: 64.5,
            78: 78.5,
            86: 86.5,
            91: 91.5, # ea:
            276: 279,
            366: 366.5,
            371: 371.5,
            290: 290.5, # aiai
            292: 292.5,
            513: 513.5,
            584: 584.5,
            588: 590,
            590: 589,
            589: 591,
            658: 662,
            662: 659,
            661: 664,
            665: 663,
            663: 666,
            696: 699,
            702: 697,
            698: 703,
            805: 805.5, # iw iw
            806: 806.5, # aiai
            817: 817.5, # exeis exeis
            818: 818.5, # aiai
            820: 820.5,
            971: 971.5,
            1030: 1030.5,
            1114: 1114.5, # iw iw:
            1132: 1132.5, # apais, apais
            1135: 1135.5, # iw iw
            1140: 1140.5,
            1146: 1146.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Trojan Women"):
        map = {
            140: 140.5,
            170: 172,
            172: 171,
            171: 173,
            173: 173.5,
            174: 174.5,
            186: 186.5, # iw iw
            190: 190.5, # feu feu
            191: 191.5,
            192: 192.5, # aiai
            202: 202.5,
            239: 239.5, # aiai tode
            241: 241.5, # aiai, tin h
            309: 309.5,
            320: 320.5,
            327: 327.5,
            340: 340.5,
            345: 345.5,
            574: 574.5,
            577: 577.5, # oimoi
            578: 578.5, # aiai
            580: 580.5, # w zeu
            581: 581.5, # tekea
            582: 582.5,
            583: 583.5, # feu feu
            585: 585.5,
            586: 586.5,
            595: 595.5,
            596: 596.5,
            598: 598.5,
            600: 600.5,
            601: 601.5,
            602: 602.5,
            617: 617.5, # feu feu
            826: 829,
            945: 945.5, # eien
            1082: 1085,
            1118: 1118.5, # iw iw,
            1168: 1168.5,
            1216: 1216.5,
            1229: 1229.5, # aiai.
            1230: 1230.5,
            1251: 1251.5, # iw iw:
            1255: 1255.5, # ea ea:
            1302: 1302.5, # e e.
            1310: 1310.5,
            1311: 1311.5,
            1312: 1312.5, # iw
            1317: 1317.5, # e e.
            1327: 1327.5,
            1328: 1328.5, # iw:
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Ajax"):
        map = {
            215: 215.5,
            222: 225,
            232: 235,
            247: 250,
            252: 255,
            401: 401.5,
            412: 412.5, # iw
            555: 555.5,
            591: 591.5,
            592: 592.5,
            593: 593.5,
            594: 594.5,
            602: 605,
            617: 620,
            622: 625,
            697: 700,
            702: 705,
            880: 883,
            907: 910,
            927: 930,
            956: 960,
            981: 981.5,
            982: 982.5,
            983: 983.5,
            985: 985.5,
            1187: 1190,
            1192: 1195,
            1395: 1395.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Antigone"):
        map = {
            107: 110,
            119: 119.5,
            121: 125,
            161: 161.5,
            322: 322.5, # feu
            332: 335,
            336: 336.5,
            340: 343,
            361: 365,
            367: 370,
            371: 375,
            587: 590,
            597: 600,
            602: 605,
            607: 610,
            617: 620,
            782: 785,
            786: 790,
            792: 795,
            796: 800,
            807: 810,
            812: 815,
            827: 830,
            831: 834,
            842: 845,
            847: 850,
            861: 865,
            867: 870,
            947: 950,
            962: 965,
            967: 970,
            977: 980,
            1047: 1047.5, # feu
            1122: 1125,
            1142: 1145,
            1152: 1155,
            1261: 1261.5, # iw
            1284: 1284.5, # iw.
            1321: 1325,
            1342: 1345,
        }
        if lineNum in map:
            return map[lineNum]
    # 1058-60 is fine
    elif (textName == "Electra" and authorName == "Sophocles"):
        map = {
            477: 480,
            482: 485,
            497: 500,
            837: 840,
            1020: 1020.5, # feu
            1057: 1060,
            1072: 1075,
            1086: 1089,
            1209: 1209.5,
            1220: 1220.5,
            1221: 1221.5,
            1222: 1222.5,
            1224: 1224.5,
            1225: 1225.5,
            1226: 1226.5,
            1247: 1250,
            1264: 1264.5,
            1267: 1270,
            1347: 1347.5,
            1349: 1349.5,
            1400: 1400.5,
            1404: 1404.5,
            1424: 1424.5,
            1436: 1436.5,
            1484: 1484.5,
            1502: 1502.5,
            1503: 1503.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Oedipus at Colonus"):
        map = {
            46: 46.5,
            173: 173.5,
            178: 178.33,
            178.33: 178.67,
            178.67: 179,
            195: 195.5,
            198: 198.5, # iw moi moi.
            212: 212.5,
            220: 220.5,
            221: 221.5,
            222: 222.5,
            223: 223.5,
            224: 224.5,
            237: 237.5,
            253: 253.5,
            311: 311.5,
            321: 321.5,
            327: 327.5,
            328: 328.5,
            329: 329.5,
            330: 330.5,
            331: 331.5,
            332: 332.5,
            333: 333.5,
            518: 518.5, # wmoi.
            519: 519.5, # feu feu.
            532: 532.5, # w zeu.
            535: 535.5, # iw
            537: 537.5,
            538: 538.5,
            539: 539.5,
            543: 543.5,
            544: 544.5,
            545: 545.5,
            546: 546.5,
            547: 547.5,
            560: 560.5,
            565: 565.5,
            652: 652.5,
            653: 653.5,
            654: 654.5,
            655: 655.5,
            656: 656.5,
            707: 710,
            722: 722.5,
            819: 819.5, # oimoi.
            821: 821.5,
            832: 832.5,
            834: 834.5,
            835: 835.5,
            840: 840.5,
            845: 845.5,
            846: 846.5,
            847: 847.5,
            856: 856.5,
            860: 860.5,
            861: 861.5,
            864: 864.5,
            880: 880.5,
            883: 883.5,
            896: 896.5,
            970: 970.5,
            1075: 1075.5,
            1081: 1085,
            1099: 1099.5,
            1102: 1102.5,
            1107: 1107.5,
            1108: 1108.5,
            1109: 1109.5,
            1169: 1169.5,
            1170: 1170.5,
            1205: 1205.5,
            1217: 1220,
            1227: 1230,
            1232: 1235,
            1252: 1252.5,
            1438: 1438.5,
            1441: 1441.5,
            1442: 1442.5,
            1452: 1455,
            1467: 1470,
            1477: 1480,
            1483: 1486,
            1496: 1500,
            1583: 1583.5,
            1676: 1676.5,
            1677: 1677.5,
            1692: 1695,
            1695: 1699,
            1705: 1705.5,
            1706: 1706.5,
            1707: 1707.5,
            1708: 1708.5,
            1715: 1719,
            1723: 1723.5,
            1724: 1724.5,
            1739: 1739.5,
            1741: 1741.5,
            1743: 1743.5,
            1747: 1747.5,
            1759: 1765,
            1765: 1765.5,
            1766: 1766.5,
            1767: 1767.5,
            1768: 1768.5,
            1769: 1769.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Oedipus Tyrannus"):
        map = {
            162: 162.5,
            166: 169,
            187: 190,
            207: 210,
            487: 490,
            492: 495,
            496: 500,
            502: 505,
            506: 510,
            626: 626.5,
            627: 627.5,
            628: 628.5,
            629: 629.5,
            662: 665,
            681: 681.5,
            897: 900,
            902: 905,
            905: 905.5,
            1087: 1090,
            1092: 1095,
            1102: 1105,
            1107: 1110,
            1173: 1173.5,
            1174: 1174.5,
            1175: 1175.5,
            1176: 1176.5,
            1200: 1200.5,
            1208: 1208.5,
            1217: 1217.5,
            1277: 1277.5,
            1300: 1300.5,
            1332: 1335,
            1342: 1345,
            1352: 1355,
            1361: 1365,
            1516: 1516.5,
            1517: 1517.5,
            1518: 1518.5,
            1519: 1519.5,
            1520: 1520.5,
            1521: 1521.5,
            1522: 1522.5,
        }
        if lineNum in map:
            return map[lineNum]
    elif (textName == "Philoctetes"):
        map = {
            54: 54.5,
            201: 201.5,
            265: 265.5,
            392: 395,
            397: 400,
            466: 466.5,
            511: 515,
            589: 589.5,
            590: 590.5,
            677: 680,
            693: 696,
            713: 716,
            722: 725,
            731: 731.5, # aa, aa.
            737: 740,
            752: 752.5,
            753: 753.5,
            756: 756.5,
            791: 795,
            809: 809.33,
            809.33: 809.67,
            809.67: 810,
            812: 812.5,
            813: 813.33,
            813.33: 813.67,
            813.67: 814,
            816: 816.25,
            816.25: 816.5,
            816.5: 816.75,
            816.75: 817,
            860: 860.5,
            917: 917.5,
            922: 922.5, # this is a dumb line split
            974: 974.5,
            981: 981.5,
            994: 994.5,
            1001: 1001.5,
            1083: 1086,
            1103: 1106,
            1137: 1140,
            1211: 1211.5,
            1218: 1218.5,
            1257: 1257.5,
            1276: 1276.5,
            1277: 1277.5,
            1303: 1303.5,
            1305: 1305.5,
            1355: 1355.5,
            1402: 1402.5,
            1403: 1403.5,
            1404: 1404.5,
            1405: 1405.5,
            1406: 1406.5,
            1407: 1407.33,
            1407.33: 1407.67,
            1407.67: 1408,
        }
        if lineNum in map:
            return map[lineNum]
    # TODO
    elif (textName == "Trachiniae"):
        map = {
            107: 110,
            115: 120,
            122: 125,
            127: 130,
            137: 140,
        }
        if lineNum in map:
            return map[lineNum]


    # automatically handle added lines
    if (lineNum % 1 == 0.5):
        return lineNum + 0.5

    # default
    return lineNum + 1

# Python's XML parser doesn't like Perseus including raw text and subchildren
# in the same element, so this extracts it from the line xml element
def getLineTextXML(xml):
    t = xml.text
    if (t):
        return t
    else:
        elementText = ET.tostring(xml, encoding="utf8").decode(encoding="utf8")
        lineText = re.sub(r'<[^>]*>', r'', elementText)
        return lineText

# parse the TEI data
def parse_TEI_lines(xml, textName, authorName, book):
    # remove notes and bibliography
    noNotes = re.sub(r'<note[\S\s]*?/note>', " ", xml)
    noBibl = re.sub(r'<bibl[\S\s]*?/bibl>', " ", noNotes)
    noForeign = re.sub(r'<foreign lang="la"[\S\s]*?/foreign>', " ", noBibl)
    xml = re.sub(r'</div1>[\S\s]*?<div1[\S\s]*?>', " ", noForeign)
    xml = re.sub(r'</body>[\S\s]*?<body[\S\s]*?>', " ", xml)


    # grab all of the lines in the document
    try:
        data = ET.fromstring(xml)
    except ET.ParseError as err:
        print(xml)
        print(err)
        raise("Failed")

    linesFound = []

    for lineXML in data.iter('l'):
        lineText = getLineTextXML(lineXML)

        rawLine = ET.tostring(lineXML, encoding="utf8").decode(encoding="utf8")
        linesFound.append([lineText, rawLine])

    # aka no lines were found
    if (len(linesFound) == 0):
        for lineXML in data.iter('p'):
            paragraphText = ET.tostring(lineXML, encoding="utf8").decode(encoding="utf8") #
            split = paragraphText.split("<lb")
            for line in split:
                if (line.startswith("<p")):
                    fixedLine = line
                else:
                    fixedLine = "<lb" + line;
                lineText = re.sub(r'<[^>]*>', r'', fixedLine)

                linesFound.append([lineText, fixedLine])

    # save and return the lines we found
    lineStart = 1

    if (textName == "Iphigenia in Aulis"):
        lineStart = 49

    lineNum = lineStart

    lines = []

    diff = 0
    for pair in linesFound:
        lineText, rawText = pair

        matches = re.finditer(r'n=\"(\d+)\"', rawText)
        for m in matches:
            targetLine = int(m.group(1))

            if ((textName == "Libation Bearers" and targetLine == 966) or
                (textName == "Prometheus Bound" and targetLine == 575)):
                continue

            if (targetLine - lineNum == 1):
                lineNum += 1
                #print("Skipped a line at %s %d" % (textName, lineNum))

            if not(targetLine - lineNum == diff):
                print("%s: should be %d but my count said %d" % (textName, targetLine, lineNum))
                diff = targetLine - lineNum

            break;

        # this fixes an issue with perseus where there is a weird 3 hanging out
        lineText = re.sub(r'\d', r'', lineText)

        # if the text has content
        if ((len(lineText) > 0) and not(lineText.isspace())):
            line = {"line_text": lineText, "poem": textName, "book": book, "line_number": lineNum}
            lines.append(line)
            lineNum = getNextLineNum(textName, authorName, lineNum)

    return lines


# parse the TEI data for a full book
def parse_TEI_full_book(xml):
    # remove notes and bibliography
    noNotes = re.sub(r'<note[\S\s]*?/note>', " ", xml)
    noBibl = re.sub(r'<bibl[\S\s]*?/bibl>', " ", noNotes)
    noForeign = re.sub(r'<foreign lang="la"[\S\s]*?/foreign>', " ", noBibl)
    # remove all the xml tags since we just need the whole text
    noTags = re.sub(r'<[^>][\S\s]*?>', " ", noForeign)
    return noTags
