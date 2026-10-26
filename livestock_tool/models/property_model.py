"""The basic properties of every product, as ecoinvent needs them: dry mass,
carbon content (non-fossil and fossil, per kg of dry mass), water content
(per kg of dry mass), water in wet mass, wet mass and price.

In this order: a property given in the data collection (section 6, Properties, with its
source); else computed from the product's composition (section 6) or the cited default
of its species or fibre (tables/product_properties.py); else it is missing,
an open point. The price is never computed.
"""
from ..references import cited
from ..sources import ECOINVENT_MD
from ..tables import product_properties as pp
from .base import fmt
from .routing import country_of

BASIC = ('dry mass', 'carbon content, non-fossil', 'carbon content, fossil', 'price')


def species_of(dataset, product):
    if product.get('species'):
        return product['species']
    found = {pp.SPECIES.get(h['category']) for h in dataset.herd}
    return found.pop() if len(found) == 1 else None


def _milk(product, species):
    d = pp.MILK.get(species)
    if d is None:
        return None     # no composition for this species: lactose and ash unknown
    fat, protein = product.get('fat_pct'), product.get('protein_pct')
    lactose, ash = d['lactose'], d['ash']
    if fat is None and protein is None:
        fat, protein, solids = d['fat'], d['protein'], 100 - d['water']
        basis = f'total solids {fmt(solids)} g per 100 g (100 - water {d["water"]})'
        where = f'{pp.USDA_FDC.short}, {d["where"]}'
    else:
        fat, protein = fat if fat is not None else d['fat'], protein if protein is not None \
            else d['protein']
        solids = fat + protein + lactose + ash
        basis = (f'total solids {fmt(solids)} g per 100 g = fat {fmt(fat)} + protein {fmt(protein)} '
                 f'(given in the data collection) + lactose {fmt(lactose)} + ash {fmt(ash)}')
        where = f'lactose and ash: {pp.USDA_FDC.short}, {d["where"]}'
    carbon = (pp.C_FAT.value * fat + pp.C_PROTEIN.value * protein + pp.C_LACTOSE * lactose) / solids
    dm_text = f'{species} milk: {basis} ({where}) = {fmt(solids / 100)} kg per kg'
    c_text = (f'per kg dry mass: ({pp.C_FAT.value} x fat {fmt(fat)} + {pp.C_PROTEIN.value} x protein '
              f'{fmt(protein)} + {pp.C_LACTOSE:.3f} x lactose {fmt(lactose)}) / total solids '
              f'{fmt(solids)} = {fmt(carbon)} (carbon of fat, {pp.C_FAT.note}, and of protein, '
              f'{pp.C_PROTEIN.note}, as {pp.C_FAT.cite()}; lactose C12H22O11; {where})')
    return solids / 100, dm_text, carbon, c_text


def body_class_of(dataset, product):
    """The body class of a live-weight product: given in the data collection, else the
    default of the herd's category when the herd has one category."""
    if product.get('body_class'):
        return product['body_class']
    cats = {h['category'] for h in dataset.herd}
    return pp.DEFAULT_BODY_CLASS.get(cats.pop()) if len(cats) == 1 else None


