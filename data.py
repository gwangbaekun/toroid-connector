# data.py
from models import Core, Coil

# Example, simplified data. Replace/extend with your catalog

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