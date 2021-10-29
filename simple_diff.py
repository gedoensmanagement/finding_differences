import difflib

list1 = ["Finding", "diferences", "is", "complicated", "."]
list2 = ["Finding", "differences", "is", "easy", "."]

d = difflib.Differ()
delta = d.compare(list1, list2)  # returns a generator
delta = [*delta]  # converts the generator into a list

for line in delta:
    print(line)