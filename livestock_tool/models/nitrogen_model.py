from ..sources import GIVEN, Factor
from ..tables import emep2023 as emep
from ..tables import ipcc2019 as ipcc
from ..tables import wfldb35 as wfldb
from .atomic_mass import N_TO_N2O, N_TO_NH3, N_TO_NO2, N_TO_NO3
from .base import Model, fmt, pct
from .model_enums import CATEGORIES, SYSTEMS


def ef3_prp(category, moisture):
    cat = CATEGORIES[category]
    return ipcc.EF3_PRP_SO if cat.prp == 'SO' else ipcc.EF3_PRP_CPP[moisture]


def frac_leach_pasture(moisture, irrigated):
    if moisture is None:
        raise ValueError('wet or dry climate is needed for N leaching from pasture '
                         '(IPCC 2019, Vol. 4, Ch. 11, Table 11.3)')
    return ipcc.FRAC_LEACH['wet' if moisture == 'wet' or irrigated else 'dry']


# Leaching from manure management. Default 'ipcc': IPCC 2019 Table 10.22 on
# every system. 'wfldb': only the systems of WFLDB v3.5, 3.9.5.2 (p. 40),
# "liquid/slurry and solid storage", with the Table 10.22 fractions (WFLDB's
# own FAO 2010 values are not among the sources). 'all_systems' is the old
# name of 'ipcc'.
WFLDB_LEACHING_SYSTEMS = ('liquid_slurry_crust', 'liquid_slurry_no_crust', 'liquid_slurry_cover',
                          'solid_storage', 'solid_storage_covered', 'solid_storage_bulking_agent',
                          'solid_storage_additives')


def leaching_scope(inputs):
    scope = inputs.get('mms_leaching') or 'ipcc'
    return 'ipcc' if scope == 'all_systems' else scope


def manure_leach_fraction(key, system, column, scope='ipcc'):
    if scope == 'wfldb' and key not in WFLDB_LEACHING_SYSTEMS:
        return None
    return ipcc.frac_leach_ms(system.frac, column)


def manure_system_rows(shares):
    """The manure systems other than pasture that have N emissions. Dung
    burned for fuel has none in manure management: IPCC 2019 reports its
    burning under Fuel Combustion (Table 10.21) and gives no FracGas_MS or
    FracLeach_MS for it (Table 10.22, NA); its N leaves with the fuel."""
    for key, share in shares.items():
        if key in ('pasture', BURNED) or not share:
            continue
        yield key, SYSTEMS[key], share


BURNED = 'burned_for_fuel'
BURNED_NOTE = ('dung burned for fuel {share}, {n} kg N: no manure-management N emissions, its '
               'burning is fuel combustion (IPCC 2019, Vol. 4, Ch. 10, Table 10.21; Table 10.22: NA)')


def table39(cat, manure_type, field):
    """A value of EMEP/EEA 2023 3.B, Table 3-9 for the category: the row of
    the manure type, else the category's other row."""
    for t in (manure_type, 'slurry', 'solid'):
        if (cat.emep, t) in emep.TIER2_NH3:
            return emep.tier2_nh3(cat.emep, t, field)
    raise KeyError(f'EMEP/EEA 2023 Table 3-9 has no {field} for {cat.label}')


