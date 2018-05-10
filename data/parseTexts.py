# Go through all downloaded raw texts and convert them to simple text, removing XML and punctuation
import utils
import unicodedata

RAW_FOLDER = "rawTexts/"
PARSED_FOLDER = "texts/"

# given a location, convert it from XML to the format we want
def convertBook(location):
    filename = loc.replace(RAW_FOLDER, "")
    newLoc = PARSED_FOLDER+filename
    t = utils.XMLText(loc)
    res = t.convertFromXML()
    utils.safeWrite(newLoc, res, True)
    return newLoc, res["booksRaw"]

# get the available texts and count them up
available = utils.getContent(RAW_FOLDER + "available.json", True)

numTexts = 0
for o in available:
    workLocs = o["works"]
    for w in workLocs:
        numTexts += 1

# Parse each book
i = 1
allBooks = []
for o in available:
    workLocs = o["works"]
    for w in workLocs:
        if (i % 20 == 0):
            print("%d out of %d (%.2f%%)" % (i, numTexts, (100*i/numTexts)))
        loc = w["location"]
        if (True or i == TARGET_BOOK):
            newLoc, books = convertBook(loc)
            allBooks.extend(books)
            w["location"] = newLoc
        i += 1

utils.safeWrite(PARSED_FOLDER + "available.json", available, True)
print("Done.")

# If desired, analyze the unicode characters in the processed texts.
countChars = False#True#
if countChars:
    print("Counting Chars")
    chars = {}
    for b in allBooks:
        bookText = b["bookText"]
        for char in bookText:
            chars[char] = True

    sortedChars = sorted(list(chars.keys()))


    for c in sortedChars:
        utils.printUnicodeChar(c)
    print("======")

    if False:
        decomposedChars = {}
        for c in sortedChars:
            res = utils.fullyDecomposeUnicodeChar(c)
            for newC in res:
                decomposedChars[newC] = True

        sortedDecompChars = sorted(list(decomposedChars.keys()))

        for c in sortedDecompChars:
            utils.printUnicodeChar(c)
