"""
Laghu Parashari Core Module

Core analysis functions for Vedic astrology dasha analysis based on Laghu Parashari
principles. This module provides:
- Chart calculation using Swiss Ephemeris
- Shadbala (six-fold strength) calculation
- Functional nature (FB/FM) classification
- Vimshottari dasha period generation and classification
"""

import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum

import swisseph as swe

# =============================================================================
# CONSTANTS
# =============================================================================

class FunctionalNature(Enum):
    FB = "FB"  # Functional Benefic
    FM = "FM"  # Functional Malefic
    IMPRESSIONABLE = "IMP"  # Needs resolution based on associations
    NEUTRAL = "NEU"  # Neutral (kendra lords without trikona)

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

SIGN_ABBREV = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir",
               "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

SWE_PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}

SIGN_LORD = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORD = {
    0: "Ketu", 1: "Venus", 2: "Sun", 3: "Moon", 4: "Mars", 5: "Rahu",
    6: "Jupiter", 7: "Saturn", 8: "Mercury", 9: "Ketu", 10: "Venus", 11: "Sun",
    12: "Moon", 13: "Mars", 14: "Rahu", 15: "Jupiter", 16: "Saturn", 17: "Mercury",
    18: "Ketu", 19: "Venus", 20: "Sun", 21: "Moon", 22: "Mars", 23: "Rahu",
    24: "Jupiter", 25: "Saturn", 26: "Mercury"
}

VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

VIMSHOTTARI_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

PLANET_ORBS = {
    "Sun": 15, "Moon": 12, "Mars": 9, "Mercury": 7,
    "Jupiter": 9, "Venus": 7, "Saturn": 9, "Rahu": 15, "Ketu": 15
}

EFFECTIVE_ORB_MULTIPLIER = 1.33

ASPECT_DEGREES = {
    "Sun": [180], "Moon": [180], "Mercury": [180], "Venus": [180],
    "Mars": [90, 180, 210], "Jupiter": [120, 180, 240],
    "Saturn": [60, 180, 270], "Rahu": [120, 180, 240], "Ketu": [120, 180, 240],
}

# Shadbala Constants
EXALTATION_DEGREES = {
    "Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
    "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0,
}

DIG_BALA_STRONG_HOUSE = {
    "Sun": 10, "Moon": 4, "Mars": 10, "Mercury": 1,
    "Jupiter": 1, "Venus": 4, "Saturn": 7,
}

NAISARGIKA_BALA = {
    "Sun": 60.00, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
    "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57, "Rahu": 30.0, "Ketu": 30.0,
}

MIN_RUPAS_REQUIRED = {
    "Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
    "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0, "Rahu": 5.0, "Ketu": 5.0,
}

