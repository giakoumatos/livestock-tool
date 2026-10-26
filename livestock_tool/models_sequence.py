"""Runs the models for one dataset, class by class, in the crop tool's
modelsSequence pattern: inputs -> defaults -> models in order -> outputs.

Each class gives per-year totals; the dataset's outputs are their sums,
and the traces keep every class's calculation for the flow comments.
"""
from .default_generation import DefaultValuesWrapper, FunctionDefault
from .models.air_model import NmvocModel, ParticulateModel
from .models.base import fmt, pct
from .models.emep_nitrogen_model import LITTER_BASED, EmepNitrogenModel
from .models.energy_model import EnergyModel
from .models.enteric_model import EntericModel, ym_factor
from .models.excretion_model import ExcretionModel
from .models.manure_ch4_model import ManureCh4Model
from .models.model_enums import CATEGORIES, SYSTEMS
from .models.nitrogen_model import NitrogenModel, leaching_scope
from .models.routing import Route, route_for
from .models.salca_model import SalcaModel
from .tables import emep2023 as emep
from .tables import ipcc2019 as ipcc
from .workbooks.input_reader import ACTION

# Defaults the data collection may leave empty, each a cited table value.
DEFAULT_GENERATORS = {
    'ue_frac': FunctionDefault(ipcc.ue_default, 'category', 'grain_share'),
}
OUTPUT_KEYS = ('ch4_enteric', 'ch4_manure', 'n2o_manure_direct', 'n2o_pasture_direct',
               'n2o_indirect_volatilisation', 'n2o_indirect_leaching', 'nh3', 'nox',
               'no3_groundwater', 'pm25', 'pm25_10', 'pm10_plus', 'nmvoc')
_N_KEYS = ('n2o_manure_direct', 'n2o_pasture_direct', 'n2o_indirect_volatilisation',
           'n2o_indirect_leaching', 'nh3', 'nox', 'no3_groundwater')
# Which calculation steps each flow's comment shows, in order.
COMMENT_STEPS = {'ch4_enteric': ('ge', 'ch4_enteric'), 'ch4_manure': ('ge', 'vs', 'ch4_manure'),
                 'nmvoc': ('ge', 'vs', 'nmvoc'), 'pm25': ('pm25',), 'pm25_10': ('pm25_10',),
                 'pm10_plus': ('pm10_plus',), **{k: ('nex', k) for k in _N_KEYS}}
SALCA_STEPS = {'ch4_enteric': ('ch4_enteric',), 'ch4_manure': ('ch4_manure',),
               **{k: ('nex', k) for k in _N_KEYS}}
# Manure systems whose excreta fall outside buildings (IPCC 2019 Table 10.18).
OPEN_AIR = ('pasture', 'dry_lot', 'burned_for_fuel')


