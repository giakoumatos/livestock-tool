"""The elementary flows the livestock models write, by output key.

Names, compartments and units are ecoinvent's (checked against the ecoinvent
Master Data, 2026-10-21). Each output key of the models maps to one row; a
flow may appear on several rows (e.g. enteric and manure methane), each with
its own comment, as in the data provision files.
"""
from dataclasses import dataclass

_AIR = ('air', 'non-urban air or from high stacks')


@dataclass(frozen=True)
class FlowTemplate:
    key: str
    name: str
    compartment: str
    subcompartment: str
    unit: str = 'kg'


FLOW_TEMPLATES = {t.key: t for t in (
    FlowTemplate('ch4_enteric', 'Methane, non-fossil', *_AIR),
    FlowTemplate('ch4_manure', 'Methane, non-fossil', *_AIR),
    FlowTemplate('n2o_manure_direct', 'Dinitrogen monoxide', *_AIR),
    FlowTemplate('n2o_pasture_direct', 'Dinitrogen monoxide', *_AIR),
    FlowTemplate('n2o_indirect_volatilisation', 'Dinitrogen monoxide', *_AIR),
    FlowTemplate('n2o_indirect_leaching', 'Dinitrogen monoxide', *_AIR),
    FlowTemplate('nh3', 'Ammonia', *_AIR),
    FlowTemplate('nox', 'Nitrogen oxides', *_AIR),
    FlowTemplate('nmvoc', 'NMVOC, non-methane volatile organic compounds', *_AIR),
    FlowTemplate('pm25', 'Particulate Matter, < 2.5 um', *_AIR),
    FlowTemplate('pm25_10', 'Particulate Matter, > 2.5 um and < 10um', *_AIR),
    FlowTemplate('pm10_plus', 'Particulate Matter, > 10 um', *_AIR),
    FlowTemplate('no3_groundwater', 'Nitrate', 'water', 'ground-'),
)}