NATURAL_BENEFICS = {"Jupiter", "Venus"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
DAY_PLANETS = {"Sun", "Jupiter", "Venus"}
NIGHT_PLANETS = {"Moon", "Mars", "Saturn"}
HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
WEEKDAY_PLANET = {0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Sun"}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ShadbalaResult:
    """Six-fold strength calculation results in virupas (1 rupa = 60 virupas)."""
    uccha_bala: float = 0.0
    saptavargaja_bala: float = 0.0
    ojhayugma_bala: float = 0.0
    kendradi_bala: float = 0.0
    drekkana_bala: float = 0.0
    sthana_bala: float = 0.0
    dig_bala: float = 0.0
    kala_bala: float = 0.0
    chesta_bala: float = 0.0
    naisargika_bala: float = 0.0
    drig_bala: float = 0.0
    total_virupas: float = 0.0
    total_rupas: float = 0.0
    strength_class: str = "Medium"
    strength_percent: float = 0.0

@dataclass
class PlanetData:
    name: str
    longitude: float
    sign_index: int
    degree_in_sign: float
    nakshatra_index: int
    nakshatra_name: str
    house: int
    lordships: List[int] = field(default_factory=list)
    base_nature: FunctionalNature = FunctionalNature.NEUTRAL
    final_nature: FunctionalNature = FunctionalNature.NEUTRAL
    is_maraka: bool = False
    maraka_reason: str = ""
    virtual_longitude: Optional[float] = None
    exchange_partner: Optional[str] = None
    aspects_received: List[Dict] = field(default_factory=list)
    aspects_given: List[Dict] = field(default_factory=list)
    influences: List[str] = field(default_factory=list)
    shadbala: Optional[ShadbalaResult] = None
    speed: float = 0.0

@dataclass
class ChartData:
    birth_date: datetime
    latitude: float
    longitude: float
    timezone_offset: float
    ayanamsa: float
    lagna_degree: float
    lagna_sign: int
    julian_day: float = 0.0
    sunrise_jd: float = 0.0
    sunset_jd: float = 0.0
    is_day_birth: bool = True
    moon_phase: float = 0.0
    planets: Dict[str, PlanetData] = field(default_factory=dict)
    exchanges: List[Tuple[str, str]] = field(default_factory=list)

@dataclass
class DashaPeriod:
    md_lord: str
    ad_lord: str
    pd_lord: str
    start_date: datetime
    end_date: datetime
    md_nature: str
    ad_nature: str
    pd_nature: str
    md_maraka: bool
    ad_maraka: bool
    pd_maraka: bool
    overall_result: str = ""
    affected_houses: str = ""

@dataclass
class AnalysisResult:
    chart: ChartData
    dasha_periods: List[DashaPeriod]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def norm_deg(x: float) -> float:
    return x % 360.0

def angular_distance(a: float, b: float) -> float:
    diff = abs(a - b)
    return 360 - diff if diff > 180 else diff

def get_sign_index(lon: float) -> int:
    return int(norm_deg(lon) / 30.0)

def get_nakshatra_index(lon: float) -> int:
    return int(norm_deg(lon) / (360.0 / 27.0))

# =============================================================================
# SHADBALA CALCULATION
# =============================================================================

def calculate_uccha_bala(planet_name: str, longitude: float) -> float:
    if planet_name not in EXALTATION_DEGREES:
        return 30.0
    exalt_deg = EXALTATION_DEGREES[planet_name]
    debil_deg = norm_deg(exalt_deg + 180)
    dist_from_debil = angular_distance(longitude, debil_deg)
    return (dist_from_debil / 180.0) * 60.0

def calculate_saptavargaja_bala(planet_name: str, longitude: float) -> float:
    total = 0.0
    sign_idx = get_sign_index(longitude)
    sign_lord = SIGN_LORD[sign_idx]
    
    if sign_lord == planet_name:
        total += 30.0
    elif planet_name in EXALTATION_DEGREES:
        exalt_sign = get_sign_index(EXALTATION_DEGREES[planet_name])
        total += 45.0 if sign_idx == exalt_sign else 15.0
    else:
        total += 15.0
    
    navamsa_long = (longitude * 9) % 360.0
    navamsa_sign = get_sign_index(navamsa_long)
    total += 30.0 if SIGN_LORD[navamsa_sign] == planet_name else 15.0
    
    drekkana_long = (longitude * 3) % 360.0
    total += 30.0 if SIGN_LORD[get_sign_index(drekkana_long)] == planet_name else 15.0
    
    hora_deg = longitude % 30.0
    is_day_hora = hora_deg < 15.0
    if (planet_name == "Sun" and is_day_hora) or (planet_name == "Moon" and not is_day_hora):
        total += 30.0
    else:
        total += 15.0
    
    return total / 4.0

def calculate_ojhayugma_bala(planet_name: str, sign_index: int) -> float:
    is_odd_sign = sign_index % 2 == 0
    odd_strong = {"Sun", "Mars", "Jupiter", "Mercury", "Saturn"}
    even_strong = {"Moon", "Venus"}
    
    if planet_name in odd_strong:
        return 15.0 if is_odd_sign else 0.0
    elif planet_name in even_strong:
        return 15.0 if not is_odd_sign else 0.0
    return 7.5

def calculate_kendradi_bala(house: int) -> float:
    if house in [1, 4, 7, 10]:
        return 60.0
    elif house in [2, 5, 8, 11]:
        return 30.0
    return 15.0

def calculate_drekkana_bala(planet_name: str, degree_in_sign: float) -> float:
    male_planets = {"Sun", "Mars", "Jupiter"}
    neutral_planets = {"Mercury", "Saturn", "Rahu", "Ketu"}
    female_planets = {"Moon", "Venus"}
    
    if degree_in_sign < 10.0:
        return 15.0 if planet_name in male_planets else 0.0
    elif degree_in_sign < 20.0:
        return 15.0 if planet_name in neutral_planets else 0.0
    return 15.0 if planet_name in female_planets else 0.0

def calculate_sthana_bala(planet: PlanetData) -> Tuple[float, float, float, float, float, float]:
    uccha = calculate_uccha_bala(planet.name, planet.longitude)
    saptavargaja = calculate_saptavargaja_bala(planet.name, planet.longitude)
    ojhayugma = calculate_ojhayugma_bala(planet.name, planet.sign_index)
    kendradi = calculate_kendradi_bala(planet.house)
    drekkana = calculate_drekkana_bala(planet.name, planet.degree_in_sign)
    total = uccha + saptavargaja + ojhayugma + kendradi + drekkana
    return (uccha, saptavargaja, ojhayugma, kendradi, drekkana, total)

def calculate_dig_bala(planet_name: str, house: int) -> float:
    if planet_name not in DIG_BALA_STRONG_HOUSE:
        return 30.0
    strong_house = DIG_BALA_STRONG_HOUSE[planet_name]
    distance = abs(house - strong_house)
    if distance > 6:
        distance = 12 - distance
    return max(0.0, 60.0 * (1.0 - distance / 6.0))

def calculate_kala_bala(chart: ChartData, planet_name: str) -> float:
    total = 0.0
    
    if planet_name in DAY_PLANETS:
        total += 60.0 if chart.is_day_birth else 0.0
    elif planet_name in NIGHT_PLANETS:
        total += 60.0 if not chart.is_day_birth else 0.0
    else:
        total += 30.0
    
    is_shukla = chart.moon_phase < 0.5
    if planet_name == "Moon":
        if is_shukla:
            total += chart.moon_phase * 2 * 60.0
        else:
            total += (1.0 - chart.moon_phase) * 2 * 60.0
    elif planet_name in NATURAL_BENEFICS:
        total += 60.0 if is_shukla else 30.0
    elif planet_name in NATURAL_MALEFICS:
        total += 30.0 if is_shukla else 60.0
    else:
        total += 30.0
    
    jd = chart.julian_day
    if chart.is_day_birth:
        day_length = chart.sunset_jd - chart.sunrise_jd
        time_in_day = jd - chart.sunrise_jd
        third = int(time_in_day / day_length * 3) if day_length > 0 else 0
        tribhaga_lords = ["Mercury", "Sun", "Saturn"]
    else:
        night_length = chart.sunrise_jd + 1 - chart.sunset_jd
        time_in_night = jd - chart.sunset_jd if jd > chart.sunset_jd else jd + 1 - chart.sunset_jd
        third = min(2, int(time_in_night / night_length * 3)) if night_length > 0 else 0
        tribhaga_lords = ["Moon", "Venus", "Mars"]
    
    total += 60.0 if planet_name == tribhaga_lords[third] else 0.0
    
    weekday = chart.birth_date.weekday()
    weekday_lord = WEEKDAY_PLANET.get(weekday, "Sun")
    total += 45.0 if planet_name == weekday_lord else 15.0
    
    hours_since_sunrise = (jd - chart.sunrise_jd) * 24
    hora_index = int(hours_since_sunrise) % 7
    weekday_start_idx = HORA_SEQUENCE.index(weekday_lord) if weekday_lord in HORA_SEQUENCE else 0
    hora_lord = HORA_SEQUENCE[(weekday_start_idx + hora_index) % 7]
    total += 60.0 if planet_name == hora_lord else 15.0
    
    return total

def calculate_chesta_bala(planet_name: str, speed: float) -> float:
    MEAN_SPEEDS = {
        "Sun": 0.9856, "Moon": 13.176, "Mars": 0.524, "Mercury": 1.383,
        "Jupiter": 0.083, "Venus": 1.201, "Saturn": 0.034, "Rahu": -0.053, "Ketu": -0.053,
    }
    
    if planet_name not in MEAN_SPEEDS:
        return 30.0
    mean_speed = MEAN_SPEEDS[planet_name]
    
    if planet_name in ["Sun", "Moon"]:
        ratio = speed / mean_speed if mean_speed != 0 else 1.0
        if ratio > 1.1:
            return 60.0
        elif ratio < 0.9:
            return 30.0
        return 45.0
    
    if planet_name in ["Rahu", "Ketu"]:
        return 45.0
    
    if speed < 0:
        return 60.0
    elif abs(speed) < 0.1 * abs(mean_speed):
        return 45.0
    elif speed < 0.5 * mean_speed:
        return 30.0
    return 15.0 + (speed / mean_speed) * 15.0

def calculate_naisargika_bala(planet_name: str) -> float:
    return NAISARGIKA_BALA.get(planet_name, 30.0)

def calculate_drig_bala(chart: ChartData, planet_name: str) -> float:
    planet = chart.planets[planet_name]
    drig_bala = 0.0
    moon_is_benefic = chart.moon_phase < 0.5
    
    for aspect in planet.aspects_received:
        aspector_name = aspect["from"]
        aspect_strength = 60.0 / len(planet.aspects_received) if planet.aspects_received else 15.0
        
        if aspector_name in NATURAL_BENEFICS:
            drig_bala += aspect_strength
        elif aspector_name in NATURAL_MALEFICS:
            drig_bala -= aspect_strength * 0.5
        elif aspector_name == "Moon":
            drig_bala += aspect_strength * 0.75 if moon_is_benefic else -aspect_strength * 0.25
    
    return max(-60.0, min(60.0, drig_bala))

def calculate_shadbala(chart: ChartData) -> None:
    for planet_name, planet in chart.planets.items():
        uccha, saptavargaja, ojhayugma, kendradi, drekkana, sthana_total = calculate_sthana_bala(planet)
        dig = calculate_dig_bala(planet_name, planet.house)
        kala = calculate_kala_bala(chart, planet_name)
        chesta = calculate_chesta_bala(planet_name, planet.speed)
        naisargika = calculate_naisargika_bala(planet_name)
        drig = calculate_drig_bala(chart, planet_name)
        
        total_virupas = sthana_total + dig + kala + chesta + naisargika + drig
        total_rupas = total_virupas / 60.0
        
        min_required = MIN_RUPAS_REQUIRED.get(planet_name, 5.0)
        if total_rupas >= min_required * 1.2:
            strength_class = "Strong"
        elif total_rupas >= min_required * 0.8:
            strength_class = "Medium"
        else:
            strength_class = "Weak"
        
        strength_percent = (total_rupas / min_required) * 100.0
        
        planet.shadbala = ShadbalaResult(
            uccha_bala=uccha, saptavargaja_bala=saptavargaja, ojhayugma_bala=ojhayugma,
            kendradi_bala=kendradi, drekkana_bala=drekkana, sthana_bala=sthana_total,
            dig_bala=dig, kala_bala=kala, chesta_bala=chesta, naisargika_bala=naisargika,
            drig_bala=drig, total_virupas=total_virupas, total_rupas=total_rupas,
            strength_class=strength_class, strength_percent=strength_percent
        )

# =============================================================================
# CHART CALCULATION
# =============================================================================

def calculate_ayanamsa(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa_ut(jd)

def calculate_chart(date_str: str, time_str: str, lat: float, lon: float, tz_offset: float) -> ChartData:
    date_parts = [int(x) for x in date_str.split('-')]
    time_parts = [int(x) for x in time_str.split(':')]
    year, month, day = date_parts
    hour, minute = time_parts[0], time_parts[1] if len(time_parts) > 1 else 0
    
    decimal_hour = hour + minute / 60.0 - tz_offset
    jd_ut = swe.julday(year, month, day, decimal_hour)
    ayanamsa = calculate_ayanamsa(jd_ut)
    
    houses, ascmc = swe.houses(jd_ut, lat, lon, b'P')
    lagna_tropical = ascmc[0]
    lagna_sidereal = norm_deg(lagna_tropical - ayanamsa)
    lagna_sign = get_sign_index(lagna_sidereal)
    
    try:
        sunrise_result = swe.rise_trans(jd_ut - 0.5, swe.SUN, lon, lat, 0, 0, 1)
        sunrise_jd = sunrise_result[1][0] if sunrise_result[0] >= 0 else jd_ut - 0.25
        sunset_result = swe.rise_trans(jd_ut - 0.5, swe.SUN, lon, lat, 0, 0, 2)
        sunset_jd = sunset_result[1][0] if sunset_result[0] >= 0 else jd_ut + 0.25
    except:
        sunrise_jd = jd_ut - (decimal_hour / 24.0) + (6.0 / 24.0)
        sunset_jd = sunrise_jd + 0.5
    
    is_day_birth = sunrise_jd <= jd_ut <= sunset_jd
    
    sun_result, _ = swe.calc_ut(jd_ut, swe.SUN)
    moon_result, _ = swe.calc_ut(jd_ut, swe.MOON)
    moon_phase = ((moon_result[0] - sun_result[0]) % 360.0) / 360.0
    
    birth_dt = datetime(year, month, day, hour, minute)
    chart = ChartData(
        birth_date=birth_dt, latitude=lat, longitude=lon, timezone_offset=tz_offset,
        ayanamsa=ayanamsa, lagna_degree=lagna_sidereal, lagna_sign=lagna_sign,
        julian_day=jd_ut, sunrise_jd=sunrise_jd, sunset_jd=sunset_jd,
        is_day_birth=is_day_birth, moon_phase=moon_phase
    )
    
    for planet_name, swe_code in SWE_PLANETS.items():
        result, flag = swe.calc_ut(jd_ut, swe_code)
        lon_sidereal = norm_deg(result[0] - ayanamsa)
        sign_idx = get_sign_index(lon_sidereal)
        nak_idx = get_nakshatra_index(lon_sidereal)
        house = ((sign_idx - lagna_sign) % 12) + 1
        
        chart.planets[planet_name] = PlanetData(
            name=planet_name, longitude=lon_sidereal, sign_index=sign_idx,
            degree_in_sign=lon_sidereal % 30.0, nakshatra_index=nak_idx,
            nakshatra_name=NAKSHATRAS[nak_idx], house=house, speed=result[3]
        )
    
    rahu = chart.planets["Rahu"]
    ketu_lon = norm_deg(rahu.longitude + 180)
    ketu_sign = get_sign_index(ketu_lon)
    ketu_nak = get_nakshatra_index(ketu_lon)
    chart.planets["Ketu"] = PlanetData(
        name="Ketu", longitude=ketu_lon, sign_index=ketu_sign,
        degree_in_sign=ketu_lon % 30.0, nakshatra_index=ketu_nak,
        nakshatra_name=NAKSHATRAS[ketu_nak], house=((ketu_sign - lagna_sign) % 12) + 1
    )
    
    return chart

# =============================================================================
# LORDSHIP & NATURE CLASSIFICATION
# =============================================================================

def calculate_lordships(chart: ChartData) -> None:
    lagna_sign = chart.lagna_sign
    for planet in chart.planets.values():
        planet.lordships = []
    for house_num in range(1, 13):
        house_sign = (lagna_sign + house_num - 1) % 12
        lord_name = SIGN_LORD[house_sign]
        if lord_name in chart.planets:
            chart.planets[lord_name].lordships.append(house_num)

def classify_base_nature(chart: ChartData) -> None:
    TRIKONA = {1, 5, 9}
    KENDRA = {1, 4, 7, 10}
    TRISHADAYA = {3, 6, 11}
    
    for planet in chart.planets.values():
        if planet.name in ["Rahu", "Ketu"]:
            planet.base_nature = FunctionalNature.IMPRESSIONABLE
            continue
        
        lordships = set(planet.lordships)
        if not lordships:
            planet.base_nature = FunctionalNature.NEUTRAL
            continue
        
        has_trikona = bool(lordships & TRIKONA)
        has_kendra = bool(lordships & KENDRA)
        has_trishadaya = bool(lordships & TRISHADAYA)
        has_8th = 8 in lordships
        has_2nd = 2 in lordships
        has_12th = 12 in lordships
        has_1st = 1 in lordships
        has_3rd = 3 in lordships
        has_10th = 10 in lordships
        
        pure_kendra = lordships & {4, 7, 10}
        pure_trikona = lordships & {5, 9}
        
        if pure_kendra and pure_trikona:
            planet.base_nature = FunctionalNature.FB
        elif has_trikona:
            planet.base_nature = FunctionalNature.FB
        elif has_3rd and has_10th:
            planet.base_nature = FunctionalNature.IMPRESSIONABLE
        elif has_trishadaya and not has_trikona:
            planet.base_nature = FunctionalNature.FM
        elif has_8th and not has_1st:
            planet.base_nature = FunctionalNature.FM
        elif (has_2nd or has_12th) and not has_trikona and not has_trishadaya:
            if lordships <= {2, 4, 7, 10, 12}:
                planet.base_nature = FunctionalNature.IMPRESSIONABLE
        elif pure_kendra and not has_trikona and not has_trishadaya:
            planet.base_nature = FunctionalNature.NEUTRAL
        else:
            planet.base_nature = FunctionalNature.NEUTRAL

# =============================================================================
# EXCHANGE DETECTION
# =============================================================================

def detect_exchanges(chart: ChartData) -> None:
    chart.exchanges = []
    planets_list = [p for p in chart.planets.values() if p.name not in ["Rahu", "Ketu"]]
    
    for i, p1 in enumerate(planets_list):
        for p2 in planets_list[i+1:]:
            p1_sign_lord = SIGN_LORD[p1.sign_index]
            p2_sign_lord = SIGN_LORD[p2.sign_index]
            
            if p1_sign_lord == p2.name and p2_sign_lord == p1.name:
                chart.exchanges.append((p1.name, p2.name))
                p1.exchange_partner = p2.name
                p2.exchange_partner = p1.name
                p1.virtual_longitude = norm_deg((p2.sign_index * 30) + p1.degree_in_sign)
                p2.virtual_longitude = norm_deg((p1.sign_index * 30) + p2.degree_in_sign)

# =============================================================================
# ASPECT CALCULATION
# =============================================================================

def calculate_aspects(chart: ChartData) -> None:
    all_planets = list(chart.planets.values())
    for aspecting_planet in all_planets:
        effective_orb = PLANET_ORBS[aspecting_planet.name] * EFFECTIVE_ORB_MULTIPLIER
        aspect_degrees = ASPECT_DEGREES.get(aspecting_planet.name, [180])
        _check_aspects_from_position(aspecting_planet, aspecting_planet.longitude, "physical",
                                     effective_orb, aspect_degrees, all_planets)
        if aspecting_planet.virtual_longitude is not None:
            _check_aspects_from_position(aspecting_planet, aspecting_planet.virtual_longitude, "virtual",
                                         effective_orb, aspect_degrees, all_planets)

def _check_aspects_from_position(aspecting_planet: PlanetData, from_longitude: float,
                                  position_type: str, effective_orb: float,
                                  aspect_degrees: List[int], all_planets: List[PlanetData]) -> None:
    aspect_names = {90: "4th", 180: "7th", 210: "8th", 120: "5th", 240: "9th", 60: "3rd", 270: "10th"}
    
    for asp_deg in aspect_degrees:
        aspect_point = norm_deg(from_longitude + asp_deg)
        for target_planet in all_planets:
            if target_planet.name == aspecting_planet.name:
                continue
            dist = angular_distance(aspect_point, target_planet.longitude)
            if dist <= effective_orb:
                aspect_info = {
                    "from": aspecting_planet.name, "to": target_planet.name,
                    "aspect_type": aspect_names.get(asp_deg, f"{asp_deg}°"), "orb": round(dist, 2),
                    "from_position": position_type, "to_position": "physical"
                }
                aspecting_planet.aspects_given.append(aspect_info)
                target_planet.aspects_received.append(aspect_info)

def calculate_conjunctions(chart: ChartData) -> None:
    all_planets = list(chart.planets.values())
    for i, p1 in enumerate(all_planets):
        for p2 in all_planets[i+1:]:
            if p1.sign_index == p2.sign_index:
                orb = min(PLANET_ORBS[p1.name], PLANET_ORBS[p2.name]) * EFFECTIVE_ORB_MULTIPLIER
                dist = angular_distance(p1.longitude, p2.longitude)
                if dist <= orb:
                    p1.aspects_received.append({"from": p2.name, "to": p1.name, "aspect_type": "conj",
                                                "orb": round(dist, 2), "from_position": "physical", "to_position": "physical"})
                    p2.aspects_received.append({"from": p1.name, "to": p2.name, "aspect_type": "conj",
                                                "orb": round(dist, 2), "from_position": "physical", "to_position": "physical"})

# =============================================================================
# IMPRESSIONABLE PLANET RESOLUTION
# =============================================================================

def calculate_exchange_weight(planet: PlanetData, partner: PlanetData) -> float:
    deg_diff = abs(planet.degree_in_sign - partner.degree_in_sign)
    if deg_diff <= 5:
        return 3.0
    elif deg_diff <= 15:
        return 2.0
    elif deg_diff <= 25:
        return 1.0
    return 0.5

def find_degree_sambandha(planet: PlanetData, chart: ChartData,
                          fixed_planets: Dict[str, PlanetData]) -> List[Tuple[str, float, str]]:
    DEGREE_ORB = 5.0
    sambandhas = []
    for other_name, other_planet in chart.planets.items():
        if other_name == planet.name or not other_planet.exchange_partner:
            continue
        deg_diff = abs(planet.degree_in_sign - other_planet.degree_in_sign)
        if deg_diff <= DEGREE_ORB and other_name in fixed_planets:
            weight = (DEGREE_ORB - deg_diff) / DEGREE_ORB * 2.0
            nature = fixed_planets[other_name].final_nature.value
            sambandhas.append((other_name, weight, f"deg-conj {other_name}({nature}) {deg_diff:.1f}°"))
    return sambandhas

def resolve_impressionable_planets(chart: ChartData) -> None:
    fixed_planets = {}
    impressionable_planets = {}
    
    for name, planet in chart.planets.items():
        if planet.base_nature in [FunctionalNature.FB, FunctionalNature.FM]:
            planet.final_nature = planet.base_nature
            fixed_planets[name] = planet
        else:
            impressionable_planets[name] = planet
    
    max_iterations = 10
    iteration = 0
    
    while impressionable_planets and iteration < max_iterations:
        iteration += 1
        resolved_this_round = []
        
        for name, planet in impressionable_planets.items():
            fb_score, fm_score = 0.0, 0.0
            influences = []
            
            if planet.exchange_partner:
                partner = chart.planets.get(planet.exchange_partner)
                if partner and partner.name in fixed_planets:
                    exchange_weight = calculate_exchange_weight(planet, partner)
                    deg_diff = abs(planet.degree_in_sign - partner.degree_in_sign)
                    if partner.final_nature == FunctionalNature.FB:
                        fb_score += exchange_weight
                        influences.append(f"Exch {partner.name}(FB) {deg_diff:.0f}° wt:{exchange_weight:.1f}")
                    elif partner.final_nature == FunctionalNature.FM:
                        fm_score += exchange_weight
                        influences.append(f"Exch {partner.name}(FM) {deg_diff:.0f}° wt:{exchange_weight:.1f}")
            
            for other_name, weight, desc in find_degree_sambandha(planet, chart, fixed_planets):
                other = fixed_planets[other_name]
                if other.final_nature == FunctionalNature.FB:
                    fb_score += weight
                elif other.final_nature == FunctionalNature.FM:
                    fm_score += weight
                influences.append(desc)
            
            for aspect in planet.aspects_received:
                aspector_name = aspect["from"]
                if aspector_name in fixed_planets:
                    aspector = fixed_planets[aspector_name]
                    if aspector.final_nature == FunctionalNature.FB:
                        fb_score += 1.0
                        influences.append(f"{aspector_name}(FB) {aspect['aspect_type']}")
                    elif aspector.final_nature == FunctionalNature.FM:
                        fm_score += 1.0
                        influences.append(f"{aspector_name}(FM) {aspect['aspect_type']}")
            
            if fb_score > 0 or fm_score > 0:
                planet.influences = influences
                if fb_score > fm_score:
                    planet.final_nature = FunctionalNature.FB
                elif fm_score > fb_score:
                    planet.final_nature = FunctionalNature.FM
                else:
                    if planet.shadbala and planet.shadbala.strength_class == "Strong":
                        planet.final_nature = FunctionalNature.FB
                        influences.append(f"Tie→FB (Strong Shadbala: {planet.shadbala.total_rupas:.1f}R)")
                    elif planet.shadbala and planet.shadbala.strength_class == "Weak":
                        planet.final_nature = FunctionalNature.FM
                        influences.append(f"Tie→FM (Weak Shadbala: {planet.shadbala.total_rupas:.1f}R)")
                    else:
                        planet.final_nature = FunctionalNature.FB
                        if planet.shadbala:
                            influences.append(f"Tie→FB (Medium Shadbala: {planet.shadbala.total_rupas:.1f}R)")
                
                fixed_planets[name] = planet
                resolved_this_round.append(name)
        
        for name in resolved_this_round:
            del impressionable_planets[name]
    
    for name, planet in impressionable_planets.items():
        if planet.house in [1, 4, 5, 7, 9, 10]:
            planet.final_nature = FunctionalNature.FB
        else:
            planet.final_nature = FunctionalNature.FM
        planet.influences.append("Default by house placement")

# =============================================================================
# MARAKA CLASSIFICATION
# =============================================================================

def classify_marakas(chart: ChartData) -> None:
    lagna_sign = chart.lagna_sign
    lord_2 = SIGN_LORD[(lagna_sign + 1) % 12]
    lord_7 = SIGN_LORD[(lagna_sign + 6) % 12]
    lord_3 = SIGN_LORD[(lagna_sign + 2) % 12]
    lord_6 = SIGN_LORD[(lagna_sign + 5) % 12]
    lord_11 = SIGN_LORD[(lagna_sign + 10) % 12]
    
    trishadaya_lords = {lord_3, lord_6, lord_11}
    maraka_lords = {lord_2, lord_7}
    
    for maraka_lord_name in maraka_lords:
        planet = chart.planets.get(maraka_lord_name)
        if not planet:
            continue
        
        associated_trishadaya = []
        if planet.exchange_partner in trishadaya_lords:
            associated_trishadaya.append(f"exchange w/{planet.exchange_partner}")
        for aspect in planet.aspects_received:
            if aspect["from"] in trishadaya_lords:
                associated_trishadaya.append(f"{aspect['from']} {aspect['aspect_type']}")
        for tri_lord in trishadaya_lords:
            tri_planet = chart.planets.get(tri_lord)
            if tri_planet and tri_planet.sign_index == planet.sign_index and tri_lord != maraka_lord_name:
                dist = angular_distance(planet.longitude, tri_planet.longitude)
                orb = min(PLANET_ORBS[planet.name], PLANET_ORBS[tri_lord]) * EFFECTIVE_ORB_MULTIPLIER
                if dist <= orb:
                    associated_trishadaya.append(f"conj {tri_lord}")
        
        if associated_trishadaya:
            planet.is_maraka = True
            which_lord = "2L" if 2 in planet.lordships else "7L"
            planet.maraka_reason = f"{which_lord} + {', '.join(associated_trishadaya)}"

# =============================================================================
# VIMSHOTTARI DASHA ENGINE
# =============================================================================

def calculate_vimshottari_dashas(chart: ChartData, start_year: int, end_year: int) -> List[DashaPeriod]:
    moon = chart.planets["Moon"]
    nak_idx = moon.nakshatra_index
    nak_lord = NAKSHATRA_LORD[nak_idx]
    
    nak_span = 360.0 / 27.0
    nak_start = nak_idx * nak_span
    portion_remaining = 1.0 - (moon.longitude - nak_start) / nak_span
    balance_years = VIMSHOTTARI_YEARS[nak_lord] * portion_remaining
    
    birth_date = chart.birth_date
    start_idx = VIMSHOTTARI_SEQUENCE.index(nak_lord)
    
    all_periods = []
    current_date = birth_date
    target_start = datetime(start_year, 1, 1)
    target_end = datetime(end_year, 12, 31)
    
    md_idx = start_idx
    
    while current_date < target_end:
        md_lord = VIMSHOTTARI_SEQUENCE[md_idx % 9]
        md_years = VIMSHOTTARI_YEARS[md_lord] if md_idx != start_idx else balance_years
        md_end = current_date + timedelta(days=md_years * 365.25)
        
        if md_end >= target_start:
            ad_periods = _generate_antardashas(chart, md_lord, current_date, md_end, target_start, target_end)
            all_periods.extend(ad_periods)
        
        current_date = md_end
        md_idx += 1
        
        if (current_date - birth_date).days > 200 * 365:
            break
    
    return all_periods

def _generate_antardashas(chart: ChartData, md_lord: str, md_start: datetime, md_end: datetime,
                          target_start: datetime, target_end: datetime) -> List[DashaPeriod]:
    md_total_days = (md_end - md_start).days
    ad_start_idx = VIMSHOTTARI_SEQUENCE.index(md_lord)
    
    periods = []
    ad_current = md_start
    
    for i in range(9):
        ad_lord = VIMSHOTTARI_SEQUENCE[(ad_start_idx + i) % 9]
        ad_proportion = VIMSHOTTARI_YEARS[ad_lord] / 120.0
        ad_days = md_total_days * ad_proportion
        ad_end = ad_current + timedelta(days=ad_days)
        
        if ad_end >= target_start and ad_current <= target_end:
            pd_periods = _generate_pratyantardashas(chart, md_lord, ad_lord, ad_current, ad_end, target_start, target_end)
            periods.extend(pd_periods)
        
        ad_current = ad_end
        if ad_current > md_end:
            break
    
    return periods

def _generate_pratyantardashas(chart: ChartData, md_lord: str, ad_lord: str,
                                ad_start: datetime, ad_end: datetime,
                                target_start: datetime, target_end: datetime) -> List[DashaPeriod]:
    ad_total_days = (ad_end - ad_start).days
    pd_start_idx = VIMSHOTTARI_SEQUENCE.index(ad_lord)
    
    periods = []
    pd_current = ad_start
    
    for i in range(9):
        pd_lord = VIMSHOTTARI_SEQUENCE[(pd_start_idx + i) % 9]
        pd_proportion = VIMSHOTTARI_YEARS[pd_lord] / 120.0
        pd_days = ad_total_days * pd_proportion
        pd_end = pd_current + timedelta(days=pd_days)
        
        if pd_end >= target_start and pd_current <= target_end:
            md_planet = chart.planets[md_lord]
            ad_planet = chart.planets[ad_lord]
            pd_planet = chart.planets[pd_lord]
            
            md_display = f"{md_planet.final_nature.value}+Mrk" if md_planet.is_maraka else md_planet.final_nature.value
            ad_display = f"{ad_planet.final_nature.value}+Mrk" if ad_planet.is_maraka else ad_planet.final_nature.value
            pd_display = f"{pd_planet.final_nature.value}+Mrk" if pd_planet.is_maraka else pd_planet.final_nature.value
            
            overall_result = classify_dasha_result_laghu_parashari(chart, md_lord, ad_lord, pd_lord)
            affected_houses = get_dasha_affected_houses(chart, md_lord, ad_lord, pd_lord)
            
            periods.append(DashaPeriod(
                md_lord=md_lord, ad_lord=ad_lord, pd_lord=pd_lord,
                start_date=pd_current, end_date=pd_end,
                md_nature=md_display, ad_nature=ad_display, pd_nature=pd_display,
                md_maraka=md_planet.is_maraka, ad_maraka=ad_planet.is_maraka, pd_maraka=pd_planet.is_maraka,
                overall_result=overall_result, affected_houses=affected_houses
            ))
        
        pd_current = pd_end
        if pd_current > ad_end:
            break
    
    return periods

# =============================================================================
# DASHA CLASSIFICATION
# =============================================================================

def get_aspected_houses(chart: ChartData, planet_name: str) -> List[int]:
    planet = chart.planets.get(planet_name)
    if not planet:
        return []
    
    aspect_offsets = {
        "Sun": [6], "Moon": [6], "Mercury": [6], "Venus": [6],
        "Mars": [3, 6, 7], "Jupiter": [4, 6, 8], "Saturn": [2, 6, 9],
        "Rahu": [4, 6, 8], "Ketu": [4, 6, 8]
    }
    
    offsets = aspect_offsets.get(planet_name, [6])
    return sorted(set(((planet.house - 1 + offset) % 12) + 1 for offset in offsets))

def get_planet_affected_houses(chart: ChartData, planet_name: str) -> Dict[str, List[int]]:
    planet = chart.planets.get(planet_name)
    if not planet:
        return {'aspect': [], 'placement': [], 'lordship': []}
    return {
        'aspect': get_aspected_houses(chart, planet_name),
        'placement': [planet.house],
        'lordship': sorted(planet.lordships) if planet.lordships else []
    }

def get_dasha_affected_houses(chart: ChartData, md_lord: str, ad_lord: str, pd_lord: str) -> str:
    md_houses = get_planet_affected_houses(chart, md_lord)
    ad_houses = get_planet_affected_houses(chart, ad_lord)
    pd_houses = get_planet_affected_houses(chart, pd_lord)
    
    house_info = {}
    priorities = {'aspect': 1, 'placement': 2, 'lordship': 3}
    
    for category in ['aspect', 'placement', 'lordship']:
        pri = priorities[category]
        prefix = category[0]
        for h in md_houses[category]:
            house_info.setdefault(h, []).append((pri, f"{prefix}:MD"))
        for h in ad_houses[category]:
            house_info.setdefault(h, []).append((pri, f"{prefix}:AD"))
        for h in pd_houses[category]:
            house_info.setdefault(h, []).append((pri, f"{prefix}:PD"))
    
    sorted_houses = sorted(house_info.keys(), key=lambda h: min(p[0] for p in house_info[h]))
    
    result_parts = []
    for h in sorted_houses[:6]:
        activations = house_info[h]
        min_pri = min(p[0] for p in activations)
        sources_str = ",".join(sorted(set(p[1] for p in activations if p[0] == min_pri)))
        result_parts.append(f"{h}({sources_str})")
    
    return " ".join(result_parts)

def are_planets_connected(chart: ChartData, planet1_name: str, planet2_name: str) -> bool:
    if planet1_name == planet2_name:
        return True
    p1 = chart.planets.get(planet1_name)
    p2 = chart.planets.get(planet2_name)
    if not p1 or not p2:
        return False
    
    if p1.exchange_partner == planet2_name:
        return True
    for asp in p1.aspects_received:
        if asp["from"] == planet2_name:
            return True
    for asp in p2.aspects_received:
        if asp["from"] == planet1_name:
            return True
    if p1.sign_index == p2.sign_index:
        dist = angular_distance(p1.longitude, p2.longitude)
        orb = min(PLANET_ORBS[p1.name], PLANET_ORBS[p2.name]) * EFFECTIVE_ORB_MULTIPLIER
        if dist <= orb:
            return True
    return False

def are_same_nature(chart: ChartData, planet1_name: str, planet2_name: str) -> bool:
    p1 = chart.planets.get(planet1_name)
    p2 = chart.planets.get(planet2_name)
    if not p1 or not p2:
        return False
    return p1.final_nature == p2.final_nature

def is_yoga_karaka(chart: ChartData, planet_name: str) -> bool:
    planet = chart.planets.get(planet_name)
    if not planet:
        return False
    lordships = set(planet.lordships)
    return bool(lordships & {4, 7, 10}) and bool(lordships & {5, 9})

def get_shadbala_strength_factor(planet: PlanetData) -> str:
    if not planet.shadbala:
        return "medium"
    pct = planet.shadbala.strength_percent
    if pct >= 120:
        return "strong"
    elif pct >= 80:
        return "medium"
    return "weak"

def apply_shadbala_modifier(base_result: str, md_strength: str, ad_strength: str) -> str:
    amplify_up = {"Good": "Excellent", "Good(FM PD)": "Good", "Mixed": "Good"}
    amplify_down = {"Bad": "Very Bad", "Mixed(FM AD)": "Bad", "Mixed(more FM)": "Bad", "Bad(less)": "Bad"}
    dampen_up = {"Very Bad": "Bad", "Bad": "Mixed", "Bad+Maraka": "Bad", "Maraka(Danger)": "Maraka"}
    dampen_down = {"Excellent": "Good", "Good": "Mixed"}
    
    if md_strength == "strong":
        if base_result in amplify_up:
            return amplify_up[base_result] + "(Strong MD)"
        elif base_result in amplify_down:
            return amplify_down[base_result] + "(Strong MD)"
    elif md_strength == "weak":
        if base_result in dampen_up:
            return dampen_up[base_result] + "(Weak MD)"
        elif base_result in dampen_down:
            return dampen_down[base_result] + "(Weak MD)"
    
    return base_result

def classify_dasha_result_laghu_parashari(chart: ChartData, md_lord: str, ad_lord: str, pd_lord: str) -> str:
    md_planet = chart.planets[md_lord]
    ad_planet = chart.planets[ad_lord]
    pd_planet = chart.planets[pd_lord]
    
    md_fb = md_planet.final_nature == FunctionalNature.FB
    ad_fb = ad_planet.final_nature == FunctionalNature.FB
    pd_fb = pd_planet.final_nature == FunctionalNature.FB
    
    md_maraka = md_planet.is_maraka
    ad_maraka = ad_planet.is_maraka
    
    md_ad_connected = are_planets_connected(chart, md_lord, ad_lord)
    md_ad_same = are_same_nature(chart, md_lord, ad_lord)
    ad_yoga = is_yoga_karaka(chart, ad_lord)
    
    if {md_lord, ad_lord} == {"Saturn", "Venus"}:
        md_ad_connected = True
    
    md_strength = get_shadbala_strength_factor(md_planet)
    ad_strength = get_shadbala_strength_factor(ad_planet)
    
    base_result = None
    
    if md_lord == ad_lord:
        base_result = "Ordinary(FB)" if md_fb else "Ordinary(FM)"
    elif md_maraka or ad_maraka:
        any_fm = not md_fb or not ad_fb or not pd_fb
        if md_maraka and ad_fb and pd_fb:
            base_result = "Maraka(Protected)"
        elif md_maraka and not ad_fb:
            base_result = "Maraka(Danger)"
        elif ad_maraka and not md_fb:
            base_result = "Bad+Maraka"
        elif md_maraka or ad_maraka:
            base_result = "Bad+Maraka" if any_fm else "Maraka"
    elif md_fb:
        if ad_fb:
            if md_ad_connected or md_ad_same:
                base_result = "Excellent" if pd_fb else "Good(FM PD)"
            else:
                base_result = "Good" if pd_fb else "Mixed"
        else:
            if md_ad_connected:
                base_result = "Mixed"
            else:
                base_result = "Mixed(FM AD)" if pd_fb else "Bad"
    else:
        if ad_fb:
            if md_ad_connected:
                base_result = "Mixed" if ad_yoga else "Mixed(more FM)"
            else:
                base_result = "Bad(less)" if ad_yoga else "Very Bad"
        else:
            if md_ad_connected or md_ad_same:
                base_result = "Bad" if pd_fb else "Very Bad"
            else:
                base_result = "Very Bad"
    
    return apply_shadbala_modifier(base_result, md_strength, ad_strength) if base_result else "Unknown"

# =============================================================================
# DASHA EXPLANATION
# =============================================================================

def get_dasha_classification_explanation(chart: ChartData, md_lord: str, ad_lord: str, pd_lord: str) -> Dict:
    """Get detailed explanation for dasha classification."""
    md_planet = chart.planets[md_lord]
    ad_planet = chart.planets[ad_lord]
    pd_planet = chart.planets[pd_lord]
    
    md_fb = md_planet.final_nature == FunctionalNature.FB
    ad_fb = ad_planet.final_nature == FunctionalNature.FB
    pd_fb = pd_planet.final_nature == FunctionalNature.FB
    
    md_maraka = md_planet.is_maraka
    ad_maraka = ad_planet.is_maraka
    
    md_ad_connected = are_planets_connected(chart, md_lord, ad_lord)
    md_ad_same = are_same_nature(chart, md_lord, ad_lord)
    ad_pd_connected = are_planets_connected(chart, ad_lord, pd_lord)
    ad_yoga = is_yoga_karaka(chart, ad_lord)
    
    if {md_lord, ad_lord} == {"Saturn", "Venus"}:
        md_ad_connected = True
    
    result = classify_dasha_result_laghu_parashari(chart, md_lord, ad_lord, pd_lord)
    
    # Build factors list
    factors = []
    
    def get_lordship_str(planet):
        return ", ".join(f"{h}L" for h in planet.lordships) if planet.lordships else "shadow"
    
    def get_lordship_meaning(lordships):
        meanings = []
        for h in lordships:
            if h in [1, 5, 9]:
                meanings.append(f"{h}L=trikona✓")
            elif h in [3, 6, 11]:
                meanings.append(f"{h}L=trishadaya✗")
            elif h in [4, 7, 10]:
                meanings.append(f"{h}L=kendra")
            elif h == 8:
                meanings.append("8L=dusthana✗")
            elif h == 2:
                meanings.append("2L=maraka")
            elif h == 12:
                meanings.append("12L=loss")
        return ", ".join(meanings) if meanings else ""
    
    md_meaning = get_lordship_meaning(md_planet.lordships)
    ad_meaning = get_lordship_meaning(ad_planet.lordships)
    pd_meaning = get_lordship_meaning(pd_planet.lordships)
    
    factors.append(f"**{md_lord}** ({get_lordship_str(md_planet)}): {md_meaning} → {'FB' if md_fb else 'FM'}")
    factors.append(f"**{ad_lord}** ({get_lordship_str(ad_planet)}): {ad_meaning} → {'FB' if ad_fb else 'FM'}")
    factors.append(f"**{pd_lord}** ({get_lordship_str(pd_planet)}): {pd_meaning} → {'FB' if pd_fb else 'FM'}")
    
    # Connection details
    def get_connection_details(p1_name, p2_name):
        p1 = chart.planets[p1_name]
        p2 = chart.planets[p2_name]
        details = []
        if p1.exchange_partner == p2_name:
            details.append("exchange")
        for asp in p1.aspects_received:
            if asp["from"] == p2_name:
                details.append(f"{p2_name} aspects {p1_name}")
        for asp in p2.aspects_received:
            if asp["from"] == p1_name:
                details.append(f"{p1_name} aspects {p2_name}")
        if p1.sign_index == p2.sign_index:
            dist = angular_distance(p1.longitude, p2.longitude)
            orb = min(PLANET_ORBS[p1_name], PLANET_ORBS[p2_name]) * EFFECTIVE_ORB_MULTIPLIER
            if dist <= orb:
                details.append(f"conjunction ({dist:.0f}°)")
        if {p1_name, p2_name} == {"Saturn", "Venus"}:
            details.append("natural friends")
        return details
    
    if md_lord != ad_lord:
        md_ad_details = get_connection_details(md_lord, ad_lord)
        if md_ad_details:
            factors.append(f"✓ MD↔AD connected: {', '.join(md_ad_details)}")
        else:
            factors.append("❌ MD↔AD NOT connected")
    
    if ad_lord != pd_lord:
        ad_pd_details = get_connection_details(ad_lord, pd_lord)
        if ad_pd_details:
            factors.append(f"✓ AD↔PD connected: {', '.join(ad_pd_details)}")
        else:
            factors.append("○ AD↔PD not connected")
    
    if ad_yoga:
        factors.append(f"✓ {ad_lord} is Yoga Karaka")
    
    # Build story
    story = ""
    rule = ""
    
    if md_lord == ad_lord:
        story = f"When {md_lord} runs its own sub-period, it gives ordinary results only - not amplified."
        rule = "Verse 29: Own AD in own MD"
    elif md_maraka and ad_fb and pd_fb:
        story = f"{md_lord} is Maraka but {ad_lord} (FB) and {pd_lord} (FB) provide protection. Health issues may arise but are mitigated."
        rule = "Verse 39: Maraka protection"
    elif md_maraka and not ad_fb:
        story = f"⚠️ DANGER: {md_lord} is Maraka and {ad_lord} is FM - Maraka potential is activated, not suppressed."
        rule = "Verse 39: Maraka activated"
    elif md_fb and ad_fb:
        if md_ad_connected or md_ad_same:
            story = f"Excellent! Both {md_lord} and {ad_lord} are FB and connected - they amplify each other's positive effects."
            rule = "Verses 30-32: Connected benefics"
        else:
            story = f"Both {md_lord} and {ad_lord} are FB but not connected - positive results but not amplified."
            rule = "Verse 33: Unconnected benefics"
    elif md_fb and not ad_fb:
        if md_ad_connected:
            story = f"{md_lord} (FB) is connected to {ad_lord} (FM) - the connection allows some mixing of results."
            rule = "Verse 34: Connected FB+FM"
        else:
            story = f"{md_lord} (FB) cannot control {ad_lord} (FM) since they're unconnected - FM results dominate."
            rule = "Verses 35-36: Unconnected FM dominates"
    elif not md_fb and ad_fb:
        if md_ad_connected:
            story = f"{ad_lord} (FB) is connected to {md_lord} (FM) - can provide some relief during difficult period."
            rule = "Verse 37: Connected FB helps FM"
        else:
            if ad_yoga:
                story = f"{ad_lord} is Yoga Karaka - provides some protection even without connection to {md_lord} (FM)."
                rule = "Verse 38: Yoga Karaka exception"
            else:
                story = f"🔴 Very Bad: {ad_lord} (FB) has NO connection to {md_lord} (FM) - cannot help at all. The benefic's energy is wasted."
                rule = "Verse 37: Unconnected FB useless"
    else:
        story = f"Both {md_lord} and {ad_lord} are FM - compounded difficult period with no benefic relief."
        rule = "FM + FM combination"
    
    # Shadbala impact
    shadbala_note = ""
    if md_planet.shadbala:
        if md_planet.shadbala.strength_class == "Strong":
            shadbala_note = f"💪 {md_lord}'s strong Shadbala ({md_planet.shadbala.total_rupas:.1f}R) amplifies this result."
        elif md_planet.shadbala.strength_class == "Weak":
            shadbala_note = f"⚡ {md_lord}'s weak Shadbala ({md_planet.shadbala.total_rupas:.1f}R) dampens extreme effects."
    
    return {
        "result": result,
        "factors": factors,
        "story": story,
        "rule": rule,
        "shadbala_note": shadbala_note,
        "md_fb": md_fb,
        "ad_fb": ad_fb,
        "pd_fb": pd_fb,
        "md_ad_connected": md_ad_connected,
        "ad_pd_connected": ad_pd_connected,
        "md_maraka": md_maraka,
        "ad_maraka": ad_maraka,
        "ad_yoga_karaka": ad_yoga,
    }

# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_chart(date: str, time: str, latitude: float, longitude: float,
                  timezone_offset: float, dasha_start_year: int = None,
                  dasha_end_year: int = None) -> AnalysisResult:
    """
    Main analysis function.
    
    Args:
        date: Birth date in YYYY-MM-DD format
        time: Birth time in HH:MM format (24-hour)
        latitude: Birth latitude
        longitude: Birth longitude (positive East)
        timezone_offset: Timezone offset from UTC (e.g., 5.5 for IST)
        dasha_start_year: Start year for dasha listing (default: current year)
        dasha_end_year: End year for dasha listing (default: start + 10)
    
    Returns:
        AnalysisResult with chart data and dasha periods
    """
    chart = calculate_chart(date, time, latitude, longitude, timezone_offset)
    calculate_lordships(chart)
    classify_base_nature(chart)
    detect_exchanges(chart)
    calculate_aspects(chart)
    calculate_conjunctions(chart)
    calculate_shadbala(chart)
    resolve_impressionable_planets(chart)
    classify_marakas(chart)
    
    if dasha_start_year is None:
        dasha_start_year = datetime.now().year
    if dasha_end_year is None:
        dasha_end_year = dasha_start_year + 10
    
    dasha_periods = calculate_vimshottari_dashas(chart, dasha_start_year, dasha_end_year)
    
    return AnalysisResult(chart=chart, dasha_periods=dasha_periods)
