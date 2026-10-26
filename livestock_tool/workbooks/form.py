"""The Dataset sheet of the data collection workbook: a questionnaire in the
manner of the crop agritool's template, one sheet per dataset. Each row asks
one thing in plain words; column A (hidden) holds the row's key, by which
the sheet is read back into the records of workbooks/schema.py.

Columns: A key | B section number | C question | D unit | E needed |
F-M data: one cell (F:M merged) for a single answer, one column per animal
class (F-M), or one column per product (F-J, product 1 the reference
product) | N source of the value | O how to fill. The inputs of section 7
are a table with its own column headings.
"""
from dataclasses import dataclass

from ..models.model_enums import SYSTEMS
from .schema import CH, C, D, OPTIONAL, RECOMMENDED, REQUIRED, SHEETS

MARKER = 'livestock_dataset_form'       # cell A1 of every Dataset sheet
SINGLE, CLASSES, MANURE, PRODUCTS, INPUTS = 'single', 'classes', 'manure', 'products', 'inputs'
COL_KEY, COL_NO, COL_LABEL, COL_UNIT, COL_NEED, COL_DATA = 1, 2, 3, 4, 5, 6
N_CLASSES, N_PRODUCTS, N_INPUTS = 8, 5, 60
COL_SOURCE, COL_HELP = COL_DATA + N_CLASSES, COL_DATA + N_CLASSES + 1
# Section 7: the columns of the inputs table (field, heading, first and last column).
INPUT_COLUMNS = (
    ('name', 'ecoinvent name of the product or flow', 3, 3),
    ('unitName', 'Unit', 4, 4),
    ('group', 'Type', 5, 5),
    ('amount', 'Amount', 6, 6),
    ('basis', 'Basis', 7, 7),
    ('compartment', 'Compartment', 8, 8),
    ('subcompartment', 'Sub-compartment', 9, 9),
    ('water_use', 'Water use', 10, 10),
    ('comment', 'Source and how the amount was obtained', 11, 14),
)

# Product rows that become "properties" records: (property, unit row or unit).
PRICE, PRICE_UNIT, PRICE_COMMENT, PROPERTIES_SOURCE = \
    'price', 'price_unit', 'price_comment', 'properties_source'
PROPERTY_UNITS = {'dry mass': 'kg', 'carbon content, non-fossil': 'dimensionless',
                  'carbon content, fossil': 'dimensionless', 'water content': 'dimensionless',
                  'water in wet mass': 'kg', 'wet mass': 'kg'}
_PRODUCT_EXTRA = {
    PRICE: C(PRICE, REQUIRED, 'per kg', 'Price per kg of the product at the farm gate: it sets the '
             'economic allocation.', '47.71'),
    PRICE_UNIT: C(PRICE_UNIT, REQUIRED, '-', 'Currency of the price.', 'USD'),
    PRICE_COMMENT: D(PRICE_COMMENT, REQUIRED, 'text', 'Source of the price, always with its year.',
                     'Data provider, production year 2022-2023'),
    'dry mass': C('dry mass', OPTIONAL, 'kg/kg', 'Dry mass per kg of product.', '0.88'),
    'carbon content, non-fossil': C('carbon content, non-fossil', OPTIONAL, 'kg C/kg DM',
                                    'Biogenic carbon per kg of dry mass.', '0.50'),
    'carbon content, fossil': C('carbon content, fossil', OPTIONAL, 'kg C/kg DM',
                                'Fossil carbon per kg of dry mass (animal products: 0).', '0'),
    'water content': C('water content', OPTIONAL, 'kg/kg DM', 'Water per kg of dry mass.', '0.14'),
    'water in wet mass': C('water in wet mass', OPTIONAL, 'kg/kg', 'Water per kg of product.',
                           '0.12'),
    'wet mass': C('wet mass', OPTIONAL, 'kg/kg', 'Wet mass per kg of product (1).', '1'),
    PROPERTIES_SOURCE: D(PROPERTIES_SOURCE, OPTIONAL, 'text', 'Source of the properties given '
                         'above.'),
}


@dataclass(frozen=True)
class Row:
    field: str
    label: str
    source: str = ''        # the field its Source cell fills


@dataclass(frozen=True)
class Part:
    title: str
    note: str
    kind: str
    rows: tuple


@dataclass(frozen=True)
class Section:
    number: int
    title: str
    note: str
    parts: tuple


def R(field, label, source=''):
    return Row(field, label, source)


