# Finding censorship in 16th century Latin prints

(Tested with Python 3.8 on Linux and Windows.)

## Installation
* Create a new environment with Python 3.8 using [venv](https://docs.python-guide.org/dev/virtualenvs/) or [conda](https://docs.anaconda.com/), e.g. `conda create --name dh_blog python=3.8`.
* Activate the new environment, e.g. `conda activate dh_blog`.
* Clone this repository.
* Use pip to install the required Python packages: `pip install -r requirements.txt`.
* Download [`hunspell-la.zip`](https://latin-dict.github.io/docs/hunspell-la.zip), the Latin Hunspell dictionary by Karl Zeiler and Jean-Pierre Sutto, and unzip it to the project folder (“resolve_abbreviations”).

## Usage
* Read the blog article on https://dhlab.hypotheses.org/2271.
* Execute `python normalize_and_compre.py` and follow the command line instructions.

## Description
* `simple_diff.py` demonstrates the use of Python's [difflib](https://docs.python.org/3/library/difflib.html)
* `simple_diff_2.py` adds markup to difflib's output using combining unicode characters.
* `simple_diff_3.py` adds an intermediate step separating the evaluation of difflib's output and the rendering of the markup. This is helpful if you want to integrate the logic into a proper graphical user interface.
* The other scripts are explained [here](https://github.com/gedoensmanagement/resolve_abbreviations).

