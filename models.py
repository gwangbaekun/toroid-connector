# models.py
from dataclasses import dataclass
from math import pi, floor, sqrt, log

@dataclass
class Core:
	name: str
	mu_r: float                      # relative permeability
	area_m2: float                   # magnetic cross-sectional area [m^2]
	r_mean_m: float                  # mean magnetic radius [m]
	window_area_m2: float            # winding window area [m^2]
	b_sat_t: float | None = None     # optional saturation flux density [T]
	price_usd: float = 0.0

	# Optional geometric dimensions (before coating) to enable PDF-accurate path length
	# OD = outside diameter, ID = inside diameter, HT = height
	od_m: float | None = None
	id_m: float | None = None
	ht_m: float | None = None

	@property
	def path_length_m(self) -> float:
		# Prefer PDF formula when OD/ID are available:
		# le = π (OD - ID) / ln(OD/ID)
		if self.od_m is not None and self.id_m is not None and self.od_m > self.id_m > 0:
			try:
				return pi * (self.od_m - self.id_m) / log(self.od_m / self.id_m)
			except ValueError:
				# Fallback to mean-radius approximation when log argument invalid
				return 2 * pi * self.r_mean_m
		# Else, attempt to derive OD/ID/HT from available fields
		derived = self._derive_dimensions_from_fields()
		if derived is not None:
			od_m, id_m, _ht_m = derived
			try:
				return pi * (od_m - id_m) / log(od_m / id_m)
			except ValueError:
				return 2 * pi * self.r_mean_m
		# Magnetic path length ℓ ≈ 2π r_mean (approximation)
		return 2 * pi * self.r_mean_m

	def _derive_dimensions_from_fields(self) -> tuple[float, float, float] | None:
		"""Derive (OD, ID, HT) from existing fields when explicit dims are absent.

		Uses window area (hole) to get ID, mean radius to get OD, and area to get HT.
		Returns None if derivation is not possible.
		"""
		try:
			if self.window_area_m2 is None or self.window_area_m2 <= 0:
				return None
			# Window area Wa = π (ID/2)^2  =>  ID = 2 * sqrt(Wa / π)
			id_m = 2 * sqrt(self.window_area_m2 / pi)
			r_i = id_m / 2
			r_mean = self.r_mean_m
			r_o = max(r_i * 1.000001, 2 * r_mean - r_i)  # ensure positive width
			od_m = 2 * r_o
			width_m = max(1e-9, r_o - r_i)
			ht_m = self.area_m2 / width_m
			return (od_m, id_m, ht_m)
		except Exception:
			return None

@dataclass
class Coil:
	name: str
	awg: int
	wire_diameter_m: float           # bare copper diameter [m]
	resistance_per_m_ohm: float      # [ohm/m]
	price_per_m_usd: float           # [USD/m]
	packing_factor: float = 0.7      # fill efficiency 0..1
	base_price_usd: float = 0.0      # optional fixed cost per coil
	enamel_thickness_m: float = 0.0  # single-side enamel thickness [m]

	def max_turns_on(self, core: Core) -> int:
		# Approximate max turns from window fill using effective wire diameter
		# Effective diameter = bare + 2 * enamel
		effective_diameter = self.wire_diameter_m + 2 * max(0.0, self.enamel_thickness_m)
		wire_area = pi * (effective_diameter / 2) ** 2
		# Prefer window area computed from ID when dimensions are available
		if core.id_m is not None:
			window_area = pi * (core.id_m / 2) ** 2
		else:
			derived = core._derive_dimensions_from_fields()
			if derived is not None:
				_od_m, id_m, _ht_m = derived
				window_area = pi * (id_m / 2) ** 2
			else:
				window_area = core.window_area_m2

		usable_area = window_area * self.packing_factor
		if wire_area <= 0:
			return 0
		return max(0, floor(usable_area / wire_area))