"""Full references for every comment the tool writes.

A comment cites its sources in short form ("IPCC 2019, Vol. 4, Ch. 10,
Table 10.21"); `with_references` ends it with the full reference of each
source it names, in the order they first appear. The sources come from
sources.py and the source objects of the tables, the literature below
(cited through them), and the project's own references ("Full references of
the sources", section 9 of the Dataset sheet: one per line, "short name = full reference").
"""
import re

from .sources import SOURCES
from .tables import product_properties as pp

# Literature the tables cite through a primary source, by the short form
# the comments use (regex) -> full reference, as printed in the reference
# list of the source that cites it.
LITERATURE = {
    r'Shaffer \(?2008\)?': 'Shaffer K.H. (2008) Consumptive water use in the Great Lakes Basin. '
                           'U.S. Geological Survey Fact Sheet 2008-3032, 6 p.',
    r'L[eé]vov[aá] (?:& Pfister|et al\.)?\s*\(?2012\)?':
        'Lévová T. & Pfister S. (2012) Good practice for life cycle inventories - modeling of water '
        'use. Swiss Centre for Life Cycle Inventories, Dübendorf, Switzerland.',
    r'ICID 2012': 'ICID (2012) Sprinkler and micro irrigated area in the World. International '
                  'Commission on Irrigation and Drainage. http://www.icid.org/icid_data.html',
    r'FAO 1989': 'FAO (1989) Irrigation Water Management: Irrigation Scheduling. Training manual '
                 'no. 4, Annex I: Irrigation efficiencies. FAO, Rome.',
    r'Mahgoub & Lodge 1998': 'Mahgoub O. & Lodge G.A. (1998) A comparative study on growth, body '
                             'composition and carcass tissue distribution in Omani sheep and goats. '
                             'Journal of Agricultural Science 131(3), 329-339.',
    r'Sanson et al\. 1993': 'Sanson D., West T., Tatman W., Riley M., Judkins M. & Moss G. (1993) '
                            'Relationship of body composition of mature ewes with condition score and '
                            'body weight. Journal of Animal Science 71(5), 1112-1116. '
                            'https://doi.org/10.2527/1993.7151112x',
    r'Rouwenhorst et al\. 1991': 'Rouwenhorst R.J., Frank Jzn J., Scheffers W.A. & van Dijken J.P. '
                                 '(1991) Determination of protein concentration by total organic '
                                 'carbon analysis. Journal of Biochemical and Biophysical Methods '
                                 '22(2), 119-128. https://doi.org/10.1016/0165-022X(91)90024-Q',
    r'Bray & Bouchard 2003': 'Bray G.A. & Bouchard C. (eds) (2003) Handbook of Obesity: Etiology '
                             'and Pathophysiology, 2nd edition. CRC Press. '
                             'https://doi.org/10.3109/9780203913376',
    r'Hawkesworth 1948': 'Hawkesworth A. (1948) Australasian sheep and wool. William Brooks & Co.',
    r'Simmonds 1954': 'Simmonds D.H. (1954) The amino acid composition of keratins. I. The amino '
                      'acid analysis of merino 64\'s quality virgin wool. Australian Journal of '
                      'Biological Sciences 7(1), 98-110.',
    r'von Bergen 1963': 'von Bergen W. (1963) Wool Handbook, Volume 1. John Wiley and Sons.',
    r'Mongolian Agency for Standardization and Metrology 2019|MASM 2019':
        'Mongolian Agency for Standardization and Metrology (2019) MNS 6741:2019 Textiles. Washed '
        'cashmere, wool, and wool of goats, camels and yaks. Technical requirements.',
    r'Th[ée]iriez et al\. 1981': 'Théiriez M., Tissier M. & Robelin J. (1981) The chemical '
                                  'composition of the intensively fed lamb. Animal Production 32(1), '
                                  '29-37. https://doi.org/10.1017/S0003356100024739',
    r'Cannas et al\. 2004': 'Cannas A., Tedeschi L.O., Fox D.G., Pell A.N. & Van Soest P.J. (2004) A '
                            'mechanistic model for predicting the nutrient requirements and feed '
                            'biological values for sheep. Journal of Animal Science 82(1), 149-169. '
                            'https://doi.org/10.2527/2004.821149x',
    r'NRC 2007': 'NRC (2007) Nutrient Requirements of Small Ruminants: Sheep, Goats, Cervids, and '
                 'New World Camelids. The National Academies Press, Washington, DC. '
                 'https://doi.org/10.17226/11654',
    r'Honig et al\. 2022': 'Honig A.C., Inhuber V., Spiekers H., Windisch W., Götz K.-U., Schuster M. '
                           '& Ettle T. (2022) Body composition and composition of gain of growing beef '
                           'bulls fed rations with varying energy concentrations. Meat Science 184, '
                           '108685. https://doi.org/10.1016/j.meatsci.2021.108685',
    r'NASEM 2021': 'NASEM (2021) Nutrient Requirements of Dairy Cattle, Eighth Revised Edition. '
                   'National Academies of Sciences, Engineering, and Medicine. The National Academies '
                   'Press, Washington, DC. https://doi.org/10.17226/25806',
    r'Kasper et al\. 2021': 'Kasper C., Schlegel P., Ruiz-Ascacibar I., Stoll P. & Bee G. (2021) '
                            'Accuracy of predicting chemical body composition of growing pigs using '
                            'dual-energy X-ray absorptiometry. Animal 15(8), 100307. '
                            'https://doi.org/10.1016/j.animal.2021.100307; data set: '
                            'https://doi.org/10.5281/zenodo.3981182',
    r'Atapattu et al\. 2026': 'Atapattu N.S.B.M., Nelson K.B., Kidd M.T. & Gous R.M. (2026) '
                              'Evaluation of the potential growth and body composition of the Cobb '
                              'MV x500 genotype. Poultry Science 105(12), 107911. '
                              'https://doi.org/10.1016/j.psj.2026.107911',
    r'Sakomura et al\. 2026': 'Sakomura N.K., Reis M.P., Viana G.S. & Riveros R. (2026) Modeling '
                              'poultry growth and requirement for energy and essential amino acids. '
                              'Animal Nutrition 26, 235-247. https://doi.org/10.1016/j.aninu.2025.12.016',
    r'Nys et al\. 2004': 'Nys Y., Gautron J., Garcia-Ruiz J.M. & Hincke M.T. (2004) Avian eggshell '
                         'mineralization: biochemical and functional characterization of matrix '
                         'proteins. Comptes Rendus Palevol 3(6-7), 549-562. '
                         'https://doi.org/10.1016/j.crpv.2004.08.002',
    r'Long et al\. 1983': 'Long A., Hendershott R.B. & Martin P.S. (1983) Radiocarbon dating of fossil '
                          'eggshell. Radiocarbon 25(2), 533-539. '
                          'https://doi.org/10.1017/S003382220000583X',
    r'Barry 2009': 'Barry R. (2009) Topic 8 Yield. In: WOOL472/572 Wool Biology and Metrology. '
                   'Australian Wool Education Trust / University of New England, Armidale; sections 8.2 '
                   'and 8.7 (IWTO-19-03 and the IWTO Core Test Regulations). '
                   'https://www.woolwise.com/wp-content/uploads/2017/07/Wool-472-572-08-T-08.pdf',
    r'Wood 2009': 'Wood E. (2009) Topic 6 Scoured wool quality and testing. In: WOOL482/582 Wool '
                  'Processing. Australian Wool Education Trust / University of New England, Armidale; '
                  'p. 6-4 to 6-7 and 6-18. '
                  'https://www.woolwise.com/wp-content/uploads/2017/07/Wool-482-582-08-T-06.pdf',
    r'IWTO 2024': 'IWTO (2024) Wool Notes: A summary of wool textile information, Issue 3. '
                  'International Wool Textile Organisation, Brussels. '
                  'https://iwto.org/wp-content/uploads/2024/08/IWTO-Wool-Notes-Final-2024-Digital.pdf',
    r'ICAR 2018': 'ICAR (2018) Guidelines for Performance Recording in Dairy Sheep and Goats. '
                  'International Committee for Animal Recording.',
}
_SOURCE_OBJECTS = list(SOURCES.values()) + [pp.USDA_FDC, pp.LONGWORTH2026, pp.GB18267, pp.ALVES2008,
                                             pp.AWET, pp.FAO_TCF]
