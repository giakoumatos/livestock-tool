from ..tables import ipcc2019 as ipcc
from .atomic_mass import CH4_KG_PER_M3
from .base import Model, fmt, pct
from .model_enums import CATEGORIES, SYSTEMS


def system_mcf(key, system, zone, inputs):
    """The MCF of one system (Table 10.17) and the words for it: liquid and
    pit storage by retention time; a thick, dry crust lowers it by 40 % and a
    solid cover by the reduction given (fn 1); digesters by their type."""
    if system.mcf == 'liquid':
        months = int(inputs.get('liquid_retention_months') or 6)
        mcf = ipcc.mcf(f'liquid_slurry_{months}_month', zone)
        value, text = mcf.value, f'MCF {fmt(mcf.value)} % ({mcf.note}, {months} months)'
        if key == 'liquid_slurry_crust' and inputs.get('crust_thick_dry'):
            r = ipcc.MCF_CRUST_REDUCTION
            value *= 1 - r.value
            text += f' less {pct(r.value)} for a thick, dry crust ({r.cite()}) = {fmt(value)} %'
        elif key == 'liquid_slurry_cover' and inputs.get('cover_ch4_reduction') is not None:
            r = inputs['cover_ch4_reduction']
            low, high = ipcc.COVER_REDUCTION_RANGE
            if not 0 <= r <= 0.9:
                raise ValueError(f'cover_ch4_reduction {r} is outside 0-0.9 (IPCC 2019 Table 10.17, '
                                 f'fn 1)')
            value *= 1 - r
            text += (f' less {pct(r)} for the solid cover, given (IPCC 2019 Table 10.17, fn 1: '
                     f'{pct(low)}-{pct(high)}, range 0-90 %) = {fmt(value)} %')
        return value, text
    if system.mcf == 'digester':
        kind = inputs.get('digester_type')
        if kind not in ipcc.DIGESTER_TYPES:
            raise ValueError('anaerobic digester: give digester_type (IPCC 2019 Table 10.17: '
                             + ', '.join(ipcc.DIGESTER_TYPES) + ')')
        mcf = ipcc.mcf(f'anaerobic_digester_{kind}', zone)
        return mcf.value, f'MCF {fmt(mcf.value)} % ({kind.replace("_", " ")}, {mcf.note})'
    mcf = ipcc.mcf(system.mcf, zone)
    return mcf.value, f'MCF {fmt(mcf.value)} % ({mcf.note})'


class ManureCh4Model(Model):
    """Methane from manure management of one animal class, IPCC 2019 Tier 2
    (Vol. 4, Ch. 10, Eq. 10.23, p. 10.64):
    EF = VS x 365 x B0 x 0.67 x sum(MCF/100 x AWMS). On pasture, range and
    paddock the MCF of 0.47 % is used with B0 0.19 (Table 10.17, fn 2).

    Inputs:
      category, head, vs (kg VS/(head*day)),
      shares: {manure system: share of the manure}, adding up to 1
      climate_zone: IPCC climate zone (tables.ipcc2019.CLIMATE_ZONES)
      b0_region: column of Table 10.16A ('western_europe', 'other_low', ...)
      liquid_retention_months: 1, 3, 4, 6 or 12 (liquid and pit storage;
        6 if not known, Table 10.17 fn 1)
      crust_thick_dry: liquid storage with a natural crust has a thick, dry
        crust (MCF - 40 %, Table 10.17 fn 1)
      cover_ch4_reduction: CH4 reduction of a solid cover on liquid storage
        (fn 1: 25-50 %), or None (no reduction)
      digester_type: row of Table 10.17 for an anaerobic digester
      pasture_in_dataset: the excreta on pasture count here (else they belong
        to the pasture dataset, WFLDB v3.5 section 3.12.2)
    Outputs:
      m_manure_ch4: kg CH4/year for the class
    """

    _input_variables = ('category', 'head', 'vs', 'shares', 'climate_zone', 'b0_region')

    def compute(self):
        cat = CATEGORIES[self.category]
        b0_animal = ipcc.b0(cat.b0, self.b0_region)
        per_head, parts = 0.0, []
        for key, share in self.shares.items():
            if not share or (key == 'pasture' and not self.inputs.get('pasture_in_dataset', True)):
                continue
            system = SYSTEMS[key]
            mcf, mcf_text = system_mcf(key, system, self.climate_zone, self.inputs)
            b0 = ipcc.B0_PRP if key == 'pasture' else b0_animal
            ch4 = self.vs * 365 * b0.value * CH4_KG_PER_M3 * mcf / 100 * share
            per_head += ch4
            parts.append(f'{system.label} {pct(share)}: {mcf_text}, B0 {fmt(b0.value)}')
        total = per_head * self.head
        self.note('ch4_manure',
                  f'{fmt(per_head)} kg CH4 per head and year = VS {fmt(self.vs)} kg/d x 365 x B0 x '
                  f'0.67 kg/m3 x MCF x share ({ipcc.EQ_MANURE_CH4}), by system: '
                  + '; '.join(parts) +
                  f' (MCF: {ipcc._MCF_WHERE}; B0: {b0_animal.cite()}, {b0_animal.note}; '
                  f'pasture B0 {ipcc.B0_PRP.value}, same table); x {fmt(self.head)} head = '
                  f'{fmt(total)} kg')
        return {'m_manure_ch4': total}
