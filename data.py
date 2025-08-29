# data.py
from models import Core, Coil

# Example, simplified data. Replace/extend with your catalog.
CORES: list[Core] = [
    Core(
        name="Generic Ferrite T30",
        mu_r=2000.0,
        area_m2=25e-6,             # 25 mm^2
        r_mean_m=12.5e-3,          # mean radius 12.5 mm
        window_area_m2=35e-6,      # 35 mm^2 window
        # Optional geometric dims (if known) improve path length accuracy
        od_m=30e-3,
        id_m=15e-3,
        ht_m= (25e-6) / ((30e-3 - 15e-3)/2) ,
        b_sat_t=0.35,
        price_usd=2.50,
    ),
    Core(
        name="Powdered Iron T50-2",
        mu_r=10.0,
        area_m2=12e-6,             # 12 mm^2
        r_mean_m=19.0e-3,          # 19 mm
        window_area_m2=40e-6,      # 40 mm^2
        od_m=50e-3,
        id_m=20e-3,
        ht_m=(12e-6)/((50e-3-20e-3)/2),
        b_sat_t=1.0,
        price_usd=1.40,
    ),
    Core(
        name="Air-core Form 30mm",
        mu_r=1.0,
        area_m2=50e-6,
        r_mean_m=15e-3,
        window_area_m2=200e-6,
        od_m=30e-3,
        id_m=20e-3,
        ht_m=(50e-6)/((30e-3-20e-3)/2),
        b_sat_t=None,
        price_usd=0.30,
    ),
    # Added: larger gapped ferrite toroid (low mu_r, bigger area) to avoid saturation at 0.5 A
    Core(
        name="Gapped Ferrite T80G",
        mu_r=90.0,
        area_m2=150e-6,            # 150 mm^2 effective magnetic area
        r_mean_m=20.0e-3,          # mean radius 20 mm
        window_area_m2=200e-6,     # 200 mm^2 winding window
        od_m=48e-3,
        id_m=24e-3,
        ht_m=(150e-6)/((48e-3-24e-3)/2),
        b_sat_t=0.35,              # ferrite-like Bsat
        price_usd=4.00,
    ),
    # Added: larger powdered iron toroid with moderate mu_r and big window
    Core(
        name="Powdered Iron T130-26",
        mu_r=75.0,
        area_m2=100e-6,            # 100 mm^2
        r_mean_m=32.0e-3,          # mean radius 32 mm
        window_area_m2=250e-6,     # 250 mm^2
        od_m=65e-3,
        id_m=30e-3,
        ht_m=(100e-6)/((65e-3-30e-3)/2),
        b_sat_t=1.0,
        price_usd=6.00,
    ),
]

COILS: list[Coil] = [
    Coil(
        name="AWG 30 enamel",
        awg=30,
        wire_diameter_m=0.255e-3,
        resistance_per_m_ohm=0.345,
        price_per_m_usd=0.04,
        packing_factor=0.68,
        enamel_thickness_m=0.010e-3,   # typical single-coat (~10 µm)
        base_price_usd=0.0,
    ),
    Coil(
        name="AWG 28 enamel",
        awg=28,
        wire_diameter_m=0.321e-3,          # bare copper ~0.321 mm
        resistance_per_m_ohm=0.214,        # ohm/m at 20C (approx)
        price_per_m_usd=0.05,
        packing_factor=0.68,
        enamel_thickness_m=0.012e-3,
        base_price_usd=0.0,
    ),
    Coil(
        name="AWG 26 enamel",
        awg=26,
        wire_diameter_m=0.405e-3,
        resistance_per_m_ohm=0.135,
        price_per_m_usd=0.06,
        packing_factor=0.70,
        enamel_thickness_m=0.015e-3,
    ),
    Coil(
        name="AWG 24 enamel",
        awg=24,
        wire_diameter_m=0.511e-3,
        resistance_per_m_ohm=0.085,
        price_per_m_usd=0.07,
        packing_factor=0.72,
        enamel_thickness_m=0.018e-3,
    ),
    Coil(
        name="AWG 22 enamel",
        awg=22,
        wire_diameter_m=0.644e-3,
        resistance_per_m_ohm=0.0535,
        price_per_m_usd=0.09,
        packing_factor=0.73,
        enamel_thickness_m=0.020e-3,
    ),
]