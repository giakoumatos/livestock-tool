"""Conversion factors, as the IPCC equations write them (e.g. 44/28 in
IPCC 2006, Vol. 4, Eq. 10.25), so a comment that says "x 44/28" is exact."""
MA_P = 30.973762
MA_O = 15.9994

N_TO_N2O = 44 / 28
N_TO_NH3 = 17 / 14
N_TO_NO2 = 46 / 14          # ecoinvent's "Nitrogen oxides" are counted as NO2
N_TO_NO3 = 62 / 14
P_TO_PO4 = (MA_P + 4 * MA_O) / MA_P
C_TO_CO2 = 44 / 12
CH4_KG_PER_M3 = 0.67        # IPCC 2006, Vol. 4, Eq. 10.23
CH4_MJ_PER_KG = 55.65       # IPCC 2006, Vol. 4, Eq. 10.21
