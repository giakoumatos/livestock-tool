"""The model contract, as in the crop tool's models: each model is a class
whose docstring lists its inputs and outputs with units, that reads the
inputs named in `_input_variables` and returns its outputs from `compute()`
under keys prefixed with the model's name.

On top of the crop tool, each model writes `trace`: the calculation in
words with its numbers and the table every factor comes from, which the
flow comments are made of.
"""


class Model:
    _input_variables = ()

    def __init__(self, inputs):
        self.inputs = inputs
        for key in self._input_variables:
            setattr(self, key, inputs[key])
        self.trace = {}

    def note(self, key, text):
        self.trace.setdefault(key, []).append(text)

    def compute(self):
        raise NotImplementedError


def fmt(x, digits=4):
    """A number as a comment shows it: four significant digits, no
    scientific notation for the sizes found in a herd's year."""
    if x == 0:
        return '0'
    a = abs(x)
    if a >= 1000:
        return f'{x:,.0f}'
    if a >= 1:
        text = f'{x:.{max(digits - len(str(int(a))), 0)}f}'
        return text.rstrip('0').rstrip('.') if '.' in text else text
    return f'{x:.{digits}g}'


def pct(x):
    return f'{fmt(x * 100, 3)} %'
