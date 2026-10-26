# livestock-tool

Builds livestock datasets (activity data in, emissions, flows, metadata and
flow comments out) for ecoinvent, the way the crop agritool
(`C:\python\sri-crop-tool`) does it for crops. It shares no code with the
crop tool or with the agri-lca-pipeline: it writes the ecoinvent data
provision workbook that the pipeline reads from its `input datasets` folder,
and that file is the only link.

## Methods, by geography

| Geography | Method |
|---|---|
| Switzerland | SALCAanimal V1.0 (SALCA, Agroscope), as documented in its appendix |
| EU-27 | IPCC 2019 for greenhouse gases and N flows; EMEP/EEA 2023 for NH3, NOx, NMVOC and particulate matter |
| Every other country | IPCC 2019 Refinement, within the system boundaries of WFLDB v3.5 (always the most correct and up-to-date method: see docs/method_decisions.md) |

Every factor carries its source and table, and the flow comments are written
from them. The sources and pages are in [docs/sources.md](docs/sources.md),
and the structure, step by step against the crop tool, is in
[docs/structure.md](docs/structure.md).

## Use

1. Copy `templates/livestock_data_collection.xlsx` to `projects/<project>/`
   and fill it, one "Dataset" sheet per dataset (copy the sheet for each
   one). It is a questionnaire in the manner of the crop template: numbered
   sections, one question per row with its unit, a "Needed" tag (Required,
   Tier 2, Cattle, EU only, CH only, ...), the yellow data cells, a Source
   cell and a short "How to fill"; animal classes and products are columns.
   The "Start here" sheet says which parts to fill for which dataset.
   `projects/cashmere/` is a filled example. Rebuild the template with
   `python tools/build_template.py` after a change to the schema or the
   form; a workbook in the old table layout is converted with
   `python tools/convert_workbook.py old.xlsx new.xlsx`.
2. Run `python run_tool.py projects/<project>/<workbook>.xlsx`.
3. Take `output/<project>/ecoinvent_data_provision_file_<project>.xlsx` to the
   pipeline, and read `output/<project>/open_points.md`: the defaults,
   assumptions and data gaps the run relied on.

The models work per animal class and per year. A class can come with its dry
matter intake (gross energy = DMI x 18.45 MJ/kg), with the animal data for
IPCC 2019 Tier 2 gross energy, or, for cattle, with the simplified Tier 2
intake equations; a class with none of these falls back to IPCC 2019 Tier 1
(not cattle), with an open point. The climate zone and the wet/dry class can
be given or placed from climate data by the IPCC decision tree. The method
choices and their alternatives are in [docs/method_decisions.md](docs/method_decisions.md). Herd totals are divided by the reference
product's yearly amount when the exchanges are written.

## Layout

```
run_tool.py                  read -> models -> flows and meta -> provision workbook
livestock_tool/
  sources.py                 the allowed sources and the cited value type
  tables/                    one module per source: ipcc2019, emep2023, wfldb35,
                             salca, idf2022
  models/                    routing, energy, enteric, excretion, manure CH4,
                             nitrogen (IPCC route), emep_nitrogen (EU), salca (CH),
                             air (PM, NMVOC), water (release), allocation (IDF dairy)
  models_sequence.py         runs the models class by class
  default_generation.py      cited defaults for empty inputs
  output_mapping.py          per-kg exchanges with their comments
  metadata/meta_builder.py   the meta fields
  flows/templates.py         ecoinvent elementary flows
  workbooks/                 schema (the input fields), form (the Dataset sheet's
                             layout and wording, and its reading), form_writer
                             (draws the workbook), input_reader, provision writer
docs/references/             the source documents (PDF, Word, code archive)
tools/                       build_template.py, convert_workbook.py (old table layout)
templates/                   the data collection workbook
projects/<project>/          filled data collection workbooks
output/<project>/            results (not versioned)
```

There is no test suite: a change is checked by running a project and
recomputing its figures by hand.
