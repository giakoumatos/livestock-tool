"""Fills the inputs the data collection workbook leaves empty, from the
cited tables in `tables/` (the crop tool's defaultGeneration.py pattern).

Every default that is used is recorded with its Factor, so the flow
comments can say which value was a default and from which table it comes.
"""
from .sources import Factor


class DefaultValuesWrapper:
    def __init__(self, inputs, generators):
        self.inputs = inputs
        self._generators = generators
        self.used_defaults = {}

    def __getitem__(self, name):
        value = self.inputs.get(name)
        if value is not None:
            return value
        generator = self._generators.get(name)
        if generator is None:
            if name in self.inputs:
                return None         # an optional input left empty
            raise KeyError(f'no value and no default for "{name}"')
        factor = generator.generate(name, self)
        if isinstance(factor, Factor):
            self.used_defaults[name] = factor
            return factor.value
        return factor

    def __contains__(self, name):
        return self.inputs.get(name) is not None or name in self._generators

    def get(self, name, default=None):
        return self[name] if name in self else default


class FactorDefault:
    """A single cited value."""
    def __init__(self, factor):
        self._factor = factor

    def generate(self, name, values):
        return self._factor


class FunctionDefault:
    """A cited value chosen from other inputs, e.g. UE by animal category."""
    def __init__(self, function, *fields):
        self._function = function
        self._fields = fields

    def generate(self, name, values):
        factor = self._function(*(values.get(f) for f in self._fields))
        if factor is None:
            raise KeyError(f'no default for "{name}" in the sources; give it in the data '
                           'collection')
        return factor
