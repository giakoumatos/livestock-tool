"""The fields of the livestock data collection: for each record the reader
returns (activity, herd class, manure share, product, property, input),
every field with when it is needed, its unit, what to enter, an example
and, for a closed list, the allowed values (a dropdown in the template).
workbooks/form.py places them on the Dataset sheet and words its questions.

Fields made with C() are calculation inputs: the models, the per-kg
division, the properties, the allocation or the water rows read them.
Fields made with D() are documentation: dataset texts and the sources of
the values, which go into the meta fields and the comments but into no
calculation.
"""
from dataclasses import dataclass

from ..models.model_enums import CATEGORIES, FEEDING_SITUATIONS_CATTLE, \
    FEEDING_SITUATIONS_SHEEP_GOATS, SYSTEMS
from ..tables.ipcc2019 import CLIMATE_ZONES, DIGESTER_TYPES, DMI_EQUATIONS, IPCC_REGIONS, \
    YM_CATTLE, _B0_COLUMNS
from ..tables.idf2022 import NEG_PER_KG_LW
from ..tables.product_properties import BODY, FIBRE, SPECIES

REQUIRED = 'required'
TIER2 = 'Tier 2: if no intake'
TIER1 = 'Tier 1: if no intake data'
CATTLE = 'cattle'
DAIRY = 'dairy'
EU = 'EU only'
CH = 'CH only'
CLIMATE = 'if no climate zone'
FIBRE_PRODUCT = 'fibre products'
LIVE_WEIGHT = 'live weight products'
DIGESTER = 'if digester'
IF_WATER = 'if water'
ENVIRONMENT = 'environment rows'
RECOMMENDED = 'recommended'
OPTIONAL = 'optional'
NEEDS = (REQUIRED, CLIMATE, TIER2, TIER1, CATTLE, DAIRY, FIBRE_PRODUCT, LIVE_WEIGHT, EU, CH,
         DIGESTER, IF_WATER, ENVIRONMENT, RECOMMENDED, OPTIONAL)
YES_NO = ('yes', 'no')


@dataclass(frozen=True)
class Column:
    name: str
    need: str
    unit: str
    text: str
    example: str = ''
    choices: tuple = ()
    doc: bool = False


def C(name, need, unit, text, example='', choices=()):
    """A calculation input."""
    return Column(name, need, unit, text, example, tuple(choices))


def D(name, need, unit, text, example='', choices=()):
    """Documentation: a dataset text or the source of a value."""
    return Column(name, need, unit, text, example, tuple(choices), doc=True)


_FEED = FEEDING_SITUATIONS_SHEEP_GOATS + FEEDING_SITUATIONS_CATTLE

