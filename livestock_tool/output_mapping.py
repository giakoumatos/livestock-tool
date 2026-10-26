"""Maps the model outputs and the data collection to exchange rows (the crop
tool's outputMapping step, and its EcospoldFileWriter division by the
yield): herd totals for the year are divided by the reference product's
yearly amount, and every row carries a comment that shows the calculation.
"""
from .flows.templates import FLOW_TEMPLATES
from .models.base import fmt
from .models.property_model import missing_basic, product_properties
from .models.routing import Route
from .models.water_model import water_balance
from .references import cited, project_references, with_references
from .tables import idf2022 as idf
from .tables import wfldb35 as wfldb
from .workbooks.input_reader import ACTION

HEADLINES = {
    'ch4_enteric': 'Methane from enteric fermentation',
    'ch4_manure': 'Methane from manure management and from the excreta on pasture',
    'n2o_manure_direct': 'Direct nitrous oxide from manure management',
    'n2o_pasture_direct': 'Direct nitrous oxide from the dung and urine deposited on pasture',
    'n2o_indirect_volatilisation': ('Induced nitrous oxide from the nitrogen volatilised as ammonia '
                                    'and nitrogen oxides'),
    'n2o_indirect_leaching': 'Induced nitrous oxide from the nitrogen leached',
    'nh3': 'Ammonia from housing, manure management and pasture',
    'nox': 'Nitrogen oxides from manure management and pasture',
    'no3_groundwater': 'Nitrate leached to ground water from manure management and pasture',
    'pm25': 'Particulate matter (PM2.5) from animal housing',
    'pm25_10': 'Particulate matter (PM2.5 to PM10) from animal housing',
    'pm10_plus': 'Particulate matter (above PM10) from animal housing',
    'nmvoc': 'NMVOC from silage, housing, manure storage and grazing',
}
_DATA_KEYS = (('head_source', 'head'), ('dmi_source', 'intake'), ('de_source', 'digestibility'),
              ('cp_source', 'crude protein'), ('ash_source', 'ash'), ('ym_source', 'Ym'),
              ('nex_source', 'N excreted'))
_NEEDS = {'ch4_enteric': ('head', 'intake', 'digestibility', 'Ym'),
          'ch4_manure': ('head', 'intake', 'digestibility', 'ash'),
          'pm25': ('head',), 'pm25_10': ('head',), 'pm10_plus': ('head',)}


def per_kg_sentence(total, unit, ref_amount, ref_name):
    return (f'Per kg of {ref_name}: {fmt(total)} {unit} for the herd\'s year, divided by its '
            f'{ref_amount:,.2f} kg of {ref_name}.')


def _data_sentence(row, needed, more=()):
    parts = [f'{label}: {row[key]}' for key, label in _DATA_KEYS
             if label in needed and row.get(key)]
    parts += [f'{label}: {text}' for label, text in more if text]
    return ('Data: ' + '; '.join(parts) + '.') if parts else ''


def _manure_data(dataset, seq, key, herd_row):
    """The sources of the manure shares and of the B0 column, for the flows
    that depend on them (the "manure" sheet is not used for CH; PM takes the
    shares only when no housing days are given)."""
    if seq.route is Route.SALCA or key in ('ch4_enteric', 'nmvoc') or (
            key.startswith('pm') and herd_row.get('housing_days') is not None):
        return ()
    sources = dict.fromkeys(m['source'] for m in dataset.manure_rows(herd_row['class_name'])
                            if m.get('source'))
    more = [('manure shares', '; '.join(sources))]
    if key == 'ch4_manure':
        more.append(('B0 column', dataset.activity.get('b0_region_source')))
    return more


