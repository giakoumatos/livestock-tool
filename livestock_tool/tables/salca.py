"""SALCA (Switzerland): SALCAanimal V1.0 as Agroscope documents it in
Appendix 6 of Nemecek et al. (2024), "Modelling of nutrient balances,
excretion and emissions from animal production (SALCAanimal)", published on
the Agroscope SALCA page; the code is agroscope-ch/salca v1.0.1.

Groups are SALCA's: 'dairy' (loose housing), 'dairy_tied', 'other_cattle',
'fattening_pigs', 'sows', 'sheep', 'goats', 'horses', 'laying_hens',
'broilers'.
"""
from ..sources import SALCA, Factor

A6 = 'Appendix 6'


def _f(value, unit, where, note=''):
    return Factor(value, unit, SALCA, f'{A6}, {where}', note)


CATTLE = ('dairy', 'dairy_tied', 'other_cattle')
PIGS = ('fattening_pigs', 'sows')

# Tab. 1: Ym, % of GE (cattle by digestibility and raw fibre, from IPCC 2019
# Table 10.12; horses, pigs and poultry from FOEN 2019).
YM = {'horses': 2.45, 'sheep': 6.70, 'goats': 5.50, 'fattening_pigs': 0.60, 'sows': 0.60,
      'laying_hens': 0.16, 'broilers': 0.16}


def ym(group, de_pct, ndf_pct=None):
    """Tab. 1 writes "raw fibre content < 35 %" for dairy cows at DE >= 70 %;
    the row is IPCC 2019 Table 10.12's, where the 35 % is NDF, so NDF is
    asked for."""
    if group in ('dairy', 'dairy_tied'):
        if de_pct >= 70:
            if ndf_pct is None:
                raise ValueError('SALCA Ym of dairy cows at DE >= 70 % needs the NDF (ndf_pct; Tab. '
                                 '1 "raw fibre", the NDF of IPCC 2019 Table 10.12)')
            value = 5.7 if ndf_pct < 35 else 6.0
        else:
            value = 6.3 if de_pct >= 62 else 6.5
    elif group == 'other_cattle':
        value = 3.0 if de_pct >= 75 else 4.0 if de_pct >= 72 else 6.3 if de_pct >= 62 else 7.0
    else:
        value = YM[group]
    return _f(value, '% of GE', 'Tab. 1')


# Tab. 2: B0 (m3 CH4/kg VS) and UE (MJ/MJ GE).
B0_UE = {'dairy': (0.24, 0.04), 'dairy_tied': (0.24, 0.04), 'other_cattle': (0.18, 0.04),
         'horses': (0.30, 0.04), 'sheep': (0.19, 0.04), 'goats': (0.18, 0.04),
         'sows': (0.45, 0.02), 'fattening_pigs': (0.45, 0.04), 'laying_hens': (0.39, 0.02),
         'broilers': (0.36, 0.02)}
# Tab. 3: MCF for cool and moist climates, fraction.
MCF = {'pasture_drylot': 0.01, 'solid_storage': 0.02, 'pit_storage': 0.21,
       'anaerobic_digester': 0.026, 'deep_bedding': 0.21, 'composting': 0.005,
       'poultry_manure': 0.015}
# Tab. 4: N in animal products, kg N per kg. Tab. 4 prints the unit of milk
# as "m3", a misprint: 5.72E-03 kg N is the N of 1 kg of cow milk (about
# 3.3 % protein / 6.38), and the SALCA code takes the products in kg.
PRODUCT_N = {'cow_milk_kg': 5.72e-03, 'sheep_milk_kg': 3.13e-03, 'goat_milk_kg': 5.76e-03,
             'horse_milk_kg': 2.90e-03, 'sheep_wool_kg': 2.20e-02, 'eggs_kg': 1.80e-02}
# Tab. 5: N in animal bodies, g N per kg live weight (Richner et al. 2017).
BODY_N_G_PER_KG = {'dairy': 25.0, 'dairy_tied': 25.0, 'other_cattle': 26.0, 'horses': 24.3,
                   'sheep': 22.0, 'goats': 21.0, 'sows': 26.0, 'fattening_pigs': 25.0,
                   'laying_hens': 29.0, 'broilers': 29.0}
