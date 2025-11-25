from __future__ import annotations

import re
from abc import ABCMeta
from collections import Counter
from enum import Enum, EnumMeta
from typing import Any, Dict, List, Tuple

from ehubx.data import exceptions


# Literals
LOG_MODULE_STR: str = "data/unit"


class ABCEnumMeta(ABCMeta, EnumMeta):
    pass


class Unit:
    @classmethod
    def create(
        cls, numerator: List[BasicUnit] = [], denominator: List[BasicUnit] = []
    ) -> Unit:
        """
        Factory function to create a Unit from numerator and denominator BasicUnits.
        """
        # Count units
        num_counts = Counter(numerator)
        den_counts = Counter(denominator)

        # Cancel common units
        all_units = set(num_counts) | set(den_counts)
        final_num = []
        final_den = []

        for unit in all_units:
            diff = num_counts[unit] - den_counts[unit]
            if diff > 0:
                final_num.extend([unit] * diff)
            elif diff < 0:
                final_den.extend([unit] * -diff)

        if len(final_num) == 0 and len(final_den) == 0:
            return DimlessUnit()

        if len(final_num) == 1 and len(final_den) == 0:
            return final_num[0]

        return CompoundUnit._create(numerator=final_num, denominator=final_den)

    @classmethod
    def from_str(cls, s: str) -> Unit:
        s = s.strip()

        # First, check derived units
        if s in _DERIVED_UNIT_ALIASES:
            num, den = _DERIVED_UNIT_ALIASES[s]
            return Unit.create(num, den)

        if not s:
            return DimlessUnit()

        if re.search(r"/.*\*.*", s) and not re.search(r"/\s*\(", s):
            raise exceptions.UnitException(
                unit=s,
                msg=(
                    f"Ambiguous unit string '{s}'. Use parentheses to disambiguate "
                    "denominators, e.g. 'EUR/(kW*h)'."
                ),
                module=LOG_MODULE_STR,
            )

        def parse_units_part(part: str) -> List[BasicUnit]:
            part = part.strip()
            # Remove parentheses if the whole part is enclosed in ()
            if part.startswith("(") and part.endswith(")"):
                part = part[1:-1].strip()
            tokens = [t.strip() for t in part.split("*") if t.strip()]
            units = []
            for token in tokens:
                if token == "1":
                    continue
                match = re.fullmatch(r"([a-zA-Z]+)(\^|\*\*)(-?\d+)?", token)
                if match:
                    base, _, exp_str = match.groups()
                    exponent = int(exp_str) if exp_str else 1
                    unit = BasicUnit.from_str(base)
                    units.extend([unit] * exponent)
                else:
                    # Check if token is a derived unit first
                    if token in _DERIVED_UNIT_ALIASES:
                        num_units, den_units = _DERIVED_UNIT_ALIASES[token]
                        units.extend(num_units)
                        for d in den_units:
                            # Add to denominator
                            units.append(d)  # handled later as denominator in from_str
                        continue

                    # Otherwise, parse as basic
                    unit = BasicUnit.from_str(token)
                    units.append(unit)
            return units

        # Split by '/', all parts after first are denominator units
        parts = [p.strip() for p in s.split("/") if p.strip()]
        if not parts:
            return DimlessUnit()

        numerator_str = parts[0]
        denominator_strs = parts[1:]  # all subsequent parts go to denominator

        numerator_units = parse_units_part(numerator_str)

        # denominator units are all denominator parts joined with '*'
        # i.e. 'MW/GW' -> denominator units ['MW', 'GW']
        denominator_units = []
        for d_str in denominator_strs:
            denominator_units.extend(parse_units_part(d_str))

        return Unit.create(numerator_units, denominator_units)

    @classmethod
    def get_def_unit(cls, u: Unit) -> Unit:
        if isinstance(u, CompoundUnit):
            # Step 1: Normalize all subunits
            norm_num = [Unit.get_def_unit(n) for n in u.numerator]
            norm_den = [Unit.get_def_unit(d) for d in u.denominator]

            # Step 2: Count occurrences
            num_counts = Counter(norm_num)
            den_counts = Counter(norm_den)

            # Step 3: Cancel out shared units
            all_units = set(num_counts) | set(den_counts)
            final_num: List[BasicUnit] = []
            final_den: List[BasicUnit] = []

            for unit in all_units:
                assert isinstance(unit, BasicUnit)
                diff = num_counts[unit] - den_counts[unit]
                if diff > 0:
                    final_num.extend([unit] * diff)
                elif diff < 0:
                    final_den.extend([unit] * (-diff))

            # Step 4: If fully canceled, return a neutral "unit"
            if not final_num and not final_den:
                return DimlessUnit()

            return Unit.create(final_num, final_den)
        if isinstance(u, DimlessUnit):
            return DimlessUnit()
        if isinstance(u, BasicUnit):
            return _DEF_UNITS[type(u)]
        raise NotImplementedError()

    @classmethod
    def get_conv_factor_to_def_unit(cls, u: Unit) -> float:
        if isinstance(u, CompoundUnit):
            num_factor = 1.0
            for unit in u.numerator:
                num_factor *= Unit.get_conv_factor_to_def_unit(unit)

            den_factor = 1.0
            for unit in u.denominator:
                den_factor *= Unit.get_conv_factor_to_def_unit(unit)

            return num_factor / den_factor
        if isinstance(u, DimlessUnit):
            return 1.0
        if isinstance(u, BasicUnit):
            return _CONV_FACTORS_FOR_BASIC_UNITS[type(u)][u]
        raise NotImplementedError()

    def same_type_as(self, other: Unit) -> bool:
        """
        Check if this unit is of the same type as another unit.
        """
        return Unit.get_def_unit(self) == Unit.get_def_unit(other)

    def __mul__(self, other: Unit) -> Unit:
        if not isinstance(other, Unit):
            raise exceptions.UnitException(
                unit=str(other),
                msg=f"Cannot multiply with non-unit type: {type(other)}",
                module=LOG_MODULE_STR,
            )

        # Flatten units
        self_num = (
            self.numerator
            if isinstance(self, CompoundUnit)
            else [self]
            if isinstance(self, BasicUnit)
            else []
        )
        self_den = self.denominator if isinstance(self, CompoundUnit) else []

        other_num = (
            other.numerator
            if isinstance(other, CompoundUnit)
            else [other]
            if isinstance(other, BasicUnit)
            else []
        )
        other_den = other.denominator if isinstance(other, CompoundUnit) else []

        return Unit.create(
            numerator=self_num + other_num,
            denominator=self_den + other_den,
        )

    def __truediv__(self, other: Unit) -> Unit:
        if not isinstance(other, Unit):
            return NotImplemented

        # Flatten units
        self_num = (
            self.numerator
            if isinstance(self, CompoundUnit)
            else [self]
            if isinstance(self, BasicUnit)
            else []
        )
        self_den = self.denominator if isinstance(self, CompoundUnit) else []

        other_num = (
            other.numerator
            if isinstance(other, CompoundUnit)
            else [other]
            if isinstance(other, BasicUnit)
            else []
        )
        other_den = other.denominator if isinstance(other, CompoundUnit) else []

        return Unit.create(
            numerator=self_num + other_den,
            denominator=self_den + other_num,
        )

    def __pow__(self, exponent: int) -> Unit:
        if not isinstance(exponent, int):
            raise TypeError("Exponent must be an integer")

        if exponent == 0:
            return DimlessUnit()

        base_units = (
            [self]
            if isinstance(self, BasicUnit)
            else self.numerator
            if isinstance(self, CompoundUnit)
            else []
        )
        denom_units = self.denominator if isinstance(self, CompoundUnit) else []

        new_num = base_units * exponent
        new_den = denom_units * exponent

        return Unit.create(new_num, new_den)

    def root(self, deg: int) -> Unit:
        if deg <= 0:
            raise exceptions.UnitException(
                unit=str(self),
                msg=(
                    f"Failed to take root of unit '{self}' with degree {deg}: "
                    f"Root degree must be a positive integer."
                ),
                module=LOG_MODULE_STR,
            )

        if isinstance(self, DimlessUnit):
            return DimlessUnit()

        # Extract numerator and denominator unit lists
        if isinstance(self, BasicUnit):
            num_counts = Counter([self])
            den_counts: Counter[BasicUnit] = Counter()
        elif isinstance(self, CompoundUnit):
            num_counts = Counter(self.numerator)
            den_counts = Counter(self.denominator)
        else:
            raise TypeError(f"Unsupported unit type: {type(self)}")

        # Merge all units with their net exponents
        result_exp: Counter[BasicUnit] = Counter()
        all_units = set(num_counts) | set(den_counts)
        for unit in all_units:
            exp = num_counts[unit] - den_counts[unit]
            if exp % deg != 0:
                raise ValueError(
                    f"Cannot take root of unit '{self}': exponent of {unit} "
                    f"is {exp}, not divisible by {deg}."
                )
            result_exp[unit] = exp // deg

        # Rebuild numerator and denominator
        new_num = []
        new_den = []
        for unit, exp in result_exp.items():
            if exp > 0:
                new_num.extend([unit] * exp)
            elif exp < 0:
                new_den.extend([unit] * (-exp))

        return Unit.create(new_num, new_den)

    def as_key(self) -> Tuple[Tuple[Tuple[str, int], ...], Tuple[Tuple[str, int], ...]]:
        """
        Returns a normalized, hashable representation of the unit.
        Format: ((numerator unit strings), (denominator unit strings))
        """

        def count_units(units: List[BasicUnit]) -> Tuple[Tuple[str, int], ...]:
            return tuple(sorted(Counter(str(u) for u in units).items()))

        if isinstance(self, BasicUnit):
            return (((str(self), 1),), ())

        if isinstance(self, CompoundUnit):
            return count_units(self.numerator), count_units(self.denominator)

        if isinstance(self, DimlessUnit):
            return ((), ())

        raise TypeError(f"Unsupported unit type for hashing: {type(self)}")


