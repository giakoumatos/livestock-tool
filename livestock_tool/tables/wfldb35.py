"""WFLDB Methodological Guidelines v3.5 (Nemecek et al. 2019): the rules
the livestock tool follows, and the values WFLDB publishes that have no
newer edition (printed page = PDF page).

Where WFLDB cites an IPCC 2006 or EMEP/EEA 2016 table, the tool takes the
same table from the IPCC 2019 Refinement or the EMEP/EEA 2023 Guidebook
(tables/ipcc2019.py, tables/emep2023.py), and WFLDB's structure stays.
"""
from ..sources import WFLDB35, Factor


def _f(value, unit, where, note=''):
    return Factor(value, unit, WFLDB35, where, note)


# 3.9.3.2 (p. 38) and 3.9.4 (p. 38-39): the N volatilised from manure
# management and from excreta on pasture is 60 % NH3 and 40 % NOx; on
# pasture it is taken on the TAN of the excreta.
NH3_SHARE = _f(0.60, 'kg NH3-N/kg N volatilised', 'section 3.9.3.2, p. 38',
               'proportions observed in EEA 2016, 3.D, Tab. 3.1')
NOX_SHARE = _f(0.40, 'kg NOx-N/kg N volatilised', 'section 3.9.4, p. 38-39',
               'proportions observed in EEA 2016, 3.D, Tab. 3.1')

# Tab. 10 (p. 41): Ym for animals IPCC gives none for. IPCC 2019 has no Ym
# for pigs, horses or poultry either, so WFLDB's published values stay.
YM_FOEN = {
    'swine': _f(0.60, '% of GE', 'section 3.9.6.1, Tab. 10, p. 41', 'FOEN (2013)'),
    'horses': _f(2.50, '% of GE', 'section 3.9.6.1, Tab. 10, p. 41', 'FOEN (2013)'),
    'poultry': _f(0.16, '% of GE', 'section 3.9.6.1, Tab. 10, p. 41', 'FOEN (2013)'),
}

# 3.5.5 (p. 29): water for animals, 83 % consumed and 17 % released when no
# specific data are available (Shaffer 2008).
WATER_RELEASED = _f(0.17, 'm3/m3', 'section 3.5.5, p. 29', 'Shaffer (2008)')
# 3.5.2, Tab. 4 (p. 27): irrigation efficiency EFirr = Ea x Ec (FAO 1989).
IRRIGATION_EFFICIENCY = {
    'surface': _f(0.45, '-', 'section 3.5.2, Tab. 4, p. 27', 'surface irrigation, 0.60 x 0.75'),
    'sprinkler': _f(0.75, '-', 'section 3.5.2, Tab. 4, p. 27', 'sprinkler irrigation, 0.75 x 1.00'),
    'drip': _f(0.90, '-', 'section 3.5.2, Tab. 4, p. 27', 'drip irrigation, 0.90 x 1.00'),
}
# Tab. 34 (p. 81-82, ICID 2012): share of the irrigated area under sprinkler
# and micro (drip) irrigation, %, by country; the rest is surface irrigation.
# WFLDB's level 1 default (3.5.2): the country shares weight Tab. 4. Some
# printed shares exceed 100 % (the source's area figures); they are capped.
IRRIGATION_SHARES = {
    'IN': ('India', 5, 3, 2010),
    'CN': ('China', 5, 3, 2009),
    'US': ('United States', 50, 7, 2009),
    'IR': ('Iran', 5, 3, 2009),
    'MX': ('Mexico', 6, 3, 1999),
    'TR': ('Turkey', 9, 3, 2012),
    'RU': ('Russia', 56, 1, 2008),
    'BR': ('Brazil', 54, 7, 2006),
    'UZ': ('Uzbekistan', 102, 0, 2009),
    'ES': ('Spain', 23, 48, 2011),
    'EG': ('Egypt', 13, 3, 2000),
    'FR': ('France', 48, 4, 2011),
    'IT': ('Italy', 37, 21, 2010),
    'AU': ('Australia', 21, 7, 2000),
    'JP': ('Japan', 17, 2, 2010),
    'UA': ('Ukraine', 112, 2, 2010),
    'KZ': ('Kazakhstan', 66, 1, 2006),
    'ZA': ('South Africa', 55, 22, 2012),
    'MA': ('Morocco', 12, 1, 2003),
    'SA': ('Saudi Arabia', 44, 12, 2004),
    'PH': ('Philippines', 0, 0, 2004),
    'RO': ('Romania', 30, 0, 2008),
    'AZ': ('Azerbaijan', 43, 0, 2009),
    'SY': ('Syria', 7, 5, 2000),
    'CL': ('Chile', 1, 2, 2006),
    'KR': ('Korea', 20, 40, 2009),
    'CA': ('Canada', 79, 1, 2004),
    'PT': ('Portugal', 6, 4, 1999),
    'BG': ('Bulgaria', 4, 1, 2008),
    'DE': ('Germany', 97, 1, 2005),
    'TW': ('Chinese Taipei', 5, 2, 2009),
    'MY': ('Malaysia', 1, 1, 2009),
    'SK': ('Slovak Republic', 99, 1, 2000),
    'IL': ('Israel', 26, 74, 2000),
    'MD': ('Moldova', 64, 7, 2009),
    'HU': ('Hungary', 84, 3, 2008),
    'CZ': ('Czech Republic', 7, 3, 2007),
    'GB': ('Great Britain', 95, 5, 2005),
    'PL': ('Poland', 5, 8, 2008),
    'FI': ('Finland', 86, 14, 2010),
    'MW': ('Malawi', 79, 10, 2000),
    'MK': ('Macedonia', 9, 2, 2008),
    'SI': ('Slovenia', 111, 10, 2009),
    'LT': ('Lithuania', 101, 0, 2010),
    'EE': ('Estonia', 50, 50, 2010),
}