def frac_gas(system, column, inputs):
    """FracGas_MS of Table 10.22. A digester's digestate storage has only a
    range (0.05-0.50, fn 3): uncovered digestate takes the liquid slurry
    without cover, as fn 3 advises; covered digestate needs its value."""
    if system.key != 'anaerobic_digester':
        return ipcc.frac_gas_ms(system.frac, column)
    if (inputs.get('digester_type') or '') in ipcc.DIGESTER_OPEN_STORAGE:
        f = ipcc.frac_gas_ms('liquid_slurry_no_crust', column)
        return Factor(f.value, f.unit, f.source, f.where,
                      f'{f.note}; uncovered digestate as liquid slurry without cover (fn 3)')
    given = inputs.get('frac_gas_digester')
    low, high = ipcc.FRAC_GAS_DIGESTER_RANGE
    if given is None:
        raise ValueError('anaerobic digester with covered digestate storage: IPCC 2019 Table '
                         f'10.22 gives FracGas_MS only as {low}-{high} (fn 3); give '
                         'frac_gas_digester')
    if not low <= given <= high:
        raise ValueError(f'frac_gas_digester {given} is outside the IPCC 2019 Table 10.22 range '
                         f'{low}-{high} (fn 3)')
    return Factor(given, 'kg N/kg N excreted', GIVEN, 'activity, frac_gas_digester',
                  f'covered digestate; IPCC 2019 Table 10.22 range {low}-{high} (fn 3)')


def tan_share(cat, manure_type):
    """The category's TAN share, EMEP/EEA 2023 3.B, Table 3-9."""
    return table39(cat, manure_type, 'tan_share')


