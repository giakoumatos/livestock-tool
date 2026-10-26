from ..tables import emep2023 as emep
from ..tables import ipcc2019 as ipcc
from ..tables import wfldb35 as wfldb
from .atomic_mass import N_TO_N2O, N_TO_NH3, N_TO_NO2, N_TO_NO3
from .base import Model, fmt, pct
from .model_enums import CATEGORIES, SYSTEMS
from .nitrogen_model import ef3_prp, frac_leach_pasture, leaching_scope, \
    manure_leach_fraction, manure_system_rows

# Solid manure kept on straw (EMEP/EEA 2023, 3.B, Step 7: "litter-based" systems).
LITTER_BASED = ('solid_storage', 'solid_storage_covered', 'solid_storage_bulking_agent',
                'solid_storage_additives', 'deep_bedding', 'composting_in_vessel',
                'composting_static_pile', 'composting_intensive_windrow',
                'composting_passive_windrow')


class EmepNitrogenModel(Model):
    """Nitrogen emissions of one animal class on the EU route.

    NH3 and NO: EMEP/EEA 2023, 3.B, Tier 2 mass flow (section 3.4.1, Steps 3
    to 10, 14 and 15, p. 22-26; Steps 11-13, the application to land, belong
    to the crop datasets), on the N excreted from IPCC 2019 (as Step 2 asks):
      Step 3: excreta in buildings, on yards and on pasture; the yard time
        reduces housing and grazing alike (section 3.4.5, p. 32);
      Steps 4-6: TAN, slurry and solid manure, housing and yard NH3
        (Table 3-9); the yard remainder goes to the slurry store, or to the
        solid store where there is no slurry (p. 24);
      Step 7: straw of litter-based solid manure (Table 3-7) and its TAN
        immobilisation;
      Steps 8-10: manure stored or spread directly (daily spread, within its
        own manure type), mineralisation in slurry stores, storage NH3
        (Table 3-9) and NO (Table 3-10);
      Step 14: grazing NH3 (Table 3-9); NO from excreta on pasture by 3.D,
        Table 3-1.
    Emissions after manure application are left out (WFLDB v3.5, 3.12).
    N2O and N leaching: IPCC 2019, as on the WFLDB route; induced N2O is
    taken on the NH3-N and NOx-N of this mass flow, which IPCC 2019 allows
    (Vol. 4, Ch. 10, p. 10.89, citing EMEP/EEA 3.B).

    Inputs:
      category, nex (kg N/year for the class), shares {system: share}, head,
      moisture, irrigated, pasture_in_dataset,
      yard_share: share of the time on yards (default EMEP Step 3)
      housing_days: days in buildings (scales the default straw)
      straw_kg_year: straw per head and year on litter-based solid manure
        (default EMEP Table 3-7, scaled to the housing days)
      daily_spread_type: 'slurry' or 'solid' (default solid)
      mms_leaching: 'ipcc' (default, IPCC 2019 Table 10.22 on every system) or 'wfldb'
    Outputs (kg/year for the class): as NitrogenModel, plus m_n_nh3_hous,
      m_n_nh3_storage, m_n_housed_share, m_n_yard_share
    """

    _input_variables = ('category', 'nex', 'shares', 'moisture', 'irrigated',
                        'pasture_in_dataset', 'head')

    def compute(self):
        cat = CATEGORIES[self.category]
        if cat.emep is None or cat.frac_column is None:
            raise ValueError(f'{cat.label}: EMEP/EEA 2023 Table 3-9 or IPCC 2019 Table 10.22 has no '
                             f'row for it')
        nex, out = self.nex, {}
        if self.shares.get('burned_for_fuel'):
            raise ValueError(f'{cat.label}: dung burned for fuel has no place in the EMEP/EEA 2023 '
                             f'3.B mass flow; give the share it is collected from (e.g. pasture)')

        # Step 3: where the excreta fall.
        share_p = self.shares.get('pasture') or 0.0
        given = self.inputs.get('yard_share')
        default = emep.YARD_SHARE.get(cat.emep)
        x_yard = given if given is not None else (default.value if default else 0.0)
        x_graz, x_hous = share_p * (1 - x_yard), (1 - share_p) * (1 - x_yard)

        # Steps 5 and 8: manure types and the share of each that is stored.
        daily_type = self.inputs.get('daily_spread_type') or 'solid'
        housed = list(manure_system_rows(self.shares))
        housed_total = sum(sh for _, _, sh in housed) or 1.0
        part = {'slurry': 0.0, 'solid': 0.0}
        direct = {'slurry': 0.0, 'solid': 0.0}
        litter = 0.0
        for key, system, sh in housed:
            t = daily_type if system.emep_type == 'direct' else system.emep_type
            part[t] += sh / housed_total
            if system.emep_type == 'direct':
                direct[t] += sh / housed_total
            if key in LITTER_BASED or (system.emep_type == 'direct' and t == 'solid'):
                litter += sh / housed_total
        for t in part:
            if part[t] and (cat.emep, t) not in emep.TIER2_NH3:
                raise ValueError(f'{cat.label}: {pct(part[t])} of the housed manure is {t}, but '
                                 f'EMEP/EEA 2023 Table 3-9 has no {t} row for it')
        rows = [t for t in ('slurry', 'solid') if (cat.emep, t) in emep.TIER2_NH3]

        def ef(t, field):
            return emep.tier2_nh3(cat.emep, t, field).value

        tan_share = ef(rows[0], 'tan_share')
        m_hous_n, m_yard_n, m_graz_n = x_hous * nex, x_yard * nex, x_graz * nex
        m_yard_tan = tan_share * m_yard_n

        # Step 6: the yard emission, once.
        e_yard = 0.0
        if m_yard_tan:
            yard_row = next((t for t in rows if emep.TIER2_NH3[(cat.emep, t)][4] is not None), None)
            if yard_row is None:
                raise ValueError(f'{cat.label}: EMEP/EEA 2023 Table 3-9 gives no yard EF; set '
                                 f'yard_share to 0')
            e_yard = m_yard_tan * ef(yard_row, 'ef_yard')
        yard_to = 'slurry' if part['slurry'] else 'solid' if part['solid'] else None
        parts = [f'{fmt(nex)} kg N excreted: {pct(x_hous)} in buildings, {pct(x_yard)} on yards, '
                 f'{pct(x_graz)} on pasture (Step 3, p. 22; yard time taken from housing and '
                 f'grazing alike, p. 32); TAN {fmt(tan_share)}']
        if e_yard:
            parts.append(f'yards {fmt(m_yard_tan)} kg TAN x EF {ef(yard_row, "ef_yard")}; the rest '
                         + (f'goes to the {yard_to} manure (p. 24)' if yard_to else
                            'is not stored, as the class has no housed manure'))

        e_hous, e_store_nh3, e_store_no = {}, 0.0, 0.0
        for t in ('slurry', 'solid'):
            if not part[t]:
                continue
            n, tan = m_hous_n * part[t], m_hous_n * part[t] * tan_share
            eh = tan * ef(t, 'ef_housing')
            e_hous[t] = eh
            mex_tan, mex_n = tan - eh, n - eh
            text = f'{t}: {fmt(tan)} kg TAN in buildings x housing EF {ef(t, "ef_housing")}'
            if t == 'solid' and litter:
                straw, straw_text = self._straw(cat, litter)
                imm = min(mex_tan * min(1.0, litter / part[t]), straw * emep.F_IMM.value)
                mex_tan -= imm
                mex_n += straw * emep.STRAW_N_CONTENT.value
                text += (f'; straw {fmt(straw)} kg ({straw_text}) immobilises {fmt(imm)} kg TAN '
                         f'(Step 7, Eq. 18)')
            if t == yard_to:
                mex_tan += m_yard_tan - e_yard
                mex_n += m_yard_n - e_yard
            stored = 1 - direct[t] / part[t]
            st_tan, st_n = mex_tan * stored, mex_n * stored
            if t == 'slurry':
                st_tan += (st_n - st_tan) * emep.F_MIN.value
            es = st_tan * ef(t, 'ef_storage')
            e_store_nh3 += es
            e_store_no += st_tan * emep.STORAGE_NO[t].value
            text += (f'; {pct(stored)} stored: {fmt(st_tan)} kg TAN'
                     + (' after 10 % mineralisation' if t == 'slurry' else '')
                     + f' x storage EF {ef(t, "ef_storage")}')
            parts.append(text)

        # Step 14: grazing.
        e_graz = 0.0
        if m_graz_n and self.pasture_in_dataset:
            graz_row = next((t for t in rows + ['outdoor'] if (cat.emep, t) in emep.TIER2_NH3
                             and emep.TIER2_NH3[(cat.emep, t)][7] is not None), None)
            if graz_row is None:
                raise ValueError(f'{cat.label}: EMEP/EEA 2023 Table 3-9 gives no grazing EF')
            e_graz = m_graz_n * tan_share * ef(graz_row, 'ef_grazing')
            parts.append(f'grazing {fmt(m_graz_n * tan_share)} kg TAN x EF '
                         f'{ef(graz_row, "ef_grazing")}')

        nh3_n = sum(e_hous.values()) + e_yard + e_store_nh3 + e_graz
        out['m_n_nh3'] = nh3_n * N_TO_NH3
        out['m_n_nh3_hous'] = sum(e_hous.values()) * N_TO_NH3
        out['m_n_nh3_storage'] = e_store_nh3 * N_TO_NH3
        self.note('nh3', f'EMEP/EEA 2023 Tier 2 mass flow ({emep._T39}; Steps 3-10, 14 and 15, '
                         f'p. 22-26): '
                         + '; '.join(parts) + f'; {fmt(nh3_n)} kg NH3-N x 17/14 = '
                         f'{fmt(out["m_n_nh3"])} kg NH3. Manure application is not included '
                         f'(WFLDB v3.5, section 3.12)')
        no2_graz = emep.SOIL_NO.value * m_graz_n if self.pasture_in_dataset else 0.0
        out['m_n_nox'] = e_store_no * N_TO_NO2 + no2_graz
        nox_n = out['m_n_nox'] / N_TO_NO2
        self.note('nox', f'{fmt(e_store_no)} kg NO-N from storage ({emep._T310}) x 46/14'
                         + (f', plus {fmt(m_graz_n)} kg N on pasture x {emep.SOIL_NO.value} kg NO2/kg N '
                            f'({emep.SOIL_NO.cite()})' if no2_graz else '')
                         + f' = {fmt(out["m_n_nox"])} kg NOx as NO2')

        # IPCC 2019: direct N2O and leaching.
        scope = leaching_scope(self.inputs)
        n2o_mms = leach_n = mms_leach = 0.0
        receiving = [(k, sh) for k, sys_, sh in housed if sys_.emep_type == yard_to] or \
            [(k, sh) for k, sys_, sh in housed
             if sys_.emep_type == 'direct' and daily_type == yard_to]
        receiving_total = sum(sh for _, sh in receiving)
        for key, system, share in housed:
            n = nex * share * (1 - x_yard)
            if receiving_total and key in dict(receiving):
                n += m_yard_n * dict(receiving)[key] / receiving_total
            n2o_mms += ipcc.ef3(system.ef3).value * n
            f = manure_leach_fraction(key, system, cat.frac_column, scope)
            mms_leach += (f.value if f else 0.0) * n
        leach_n = mms_leach
        out['m_n_n2o_manure_direct'] = n2o_mms * N_TO_N2O
        self.note('n2o_manure_direct', f'{fmt(n2o_mms)} kg N2O-N by IPCC 2019 EF3 per system on the '
                                       f'N excreted in buildings and, for the store the yard manure '
                                       f'goes to, on yards ({ipcc.EF3_WHERE}) x 44/28 = '
                                       f'{fmt(out["m_n_n2o_manure_direct"])} kg N2O')
        n2o_prp = 0.0
        n_prp = m_graz_n
        if n_prp and self.pasture_in_dataset:
            e = ef3_prp(self.category, self.moisture)
            n2o_prp = e.value * n_prp
            fl = frac_leach_pasture(self.moisture, self.irrigated)
            leach_n += fl.value * n_prp
            self.note('n2o_pasture_direct', f'{fmt(n_prp)} kg N on pasture (the pasture share less '
                                            f'its yard time, Step 3) x EF3PRP {fmt(e.value)} '
                                            f'({e.cite()}) x 44/28 = {fmt(n2o_prp * N_TO_N2O)} kg '
                                            f'N2O. {wfldb.RULE_PASTURE.rstrip(".")}')
        out['m_n_n2o_pasture_direct'] = n2o_prp * N_TO_N2O
        ef4 = ipcc.EF4[self.moisture]
        out['m_n_n2o_indirect_volatilisation'] = ef4.value * (nh3_n + nox_n) * N_TO_N2O
        self.note('n2o_indirect_volatilisation',
                  f'({fmt(nh3_n)} kg NH3-N + {fmt(nox_n)} kg NOx-N of the EMEP/EEA mass flow) x EF4 '
                  f'{fmt(ef4.value)} ({ef4.cite()}; mass-flow N allowed by IPCC 2019, Vol. 4, Ch. 10, '
                  f'p. 10.89) x 44/28 = {fmt(out["m_n_n2o_indirect_volatilisation"])} kg N2O')
        out['m_n_n2o_indirect_leaching'] = ipcc.EF5.value * leach_n * N_TO_N2O
        out['m_n_no3_groundwater'] = leach_n * N_TO_NO3
        self.note('n2o_indirect_leaching', f'{fmt(leach_n)} kg N leached (manure management '
                                           f'{fmt(mms_leach)}, pasture {fmt(leach_n - mms_leach)}) x '
                                           f'EF5 {ipcc.EF5.value} ({ipcc.EF5.cite()}) x 44/28 = '
                                           f'{fmt(out["m_n_n2o_indirect_leaching"])} kg N2O')
        self.note('no3_groundwater', f'{fmt(leach_n)} kg N leached x 62/14 = '
                                     f'{fmt(out["m_n_no3_groundwater"])} kg nitrate')
        out.update(m_n_nh3_n=nh3_n, m_n_nox_n=nox_n, m_n_leached_n=leach_n,
                   m_n_mms_leached_n=mms_leach, m_n_housed_share=x_hous, m_n_yard_share=x_yard)
        return out

    def _straw(self, cat, litter):
        """Bedding straw of the class in the year and the words for it. A
        given straw_kg_year is the straw the class uses, per head; the Table
        3-7 default is per head kept on litter, so it is scaled to the
        litter-based share of the housed manure and to the housing days."""
        given = self.inputs.get('straw_kg_year')
        if given is not None:
            return given * self.head, f'{fmt(given)} kg per head, given'
        days_default, straw_default = emep.STRAW.get(cat.emep, (None, 0.0))
        if not straw_default:
            return 0.0, 'no default in Table 3-7'
        days = self.inputs.get('housing_days')
        if days is None:
            days = 365 * (1 - (self.shares.get('pasture') or 0.0))
        straw = straw_default * days / days_default * self.head * litter
        return straw, (f'Table 3-7: {fmt(straw_default)} kg per head and {fmt(days_default)} days, x '
                       f'{fmt(days)} housing days, x {pct(litter)} of the housed manure on litter')
