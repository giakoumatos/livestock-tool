from ..tables import idf2022 as idf
from .base import fmt, pct


def dairy_allocation(dataset):
    """Milk/meat allocation of a dairy farm by IDF 2022 (Equation 4): the
    milk's share of the net energy for lactation and growth. Returns
    (factors by product name, explanation) or None when the dataset has no
    milk in FPCM and live weight with its animal class."""
    milk = [p for p in dataset.products if p.get('product_type') == 'milk' and p.get('fpcm_kg')]
    meat = [p for p in dataset.products if p.get('product_type') == 'live_weight']
    if not milk or not meat:
        return None
    for p in meat:
        if p.get('sold_class') not in idf.NEG_PER_KG_LW:
            raise ValueError(f'{dataset.name}, {p["name"]}: give sold_class '
                             f'({", ".join(idf.NEG_PER_KG_LW)}) for the IDF allocation')
    e_milk = sum(idf.NEL_PER_KG_FPCM.value * p['fpcm_kg'] for p in milk)
    e_meat = {p['name']: idf.NEG_PER_KG_LW[p['sold_class']].value * p['amount_per_year']
              for p in meat}
    total = e_milk + sum(e_meat.values())
    factors = {p['name']: idf.NEL_PER_KG_FPCM.value * p['fpcm_kg'] / total for p in milk}
    factors.update({name: e / total for name, e in e_meat.items()})
    parts = [f'{p["name"]}: {fmt(p["fpcm_kg"])} kg FPCM x {idf.NEL_PER_KG_FPCM.value} MJ/kg'
             for p in milk]
    parts += [f'{p["name"]}: {fmt(p["amount_per_year"])} kg live weight x '
              f'{idf.NEG_PER_KG_LW[p["sold_class"]].value} MJ/kg '
              f'({idf.NEG_PER_KG_LW[p["sold_class"]].note})' for p in meat]
    text = ('Milk and meat are allocated by the IDF method (IDF 2022, ' + idf.ALLOCATION_WHERE +
            '), the share of the net energy for lactation and growth, as WFLDB v3.5 asks for '
            'dairy farms (section 2.6.3): ' + '; '.join(parts) + '. Allocation factors: ' +
            ', '.join(f'{n} {pct(f)}' for n, f in factors.items()) + '.')
    return factors, text