class BasicUnit(Unit, Enum, metaclass=ABCEnumMeta):
    @classmethod
    def get_all(cls) -> List[BasicUnit]:
        """
        Returns a list of all basic units defined in the module.
        """
        basic_units = []
        for unit in cls.__subclasses__():
            basic_units += list(unit)
        return basic_units

    @classmethod
    def from_str(cls, s: str) -> BasicUnit:
        """
        Factory method to create a BasicUnit from a string.
        Returns None if the string does not match any BasicUnit.
        """
        s = s.strip()
        for unit in cls.get_all():
            if unit.value == s:
                return unit
        raise exceptions.UnitException(
            unit=s,
            msg=f"Unknown basic unit: '{s}'",
            module=LOG_MODULE_STR,
        )

    def __str__(self) -> str:
        return self.value


class PowerUnit(BasicUnit):
    """
    Enum for power units
    """

    W = "W"
    """Watt"""
    KW = "kW"
    """Kilowatt"""
    MW = "MW"
    """Megawatt"""
    GW = "GW"
    """Gigawatt"""
    TW = "TW"
    """Terawatt"""


class MassUnit(BasicUnit):
    """
    Enum for mass units
    """

    KG = "kg"
    """Kilogram"""
    T = "t"
    """Ton"""
    KT = "kt"
    """Kiloton"""
    MT = "mt"
    """Megaton"""


