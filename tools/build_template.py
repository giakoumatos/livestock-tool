"""Writes templates/livestock_data_collection.xlsx (or the path given): the
"Start here" sheet and an empty "Dataset 1" sheet
(livestock_tool/workbooks/form.py lays it out, form_writer.py draws it).
Run after a change to the schema or the form; it stops if a schema field
has no row on the form.

    python tools/build_template.py [target.xlsx]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from livestock_tool.workbooks.form import check_coverage  # noqa: E402
from livestock_tool.workbooks.form_writer import write_workbook  # noqa: E402


def main():
    check_coverage()
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        ROOT / 'templates' / 'livestock_data_collection.xlsx'
    write_workbook(target)
    print(target)


if __name__ == '__main__':
    main()
