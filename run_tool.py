"""Builds livestock datasets from a filled data collection workbook.

    python run_tool.py projects/<project>/<workbook>.xlsx

Writes output/<project>/ecoinvent_data_provision_file_<project>.xlsx, the
workbook the agri-lca-pipeline reads from "input datasets/<project>/", and
output/<project>/open_points.md, the defaults and gaps the run relied on.
"""
import sys
from pathlib import Path

from livestock_tool.metadata.meta_builder import build_meta
from livestock_tool.models.base import fmt
from livestock_tool.models_sequence import ModelsSequence
from livestock_tool.output_mapping import emission_rows, input_rows, product_rows, \
    property_rows, route_label, water_row
from livestock_tool.workbooks.input_reader import ACTION, read_datasets
from livestock_tool.workbooks.provision_writer import ProvisionDataset, write_provision

ROOT = Path(__file__).resolve().parent


def build(workbook):
    workbook = Path(workbook).resolve()
    project = workbook.parent.name
    out_dir = ROOT / 'output' / project
    out_dir.mkdir(parents=True, exist_ok=True)
    provisions, notes = [], [f'# Open points: {project}', '',
                             'Per dataset: first what still needs a choice or data, then how '
                             'each gap was filled (already applied in the provision file).', '']
    for ds in read_datasets(workbook):
        seq = ModelsSequence(ds).execute()
        meta, facts = build_meta(ds, seq)
        provisions.append(ProvisionDataset(
            meta, facts,
            product_rows(ds) + emission_rows(ds, seq) + water_row(ds) + input_rows(ds),
            property_rows(ds)))
        notes += [f'## {ds.name} ({ds.activity["geography"]}, {route_label(seq.route)})', '']
        act = [p[len(ACTION):] for p in seq.open_points if p.startswith(ACTION)]
        done = [p for p in seq.open_points if not p.startswith(ACTION)]
        notes += ['### Needs action', ''] + ([f'- {p}' for p in act] or ['- none']) + ['']
        notes += ['### Handled: how the gaps were filled, for the record', '']
        notes += [f'- {p}' for p in done] or ['- none']
        notes.append('')
        ref = ds.reference_product()
        print(f'{ds.name}: ' + ', '.join(
            f'{k} {fmt(v / ds.amount(ref))}' for k, v in seq.totals.items() if v)
            + f' (kg per kg {ref["name"]})')
    target = out_dir / f'ecoinvent_data_provision_file_{project}.xlsx'
    write_provision(target, provisions)
    (out_dir / 'open_points.md').write_text('\n'.join(notes), encoding='utf-8')
    print(f'written: {target}')
    return target


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