FORM = (
    Section(1, 'Dataset', '', (
        Part('', '', SINGLE, (
            R('activityName', 'Dataset name'),
            R('geography', 'Country or region (ISO code)'),
            R('startDate', 'First day of the data period'),
            R('endDate', 'Last day of the data period'),
            R('technologyLevel', 'Technology level'),
        )),
    )),
    Section(2, 'Location and climate', '', (
        Part('', '', SINGLE, (
            R('climate_zone', 'IPCC climate zone', 'climate_zone_source'),
            R('moisture', 'Wet or dry climate', 'moisture_source'),
            R('b0_region', 'Productivity class for manure methane (B0)', 'b0_region_source'),
        )),
        Part('Climate data', 'Only when the climate zone is left empty: the tool then places it by '
             'the IPCC decision tree.', SINGLE, (
            R('mat_c', 'Mean annual temperature', 'climate_data_source'),
            R('map_mm', 'Mean annual precipitation'),
            R('pet_mm', 'Mean annual potential evapotranspiration'),
            R('elevation_m', 'Elevation'),
            R('frost_days', 'Frost days a year'),
            R('warmest_month_c', 'Mean temperature of the warmest month'),
        )),
        Part('Tier 1 region', 'Only for animal classes with neither feed intake nor Tier 2 data.',
             SINGLE, (
            R('ipcc_region', 'IPCC region and productivity'),
        )),
    )),
    Section(3, 'Grazing', '', (
        Part('', '', SINGLE, (
            R('pasture_in_dataset', 'Does this dataset include the grazing land?'),
            R('irrigated_pasture', 'Is the pasture irrigated (other than by drip)?'),
        )),
    )),
    Section(4, 'Animal classes', 'One column per animal class (e.g. breeding does, kids, bucks), or '
            'one column "whole herd" when the data are for the whole herd.', (
        Part('Herd and feed', 'Every dataset.', CLASSES, (
            R('class_name', 'Name of the class'),
            R('category', 'Animal category'),
            R('head', 'Average number of animals present', 'head_source'),
            R('dmi_kg_day', 'Dry matter intake per animal and day', 'dmi_source'),
            R('dmi_kg_year_class', 'or: dry matter intake of the whole class in the year'),
            R('de_pct', 'Digestibility of the feed energy (DE)', 'de_source'),
            R('cp_pct', 'Crude protein of the ration', 'cp_source'),
            R('ash_frac', 'Ash content of the feed', 'ash_source'),
            R('housing_days', 'Days a year in buildings'),
        )),
        Part('Replace a default', 'Only with a measured or better value; empty = the cited default.',
             CLASSES, (
            R('ue_frac', 'Urinary energy, share of gross energy'),
            R('ym_pct', 'Methane conversion factor Ym', 'ym_source'),
            R('nex_kg_year', 'Nitrogen excreted per animal and year', 'nex_source'),
            R('grain_share', 'Grain share of the ration (ruminants)'),
        )),
        Part('Tier 2 gross energy', 'Only for classes without feed intake (IPCC 2019 Tier 2).',
             CLASSES, (
            R('weight_kg', 'Average live weight'),
            R('feeding_days', 'Days per feeding situation'),
            R('sex', 'Sex'),
            R('age_class', 'Age class (sheep)'),
            R('weight_start_kg', 'Live weight at weaning, or at the start of the stage'),
            R('weight_end_kg', 'Live weight at 1 year or at slaughter, or at the end of the stage'),
            R('milk_kg_day', 'Milk produced per animal and day'),
            R('weaning_gain_kg', 'Weight gained to weaning by the young of one female'),
            R('fibre_type', 'Fibre produced'),
            R('wool_kg_year', 'Wool per animal and year'),
            R('pregnant_share', 'Share of the class giving birth in the year'),
            R('offspring_per_birth', 'Young born per birth'),
            R('mature_weight_kg', 'Mature weight (cattle)'),
            R('weight_gain_kg_day', 'Daily weight gain (cattle)'),
        )),
        Part('Pigs and poultry', 'Sows, growing pigs, laying hens and broilers: the N kept in the '
             'animals and eggs.', CLASSES, (
            R('production_days', 'Days from start to end weight'),
            R('litter_size', 'Piglets born per litter'),
            R('farrowings_per_year', 'Farrowings per sow and year'),
            R('piglet_birth_kg', 'Piglet weight at birth'),
            R('piglet_weaning_kg', 'Piglet weight at weaning'),
            R('sow_weight_change_kg', 'Sow weight gained from farrowing to farrowing'),
            R('egg_g_day', 'Egg mass per hen and day'),
        )),
        Part('Cattle', 'Cattle and buffalo only.', CLASSES, (
            R('milk_fat_pct', 'Milk fat'),
            R('dmi_equation', 'Simplified Tier 2 intake equation (no intake data)'),
            R('nemf_mj_kg', 'Net energy for maintenance of the diet (NEmf)'),
            R('lactation_days', 'Days in milk a year (dairy cows)'),
            R('ym_class', 'Ym class (IPCC 2019 Table 10.12)'),
            R('ndf_pct', 'Neutral detergent fibre (NDF) of the ration'),
            R('forage_share', 'Forage share of the ration (non-dairy cattle)'),
        )),
        Part('EU only', 'EU-27 countries (EMEP/EEA 2023).', CLASSES, (
            R('silage_share_of_max', 'Silage fed, as a share of the maximum possible'),
            R('yard_share', 'Share of the N excreted on yards'),
            R('straw_kg_year', 'Bedding straw per animal and year (EU and Switzerland)'),
        )),
        Part('Switzerland only', 'SALCA: the time on pasture and yards takes the place of the manure '
             'shares of section 5.', CLASSES, (
            R('tied_housing', 'Tied housing (dairy cows)'),
            R('ge_mj_per_kg_dm', 'Gross energy of the ration'),
            R('pasture_days_spring', 'Days on pasture, March-May'),
            R('pasture_days_summer', 'Days on pasture, June-August'),
            R('pasture_days_autumn', 'Days on pasture, September-November'),
            R('pasture_days_winter', 'Days on pasture, December-February'),
            R('pasture_days', 'Days on pasture a year (animals other than cattle)'),
            R('pasture_hours', 'Hours on pasture on a grazing day'),
            R('yard_days', 'Days on the yard a year'),
            R('yard_hours', 'Hours on the yard on those days'),
            R('grazing_n_ratio', 'N in grazed feed / N in the ration (cattle)'),
            R('liquid_n_share', 'Share of the housing N in liquid manure'),
            R('lw_purchased_kg_year_class', 'Live weight bought in, per year'),
            R('lw_sold_kg_year_class', 'Live weight sold, per year'),
            R('lw_gain_kg_year_class', 'Change of the class\'s live weight, per year'),
            R('milk_kg_year_class', 'Milk produced by the class, per year'),
            R('eggs_kg_year_class', 'Eggs produced by the class, per year'),
        )),
    )),
    Section(5, 'Manure management', '', (
        Part('Share of the manure in each system', 'Each class column adds up to 1. Not used for '
             'Switzerland.', MANURE, tuple(R(k, s.label) for k, s in SYSTEMS.items())),
        Part('Storage details', 'Only for the systems used.', SINGLE, (
            R('mms_leaching', 'N leaching from manure management'),
            R('liquid_retention_months', 'Storage time of liquid manure'),
            R('crust_thick_dry', 'Thick, dry natural crust on the liquid storage?'),
            R('cover_ch4_reduction', 'CH4 reduction by the cover of the liquid storage'),
            R('digester_type', 'Anaerobic digester type'),
            R('frac_gas_digester', 'N volatilised from covered digestate'),
            R('daily_spread_type', 'Daily-spread manure: slurry or solid (EU)'),
        )),
        Part('Switzerland only', 'SALCA manure options.', SINGLE, (
            R('nh3_option', 'Ammonia factors: EEA or Agrammon'),
            R('liquid_crust_share', 'Share of liquid manure with a natural crust'),
            R('liquid_pit_share', 'Share of liquid manure in pits below the animals'),
            R('liquid_digester_share', 'Share of liquid manure going to biogas'),
            R('solid_compost_share', 'Share of solid manure composted'),
            R('solid_deep_bedding_share', 'Share of housed solid manure as deep bedding'),
        )),
    )),
    Section(6, 'Products', 'The first column is the reference product, the others by-products. '
            'Amounts are for the herd and the year.', (
        Part('Product', 'Every product.', PRODUCTS, (
            R('name', 'ecoinvent product name'),
            R('amount_per_year', 'Amount leaving the farm in the year'),
            R('product_type', 'Type of product'),
            R('comment', 'Source of the amount, and any conversion'),
            R('species', 'Species (only for a mixed herd)'),
        )),
        Part('Price', 'Every product: the economic allocation.', PRODUCTS, (
            R(PRICE, 'Price per kg'),
            R(PRICE_UNIT, 'Currency'),
            R(PRICE_COMMENT, 'Source and year of the price'),
        )),
        Part('Milk', 'Milk products.', PRODUCTS, (
            R('fat_pct', 'Fat'),
            R('protein_pct', 'True protein'),
        )),
        Part('Dairy live weight', 'Animals sold from a dairy herd (IDF allocation).', PRODUCTS, (
            R('sold_class', 'Class of the animals sold'),
        )),
        Part('Fibre', 'Fibre products: dry mass and carbon content.', PRODUCTS, (
            R('fibre_type', 'Fibre'),
            R('scoured_yield', 'Scoured fibre per kg of raw fibre'),
            R('grease_share', 'Grease per kg of raw fibre'),
        )),
        Part('Live weight', 'Animals sold: dry mass and carbon content. Empty = the default of the '
             'herd category\'s body class.', PRODUCTS, (
            R('body_class', 'Body class'),
            R('body_ebw', 'Empty body per kg of live weight'),
            R('body_protein', 'Protein per kg of empty body'),
            R('body_fat', 'Fat per kg of empty body'),
            R('body_ash', 'Ash per kg of empty body'),
        )),
        Part('Eggs', 'Eggs in shell: dry mass and carbon content.', PRODUCTS, (
            R('egg_shell_share', 'Shell per kg of egg in shell'),
        )),
        Part('Properties', 'Only to replace a property the tool computes. Carbon and water content '
             'per kg of dry mass, as ecoinvent defines them.', PRODUCTS, (
            R('dry mass', 'Dry mass'),
            R('carbon content, non-fossil', 'Carbon content, non-fossil'),
            R('carbon content, fossil', 'Carbon content, fossil'),
            R('water content', 'Water content'),
            R('water in wet mass', 'Water in wet mass'),
            R('wet mass', 'Wet mass'),
            R(PROPERTIES_SOURCE, 'Source of the properties given'),
        )),
    )),
    Section(7, 'Inputs and other exchanges', 'Everything the herd uses (feed, water, energy, '
            'materials, land) and emissions the models do not compute, one row each. Animal emissions '
            'are computed by the tool: do not enter them.', (
        Part('', '', INPUTS, ()),
    )),
    Section(8, 'Water', 'Only when water rows are entered in section 7.', (
        Part('', '', SINGLE, (
            R('water_release_compartment', 'Where the released water goes',
              'water_release_compartment_source'),
            R('water_release_share', 'Share of the animals\' water released', 'water_release_source'),
            R('irrigation_technique', 'Irrigation technique (fodder)'),
            R('irrigation_efficiency', 'Irrigation efficiency EFirr', 'irrigation_efficiency_source'),
        )),
    )),
    Section(9, 'Description of the dataset', 'Texts for the dataset documentation; no calculation '
            'reads them.', (
        Part('', '', SINGLE, (
            R('product_description', 'What 1 kg of the reference product is'),
            R('system_description', 'The production system'),
            R('technology_description', 'Herd management, feeding, housing and manure handling'),
            R('data_source', 'Kind of data'),
            R('data_source_reference', 'Reference of the data source'),
            R('farms_sampled', 'Number of farms sampled'),
            R('region_detail', 'Area the data refer to'),
            R('share_of_national_production', 'Share of the national production represented'),
            R('sampling_procedure', 'How the data were collected'),
            R('time_period_comment', 'How the data period was covered'),
            R('geography_comment', 'Which area the data represent'),
            R('allocation_basis', 'Prices: source and year, for the allocation comment'),
            R('yield_source', 'Where the product amounts come from'),
            R('price_source', 'Where the prices come from'),
            R('production_volume', 'Annual production in the geography', 'production_volume_comment'),
            R('pv_years', 'Years of the production volume'),
            R('references', 'Full references of the sources'),
            R('open_points', 'Open points and assumptions'),
        )),
    )),
)

