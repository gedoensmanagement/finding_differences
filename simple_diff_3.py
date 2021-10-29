import difflib

list1 = ["Finding", "diferences", "is", "complicated", "yet", "it", "could", "be", "so", "easy", "."]
list2 = ["Finding", "differences", "is", "easy", "."]

d = difflib.Differ()
delta = d.compare(list1, list2)  # returns a generator
delta = [*delta]  # converts the generator into a list

# Process the output of difflib:

# Define a variable to cache the data:
pairs = []
# Define pointers for list1 and list2:
position_d1 = 0
position_d2 = 0

for line in delta:
    # Break out of the for-loop if the position of the pointers exceed the length of the input lists:
    if position_d1 + 1 > len(list1) or position_d2 + 1 > len(list2):
        break

    # Extract the code at the beginning of each line and the data:
    code = line[:1]
    data = line[2:]

    # Build a list of output pairs according to the code:
    if code == "?" or code == "":
        pass
    elif code == " ":
        pairs.append([code, list1[position_d1], list2[position_d2]])
        position_d1 += 1
        position_d2 += 1
    elif code == "+":
        pairs.append([code, "", list2[position_d2]])
        position_d2 += 1
    elif code == "-":
        pairs.append([code, list1[position_d1], ""])
        position_d1 += 1

# Markup with combining unicode characters
def strikethrough(text):
    return ''.join([u'\u0336{}'.format(c) for c in text])

def underline(text):
    return ''.join([u'\u0332{}'.format(c) for c in text])

# Add markup and print the result to the console:
output = []
for pair in pairs:
    if pair[0] == " ":
        output.append(pair[1])
    elif pair[0] == "-":
        output.append(strikethrough(pair[1]))
    elif pair[0] == "+":
        output.append(underline(pair[2]))

print(" ".join(output))