class CurrencyUnit(BasicUnit):
    """
    Enum for currency units
    """

    EUR = "EUR"
    """Euro"""
    kEUR = "kEUR"
    """Thousand Euro"""
    MEUR = "MEUR"
    """Million Euro"""
    USD = "USD"
    """US Dollar"""
    kUSD = "kUSD"
    """Thousand US Dollars"""
    MUSD = "MUSD"
    """Million US Dollars"""
    GBP = "GBP"
    """British Pound"""
    kGBP = "kGBP"
    """Thousand British Pounds"""
    MGBP = "MGBP"
    """Million British Pounds"""
    CHF = "CHF"
    """Swiss Franc"""
    kCHF = "kCHF"
    """Thousand Swiss Francs"""
    MCHF = "MCHF"
    """Million Swiss Francs"""


class TimeUnit(BasicUnit):
    """
    Enum for time units
    """

    S = "s"
    """Second"""
    MIN = "min"
    """Minute"""
    H = "h"
    """Hour"""
    D = "d"
    """Day"""
    A = "a"
    """Year"""


class LengthUnit(BasicUnit):
    """
    Enum for length units
    """

    M = "m"
    """Meter"""
    KM = "km"
    """Kilometer"""
    FT = "ft"
    """Foot"""
    MI = "mi"
    """Mile"""


class TemperatureUnit(BasicUnit):
    """
    Enum for temperature units
    """

    K = "K"
    """Kelvin"""


class DimlessUnit(Unit):
    """
    A unit representing a dimensionless quantity.
    This is a placeholder for cases where no specific unit is applicable.
    """

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DimlessUnit):
            return True
        return False

    def __str__(self):
        return "[-]"


