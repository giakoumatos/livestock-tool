"""EMEP/EEA air pollutant emission inventory guidebook 2023 (EU route).

Chapter 3.B Manure management ("Version Guidebook 2023"); printed page =
PDF page. Values transcribed from the chapter, row by row. Used for EU
countries (models/routing.py), and outside the EU for two items IPCC 2019
does not give: the particulate factors (WFLDB v3.5 section 3.9.12, Tab. 29
= Table 3-5 below) and the NOx part of the N volatilised from manure
management, the storage NO factor (Table 3-10) on the TAN share of Table
3-9 (docs/method_decisions.md, decision 2). N2O from storage is IPCC 2019's,
not Table 3-8.
"""
from ..sources import EMEP2023, Factor


def _f(value, unit, where, note=''):
    return Factor(value, unit, EMEP2023, where, note)


# Table 3-9 (p. 29-30): default Tier 2 NH3-N EFs, as a proportion of TAN.
# (category, manure type) -> housing days, Nex (kg N per AAP and year),
# TAN share, EF housing, EF yard, EF storage, EF application, EF grazing.
_T39 = '3.B, Table 3-9, p. 29-30'
TIER2_NH3 = {
    ('dairy_cattle', 'slurry'): (180, 105, 0.6, 0.24, 0.30, 0.25, 0.55, 0.14),
    ('dairy_cattle', 'solid'): (180, 105, 0.6, 0.08, 0.30, 0.32, 0.68, 0.14),
    ('other_cattle', 'slurry'): (180, 41, 0.6, 0.24, 0.53, 0.25, 0.55, 0.14),
    ('other_cattle', 'solid'): (180, 41, 0.6, 0.08, 0.53, 0.32, 0.68, 0.14),
    ('sheep', 'solid'): (30, 15.5, 0.5, 0.22, 0.75, 0.32, 0.90, 0.09),
    ('swine_finishing', 'slurry'): (365, 12.1, 0.7, 0.27, 0.53, 0.11, 0.40, None),
    ('swine_finishing', 'solid'): (365, 12.1, 0.7, 0.23, 0.53, 0.29, 0.45, None),
    ('swine_sows', 'slurry'): (365, 34.5, 0.7, 0.35, None, 0.11, 0.29, None),
    ('swine_sows', 'solid'): (365, 34.5, 0.7, 0.24, None, 0.29, 0.45, None),
    ('swine_sows', 'outdoor'): (0, 34.5, 0.7, None, None, None, None, 0.31),
    ('buffalo', 'solid'): (140, 82.0, 0.5, 0.20, None, 0.17, 0.55, 0.14),
    ('goats', 'solid'): (30, 15.5, 0.5, 0.22, 0.75, 0.28, 0.90, 0.09),
    ('horses', 'solid'): (180, 47.5, 0.6, 0.22, None, 0.35, 0.90, 0.35),
    ('mules_asses', 'solid'): (180, 47.5, 0.6, 0.22, None, 0.35, 0.90, 0.35),
    ('laying_hens', 'solid'): (365, 0.77, 0.7, 0.20, None, 0.08, 0.45, None),
    ('laying_hens', 'slurry'): (365, 0.77, 0.7, 0.41, None, 0.14, 0.69, None),
    ('broilers', 'solid'): (365, 0.36, 0.7, 0.21, None, 0.30, 0.38, None),
    ('turkeys', 'solid'): (365, 1.64, 0.7, 0.35, None, 0.24, 0.54, None),
    ('ducks', 'solid'): (365, 1.26, 0.7, 0.24, None, 0.24, 0.54, None),
    ('geese', 'solid'): (365, 0.55, 0.7, 0.57, None, 0.16, 0.45, None),
}
_T39_FIELDS = ('housing_days', 'nex', 'tan_share', 'ef_housing', 'ef_yard', 'ef_storage',
               'ef_application', 'ef_grazing')
_T39_UNITS = ('d/a', 'kg N/(AAP*a)', 'kg TAN/kg N', *(['kg NH3-N/kg TAN'] * 5))


def tier2_nh3(category, manure_type, field):
    row = TIER2_NH3.get((category, manure_type))
    if row is None:
        raise KeyError(f'EMEP/EEA 2023 Table 3-9 has no row for {category}, {manure_type}')
    i = _T39_FIELDS.index(field)
    if row[i] is None:
        raise KeyError(f'EMEP/EEA 2023 Table 3-9 gives no {field} for {category}, {manure_type}')
    return _f(row[i], _T39_UNITS[i], _T39)


# Step 3 (p. 22): share of N excreted on yards, given only for these.
YARD_SHARE = {
    'dairy_cattle': _f(0.25, 'kg N/kg N', '3.B, section 3.4.1, Step 3, p. 22'),
    'other_cattle': _f(0.10, 'kg N/kg N', '3.B, section 3.4.1, Step 3, p. 22'),
    'sheep': _f(0.02, 'kg N/kg N', '3.B, section 3.4.1, Step 3, p. 22'),
}

