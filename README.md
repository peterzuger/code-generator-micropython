<h2 align="center">MicroPython code generator</h2>

<p align="center">
<a href="https://github.com/peterzuger/code-generator-micropython/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/peterzuger/code-generator-micropython"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

## Table of Contents
+ [About](#about)
+ [Getting Started](#getting_started)
+ [Usage](#usage)

## About <a name = "about"></a>
This is a code generator for
[micropython](https://github.com/micropython/micropython).

MicroPython has multiple ways of including your code into an
application, one of those is so called frozen bytecode. See
[this](https://docs.micropython.org/en/latest/reference/packages.html)
for more info.

The problem with frozen bytecode is that if a frozen module is
`import`'ed all of it is loaded into RAM. When a Project contains
large dictionary's that are accessed very frequently this can quickly
eat up a lot of the RAM available.

This problem does not exist with
[C-modules](https://docs.micropython.org/en/latest/develop/cmodules.html),
since C modules are normal C code that gets integrated into the
MicroPython executable. They don't get loaded into RAM when they are
imported in Python.

But writing C modules for micropython dictionary's is very tedious,
and the resulting code is not very readable. This is why this code
generator was created, it allows you to write your dictionary's in
your normal `.py` files with all the comments and decorations that you
may want to describe your dictionary. This code is then taken by this
code generator and a C module with the exact contents is created that
can then be imported without taking up precious RAM.


## Getting Started <a name = "getting_started"></a>

### Prerequisites
This generator does not have any prerequisites apart from a standard
[Python 3](https://www.python.org/) install.


## Usage <a name = "usage"></a>
This generator is currently lacking any code generation options, the C
code is just generated in a fixed fashion.

### Example
Given the example file `test.py`:
```python
# comment ignored by the generator

dictionary = {
    "HELLO":1,
    "WORLD":2
}

# Formattion is ignored too !
dict={"BAD":1,"FORMATTING":"YES"}
```

A C module containing the same 2 dictionary's can be created as
follows:
```bash
./generator.py --filename test.py
```

The generated module will be in the folder test. The module name will
be "test" which is taken from the basename of the provided file.

They can also be specified on the commandline using `--directory` and
`--modulename`.
