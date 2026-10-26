from ..tables import ipcc2019 as ipcc
from ..tables import wfldb35 as wfldb
from .atomic_mass import CH4_MJ_PER_KG
from .base import Model, fmt
from .model_enums import CATEGORIES


def ym_factor(inputs):
    """Ym, in this order: given in the data collection; IPCC 2019 Table
    10.12 for cattle and buffalo (the class given, or the one milk yield,
    DE, NDF or forage share point to); Table 10.13 for sheep and goats;
    WFLDB Tab. 10 where IPCC gives none (pigs, horses, poultry)."""
    if inputs.get('ym_pct') is not None:
        return inputs['ym_pct'], inputs.get('ym_source') or 'given in the data collection'
    cat = CATEGORIES[inputs['category']]
    if cat.energy == 'cattle':
        # The dairy block of Table 10.12 is "Dairy cows and Buffalo".
        dairy = cat.key == 'dairy_cattle' or (cat.key == 'buffalo' and inputs.get('milk_kg_day'))
        key = inputs.get('ym_class') or ipcc.ym_cattle_class(
            dairy, (inputs.get('milk_kg_day') or 0) * 365, inputs['de_pct'],
            inputs.get('ndf_pct'), inputs.get('forage_share'))
        if key not in ipcc.YM_CATTLE:
            raise ValueError(f'{cat.label}: the data do not decide the row of IPCC 2019 Table '
                             f'10.12; give ym_class ({", ".join(ipcc.YM_CATTLE)})')
        f = ipcc.YM_CATTLE[key]
        return f.value, f'{f.cite()}, {f.note}'
    if cat.ym == 'sheep':
        f = ipcc.ym_sheep(inputs.get('dmi'))
        return f.value, f'{f.cite()}, {f.note}' if f.note else f.cite()
    if cat.ym in ipcc.YM:
        f = ipcc.YM[cat.ym]
    elif cat.ym in wfldb.YM_FOEN:
        f = wfldb.YM_FOEN[cat.ym]
    else:
        raise ValueError(f'{cat.label}: no Ym in the sources; give ym_pct in the data collection')
    return f.value, f.cite()


class EntericModel(Model):
    """Enteric methane of one animal class, IPCC 2019 Tier 2 (Vol. 4,
    Ch. 10, Eq. 10.21, p. 10.47): EF = GE x Ym/100 x 365 / 55.65.

    Inputs:
      category: key of model_enums.CATEGORIES
      ge: gross energy intake, MJ/(head*day)
      ym_pct, ym_source: Ym given in the data collection (% of GE), or None
      ym_class: row of IPCC 2019 Table 10.12 (cattle, buffalo), or None
      milk_kg_day, de_pct, ndf_pct, forage_share: to find that row
      head: average number of animals present in the year
    Outputs:
      m_enteric_ch4: kg CH4/year for the class
    """

    _input_variables = ('category', 'ge', 'head')

    def compute(self):
        if self.ge is None:
            return self._tier1()
        ym, ym_cite = ym_factor(self.inputs)
        per_head = self.ge * ym / 100 * 365 / CH4_MJ_PER_KG
        total = per_head * self.head
        self.note('ch4_enteric', f'{fmt(per_head)} kg CH4 per head and year = GE {fmt(self.ge)} '
                                 f'MJ/d x Ym {fmt(ym)} % ({ym_cite}) x 365 / '
                                 f'{CH4_MJ_PER_KG} MJ/kg ({ipcc.EQ_ENTERIC}), x {fmt(self.head)} '
                                 f'head = {fmt(total)} kg')
        return {'m_enteric_ch4': total}

    def _tier1(self):
        """IPCC 2019 Tier 1 (Eq. 10.19): the Table 10.10 factor x head."""
        region = self.inputs.get('ipcc_region')
        if region is None:
            raise ValueError('Tier 1 (no intake data): give ipcc_region (IPCC 2019 Tables 10.10, '
                             '10.13A and 10.19)')
        cat = CATEGORIES[self.category]
        if cat.ym == 'poultry':
            self.note('ch4_enteric', 'no enteric methane: IPCC 2019 Table 10.10 (p. 10.38) has '
                                     '"insufficient data for calculation" for poultry, and without '
                                     'an intake WFLDB\'s Ym cannot be applied')
            return {'m_enteric_ch4': 0.0}
        ef = ipcc.enteric_tier1(self.category, region)
        total = ef.value * self.head
        self.note('ch4_enteric', f'{fmt(ef.value)} kg CH4 per head and year by IPCC 2019 Tier 1 '
                                 f'({ef.cite()}, {ef.note}; {ipcc.EQ_ENTERIC_TIER1}), x '
                                 f'{fmt(self.head)} head = {fmt(total)} kg')
        return {'m_enteric_ch4': total}