def irrigation_efficiency(country):
    """EFirr of a country from its Tab. 34 shares and the Tab. 4 values, and
    the words for it; None for a country Tab. 34 does not list."""
    row = IRRIGATION_SHARES.get(country)
    if row is None:
        return None
    name, s, m, year = row
    sprinkler = min(s, 100) / 100
    micro = min(m, 100 - min(s, 100)) / 100
    surface = 1 - sprinkler - micro
    e = IRRIGATION_EFFICIENCY
    ef = surface * e['surface'].value + sprinkler * e['sprinkler'].value + micro * e['drip'].value
    capped = ' (printed shares above 100 %, capped)' if s + m > 100 else ''
    return ef, (f'{name}: {s} % sprinkler and {m} % micro irrigation{capped}, so '
                f'{round(surface * 100)} % surface (Tab. 34, p. 81-82, ICID 2012, reported {year}), weighted with the EFirr of '
                f'Tab. 4 (surface 0.45, sprinkler 0.75, drip 0.90): {ef:.3f} (section 3.5.2, level 1)')


# 3.5.4 (p. 29): irrigation water to air = ETirr (= withdrawal x EFirr); the
# rest 80 % to surface water and 20 % to ground water (after Lévová & Pfister 2012).
IRRIGATION_SURFACE_SHARE = _f(0.8, '-', 'section 3.5.4, p. 29', 'Lévová & Pfister 2012')

# The rules the metadata and the flow comments state.
RULE_MANURE_SPREADING = ('Emissions from manure spreading are not included: they belong to the '
                         'crop and feed production that receives the manure (Nemecek et al. 2019, '
                         'WFLDB guidelines v3.5, section 3.12).')
RULE_PASTURE = ('WFLDB counts the excreta dropped on pasture in the pasture datasets (section '
                '3.12.2); here the grazing land is occupied by this dataset itself, so the '
                'emissions from the excreta on it are included here.')
RULE_FIBRE_UNIT = ('Animal fibre is counted as greasy weight at the farm gate (Nemecek et al. '
                   '2019, WFLDB guidelines v3.5, section 3.2.2).')
RULE_ECONOMIC_ALLOCATION = ('WFLDB allocates the meat and fibre of sheep farms economically by '
                            'default (Nemecek et al. 2019, WFLDB guidelines v3.5, section '
                            '2.6.3).')
# 2.6.3 (p. 17): dairy by IDF 2015; where the data for it are missing, the
# default 12 % to meat and 88 % to milk (FPCM), BMR 0.02 kg meat/kg milk.
DAIRY_DEFAULT_MEAT_SHARE = _f(0.12, 'kg/kg', 'section 2.6.3, p. 17',
                              'IDF 2015; PEFCR dairy products (EDA 2018)')
DAIRY_DEFAULT_MILK_SHARE = _f(0.88, 'kg/kg', 'section 2.6.3, p. 17',
                              'IDF 2015; PEFCR dairy products (EDA 2018)')
RULE_EGG_ALLOCATION = ('WFLDB allocates the spent hens of egg production economically by default; '
                       'their value is in most cases negligible, so no allocation is needed unless '
                       'otherwise specified (Nemecek et al. 2019, WFLDB guidelines v3.5, section '
                       '2.6.3, p. 17).')
RULE_NO_ALLOCATION_RULE = ('WFLDB gives no allocation rule for these animals; it refers to the LEAP '
                           'guidelines to support the choice (Nemecek et al. 2019, WFLDB guidelines '
                           'v3.5, section 2.6.3, p. 17).')
RULE_CH4_SEPARATE = ('Enteric and manure methane are kept on separate rows (Nemecek et al. 2019, '
                     'WFLDB guidelines v3.5, section 3.9.6).')