class NitrogenModel(Model):
    """Nitrogen emissions of one animal class on the IPCC route (every
    country outside the EU and Switzerland): IPCC 2019 Refinement, Vol. 4,
    within the boundary of WFLDB v3.5 (manure spreading belongs to the crops,
    section 3.12).

      manure management, per system S (Ch. 10):
        N2O-N = EF3(S) x N(S) (Table 10.21);
        volatilised N = FracGas_MS(S) x N(S) (Table 10.22, NH3 + NOx). IPCC
        gives no split, only that "most of the loss" is NH3 and that the
        EMEP/EEA Guidebook 3.B has the methods (p. 10.89): NOx-N = the
        EMEP/EEA 2023 storage NO factor (Table 3-10, kg NO-N per kg TAN) x
        TAN (Table 3-9 share) x N(S), NH3-N = the rest; daily spread is not
        stored, so all of it is NH3-N;
        leached N = FracLeach_MS(S) x N(S) (Table 10.22, every system; option
        'wfldb': liquid/slurry and solid storage only);
      pasture (Ch. 11): N2O-N = EF3PRP x N (Table 11.1); NH3-N = 0.197 x N
        and NOx-N = 0.015 x N (Annex 11A.8, Table 8A.1; their sum is FracGASM
        0.21, Table 11.3); leached N = FracLEACH x N (Table 11.3, zero in
        dry climates);
      induced N2O-N = EF4 x (NH3-N + NOx-N) + EF5 x leached N (Table 11.3);
      nitrate to ground water = leached N x 62/14.

    Inputs:
      category, nex (kg N/year for the class), shares {system: share},
      moisture: 'wet', 'dry' or None (IPCC 2019 Ch. 11 climate split),
      irrigated: pasture irrigated other than by drip (FracLEACH),
      pasture_in_dataset: the grazing land is occupied by this dataset,
      mms_leaching: 'ipcc' (default) or 'wfldb',
      digester_type, frac_gas_digester: anaerobic digesters
    Outputs (kg/year for the class):
      m_n_n2o_manure_direct, m_n_n2o_pasture_direct, m_n_nh3, m_n_nox,
      m_n_n2o_indirect_volatilisation, m_n_n2o_indirect_leaching,
      m_n_no3_groundwater, m_n_nh3_n, m_n_nox_n, m_n_leached_n
    """

    _input_variables = ('category', 'nex', 'shares', 'moisture', 'irrigated',
                        'pasture_in_dataset')

    def compute(self):
        cat = CATEGORIES[self.category]
        if cat.frac_column is None:
            raise ValueError(f'{cat.label}: IPCC 2019 Table 10.22 has no column for it')
        scope = leaching_scope(self.inputs)
        n2o_mms = nh3_n = nox_n = leach_n = 0.0
        mms_parts, vol_parts, nox_parts, leach_parts = [], [], [], []
        for key, system, share in manure_system_rows(self.shares):
            n = self.nex * share
            ef3 = ipcc.ef3(system.ef3)
            gas = frac_gas(system, cat.frac_column, self.inputs)
            leach = manure_leach_fraction(key, system, cat.frac_column, scope)
            vol = gas.value * n
            if system.emep_type in ('slurry', 'solid') and key != 'dry_lot':
                # Table 3-10 is per kg TAN entering the store (Step 10, Eq. 33-34):
                # the TAN excreted less the housing NH3 loss. A dry lot is an
                # open yard: EMEP/EEA gives yards no NO factor.
                tan = tan_share(cat, system.emep_type)
                ef_h = table39(cat, system.emep_type, 'ef_housing')
                no = emep.STORAGE_NO[system.emep_type]
                no_n = min(no.value * tan.value * (1 - ef_h.value) * n, vol)
                nox_parts.append(f'{SYSTEMS[key].label} {fmt(n)} kg N x TAN {fmt(tan.value)} x (1 - '
                                 f'housing NH3 {fmt(ef_h.value)}) x {fmt(no.value)} kg NO-N/kg TAN '
                                 f'({system.emep_type}) = {fmt(no_n)} kg')
            else:
                no_n = 0.0
            n2o_mms += ef3.value * n
            nox_n += no_n
            nh3_n += vol - no_n
            leach_n += leach.value * n if leach else 0.0
            label = SYSTEMS[key].label
            mms_parts.append(f'{label} {pct(share)}, {fmt(n)} kg N x EF3 {fmt(ef3.value)}')
            vol_parts.append(f'{label} {fmt(n)} kg N x FracGas_MS {fmt(gas.value)}'
                             + (f' ({gas.cite()}, {gas.note})' if gas.source is GIVEN or
                                'fn 3' in gas.note else ''))
            if leach and leach.value:
                leach_parts.append(f'{label} {fmt(n)} kg N x FracLeach_MS {fmt(leach.value)}')
        if self.shares.get(BURNED):
            mms_parts.append(BURNED_NOTE.format(share=pct(self.shares[BURNED]),
                                                n=fmt(self.nex * self.shares[BURNED])))
        frac_where = (f'IPCC 2019, Vol. 4, Ch. 10, Table 10.22, p. 10.97-10.98, '
                      f'{cat.frac_column.replace("_", " ")} column')
        out = {'m_n_n2o_manure_direct': n2o_mms * N_TO_N2O}
        self.note('n2o_manure_direct',
                  f'{fmt(n2o_mms)} kg N2O-N x 44/28 = {fmt(out["m_n_n2o_manure_direct"])} kg N2O '
                  f'from manure management: ' + '; '.join(mms_parts) + f' ({ipcc.EF3_WHERE})')
        mms_nh3_n, mms_nox_n = nh3_n, nox_n

        mms_leach_n = leach_n
        share_p = self.shares.get('pasture') or 0.0
        n2o_prp = prp_nh3_n = prp_nox_n = 0.0
        if share_p and self.pasture_in_dataset:
            n_p = self.nex * share_p
            ef = ef3_prp(self.category, self.moisture)
            n2o_prp = ef.value * n_p
            prp_nh3_n = ipcc.PRP_NH3_N.value * n_p
            prp_nox_n = ipcc.PRP_NOX_N.value * n_p
            nh3_n += prp_nh3_n
            nox_n += prp_nox_n
            fl = frac_leach_pasture(self.moisture, self.irrigated)
            leach_n += fl.value * n_p
            leach_parts.append(f'pasture {fmt(n_p)} kg N x FracLEACH {fmt(fl.value)} '
                               f'({fl.cite()}, {fl.note})')
            self.note('n2o_pasture_direct',
                      f'{fmt(n_p)} kg N on pasture ({pct(share_p)} of {fmt(self.nex)} kg N excreted) '
                      f'x EF3PRP {fmt(ef.value)} ({ef.cite()}, {ef.note}) x 44/28 = '
                      f'{fmt(n2o_prp * N_TO_N2O)} kg N2O. {wfldb.RULE_PASTURE.rstrip(".")}')
        out['m_n_n2o_pasture_direct'] = n2o_prp * N_TO_N2O

        out['m_n_nh3'] = nh3_n * N_TO_NH3
        out['m_n_nox'] = nox_n * N_TO_NO2
        mms_text = ('manure management: ' + '; '.join(vol_parts) + f' (FracGas_MS, NH3 + NOx: '
                    f'{frac_where}), {fmt(mms_nh3_n + mms_nox_n)} kg N, of it NOx-N by the '
                    f'EMEP/EEA 2023 storage NO factor on the TAN (3.B, Table 3-10; TAN share '
                    f'Table 3-9), as IPCC gives no split and refers to EMEP/EEA (p. 10.89)'
                    if vol_parts else '')
        prp_text = (f'pasture: {fmt(self.nex * share_p)} kg N x {ipcc.PRP_NH3_N.value} NH3-N and '
                    f'x {ipcc.PRP_NOX_N.value} NOx-N ({ipcc.PRP_NH3_N.cite()}; their sum is '
                    f'FracGASM 0.21, Table 11.3)' if prp_nh3_n else '')
        self.note('nh3', 'N volatilised, ' + '; '.join(t for t in (mms_text, prp_text) if t) +
                  f': NH3-N {fmt(mms_nh3_n)} kg from manure management + {fmt(prp_nh3_n)} kg '
                  f'from pasture = {fmt(nh3_n)} kg x 17/14 = {fmt(out["m_n_nh3"])} kg NH3')
        self.note('nox', f'NOx-N from manure management {fmt(mms_nox_n)} kg ('
                         + ('; '.join(nox_parts) if nox_parts else 'none stored')
                         + f'; EMEP/EEA 2023, 3.B, Table 3-10 on the TAN entering the store, Step '
                         f'10, p. 24; TAN share and housing NH3 Table 3-9) + from pasture '
                         f'{fmt(prp_nox_n)} kg ({ipcc.PRP_NOX_N.value} x N, {ipcc.PRP_NOX_N.cite()}) '
                         f'= {fmt(nox_n)} kg x 46/14 = {fmt(out["m_n_nox"])} kg NOx as NO2')

        ef4 = ipcc.EF4[self.moisture]
        out['m_n_n2o_indirect_volatilisation'] = ef4.value * (nh3_n + nox_n) * N_TO_N2O
        self.note('n2o_indirect_volatilisation',
                  f'({fmt(nh3_n)} kg NH3-N + {fmt(nox_n)} kg NOx-N) x EF4 {fmt(ef4.value)} '
                  f'({ef4.cite()}, {ef4.note}) x 44/28 = '
                  f'{fmt(out["m_n_n2o_indirect_volatilisation"])} kg N2O')
        out['m_n_n2o_indirect_leaching'] = ipcc.EF5.value * leach_n * N_TO_N2O
        out['m_n_no3_groundwater'] = leach_n * N_TO_NO3
        leach_text = ('; '.join(leach_parts) + f'; FracLeach_MS: {frac_where}') if leach_parts \
            else 'none'
        self.note('n2o_indirect_leaching',
                  f'{fmt(leach_n)} kg N leached ({leach_text}) x EF5 {fmt(ipcc.EF5.value)} '
                  f'({ipcc.EF5.cite()}) x 44/28 = {fmt(out["m_n_n2o_indirect_leaching"])} kg N2O')
        self.note('no3_groundwater', f'{fmt(leach_n)} kg N leached ({leach_text}) x 62/14 = '
                                     f'{fmt(out["m_n_no3_groundwater"])} kg nitrate')
        out.update(m_n_nh3_n=nh3_n, m_n_nox_n=nox_n, m_n_leached_n=leach_n,
                   m_n_mms_leached_n=mms_leach_n)
        return out
