# Odikon 2.0: A Scansion Tool for Ancient Greek Texts

**Note**: If you are looking for scanned lines, check out David Chamberlain's [hypotactic](http://hypotactic.com/latin/index.html?Use_Id=about), which includes scansion for much of Greek poetry. Because there are so many extremely uncommon rules, a database of scanned lines is going to be better than a tool like this.

Odikon is a tool for performing metrical scansion of Ancient Greek texts. It can provide scansions of single lines given the meter for that line as well as guessing the scansion of a given line.

Currently, the two meters it supports are Iambic Trimeter and Anapestic Tetrameter.

More information on the functionality available in Odikon can be found in the readme for the `odikon` folder. At the top level, we have an evaluation script, which runs the following experiments:

1) Evaluates the single line scanner on around 400 lines of Euripides.
2) Evaluates the meter identification on four plays, two from Euripides, one from Aeschylus, and one from Sophocles.
3) Uses the tool to calculate the frequency of resolution in the plays of Euripides, comparing it to the results of Caedel's "Resolved Feet in the Trimeters of Euripides and the Chronology of the Plays" (*The Classical Quarterly*, 1941).


Text and evaluation data are found in the `data/` folder.