def emission_rows(dataset, seq):
    a = dataset.activity
    ref = dataset.reference_product()
    r_amount, r_name = dataset.amount(ref), ref['name']
    rows = []
    for key, total in seq.totals.items():
        if not total:
            continue
        t = FLOW_TEMPLATES[key]
        needed = _NEEDS.get(key, ('head', 'intake', 'crude protein', 'N excreted'))
        headline = HEADLINES[key]
        if seq.route is Route.SALCA and key == 'no3_groundwater':
            headline = 'Nitrate leached to ground water from the excreta on pasture'
        if not a.get('pasture_in_dataset'):
            headline = (headline.replace(' and from the excreta on pasture', '')
                        .replace(', manure management and pasture', ' and manure management')
                        .replace(' manure management and pasture', ' manure management'))
        parts = [headline + '.']
        for herd_row, basis, steps in seq.traces[key]:
            parts.append(f'{basis}: ' + '; '.join(steps) + '.')
            data = _data_sentence(herd_row, needed, _manure_data(dataset, seq, key, herd_row))
            if data:
                parts.append(data)
        if key in ('ch4_enteric', 'ch4_manure'):
            parts.append(wfldb.RULE_CH4_SEPARATE)
        parts.append(per_kg_sentence(total, t.unit, r_amount, r_name))
        rows.append(_exchange(a, 'ToEnvironment', t.name, t.unit, total / r_amount, ' '.join(parts),
                              t.compartment, t.subcompartment))
    return rows


def product_rows(dataset):
    a = dataset.activity
    ref = dataset.reference_product()
    r_amount, r_name = dataset.amount(ref), ref['name']
    rows = [_exchange(a, 'ReferenceProduct', r_name, ref['unitName'] or 'kg', 1.0,
                      ref['comment'], pv=a.get('production_volume'))]
    rows[0]['variableName'] = 'RP'
    rows[0]['PV_variableName'] = 'RP_PV'
    rows[0]['PV_comment'] = a.get('production_volume_comment')
    if a.get('production_volume') is None:
        point = (f'{ACTION}{r_name}: no production volume; give the annual production in the '
                 f'geography in section 9 of the Dataset sheet (the by-products\' volumes follow '
                 f'from it).')
        if point not in dataset.open_points:
            dataset.open_points.append(point)
    if ref.get('fpcm_kg'):
        rows[0]['comment'] = ' '.join(c for c in (ref['comment'], _fpcm_sentence(ref)) if c)
    for i, p in enumerate((p for p in dataset.products if p['group'] == 'ByProduct'), 1):
        comment = ' '.join(c for c in (p['comment'], _fpcm_sentence(p) if p.get('fpcm_kg') else None,
                                       per_kg_sentence(dataset.amount(p), p['unitName'] or 'kg',
                                                       r_amount, r_name)) if c)
        row = _exchange(a, 'ByProduct', p['name'], p['unitName'] or 'kg',
                        dataset.amount(p) / r_amount, comment)
        row['variableName'] = f'BP_{i}'
        # The by-product's volume in the same ratio to the reference product's
        # as their amounts, as the data provision template sets it.
        row['PV_variableName'] = f'BP_{i}_PV'
        row['PV_mathematicalRelation'] = f'BP_{i}/RP*RP_PV'
        rows.append(row)
    return rows


def _fpcm_sentence(p):
    return (f'Counted as fat- and protein-corrected milk (FPCM): {fmt(p["amount_per_year"])} kg milk '
            f'x (0.1226 x {fmt(p["fat_pct"])} % fat + 0.0776 x {fmt(p["protein_pct"])} % true '
            f'protein + 0.2534) = {fmt(p["fpcm_kg"])} kg FPCM (IDF 2022, {idf.FPCM_WHERE}; '
            f'WFLDB v3.5, section 2.3).')


def water_row(dataset):
    """The Water outputs that balance the water withdrawn, one row per
    compartment."""
    ref = dataset.reference_product()
    r_amount = dataset.amount(ref)
    rows = []
    for (compartment, subcompartment), (m3, parts) in water_balance(dataset).items():
        comment = ('Water balance of the herd and the year. ' + '; '.join(parts) + '. '
                   + per_kg_sentence(m3, 'm3', r_amount, ref['name']))
        rows.append(_exchange(dataset.activity, 'ToEnvironment', 'Water', 'm3', m3 / r_amount,
                              comment, compartment, subcompartment))
    return rows


