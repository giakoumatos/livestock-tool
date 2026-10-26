"""Which method set a geography uses (user's rules, 2026-10-21).

  CH       -> SALCA v1.0.1
  EU-27    -> IPCC 2019 for greenhouse gases and N flows, EMEP/EEA 2023 for
              NH3, NOx, NMVOC and particulate matter
  any other-> IPCC 2019 within the scope of WFLDB v3.5
"""
from enum import Enum

EU27 = frozenset((
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT',
    'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'))


class Route(Enum):
    SALCA = 'CH'
    EU = 'EU'
    WFLDB = 'other'


def country_of(geography):
    """The country part of an ecoinvent geography code: 'CN-NM' is CN."""
    return geography.split('-')[0].upper()


def route_for(geography):
    """The route of an ecoinvent geography code: its country part decides,
    so 'CN-NM' is China and 'ES-AN' is Spain."""
    country = country_of(geography)
    if country == 'CH':
        return Route.SALCA
    if country in EU27:
        return Route.EU
    return Route.WFLDB
