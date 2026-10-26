from ..sources import ECOINVENT_DQG
from ..tables import wfldb35 as wfldb
from ..workbooks.input_reader import ACTION
from .base import fmt, pct
from .property_model import product_properties
from .routing import country_of

# ecoinvent data quality guideline v3: water inputs are balanced by outputs
# to the environment (section 6.6, p. 47); where the destination is not
# known, the output goes to "water, unspecified" (same section); emissions
# from agriculture go to "non-urban air or from high stacks" (Table 9.1,
# p. 62-63).
DQG = ECOINVENT_DQG.short
AIR = ('air', 'non-urban air or from high stacks')
UNSPECIFIED = ('water', 'unspecified')
SURFACE = ('water', 'surface water')
GROUND = ('water', 'ground-')


def _withdrawn(dataset, use):
    """m3 withdrawn a year for `use`. Rows given per kg of the reference
    product are scaled to the herd's year, so the balance counts them too."""
    rows = [i for i in dataset.inputs if i['group'] == 'FromEnvironment'
            and str(i['name']).startswith('Water') and (i.get('water_use') or 'animals') == use]
    per_kg = [r for r in rows if r['basis'] == 'per_kg']
    ref_amount = dataset.amount(dataset.reference_product()) if per_kg else 0.0
    if per_kg:
        point = (f'{ACTION}{"; ".join(r["name"] for r in per_kg)} ({use}) given per kg of the '
                 f'reference product: scaled to the herd\'s year with its {fmt(ref_amount)} kg for '
                 f'the water balance. Check the basis in section 7 of the Dataset sheet.')
        if point not in dataset.open_points:
            dataset.open_points.append(point)
    total = sum(r['amount'] * (ref_amount if r['basis'] == 'per_kg' else 1) for r in rows)
    return total, bool(rows)


def _product_water(dataset):
    """m3 of water leaving in the products a year (their wet mass less the
    dry mass, at 1000 kg/m3), or None when a product has no dry mass."""
    total = 0.0
    for p in dataset.products:
        dm = product_properties(dataset, p).get('dry mass')
        if dm is None:
            return None
        total += dataset.amount(p) * (1 - dm[0]) / 1000
    return total


def water_balance(dataset):
    """The water outputs of the herd and the year, as {(compartment,
    subcompartment): (m3, [comment parts])}.

    Animals (drinking and cleaning water): WFLDB v3.5, 3.5.5 counts 83 %
    consumed and 17 % released when no data are given (Shaffer 2008, whose
    "consumed" is water evaporated, transpired or incorporated into
    products). The release goes to water, unspecified (ecoinvent DQG 6.6:
    destination not known; urine and dung reach soil, ground and surface
    water, cleaning water is discharged), unless the data collection names
    the compartment; the consumed water less the water in the products is
    evaporated, to non-urban air.
    Fodder irrigation: WFLDB v3.5, 3.5.4, to air withdrawal x EFirr, the rest
    80 % to surface water and 20 % to ground water; EFirr given, or from
    the technique (Tab. 4).
    """
    a = dataset.activity
    out = {}

    def add(key, amount, text):
        m3, parts = out.get(key, (0.0, []))
        out[key] = (m3 + amount, parts + [text])

    animals, has_animals = _withdrawn(dataset, 'animals')
    if has_animals:
        share = a.get('water_release_share')
        share_text = (f'{pct(share)} released ({a.get("water_release_source") or "data collection"})'
                      if share is not None else
                      f'{pct(wfldb.WATER_RELEASED.value)} released, the WFLDB default when no data '
                      f'are given ({wfldb.WATER_RELEASED.cite()}, {wfldb.WATER_RELEASED.note})')
        share = wfldb.WATER_RELEASED.value if share is None else share
        target = a.get('water_release_compartment')
        if target:
            key = tuple(s.strip() for s in target.split('/'))
            where = a.get('water_release_compartment_source') or 'data collection'
        else:
            key = UNSPECIFIED
            where = (f'water, unspecified, as the ecoinvent rule for water whose destination is not '
                     f'known ({DQG}, section 6.6, p. 47): urine and dung reach soil, ground and '
                     f'surface water and the cleaning water is discharged')
        released = animals * share
        add(key, released, f'animals: {fmt(animals)} m3 of drinking and cleaning water withdrawn a '
                           f'year, {share_text}: {fmt(released)} m3; compartment: {where}')
        consumed = animals - released
        product_water = _product_water(dataset)
        if product_water is None:
            evaporated = consumed
            note = ('the water in the products is not subtracted, as a product has no dry mass')
            point = (f'{ACTION}The water leaving in the products is not subtracted from the water '
                     f'evaporated, as a product has no dry mass (section 6 (Products) of the Dataset sheet).')
            if point not in dataset.open_points:
                dataset.open_points.append(point)
        else:
            evaporated = max(0.0, consumed - product_water)
            note = (f'less {fmt(product_water)} m3 leaving in the products (their wet mass less '
                    f'their dry mass)')
        add(AIR, evaporated, f'animals: the {fmt(consumed)} m3 consumed ({pct(1 - share)}), '
                             f'{note}: {fmt(evaporated)} m3 evaporated ({DQG}, section 6.6, p. 47; '
                             f'agriculture to non-urban air, Table 9.1, p. 62)')

    irrigation, has_irrigation = _withdrawn(dataset, 'irrigation')
    if has_irrigation:
        ef_given, technique = a.get('irrigation_efficiency'), a.get('irrigation_technique')
        if ef_given is not None:
            ef, ef_text = ef_given, (f'EFirr {fmt(ef_given)} '
                                     f'({a.get("irrigation_efficiency_source") or "data collection"})')
        elif technique in wfldb.IRRIGATION_EFFICIENCY:
            f = wfldb.IRRIGATION_EFFICIENCY[technique]
            ef, ef_text = f.value, f'EFirr {fmt(f.value)} ({f.note}, {f.cite()})'
        elif wfldb.irrigation_efficiency(country_of(a['geography'])):
            ef, words = wfldb.irrigation_efficiency(country_of(a['geography']))
            ef_text = (f'EFirr {fmt(ef)}, technique not given: the country mix of WFLDB v3.5, '
                       f'{words}')
        else:
            dataset.open_points.append(
                f'{ACTION}{fmt(irrigation)} m3 of irrigation water a year has no outputs: the '
                f'technique is not given and WFLDB v3.5 Tab. 34 has no shares for '
                f'{country_of(a["geography"])}; give the irrigation technique or the irrigation '
                f'efficiency in section 8 (Water) of the Dataset sheet (WFLDB v3.5, sections 3.5.2 and 3.5.4).')
            return out
        s = wfldb.IRRIGATION_SURFACE_SHARE.value
        base = f'irrigation: {fmt(irrigation)} m3 withdrawn a year, {ef_text}'
        rule = wfldb.IRRIGATION_SURFACE_SHARE.cite()
        add(AIR, irrigation * ef, f'{base}: {fmt(irrigation * ef)} m3 evapotranspired ({rule})')
        add(SURFACE, irrigation * (1 - ef) * s,
            f'{base}: {pct(s)} of the {fmt(irrigation * (1 - ef))} m3 not taken up = '
            f'{fmt(irrigation * (1 - ef) * s)} m3 ({rule})')
        add(GROUND, irrigation * (1 - ef) * (1 - s),
            f'{base}: {pct(1 - s)} of the {fmt(irrigation * (1 - ef))} m3 not taken up = '
            f'{fmt(irrigation * (1 - ef) * (1 - s))} m3 ({rule})')
    return out