# Tab. 6: correction factor for the organic substance in liquid manure.
CORR_OS = {'cattle': 0.42, 'pigs': 0.32}
# Eq. 8: share of N excreted in urine for cattle = -4.7 + 20.7 x N % of diet DM,
# bounded to 30-70 %.
URINE_SLOPE, URINE_INTERCEPT = 20.7, -4.7
# Eq. 10: TAN of cattle excreta = urine share + 0.2 x dung share.
DUNG_TAN = 0.2
# Straw (section 5): 0.004 kg N per kg straw (EEA 2013, 3.B, Tab. 3.5).
STRAW_N = _f(0.004, 'kg N/kg straw', 'section 5')

# Tab. 7 (EEA 2019) and Tab. 8 (Agrammon Group 2022): NH3-N per kg TAN by
# group and manure type: TAN share (None for cattle: Eq. 10), housing, yard,
# storage, spreading, grazing (None for cattle: Tab. 10).
NH3 = {
    'EEA': {
        ('dairy', 'liquid'): (None, 0.24, 0.30, 0.25, 0.55, None),
        ('dairy', 'solid'): (None, 0.08, 0.30, 0.32, 0.68, None),
        ('dairy_tied', 'liquid'): (None, 0.09, 0.30, 0.25, 0.55, None),
        ('dairy_tied', 'solid'): (None, 0.09, 0.30, 0.32, 0.68, None),
        ('other_cattle', 'liquid'): (None, 0.24, 0.53, 0.25, 0.55, None),
        ('other_cattle', 'solid'): (None, 0.08, 0.53, 0.32, 0.68, None),
        ('fattening_pigs', 'liquid'): (0.70, 0.27, 0.53, 0.11, 0.40, 0.31),
        ('fattening_pigs', 'solid'): (0.70, 0.23, 0.53, 0.29, 0.45, 0.31),
        ('sows', 'liquid'): (0.70, 0.35, 0.53, 0.11, 0.29, 0.31),
        ('sows', 'solid'): (0.70, 0.24, 0.53, 0.29, 0.45, 0.31),
        ('sheep', 'solid'): (0.50, 0.22, 0.75, 0.32, 0.90, 0.09),
        ('goats', 'solid'): (0.50, 0.22, 0.75, 0.28, 0.90, 0.09),
        ('horses', 'solid'): (0.60, 0.22, 0.35, 0.35, 0.90, 0.35),
        ('laying_hens', 'liquid'): (0.70, 0.41, 0.70, 0.14, 0.69, 0.10),
        ('laying_hens', 'solid'): (0.70, 0.20, 0.70, 0.08, 0.45, 0.10),
        ('broilers', 'solid'): (0.70, 0.21, 0.70, 0.30, 0.38, 0.10),
    },
    'Agrammon': {
        ('dairy', 'liquid'): (None, 0.18, 0.70, 0.25, 0.50, None),
        ('dairy', 'solid'): (None, 0.18, 0.70, 0.30, 0.80, None),
        ('dairy_tied', 'liquid'): (None, 0.07, 0.70, 0.25, 0.50, None),
        ('dairy_tied', 'solid'): (None, 0.07, 0.70, 0.30, 0.80, None),
        ('other_cattle', 'liquid'): (None, 0.07, 0.70, 0.25, 0.50, None),
        ('other_cattle', 'solid'): (None, 0.07, 0.70, 0.30, 0.80, None),
        ('fattening_pigs', 'liquid'): (0.70, 0.24, 0.49, 0.20, 0.35, 0.20),
        ('fattening_pigs', 'solid'): (0.70, 0.24, 0.49, 0.50, 0.60, 0.20),
        ('sows', 'liquid'): (0.70, 0.24, 0.49, 0.20, 0.35, 0.20),
        ('sows', 'solid'): (0.70, 0.24, 0.49, 0.50, 0.60, 0.20),
        ('sheep', 'solid'): (0.40, 0.28, 0.75, 0.30, 0.70, 0.13),
        ('goats', 'solid'): (0.40, 0.28, 0.75, 0.30, 0.70, 0.13),
        ('horses', 'solid'): (0.40, 0.28, 0.35, 0.30, 0.70, 0.13),
        ('laying_hens', 'liquid'): (0.60, 0.25, 0.70, 0.25, 0.40, 0.10),
        ('laying_hens', 'solid'): (0.60, 0.50, 0.70, 0.25, 0.40, 0.10),
        ('broilers', 'solid'): (0.60, 0.20, 0.70, 0.25, 0.40, 0.10),
    },
}
NH3_FIELDS = ('tan', 'housing', 'yard', 'storage', 'spreading', 'grazing')
NH3_WHERE = {'EEA': 'Tab. 7 (EEA 2019)', 'Agrammon': 'Tab. 8 (Agrammon Group 2022)'}
# Section 6.1: with Agrammon, the housing emission rate on grazing days is
# 110 % below 5 h/day on pasture, 140 % for 5 to 12 h, 200 % for 12 to under
# 22 h and 250 % for 22-23 h; full grazing (animals not returning) sets housing
# emissions to 0. Those days have no excreta in the housing already (Eq. 7),
# so at 24 h the housing rate of the other days is left as it is (factor 1).