class ModelsSequence:
    def __init__(self, dataset):
        self.dataset = dataset
        self.route = route_for(dataset.activity['geography'])
        self.totals = dict.fromkeys(OUTPUT_KEYS, 0.0)
        self.traces = {k: [] for k in OUTPUT_KEYS}
        self.classes = []
        self.open_points = dataset.open_points
        for point in (dataset.activity.get('open_points') or '').split('\n'):
            if point.strip():
                self.open_points.append(point.strip())

    def execute(self):
        for row in self.dataset.herd:
            self._run_class(row)
        self._method_notes()
        return self

    # --- one animal class ------------------------------------------------
    def _run_class(self, row):
        a = self.dataset.activity
        inputs = DefaultValuesWrapper({**row, 'salca': self.route is Route.SALCA},
                                      DEFAULT_GENERATORS)
        name = row['class_name']
        energy = EnergyModel(inputs)
        e = energy.compute()
        common = {**row, **{k: a.get(k) for k in (
            'climate_zone', 'b0_region', 'moisture', 'liquid_retention_months', 'nh3_option',
            'liquid_crust_share', 'liquid_pit_share', 'liquid_digester_share',
            'solid_compost_share', 'solid_deep_bedding_share', 'mms_leaching',
            'daily_spread_type', 'ipcc_region', 'crust_thick_dry', 'cover_ch4_reduction',
            'digester_type', 'frac_gas_digester')},
            'ge': e['m_energy_ge'], 'dmi': e['m_energy_dmi'], 'neg': e['m_energy_neg'],
            'tier': e['m_energy_tier'],
            'irrigated': a.get('irrigated_pasture', False),
            'pasture_in_dataset': a.get('pasture_in_dataset', True)}
        if self.route is Route.SALCA:
            results, models, extra = self._salca(row, common, energy)
        else:
            results, models, extra = self._ipcc(row, common, inputs, energy)
        housed_share = extra['housed_share']
        pm = ParticulateModel({**common, 'housed_share': housed_share,
                               'route': 'EU' if self.route is Route.EU else 'WFLDB'})
        p = pm.compute()
        results.update(pm25=p['m_pm_pm25'], pm25_10=p['m_pm_pm25_10'],
                       pm10_plus=p['m_pm_pm10_plus'])
        models.append(pm)

        trace = {}
        for m in models:
            for k, lines in m.trace.items():
                trace.setdefault(k, []).extend(lines)
        steps_for = SALCA_STEPS if self.route is Route.SALCA else COMMENT_STEPS
        cat = CATEGORIES[row['category']]
        basis = f'{name} ({fmt(row["head"])} head, {cat.label})'
        for key in OUTPUT_KEYS:
            self.totals[key] += results.get(key, 0.0)
            steps = [s for part in steps_for.get(key, COMMENT_STEPS[key])
                     for s in trace.get(part, [])]
            self.traces[key].append((row, basis, steps))
        for k, f in inputs.used_defaults.items():
            self.open_points.append(f'{name}: {k} = {f.value} {f.unit} is a default ({f.cite()}).')
        self._class_points(row, cat, e, extra)
        if self.route is not Route.SALCA:
            self._default_points(row, cat, common, extra['shares'])
        if cat.n_retention in ('sheep', 'goats') and row.get('milk_kg_day')                 and row.get('nex_kg_year') is None and self.route is not Route.SALCA:
            self.open_points.append(
                f'{name}: milking {cat.label}: the N retention of IPCC 2019 Table 10.20 (0.10) is '
                f'for non-dairy sheep and goats; IPCC recommends country-specific values for dairy '
                f'ones (p. 10.85). Give nex_kg_year if known.')
        if row.get('housing_days') is None and results.get('pm25'):
            self.open_points.append(
                f'{name}: no housing days given, so the share of the year in housing for PM2.5 is '
                f'{pct(housed_share)}, {extra["housed_basis"]}.')
        self.classes.append({'class_name': name, 'head': row['head'], **results, **extra,
                             'ge': e['m_energy_ge'], 'dmi': e['m_energy_dmi'],
                             'tier': e['m_energy_tier']})

    def _class_points(self, row, cat, e, extra):
        """Open points of one class from the IPCC 2019 choices it ran on."""
        name, a = row['class_name'], self.dataset.activity
        if e['m_energy_tier'] == 'tier1':
            self.open_points.append(
                f'{name}: no intake data, so IPCC 2019 Tier 1 was used (enteric CH4 Table 10.10, VS '
                f'Table 10.13A, N excreted Table 10.19, {a.get("ipcc_region")}); Tier 1 does not '
                f'follow the diet or the productivity of the herd. Give dmi_kg_day or the Tier 2 '
                f'data to replace it.')
        if e['m_energy_tier'] == 'simplified':
            self.open_points.append(
                f'{name}: intake by the simplified Tier 2 equation "{row.get("dmi_equation")}" '
                f'(IPCC 2019 Eq. 10.17-10.18B, Table 10.8); IPCC prefers the full Tier 2 energy '
                f'calculation and uses these equations to check it (p. 10.32).')
        if e['m_energy_check']:
            self.open_points.append(f'{ACTION}{name}: {e["m_energy_check"]}; check the intake '
                                    f'and the body weight.')
        if (cat.energy == 'cattle' and row.get('milk_kg_day') and row.get('lactation_days') is None
                and e['m_energy_tier'] == 'tier2'):
            self.open_points.append(
                f'{name}: Cfi 0.386 (lactating cows, IPCC 2019 Table 10.4) is used for the whole '
                f'year; give lactation_days so the dry period takes 0.322.')
        if self.route is Route.SALCA:
            return
        shares = extra.get('shares') or {}
        if shares.get('liquid_slurry_crust') and not a.get('crust_thick_dry'):
            self.open_points.append(
                f'{name}: liquid storage with a natural crust keeps the full MCF; IPCC 2019 allows '
                f'40 % less only for a thick, dry crust (Table 10.17, fn 1): set crust_thick_dry if '
                f'it is.')
        if shares.get('liquid_slurry_cover') and a.get('cover_ch4_reduction') is None:
            self.open_points.append(
                f'{name}: covered liquid storage keeps the full MCF; a solid cover reduces CH4 by '
                f'25-50 % by IPCC 2019 (Table 10.17, fn 1), which gives no single value: give '
                f'cover_ch4_reduction.')
        if shares.get('anaerobic_digester') and self.route is Route.EU:
            self.open_points.append(
                f'{name}: on the EU route the digestate is taken as slurry storage for NH3 and NOx '
                f'(EMEP/EEA 2023, 3.B, Table 3-9); its CH4 and N2O follow IPCC 2019 Tables 10.17 '
                f'and 10.21.')

    def _default_points(self, row, cat, common, shares):
        """Open points for the cited defaults a class ran on because the data
        collection left them empty, each only where it entered the result."""
        name, a = row['class_name'], self.dataset.activity
        # Ym enters only the Tier 2 enteric methane (poultry have none).
        if row.get('ym_pct') is None and common['tier'] != 'tier1' and cat.ym != 'poultry':
            ym, cite = ym_factor(common)
            self.open_points.append(f'{name}: Ym {fmt(ym)} % is the default of {cite}; give the '
                                    f'methane conversion factor in section 4 if it is known.')
        if a.get('liquid_retention_months') is None and any(
                v and SYSTEMS[k].mcf == 'liquid' for k, v in shares.items()):
            self.open_points.append(
                f'{name}: the storage time of the liquid manure is not given, so the MCF of 6 '
                f'months is used (IPCC 2019 Table 10.17, fn 1); give it in section 5.')
        if self.route is not Route.EU:
            return
        yard = emep.YARD_SHARE.get(cat.emep)
        if row.get('yard_share') is None and yard:
            self.open_points.append(
                f'{name}: {pct(yard.value)} of the N excreted is put on yards, the EMEP/EEA default '
                f'({yard.cite()}); it also takes that share from the pasture N for the IPCC pasture '
                f'N2O and leaching (method decision 7). Give the yard share in section 4 if the '
                f'animals have no yard or another share.')
        daily = shares.get('daily_spread')
        if daily and a.get('daily_spread_type') is None:
            self.open_points.append(
                f'{name}: the daily-spread manure ({pct(daily)}) is taken as solid (EMEP/EEA 2023, '
                f'3.B, Step 8 needs slurry or solid); say which in section 5.')
        litter = any(shares.get(k) for k in LITTER_BASED) or (
            daily and (a.get('daily_spread_type') or 'solid') == 'solid')
        if row.get('straw_kg_year') is None and litter and emep.STRAW.get(cat.emep):
            self.open_points.append(
                f'{name}: the bedding straw is the EMEP/EEA default (3.B, Table 3-7, p. 23), scaled '
                f'to the housing days and the share of the manure on litter; give the straw used in '
                f'section 4.')
        if row.get('silage_share_of_max') is None and cat.emep in emep.NMVOC_TIER2_MJ:
            self.open_points.append(
                f'{ACTION}{name}: no silage share is given, so no NMVOC from silage is counted, '
                f'the largest NMVOC source of cattle; EMEP/EEA 2023 gives no default (3.B, p. 27: '
                f'1.0 when silage feeding dominates). Give it in section 4 (0 if no silage is fed).')

    def _ipcc(self, row, common, inputs, energy):
        a = self.dataset.activity
        shares = self.dataset.shares_for(row['class_name'])
        common = {**common, 'ue_frac': inputs['ue_frac'], 'shares': shares}
        enteric = EntericModel(common)
        excretion = ExcretionModel(common)
        x = excretion.compute()
        manure = ManureCh4Model({**common, 'vs': x['m_excretion_vs']})
        nitrogen = (EmepNitrogenModel if self.route is Route.EU else NitrogenModel)(
            {**common, 'nex': x['m_excretion_nex']})
        n = nitrogen.compute()
        results = {'ch4_enteric': enteric.compute()['m_enteric_ch4'],
                   'ch4_manure': manure.compute()['m_manure_ch4'],
                   **{k: n['m_n_' + k] for k in _N_KEYS}}
        models = [energy, enteric, excretion, manure, nitrogen]
        # The time in buildings, for PM (Table 3-5, housed animals, p. 18) and
        # NMVOC (x_hous of Eq. 48-54, p. 27). Yards and dry lots are open-air
        # areas, not housing: their time counts with grazing.
        housed = row.get('housing_days')
        if housed is not None:
            housed_share, basis = housed / 365, 'from the housing days'
        elif 'm_n_housed_share' in n:
            housed_share = n['m_n_housed_share']
            basis = 'the share of the excreta in buildings (yards not counted)'
        else:
            housed_share = 1 - sum(shares.get(k) or 0.0 for k in OPEN_AIR)
            basis = 'the share of the manure not on pasture, dry lots or burned dung'
        if self.route is Route.EU:
            nmvoc = NmvocModel({**common, 'vs': x['m_excretion_vs'], 'housed_share': housed_share,
                                'nh3_hous': n['m_n_nh3_hous'],
                                'nh3_storage': n['m_n_nh3_storage']})
            results['nmvoc'] = nmvoc.compute()['m_nmvoc']
            models.append(nmvoc)
        if n.get('m_n_mms_leached_n'):
            scope = leaching_scope(a)
            self.open_points.append(
                f'{row["class_name"]}: {fmt(n["m_n_mms_leached_n"])} kg N a year leach from manure '
                f'management by IPCC 2019 Table 10.22 (FracLeach_MS), '
                + ('on the systems WFLDB leaches (liquid/slurry and solid storage, section 3.9.5.2, '
                   'mms_leaching wfldb); ' if scope == 'wfldb' else 'on every system; ')
                + 'IPCC applies these fractions only to uncovered manure without runoff '
                  'containment (Table 10.22, fn 5)'
                + (', and the climate is dry.' if a.get('moisture') == 'dry' else '.'))
        return results, models, {'shares': shares, 'housed_share': housed_share,
                                 'housed_basis': basis, 'nex': x['m_excretion_nex'],
                                 'vs': x['m_excretion_vs']}

    def _salca(self, row, common, energy):
        if row.get('dmi_kg_day') is None:
            raise ValueError(f'{row["class_name"]}: SALCA takes the feed intake from the data '
                             '(dmi_kg_day or dmi_kg_year_class); it has no feed requirement model')
        model = SalcaModel(common)
        out = model.compute()
        results = {'ch4_enteric': out['m_n_ch4_enteric'], 'ch4_manure': out['m_n_ch4_manure'],
                   **{k: out['m_n_' + k] for k in _N_KEYS}}
        return results, [model], {'shares': {}, 'housed_share': out['m_n_housed_share'],
                                  'pasture_share': out['m_n_pasture_share'],
                                  'housed_basis': 'the share of the year not on pasture or yards'}

    # --- notes once per dataset -------------------------------------------
    def _method_notes(self):
        """The rules that move a result most, said once per dataset so the
        reviewer sees them next to the data gaps."""
        a = self.dataset.activity
        grazing_land = any(i['group'] == 'FromEnvironment' and str(i['name']).startswith('Occupation')
                           and any(w in str(i['name']).lower() for w in ('grazing', 'pasture',
                                                                         'grassland', 'meadow'))
                           for i in self.dataset.inputs)
        if a.get('pasture_in_dataset') and not grazing_land:
            self.open_points.append(
                f'{ACTION}pasture_in_dataset is yes, but no occupation of grazing land is among the '
                'inputs: '
                'either add it, or set pasture_in_dataset to no so that the excreta on pasture are '
                'left to the pasture dataset (WFLDB v3.5, section 3.12.2).')
        if self.route is Route.WFLDB and self.totals['nh3']:
            self.open_points.append(
                'NH3 and NOx follow IPCC 2019, more recent than the 60 % NH3-N / 40 % NOx-N split '
                'of WFLDB v3.5: on pasture 0.197 NH3-N and 0.015 NOx-N per kg N deposited (Vol. 4, '
                'Ch. 11, Annex 11A.8, Table 8A.1); in manure management FracGas_MS (Table 10.22) is '
                'NH3 + NOx with no split, so the NOx-N is the EMEP/EEA 2023 storage NO factor '
                '(3.B, Table 3-10) on the TAN entering the store, the guidebook IPCC refers to '
                '(p. 10.89), and the rest is NH3-N.')
        if self.totals['pm25'] and any(c['housed_share'] < 1 for c in self.classes):
            self.open_points.append(
                'PM2.5 is the EMEP/EEA housing factor (Table 3-5) taken on the share of the year '
                'in housing; EMEP/EEA says to apply it to housed animals only (3.B, p. 18) and '
                'gives no rule for animals housed part of the year.')
        if self.route is Route.SALCA:
            self.open_points.append(
                'SALCA is implemented as documented in Appendix 6 of Nemecek et al. (2024), not '
                'line by line from its code (agroscope-ch/salca v1.0.1). Where they differ the '
                'appendix is followed: the pasture NH3 and nitrate of cattle are weighted by the '
                'pasture days (the code divides by 365); the liquid-storage N2O factors by the crust '
                'and pit shares (the code mixes up the pit share with its EF); the Agrammon housing '
                'correction on grazing days only with the Agrammon option, with 12 h in the 140 % '
                'class (the code: under both options, below 12 h); no farm-level Agrammon '
                'corrections for housing, yard, store cover and stirring (the appendix has none); '
                'corrOS 0.32 for pigs (Tab. 6; the code 0.42); laying hens on the poultry MCF; the '
                'yard N2O on the yard urine share; the immobilisation base with the yard TAN; NOx '
                'on pasture 0.012 as printed; Tab. 8 and 10 as printed (the code files carry more '
                'digits); grazing pigs leach 50 % of the TAN excreted (the code: after losses); '
                'other animals take both Tab. 10 means (urine on the TAN, dung on the rest; the '
                'code the urine mean only). Readings of the appendix: milk N of Tab. 4 per kg (its '
                '"m3" is a misprint); the EEA immobilisation per kg straw, as EMEP/EEA 3.B Eq. 18 '
                'has it (the appendix writes per kg TAN), and both options before the storage '
                'losses, as the code does; the raw-fibre limit of Tab. 1 is IPCC\'s NDF; Eq. 9 '
                'splits the organic matter between slurry and solid manure only where there is '
                'solid manure (a slurry-only herd stores all of it as slurry; as printed, and in '
                'the code, it would go to solid storage that does not exist). Not used: '
                'Kirchgessner (Eq. 2) and the code\'s CH4 '
                'correction factors. SALCA counts its storage NOx factors (EEA 2019, Table 3.10) '
                'x 14/30, as its appendix states, although the table is already in N; PM2.5, which '
                'SALCA does not model, follows WFLDB (EMEP/EEA Table 3-5).')
