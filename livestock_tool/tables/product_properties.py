"""Basic properties of livestock products: the cited defaults and constants
the property model computes dry mass and carbon from (ecoinvent: carbon per
kg of dry mass, water content per kg of dry mass).

Only values from a confirmed source are here; a product with no default
must get its composition or its properties from the data collection.
"""
from ..sources import Factor, Source

USDA_FDC = Source(
    'USDA_FDC', 'USDA FoodData Central (SR Legacy)',
    'U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, SR Legacy '
    '(2019). https://fdc.nal.usda.gov/')
LONGWORTH2026 = Source(
    'LONGWORTH2026', 'Longworth et al. 2026',
    'Longworth E., Crone H. & Wiedemann S. (2026) Life Cycle Assessment of Cashmere. Textile '
    'Exchange and Integrity Ag, 3 February 2026.')
GB18267 = Source(
    'GB18267', 'GB 18267-2013',
    'GB 18267-2013 Cashmere (山羊绒). National standard of the People\'s Republic of China, '
    'Standardization Administration of China. Clause 5.1.4: regain of raw cashmere not more than '
    '13 % (read in the approval draft, https://law.resource.org/pub/cn/ibr/gb.18267.c.2012.pdf).')
ALVES2008 = Source(
    'ALVES2008', 'Alves et al. 2008',
    'Alves K.S., Carvalho F.F.R., Batista A.M.V., Véras A.S.C., Mattos C.W., Medeiros A.N. & '
    'Vasconcelos R.M.J. (2008) Composição corporal e exigências de energia para ganho de peso de '
    'caprinos Moxotó em crescimento (Body composition and energy requirements for weight gain of '
    'growing Moxotó goats). Revista Brasileira de Zootecnia 37(10), 1853-1859. '
    'https://doi.org/10.1590/S1516-35982008001000020')


AWET = Source(
    'AWET', 'MacPherson 2012',
    'MacPherson S. (2012) Topic 5 Wool classing. In: WOOL422/522 Wool Marketing & Clip Preparation. '
    'Australian Wool Education Trust / University of New England, Armidale; Fig. 5.39 Composition of '
    'greasy wool, p. 5-26 to 5-29. https://www.woolwise.com/wp-content/uploads/2017/07/'
    'WOOL-422-522-12-T-05.pdf')
FAO_TCF = Source(
    'FAO_TCF', 'FAO Technical Conversion Factors',
    'FAO Statistics Division (n.d., data 1992-1996) Technical Conversion Factors for Agricultural '
    'Commodities. FAO, Rome; country tables "Wool, greasy: clean yield of greasy wool". '
    'https://www.fao.org/fileadmin/templates/ess/documents/methodology/tcf.pdf')


def _f(value, unit, source, where, note=''):
    return Factor(value, unit, source, where, note)


# Carbon per kg of a component. Protein and fat as the cashmere LCA cites
# them (Rouwenhorst et al. 1991; Bray & Bouchard 2003); lactose from its
# formula C12H22O11 (12 x 12.011 / 342.30); keratin and wool grease as
# cited there (Simmonds 1954, von Bergen 1963).
C_PROTEIN = _f(0.53, 'kg C/kg', LONGWORTH2026, 'Table 15', 'Rouwenhorst et al. 1991')
C_FAT = _f(0.75, 'kg C/kg', LONGWORTH2026, 'Table 15', 'Bray & Bouchard 2003')
C_LACTOSE = 12 * 12.011 / 342.30
C_KERATIN = _f(0.50, 'kg C/kg', LONGWORTH2026, 'Table 15',
               'Hawkesworth 1948; Simmonds 1954; von Bergen 1963')
C_GREASE = _f(0.75, 'kg C/kg', LONGWORTH2026, 'Table 15', 'von Bergen 1963')

# Raw milk composition, g per 100 g (carbohydrate by difference is lactose).
MILK = {
    'cattle': dict(water=88.1, fat=3.25, protein=3.15, lactose=4.80, ash=0.67,
                   where='FDC 171265, Milk, whole, 3.25 % milkfat'),
    'buffalo': dict(water=83.4, fat=6.89, protein=3.75, lactose=5.18, ash=0.79,
                    where='FDC 171280, Milk, indian buffalo, fluid'),
    'sheep': dict(water=80.7, fat=7.0, protein=5.98, lactose=5.36, ash=0.96,
                  where='FDC 170882, Milk, sheep, fluid'),
    'goat': dict(water=87.0, fat=4.14, protein=3.56, lactose=4.45, ash=0.82,
                 where='FDC 171278, Milk, goat, fluid'),
}

