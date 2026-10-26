from ..tables import emep2023 as emep
from .base import Model, fmt, pct
from .model_enums import CATEGORIES

_POULTRY = ('laying_hens', 'broilers')


class ParticulateModel(Model):
    """Particulate matter from housing of one animal class.

    EMEP/EEA 2023, 3.B, Table 3-5 (Tier 1, kg per animal and year in
    housing). WFLDB v3.5 (section 3.9.12, Tab. 29) takes PM2.5 from the
    2016 edition of this table; the EU route adds PM10 and TSP. The factor
    applies to housed animals only, so it is taken on the share of the year
    the class is housed (EMEP/EEA 2023, 3.B, p. 18); poultry count as housed
    all year, free-range or not (same page).

    Inputs:
      category, head, housed_share (share of the year in buildings),
      route: 'WFLDB' or 'EU'
    Outputs (kg/year for the class):
      m_pm_pm25, m_pm_pm25_10, m_pm_pm10_plus
    """

    _input_variables = ('category', 'head', 'housed_share', 'route')

    def compute(self):
        cat = CATEGORIES[self.category]
        share = 1.0 if self.category in _POULTRY else self.housed_share
        aap = self.head * share
        pm25 = emep.pm_tier1(cat.emep, 'pm25')
        out = {'m_pm_pm25': pm25.value * aap, 'm_pm_pm25_10': 0.0, 'm_pm_pm10_plus': 0.0}
        basis = (f'{fmt(self.head)} head x {pct(share)} of the year housed = {fmt(aap)} animals '
                 f'in housing')
        self.note('pm25', f'{basis} x {pm25.value} kg PM2.5 per animal and year ({pm25.cite()}'
                          + ('; WFLDB v3.5, section 3.9.12, Tab. 29' if self.route == 'WFLDB'
                             else '') + f') = {fmt(out["m_pm_pm25"])} kg')
        if self.route == 'EU':
            pm10, tsp = emep.pm_tier1(cat.emep, 'pm10'), emep.pm_tier1(cat.emep, 'tsp')
            out['m_pm_pm25_10'] = (pm10.value - pm25.value) * aap
            out['m_pm_pm10_plus'] = (tsp.value - pm10.value) * aap
            self.note('pm25_10', f'{basis} x (PM10 {pm10.value} - PM2.5 {pm25.value}) kg per '
                                 f'animal and year ({pm10.cite()}) = {fmt(out["m_pm_pm25_10"])} kg')
            self.note('pm10_plus', f'{basis} x (TSP {tsp.value} - PM10 {pm10.value}) kg per '
                                   f'animal and year ({tsp.cite()}) = '
                                   f'{fmt(out["m_pm_pm10_plus"])} kg')
        return out


class NmvocModel(Model):
    """NMVOC of one animal class, EU route only (WFLDB v3.5 has no NMVOC
    model). EMEP/EEA 2023, 3.B, Tier 2 (section 3.4.2, Eq. 48-60, p. 27-28):
    silage store and feeding, housing, manure store (as a share of housing,
    by the NH3 ratio) and grazing; manure application is left out (WFLDB
    v3.5, section 3.12). Cattle per MJ of gross feed intake (Table 3-11),
    other animals per kg VS excreted (Table 3-12).

    Inputs:
      category, head, ge (MJ/(head*day)), vs (kg VS/(head*day)), housed_share,
      silage_share_of_max (Frac_of_maxsilage, 0 when no silage is fed),
      nh3_hous, nh3_storage (kg NH3/year, from EmepNitrogenModel)
    Outputs:
      m_nmvoc: kg NMVOC/year for the class
    """

    _input_variables = ('category', 'head', 'ge', 'vs', 'housed_share', 'silage_share_of_max',
                        'nh3_hous', 'nh3_storage')

    def compute(self):
        cat = CATEGORIES[self.category]
        cattle = cat.emep in emep.NMVOC_TIER2_MJ
        basis = self.ge * 365 if cattle else self.vs * 365
        unit = 'MJ GE' if cattle else 'kg VS'
        x = self.housed_share
        silage = self.silage_share_of_max or 0.0
        parts, total = [], 0.0
        if silage:
            ef_s = emep.nmvoc_tier2(cat.emep, 'silage_feeding')
            feeding = basis * x * ef_s.value * silage
            store = feeding * emep.SILAGE_STORE_SHARE.value
            total += feeding + store
            parts.append(f'silage feeding and store {fmt(feeding + store)} kg (EF {ef_s.value}, '
                         f'silage {pct(silage)} of the maximum, store share '
                         f'{emep.SILAGE_STORE_SHARE.value})')
        ef_h = emep.nmvoc_tier2(cat.emep, 'building')
        hous = basis * x * ef_h.value
        total += hous
        parts.append(f'housing {fmt(hous)} kg (EF {ef_h.value})')
        if self.nh3_hous:
            store_m = hous * self.nh3_storage / self.nh3_hous
            total += store_m
            parts.append(f'manure store {fmt(store_m)} kg (housing x NH3 storage/housing ratio)')
        try:
            if not self.inputs.get('pasture_in_dataset', True):
                raise KeyError('pasture not in this dataset')
            ef_g = emep.nmvoc_tier2(cat.emep, 'grazing')
            graz = basis * (1 - x) * ef_g.value
            total += graz
            parts.append(f'grazing {fmt(graz)} kg (EF {ef_g.value})')
        except KeyError:
            pass
        per_head = total
        total *= self.head
        self.note('nmvoc', f'per head: {fmt(basis)} {unit} a year, {pct(x)} housed: '
                           + '; '.join(parts) + f' ({ef_h.cite()}; EMEP/EEA 2023, 3.B, Eq. 48-60, '
                           f'p. 27-28); x {fmt(self.head)} head = {fmt(total)} kg NMVOC')
        return {'m_nmvoc': total}