def _live_weight(dataset, product, species):
    body = body_class_of(dataset, product)
    if body is not None and body not in pp.BODY:
        raise ValueError(f'{product["name"]}: body_class "{body}" is not one of '
                         f'{", ".join(pp.BODY)}')
    d = dict(pp.BODY.get(body) or {})
    given = {k: product.get(f'body_{k}') for k in ('ebw', 'protein', 'fat', 'ash')}
    if any(v is not None for v in given.values()):
        d.update({k: v for k, v in given.items() if v is not None})
        d['where'] = 'body composition given in the data collection' + (
            f', the rest {pp.BODY[body]["where"]}' if body in pp.BODY else '')
    if any(d.get(k) is None for k in ('ebw', 'protein', 'fat', 'ash')):
        return None
    dm = d['ebw'] * (d['protein'] + d['fat'] + d['ash'])
    c = d['ebw'] * (pp.C_PROTEIN.value * d['protein'] + pp.C_FAT.value * d['fat'])
    label = (body or species or 'animal').replace('_', ' ')
    gut = ('' if d['ebw'] >= 1 else '; the gut contents get no dry mass (no confirmed value)')
    dm_text = (f'{label}, live weight: empty body {fmt(d["ebw"])} kg per kg x (protein '
               f'{fmt(d["protein"])} + fat {fmt(d["fat"])} + ash {fmt(d["ash"])}) = {fmt(dm)} kg'
               f'{gut} ({d["where"]})')
    c_text = (f'per kg dry mass: {fmt(d["ebw"])} x ({pp.C_PROTEIN.value} x protein + '
              f'{pp.C_FAT.value} x fat) = {fmt(c)} kg C per kg live weight, / dry mass {fmt(dm)} = '
              f'{fmt(c / dm)} (carbon of protein, {pp.C_PROTEIN.note}, and fat, {pp.C_FAT.note}, as '
              f'{pp.C_FAT.cite()})')
    return dm, dm_text, c / dm, c_text


def _fibre(dataset, product):
    d = pp.FIBRE.get(product.get('fibre_type'))
    if d is None:
        return None
    r = d['raw_regain']
    dm = 1 / (1 + r.value)
    dm_text = (f'raw {product["fibre_type"]} at a regain of {fmt(r.value)} kg water per kg dry fibre '
               f'({r.cite()}, {r.note}): 1 / (1 + {fmt(r.value)}) = {fmt(dm)} kg per kg')
    sy, grease = product.get('scoured_yield'), product.get('grease_share')
    sy_src = grease_src = 'given in the data collection'
    if sy is None and product['fibre_type'] == 'wool':
        country = country_of(dataset.activity['geography'])
        if country in pp.WOOL_YIELD:
            sy, sy_src = pp.WOOL_YIELD[country], f'{pp.FAO_TCF.short}, {country}'
        else:
            sy, sy_src = pp.WOOL_YIELD_WORLD, 'world 2022, IWTO 2024, Wool Notes, p. 4'
    if grease is None and d.get('default_grease') is not None:
        grease, grease_src = d['default_grease'], f'typical, {pp.AWET.short}, Fig. 5.39'
    if sy is None or grease is None:
        return dm, dm_text, None, None
    fibre = sy / (1 + d['scoured_regain']) * (1 - d['scoured_residue'])
    c_raw = fibre * pp.C_KERATIN.value + grease * pp.C_GREASE.value
    c_text = (f'per kg dry mass: clean dry fibre {fmt(fibre)} kg per kg raw (scoured yield {fmt(sy)}, '
              f'{sy_src}, / {fmt(1 + d["scoured_regain"])}, less {fmt(d["scoured_residue"])} '
              f'residues; {d["where"]}) x {pp.C_KERATIN.value} kg C (keratin, {pp.C_KERATIN.note}) + '
              f'grease {fmt(grease)} kg ({grease_src}) x {pp.C_GREASE.value} kg C ({pp.C_GREASE.note}), as '
              f'{pp.C_KERATIN.cite()}: {fmt(c_raw)} kg C per kg raw, / dry mass {fmt(dm)} = '
              f'{fmt(c_raw / dm)}; suint and the organic part of the dirt are not counted (no '
              f'confirmed values), the vegetable matter is counted with the fibre')
    return dm, dm_text, c_raw / dm, c_text


