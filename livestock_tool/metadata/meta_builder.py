"""Writes the meta fields of a livestock dataset from the data collection and
the model results, in the wording of the agri-lca-pipeline's template."""
from ..models.allocation_model import dairy_allocation
from ..models.base import fmt, pct
from ..models.model_enums import CATEGORIES, SYSTEMS
from ..models.routing import Route
from ..output_mapping import route_label
from ..references import project_references, with_references
from ..sources import EMEP2023, IDF2022, IPCC2006, IPCC2019, SALCA, WFLDB35
from ..tables import wfldb35 as wfldb
from ..workbooks.input_reader import ACTION

_EMISSIONS = {
    'ch4_enteric': 'methane from enteric fermentation and manure',
    'ch4_manure': 'methane from enteric fermentation and manure',
    'n2o_manure_direct': 'direct and induced nitrous oxide',
    'n2o_pasture_direct': 'direct and induced nitrous oxide',
    'n2o_indirect_volatilisation': 'direct and induced nitrous oxide',
    'n2o_indirect_leaching': 'direct and induced nitrous oxide',
    'nh3': 'ammonia', 'nox': 'nitrogen oxides', 'no3_groundwater': 'nitrate to ground water',
    'pm25': 'particulate matter', 'nmvoc': 'NMVOC',
}


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]


SALCA_SPREADING = ('Emissions after the application of the manure are outside SALCAanimal; they '
                   'are modelled with the crops that receive it (SALCAfield; Nemecek et al. 2024, '
                   'Appendix 6).')


def _salca_manure(dataset):
    a = dataset.activity
    liquid = ', '.join(f'{c["class_name"]} {pct(c["liquid_n_share"] or 0)}' for c in dataset.herd)
    shares = [(k, a.get(k)) for k in ('liquid_crust_share', 'liquid_pit_share',
                                     'liquid_digester_share', 'solid_compost_share',
                                     'solid_deep_bedding_share') if a.get(k)]
    words = {'liquid_crust_share': 'liquid manure with a natural crust',
             'liquid_pit_share': 'liquid manure in pits below the animals',
             'liquid_digester_share': 'liquid manure to biogas',
             'solid_compost_share': 'solid manure composted',
             'solid_deep_bedding_share': 'housed solid manure as deep bedding'}
    return (f'SALCA manure data: share of the housing N in liquid manure: {liquid}'
            + ''.join(f'; {words[k]} {pct(v)}' for k, v in shares)
            + f'; ammonia factors {a.get("nh3_option")}.')


def build_meta(dataset, seq):
    a = dataset.activity
    ref = dataset.reference_product()
    byproducts = [p['name'] for p in dataset.products if p['group'] == 'ByProduct']
    products = [ref['name']] + byproducts
    herd = sum(c['head'] for c in seq.classes)
    systems = {}
    for c in seq.classes:
        for k, v in c['shares'].items():
            systems[k] = systems.get(k, 0.0) + v * c['head'] / herd
    grazing = (systems.get('pasture', 0) if seq.route is not Route.SALCA else
               any(c.get('pasture_share') for c in seq.classes)) and a['pasture_in_dataset']
    mms = [SYSTEMS[k].label for k, v in systems.items() if v and k != 'pasture']
    included = list(dict.fromkeys(v for k, v in _EMISSIONS.items() if seq.totals.get(k)))
    where = [w for w in (f'housing and manure management ({", ".join(mms)})' if mms else
                         'housing and manure management',
                         'the dung and urine deposited on pasture' if grazing else None) if w]
    end = (f'This activity ends with the delivery of {_join(products)} at the farm gate. The '
           f'emissions of the animals are included: {_join(included)}, '
           + ', and '.join(f'from {w}' for w in where) + '. '
           + (SALCA_SPREADING if seq.route is Route.SALCA else wfldb.RULE_MANURE_SPREADING)
           + ' All processes after the farm gate are excluded.')
    unit = 'kg FPCM' if ref.get('fpcm_kg') else 'kg'
    general = ' '.join(t for t in (
        a.get('product_description'), a.get('system_description'),
        wfldb.RULE_FIBRE_UNIT if any(h.get('fibre_type') for h in dataset.herd) else None,
        f'The emissions of the animals are calculated per animal class by the '
        f'{route_label(seq.route)}.',
        f'Herd production: [{dataset.amount(ref):.2f}] {unit} of {ref["name"]} per year.',
        f'Herd size: [{fmt(herd)}] animals.') if t)
    housing = ', '.join(f'{c["class_name"]} {pct(c["housed_share"])} of the year in housing'
                        for c in seq.classes)
    manure = ('Manure management: ' + ', '.join(f'{SYSTEMS[k].label} {pct(v)}'
                                                for k, v in systems.items() if v) + '; ') \
        if systems else ''
    technology = ' '.join(t for t in (a.get('technology_description'), f'{manure}{housing}.',
                                      _salca_manure(dataset) if seq.route is Route.SALCA else None)
                          if t)
    meta = {
        'activityName': a['activityName'], 'geography': a['geography'],
        'specialActivityType': 'ordinary transforming activity',
        'startDate': a['startDate'], 'endDate': a['endDate'],
        'technologyLevel': a.get('technologyLevel') or 'Current',
        'includedActivitiesStart': ('This activity starts with the animals on the farm and the '
                                    'reception of the inputs at the farm: the feed, water, fuels, '
                                    'electricity and other materials listed as inputs.'),
        'includedActivitiesEnd': end,
        'generalComment': general, 'geographyComment': a.get('geography_comment'),
        'allocationComment': allocation_comment(dataset, seq, byproducts),
        'technologyComment': technology,
        'timePeriodComment': a.get('time_period_comment'),
        'modellingAndValidation_extrapolations': extrapolations(seq, dataset),
        'modellingAndValidation_samplingProcedure': a.get('sampling_procedure'),
    }
    refs = project_references(a)
    for key in ('includedActivitiesEnd', 'generalComment', 'geographyComment', 'allocationComment',
                'technologyComment', 'timePeriodComment', 'modellingAndValidation_samplingProcedure'):
        meta[key] = with_references(meta[key], refs)
    facts = {k: a.get(k) for k in ('data_source', 'data_source_reference', 'farms_sampled',
                                   'region_detail', 'share_of_national_production', 'pv_years',
                                   'yield_source', 'price_source')}
    facts['activityName'] = a['activityName']
    return meta, {k: v for k, v in facts.items() if v is not None}


