"""IPCC 2006 Guidelines as refined by the IPCC 2019 Refinement, Volume 4
(greenhouse gases and nitrogen flows, every route but Switzerland).

Chapter 10 (livestock and manure management) and Chapter 11 (N2O from
managed soils); printed page 10.n / 11.n. Every value here was read on the
page image of the official PDF, not only in extracted text. A table the
Refinement leaves unchanged still applies from 2006, as the Refinement
intends; none of the values below needed that.
"""
from ..sources import IPCC2019, Factor


def _f(value, unit, where, note=''):
    return Factor(value, unit, IPCC2019, where, note)


# --- Gross energy, Tier 2 (Ch. 10, section 10.2) -------------------------
# Table 10.4 (p. 10.24): Cfi for net energy for maintenance, MJ/(day*kg^0.75).
CFI = {
    'cattle': _f(0.322, 'MJ/(d*kg^0.75)', 'Vol. 4, Ch. 10, Table 10.4, p. 10.24',
                 'non-lactating cows, steers, heifers and calves'),
    'cattle_lactating': _f(0.386, 'MJ/(d*kg^0.75)', 'Vol. 4, Ch. 10, Table 10.4, p. 10.24'),
    'cattle_bulls': _f(0.370, 'MJ/(d*kg^0.75)', 'Vol. 4, Ch. 10, Table 10.4, p. 10.24'),
    'sheep_lamb': _f(0.236, 'MJ/(d*kg^0.75)', 'Vol. 4, Ch. 10, Table 10.4, p. 10.24',
                     'lamb to 1 year; can be increased by 15% for intact males'),
    'sheep': _f(0.217, 'MJ/(d*kg^0.75)', 'Vol. 4, Ch. 10, Table 10.4, p. 10.24',
                'older than 1 year; can be increased by 15% for intact males'),
    'goats': _f(0.315, 'MJ/(d*kg^0.75)', 'Vol. 4, Ch. 10, Table 10.4, p. 10.24'),
}
# Table 10.5 (p. 10.25): activity coefficient Ca by feeding situation.
# Cattle/buffalo: dimensionless (Eq. 10.4, x NEm); sheep/goats: MJ/(d*kg)
# (Eq. 10.5, x live weight).
CA_CATTLE = {
    'stall': _f(0.0, '-', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'pasture': _f(0.17, '-', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'grazing_large_areas': _f(0.36, '-', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
}
CA_SHEEP_GOATS = {
    'housed_ewes': _f(0.0096, 'MJ/(d*kg)', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'grazing_flat_pasture': _f(0.0107, 'MJ/(d*kg)', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'grazing_hilly_pasture': _f(0.024, 'MJ/(d*kg)', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'housed_fattening_lambs': _f(0.0067, 'MJ/(d*kg)', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'lowland_goats': _f(0.019, 'MJ/(d*kg)', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
    'hill_mountain_goats': _f(0.024, 'MJ/(d*kg)', 'Vol. 4, Ch. 10, Table 10.5, p. 10.25'),
}
# Table 10.6 (p. 10.26): constants a, b (MJ/kg) of Eq. 10.7, NEg of sheep and goats.
NEG_A_B = {
    'sheep_intact_male': (2.5, 0.35), 'sheep_castrate': (4.4, 0.32),
    'sheep_female': (2.1, 0.45), 'goats': (5.0, 0.33),
}
NEG_A_B_WHERE = 'Vol. 4, Ch. 10, Table 10.6, p. 10.26'
# Eq. 10.10 text (p. 10.27): EVmilk, MJ per kg milk (7 % / 3.8 % fat).
EV_MILK = {
    'sheep': _f(4.6, 'MJ/kg milk', 'Vol. 4, Ch. 10, Eq. 10.10, p. 10.27', 'milk fat 7 %'),
    'goats': _f(3.0, 'MJ/kg milk', 'Vol. 4, Ch. 10, Eq. 10.10, p. 10.27', 'milk fat 3.8 %'),
}
# Eq. 10.12 text (p. 10.28): wool and fibre.
EV_WOOL_SHEEP = _f(24.0, 'MJ/kg wool', 'Vol. 4, Ch. 10, Eq. 10.12, p. 10.28')
NE_FIBRE_PER_DAY = {
    'sheep_fibre': _f(0.25, 'MJ/d', 'Vol. 4, Ch. 10, Eq. 10.12, p. 10.28',
                      'fibre-producing sheep (AFRC 1993; 1995)'),
    'goats_angora': _f(0.25, 'MJ/d', 'Vol. 4, Ch. 10, Eq. 10.12, p. 10.28', 'angora breeds'),
    'goats_cashmere': _f(0.08, 'MJ/d', 'Vol. 4, Ch. 10, Eq. 10.12, p. 10.28', 'cashmere breeds'),
}
# Table 10.7 (p. 10.29): Cpregnancy.
C_PREGNANCY = {
    'cattle': _f(0.10, '-', 'Vol. 4, Ch. 10, Table 10.7, p. 10.29'),
    'single': _f(0.077, '-', 'Vol. 4, Ch. 10, Table 10.7, p. 10.29', 'sheep/goats, single birth'),
    'double': _f(0.126, '-', 'Vol. 4, Ch. 10, Table 10.7, p. 10.29', 'sheep/goats, twins'),
    'triple': _f(0.150, '-', 'Vol. 4, Ch. 10, Table 10.7, p. 10.29', 'sheep/goats, triplets or more'),
}
# Eq. 10.16 text (p. 10.30) and Eq. 10.24 (p. 10.65): GE per kg feed DM.
GE_PER_KG_DM = _f(18.45, 'MJ/kg DM', 'Vol. 4, Ch. 10, Eq. 10.16, p. 10.30')
EQ_REM = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.14, p. 10.29'
EQ_REG = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.15, p. 10.30'
EQ_GE = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.16, p. 10.30'

# --- Enteric methane (section 10.3) --------------------------------------
EQ_ENTERIC = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.21, p. 10.47'
# Table 10.13 (p. 10.47): Ym, % of GE.
YM = {
    'sheep': _f(6.7, '% of GE', 'Vol. 4, Ch. 10, Table 10.13, p. 10.47', '+/- 0.9 (SD)'),
    'goats': _f(5.5, '% of GE', 'Vol. 4, Ch. 10, Table 10.13, p. 10.47', '+/- 1.0 (SD)'),
}


def ym_sheep(dmi_kg_day):
    """Text below Table 10.12 (p. 10.46): 6.7 % for 0.6-0.8 kg DM a day, 7.0 %
    below 0.6 and 6.5 % above 0.8."""
    if dmi_kg_day is None:
        return YM['sheep']
    value, note = ((7.0, 'intake below 0.6 kg DM/d') if dmi_kg_day < 0.6 else
                   (6.5, 'intake above 0.8 kg DM/d') if dmi_kg_day > 0.8 else
                   (6.7, 'intake 0.6-0.8 kg DM/d'))
    return _f(value, '% of GE', 'Vol. 4, Ch. 10, Table 10.13 and text p. 10.46', note)
# Table 10.12 (p. 10.46): Ym of cattle and buffalo, % of GE, by class
# (uncertainty +/- 20 %, fn 3). Dry dairy cows: 6.3 in high and medium
# production systems, 7.0 in low ones on > 75 % low-quality forage (fn 4).
_T1012 = 'Vol. 4, Ch. 10, Table 10.12, p. 10.46'
YM_CATTLE = {
    'dairy_high_ndf_low': _f(5.7, '% of GE', _T1012, 'dairy > 8500 kg milk/yr, DE >= 70, NDF <= 35'),
    'dairy_high_ndf_high': _f(6.0, '% of GE', _T1012, 'dairy > 8500 kg milk/yr, DE >= 70, NDF >= 35'),
    'dairy_medium': _f(6.3, '% of GE', _T1012, 'dairy 5000-8500 kg milk/yr, DE 63-70, NDF > 37'),
    'dairy_low': _f(6.5, '% of GE', _T1012, 'dairy < 5000 kg milk/yr, DE <= 62, NDF > 38'),
    'nondairy_forage': _f(7.0, '% of GE', _T1012, 'non-dairy, > 75 % forage, DE <= 62'),
    'nondairy_mixed': _f(6.3, '% of GE', _T1012, 'non-dairy, high-quality forage or mixed '
                                                 'rations (15-75 % forage), DE 62-71'),
    'feedlot_grains': _f(4.0, '% of GE', _T1012, 'feedlot, other grains, 0-15 % forage, DE >= 72'),
    'feedlot_steam_flaked_corn': _f(3.0, '% of GE', _T1012,
                                    'feedlot, steam-flaked corn, 0-10 % forage, DE >= 75'),
}


def ym_cattle_class(dairy, milk_kg_year, de_pct, ndf_pct=None, forage_share=None):
    """The row of Table 10.12 the data point to, or None when they do not
    decide it. Dairy: milk yield first, then DE and NDF; non-dairy: forage
    share and DE (feedlots must be named, they depend on the grain fed)."""
    if dairy:
        if not milk_kg_year:
            return None
        if milk_kg_year > 8500:
            if ndf_pct is None or de_pct < 70:
                return None
            return 'dairy_high_ndf_low' if ndf_pct <= 35 else 'dairy_high_ndf_high'
        return 'dairy_medium' if milk_kg_year >= 5000 else 'dairy_low'
    if forage_share is None:
        return None
    if forage_share > 0.75:
        return 'nondairy_forage' if de_pct <= 62 else 'nondairy_mixed' if de_pct <= 71 else None
    return 'nondairy_mixed' if forage_share >= 0.15 else None

# --- Manure methane (section 10.4) ---------------------------------------
EQ_MANURE_CH4 = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.23, p. 10.64'
EQ_VS = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.24, p. 10.65'
# Eq. 10.24 text (p. 10.65): urinary energy, fraction of GE.
_VS_WHERE = 'Vol. 4, Ch. 10, Eq. 10.24, p. 10.65'
UE_RUMINANT = _f(0.04, 'fraction of GE', _VS_WHERE, 'most ruminants')
UE_GRAIN_OR_SWINE = _f(0.02, 'fraction of GE', _VS_WHERE,
                       'ruminants fed 85 % or more grain, or swine')


def ue_default(category_key, grain_share=None):
    """UE by the text of Eq. 10.24; IPCC gives none for poultry or horses."""
    if category_key.startswith('swine'):
        return UE_GRAIN_OR_SWINE
    if category_key in ('goats', 'sheep', 'dairy_cattle', 'other_cattle', 'buffalo'):
        return UE_GRAIN_OR_SWINE if (grain_share or 0) >= 0.85 else UE_RUMINANT
    return None
# Table 10.16A (p. 10.67): B0, m3 CH4 per kg VS. Columns: North America,
# Western Europe, Eastern Europe, Oceania, other regions high productivity,
# other regions low productivity.
_B0_COLUMNS = ('north_america', 'western_europe', 'eastern_europe', 'oceania', 'other_high',
               'other_low')
_B0 = {
    'dairy_cattle': (0.24, 0.24, 0.24, 0.24, 0.24, 0.13),
    'other_cattle': (0.19, 0.18, 0.17, 0.17, 0.18, 0.13),
    'buffalo': (0.10, 0.10, 0.10, 0.10, 0.10, 0.10),
    'swine': (0.48, 0.45, 0.45, 0.45, 0.45, 0.29),
    'chicken_layer': (0.39, 0.39, 0.39, 0.39, 0.39, 0.24),
    'other_poultry': (0.36, 0.36, 0.36, 0.36, 0.36, 0.24),
    'sheep': (0.19, 0.19, 0.19, 0.19, 0.19, 0.13),
    'goats': (0.18, 0.18, 0.18, 0.18, 0.18, 0.13),
    'horses': (0.30, 0.30, 0.30, 0.30, 0.30, 0.26),
    'mules_asses': (0.33, 0.33, 0.33, 0.33, 0.33, 0.26),
    'camels': (0.26, 0.26, 0.26, 0.26, 0.26, 0.21),
}
B0_PRP = _f(0.19, 'm3 CH4/kg VS', 'Vol. 4, Ch. 10, Table 10.16A, p. 10.67',
            'all animals, pasture/range/paddock; to be used with the PRP MCF (Table 10.17, fn 2)')


def b0(b0_group, region):
    return _f(_B0[b0_group][_B0_COLUMNS.index(region)], 'm3 CH4/kg VS',
              'Vol. 4, Ch. 10, Table 10.16A, p. 10.67',
              f'{region.replace("_", " ")}')


# Table 10.17 (p. 10.68-10.69): MCF, %. Climate zones in column order; the
# three-value rows span the groups Cool (first four zones), Temperate
# (warm temperate) and Warm (tropical), as printed.
CLIMATE_ZONES = ('cool_temperate_moist', 'cool_temperate_dry', 'boreal_moist', 'boreal_dry',
                 'warm_temperate_moist', 'warm_temperate_dry', 'tropical_montane',
                 'tropical_wet', 'tropical_moist', 'tropical_dry')
CLIMATE_GROUP = {z: ('cool' if i < 4 else 'temperate' if i < 6 else 'warm')
                 for i, z in enumerate(CLIMATE_ZONES)}
_MCF_BY_ZONE = {
    'uncovered_anaerobic_lagoon': (60, 67, 50, 49, 73, 76, 76, 80, 80, 80),
    'liquid_slurry_1_month': (6, 8, 4, 4, 13, 15, 25, 38, 36, 42),
    'liquid_slurry_3_month': (12, 16, 8, 8, 24, 28, 43, 61, 57, 62),
    'liquid_slurry_4_month': (15, 19, 9, 9, 29, 32, 50, 67, 64, 68),
    'liquid_slurry_6_month': (21, 26, 14, 14, 37, 41, 59, 76, 73, 74),
    'liquid_slurry_12_month': (31, 42, 21, 20, 55, 64, 73, 80, 80, 80),
    'deep_bedding_over_1_month': (21, 26, 14, 14, 37, 41, 59, 76, 73, 74),
}
_MCF_BY_GROUP = {  # cool, temperate, warm
    'deep_bedding_under_1_month': (2.75, 6.50, 18.0),
    'solid_storage': (2.00, 4.00, 5.00),
    'solid_storage_covered': (2.00, 4.00, 5.00),
    'solid_storage_bulking_agent': (0.50, 1.00, 1.50),
    'solid_storage_additives': (1.00, 2.00, 2.50),
    'dry_lot': (1.00, 1.50, 2.00),
    'daily_spread': (0.10, 0.50, 1.00),
    'composting_static_pile': (1.00, 2.00, 2.50),
    'composting_intensive_windrow': (0.50, 1.00, 1.5),
    'composting_passive_windrow': (1.00, 2.00, 2.50),
    'anaerobic_digester_low_leak_open_storage': (3.55, 4.38, 4.59),
    'anaerobic_digester_high_leak_open_storage': (12.14, 12.97, 13.17),
}
_MCF_ALL = {
    'composting_in_vessel': 0.50,
    'pasture': 0.47,
    'poultry_manure': 1.50,
    'aerobic_treatment': 0.00,
    'burned_for_fuel': 10.00,
    'anaerobic_digester_low_leak_gastight_best': 1.00,
    'anaerobic_digester_low_leak_low_quality_gastight': 1.41,
    'anaerobic_digester_high_leak_high_quality_gastight': 9.59,
    'anaerobic_digester_high_leak_low_quality_gastight': 10.00,
}
_MCF_WHERE = 'IPCC 2019, Vol. 4, Ch. 10, Table 10.17, p. 10.68-10.69'


def mcf(system, zone):
    if zone not in CLIMATE_ZONES and system not in _MCF_ALL:
        raise ValueError(f'IPCC 2019 Table 10.17 has no MCF for the climate zone "{zone}"')
    if system in _MCF_ALL:
        value, note = _MCF_ALL[system], 'all climate zones'
    elif system in _MCF_BY_ZONE:
        value, note = _MCF_BY_ZONE[system][CLIMATE_ZONES.index(zone)], zone.replace('_', ' ')
    elif system in _MCF_BY_GROUP:
        group = CLIMATE_GROUP[zone]
        value, note = _MCF_BY_GROUP[system][('cool', 'temperate', 'warm').index(group)], \
            f'{group} climate ({zone.replace("_", " ")})'
    else:
        raise KeyError(f'IPCC 2019 Table 10.17 has no MCF for "{system}"')
    if system == 'pasture':
        note += '; used with B0 0.19 (fn 2)'
    return _f(value, '%', _MCF_WHERE.replace('IPCC 2019, ', ''), note)


# --- N excretion (section 10.5) ------------------------------------------
EQ_NEX = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.31, p. 10.81'
EQ_N_INTAKE = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.32, p. 10.82'
# Table 10.20 (p. 10.85): fraction of N intake retained; non-dairy sheep and
# goats (dairy sheep and goats: country-specific values recommended).
N_RETENTION_FRAC = {
    'sheep': 0.10, 'goats': 0.10, 'camels': 0.07, 'swine': 0.30, 'horses': 0.07,
    'poultry': 0.30,
}


def n_retention_frac(group):
    note = ('non-dairy sheep and goats; uncertainty +/-50 %' if group in ('sheep', 'goats')
            else 'uncertainty +/-50 %')
    return _f(N_RETENTION_FRAC[group], 'kg N/kg N intake', 'Vol. 4, Ch. 10, Table 10.20, p. 10.85',
              note)


# --- Manure N2O (section 10.5) -------------------------------------------
# Table 10.21 (p. 10.91-10.92): EF3, kg N2O-N per kg N excreted.
_EF3 = {
    'daily_spread': 0.0, 'solid_storage': 0.010, 'solid_storage_covered': 0.01,
    'solid_storage_bulking_agent': 0.005, 'solid_storage_additives': 0.005, 'dry_lot': 0.02,
    'liquid_slurry_crust': 0.005, 'liquid_slurry_no_crust': 0.0, 'liquid_slurry_cover': 0.005,
    'uncovered_anaerobic_lagoon': 0.0, 'pit_storage': 0.002, 'anaerobic_digester': 0.0006,
    'deep_bedding_no_mixing': 0.01, 'deep_bedding_active_mixing': 0.07,
    'composting_in_vessel': 0.006, 'composting_static_pile': 0.010,
    'composting_intensive_windrow': 0.005, 'composting_passive_windrow': 0.005,
    'poultry_with_litter': 0.001, 'poultry_without_litter': 0.001,
    'aerobic_natural': 0.01, 'aerobic_forced': 0.005,
}


EF3_WHERE = 'IPCC 2019, Vol. 4, Ch. 10, Table 10.21, p. 10.91-10.93'


def ef3(system):
    if system not in _EF3:
        raise KeyError(f'IPCC 2019 Table 10.21 has no EF3 for "{system}"')
    return _f(_EF3[system], 'kg N2O-N/kg N', 'Vol. 4, Ch. 10, Table 10.21, p. 10.91-10.93',
              'uncertainty a factor of 2 (fn 24)')


# Table 10.22 (p. 10.97-10.98): FracGas_MS (NH3 + NOx, fraction of total N
# excreted) and FracLeach_MS, by animal column. None = NA / no data.
_FRAC_COLUMNS = ('swine', 'dairy_cow', 'poultry', 'other_cattle', 'other_animals')
_FRAC_GAS_MS = {
    'uncovered_anaerobic_lagoon': (0.40, 0.35, 0.40, 0.35, 0.35),
    'liquid_slurry_crust': (0.30, 0.30, None, 0.30, 0.09),
    'liquid_slurry_no_crust': (0.48, 0.48, 0.40, 0.48, 0.15),
    'liquid_slurry_cover': (0.10, 0.10, 0.08, 0.10, 0.03),
    'pit_storage': (0.25, 0.28, 0.28, 0.25, 0.25),
    'daily_spread': (0.07, 0.07, 0.07, 0.07, 0.07),
    'solid_storage_covered': (0.22, 0.14, 0.20, 0.22, 0.05),
    'solid_storage_bulking_agent': (0.58, 0.38, 0.54, 0.58, 0.15),
    'solid_storage_additives': (0.17, 0.11, 0.16, 0.17, 0.04),
    'solid_storage': (0.45, 0.30, 0.40, 0.45, 0.12),
    'dry_lot': (0.45, 0.30, None, 0.30, 0.30),
    'deep_bedding': (0.40, 0.25, None, 0.25, None),
    'composting_in_vessel': (0.60, 0.45, 0.60, 0.60, 0.18),
    'composting_static_pile': (0.65, 0.50, 0.65, 0.65, 0.20),
    'composting_intensive_windrow': (0.65, 0.50, 0.65, 0.65, 0.20),
    'composting_passive_windrow': (0.60, 0.45, 0.60, 0.60, 0.18),
    'poultry_with_litter': (None, None, 0.40, None, None),
    'poultry_without_litter': (None, None, 0.48, None, None),
    'aerobic_forced': (0.85, 0.85, None, 0.85, 0.27),
}
_FRAC_LEACH_MS = {
    'uncovered_anaerobic_lagoon': (0, 0, 0, 0, 0), 'liquid_slurry_crust': (0, 0, 0, 0, 0),
    'liquid_slurry_no_crust': (0, 0, 0, 0, 0), 'liquid_slurry_cover': (0, 0, 0, 0, 0),
    'pit_storage': (0, 0, 0, 0, 0), 'daily_spread': (0, 0, 0, 0, 0),
    'solid_storage_covered': (0, 0, 0, 0, 0),
    'solid_storage_bulking_agent': (0.02, 0.02, 0.02, 0.02, 0.02),
    'solid_storage_additives': (0.02, 0.02, 0.02, 0.02, 0.02),
    'solid_storage': (0.02, 0.02, 0.02, 0.02, 0.02),
    'dry_lot': (0.035, 0.035, None, 0.035, 0.035),
    'deep_bedding': (0.035, 0.035, None, 0.035, None),
    'composting_in_vessel': (0, 0, 0, 0, 0),
    'composting_static_pile': (0.06, 0.06, 0.06, 0.06, 0.06),
    'composting_intensive_windrow': (0.06, 0.06, 0.06, 0.06, 0.06),
    'composting_passive_windrow': (0.04, 0.04, 0.04, 0.04, 0.04),
    'poultry_with_litter': (None, None, 0, None, None),
    'poultry_without_litter': (None, None, 0, None, None),
    'aerobic_forced': (0, 0, 0, 0, 0),
    'anaerobic_digester': (0, 0, 0, 0, 0),
}
_FRAC_WHERE = 'Vol. 4, Ch. 10, Table 10.22, p. 10.97-10.98'


def _frac(table, label, system, column):
    row = table.get(system)
    value = None if row is None else row[_FRAC_COLUMNS.index(column)]
    if value is None:
        raise KeyError(f'IPCC 2019 Table 10.22 gives no {label} for "{system}", '
                       f'{column.replace("_", " ")}')
    return value


def frac_gas_ms(system, column):
    return _f(_frac(_FRAC_GAS_MS, 'FracGas_MS', system, column), 'kg N/kg N excreted',
              _FRAC_WHERE, f'{column.replace("_", " ")} column; NH3 + NOx')


def frac_leach_ms(system, column):
    return _f(_frac(_FRAC_LEACH_MS, 'FracLeach_MS', system, column), 'kg N/kg N excreted',
              _FRAC_WHERE, f'{column.replace("_", " ")} column; leaching only from uncovered '
                           'manure without runoff containment (fn 5)')


# --- Ch. 11: N2O from managed soils (grazing) and indirect N2O ----------
# Table 11.1 (p. 11.13).
EF3_PRP_CPP = {
    None: _f(0.004, 'kg N2O-N/kg N', 'Vol. 4, Ch. 11, Table 11.1, p. 11.13', 'aggregated'),
    'wet': _f(0.006, 'kg N2O-N/kg N', 'Vol. 4, Ch. 11, Table 11.1, p. 11.13', 'wet climate'),
    'dry': _f(0.002, 'kg N2O-N/kg N', 'Vol. 4, Ch. 11, Table 11.1, p. 11.13', 'dry climate'),
}
EF3_PRP_SO = _f(0.003, 'kg N2O-N/kg N', 'Vol. 4, Ch. 11, Table 11.1, p. 11.13',
                "sheep and 'other animals' (incl. goats, fn 10); no climate split")
# Table 11.3 (p. 11.26).
EF4 = {
    None: _f(0.010, 'kg N2O-N/kg (NH3-N + NOx-N)', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26',
             'aggregated'),
    'wet': _f(0.014, 'kg N2O-N/kg (NH3-N + NOx-N)', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26',
              'wet climate'),
    'dry': _f(0.005, 'kg N2O-N/kg (NH3-N + NOx-N)', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26',
              'dry climate'),
}
EF5 = _f(0.011, 'kg N2O-N/kg N leached', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26')
FRAC_GASM = _f(0.21, 'kg (NH3-N + NOx-N)/kg N', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26',
               'organic N applied and dung and urine deposited by grazing animals')
FRAC_LEACH = {
    'wet': _f(0.24, 'kg N/kg N', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26', 'wet climate'),
    'dry': _f(0.0, 'kg N/kg N', 'Vol. 4, Ch. 11, Table 11.3, p. 11.26',
              'dry climate; 0.24 where irrigated other than by drip, section 11.2.2.2, p. 11.25'),
}
# Annex 11A.8, Table 8A.1 (p. 11.39): NH3-N and NOx-N per kg N applied or
# deposited, field data of manure application and excreta patches; FracGASM
# 0.21 (Table 11.3) is their sum (0.212), rounded.
PRP_NH3_N = _f(0.197, 'kg NH3-N/kg N', 'Vol. 4, Ch. 11, Annex 11A.8, Table 8A.1, p. 11.39',
               'mean of 172 measurements')
PRP_NOX_N = _f(0.015, 'kg NOx-N/kg N', 'Vol. 4, Ch. 11, Annex 11A.8, Table 8A.1, p. 11.39',
               'mean of 40 measurements')

# --- Climate zone (Vol. 4, Ch. 3, Annex 3A.5, Figure 3A.5.2, p. 3.48) ------
# Annex 10A.2 (p. 10.127) points to this figure; its text prints the
# PET/precipitation ratio the wrong way round, so the figure is followed.
CLIMATE_TREE_WHERE = 'IPCC 2019, Vol. 4, Ch. 3, Annex 3A.5, Figure 3A.5.2, p. 3.48'


def climate_zone(mat_c, map_mm=None, pet_mm=None, elevation_m=None, frost_days=None,
                 warmest_month_c=None):
    """The IPCC climate zone from mean annual temperature (MAT, deg C), mean
    annual precipitation (MAP, mm), potential evapotranspiration (PET, mm),
    elevation (m), frost days a year and the warmest monthly mean (deg C);
    each is asked for only where the tree needs it."""
    def need(value, name):
        if value is None:
            raise ValueError(f'{name} is needed to place the climate zone ({CLIMATE_TREE_WHERE})')
        return value
    if mat_c > 18 and need(frost_days, 'frost days a year') <= 7:
        if need(elevation_m, 'elevation') > 1000:
            return 'tropical_montane'
        p = need(map_mm, 'mean annual precipitation')
        return 'tropical_wet' if p > 2000 else 'tropical_moist' if p > 1000 else 'tropical_dry'
    moist = need(map_mm, 'mean annual precipitation') / need(pet_mm, 'potential '
                                                                     'evapotranspiration') > 1
    if mat_c > 10:
        return 'warm_temperate_moist' if moist else 'warm_temperate_dry'
    if mat_c > 0:
        return 'cool_temperate_moist' if moist else 'cool_temperate_dry'
    if need(warmest_month_c, 'mean temperature of the warmest month') < 10:
        return 'polar_moist' if moist else 'polar_dry'
    return 'boreal_moist' if moist else 'boreal_dry'


MOISTURE_WHERE = 'IPCC 2019, Vol. 4, Ch. 11, Table 11.1, fn 4, p. 11.13'


def moisture_from_zone(zone, map_mm=None):
    """Wet or dry for Ch. 11 (Table 11.1, fn 4): temperate and boreal zones by
    precipitation/PET above 1, tropical zones by precipitation above 1000 mm."""
    if zone.startswith('polar'):
        raise ValueError(f'{zone}: Table 11.1 (fn 4) defines wet and dry for temperate, boreal and '
                         f'tropical zones only; give moisture')
    if zone.endswith('_moist') and not zone.startswith('tropical') or zone == 'tropical_wet':
        return 'wet'
    if zone.endswith('_dry') and not zone.startswith('tropical'):
        return 'dry'
    if map_mm is None:
        if zone == 'tropical_moist':
            return 'wet'        # tropical moist means more than 1000 mm (Figure 3A.5.2)
        if zone == 'tropical_dry':
            return 'dry'        # less than 1000 mm
        raise ValueError(f'{zone}: the mean annual precipitation decides wet or dry '
                         f'({MOISTURE_WHERE})')
    return 'wet' if map_mm > 1000 else 'dry'


# --- Tier 1 (sections 10.3 and 10.5) --------------------------------------
# Region columns of Tables 10.13A and 10.19: four regions with one value,
# then five with a mean, a high- and a low-productivity column.
IPCC_REGIONS = ('north_america', 'western_europe', 'eastern_europe', 'oceania') + tuple(
    f'{r}_{p}' for r in ('latin_america', 'africa', 'middle_east', 'asia', 'india_subcontinent')
    for p in ('mean', 'high', 'low'))
_HIGH_PRODUCTIVITY_REGIONS = ('north_america', 'western_europe', 'eastern_europe', 'oceania')


def _row(first4, rest):
    """A row of Table 10.13A or 10.19: the first four region values, then
    the other fifteen, or one value for each of the two parts."""
    a = first4 if isinstance(first4, tuple) else (first4,) * 4
    b = rest if isinstance(rest, tuple) else (rest,) * 15
    return a + b


# Table 10.13A (p. 10.56): VS excretion rate, kg VS per 1000 kg animal mass
# and day. Buffalo: "NE" for high and low productivity (fn 2, no adequate
# difference between them), so the region's mean stands for both.
_VS_RATE = {
    'dairy_cattle': _row((9.2, 8.4, 6.7, 6.0), (7.9, 9.0, 7.1, 18.2, 21.7, 15.2, 10.7, 8.4, 11.8,
                                                  9.0, 8.1, 9.2, 14.1, 9.1, 16.1)),
    'other_cattle': _row((7.6, 5.7, 7.6, 8.7), (8.5, 8.1, 8.6, 12.1, 10.2, 12.7, 12.3, 9.3, 14.5,
                                                  9.8, 6.8, 10.8, 12.2, 13.5, 12.0)),
    'buffalo': _row((None, 7.7, 6.2, None), (11.2,) * 3 + (12.9,) * 3 + (9.8,) * 3 + (13.5,) * 3
                    + (15.2,) * 3),
    'swine_finishing': _row((3.9, 5.3, 4.9, 5.6), (6.4, 4.3, 10.0, 8.2, 5.3, 9.4, 4.9, 4.4, 7.8,
                                                     6.8, 5.1, 8.1, 8.6, 6.5, 9.5)),
    'swine_sows': _row((1.8, 2.4, 2.0, 2.1), (2.7, 1.7, 4.8, 4.4, 2.4, 6.0, 2.5, 2.3, 4.6, 3.4,
                                                2.3, 4.3, 4.6, 3.0, 5.5)),
    'laying_hens': _row((9.4, 8.6, 9.4, 8.6), (10.1, 9.3, 14.7, 10.2, 8.0, 11.6, 9.0, 8.4, 15.8,
                                                 9.3, 8.5, 12.8, 13.2, 11.6, 14.6)),
    'broilers': _row((16.8, 16.1, 16.0, 18.3), (15.6, 15.5, 17.8, 15.9, 16.0, 15.4, 17.7, 17.7,
                                                  17.9, 15.7, 15.6, 17.1, 17.7, 17.6, 18.2)),
    'sheep': _row(8.2, 8.3), 'goats': _row(9.0, 10.4), 'horses': _row(5.65, 7.2),
}
# Table 10.19 (p. 10.83): N excretion rate, kg N per 1000 kg animal mass and day.
_N_RATE = {
    'dairy_cattle': _row((0.59, 0.54, 0.42, 0.72), (0.39, 0.60, 0.28, 0.44, 0.41, 0.45, 0.50, 0.49,
                                                      0.51, 0.44, 0.55, 0.41, 0.65, 0.51, 0.70)),
    'other_cattle': _row((0.40, 0.42, 0.47, 0.46), (0.31, 0.36, 0.29, 0.45, 0.42, 0.44, 0.56, 0.51,
                                                      0.59, 0.38, 0.36, 0.39, 0.44, 0.64, 0.41)),
    'buffalo': _row((None, 0.45, 0.35, None), (0.41,) * 3 + (0.42,) * 3 + (0.39,) * 3 + (0.44,) * 3
                    + (0.58,) * 3),
    'swine_finishing': _row((0.46, 0.76, 0.77, 0.72), (0.73, 0.69, 0.80, 0.49, 0.39, 0.54, 0.73,
                                                         0.75, 0.60, 0.70, 0.63, 0.76, 0.76, 0.74,
                                                         0.76)),
    'swine_sows': _row((0.24, 0.38, 0.36, 0.31), (0.35, 0.32, 0.43, 0.29, 0.21, 0.35, 0.40, 0.41,
                                                    0.37, 0.37, 0.32, 0.43, 0.43, 0.37, 0.47)),
    'laying_hens': _row((1.13, 0.87, 0.81, 1.04), (1.17, 1.02, 2.01, 1.20, 0.99, 1.34, 1.11, 1.06,
                                                     1.70, 1.00, 0.89, 1.50, 1.65, 1.60, 1.70)),
    'broilers': _row((1.59, 1.14, 1.12, 1.59), (1.23, 1.21, 2.39, 1.40, 1.34, 1.58, 1.43, 1.42,
                                                  1.95, 1.35, 1.31, 1.84, 1.58, 1.47, 2.11)),
    'sheep': _row((0.35, 0.36, 0.36, 0.43), 0.32), 'goats': _row((0.46, 0.46, 0.44, 0.42), 0.34),
    'horses': _row((0.30, 0.26, 0.30, 0.30), 0.46),
}
_TIER1_ROW_LABEL = {'swine_finishing': 'swine, finishing', 'swine_sows': 'swine, breeding',
                    'laying_hens': 'hens >= 1 year', 'broilers': 'broilers'}


def _tier1_rate(table, category, region, where, unit):
    if category not in table:
        raise KeyError(f'{where}: no row for {category}')
    value = table[category][IPCC_REGIONS.index(region)]
    if value is None:
        raise ValueError(f'{where}: {category} does not occur in {region.replace("_", " ")} (NA)')
    note = f'{_TIER1_ROW_LABEL.get(category, category.replace("_", " "))}, ' \
           f'{region.replace("_", " ")}'
    if category == 'buffalo' and region.endswith(('_high', '_low')) and table is _VS_RATE:
        note += '; NE for this productivity (fn 2), the regional mean'
    return _f(value, unit, where, note)


def vs_rate(category, region):
    return _tier1_rate(_VS_RATE, category, region, 'Vol. 4, Ch. 10, Table 10.13A, p. 10.56',
                       'kg VS/(1000 kg animal mass*d)')


def n_rate(category, region):
    return _tier1_rate(_N_RATE, category, region, 'Vol. 4, Ch. 10, Table 10.19, p. 10.83',
                       'kg N/(1000 kg animal mass*d)')


EQ_VS_TIER1 = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.22A, p. 10.55'
EQ_NEX_TIER1 = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.30, p. 10.80'
EQ_ENTERIC_TIER1 = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.19, p. 10.39'
# Table 10.10 (p. 10.38): enteric CH4, kg per head and year (high, low
# productivity) and the live weights they stand for. Fn 1: outside North
# America, Europe and Oceania the simple Tier 1 takes the low values.
# Cattle and buffalo are in Table 10.11 (not used: cattle need Tier 2 or the
# simplified Tier 2 intake); poultry: "insufficient data for calculation".
_ENTERIC_TIER1 = {'sheep': (9, 5, '65 kg', '45 kg'), 'swine': (1.5, 1, '72 kg', '52 kg'),
                  'goats': (9, 5, '50 kg', '28 kg'), 'horses': (18, 18, '550 kg', '550 kg')}
_ENTERIC_TIER1_ROW = {'sheep': 'sheep', 'goats': 'goats', 'swine_finishing': 'swine',
                      'swine_sows': 'swine', 'horses': 'horses'}


def enteric_tier1(category, region):
    row = _ENTERIC_TIER1_ROW.get(category)
    if row is None:
        raise ValueError(f'{category}: IPCC 2019 Table 10.10 gives no Tier 1 enteric factor '
                         f'(cattle and buffalo need intake data; poultry: insufficient data)')
    high = region in _HIGH_PRODUCTIVITY_REGIONS or region.endswith('_high')
    ef_high, ef_low, w_high, w_low = _ENTERIC_TIER1[row]
    if row == 'horses':
        note = f'horses, live weight {w_high}'
    else:
        note = (f'{row}, high productivity systems, live weight {w_high}' if high else
                f'{row}, low productivity systems, live weight {w_low}'
                + ('' if region.endswith('_low') else ' (fn 1: low outside North America, '
                                                      'Europe and Oceania)'))
    return _f(ef_high if high else ef_low, 'kg CH4/(head*year)',
              'Vol. 4, Ch. 10, Table 10.10, p. 10.38', note)


# --- Simplified Tier 2 dry matter intake of cattle (p. 10.31-10.33) -------
# Eq. 10.17-10.18B and Table 10.8; IPCC uses them to check the Tier 2
# intake and, where the data for Tier 2 are missing, to predict it.
DMI_EQUATIONS = ('calves', 'growing_cattle', 'feedlot_steers_bulls', 'feedlot_heifers',
                 'mature_beef_cows', 'lactating_dairy_cows')
_DMI_WHERE = {'calves': 'Eq. 10.17, p. 10.31', 'growing_cattle': 'Eq. 10.18, p. 10.31',
              'feedlot_steers_bulls': 'Eq. 10.18A, p. 10.31',
              'feedlot_heifers': 'Eq. 10.18A, p. 10.31',
              'mature_beef_cows': 'Table 10.8, p. 10.32',
              'lactating_dairy_cows': 'Eq. 10.18B, p. 10.32'}
# Table 10.8 (p. 10.32): forage DMI capacity of mature non-dairy cows, % of
# body weight (non-lactating, lactating), by DE: < 52, 52-59, > 59 %.
_T108 = ((2.5, 2.7, 'high quality, DE > 59 %'), (2.2, 2.5, 'average quality, DE 52-59 %'),
         (1.8, 2.2, 'low quality, DE < 52 %'))


def nemf_from_de(rem, de_pct):
    """Table 10.8A source note (p. 10.33): NEmf = REM x 18.45 x DE/100."""
    return rem * GE_PER_KG_DM.value * de_pct / 100


def simplified_dmi(equation, bw, nemf=None, de_pct=None, lactating=False, milk_kg_day=None,
                   fat_pct=None):
    """Dry matter intake, kg per head and day, and the text of the step."""
    where = f'IPCC 2019, Vol. 4, Ch. 10, {_DMI_WHERE[equation]}'
    if equation in ('calves', 'growing_cattle'):
        c = 0.1128 if equation == 'calves' else 0.0869
        dmi = bw ** 0.75 * (0.0582 * nemf - 0.00266 * nemf ** 2 - c) / (0.239 * nemf)
        return dmi, (f'BW {bw:g} kg^0.75 x (0.0582 x NEmf {nemf:.3g} - 0.00266 x NEmf^2 - {c}) / '
                     f'(0.239 x NEmf) MJ/kg DM ({where})')
    if equation == 'feedlot_steers_bulls':
        return 3.83 + 0.0143 * bw * 0.96, f'3.83 + 0.0143 x BW {bw:g} kg x 0.96 ({where})'
    if equation == 'feedlot_heifers':
        return 3.184 + 0.01536 * bw * 0.96, f'3.184 + 0.01536 x BW {bw:g} kg x 0.96 ({where})'
    if equation == 'mature_beef_cows':
        dry, lact, label = _T108[0] if de_pct > 59 else _T108[1] if de_pct >= 52 else _T108[2]
        share = lact if lactating else dry
        return bw * share / 100, (f'{share} % of BW {bw:g} kg, forage {label}, '
                                  f'{"lactating" if lactating else "non-lactating"} ({where})')
    if equation == 'lactating_dairy_cows':
        fcm = 0.4324 * milk_kg_day + 16.216 * milk_kg_day * fat_pct / 100
        return 0.0185 * bw + 0.305 * fcm, (f'0.0185 x BW {bw:g} kg + 0.305 x FCM {fcm:.3g} kg/d '
                                           f'(3.5 % FCM = 0.4324 x milk + 16.216 x fat) ({where})')
    raise KeyError(equation)


# Text below Eq. 10.18B (p. 10.32): DMI is "in the order of 2 to 3 percent of
# the bodyweight of the mature or growing animals and up to 4 percent for
# high yielding lactating dairy cattle".
DMI_CHECK_WHERE = 'IPCC 2019, Vol. 4, Ch. 10, p. 10.32'

# --- N retention, Tier 2 option 2 for pigs and poultry (p. 10.86-10.89) ---
N_RET_PIG_BW = 0.025             # kg N per kg BW gain, Eq. 10.33A and 10.33B
N_RET_PIGLET_BIRTH_CORR = 0.806  # Eq. 10.33A
N_RET_PROTEIN_DIGEST = 0.98      # Eq. 10.33B
# Table 10.20B (p. 10.88): Ngain of growing pigs by phase, kg N per kg BW.
N_GAIN_PIG_PHASES = ((4, 7, 0.031), (7, 20, 0.028), (20, 40, 0.025), (40, 80, 0.024),
                     (80, 120, 0.021))
N_LW_HENS = 0.028                # kg N per kg live weight, Eq. 10.33D
N_EGG = 0.0185                   # kg N per kg egg, Eq. 10.33D
N_GAIN_BROILERS = 0.028          # kg N per kg BW gain, Eq. 10.33E
EQ_N_RET_SOWS = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.33A-B, p. 10.86 (as Table 10.20A, p. 10.87)'
EQ_N_RET_PIGS = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.33C, p. 10.87, Table 10.20B, p. 10.88'
EQ_N_RET_HENS = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.33D, p. 10.88'
EQ_N_RET_BROILERS = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.33E, p. 10.89'
EQ_NEX_OPTION2 = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.31A, p. 10.81'

# --- Liquid storage and digesters (Table 10.17, Table 10.22) --------------
# Table 10.17 fn 1 (p. 10.70): "A reduction of 40% due to crust cover may be
# applied only when a thick, dry, crust is present"; a solid cover reduces
# CH4 "by 25 to 50% (range: 0 to 90%)", no single value.
MCF_CRUST_REDUCTION = _f(0.40, 'fraction of MCF', 'Vol. 4, Ch. 10, Table 10.17, fn 1, p. 10.70',
                         'thick, dry crust only')
COVER_REDUCTION_RANGE = (0.25, 0.50)
DIGESTER_TYPES = ('low_leak_gastight_best', 'low_leak_low_quality_gastight',
                  'low_leak_open_storage', 'high_leak_high_quality_gastight',
                  'high_leak_low_quality_gastight', 'high_leak_open_storage')
DIGESTER_OPEN_STORAGE = ('low_leak_open_storage', 'high_leak_open_storage')
# Table 10.22 fn 3 (p. 10.98): FracGas_MS of digestate storage 0.05-0.50; "It
# is advised to use the liquid slurry without cover for uncovered digestate."
FRAC_GAS_DIGESTER_RANGE = (0.05, 0.50)