def agrammon_housing_factor(hours):
    if hours >= 24:
        return 1.0
    if hours < 5:
        return 1.10
    if hours <= 12:
        return 1.40
    return 2.00 if hours < 22 else 2.50

# Tab. 9: N2O-N, storage per kg TAN entering the store (without crust, with
# natural crust, pit storage) and grazing per kg N excreted.
N2O = {
    ('cattle', 'liquid'): (0.00, 0.01, 0.004, 0.01),
    ('cattle', 'solid'): (0.02, 0.0, 0.0, 0.0025),
    ('pigs', 'liquid'): (0.00, 0.01, 0.004, 0.006),
    ('pigs', 'solid'): (0.01, 0.0, 0.0, 0.006),
    ('small_ruminants_horses', 'solid'): (0.02, 0.0, 0.0, 0.006),
    ('poultry', 'liquid'): (0.002, 0.0, 0.0, 0.006),
    ('poultry', 'solid'): (0.002, 0.0, 0.0, 0.006),
}


def n2o_family(group):
    if group in CATTLE:
        return 'cattle'
    if group in PIGS:
        return 'pigs'
    return 'poultry' if group in ('laying_hens', 'broilers') else 'small_ruminants_horses'


# Section 6.2-6.4: N2 and NOx from storage (NOx as SALCA writes it: EEA 2019
# Tab. 3.10 x 14/30), mineralisation and immobilisation.
N2_STORAGE = {'liquid': 0.003, 'solid': 0.3}
NOX_STORAGE = {'liquid': 0.0001 * 14 / 30, 'solid': 0.01 * 14 / 30}
MINERALISATION_LIQUID = 0.1
IMMOBILISATION = {'EEA': 0.0067, 'Agrammon': 0.4}   # EEA: per kg straw; Agrammon: per kg TAN
# Section 6.6, Tab. 10 (Nemecek & Ledgard 2016): grazing cattle, by season
# (spring, summer, autumn, winter) and mean.
SEASONS = ('spring', 'summer', 'autumn', 'winter')
PASTURE = {'no3_urine': (0.155, 0.164, 0.273, 0.227, 0.205),
           'no3_dung': (0.028, 0.029, 0.049, 0.041, 0.037),
           'nh3_urine': (0.080, 0.150, 0.090, 0.070, 0.098)}
NOX_GRAZING = _f(0.012, 'kg NOx-N/kg N', 'section 6.6', 'EEA 2019, 0.026 x 14/30')
NO3_PIGS_OF_TAN = _f(0.5, 'kg NO3-N/kg TAN', 'section 6.6', 'Stauffer et al. 1999')
# Section 6.7: induced N2O.
EF4 = _f(0.01, 'kg N2O-N/kg (NH3-N + NOx-N)', 'section 6.7', 'IPCC 2019, Table 11.3')
EF5 = _f(0.011, 'kg N2O-N/kg NO3-N', 'section 6.7', 'IPCC 2019, Table 11.3')