class CompoundUnit(Unit):
    numerator: List[BasicUnit]
    denominator: List[BasicUnit]

    def __init__(self):
        raise RuntimeError(
            "Direct construction of CompoundUnit is forbidden. "
            "Use 'make_unit()' instead."
        )

    @classmethod
    def _create(cls, numerator: List[BasicUnit], denominator: List[BasicUnit]):
        self = cls.__new__(cls)
        self.numerator = numerator
        self.denominator = denominator
        return self

    def __str__(self) -> str:
        def unit_str(units):
            counts = Counter(units)
            parts = [
                f"{u}^{exp}" if exp != 1 else f"{u}"
                for u, exp in sorted(counts.items(), key=lambda x: x[0].value)
            ]
            return "*".join(parts)

        num_str = unit_str(self.numerator)
        den_str = unit_str(self.denominator)

        if den_str:
            return f"{num_str or '1'}/{den_str}"
        return num_str or "1"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Unit):
            return False
        if not isinstance(other, CompoundUnit):
            return False

        # Normalize both self and other using Unit.create
        norm_self = Unit.create(self.numerator, self.denominator)
        norm_other = Unit.create(other.numerator, other.denominator)

        # If both are CompoundUnits, compare numerator/denominator directly
        if isinstance(norm_self, CompoundUnit) and isinstance(norm_other, CompoundUnit):
            return Counter(norm_self.numerator) == Counter(
                norm_other.numerator
            ) and Counter(norm_self.denominator) == Counter(norm_other.denominator)

        # If both are BasicUnits or both are DimlessUnits, compare directly
        if not isinstance(norm_self, type(norm_other)) or not isinstance(
            norm_other, type(norm_self)
        ):
            return False

        return norm_self == norm_other  # Safe now, since they're not CompoundUnits


# Map string -> (numerator units, denominator units)
_DERIVED_UNIT_ALIASES: Dict[str, Tuple[List[BasicUnit], List[BasicUnit]]] = {
    "Ws": ([PowerUnit.W, TimeUnit.S], []),
    "kWh": ([PowerUnit.KW, TimeUnit.H], []),
    "MWh": ([PowerUnit.MW, TimeUnit.H], []),
    "GWh": ([PowerUnit.GW, TimeUnit.H], []),
    "TWh": ([PowerUnit.TW, TimeUnit.H], []),
}


_DEF_UNITS: Dict[type, BasicUnit] = {
    PowerUnit: PowerUnit.KW,
    MassUnit: MassUnit.KG,
    CurrencyUnit: CurrencyUnit.CHF,
    TimeUnit: TimeUnit.H,
    LengthUnit: LengthUnit.M,
    TemperatureUnit: TemperatureUnit.K,
}

_CONV_FACTORS_FOR_BASIC_UNITS: Dict[type, Dict[BasicUnit, float]] = {
    PowerUnit: {
        PowerUnit.W: 1e-3,
        PowerUnit.KW: 1e0,
        PowerUnit.MW: 1e3,
        PowerUnit.GW: 1e6,
        PowerUnit.TW: 1e9,
    },
    MassUnit: {
        MassUnit.KG: 1e0,
        MassUnit.T: 1e3,
        MassUnit.KT: 1e6,
        MassUnit.MT: 1e9,
    },
    CurrencyUnit: {
        # Note: The conversion factors for currency units are set to 1.0
        # because ehubX does not support real-time currency conversion.
        # All currency units are treated as equivalent for the purpose of
        # calculations. This means that the actual currency used does not
        # affect the calculations, and all currency units are treated as
        # having the same value in the model.
        CurrencyUnit.EUR: 1.0,
        CurrencyUnit.kEUR: 1e3,
        CurrencyUnit.MEUR: 1e6,
        CurrencyUnit.USD: 1.0,
        CurrencyUnit.kUSD: 1e3,
        CurrencyUnit.MUSD: 1e6,
        CurrencyUnit.GBP: 1.0,
        CurrencyUnit.kGBP: 1e3,
        CurrencyUnit.MGBP: 1e6,
        CurrencyUnit.CHF: 1.0,
        CurrencyUnit.kCHF: 1e3,
        CurrencyUnit.MCHF: 1e6,
    },
    TimeUnit: {
        TimeUnit.S: 1.0 / 3600.0,
        TimeUnit.MIN: 1.0 / 60.0,
        TimeUnit.H: 1.0,
        TimeUnit.D: 24.0,
        TimeUnit.A: 8760.0,
    },
    LengthUnit: {
        LengthUnit.M: 1.0,
        LengthUnit.KM: 1e3,
        LengthUnit.FT: 0.3048,  # 1 foot = 0.3048 meters
        LengthUnit.MI: 1609.34,  # 1 mile = 1609.34 meters
    },
    TemperatureUnit: {
        TemperatureUnit.K: 1.0,
    },
}