def allocation_comment(dataset, seq, byproducts):
    if not byproducts:
        return None
    a = dataset.activity
    basis = f' {a["allocation_basis"]}' if a.get('allocation_basis') else ''
    dairy = any(h['category'] in ('dairy_cattle', 'buffalo') for h in dataset.herd)
    set_up = (f'{ACTION}The allocation factors are in allocationComment; ecoinvent and the pipeline '
              'allocate by the price properties, so the factors must be applied through the '
              'allocation set-up of the dataset, not through the prices.')
    if dairy:
        found = dairy_allocation(dataset)
        dataset.open_points.append(set_up)
        if found is not None:
            factors, text = found
            return text + basis
        meat, milk = wfldb.DAIRY_DEFAULT_MEAT_SHARE, wfldb.DAIRY_DEFAULT_MILK_SHARE
        dataset.open_points.append(
            f'{ACTION}Dairy farm: the IDF allocation needs the milk with its fat and true protein '
            '(product_type milk) and the live weight sold with the class of the animals sold '
            '(section 6 (Products) of the Dataset sheet); until they are given, the WFLDB default '
            f'{pct(meat.value)} meat / {pct(milk.value)} milk applies.')
        return (f'Milk and meat are allocated {pct(milk.value)} to milk (fat and protein corrected '
                f'milk) and {pct(meat.value)} to meat, the default WFLDB applies to dairy farms when '
                f'the data for the IDF calculation are not available ({meat.cite()}; {meat.note}).'
                + basis)
    prices = [p for p in dataset.properties if p['propertyName'] == 'price']
    by_price = (' The products are allocated by their prices: '
                + '; '.join(f'{p["name"]} {fmt(p["amount"])} {p["unitName"]} per kg' for p in prices)
                + '.')
    cats = {CATEGORIES[h['category']].key for h in dataset.herd}
    if 'laying_hens' in cats:
        return wfldb.RULE_EGG_ALLOCATION + by_price + basis
    if cats & {'sheep', 'goats'}:
        analogy = ' WFLDB does not name goats; they are treated as sheep.' if 'goats' in cats else ''
        return wfldb.RULE_ECONOMIC_ALLOCATION + analogy + by_price + basis
    dataset.open_points.append(
        f'{ACTION}WFLDB gives no allocation rule for {_join(sorted(CATEGORIES[c].label for c in cats))} '
        '(section 2.6.3); the products are allocated by their prices. Confirm, or name the LEAP '
        'guideline to follow.')
    return wfldb.RULE_NO_ALLOCATION_RULE + by_price + basis


