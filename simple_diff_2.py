import difflib

list1 = ["Finding", "diferences", "is", "complicated", "yet", "it", "could", "be", "so", "easy", "."]
list2 = ["Finding", "differences", "is", "easy", "."]

d = difflib.Differ()
delta = d.compare(list1, list2)  # returns a generator
delta = [*delta]  # converts the generator into a list

# Functions providing markup with combining unicode characters
def strikethrough(text):
    return ''.join([u'\u0336{}'.format(c) for c in text])

def underline(text):
    return ''.join([u'\u0332{}'.format(c) for c in text])

# Process the differences found with difflib:
output = []
for line in delta:
    # Extract the code and the data from each line:
    code = line[:1]
    data = line[2:]

    # Add markup:
    if code == " ":
        output.append(data)
    elif code == "-":
        output.append(strikethrough(data))
    elif code == "+":
        output.append(underline(data))

print(" ".join(output))