def _eggs(product):
    e, s = pp.EGG['contents'], product.get('egg_shell_share') or pp.EGG['shell_share']
    contents = 1 - s
    dm_contents = contents * (100 - e['water']) / 100
    dm_shell = s * (pp.EGG['shell_caco3'] + pp.EGG['shell_matrix'])
    dm = dm_contents + dm_shell
    c_org = contents * (pp.C_PROTEIN.value * e['protein'] + pp.C_FAT.value * e['fat']
                        + pp.C_GLUCOSE * e['carbohydrate']) / 100 + \
        s * pp.EGG['shell_matrix'] * pp.C_PROTEIN.value
    c_shell = s * pp.EGG['shell_caco3'] * pp.C_CACO3
    shell_src = 'given in the data collection' if product.get('egg_shell_share') else '10-11 %, Nys et al. 2004'
    dm_text = (f'egg in shell: contents {fmt(contents)} kg x (100 - water {e["water"]}) / 100 + shell '
               f'{fmt(s)} kg ({shell_src}) x ({pp.EGG["shell_caco3"]} CaCO3 + {pp.EGG["shell_matrix"]} '
               f'organic matrix; the rest water) = {fmt(dm)} kg ({pp.EGG["where"]})')
    c_text = (f'per kg dry mass: contents {fmt(contents)} x ({pp.C_PROTEIN.value} x protein '
              f'{e["protein"]} + {pp.C_FAT.value} x fat {e["fat"]} + {pp.C_GLUCOSE:.3f} x carbohydrate '
              f'{e["carbohydrate"]}) / 100 + shell matrix x {pp.C_PROTEIN.value} = {fmt(c_org)} kg, '
              f'plus the shell carbonate {fmt(s)} x {pp.EGG["shell_caco3"]} x {pp.C_CACO3:.3f} = '
              f'{fmt(c_shell)} kg, biogenic (the hen builds it from blood bicarbonate, Long et al. '
              f'1983; ecoinvent counts the carbonate of limestone from algae as non-fossil), / dry '
              f'mass {fmt(dm)} = {fmt((c_org + c_shell) / dm)} (carbon of protein, {pp.C_PROTEIN.note}, '
              f'and fat, {pp.C_FAT.note}, as {pp.C_FAT.cite()}; carbohydrate as glucose)')
    return dm, dm_text, (c_org + c_shell) / dm, c_text


def product_properties(dataset, product):
    """{property: (amount, unit, comment, origin)} for one product, origin
    'given' or 'computed'; missing properties are left out."""
    name = product['name']
    out = {p['propertyName']: (p['amount'], p['unitName'], p['comment'], 'given')
           for p in dataset.properties if p['name'] == name}
    kind = product.get('product_type')
    species = species_of(dataset, product)
    found = (_milk(product, species) if kind == 'milk' else
             _live_weight(dataset, product, species) if kind == 'live_weight' else
             _fibre(dataset, product) if kind == 'fibre' else
             _eggs(product) if kind == 'eggs' else None)
    if found:
        dm, dm_text, c, c_text = found
        out.setdefault('dry mass', (dm, 'kg', dm_text[0].upper() + dm_text[1:] + '.', 'computed'))
        if c is not None:
            out.setdefault('carbon content, non-fossil',
                           (c, 'dimensionless', c_text[0].upper() + c_text[1:] + '.', 'computed'))
    if kind in ('milk', 'live_weight', 'fibre', 'eggs'):
        shell = (' The carbonate of an egg shell is biogenic too (Long et al. 1983).'
                 if kind == 'eggs' else '')
        out.setdefault('carbon content, fossil',
                       (0.0, 'dimensionless', f'Animal products hold biogenic carbon only, as in the '
                        f'{ECOINVENT_MD.short} (fossil carbon 0 for cow milk, sheep fleece in the grease '
                        f'and cattle, sheep, swine and chicken for slaughtering).{shell}', 'computed'))
    dm = out.get('dry mass')
    if dm is not None:
        v = dm[0]
        basis = '; '.join(cited(dm[2])) or 'given in the data collection'
        for prop, unit, value, how in (
                ('water in wet mass', 'kg', 1 - v, 'wet mass 1 kg less the dry mass'),
                ('water content', 'dimensionless', (1 - v) / v,
                 'water per kg dry mass, as ecoinvent defines it: (1 - dry mass) / dry mass'),
                ('wet mass', 'kg', 1.0, 'per kg of product as delivered')):
            out.setdefault(prop, (value, unit, f'Computed from the dry mass {fmt(v)} kg/kg ({basis}): '
                                               f'{how}.', 'computed'))
    return out


def missing_basic(props):
    return [k for k in BASIC if k not in props]

