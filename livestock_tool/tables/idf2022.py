"""IDF Bulletin 520/2022, The IDF global Carbon Footprint standard for the
dairy sector: milk/meat allocation of dairy farms and the FPCM unit.
WFLDB v3.5 (section 2.6.3) allocates dairy farms by the IDF method; it cites
the 2015 edition, which the 2022 edition replaces."""
from ..sources import IDF2022, Factor


def _f(value, unit, where, note=''):
    return Factor(value, unit, IDF2022, where, note)


# Equation 1: FPCM (kg) = milk (kg) x [0.1226 x fat% + 0.0776 x true protein% + 0.2534].
FPCM_WHERE = 'section 4.3, Equation 1, p. 21'
FPCM_COEFFICIENTS = (0.1226, 0.0776, 0.2534)

# Section 5.4.2, Equations 2 to 4 (p. 43-44): AFmilk = NEL x Mmilk /
# (NEL x Mmilk + sum NEGi x Mclass_i), with the net energy requirements of
# Nemecek and Thoma as given on p. 44.
ALLOCATION_WHERE = 'section 5.4.2, Equation 4, p. 44'
NEL_PER_KG_FPCM = _f(3.1, 'MJ/kg FPCM', ALLOCATION_WHERE)
NEG_PER_KG_LW = {
    'calf_at_birth': _f(27.5, 'MJ/kg LW', ALLOCATION_WHERE, 'calves sold at birth'),
    'mature': _f(15.0, 'MJ/kg LW', ALLOCATION_WHERE, 'mature animals'),
    'heifer_or_fattened_calf': _f(11.0, 'MJ/kg LW', ALLOCATION_WHERE,
                                  'bred heifers and fattened calves'),
}


def fpcm(milk_kg, fat_pct, protein_pct):
    a, b, c = FPCM_COEFFICIENTS
    return milk_kg * (a * fat_pct + b * protein_pct + c)
