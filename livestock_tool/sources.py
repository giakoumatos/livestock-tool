"""The sources the livestock tool may use, and the cited value type.

Only these sources are used (user's rules, 2026-10-21):
  - every geography: WFLDB v3.5 (the rulebook) and IPCC 2006 as refined by
    the IPCC 2019 Refinement (greenhouse gases and nitrogen flows);
  - EU countries: EMEP/EEA Guidebook 2023 for NH3, NOx, NMVOC and particulate
    matter;
  - Switzerland: SALCA v1.0.1;
  - dairy only: IDF Bulletin 520/2022 for the milk/meat allocation.
A value whose version is not confirmed, or that comes from a source built on
another one, is never used.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    key: str
    short: str
    full: str


# A value the data collection gives in place of a table value.
GIVEN = Source('given', 'data collection', 'Given in the livestock data collection workbook.')
WFLDB35 = Source(
    'WFLDB35', 'Nemecek et al. 2019 (WFLDB guidelines v3.5)',
    'Nemecek T., Bengoa X., Lansche J., Roesch A., Faist-Emmenegger M., Rossi V. & Humbert S. (2019) '
    'Methodological Guidelines for the Life Cycle Inventory of Agricultural Products. Version 3.5, '
    'December 2019. World Food LCA Database (WFLDB). Quantis and Agroscope, Lausanne and Zurich, '
    'Switzerland.')
IPCC2006 = Source(
    'IPCC2006', 'IPCC 2006',
    'IPCC (2006) 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4: Agriculture, '
    'Forestry and Other Land Use. Prepared by the National Greenhouse Gas Inventories Programme, '
    'Eggleston H.S., Buendia L., Miwa K., Ngara T. and Tanabe K. (eds). IGES, Japan.')
IPCC2019 = Source(
    'IPCC2019', 'IPCC 2019',
    'IPCC (2019) 2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories, '
    'Volume 4: Agriculture, Forestry and Other Land Use. Calvo Buendia E., Tanabe K., Kranjc A., '
    'Baasansuren J., Fukuda M., Ngarize S., Osako A., Pyrozhenko Y., Shermanau P. and Federici S. '
    '(eds). IPCC, Switzerland.')
EMEP2023 = Source(
    'EMEP2023', 'EMEP/EEA 2023',
    'EEA (2023) EMEP/EEA air pollutant emission inventory guidebook 2023. Technical guidance to '
    'prepare national emission inventories. European Environment Agency. Chapter 3.B '
    'Manure management (lead authors: Amon B., Hutchings N., Dämmgen U., Sommer S., Webb J.).')
SALCA = Source(
    'SALCA', 'Nemecek et al. 2024 (SALCAanimal V1.0)',
    'Nemecek T., Roesch A., Bystricky M., Jeanneret P., Lansche J., Stüssi M. & Gaillard G. (2024) '
    'Swiss agricultural life cycle assessment: a method to assess the emissions and environmental '
    'impacts of agricultural systems and products. The International Journal of Life Cycle '
    'Assessment 29(3), 433-455. Code and parameter tables: Agroscope, SALCA v1.0.1 (14 October '
    '2026), https://github.com/agroscope-ch/salca.')
IDF2022 = Source(
    'IDF2022', 'IDF 2022',
    'IDF (2022) The IDF global Carbon Footprint standard for the dairy sector. Bulletin of the IDF '
    'N° 520/2022. International Dairy Federation, Brussels. https://doi.org/10.56169/FKRK7166')
ECOINVENT_DQG = Source(
    'ECOINVENT_DQG', 'Weidema et al. 2013 (ecoinvent data quality guideline v3)',
    'Weidema B.P., Bauer C., Hischier R., Mutel C., Nemecek T., Reinhard J., Vadenbo C.O. & '
    'Wernet G. (2013) Overview and methodology. Data quality guideline for the ecoinvent database '
    'version 3. ecoinvent Report 1 (v3). The ecoinvent Centre, St. Gallen.')

ECOINVENT_MD = Source(
    'ECOINVENT_MD', 'ecoinvent 3.12 master data',
    'ecoinvent database version 3.12, master data of the intermediate exchanges: properties (dry '
    'mass, water content, carbon content). ecoinvent Association, Zurich.')

SOURCES = {s.key: s for s in (WFLDB35, IPCC2006, IPCC2019, EMEP2023, SALCA, IDF2022,
                              ECOINVENT_DQG, ECOINVENT_MD)}


@dataclass(frozen=True)
class Factor:
    """A value as printed in a source, with where it is printed."""
    value: float
    unit: str
    source: Source
    where: str          # e.g. 'Vol. 4, Ch. 10, Table 10.13'
    note: str = ''

    def cite(self):
        return f'{self.source.short}, {self.where}'