_KIND_SHEET = {SINGLE: 'activity', CLASSES: 'herd', PRODUCTS: 'products'}
_FIELDS = {sheet: {c.name: c for c in cols} for sheet, cols in SHEETS.items()}


def column(kind, field):
    """The schema column of a form row."""
    if kind == MANURE:
        return _FIELDS['manure']['share']
    if kind == PRODUCTS and field in _PRODUCT_EXTRA:
        return _PRODUCT_EXTRA[field]
    return _FIELDS[_KIND_SHEET[kind]][field]


def source_column(kind, row):
    """The schema column the row's Source cell fills, if any."""
    if kind == MANURE:
        return _FIELDS['manure']['source']
    return _FIELDS[_KIND_SHEET[kind]][row.source] if row.source else None


def key(kind, field):
    return f'{kind}:{field}'


# Every keyed row of the form: key -> (kind, Row).
INDEX = {key(p.kind, r.field): (p.kind, r) for s in FORM for p in s.parts for r in p.rows}


def check_coverage():
    """Every field the reader returns has its row (or its place) on the
    form, once; raises otherwise, so a new schema column cannot be left
    out."""
    placed = {'activity': [], 'herd': ['activityName'],
              'products': ['activityName', 'group', 'unitName']}
    for kind, row in INDEX.values():
        column(kind, row.field)
        sheet = _KIND_SHEET.get(kind)
        if sheet and row.field not in _PRODUCT_EXTRA:
            placed[sheet].append(row.field)
        if row.source:
            source_column(kind, row)
            placed[sheet].append(row.source)
    problems = {s: {'missing': sorted(set(_FIELDS[s]) - set(p)),
                    'twice': sorted({f for f in p if p.count(f) > 1})} for s, p in placed.items()}
    problems = {s: {k: v for k, v in d.items() if v} for s, d in problems.items()}
    problems = {s: d for s, d in problems.items() if d}
    if problems:
        raise ValueError(f'Dataset sheet and schema disagree: {problems}')


