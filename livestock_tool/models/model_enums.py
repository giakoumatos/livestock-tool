"""Animal categories and manure management systems, and how each maps onto
the rows and columns of the IPCC 2019 and EMEP/EEA 2023 tables."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    energy: str | None      # Tier 2 energy equations: 'cattle', 'sheep_goats' or None
    ym: str | None          # 'goats', 'sheep' (IPCC 2019 Table 10.13), 'swine', 'horses',
                            # 'poultry' (WFLDB Tab. 10), None: Ym must be given
    b0: str                 # IPCC 2019 Table 10.16A row
    frac_column: str | None  # IPCC 2019 Table 10.22 column
    prp: str                # IPCC 2019 Table 11.1: 'CPP' or 'SO'
    n_retention: str | None  # IPCC 2019 Table 10.20 row; None: Eq. 10.33 (cattle) or given
    n_intake_eq: str        # '10.32' (from GE) or '10.32A' (from DMI)
    emep: str | None        # EMEP/EEA 2023 Table 3-9 / 3-5 / 3-12 category


CATEGORIES = {c.key: c for c in (
    Category('goats', 'goats', 'sheep_goats', 'goats', 'goats', 'other_animals', 'SO', 'goats',
             '10.32', 'goats'),
    Category('sheep', 'sheep', 'sheep_goats', 'sheep', 'sheep', 'other_animals', 'SO', 'sheep',
             '10.32', 'sheep'),
    Category('dairy_cattle', 'dairy cattle', 'cattle', None, 'dairy_cattle', 'dairy_cow', 'CPP',
             None, '10.32', 'dairy_cattle'),
    Category('other_cattle', 'other cattle', 'cattle', None, 'other_cattle', 'other_cattle', 'CPP',
             None, '10.32', 'other_cattle'),
    Category('buffalo', 'buffalo', 'cattle', None, 'buffalo', None, 'CPP', None, '10.32',
             'buffalo'),
    Category('swine_finishing', 'finishing pigs', None, 'swine', 'swine', 'swine', 'CPP', 'swine',
             '10.32A', 'swine_finishing'),
    Category('swine_sows', 'sows', None, 'swine', 'swine', 'swine', 'CPP', 'swine', '10.32A',
             'swine_sows'),
    Category('laying_hens', 'laying hens', None, 'poultry', 'chicken_layer', 'poultry', 'CPP',
             'poultry', '10.32A', 'laying_hens'),
    Category('broilers', 'broilers', None, 'poultry', 'other_poultry', 'poultry', 'CPP',
             'poultry', '10.32A', 'broilers'),
    Category('horses', 'horses', None, 'horses', 'horses', 'other_animals', 'SO', 'horses',
             '10.32A', 'horses'),
)}


@dataclass(frozen=True)
class ManureSystem:
    key: str
    label: str
    mcf: str | None         # IPCC 2019 Table 10.17 row ('liquid' = by retention time,
                            # 'digester' = by the activity's digester_type)
    ef3: str | None         # IPCC 2019 Table 10.21 row
    frac: str | None        # IPCC 2019 Table 10.22 row
    emep_type: str | None   # EMEP/EEA 2023: 'slurry', 'solid', 'direct' (applied, not stored)


SYSTEMS = {s.key: s for s in (
    ManureSystem('pasture', 'pasture, range and paddock', 'pasture', None, None, None),
    ManureSystem('daily_spread', 'daily spread', 'daily_spread', 'daily_spread', 'daily_spread',
                 'direct'),
    ManureSystem('solid_storage', 'solid storage', 'solid_storage', 'solid_storage',
                 'solid_storage', 'solid'),
    ManureSystem('solid_storage_covered', 'solid storage (covered or compacted)',
                 'solid_storage_covered', 'solid_storage_covered', 'solid_storage_covered',
                 'solid'),
    ManureSystem('solid_storage_bulking_agent', 'solid storage with bulking agent',
                 'solid_storage_bulking_agent', 'solid_storage_bulking_agent',
                 'solid_storage_bulking_agent', 'solid'),
    ManureSystem('solid_storage_additives', 'solid storage with additives',
                 'solid_storage_additives', 'solid_storage_additives', 'solid_storage_additives',
                 'solid'),
    ManureSystem('dry_lot', 'dry lot', 'dry_lot', 'dry_lot', 'dry_lot', 'solid'),
    ManureSystem('liquid_slurry_crust', 'liquid/slurry with natural crust cover', 'liquid',
                 'liquid_slurry_crust', 'liquid_slurry_crust', 'slurry'),
    ManureSystem('liquid_slurry_no_crust', 'liquid/slurry without natural crust cover', 'liquid',
                 'liquid_slurry_no_crust', 'liquid_slurry_no_crust', 'slurry'),
    ManureSystem('liquid_slurry_cover', 'liquid/slurry with cover', 'liquid',
                 'liquid_slurry_cover', 'liquid_slurry_cover', 'slurry'),
    ManureSystem('pit_storage', 'pit storage below animal confinements', 'liquid', 'pit_storage',
                 'pit_storage', 'slurry'),
    ManureSystem('uncovered_anaerobic_lagoon', 'uncovered anaerobic lagoon',
                 'uncovered_anaerobic_lagoon', 'uncovered_anaerobic_lagoon',
                 'uncovered_anaerobic_lagoon', 'slurry'),
    ManureSystem('anaerobic_digester', 'anaerobic digester', 'digester', 'anaerobic_digester',
                 'anaerobic_digester', 'slurry'),
    ManureSystem('deep_bedding', 'deep bedding (no mixing, more than 1 month)',
                 'deep_bedding_over_1_month', 'deep_bedding_no_mixing', 'deep_bedding', 'solid'),
    ManureSystem('composting_in_vessel', 'composting (in-vessel)', 'composting_in_vessel',
                 'composting_in_vessel', 'composting_in_vessel', 'solid'),
    ManureSystem('composting_static_pile', 'composting (static pile)', 'composting_static_pile',
                 'composting_static_pile', 'composting_static_pile', 'solid'),
    ManureSystem('composting_intensive_windrow', 'composting (intensive windrow)',
                 'composting_intensive_windrow', 'composting_intensive_windrow',
                 'composting_intensive_windrow', 'solid'),
    ManureSystem('composting_passive_windrow', 'composting (passive windrow)',
                 'composting_passive_windrow', 'composting_passive_windrow',
                 'composting_passive_windrow', 'solid'),
    ManureSystem('poultry_with_litter', 'poultry manure with litter', 'poultry_manure',
                 'poultry_with_litter', 'poultry_with_litter', 'solid'),
    ManureSystem('poultry_without_litter', 'poultry manure without litter', 'poultry_manure',
                 'poultry_without_litter', 'poultry_without_litter', 'solid'),
    ManureSystem('burned_for_fuel', 'dung burned for fuel', 'burned_for_fuel', None, None, None),
)}

FEEDING_SITUATIONS_SHEEP_GOATS = ('housed_ewes', 'grazing_flat_pasture', 'grazing_hilly_pasture',
                                  'housed_fattening_lambs', 'lowland_goats',
                                  'hill_mountain_goats')
FEEDING_SITUATIONS_CATTLE = ('stall', 'pasture', 'grazing_large_areas')