# Table 3-10 (p. 31): NO from storage, kg N per kg TAN (the table also gives N2, not used).
_T310 = '3.B, Table 3-10, p. 31'
STORAGE_NO = {'slurry': _f(0.0001, 'kg NO-N/kg TAN', _T310),
              'solid': _f(0.0100, 'kg NO-N/kg TAN', _T310)}

# Table 3-7 (p. 23): straw for the stated housing period (kg per AAP and year),
# N added in straw at 4 g N per kg straw (table footnote a).
_T37 = '3.B, Table 3-7, p. 23'
STRAW = {
    'dairy_cattle': (180, 1500), 'other_cattle': (180, 500), 'swine_finishing': (365, 200),
    'swine_sows': (365, 600), 'sheep': (30, 20), 'goats': (30, 20), 'horses': (180, 500),
    'mules_asses': (180, 500), 'buffalo': (225, 1500),
}
STRAW_N_CONTENT = _f(0.004, 'kg N/kg straw', _T37 + ', footnote (a)')
# Step 7 (p. 23): TAN immobilised in straw.
F_IMM = _f(0.0067, 'kg N/kg straw', '3.B, section 3.4.1, Step 7, p. 23')
# Step 9 (p. 24): organic N mineralised in slurry storage.
F_MIN = _f(0.1, 'kg N/kg N', '3.B, section 3.4.1, Step 9, p. 24')

# 3.D, Table 3-1 (p. 14): NO from N applied in manure and excreta, as NO2.
SOIL_NO = Factor(0.04, 'kg NO2/kg N', EMEP2023, '3.D, Table 3-1, p. 14')

# Table 3-5 (p. 18-19): Tier 1 particulate matter from housing, kg per AAP and year.
_T35 = '3.B, Table 3-5, p. 18-19'
PM_TIER1 = {  # TSP, PM10, PM2.5
    'dairy_cattle': (1.38, 0.63, 0.41), 'other_cattle': (0.59, 0.27, 0.18),
    'calves': (0.34, 0.16, 0.10), 'sheep': (0.14, 0.06, 0.02),
    'swine_finishing': (1.05, 0.14, 0.006), 'swine_weaners': (0.27, 0.05, 0.002),
    'swine_sows': (0.62, 0.17, 0.01), 'buffalo': (1.45, 0.67, 0.44), 'goats': (0.14, 0.06, 0.02),
    'horses': (0.48, 0.22, 0.14), 'mules_asses': (0.34, 0.16, 0.10),
    'laying_hens': (0.19, 0.04, 0.003), 'broilers': (0.04, 0.02, 0.002),
    'turkeys': (0.11, 0.11, 0.02), 'ducks': (0.14, 0.14, 0.02), 'geese': (0.24, 0.24, 0.03),
}


def pm_tier1(category, size):
    row = PM_TIER1.get(category)
    if row is None:
        raise KeyError(f'EMEP/EEA 2023 Table 3-5 has no row for {category}')
    return _f(row[('tsp', 'pm10', 'pm25').index(size)], 'kg/(AAP*a)', _T35)


# Table 3-12 (p. 32): Tier 2 NMVOC for livestock other than cattle, kg NMVOC
# per kg VS excreted: silage feeding, building, grazing. Goats, buffalo,
# horses, mules: "Based on data for sheep" (footnote c).
_T312 = '3.B, Table 3-12, p. 32'
NMVOC_TIER2_VS = {
    'sheep': (0.010760, 0.001614, 0.00002349), 'goats': (0.010760, 0.001614, 0.00002349),
    'buffalo': (0.010760, 0.001614, 0.00002349), 'horses': (0.010760, 0.001614, 0.00002349),
    'mules_asses': (0.010760, 0.001614, 0.00002349),
    'swine_finishing': (None, 0.001703, None), 'swine_sows': (None, 0.007042, None),
    'laying_hens': (None, 0.005684, None), 'broilers': (None, 0.009147, None),
    'turkeys': (None, 0.005684, None), 'ducks': (None, 0.005684, None),
    'geese': (None, 0.005684, None),
}
# Table 3-11 (p. 31): Tier 2 NMVOC for cattle, kg NMVOC per MJ gross feed intake.
_T311 = '3.B, Table 3-11, p. 31'
NMVOC_TIER2_MJ = {
    'dairy_cattle': (0.0002002, 0.0000353, 0.0000069),
    'other_cattle': (0.0002002, 0.0000353, 0.0000069),
}
# Eq. (49)-(50) and (55)-(56) (p. 27-28): silage defaults.
SILAGE_STORE_SHARE = _f(0.25, '-', '3.B, section 3.4.2, p. 27',
                        'tentative default for European conditions')


def nmvoc_tier2(category, source):
    i = ('silage_feeding', 'building', 'grazing').index(source)
    if category in NMVOC_TIER2_MJ:
        return _f(NMVOC_TIER2_MJ[category][i], 'kg NMVOC/MJ GE', _T311)
    row = NMVOC_TIER2_VS.get(category)
    if row is None or row[i] is None:
        raise KeyError(f'EMEP/EEA 2023 Tables 3-11/3-12 give no {source} NMVOC EF for {category}')
    return _f(row[i], 'kg NMVOC/kg VS', _T312)