def need_tag(need):
    """The short "Needed" text of a row."""
    base = {REQUIRED: 'Required', RECOMMENDED: 'Recommended', OPTIONAL: 'Optional', CH: 'CH only'}
    head, _, qualifier = need.partition(' (')
    head, _, extra = head.partition(', ')
    text = base.get(head, head[:1].upper() + head[1:])
    text = text.replace('Tier 2: if no intake', 'Tier 2').replace('Tier 1: if no intake data',
                                                                     'Tier 1')
    for part in (extra, qualifier.rstrip(')')):
        if part:
            text += f', {part}'
    return text


def read_sheet(ws):
    """The records of one Dataset sheet, values as entered (the reader
    types them): {'activity': {...}, 'herd': [...], 'manure': [...],
    'products': [...], 'properties': [...], 'inputs': [...]}."""
    cells = {values[0]: values for values in ws.iter_rows(max_col=COL_HELP, values_only=True)
             if isinstance(values[0], str) and ':' in values[0]}

    def data(k, i=0):
        return _blank(cells[k][COL_DATA - 1 + i]) if k in cells else None

    def source(k):
        return _blank(cells[k][COL_SOURCE - 1]) if k in cells else None

    a = {}
    for k, (kind, row) in INDEX.items():
        if kind == SINGLE:
            a[row.field] = data(k)
            if row.source:
                a[row.source] = source(k)
    name = a.get('activityName')

    classes = [i for i in range(N_CLASSES) if data(key(CLASSES, 'class_name'), i) is not None]
    herd = []
    for i in classes:
        h = {'activityName': name}
        for k, (kind, row) in INDEX.items():
            if kind == CLASSES:
                h[row.field] = data(k, i)
                if row.source:
                    h[row.source] = source(k)
        herd.append(h)
    manure = [{'activityName': name, 'class_name': h['class_name'], 'system': row.field,
               'share': data(k, i), 'source': source(k)}
              for k, (kind, row) in INDEX.items() if kind == MANURE
              for h, i in zip(herd, classes) if data(k, i) is not None]

    used = [i for i in range(N_PRODUCTS) if data(key(PRODUCTS, 'name'), i) is not None]
    if used and used[0] != 0:
        raise ValueError(f'{name}: the reference product (first product column) has no name')
    products, properties = [], []
    for i in used:
        p = {'activityName': name, 'group': 'ReferenceProduct' if i == 0 else 'ByProduct',
             'unitName': 'kg'}
        extra = {}
        for k, (kind, row) in INDEX.items():
            if kind == PRODUCTS:
                (extra if row.field in _PRODUCT_EXTRA else p)[row.field] = data(k, i)
        products.append(p)
        for prop in (PRICE,) + tuple(PROPERTY_UNITS):
            if extra.get(prop) is not None:
                properties.append({
                    'activityName': name, 'name': p['name'], 'propertyName': prop,
                    'unitName': extra[PRICE_UNIT] if prop == PRICE else PROPERTY_UNITS[prop],
                    'amount': extra[prop],
                    'comment': extra[PRICE_COMMENT] if prop == PRICE else extra[PROPERTIES_SOURCE]})

    inputs = []
    for n in range(1, N_INPUTS + 1):
        values = cells.get(key(INPUTS, n))
        if values:
            row = {f: _blank(values[c - 1]) for f, _, c, _ in INPUT_COLUMNS}
            if any(v is not None for v in row.values()):
                inputs.append({'activityName': name, **row})
    return {'activity': a, 'herd': herd, 'manure': manure, 'products': products,
            'properties': properties, 'inputs': inputs}


def _blank(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value