def extrapolations(seq, dataset):
    dairy = any(h['category'] in ('dairy_cattle', 'buffalo') for h in dataset.herd)
    if seq.route is Route.SALCA:
        text = ('The emissions of the animals are calculated by SALCAanimal V1.0 as documented in '
                'Appendix 6 of Nemecek et al. (2024): enteric and manure methane, the N balance of '
                'the herd from feed, animals and products, ammonia from housing, yards, storage and '
                'pasture with the '
                + {'EEA': 'EEA 2019', 'Agrammon': 'Agrammon 2022'}.get(
                    dataset.activity.get('nh3_option'), '') +
                ' factors, nitrous oxide from storage, yards and pasture, nitrogen oxides from '
                'yards, storage and pasture, and nitrate from pasture; SALCA has no NMVOC. PM2.5 '
                'from housing, which SALCA does not model, by the 2023 edition of the EMEP/EEA '
                'factors WFLDB uses (section 3.9.12, Table 3-5). References: ')
        sources = (SALCA, WFLDB35, EMEP2023)
    else:
        tiers = {c.get('tier') for c in seq.classes}
        routes = {'intake': 'from the dry matter intake given (x 18.45 MJ/kg, IPCC 2019, Vol. 4, '
                            'Ch. 10, p. 10.30; WFLDB section 3.9.6.1)',
                  'simplified': 'from the simplified Tier 2 intake of cattle (IPCC 2019, Vol. 4, '
                                'Ch. 10, Eq. 10.17-10.18B, Table 10.8)',
                  'tier2': 'by IPCC 2019 Tier 2 (Vol. 4, Ch. 10, Eq. 10.3-10.16)'}
        energy = 'gross energy ' + ' or '.join(routes[t] for t in routes if t in tiers)
        tier1 = ('; for the classes without intake data IPCC 2019 Tier 1 (Tables 10.10, 10.13A and '
                 '10.19)' if 'tier1' in tiers else '')
        leaching = ('from liquid/slurry and solid storage only, as WFLDB section 3.9.5.2 has it, with '
                    'the IPCC 2019 Table 10.22 fractions'
                    if dataset.activity.get('mms_leaching') == 'wfldb' else
                    'from every manure management system by IPCC 2019 Table 10.22')
        if seq.route is Route.EU:
            air = ('ammonia and nitrogen oxides by the EMEP/EEA 2023 Tier 2 mass flow (chapter 3.B, '
                   'Steps 3-10, 14 and 15; Steps 11-13, manure application, belong to the crops), '
                   'on which the induced nitrous oxide from volatilisation is taken '
                   '(allowed by IPCC 2019, Vol. 4, Ch. 10, p. 10.89); NMVOC by its Tier 2 method '
                   'and particulate matter by its Tier 1 housing factors (Table 3-5)')
        else:
            air = ('ammonia and nitrogen oxides by IPCC 2019: from manure management the nitrogen '
                   'volatilised (FracGas_MS, Vol. 4, Ch. 10, Table 10.22), of which the nitrogen '
                   'oxides are the EMEP/EEA 2023 storage NO factor on the TAN (3.B, Tables 3-9 and '
                   '3-10), the guidebook IPCC refers to for the split (p. 10.89), and the rest '
                   'ammonia; on pasture 0.197 kg NH3-N and 0.015 kg NOx-N per kg N (Ch. 11, Annex '
                   '11A.8, Table 8A.1), in place of WFLDB\'s 60/40 split (sections 3.9.3.2 and '
                   '3.9.4); PM2.5 from housing by the 2023 edition of the EMEP/EEA factors WFLDB '
                   'uses (section 3.9.12, Table 3-5)')
        text = ('The emissions of the animals follow the WFLDB guidelines v3.5 (Nemecek et al. '
                '2019) for the scope, with the IPCC 2019 Refinement for the methods and factors '
                f'wherever it covers them: {energy}{tier1}; enteric methane, volatile solids, '
                'manure methane and nitrogen excretion by IPCC 2019 (Vol. 4, Ch. 10); direct '
                'nitrous oxide by IPCC 2019 (Vol. 4, Ch. 10 and 11); nitrogen leaching from pasture '
                f'by IPCC 2019 Ch. 11 and {leaching}; {air}. Emissions after manure application '
                'belong to the crops that receive it (WFLDB section 3.12). References: ')
        sources = (WFLDB35, IPCC2019, IPCC2006, EMEP2023)
    if dairy:
        sources += (IDF2022,)
    return text + ' '.join(s.full for s in sources)
