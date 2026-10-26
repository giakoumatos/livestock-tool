# Source register

The tool uses only these sources, under three rules: outside the EU, general
standards (IPCC, WFLDB); only versions and values that are fully confirmed;
no source that is built on another one (AGRIBALYSE, GLEAM, national
inventories and the like are left out).

WFLDB v3.5 is the rulebook: it decides what is calculated and how. Where it
cites an IPCC 2006 or EMEP/EEA 2016 table, the same table of the newer
edition is used, after checking that it gives the same quantity. Where the
newer edition has no matching value, WFLDB's published value stays.

Every value below was read on the page image of the official PDF. The
documents are in [references/](references/README.md).

| Use | Source | Where |
|---|---|---|
| Structure, boundaries, allocation, water, and what no newer source covers | WFLDB v3.5 (Nemecek et al. 2019) | sections 2.6.3, 3.2.2, 3.5.5, 3.9.6, 3.9.12, 3.12; option wfldb: leaching scope 3.9.5.2 |
| Ym of pigs, horses, poultry (no IPCC 2019 value) | WFLDB v3.5 | Tab. 10, p. 41 (FOEN 2013) |
| Gross energy, Tier 2 | IPCC 2019, Vol. 4, Ch. 10 | Eq. 10.3-10.16; Tables 10.4 (Cfi, lactating and dry cows), 10.5 (Ca), 10.6 (a, b), 10.7 (Cpregnancy), p. 10.23-10.30; cashmere NEwool 0.08 MJ/d, p. 10.28 |
| Simplified Tier 2 intake of cattle, and the intake check | IPCC 2019, Vol. 4, Ch. 10 | Eq. 10.17, 10.18, 10.18A, 10.18B, Table 10.8, p. 10.31-10.32; Table 10.8A, p. 10.33; DMI 2-3 % (dairy up to 4 %) of body weight, p. 10.32 |
| Tier 1, classes without intake data | IPCC 2019, Vol. 4, Ch. 10 | Table 10.10 and Eq. 10.19, p. 10.38-10.39 (enteric; not cattle); Table 10.13A and Eq. 10.22A, p. 10.55-10.56 (VS); Table 10.19 and Eq. 10.30, p. 10.80-10.83 (N excreted) |
| Climate zone and wet/dry class | IPCC 2019, Vol. 4, Ch. 3 and Ch. 11 | Figure 3A.5.2, p. 3.48 (the decision tree Annex 10A.2, p. 10.127, points to; its text prints the PET ratio the wrong way round); Table 11.1, fn 4, p. 11.13 |
| Enteric methane | IPCC 2019, Vol. 4, Ch. 10 | Eq. 10.21, Table 10.13 (sheep 6.7 %, goats 5.5 %), p. 10.47 |
| Volatile solids, manure methane | IPCC 2019, Vol. 4, Ch. 10 | Eq. 10.23-10.24, p. 10.64-10.65; Table 10.16A (B0), p. 10.67; Table 10.17 (MCF, with the anaerobic digester rows), p. 10.68-10.69; fn 1, p. 10.70 (thick dry crust -40 %, solid cover 25-50 %) |
| N intake and excretion | IPCC 2019, Vol. 4, Ch. 10 | Eq. 10.31, 10.31A, 10.32, 10.32A, 10.33, p. 10.81-10.85; Table 10.20, p. 10.85; N retention of sows, growing pigs, hens and broilers Eq. 10.33A-E, Tables 10.20A-B, p. 10.86-10.89 |
| Manure N2O, N volatilisation and leaching | IPCC 2019, Vol. 4, Ch. 10 | Table 10.21, p. 10.91-10.93; Table 10.22, p. 10.97-10.98 (leaching on every system; digestate fn 3); p. 10.89 (no NH3/NOx split; refers to EMEP/EEA 3.B) |
| Pasture N2O, NH3 and NOx, induced N2O, FracLEACH | IPCC 2019, Vol. 4, Ch. 11 | Table 11.1, p. 11.13; Table 11.3, p. 11.26; Annex 11A.8, Table 8A.1, p. 11.39 (0.197 NH3-N and 0.015 NOx-N per kg N) |
| EU: NH3, NO, NMVOC, PM; outside the EU: the NOx part of the manure-management FracGas_MS (Table 3-10 on the Table 3-9 TAN) and PM2.5 | EMEP/EEA 2023, 3.B and 3.D | 3.B Tables 3-5, 3-7, 3-8, 3-9, 3-10, 3-11, 3-12, Steps 3-15 (p. 18-32); 3.D Table 3-1, p. 14 |
| Cattle and buffalo Ym | IPCC 2019, Vol. 4, Ch. 10 | Table 10.12, p. 10.46 (by milk yield, DE, NDF, forage share; feedlots named) |
| Switzerland: all animal emissions | SALCAanimal V1.0, Appendix 6 of Nemecek et al. 2024 (Agroscope SALCA page); code agroscope-ch/salca v1.0.1 | Tab. 1-10 and Eq. 1-10 of the appendix: Ym, B0, UE, MCF, N in products and bodies, urine and TAN of cattle, NH3 by EEA 2019 or Agrammon 2022, N2O, N2, NOx, pasture N by season, induced N2O. Where the code differs from the appendix, the appendix is followed (open points say where) |
| Dairy milk/meat allocation and FPCM | IDF Bulletin 520/2022 | section 4.3, Equation 1, p. 21 (FPCM); section 5.4.2, Equations 2-4, p. 43-44 (NEL 3.1 MJ/kg FPCM; NEG 27.5, 15 and 11 MJ/kg live weight) |
| Water balance (animals, fodder irrigation) | WFLDB v3.5; ecoinvent data quality guideline v3 (Weidema et al. 2013); FAO LEAP water guidelines v1 (2019) | WFLDB sections 3.5.2 (Tab. 4, p. 27), 3.5.4 and 3.5.5 (p. 29), Tab. 34 (p. 81, ICID 2012); ecoinvent guideline section 6.6 (p. 47), Table 9.1 (p. 62-63); LEAP section 4.5.4-4.5.5 (p. 36) |
| Product properties (dry mass, carbon) | USDA FoodData Central SR Legacy; GB 18267-2013; Alves et al. 2008; Théiriez et al. 1981; Cannas et al. 2004; Honig et al. 2022; NASEM 2021; Kasper et al. 2021; Atapattu et al. 2026; Sakomura et al. 2026; Nys et al. 2004; Long et al. 1983; IWTO-19 (Barry 2009, Wood 2009); MacPherson 2012; FAO Technical Conversion Factors; IWTO 2024; carbon fractions as compiled in Longworth et al. 2026, Table 15 | full references in livestock_tool/references.py and tables/product_properties.py |

Where a table gives no value for an animal or system (for example deep
bedding for "other animals" in IPCC 2019 Table 10.22), the tool stops with
a message instead of borrowing another row.