# Whole-body composition of the live animal, by body class: empty body share
# of live weight and protein, fat and ash per kg of empty body. Gut contents
# get no dry mass. Only classes whose protein, fat and ash were measured in a
# primary source that was read have a default (research of 2026-10-22: no
# default for buffalo, sows, horses, spent hens, culled ewes or turkeys).
BODY = {
    'goat': dict(ebw=0.876, protein=0.204, fat=0.133, ash=0.044,
                 where=('growing Moxoto goats fed ad libitum: empty body 62.1 % water, 20.4 % '
                        'protein, 13.3 % fat, 4.4 % ash (Alves et al. 2008, Table 2, p. 1857); '
                        'empty body = -1.7778 + 0.9352 x live weight (same paper, p. 1856), 0.876 '
                        'at 30 kg')),
    'sheep_lamb': dict(ebw=0.817, protein=0.160, fat=0.195, ash=0.032,
                       where=('intensively fed lambs, shorn empty body at 30 kg: fat 179-212, protein '
                              '154-165, ash 31-33 g/kg, mid values (Théiriez et al. 1981); empty '
                              'body 0.851 x shrunk weight and shrunk weight 0.96 x live weight '
                              '(Cannas et al. 2004, as in NRC 2007); the fleece is not included')),
    'cattle_bull': dict(ebw=0.941, protein=0.191, fat=0.213, ash=0.044,
                        where=('Fleckvieh bulls at about 780 kg, measured whole-body chemical '
                               'composition (Honig et al. 2022, Table 2); empty body 734 of 780 kg')),
    'cattle_calf': dict(ebw=0.88, protein=0.200, fat=0.102, ash=0.046,
                        where=('ruminating calves of about 200 kg, measured (Honig et al. 2022, '
                               'Table 2, 200 kg group); empty body 176 of 200 kg')),
    'cattle_cull_dairy_cow': dict(ebw=0.82, protein=0.160, fat=0.255, ash=0.042,
                                  where=('culled dairy cow at mature weight, NASEM 2021 Equation '
                                         '11-4a: fat 0.067 + 0.188 x weight/mature weight, protein '
                                         '0.215 and ash 0.056 of the fat-free empty body, gut fill '
                                         '0.18 of body weight (read in the NASEM 2021 model code)')),
    'pig_finisher': dict(ebw=0.956, protein=0.170, fat=0.176, ash=0.033,
                         where=('Swiss Large White entire males at 100.9 kg, whole empty body '
                                'chemically analysed, means of the 37 pigs of the published data '
                                '(Kasper et al. 2021, Zenodo data set, file emptybody.txt)')),
    'chicken_broiler': dict(ebw=1.0, protein=0.200, fat=0.110, ash=0.023,
                            where=('Cobb broilers at 35-42 days: feather-free empty body (Atapattu '
                                   'et al. 2026, Table 5) with the feathers, 3.9 % of the body '
                                   '(Tables 2 and 4) at 0.90 protein (Sakomura et al. 2026, Table 1; '
                                   'feather fat and ash taken as 0.02 each); the study weighed the '
                                   'birds after the night, "mimicking feed withdrawal", so the '
                                   'composition is applied to the live weight')),
}
# The body class a product takes when it names none, by herd category.
DEFAULT_BODY_CLASS = {'goats': 'goat', 'sheep': 'sheep_lamb', 'dairy_cattle': 'cattle_cull_dairy_cow',
                      'swine_finishing': 'pig_finisher', 'broilers': 'chicken_broiler'}

# Eggs in shell, per kg as laid: the contents of USDA FoodData Central
# 171287 "Egg, whole, raw, fresh" (g/100 g) and the shell, 10-11 % of the egg
# (10.5 % used), 95 % CaCO3 and 3.5 % organic matrix, the rest taken as water
# (Nys et al. 2004). The shell carbonate comes from the hen's blood
# bicarbonate (Long et al. 1983), so its carbon is non-fossil, as ecoinvent
# counts the carbonate of "limestone, from algae".
EGG = dict(contents=dict(water=76.2, protein=12.6, fat=9.51, carbohydrate=0.72, ash=1.06),
           shell_share=0.105, shell_caco3=0.95, shell_matrix=0.035,
           where='USDA FoodData Central (SR Legacy), FDC 171287, Egg, whole, raw, fresh; shell: '
                 'Nys et al. 2004; carbonate carbon biogenic: Long et al. 1983')
C_CACO3 = 12.011 / 100.087
C_GLUCOSE = 6 * 12.011 / 180.156

# Animal fibre at the farm gate (greasy): regain of the raw fibre, regain of
# the scoured fibre and its residual grease and dirt.
FIBRE = {
    'wool': dict(raw_regain=_f(0.10 / 0.90, 'kg water/kg dry', AWET, 'Topic 5, Fig. 5.39',
                               'typical greasy wool, water 10 % of the greasy mass'),
                 scoured_regain=0.17, scoured_residue=0.0227, default_grease=0.16,
                 where=('IWTO-19 basis: scoured yield at 17 % regain with 2.27 % ash and alcohol '
                        'extractives (Barry 2009, Topic 8; Wood 2009, Topic 6); typical grease (wax) '
                        '16 % of greasy wool (MacPherson 2012, Fig. 5.39)')),
    'cashmere': dict(raw_regain=_f(0.13, 'kg water/kg dry', GB18267, 'clause 5.1.4',
                                   'trading limit for raw cashmere'),
                     scoured_regain=0.15, scoured_residue=0.018,
                     where=('scoured cashmere at 15 % moisture with 0.9 % grease and 0.9 % dirt '
                            '(Mongolian Agency for Standardization and Metrology 2019, as in '
                            'Longworth et al. 2026, Table 15)')),
}

# Default scoured (clean) yield of greasy wool by country (FAO Technical
# Conversion Factors, data 1992-1996), else the world figure of 2022 (IWTO
# 2024, Wool Notes, p. 4: clean / greasy world production).
WOOL_YIELD = {'AU': 0.64, 'NZ': 0.74, 'ZA': 0.61, 'CN': 0.50, 'AR': 0.55, 'UY': 0.56, 'GB': 0.71,
              'US': 0.51, 'IN': 0.66, 'IR': 0.70, 'KZ': 0.59, 'PK': 0.59, 'RU': 0.59, 'TR': 0.40,
              'NO': 0.63, 'ET': 0.52}
WOOL_YIELD_WORLD = 0.532

# Herd category -> species of its products.
SPECIES = {'goats': 'goat', 'sheep': 'sheep', 'dairy_cattle': 'cattle', 'other_cattle': 'cattle',
           'buffalo': 'buffalo', 'swine_finishing': 'pig', 'swine_sows': 'pig',
           'laying_hens': 'chicken', 'broilers': 'chicken', 'horses': 'horse'}
