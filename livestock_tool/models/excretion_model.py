from ..tables import ipcc2019 as ipcc
from .base import Model, fmt, pct
from .model_enums import CATEGORIES


class ExcretionModel(Model):
    """Volatile solids and nitrogen excreted by one animal class.

    Tier 2 (an intake is known):
      VS: IPCC 2019 Eq. 10.24 (Vol. 4, Ch. 10, p. 10.65),
          VS = [GE x (1 - DE/100) + UE x GE] x (1 - ASH) / 18.45.
      N intake: Eq. 10.32 (cattle, sheep, goats: GE/18.45 x CP/100 / 6.25) or
          Eq. 10.32A (swine, poultry: DMI x CP/100 / 6.25), p. 10.82.
      N excreted: Eq. 10.31A, option 2 (p. 10.81), N intake - N retained,
          where the retention data are given: cattle in milk and growth
          (Eq. 10.33, p. 10.85), sows (Eq. 10.33A-B), growing pigs (Eq.
          10.33C, Table 10.20B), laying hens (Eq. 10.33D), broilers and
          pullets (Eq. 10.33E); otherwise option 1 (Eq. 10.31), N intake x
          (1 - retained fraction, Table 10.20).
    Tier 1 (no intake, m_energy_tier 'tier1'): VS = Table 10.13A rate x
      weight / 1000 (Eq. 10.22A); Nex = Table 10.19 rate x weight / 1000 x
      365 (Eq. 10.30).
    A Nex given in the data collection replaces the calculation.

    Inputs:
      category, head, ge (MJ/(head*day)), dmi (kg DM/(head*day)), de_pct,
      cp_pct (% of DM), ash_frac (fraction of DM intake), ue_frac (fraction
      of GE), nex_kg_year (given, kg N/(head*year), or None), nex_source;
      tier ('tier1' or other), ipcc_region, weight_kg (Tier 1);
      cattle: milk_kg_day, milk_fat_pct, weight_gain_kg_day, neg (MJ/d);
      sows: litter_size, farrowings_per_year, piglet_birth_kg,
        piglet_weaning_kg, sow_weight_change_kg;
      growing pigs, broilers: weight_start_kg, weight_end_kg, production_days;
      laying hens: egg_g_day, weight_gain_kg_day
    Outputs:
      m_excretion_vs: kg VS/(head*day)
      m_excretion_nex: kg N/year for the class
      m_excretion_n_intake: kg N/year for the class (None on Tier 1)
    """

    _input_variables = ('category', 'head', 'ge', 'dmi', 'de_pct', 'cp_pct', 'ash_frac',
                        'ue_frac')

    def compute(self):
        if self.inputs.get('tier') == 'tier1':
            return self._tier1()
        cat = CATEGORIES[self.category]
        for name in ('de_pct', 'cp_pct', 'ash_frac'):
            if getattr(self, name) is None:
                raise ValueError(f'{name} is needed for volatile solids and N excretion '
                                 '(IPCC 2019, Vol. 4, Ch. 10, Eq. 10.24 and 10.32)')
        vs = (self.ge * (1 - self.de_pct / 100) + self.ue_frac * self.ge) * \
            (1 - self.ash_frac) / ipcc.GE_PER_KG_DM.value
        self.note('vs', f'volatile solids {fmt(vs)} kg per head and day = [GE {fmt(self.ge)} x '
                        f'(1 - {fmt(self.de_pct)} %) + UE {fmt(self.ue_frac)} x GE] x (1 - ash '
                        f'{fmt(self.ash_frac)}) / 18.45 ({ipcc.EQ_VS})')
        if cat.n_intake_eq == '10.32':
            n_in = self.ge / ipcc.GE_PER_KG_DM.value * self.cp_pct / 100 / 6.25
            eq = ipcc.EQ_N_INTAKE
        else:
            n_in = self.dmi * self.cp_pct / 100 / 6.25
            eq = 'IPCC 2019, Vol. 4, Ch. 10, Eq. 10.32A, p. 10.82' + (
                ', given for swine and poultry, used here by analogy' if cat.key == 'horses' else '')
        n_in_text = (f'N intake {fmt(n_in)} kg per head and day = dry matter intake '
                     f'{fmt(self.dmi)} kg x crude protein {fmt(self.cp_pct)} % / 6.25 ({eq})')
        given = self.inputs.get('nex_kg_year')
        retained = None if given is not None or cat.n_retention is None else self._retention()
        if given is not None:
            nex_head = given
            text = (f'N excreted {fmt(given)} kg per head and year, given '
                    f'({self.inputs.get("nex_source") or "data collection"})')
        elif retained is not None:
            ret_day, ret_text = retained
            nex_head = (n_in - ret_day) * 365
            text = (f'{n_in_text}; N retained {fmt(ret_day)} kg per head and day ({ret_text}); N '
                    f'excreted {fmt(nex_head)} kg per head and year = (N intake - N retained) x 365 '
                    f'({ipcc.EQ_NEX_OPTION2})')
        elif cat.n_retention:
            ret = ipcc.n_retention_frac(cat.n_retention)
            nex_head = n_in * (1 - ret.value) * 365
            text = (f'{n_in_text}; N excreted {fmt(nex_head)} kg per head and year = N intake x '
                    f'(1 - {pct(ret.value)} retained, {ret.cite()}) x 365 ({ipcc.EQ_NEX})')
        else:
            nex_head = self._cattle_nex(n_in, n_in_text)
            text = self.trace.pop('_nex')[0]
        if nex_head <= 0:
            raise ValueError(f'N excreted comes out at {fmt(nex_head)} kg per head and year: the N '
                             f'retained is larger than the N intake; check the intake, crude protein '
                             f'and production data')
        nex = nex_head * self.head
        self.note('nex', f'{text}; x {fmt(self.head)} head = {fmt(nex)} kg N')
        return {'m_excretion_vs': vs, 'm_excretion_nex': nex,
                'm_excretion_n_intake': n_in * 365 * self.head}

    def _tier1(self):
        inp = self.inputs
        region, w = inp.get('ipcc_region'), inp.get('weight_kg')
        if region is None or w is None:
            raise ValueError('Tier 1 (no intake data): give ipcc_region and weight_kg, the typical '
                             'animal mass (IPCC 2019 Eq. 10.22A and 10.30)')
        vr = ipcc.vs_rate(self.category, region)
        vs = vr.value * w / 1000
        self.note('vs', f'volatile solids {fmt(vs)} kg per head and day = {fmt(vr.value)} kg VS per '
                        f'1000 kg animal mass and day ({vr.cite()}, {vr.note}) x {fmt(w)} kg / 1000 '
                        f'(IPCC 2019 Tier 1, {ipcc.EQ_VS_TIER1})')
        given = inp.get('nex_kg_year')
        if given is not None:
            nex_head = given
            text = (f'N excreted {fmt(given)} kg per head and year, given '
                    f'({inp.get("nex_source") or "data collection"})')
        else:
            nr = ipcc.n_rate(self.category, region)
            nex_head = nr.value * w / 1000 * 365
            text = (f'N excreted {fmt(nex_head)} kg per head and year = {fmt(nr.value)} kg N per '
                    f'1000 kg animal mass and day ({nr.cite()}, {nr.note}) x {fmt(w)} kg / 1000 x 365 '
                    f'(IPCC 2019 Tier 1, {ipcc.EQ_NEX_TIER1})')
        nex = nex_head * self.head
        self.note('nex', f'{text}; x {fmt(self.head)} head = {fmt(nex)} kg N')
        return {'m_excretion_vs': vs, 'm_excretion_nex': nex, 'm_excretion_n_intake': None}

    def _retention(self):
        """N retained per head and day by option 2 for pigs and poultry, or
        None when the class has not the data for it."""
        inp, key = self.inputs, self.category
        need = {'swine_sows': ('litter_size', 'farrowings_per_year', 'piglet_birth_kg',
                               'piglet_weaning_kg', 'sow_weight_change_kg'),
                'swine_finishing': ('weight_start_kg', 'weight_end_kg', 'production_days'),
                'broilers': ('weight_start_kg', 'weight_end_kg', 'production_days'),
                'laying_hens': ('egg_g_day',)}.get(key)
        if need is None or any(inp.get(f) is None for f in need):
            return None
        if key == 'swine_sows':
            ls, fr = inp['litter_size'], inp['farrowings_per_year']
            ckg, wkg = inp['piglet_birth_kg'], inp['piglet_weaning_kg']
            skg = inp['sow_weight_change_kg'] + ls * ckg / ipcc.N_RET_PIGLET_BIRTH_CORR
            n_gain = ipcc.N_RET_PIG_BW * fr * skg
            n_piglets = ipcc.N_RET_PIG_BW * ls * fr * (wkg - ckg) / ipcc.N_RET_PROTEIN_DIGEST
            year = n_gain + n_piglets
            return year / 365, (
                f'{fmt(year)} kg N a year = sow 0.025 x {fmt(fr)} farrowings x Skg {fmt(skg)} kg '
                f'(sow weight change {fmt(inp["sow_weight_change_kg"])} kg + {fmt(ls)} piglets x '
                f'{fmt(ckg)} kg / 0.806) + weaned piglets 0.025 x {fmt(ls)} x {fmt(fr)} x '
                f'({fmt(wkg)} - {fmt(ckg)} kg) / 0.98, / 365 ({ipcc.EQ_N_RET_SOWS})')
        bwi, bwf, days = inp.get('weight_start_kg'), inp.get('weight_end_kg'), \
            inp.get('production_days')
        if key == 'swine_finishing':
            lo, hi = ipcc.N_GAIN_PIG_PHASES[0][0], ipcc.N_GAIN_PIG_PHASES[-1][1]
            if not lo <= bwi < bwf <= hi:
                raise ValueError(f'growing pigs from {fmt(bwi)} to {fmt(bwf)} kg: IPCC 2019 Table '
                                 f'10.20B covers {lo}-{hi} kg')
            total, parts = 0.0, []
            for start, end, n_gain in ipcc.N_GAIN_PIG_PHASES:
                gain = max(0.0, min(bwf, end) - max(bwi, start))
                if gain:
                    total += gain * n_gain
                    parts.append(f'{fmt(gain)} kg x {n_gain} ({start}-{end} kg)')
            return total / days, (f'{fmt(total)} kg N per pig = ' + ' + '.join(parts) +
                                  f', over {fmt(days)} days ({ipcc.EQ_N_RET_PIGS})')
        if key == 'broilers':
            total = (bwf - bwi) * ipcc.N_GAIN_BROILERS
            return total / days, (f'({fmt(bwf)} - {fmt(bwi)} kg) x {ipcc.N_GAIN_BROILERS} kg N/kg / '
                                  f'{fmt(days)} days ({ipcc.EQ_N_RET_BROILERS})')
        wg = inp.get('weight_gain_kg_day') or 0.0
        ret = ipcc.N_LW_HENS * wg + ipcc.N_EGG * inp['egg_g_day'] / 1000
        return ret, (f'{ipcc.N_LW_HENS} x weight gain {fmt(wg)} kg/d + {ipcc.N_EGG} x '
                     f'{fmt(inp["egg_g_day"])} g egg/d / 1000 ({ipcc.EQ_N_RET_HENS})')

    def _cattle_nex(self, n_in, n_in_text):
        inp = self.inputs
        milk = inp.get('milk_kg_day') or 0.0
        wg = inp.get('weight_gain_kg_day') or 0.0
        n_milk = milk * (1.9 + 0.4 * (inp.get('milk_fat_pct') or 4.0)) / 100 / 6.38 if milk else 0.0
        n_growth = wg * (268 - 7.03 * inp['neg'] / wg) / 1000 / 6.25 if wg else 0.0
        nex = (n_in - n_milk - n_growth) * 365
        self.note('_nex', f'{n_in_text}; N retained {fmt(n_milk + n_growth)} kg per head and day '
                          f'in milk and growth (IPCC 2019, Vol. 4, Ch. 10, Eq. 10.33, p. 10.85); '
                          f'N excreted {fmt(nex)} kg per head and year (Eq. 10.31A, p. 10.81)')
        return nex
