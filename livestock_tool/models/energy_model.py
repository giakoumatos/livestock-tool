from ..sources import WFLDB35
from ..tables import ipcc2019 as ipcc
from .base import Model, fmt, pct
from .model_enums import CATEGORIES


class EnergyModel(Model):
    """Gross energy intake of one animal class.

    Routes, in this order:
      1. a dry matter intake is given (dmi_kg_day, kg DM per head and day):
         GE = DMI x 18.45 MJ/kg DM (IPCC 2019, Vol. 4, Ch. 10, Eq. 10.16
         text, p. 10.30; WFLDB v3.5 section 3.9.6.1 allows it "when no
         better data are available");
      2. cattle with dmi_equation: the simplified Tier 2 intake (Eq. 10.17,
         10.18, 10.18A, 10.18B or Table 10.8, p. 10.31-10.33), then as 1;
      3. IPCC 2019 Tier 2 (Eq. 10.3 to 10.16), for sheep and goats or for
         cattle and buffalo, when feeding_days are given;
      4. otherwise Tier 1 (m_energy_tier 'tier1', no GE): the enteric and
         excretion models then take the Tier 1 tables. Cattle have no Tier 1
         here (Table 10.11 is by region only), so they stop.
    For cattle the intake is checked against body weight (p. 10.32).

    Inputs:
      category: key of model_enums.CATEGORIES
      dmi_kg_day: kg DM/(head*day), or None
      de_pct: digestibility of the feed, % of GE
      weight_kg: average live weight, kg
      sex: 'female', 'intact_male' or 'castrate'
      age_class: 'young' (sheep lamb to 1 year) or 'adult'
      feeding_days: {feeding situation (Table 10.5): days per year}
      weight_start_kg, weight_end_kg: sheep/goats, live weight at weaning
        and at one year or slaughter (Eq. 10.7), kg
      weight_gain_kg_day, mature_weight_kg: cattle (Eq. 10.6)
      milk_kg_day, milk_fat_pct: milk produced, kg/(head*day) averaged over the
        whole class and the year, fat %
      weaning_gain_kg: sheep/goats whose milk is not known: weight gained to
        weaning by the young of one female giving birth, kg (Eq. 10.10;
        weighted by pregnant_share, Table 10.3 footnote)
      fibre_type: 'cashmere', 'angora', 'sheep_fibre', 'wool' or None
      wool_kg_year: wool per head and year (fibre_type 'wool'), kg
      pregnant_share: share of the class that gives birth in the year
      offspring_per_birth: kids or lambs born per female giving birth
      work_hours_day: draught work, cattle and buffalo, h/day
      lactation_days: dairy cows, days in milk a year (Cfi weighted, Table 10.4)
      dmi_equation, nemf_mj_kg: simplified Tier 2 intake of cattle

    Outputs:
      m_energy_ge: MJ/(head*day), None on Tier 1
      m_energy_dmi: kg DM/(head*day), None on Tier 1
      m_energy_neg: net energy for growth, MJ/(head*day)
      m_energy_tier: 'intake', 'simplified', 'tier2' or 'tier1'
      m_energy_check: the body-weight check's warning, or None
    """

    _input_variables = ('category', 'dmi_kg_day', 'de_pct')

    def compute(self):
        cat = CATEGORIES[self.category]
        inp = self.inputs
        self._neg = 0.0
        if self.de_pct is not None and self.de_pct < 45:
            raise ValueError(f'digestibility {fmt(self.de_pct)} % is below 45 %: REM and REG (IPCC '
                             f'2019 Eq. 10.14-10.15) are not meaningful there')
        dmi = self.dmi_kg_day
        if dmi is None and cat.energy == 'cattle' and inp.get('dmi_equation'):
            dmi, tier = self._simplified_dmi(), 'simplified'
        elif dmi is not None:
            tier = 'intake'
        if dmi is not None:
            ge = dmi * ipcc.GE_PER_KG_DM.value
            self.note('ge', f'gross energy {fmt(ge)} MJ per head and day = dry matter intake '
                            f'{fmt(dmi)} kg x {fmt(ipcc.GE_PER_KG_DM.value)} MJ/kg '
                            f'({ipcc.GE_PER_KG_DM.cite()}; {WFLDB35.short}, section 3.9.6.1)')
            if cat.energy == 'cattle' and inp.get('weight_gain_kg_day') and not inp.get('salca'):
                self._neg = self._cattle_neg()
        elif cat.energy and inp.get('feeding_days'):
            tier = 'tier2'
            ge = self._sheep_goats() if cat.energy == 'sheep_goats' else self._cattle()
            dmi = ge / ipcc.GE_PER_KG_DM.value
            self.note('ge', f'dry matter intake {fmt(dmi)} kg per head and day = GE / '
                            f'{fmt(ipcc.GE_PER_KG_DM.value)} MJ/kg ({ipcc.GE_PER_KG_DM.cite()})')
        elif cat.energy == 'cattle':
            raise ValueError(f'{cat.label}: give the dry matter intake, the Tier 2 data (feeding_days '
                             f'and the rest) or dmi_equation (IPCC 2019 Eq. 10.17-10.18B); the Tier 1 '
                             f'factors of cattle (Table 10.11) are not used')
        else:
            return {'m_energy_ge': None, 'm_energy_dmi': None, 'm_energy_neg': 0.0,
                    'm_energy_tier': 'tier1', 'm_energy_check': None}
        return {'m_energy_ge': ge, 'm_energy_dmi': dmi, 'm_energy_neg': self._neg,
                'm_energy_tier': tier, 'm_energy_check': self._dmi_check(dmi)}

    def _simplified_dmi(self):
        """Simplified Tier 2 intake of cattle (Eq. 10.17-10.18B, Table 10.8)."""
        inp, eq = self.inputs, self.inputs['dmi_equation']
        if eq not in ipcc.DMI_EQUATIONS:
            raise ValueError(f'dmi_equation "{eq}": one of {", ".join(ipcc.DMI_EQUATIONS)}')
        if inp.get('weight_kg') is None:
            raise ValueError('dmi_equation needs weight_kg (live body weight)')
        nemf, nemf_text = inp.get('nemf_mj_kg'), 'given'
        if eq in ('calves', 'growing_cattle') and nemf is None:
            if self.de_pct is None:
                raise ValueError(f'{eq}: give nemf_mj_kg (IPCC 2019 Table 10.8A) or de_pct')
            nemf = ipcc.nemf_from_de(self._rem(), self.de_pct)
            nemf_text = (f'REM {fmt(self._rem())} x 18.45 x DE {fmt(self.de_pct)} % (IPCC 2019 Table '
                         f'10.8A, source note, p. 10.33)')
        if eq == 'lactating_dairy_cows' and (inp.get('milk_kg_day') is None or
                                             inp.get('milk_fat_pct') is None):
            raise ValueError('lactating_dairy_cows: give milk_kg_day and milk_fat_pct (FCM)')
        if eq == 'mature_beef_cows' and self.de_pct is None:
            raise ValueError('mature_beef_cows: give de_pct (IPCC 2019 Table 10.8)')
        dmi, text = ipcc.simplified_dmi(eq, inp['weight_kg'], nemf=nemf, de_pct=self.de_pct,
                                        lactating=bool(inp.get('milk_kg_day')),
                                        milk_kg_day=inp.get('milk_kg_day'),
                                        fat_pct=inp.get('milk_fat_pct'))
        if eq in ('calves', 'growing_cattle'):
            text += f'; NEmf {fmt(nemf)} MJ/kg DM, {nemf_text}'
        self.note('ge', f'dry matter intake {fmt(dmi)} kg per head and day by the simplified Tier 2 '
                        f'method = {text}')
        return dmi

    def _dmi_check(self, dmi):
        """Cattle: IPCC's cross-check of the intake against body weight."""
        w = self.inputs.get('weight_kg')
        if CATEGORIES[self.category].energy != 'cattle' or not w:
            return None
        ratio = dmi / w
        high = 0.04 if self.inputs.get('milk_kg_day') else 0.03
        if 0.02 <= ratio <= high:
            return None
        return (f'dry matter intake {fmt(dmi)} kg/d is {pct(ratio)} of the {fmt(w)} kg body weight; '
                f'IPCC expects about 2-3 % for mature or growing cattle and up to 4 % for high '
                f'yielding dairy cows ({ipcc.DMI_CHECK_WHERE})')

    def _cattle_neg(self):
        """NEg of cattle and buffalo, Eq. 10.6 (p. 10.25); also needed for the N
        retained in growth (Eq. 10.33) when the intake is given."""
        inp = self.inputs
        if inp.get('weight_kg') is None or inp.get('mature_weight_kg') is None:
            raise ValueError('cattle with a weight gain: give weight_kg and mature_weight_kg for '
                             'NEg (IPCC 2019 Eq. 10.6), which the N retained in growth needs')
        c = {'female': 0.8, 'castrate': 1.0, 'intact_male': 1.2}[inp.get('sex') or 'female']
        return 22.02 * (inp['weight_kg'] / (c * inp['mature_weight_kg'])) ** 0.75 *             inp['weight_gain_kg_day'] ** 1.097

    # Eq. 10.14 and 10.15: DE in percent.
    def _rem(self):
        de = self.de_pct
        return 1.123 - 4.092e-3 * de + 1.126e-5 * de ** 2 - 25.4 / de

    def _reg(self):
        de = self.de_pct
        return 1.164 - 5.16e-3 * de + 1.308e-5 * de ** 2 - 37.4 / de

    def _feeding_ca(self, table):
        days = self.inputs['feeding_days']
        total = sum(days.values())
        if abs(total - 365) > 0.5:
            raise ValueError(f'feeding days add up to {fmt(total)}, not 365')
        ca = sum(table[s].value * d for s, d in days.items()) / 365
        parts = ', '.join(f'{s.replace("_", " ")} {fmt(d)} d at {table[s].value}'
                          for s, d in days.items())
        return ca, f'Ca {fmt(ca)} weighted by days ({parts}; {next(iter(table.values())).cite()})'

    def _pregnancy(self):
        share = self.inputs.get('pregnant_share') or 0.0
        if not share:
            return 0.0, None
        per_birth = self.inputs.get('offspring_per_birth') or 1.0
        if per_birth <= 1.0:
            c = ipcc.C_PREGNANCY['single'].value
        elif per_birth < 2.0:
            double = per_birth - 1.0
            c = ipcc.C_PREGNANCY['double'].value * double + \
                ipcc.C_PREGNANCY['single'].value * (1 - double)
        else:
            raise ValueError('offspring_per_birth of 2 or more: give the triplet share')
        return c * share, (f'Cpregnancy {fmt(c)} for {fmt(per_birth)} offspring per birth x '
                           f'{pct(share)} giving birth ({ipcc.C_PREGNANCY["single"].cite()})')

    def _sheep_goats(self):
        inp, cat = self.inputs, CATEGORIES[self.category]
        w = inp['weight_kg']
        if cat.key == 'goats':
            cfi, a_b = ipcc.CFI['goats'], ipcc.NEG_A_B['goats']
        else:
            cfi = ipcc.CFI['sheep_lamb' if inp.get('age_class') == 'young' else 'sheep']
            a_b = ipcc.NEG_A_B['sheep_' + (inp.get('sex') or 'female')]
        cf = cfi.value * (1.15 if cat.key == 'sheep' and inp.get('sex') == 'intact_male' else 1)
        nem = cf * w ** 0.75
        ca, ca_text = self._feeding_ca(ipcc.CA_SHEEP_GOATS)
        nea = ca * w
        neg = 0.0
        bwi, bwf = inp.get('weight_start_kg'), inp.get('weight_end_kg')
        if bwi is not None and bwf is not None and bwf > bwi:
            a, b = a_b
            neg = (bwf - bwi) * (a + 0.5 * b * (bwi + bwf)) / 365
        nel, nel_text = 0.0, None
        ev = ipcc.EV_MILK['goats' if cat.key == 'goats' else 'sheep']
        if inp.get('milk_kg_day'):
            nel = inp['milk_kg_day'] * ev.value
            nel_text = (f'NEl {fmt(nel)} = {fmt(inp["milk_kg_day"])} kg milk/d x EVmilk {ev.value} '
                        f'MJ/kg (Eq. 10.9; {ev.cite()})')
        elif inp.get('weaning_gain_kg'):
            share = inp.get('pregnant_share')
            if share is None:
                raise ValueError('weaning_gain_kg is per female giving birth: give pregnant_share '
                                 '(IPCC 2019 Table 10.3, footnote: NEl applies only to them)')
            nel = 5 * inp['weaning_gain_kg'] / 365 * ev.value * share
            nel_text = (f'NEl {fmt(nel)} = 5 x {fmt(inp["weaning_gain_kg"])} kg gained by the young '
                        f'of a female to weaning / 365 x EVmilk {ev.value} MJ/kg x {pct(share)} '
                        f'giving birth (milk not known: {ev.cite()}; Table 10.3, footnote)')
        newool, wool_text = 0.0, None
        fibre = inp.get('fibre_type')
        if fibre == 'wool':
            newool = ipcc.EV_WOOL_SHEEP.value * inp['wool_kg_year'] / 365
            wool_text = (f'NEwool {fmt(newool)} = {ipcc.EV_WOOL_SHEEP.value} MJ/kg x '
                         f'{fmt(inp["wool_kg_year"])} kg/365 ({ipcc.EV_WOOL_SHEEP.cite()})')
        elif fibre:
            key = {'cashmere': 'goats_cashmere', 'angora': 'goats_angora',
                   'sheep_fibre': 'sheep_fibre'}[fibre]
            newool = ipcc.NE_FIBRE_PER_DAY[key].value
            wool_text = f'NEwool {fmt(newool)} MJ/d for {fibre} ({ipcc.NE_FIBRE_PER_DAY[key].cite()})'
        c_preg, preg_text = self._pregnancy()
        nep = c_preg * nem
        rem, reg = self._rem(), self._reg()
        ge = ((nem + nea + nel + nep) / rem + (neg + newool) / reg) / (self.de_pct / 100)
        parts = [f'NEm {fmt(nem)} = Cfi {fmt(cf)} x {fmt(w)} kg^0.75 ({cfi.cite()})',
                 f'NEa {fmt(nea)} = {ca_text} x {fmt(w)} kg']
        if neg:
            parts.append(f'NEg {fmt(neg)} from {fmt(bwi)} to {fmt(bwf)} kg, a {a_b[0]}, b '
                         f'{a_b[1]} ({ipcc.NEG_A_B_WHERE})')
        if nel_text:
            parts.append(nel_text)
        if wool_text:
            parts.append(wool_text)
        if preg_text:
            parts.append(f'NEp {fmt(nep)} = {preg_text} x NEm')
        self.note('ge', f'gross energy {fmt(ge)} MJ per head and day by IPCC 2019 Tier 2 '
                        f'({ipcc.EQ_GE}): ' + '; '.join(parts) +
                        f'; REM {fmt(rem)}, REG {fmt(reg)} at DE {fmt(self.de_pct)} % '
                        f'({ipcc.EQ_REM}; {ipcc.EQ_REG})')
        return ge

    def _cattle(self):
        inp = self.inputs
        w = inp['weight_kg']
        days = inp.get('lactation_days')
        if inp.get('milk_kg_day'):
            cfi = ipcc.CFI['cattle_lactating']
        elif inp.get('sex') == 'intact_male':
            cfi = ipcc.CFI['cattle_bulls']
        else:
            cfi = ipcc.CFI['cattle']
        cf, cfi_text = cfi.value, cfi.cite()
        if inp.get('milk_kg_day') and days is not None:
            # Table 10.4: 0.386 while lactating, 0.322 for non-lactating cows.
            dry = ipcc.CFI['cattle'].value
            cf = (cfi.value * days + dry * (365 - days)) / 365
            cfi_text = (f'Cfi {fmt(cf)} = {cfi.value} for {fmt(days)} days in milk and {dry} for '
                        f'{fmt(365 - days)} dry days, {cfi.cite()}')
        nem = cf * w ** 0.75
        ca, ca_text = self._feeding_ca(ipcc.CA_CATTLE)
        nea = ca * nem
        neg = self._cattle_neg() if inp.get('weight_gain_kg_day') else 0.0
        self._neg = neg
        if inp.get('milk_kg_day') and inp.get('milk_fat_pct') is None:
            raise ValueError(f'{inp.get("class_name")}: give the milk fat (section 4, Cattle); NEl of '
                             f'IPCC 2019 Eq. 10.8 takes it')
        nel = inp['milk_kg_day'] * (1.47 + 0.40 * inp['milk_fat_pct']) if inp.get('milk_kg_day') \
            else 0.0
        nework = 0.10 * nem * (inp.get('work_hours_day') or 0)
        c_preg = ipcc.C_PREGNANCY['cattle'].value * (inp.get('pregnant_share') or 0)
        nep = c_preg * nem
        rem, reg = self._rem(), self._reg()
        ge = ((nem + nea + nel + nework + nep) / rem + neg / reg) / (self.de_pct / 100)
        self.note('ge', f'gross energy {fmt(ge)} MJ per head and day by IPCC 2019 Tier 2 '
                        f'({ipcc.EQ_GE}): NEm {fmt(nem)} ({cfi_text}), NEa {fmt(nea)} ({ca_text}), '
                        f'NEg {fmt(neg)} (Eq. 10.6, p. 10.25), NEl {fmt(nel)} (Eq. 10.8, p. 10.26), '
                        f'NEwork {fmt(nework)} (Eq. 10.11), NEp {fmt(nep)} (Table 10.7); REM '
                        f'{fmt(rem)}, REG {fmt(reg)} at DE {fmt(self.de_pct)} %')
        return ge