_WATER_USE = {'animals': 'Use: drinking and cleaning water of the animals.',
              'irrigation': 'Use: irrigation of the fodder crops.'}


def input_rows(dataset):
    a = dataset.activity
    ref = dataset.reference_product()
    r_amount, r_name = dataset.amount(ref), ref['name']
    rows = []
    for i in dataset.inputs:
        if i['basis'] not in ('herd_year', 'per_kg'):
            raise ValueError(f'{dataset.name}, {i["name"]}: basis must be herd_year or per_kg')
        if i['basis'] == 'herd_year':
            amount = i['amount'] / r_amount
            comment = ' '.join(c for c in (i['comment'], per_kg_sentence(
                i['amount'], i['unitName'], r_amount, r_name)) if c)
        else:
            amount, comment = i['amount'], i['comment']
        if i['group'] == 'FromEnvironment' and str(i['name']).startswith('Water'):
            # The use is stated in the comment, the one place the provision
            # file has for it: the water balance and the pipeline's water
            # check depend on it.
            comment = f'{_WATER_USE[i.get("water_use") or "animals"]} {comment or ""}'.strip()
        if not cited(i['comment'], project_references(a)) and 'Source:' not in (i['comment'] or ''):
            point = (f'{ACTION}{i["name"]}: its comment cites no source; name the reference of the '
                     f'amount (with its full reference in section 9 of the Dataset sheet, "Full references of the sources").')
            if point not in dataset.open_points:
                dataset.open_points.append(point)
        rows.append(_exchange(a, i['group'], i['name'], i['unitName'], amount, comment,
                              i['compartment'], i['subcompartment']))
    return rows


def property_rows(dataset):
    """Every product's basic properties (models/property_model.py); a
    product missing one is an open point."""
    a = dataset.activity
    rows = []
    for product in dataset.products:
        name = product['name']
        props = product_properties(dataset, product)
        missing = missing_basic(props)
        if missing:
            hint = {'live_weight': ' Give body_class, or the body composition (body_ebw, '
                                   'body_protein, body_fat, body_ash) with its source.',
                    'fibre': ' Give fibre_type, scoured_yield and grease_share with their sources.',
                    'milk': ' Give species, fat_pct and protein_pct with their sources.'}.get(
                product.get('product_type'), '') if set(missing) - {'price'} else ''
            point = (f'{ACTION}{name}: no {", no ".join(missing)}, neither given in section 6 (Products) of the Dataset sheet nor '
                     f'computable from the product\'s data and the tool\'s cited defaults; ecoinvent '
                     f'needs {"it" if len(missing) == 1 else "them"} for every product (carbon '
                     f'contents per kg of dry mass).{hint}')
            if point not in dataset.open_points:
                dataset.open_points.append(point)
        for prop, (amount, unit, comment, _) in props.items():
            rows.append({'activityName': a['activityName'], 'geography': a['geography'],
                         'group': product['group'], 'name': name, 'propertyName': prop,
                         'unitName': unit, 'amount': amount,
                         'comment': with_references(comment, project_references(a))})
    return rows


def _exchange(a, group, name, unit, amount, comment, compartment=None, subcompartment=None,
              pv=None):
    return {'activityName': a['activityName'], 'geography': a['geography'], 'group': group,
            'name': name, 'compartment': compartment, 'subcompartment': subcompartment,
            'unitName': unit, 'amount': amount,
            'comment': with_references(comment, project_references(a)), 'PV_amount': pv}


def route_label(route):
    return {Route.WFLDB: 'IPCC 2019 Refinement within the scope of the WFLDB v3.5 guidelines',
            Route.EU: 'IPCC 2019 for greenhouse gases and EMEP/EEA 2023 for air pollutants',
            Route.SALCA: 'SALCAanimal V1.0 as documented in Appendix 6 of Nemecek et al. (2024)'
            }[route]