# Other short forms the comments use for these sources.
ALIASES = {
    'WFLDB35': r'WFLDB', 'EMEP2023': r'EMEP/EEA', 'SALCA': r'SALCA', 'IDF2022': r'IDF 2022|IDF method',
    'ECOINVENT_DQG': r'ecoinvent data quality guideline', 'USDA_FDC': r'USDA FoodData Central',
    'GB18267': r'GB 18267', 'LONGWORTH2026': r'Longworth et al\.? 2026', 'ALVES2008':
    r'Alves et al\.? 2008', 'IPCC2006': r'IPCC 2006',
}


def _patterns(project_refs=()):
    out = [(re.escape(s.short) + ('|' + ALIASES[s.key] if s.key in ALIASES else ''), s.full)
           for s in _SOURCE_OBJECTS]
    out += list(LITERATURE.items())
    out += [(re.escape(short), full) for short, full in project_refs]
    return out


def project_references(activity):
    """The project's references from the "references" column: lines of
    "short name = full reference"."""
    refs = []
    for line in str(activity.get('references') or '').splitlines():
        if '=' in line:
            short, full = (x.strip() for x in line.split('=', 1))
            if short and full:
                refs.append((short, full))
    return refs


def cited(comment, project_refs=()):
    """The short citations a comment makes, in order (the matched text)."""
    found = []
    for pattern, _ in _patterns(project_refs):
        m = re.search(pattern, comment or '')
        if m and m.group(0) not in (t for _, t in found):
            found.append((m.start(), m.group(0)))
    return [t for _, t in sorted(found)]


def with_references(comment, project_refs=()):
    """The comment ending with "References: ..." for the sources it names;
    unchanged when it names none, or already ends with them."""
    if not comment or ' References: ' in comment:
        return comment
    found = []
    for pattern, full in _patterns(project_refs):
        m = re.search(pattern, comment)
        if m and full not in comment and full not in (f for _, f in found):
            found.append((m.start(), full))
    if not found:
        return comment
    refs = '; '.join(full.rstrip('.') for _, full in sorted(found))
    return f'{comment.rstrip()} References: {refs}.'