SHEETS = {
    'activity': (
        C('activityName', REQUIRED, '-', 'Lowercase: animal + "production", then the system.',
          'cashmere goat production, farmed'),
        C('geography', REQUIRED, '-', 'ISO country code or ecoinvent region. It decides the method set: '
          'CH -> SALCA; EU-27 -> IPCC 2019 + EMEP/EEA 2023; any other -> WFLDB v3.5 with IPCC 2019.',
          'CN-NM'),
        D('startDate', REQUIRED, 'yyyy-mm-dd', 'First day of the data period.', '2022-09-01'),
        D('endDate', REQUIRED, 'yyyy-mm-dd', 'Last day of the data period.', '2023-08-31'),
        D('technologyLevel', OPTIONAL, '-', 'Empty = Current.', 'Current',
          ('Current', 'Modern', 'Old', 'Outdated', 'New', 'Undefined')),
        C('climate_zone', REQUIRED + ' (or the climate data)', '-', 'IPCC climate zone (IPCC 2019, '
          'Vol. 4, Ch. 10, Annex 10A.2). Sets the manure MCF. Empty: placed from the climate data '
          'below by the IPCC decision tree (Vol. 4, Ch. 3, Figure 3A.5.2).', 'cool_temperate_dry',
          CLIMATE_ZONES),
        D('climate_zone_source', RECOMMENDED, '-', 'Where the climate zone comes from.'),
        C('moisture', RECOMMENDED, '-', 'wet or dry by IPCC 2019 Ch. 11 (temperate/boreal: annual '
          'precipitation/PET above or below 1; tropical: above or below 1000 mm). Sets EF4, EF3PRP of '
          'cattle, pigs and poultry, and N leaching. Empty: from the climate zone (Table 11.1, fn 4).',
          'dry', ('wet', 'dry')),
        C('mat_c', CLIMATE, 'deg C', 'Mean annual temperature.', '4.5'),
        C('map_mm', CLIMATE, 'mm/year', 'Mean annual precipitation.', '350'),
        C('pet_mm', CLIMATE, 'mm/year', 'Mean annual potential evapotranspiration (outside the '
          'tropics).', '700'),
        C('elevation_m', CLIMATE, 'm', 'Elevation (tropics: montane above 1000 m).'),
        C('frost_days', CLIMATE, 'days/year', 'Days of frost a year (tropics: at most 7).'),
        C('warmest_month_c', CLIMATE, 'deg C', 'Mean temperature of the warmest month (below 0 '
          'deg C mean annual temperature: boreal or polar).'),
        D('climate_data_source', CLIMATE, 'text', 'Source and period of the climate data.'),
        D('moisture_source', RECOMMENDED, '-', 'Where the wet/dry class comes from.'),
        C('b0_region', REQUIRED + ' (not CH)', '-', 'Column of IPCC 2019 Table 10.16A for B0. For '
          'other regions IPCC takes low productivity as the default (fn 1).', 'other_low',
          _B0_COLUMNS),
        D('b0_region_source', RECOMMENDED, '-', 'Why that column (written in the manure methane '
          'comment).'),
        C('ipcc_region', TIER1, '-', 'Region and productivity column of IPCC 2019 Tables 10.13A and '
          '10.19 (and Table 10.10: high productivity in North America, Europe and Oceania), for '
          'classes without intake data.', 'asia_low', IPCC_REGIONS),
        C('pasture_in_dataset', REQUIRED, 'yes/no', 'yes when this dataset occupies the grazing land '
          '(the excreta emissions are then included); no when pasture is bought in.', 'yes', YES_NO),
        C('irrigated_pasture', OPTIONAL, 'yes/no', 'yes if pasture is irrigated other than by drip (N '
          'leaching then applies in a dry climate).', 'no', YES_NO),
        C('mms_leaching', OPTIONAL, '-', 'N leaching from manure management: ipcc (empty: IPCC 2019 '
          'Table 10.22 on every system; IPCC: uncovered manure without runoff containment) or wfldb '
          '(liquid/slurry and solid storage only, WFLDB v3.5 section 3.9.5.2).', 'ipcc',
          ('ipcc', 'wfldb')),
        C('daily_spread_type', EU, '-', 'Whether daily-spread manure is slurry or solid (EMEP/EEA '
          'Step 8); empty = solid.', 'solid', ('slurry', 'solid')),
        C('liquid_retention_months', OPTIONAL, 'months', 'Liquid/slurry and pit storage: 1, 3, 4, 6 or '
          '12; empty = 6 (IPCC 2019 Table 10.17, fn 1).', '6', ('1', '3', '4', '6', '12')),
        C('crust_thick_dry', OPTIONAL, 'yes/no', 'Liquid storage with natural crust: yes only for a '
          'thick, dry crust (MCF less 40 %, IPCC 2019 Table 10.17, fn 1).', 'no', YES_NO),
        C('cover_ch4_reduction', OPTIONAL, 'fraction', 'Liquid storage with cover: CH4 reduction of '
          'the solid cover, 0.25-0.50 by IPCC 2019 Table 10.17 fn 1; empty = no reduction.', '0.25'),
        C('digester_type', DIGESTER, '-', 'Anaerobic digester: leakage, technology and digestate '
          'storage (IPCC 2019 Table 10.17); open storage = uncovered digestate.',
          'low_leak_open_storage', DIGESTER_TYPES),
        C('frac_gas_digester', DIGESTER, 'fraction', 'Covered (gastight) digestate storage: N '
          'volatilised, 0.05-0.50 (IPCC 2019 Table 10.22, fn 3); open storage takes the liquid '
          'slurry value.', '0.10'),
        D('product_description', REQUIRED, 'text', 'What 1 kg of the reference product is, and its '
          'destination (generalComment).',
          'This dataset represents the production of 1 kg of raw (greasy) cashmere ...'),
        D('system_description', REQUIRED, 'text', 'The production system in a few sentences, with '
          'the source (generalComment).'),
        D('technology_description', REQUIRED, 'text', 'Herd management, feeding, housing and manure '
          'handling (technologyComment).'),
        D('data_source', REQUIRED, '-', 'Kind of data.', 'field', ('field', 'statistical', 'literature')),
        D('data_source_reference', REQUIRED, 'text', 'Full reference of the data source.'),
        D('farms_sampled', RECOMMENDED, 'number', 'Number of farms, if from a survey.', '60'),
        D('region_detail', RECOMMENDED, 'text', 'The narrower area the data refer to.'),
        D('share_of_national_production', RECOMMENDED, '%', 'Share of the national production '
          'represented.', '46'),
        D('sampling_procedure', REQUIRED, 'text', 'How the data were collected '
          '(samplingProcedure).'),
        D('time_period_comment', REQUIRED, 'text', 'How the period was covered (timePeriodComment).'),
        D('geography_comment', REQUIRED, 'text', 'Which area the data represent (geographyComment).'),
        D('allocation_basis', RECOMMENDED, 'text', 'Source and year of the prices, for '
          'allocationComment.'),
        D('yield_source', RECOMMENDED, 'text', 'Where the product amounts come from, as cited.'),
        D('price_source', RECOMMENDED, 'text', 'Where the prices come from, as cited.'),
        D('production_volume', RECOMMENDED, 'kg/year', 'Annual production of the reference product in '
          'the geography (not the herd\'s).'),
        D('production_volume_comment', RECOMMENDED, 'text', 'Source and year of the production volume.'),
        D('pv_years', RECOMMENDED, 'years', 'Years the production volume refers to.', '2020-2022'),
        C('water_release_compartment', OPTIONAL, '-', 'Where the released '
          'share of the animals\' water goes, if known; empty = water/unspecified (ecoinvent data '
          'quality guideline v3, section 6.6: destination not known).', 'water/unspecified',
          ('water/unspecified', 'water/surface water', 'water/ground-')),
        D('water_release_compartment_source', IF_WATER, 'text', 'Why that compartment.'),
        C('water_release_share', OPTIONAL, 'fraction', 'Share of the animals\' water released; empty = '
          '0.17 (WFLDB v3.5, section 3.5.5).', '0.17'),
        D('water_release_source', OPTIONAL, 'text', 'Source of a release share given here.'),
        C('irrigation_technique', IF_WATER, '-', 'Fodder irrigation (inputs with water_use '
          'irrigation): the technique, for EFirr (WFLDB v3.5, Tab. 4).', 'surface',
          ('surface', 'sprinkler', 'drip')),
        C('irrigation_efficiency', IF_WATER, 'fraction', 'Fodder irrigation: EFirr, the share '
          'evapotranspired, if known or a mix of techniques (it replaces irrigation_technique).',
          '0.48'),
        D('irrigation_efficiency_source', IF_WATER, 'text', 'Source of the EFirr given here.'),
        C('nh3_option', CH, '-', 'The SALCA ammonia option: EEA 2019 or Agrammon 2022 factors.',
          'Agrammon', ('EEA', 'Agrammon')),
        C('liquid_crust_share', CH, 'fraction', 'Share of liquid manure stored with a natural crust.'),
        C('liquid_pit_share', CH, 'fraction', 'Share of liquid manure in pit storage below the '
          'animals.'),
        C('liquid_digester_share', CH, 'fraction', 'Share of liquid manure going to biogas.'),
        C('solid_compost_share', CH, 'fraction', 'Share of solid manure composted.'),
        C('solid_deep_bedding_share', CH, 'fraction', 'Share of housed solid manure as deep bedding.'),
        D('references', RECOMMENDED, 'text', 'Full references of the project\'s own sources, one per '
          'line as "short name = full reference" (e.g. "Smith et al. 2024 = Smith J. (2024) Title. '
          'Journal 1, 1-10."); every comment that cites the short name ends with the full one.'),
        D('open_points', OPTIONAL, 'text', 'Assumptions made while filling this workbook, one per '
          'line; they are listed with the run\'s open points. Start a line with "ACTION: " when '
          'it still needs a choice or data.'),
    ),
    'herd': (
        C('activityName', REQUIRED, '-', 'As on "activity".'),
        C('class_name', REQUIRED, '-', 'Animal class; "whole herd" when the data are for the herd.',
          'breeding does'),
        C('category', REQUIRED, '-', 'Animal category; it selects the rows of the IPCC and EMEP/EEA '
          'tables.', 'goats', tuple(CATEGORIES)),
        C('head', REQUIRED, 'head', 'Average number of animals present in the year (AAP).', '171'),
        D('head_source', RECOMMENDED, 'text', 'Source of the number of animals.'),
        C('dmi_kg_day', REQUIRED + ' (or Tier 2 / Tier 1)', 'kg DM/(head*day)', 'Dry matter intake. '
          'When given, gross energy = DMI x 18.45 MJ/kg; otherwise IPCC 2019 Tier 2 from the Tier 2 '
          'columns, the simplified Tier 2 intake (cattle, dmi_equation) or Tier 1 (ipcc_region). '
          'CH: always needed.', '0.95'),
        C('dmi_kg_year_class', OPTIONAL, 'kg DM/year', 'Alternative: dry matter intake of the whole '
          'class in the year.', '136689'),
        D('dmi_source', RECOMMENDED, 'text', 'Source of the intake.'),
        C('de_pct', REQUIRED, '% of GE', 'Digestibility of the feed energy.', '63'),
        D('de_source', RECOMMENDED, 'text', 'Source of the digestibility.'),
        C('cp_pct', REQUIRED, '% of DM', 'Crude protein of the ration: it sets the N intake and '
          'excretion.', '11'),
        D('cp_source', RECOMMENDED, 'text', 'Source of the crude protein.'),
        C('ash_frac', REQUIRED, 'fraction of DM', 'Ash of the feed (IPCC 2019 Eq. 10.24; e.g. 0.06 for '
          'sows).', '0.08'),
        D('ash_source', RECOMMENDED, 'text', 'Source of the ash content.'),
        C('housing_days', RECOMMENDED, 'days/year', 'Days in buildings; empty = 365 x the share of the '
          'manure not on pasture.', '155'),
        C('ue_frac', OPTIONAL, 'fraction of GE', 'Urinary energy; empty = 0.04 for ruminants, 0.02 for '
          'pigs (IPCC 2019 Eq. 10.24); poultry and horses must give it.', '0.04'),
        C('ym_pct', OPTIONAL, '% of GE', 'Ym; empty = IPCC 2019 Table 10.13 (sheep 6.7, goats 5.5), '
          'Table 10.12 (cattle, by class) or WFLDB Tab. 10 (pigs, horses, poultry).', '5.5'),
        D('ym_source', OPTIONAL, 'text', 'Source of a Ym given here.'),
        C('nex_kg_year', OPTIONAL, 'kg N/(head*year)', 'N excreted, if measured; empty = IPCC 2019 '
          'Eq. 10.31.', ''),
        D('nex_source', OPTIONAL, 'text', 'Source of a Nex given here.'),
        C('grain_share', OPTIONAL, 'fraction', 'Ruminants: grain share of the ration (UE 0.02 at 0.85 '
          'or more).'),
        C('weight_kg', TIER2, 'kg', 'Average live weight (Tier 1: the typical animal mass, TAM).',
          '36'),
        C('feeding_days', TIER2, 'situation:days; ...', 'Days per feeding situation (IPCC 2019 Table '
          '10.5), adding up to 365: ' + ', '.join(_FEED) + '.',
          'lowland_goats:210; housed_fattening_lambs:155'),
        C('sex', TIER2, '-', 'For NEm and NEg.', 'female', ('female', 'intact_male', 'castrate')),
        C('age_class', TIER2, '-', 'Sheep: lamb to 1 year or adult (Table 10.4).', 'adult',
          ('young', 'adult')),
        C('weight_start_kg', TIER2, 'kg', 'Sheep/goats growing: live weight at weaning (Eq. 10.7). '
          'Growing pigs, broilers: live weight at the start of the stage (N retention, Eq. 10.33C, '
          '10.33E).'),
        C('weight_end_kg', TIER2, 'kg', 'Sheep/goats growing: live weight at 1 year or at slaughter. '
          'Growing pigs, broilers: at the end of the stage.'),
        C('production_days', OPTIONAL, 'days', 'Growing pigs, broilers: days from start to end '
          'weight (N retention per day).', '110'),
        C('litter_size', OPTIONAL, 'piglets', 'Sows: piglets born per litter (Eq. 10.33A-B).', '9.2'),
        C('farrowings_per_year', OPTIONAL, '1/year', 'Sows: farrowings per sow and year.', '2.1'),
        C('piglet_birth_kg', OPTIONAL, 'kg', 'Sows: live weight of a piglet at birth.', '1.2'),
        C('piglet_weaning_kg', OPTIONAL, 'kg', 'Sows: live weight of a piglet at weaning.', '7.0'),
        C('sow_weight_change_kg', OPTIONAL, 'kg', 'Sows: live weight gained from farrowing to '
          'farrowing (Table 10.20A example: 12.5).', '12.5'),
        C('egg_g_day', OPTIONAL, 'g/(head*day)', 'Laying hens: egg mass laid per hen and day (N '
          'retention, Eq. 10.33D).', '55'),
        C('milk_kg_day', TIER2, 'kg/(head*day)', 'Milk produced, averaged over the whole class and '
          'the year (NEl; cattle: also the Table 10.12 row from milk x 365).'),
        C('weaning_gain_kg', TIER2, 'kg', 'Sheep/goats whose milk is not known: weight gained to '
          'weaning by the young of one female giving birth (Eq. 10.10; weighted by pregnant_share).',
          '12'),
        C('fibre_type', TIER2, '-', 'Fibre: cashmere and angora goats and fibre sheep use IPCC\'s '
          'NEwool per day; wool uses 24 MJ/kg (Eq. 10.12).', 'cashmere',
          ('cashmere', 'angora', 'sheep_fibre', 'wool')),
        C('wool_kg_year', TIER2, 'kg/(head*year)', 'fibre_type wool: wool per head (CH: also the N '
          'balance).'),
        C('pregnant_share', TIER2, 'fraction', 'Share of the class giving birth in the year.', '0.9'),
        C('offspring_per_birth', TIER2, 'young/birth', 'Young born per female giving birth.', '1.1'),
        C('mature_weight_kg', TIER2 + ', cattle', 'kg', 'Mature weight (Eq. 10.6).'),
        C('weight_gain_kg_day', TIER2 + ', cattle', 'kg/day', 'Daily weight gain (Eq. 10.6).'),
        C('milk_fat_pct', CATTLE, '%', 'Milk fat (NEl, Eq. 10.8; N in milk, Eq. 10.33).', '4.0'),
        C('dmi_equation', CATTLE, '-', 'Cattle without intake or Tier 2 data: the simplified Tier 2 '
          'intake (IPCC 2019 Eq. 10.17-10.18B, Table 10.8).', 'growing_cattle', DMI_EQUATIONS),
        C('nemf_mj_kg', CATTLE, 'MJ/kg DM', 'Calves, growing cattle: NEmf of the diet (Table 10.8A); '
          'empty = REM x 18.45 x DE.', '6.0'),
        C('lactation_days', DAIRY, 'days/year', 'Dairy cows: days in milk a year (Cfi 0.386 while '
          'lactating, 0.322 when dry, Table 10.4).', '305'),
        C('ym_class', CATTLE, '-', 'Row of IPCC 2019 Table 10.12; empty = chosen from milk yield, DE, '
          'NDF or forage share.', 'dairy_medium', tuple(YM_CATTLE)),
        C('ndf_pct', CATTLE, '% of DMI', 'NDF (IPCC 2019 Table 10.12, dairy above 8,500 kg milk; CH: dairy '
          'cows at DE >= 70 %, SALCA Tab. 1 "raw fibre", which is this NDF).', '33'),
        C('forage_share', CATTLE, 'fraction', 'Non-dairy cattle: forage share of the ration (Table '
          '10.12).', '0.8'),
        C('silage_share_of_max', EU, 'fraction', 'NMVOC: silage fed as a share of the maximum '
          'possible; 0 if no silage.', '0.5'),
        C('yard_share', EU, 'fraction', 'Share of N excreted on yards; empty = EMEP/EEA 2023 Step 3 '
          '(dairy 0.25, other cattle 0.10, sheep 0.02).'),
        C('straw_kg_year', EU + ', CH', 'kg/(head*year)', 'Bedding straw the class uses, per head '
          'and year. EU empty = EMEP/EEA 2023 Table 3-7 (per head on litter, scaled to the '
          'litter-based share and the housing days).', '20'),
        C('tied_housing', CH, 'yes/no', 'Dairy cows in tied housing (SALCA group).', 'no', YES_NO),
        C('ge_mj_per_kg_dm', CH, 'MJ/kg DM', 'Gross energy of the ration; empty = 18.45 (IPCC 2019).'),
        C('pasture_days_spring', CH, 'days', 'Days on pasture in March-May (cattle: SALCA Tab. 10).'),
        C('pasture_days_summer', CH, 'days', 'Days on pasture in June-August.'),
        C('pasture_days_autumn', CH, 'days', 'Days on pasture in September-November.'),
        C('pasture_days_winter', CH, 'days', 'Days on pasture in December-February.'),
        C('pasture_days', CH, 'days/year', 'Animals other than cattle: days on pasture.'),
        C('pasture_hours', CH, 'h/day', 'Hours on pasture on a grazing day.', '8'),
        C('yard_days', CH, 'days/year', 'Days on the yard (exercise area).'),
        C('yard_hours', CH, 'h/day', 'Hours on the yard on those days.'),
        C('grazing_n_ratio', CH, 'ratio', 'Cattle: N content of grazed feed / mean of the ration; '
          'empty = 1.'),
        C('liquid_n_share', CH, 'fraction', 'Share of the N excreted in housing that goes to liquid '
          'manure.', '0.8'),
        C('lw_purchased_kg_year_class', CH, 'kg LW/year', 'Live weight of animals bought in.'),
        C('lw_sold_kg_year_class', CH, 'kg LW/year', 'Live weight of animals sold.'),
        C('lw_gain_kg_year_class', CH, 'kg LW/year', 'Change of the class\'s live weight (may be '
          'negative).'),
        C('milk_kg_year_class', CH, 'kg/year', 'Milk produced by the class (SALCA Tab. 4, kg N per kg).'),
        C('eggs_kg_year_class', CH, 'kg/year', 'Eggs produced by the class.'),
    ),
    'manure': (
        C('activityName', REQUIRED, '-', 'As on "activity".'),
        C('class_name', REQUIRED, '-', 'Animal class as on "herd", or "all".', 'all'),
        C('system', REQUIRED + ' (not CH)', '-', 'Manure management system (IPCC 2019 Table 10.18). '
          'Not used for CH (SALCA derives the systems from the time on pasture and yards).',
          'pasture', tuple(SYSTEMS)),
        C('share', REQUIRED + ' (not CH)', 'fraction', 'Share of the manure in this system; the '
          'shares of a class add up to 1.', '0.57'),
        D('source', RECOMMENDED, 'text', 'Source of the share (written in the comments of the '
          'manure emissions).'),
    ),
    'products': (
        C('activityName', REQUIRED, '-', 'As on "activity".'),
        C('group', REQUIRED, '-', 'Exactly one ReferenceProduct per dataset.', 'ReferenceProduct',
          ('ReferenceProduct', 'ByProduct')),
        C('name', REQUIRED, '-', 'ecoinvent product name, lowercase.', 'raw cashmere'),
        C('unitName', REQUIRED, '-', 'kg.', 'kg', ('kg',)),
        C('amount_per_year', REQUIRED, 'kg/year', 'Amount leaving the farm in the year (sold, '
          'delivered or used at home). Milk: the milk leaving the farm, not the milk fed to calves '
          '(IDF 2022, section 4.3.1); the milk the animals produce goes in section 4. Fibre: greasy '
          'weight.', '215.01'),
        D('comment', REQUIRED, 'text', 'Source of the amount, and any conversion.'),
        C('product_type', REQUIRED, '-', 'Sets how dry mass and carbon are computed when they are '
          'not given under "Properties". Cattle and buffalo milk with fat and protein is counted as '
          'FPCM; dairy farms are allocated by the IDF method.', 'fibre',
          ('milk', 'live_weight', 'fibre', 'eggs', 'other')),
        C('species', OPTIONAL, '-', 'Species of the product; empty = the herd\'s, when it has one '
          '(a mixed herd must give it for milk and live weight).',
          'goat', tuple(sorted(set(SPECIES.values())))),
        C('fat_pct', DAIRY, '%', 'Milk: fat (cattle/buffalo: FPCM, IDF 2022 Equation 1; every milk: '
          'dry mass and carbon). Empty = USDA FoodData Central for the species.', '4.1'),
        C('protein_pct', DAIRY, '%', 'Milk: true protein (as fat_pct).', '3.4'),
        C('fibre_type', FIBRE_PRODUCT, '-', 'Fibre: the fibre, for the regain of the raw fibre (dry '
          'mass).', 'cashmere', tuple(FIBRE)),
        C('scoured_yield', FIBRE_PRODUCT, 'kg/kg', 'Fibre: scoured (clean) fibre per kg of raw fibre, '
          'for the carbon content.', '0.74'),
        C('grease_share', FIBRE_PRODUCT, 'kg/kg', 'Fibre: grease per kg of raw fibre, for the carbon '
          'content.', '0.0427'),
        C('body_class', LIVE_WEIGHT, '-', 'Live weight: the body class whose cited composition sets '
          'dry mass and carbon; empty = the herd category default (goats, sheep lambs, cull dairy '
          'cows, finishing pigs, broilers). Other classes (buffalo, sows, horses, spent hens, cull '
          'ewes): give the body composition.', 'goat', tuple(BODY)),
        C('body_ebw', LIVE_WEIGHT, 'kg/kg', 'Live weight: empty body per kg live weight. Empty = the '
          'default of the body class; without one, give the four body values.', '0.89'),
        C('body_protein', LIVE_WEIGHT, 'kg/kg', 'Live weight: protein per kg empty body.', '0.164'),
        C('body_fat', LIVE_WEIGHT, 'kg/kg', 'Live weight: fat per kg empty body.', '0.154'),
        C('body_ash', LIVE_WEIGHT, 'kg/kg', 'Live weight: ash per kg empty body.', '0.044'),
        C('egg_shell_share', OPTIONAL, 'kg/kg', 'Eggs: shell per kg of egg in shell; empty = 0.105 '
          '(Nys et al. 2004, 10-11 %).', '0.105'),
        C('sold_class', DAIRY, '-', 'Dairy live weight: class sold (IDF 2022 net energy for growth).',
          'mature', tuple(NEG_PER_KG_LW)),
    ),
    'properties': (
        C('activityName', REQUIRED, '-', 'As on "activity".'),
        C('name', REQUIRED, '-', 'Product, as on "products".'),
        C('propertyName', REQUIRED, '-', 'Price always. Any other property given here, with its '
          'source, replaces the one the tool computes from "products" and its cited defaults.',
          'price',
          ('price', 'carbon content, non-fossil', 'carbon content, fossil', 'water content',
           'dry mass', 'wet mass', 'water in wet mass')),
        C('unitName', REQUIRED, '-', 'For price the currency; contents dimensionless.', 'USD'),
        C('amount', REQUIRED, 'per kg', 'Per kg of the product; carbon contents and water content '
          'per kg of dry mass, as ecoinvent defines them.', '47.71'),
        D('comment', REQUIRED, 'text', 'Source; for price always the year.'),
    ),
    'inputs': (
        C('activityName', REQUIRED, '-', 'As on "activity".'),
        C('group', REQUIRED, '-', 'Everything the herd uses, and emissions the livestock models do not '
          'compute.', 'FromTechnosphere', ('FromTechnosphere', 'FromEnvironment', 'ToEnvironment')),
        C('name', REQUIRED, '-', 'ecoinvent name of the product or flow.', 'maize grain, feed'),
        C('compartment', ENVIRONMENT, '-', 'FromEnvironment / ToEnvironment only.',
          'natural resource'),
        C('subcompartment', ENVIRONMENT, '-', 'FromEnvironment / ToEnvironment only.', 'land'),
        C('unitName', REQUIRED, '-', 'ecoinvent unit.', 'kg'),
        C('amount', REQUIRED, 'unit', 'Amount on the basis below.', '7097'),
        C('basis', REQUIRED, '-', 'herd_year: for the herd and the year (divided by the reference '
          'product); per_kg: already per kg of the reference product.', 'herd_year',
          ('herd_year', 'per_kg')),
        D('comment', REQUIRED, 'text', 'Source and how the amount was obtained (e.g. "15.1 kg per sheep '
          'unit x 470 sheep units, Table 5").'),
        C('water_use', IF_WATER, '-', 'Water rows: animals (drinking and cleaning) or irrigation.',
          'animals', ('animals', 'irrigation')),
    ),
}
