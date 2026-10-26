# Structure, and how it mirrors the crop tool

The crop agritool (`C:\python\sri-crop-tool`, Quantis ALCIG for ecoinvent) is
only a pattern here: nothing is imported from it and nothing in it is changed.
Its Python layer works in five steps, and the livestock tool keeps the same
five, in Python only (no Java backend, no web front end).

| Step | Crop tool | Livestock tool |
|---|---|---|
| 1. Read the filled data collection workbook | `ExcelInputReader.java` reads `LCI-Database_Data-collection_Crop_v2.xlsx`, a questionnaire with a hidden key column | `workbooks/input_reader.py` reads every Dataset sheet of `templates/livestock_data_collection.xlsx`, also a questionnaire with a hidden key column (`workbooks/form.py`) |
| 2. Map the inputs to model variables | `inputMappings.py`, `excelInputMappingRules.py` | no separate module: `workbooks/form.py` maps each row's key to its field, `input_reader.py` types the values, and `models_sequence.py` hands them to the models |
| 3. Fill what the user left empty | `defaultGeneration.py` with `defaultTables.py` | `default_generation.py` with `tables/` (one module per source, each value cited) |
| 4. Run the models in order | `modelsSequence.py` calls each model in `models/`; every model is a class whose docstring lists its inputs and outputs with units, `_input_variables`, and `compute()` returning prefixed keys | `models_sequence.py` with `models/`, same model contract |
| 5. Map the model outputs to exchanges and write the dataset | `outputMapping.py`, then `EcospoldFileWriter.java` with exchange templates | `output_mapping.py` with `flows/templates.py`, `metadata/` for the meta texts and flow comments, and `workbooks/provision_writer.py` |

## What is different, and why

- **One route per geography** (`models/routing.py`): Switzerland uses SALCA;
  EU countries use IPCC 2019 for greenhouse gases and EMEP/EEA 2023 for air
  pollutants; every other country uses the IPCC 2019 Refinement within the
  scope of WFLDB v3.5 (the route is still named WFLDB in the code).
- **Every factor is cited** (`sources.Factor`): the value, its unit, the
  source and the table it is printed in. The flow comments are written from
  these citations, so a comment always names the table its number comes from.
- **Output is the ecoinvent data provision workbook**, the format the
  agri-lca-pipeline reads from `input datasets/<project>/`. The two projects
  share no code; the workbook is the only link.
- **The model works per animal class and per year**, and the herd's totals are
  divided by the reference product's yearly amount only when the exchanges are
  written, as the crop tool divides by the yield.
