# Odikon 2.0 - Available Features

Odikon provides the following functions:

- scanLine(line, meter): given a line and a meter ("IAMBS" or "ANAPESTS"), return the best scansion of that line if one is found.
- skipLine(line): return true if this line contains only a short exclamation.
- getScanString(scan): given a scansion object, return a simple string like "--|vv-"
- guessMeter(line): given a line, return the best guess for the lines meter.
- guessMeterSections(lines): given a list of lines, segment them into groups by meter. Returns two versions, one where it groups them by best guess per line, and one where it avoids single lines of one meter surrounded by two lines of another meter.
