from ..tables import ipcc2019 as ipcc
from ..tables import salca as s
from .atomic_mass import CH4_KG_PER_M3, CH4_MJ_PER_KG, N_TO_N2O, N_TO_NH3, N_TO_NO2, N_TO_NO3
from .base import Model, fmt, pct

_GROUPS = {'dairy_cattle': 'dairy', 'other_cattle': 'other_cattle',
           'swine_finishing': 'fattening_pigs', 'swine_sows': 'sows', 'sheep': 'sheep',
           'goats': 'goats', 'horses': 'horses', 'laying_hens': 'laying_hens',
           'broilers': 'broilers'}
_W = f'{s.SALCA.short}, {s.A6}'


def salca_group(category, tied_housing=False):
    group = _GROUPS.get(category)
    if group is None:
        raise ValueError(f'SALCA has no animal group for {category}')
    return 'dairy_tied' if group == 'dairy' and tied_housing else group


class SalcaModel(Model):
    """Emissions of one animal class in Switzerland by SALCAanimal V1.0, as
    documented in Appendix 6 of Nemecek et al. (2024). SALCA takes the feed
    ration from the user and has no feed requirement model.

    Inputs (class totals per year unless said):
      category, head, dmi (kg DM/(head*day)), ge_mj_per_kg_dm (default IPCC
      18.45), de_pct, cp_pct (% DM), ash_frac (of DM intake), ndf_pct
      (dairy cows at DE >= 70 %), tied_housing (dairy),
      pasture_days_spring/_summer/_autumn/_winter or pasture_days, pasture_hours,
      yard_days, yard_hours, grazing_n_ratio (N content of grazed feed /
      ration mean, cattle, default 1), liquid_n_share (share of housing N in
      liquid manure), straw_kg_year (per head),
      lw_purchased_kg_year_class, lw_sold_kg_year_class, lw_gain_kg_year_class,
      milk_kg_year_class, wool_kg_year (per head), eggs_kg_year_class,
      nh3_option ('EEA' or 'Agrammon'), liquid_crust_share, liquid_pit_share,
      liquid_digester_share, solid_compost_share, solid_deep_bedding_share,
      pasture_in_dataset (the excreta on pasture count here)
    Outputs (kg/year for the class): as NitrogenModel, plus m_n_ch4_enteric,
      m_n_ch4_manure, m_n_housed_share
    """

    _input_variables = ('category', 'head', 'dmi', 'de_pct', 'cp_pct', 'ash_frac')

    def compute(self):
        inp = self.inputs
        g = salca_group(self.category, bool(inp.get('tied_housing')))
        option = inp.get('nh3_option')
        if option not in s.NH3:
            raise ValueError('SALCA needs nh3_option: EEA or Agrammon (Appendix 6, section 6.1)')
        head = self.head
        dm = self.dmi * 365 * head
        ge_content = inp.get('ge_mj_per_kg_dm') or ipcc.GE_PER_KG_DM.value
        ge = dm * ge_content
        n_feed = dm * self.cp_pct / 100 / 6.25
        n_pct = n_feed / dm * 100
        out = {}

        # Methane (section 4).
        y = s.ym(g, self.de_pct, inp.get('ndf_pct'))
        out['m_n_ch4_enteric'] = ge * y.value / 100 / CH4_MJ_PER_KG
        self.note('ch4_enteric', f'feed {fmt(dm)} kg DM a year ({fmt(self.dmi)} kg per head and day '
                                 f'x {fmt(head)} head) x {fmt(ge_content)} MJ/kg = {fmt(ge)} MJ; x Ym '
                                 f'{fmt(y.value)} % ({y.cite()}) / 55.65 MJ/kg ({_W}, Eq. 1) = '
                                 f'{fmt(out["m_n_ch4_enteric"])} kg CH4')
        b0, ue = s.B0_UE[g]
        vs = ge * (1 - self.de_pct / 100 + ue) * (1 - self.ash_frac) / 18.45
        fp, fy = self._time_fractions()
        fh = max(0.0, 1 - fp - fy)
        f_liq = inp.get('liquid_n_share') or 0.0
        family = s.n2o_family(g)
        if f_liq and (family, 'liquid') not in s.N2O:
            raise ValueError(f'SALCA {g}: Appendix 6 Tab. 7-9 give solid manure only for sheep, goats '
                             f'and horses; set liquid_n_share to 0')
        on_pasture = inp.get('pasture_in_dataset', True)
        corr_os = s.CORR_OS.get('cattle' if family == 'cattle' else 'pigs' if family == 'pigs'
                                else None)
        # Eq. 9 splits the organic matter between slurry and solid manure; a
        # herd with slurry only has no solid manure, so all of it is slurry.
        if f_liq >= 1:
            os_liq = fh
        else:
            os_liq = fh * f_liq * corr_os if corr_os else 0.0
        os_sol = fh - os_liq
        deep = os_sol * (inp.get('solid_deep_bedding_share') or 0.0)
        compost = (os_sol - deep) * (inp.get('solid_compost_share') or 0.0)
        rest = os_sol - deep - compost
        digester = os_liq * (inp.get('liquid_digester_share') or 0.0)
        ms = {'pasture_drylot': (fp if on_pasture else 0.0) + fy, 'pit_storage': os_liq - digester,
              'anaerobic_digester': digester, 'deep_bedding': deep, 'composting': compost,
              'poultry_manure' if family == 'poultry' else 'solid_storage': rest}
        mcf_sum = sum(s.MCF[k] * v for k, v in ms.items())
        out['m_n_ch4_manure'] = vs * b0 * CH4_KG_PER_M3 * mcf_sum
        self.note('ch4_manure', f'VS {fmt(vs)} kg a year = GE {fmt(ge)} MJ x (1 - DE '
                                f'{fmt(self.de_pct)} % + UE {ue}) x (1 - ash {fmt(self.ash_frac)}) / '
                                f'18.45 ({_W}, Eq. 4, UE Tab. 2); x B0 {b0} (Tab. 2) x 0.67 x MCF '
                                f'(Tab. 3: ' + ', '.join(f'{k.replace("_", " ")} {pct(v)} at '
                                                         f'{s.MCF[k]}' for k, v in ms.items() if v)
                  + f') = {fmt(out["m_n_ch4_manure"])} kg CH4')

        # N balance and excretion (section 5).
        body_n = s.BODY_N_G_PER_KG[g] / 1000
        lw_in = inp.get('lw_purchased_kg_year_class') or 0.0
        lw_out = (inp.get('lw_sold_kg_year_class') or 0.0) + (inp.get('lw_gain_kg_year_class') or 0.0)
        milk_key = {'dairy': 'cow_milk_kg', 'dairy_tied': 'cow_milk_kg', 'sheep': 'sheep_milk_kg',
                    'goats': 'goat_milk_kg', 'horses': 'horse_milk_kg'}.get(g)
        n_products = ((inp.get('milk_kg_year_class') or 0.0) * s.PRODUCT_N.get(milk_key, 0.0)
                      + (inp.get('wool_kg_year') or 0.0) * head * s.PRODUCT_N['sheep_wool_kg']
                      + (inp.get('eggs_kg_year_class') or 0.0) * s.PRODUCT_N['eggs_kg'])
        n_ex = n_feed + lw_in * body_n - lw_out * body_n - n_products
        self.note('nex', f'N excreted {fmt(n_ex)} kg a year = feed N {fmt(n_feed)} kg ({fmt(dm)} kg '
                         f'DM x crude protein {fmt(self.cp_pct)} % / 6.25) + bought animals '
                         f'{fmt(lw_in * body_n)} - sold and grown animals {fmt(lw_out * body_n)} '
                         f'({fmt(s.BODY_N_G_PER_KG[g])} g N/kg live weight, Tab. 5) - products '
                         f'{fmt(n_products)} kg N (Tab. 4, per kg; its "m3" for milk is a misprint) '
                         f'({_W}, Eq. 6); {pct(fp)} on pasture, '
                         f'{pct(fy)} on yards, {pct(fh)} in housing (Eq. 7)')

        cattle = family == 'cattle'
        ratio = inp.get('grazing_n_ratio') or 1.0 if cattle else 1.0
        if cattle:
            rel_hy = (1 - fp * ratio) / (1 - fp) if fp < 1 else 0.0
            u_year, u_past, u_hy = (self._urine(n_pct), self._urine(n_pct * ratio),
                                    self._urine(n_pct * rel_hy))
            tan = u_year + s.DUNG_TAN * (1 - u_year)
            tan_text = (f'TAN {pct(tan)} = urine N {pct(u_year)} (Eq. 8, at {fmt(n_pct)} % N in '
                        f'the ration DM) + 0.2 x dung N (Eq. 10)')
        else:
            rel_hy, u_past, u_hy = 1.0, None, None
            tan = self._ef(g, option, 'liquid' if f_liq else 'solid', 'tan')
            tan_text = f'TAN {pct(tan)} ({s.NH3_WHERE[option]})'
        n_past, n_yard = n_ex * fp * ratio, n_ex * fy * rel_hy
        n_house = n_ex * fh * rel_hy
        n_hl, n_hs = n_house * f_liq, n_house * (1 - f_liq)

        # Housing NH3 (section 6.1), with Agrammon's factor on grazing days.
        corr, corr_text = 1.0, ''
        if option == 'Agrammon' and fp:
            hours = inp.get('pasture_hours') or 0.0
            factor = s.agrammon_housing_factor(hours)
            corr = (factor - 1) * self._pasture_days() / 365 + 1
            corr_text = (f', x {fmt(corr)} for housing emissions on grazing days ({fmt(hours)} h on '
                         f'pasture: {pct(factor)}, section 6.1)')
        nh3_hl = n_hl * tan * self._ef(g, option, 'liquid', 'housing') * corr if n_hl else 0.0
        nh3_hs = n_hs * tan * self._ef(g, option, 'solid', 'housing') * corr if n_hs else 0.0

        # Yard (section 6).
        nh3_y = n_yard * tan * self._ef(g, option, 'liquid' if f_liq else 'solid', 'yard') \
            if n_yard else 0.0
        nox_y = n_yard * s.NOX_GRAZING.value
        ef_gr = self._n2o_grazing(g, family, u_hy)
        n2o_y = n_yard * ef_gr
        dep_y = max(0.0, n_yard - nh3_y - nox_y - n2o_y)
        tan_y = max(0.0, n_yard * tan - nh3_y - nox_y - n2o_y)

        # Storage (section 6.1-6.5).
        straw = (inp.get('straw_kg_year') or 0.0) * head
        straw_n = straw * s.STRAW_N.value
        n_sl = n_hl - nh3_hl + dep_y * f_liq + (straw_n if f_liq == 1 else 0.0)
        n_ss = n_hs - nh3_hs + dep_y * (1 - f_liq) + (straw_n if f_liq < 1 else 0.0)
        tan_sl = max(0.0, n_hl * tan - nh3_hl + tan_y * f_liq)
        tan_ss = max(0.0, n_hs * tan - nh3_hs + tan_y * (1 - f_liq))
        tan_sl += (n_sl - tan_sl) * s.MINERALISATION_LIQUID
        imm = min(tan_ss, s.IMMOBILISATION['EEA'] * straw if option == 'EEA'
                  else s.IMMOBILISATION['Agrammon'] * tan_ss)
        tan_ss -= imm
        nh3_sl = tan_sl * self._ef(g, option, 'liquid', 'storage') if tan_sl else 0.0
        nh3_ss = tan_ss * self._ef(g, option, 'solid', 'storage') if tan_ss else 0.0
        nox_s = tan_sl * s.NOX_STORAGE['liquid'] + tan_ss * s.NOX_STORAGE['solid']
        # Crust and pit are columns of Tab. 9 for cattle and pig slurry only.
        crust, pit = ((inp.get('liquid_crust_share') or 0.0, inp.get('liquid_pit_share') or 0.0)
                      if family in ('cattle', 'pigs') else (0.0, 0.0))
        n2o_s = 0.0
        if tan_sl:
            no_crust, with_crust, pit_ef, _ = s.N2O[(family, 'liquid')]
            n2o_s += tan_sl * (crust * with_crust + pit * pit_ef + (1 - crust - pit) * no_crust)
        if tan_ss:
            n2o_s += tan_ss * s.N2O[(family, 'solid')][0]

        # Pasture (section 6.6).
        nh3_p = nox_p = n2o_p = no3_p = 0.0
        if n_past and on_pasture:
            nox_p = n_past * s.NOX_GRAZING.value
            if cattle:
                w = self._season_weights()
                nh3_p = n_past * u_past * sum(wi * v for wi, v in zip(w, s.PASTURE['nh3_urine']))
                n2o_p = n_past * self._n2o_grazing_split(u_past)
                dep = max(0.0, n_past - nh3_p - nox_p - n2o_p)
                no3_p = dep * (u_past * sum(wi * v for wi, v in zip(w, s.PASTURE['no3_urine']))
                               + (1 - u_past) * sum(wi * v for wi, v in zip(w, s.PASTURE['no3_dung'])))
            else:
                nh3_p = n_past * tan * self._ef(g, option, 'solid', 'grazing')
                n2o_p = n_past * s.N2O[(family, 'solid')][3]
                if family == 'pigs':
                    # "50% of excreted TAN" (section 6.6).
                    no3_p = n_past * tan * s.NO3_PIGS_OF_TAN.value
                else:
                    # "the mean values from Tab. 10": urine mean on the TAN, dung
                    # mean on the rest, both after the losses on pasture.
                    dep_tan = max(0.0, n_past * tan - nh3_p - nox_p - n2o_p)
                    dep_org = max(0.0, n_past * (1 - tan))
                    no3_p = dep_tan * s.PASTURE['no3_urine'][4] + dep_org * s.PASTURE['no3_dung'][4]

        nh3_n = nh3_hl + nh3_hs + nh3_y + nh3_sl + nh3_ss + nh3_p
        nox_n = nox_y + nox_s + nox_p
        out.update(
            m_n_nh3=nh3_n * N_TO_NH3, m_n_nox=nox_n * N_TO_NO2,
            m_n_n2o_manure_direct=(n2o_s + n2o_y) * N_TO_N2O, m_n_n2o_pasture_direct=n2o_p * N_TO_N2O,
            m_n_n2o_indirect_volatilisation=s.EF4.value * (nh3_n + nox_n) * N_TO_N2O,
            m_n_n2o_indirect_leaching=s.EF5.value * no3_p * N_TO_N2O,
            m_n_no3_groundwater=no3_p * N_TO_NO3, m_n_housed_share=fh,
            m_n_pasture_share=fp if on_pasture else 0.0)
        nh3_where = f'{_W}, {s.NH3_WHERE[option]}'
        self.note('nh3', f'{tan_text}; housing: {fmt(n_house)} kg N ({pct(f_liq)} liquid) x TAN x EF '
                         f'= {fmt(nh3_hl + nh3_hs)} kg NH3-N{corr_text}; yard {fmt(nh3_y)}; storage '
                         f'{fmt(nh3_sl + nh3_ss)} kg NH3-N (liquid TAN {fmt(tan_sl)} kg after 10 % '
                         f'mineralisation, solid TAN {fmt(tan_ss)} kg after {fmt(imm)} kg immobilised, '
                         f'section 6.5); pasture {fmt(nh3_p)} kg NH3-N'
                         + (' (cattle: urine N x Tab. 10, by season)' if cattle else '')
                         + f' ({nh3_where}); total {fmt(nh3_n)} kg NH3-N x 17/14 = '
                           f'{fmt(out["m_n_nh3"])} kg NH3. Manure spreading is calculated in '
                           f'SALCAfield, not here')
        self.note('nox', f'yard and pasture {fmt(n_yard + n_past)} kg N x {s.NOX_GRAZING.value} '
                         f'({s.NOX_GRAZING.cite()}), storage TAN x {fmt(s.NOX_STORAGE["liquid"])} '
                         f'(liquid) and {fmt(s.NOX_STORAGE["solid"])} (solid) kg NOx-N per kg '
                         f'({_W}, section 6.4): {fmt(nox_n)} kg NOx-N x 46/14 = '
                         f'{fmt(out["m_n_nox"])} kg NOx as NO2')
        self.note('n2o_manure_direct', f'storage {fmt(n2o_s)} kg N2O-N on TAN entering the store '
                                       f'(liquid: {pct(crust)} with crust, {pct(pit)} pit, rest '
                                       f'without crust; {_W}, Tab. 9) and yard {fmt(n2o_y)} kg; x '
                                       f'44/28 = {fmt(out["m_n_n2o_manure_direct"])} kg N2O')
        self.note('n2o_pasture_direct', f'{fmt(n_past)} kg N on pasture x '
                                        + ('urine 1 % / dung 0.25 %' if cattle else
                                           f'{s.N2O[(family, "solid")][3]}')
                                        + f' ({_W}, Tab. 9) x 44/28 = '
                                          f'{fmt(out["m_n_n2o_pasture_direct"])} kg N2O')
        self.note('n2o_indirect_volatilisation',
                  f'({fmt(nh3_n)} kg NH3-N + {fmt(nox_n)} kg NOx-N) x {s.EF4.value} '
                  f'({s.EF4.cite()}) x 44/28 = {fmt(out["m_n_n2o_indirect_volatilisation"])} kg N2O')
        self.note('n2o_indirect_leaching', f'{fmt(no3_p)} kg NO3-N from pasture x {s.EF5.value} '
                                           f'({s.EF5.cite()}) x 44/28 = '
                                           f'{fmt(out["m_n_n2o_indirect_leaching"])} kg N2O')
        no3_rule = ('cattle: deposited N x Tab. 10 by season and urine share' if cattle else
                    'pigs: 50 % of the TAN excreted on pasture' if family == 'pigs' else
                    'Tab. 10 means: urine 20.5 % of the TAN, dung 3.7 % of the rest, after the '
                    'losses on pasture')
        self.note('no3_groundwater', f'{fmt(no3_p)} kg NO3-N leached from pasture ({no3_rule}; '
                                     f'{_W}, section 6.6) x 62/14 = '
                                     f'{fmt(out["m_n_no3_groundwater"])} kg nitrate')
        return out

    def _ef(self, group, option, manure, field):
        row = s.NH3[option].get((group, manure)) or s.NH3[option].get((group, 'solid'))
        value = row[s.NH3_FIELDS.index(field)]
        if value is None:
            raise ValueError(f'SALCA {s.NH3_WHERE[option]} has no {field} value for {group}')
        return value

    def _pasture_days(self):
        seasons = [self.inputs.get(f'pasture_days_{x}') for x in s.SEASONS]
        if any(v is not None for v in seasons):
            return sum(v or 0.0 for v in seasons)
        return self.inputs.get('pasture_days') or 0.0

    def _season_weights(self):
        days = [self.inputs.get(f'pasture_days_{x}') or 0.0 for x in s.SEASONS]
        total = sum(days)
        if not total:
            raise ValueError('SALCA grazing cattle: give the pasture days per season (Tab. 10)')
        return [d / total for d in days]

    def _time_fractions(self):
        inp = self.inputs
        if self._pasture_days() and inp.get('pasture_hours') is None:
            raise ValueError('SALCA: pasture days are given but no pasture_hours (Eq. 7 needs the '
                             'hours on pasture per grazing day)')
        if (inp.get('yard_days') or 0) and inp.get('yard_hours') is None:
            raise ValueError('SALCA: yard days are given but no yard_hours (Eq. 7)')
        fp = self._pasture_days() / 365 * (inp.get('pasture_hours') or 0.0) / 24
        fy = (inp.get('yard_days') or 0.0) / 365 * (inp.get('yard_hours') or 0.0) / 24
        return fp, fy

    @staticmethod
    def _urine(n_pct):
        return min(70.0, max(30.0, s.URINE_INTERCEPT + s.URINE_SLOPE * n_pct)) / 100

    @staticmethod
    def _n2o_grazing_split(urine):
        liquid, solid = s.N2O[('cattle', 'liquid')][3], s.N2O[('cattle', 'solid')][3]
        return urine * liquid + (1 - urine) * solid

    def _n2o_grazing(self, group, family, urine):
        if family == 'cattle':
            return self._n2o_grazing_split(urine)
        return s.N2O[(family, 'solid')][3]
