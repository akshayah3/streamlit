import streamlit as st
import math
from datetime import datetime, timezone, timedelta
import pandas as pd
import swisseph as swe

st.set_page_config(
    page_title="Vedic Astrology Chart Analysis",
    page_icon="🪐",
    layout="wide"
)

st.title("🪐 Vedic Astrology Chart Analysis")
st.markdown("Generate detailed Vedic astrology charts with planetary relationships, aspects, and more!")

# Sidebar for inputs
st.sidebar.header("Birth Details")

# Date and time inputs
birth_date = st.sidebar.date_input(
    "Birth Date",
    value=datetime(1975, 8, 11),
    min_value=datetime(1800, 1, 1),
    max_value=datetime(2100, 12, 31)
)

birth_time = st.sidebar.time_input(
    "Birth Time",
    value=datetime.strptime("19:10", "%H:%M").time(),
    step=60  # 60 seconds = 1 minute intervals
)

# Location inputs
st.sidebar.subheader("Birth Location")
latitude = st.sidebar.number_input(
    "Latitude (degrees)", 
    value=16.705,
    format="%.3f",
    help="North is positive, South is negative"
)

longitude = st.sidebar.number_input(
    "Longitude (degrees)", 
    value=74.243, 
    format="%.3f",
    help="East is positive, West is negative"
)

# Timezone input
timezone_offset = st.sidebar.number_input(
    "Timezone Offset (hours from UTC)",
    value=5.5,
    format="%.1f",
    help="e.g., 5.5 for IST, -5.0 for EST"
)

location_name = st.sidebar.text_input(
    "Location Name (optional)",
    value="Kolhapur"
)

# Generate button
# Initialize session state for chart data
if 'chart_generated' not in st.session_state:
    st.session_state.chart_generated = False

if st.sidebar.button("🔮 Generate Chart", type="primary"):
    
    # Combine date and time
    birth_local = datetime.combine(
        birth_date, 
        birth_time, 
        tzinfo=timezone(timedelta(hours=timezone_offset))
    )
    
    # Helper functions (from your original code)
    def norm_deg(x): 
        return x % 360.0
    
    def sign_index(lon): 
        return int(math.floor(norm_deg(lon) / 30.0))
    
    def sign_name(idx):
        return ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
                "Sagittarius","Capricorn","Aquarius","Pisces"][idx % 12]

    def nakshatra_index(lon):
        return int(math.floor(norm_deg(lon) / (360.0/27.0)))
    
    def nakshatra_name(idx):
        names = ["Ashvini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha",
                "Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
                "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
                "Uttara Bhadrapada","Revati"]
        return names[idx % 27]

    def navamsa_sign_index(lon_sid):
        s = sign_index(lon_sid)
        within = norm_deg(lon_sid) - s*30.0
        p = int(math.floor(within / (30.0/9.0)))
        if s in (0,3,6,9):
            start_offset = 0
        elif s in (1,4,7,10):
            start_offset = 8
        else:
            start_offset = 4
        return (s + start_offset + p) % 12
    
    def navamsa_sign_name(lon_sid): 
        return sign_name(navamsa_sign_index(lon_sid))

    # Ayanamsha calculation
    reference_date = datetime(1900, 1, 1)
    ayanamsa_1900_deg = 22 + 33/60 + 38.81/3600
    precession_rate_arcsec_per_year = 50.278658
    precession_rate_deg_per_year = precession_rate_arcsec_per_year / 3600
    
    birth_date_only = datetime(birth_local.year, birth_local.month, birth_local.day)
    years_elapsed = (birth_date_only - reference_date).days / 365.25
    ayanamsa_deg = ayanamsa_1900_deg + (years_elapsed * precession_rate_deg_per_year)
    
    # Julian day calculation
    utc = birth_local.astimezone(timezone.utc)
    jd_ut = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60 + utc.second/3600.0)

    # Planets
    PLANETS = [
        ("Sun", swe.SUN),
        ("Moon", swe.MOON),
        ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS),
        ("Saturn", swe.SATURN),
        ("Rahu", swe.MEAN_NODE),
        ("Ketu", None),
    ]

    # Calculate planetary positions
    FLAGS = swe.FLG_SWIEPH
    planet_lon_sid = {}
    for name, pid in PLANETS:
        if name == "Ketu":
            continue
        coords, status = swe.calc_ut(jd_ut, pid, FLAGS)
        lon_trop, latp, dist, lon_speed, _, _ = coords
        planet_lon_sid[name] = norm_deg(lon_trop - ayanamsa_deg)
    
    planet_lon_sid["Ketu"] = norm_deg(planet_lon_sid["Rahu"] + 180.0)

    # House calculations
    house_system = b'O'  # Sripati
    cusps_trop, ascmc = swe.houses(jd_ut, latitude, longitude, house_system)
    cusps_sid = {i+1: norm_deg(cusps_trop[i] - ayanamsa_deg) for i in range(12)}

    # Calculate Sripati house boundaries
    def calculate_sripati_boundaries(cusps_dict):
        boundaries = {}
        for house in range(1, 13):
            prev_house = 12 if house == 1 else house - 1
            next_house = 1 if house == 12 else house + 1
            
            prev_cusp = cusps_dict[prev_house]
            curr_cusp = cusps_dict[house]
            
            if prev_cusp > curr_cusp:
                start = norm_deg((prev_cusp + curr_cusp + 360) / 2)
            else:
                start = norm_deg((prev_cusp + curr_cusp) / 2)
            
            next_cusp = cusps_dict[next_house]
            
            if curr_cusp > next_cusp:
                end = norm_deg((curr_cusp + next_cusp + 360) / 2)
            else:
                end = norm_deg((curr_cusp + next_cusp) / 2)
                
            boundaries[house] = (start, end)
        return boundaries

    house_boundaries = calculate_sripati_boundaries(cusps_sid)

    # Planetary house placement
    def get_sripati_house(longitude, boundaries):
        for house in range(1, 13):
            start, end = boundaries[house]
            if start > end:
                if longitude >= start or longitude < end:
                    return house
            else:
                if start <= longitude < end:
                    return house
        return None

    # House sign assignment - sequential from ascendant sign
    ascendant_sign_idx = sign_index(cusps_sid[1])
    house_sign_idx = {i: (ascendant_sign_idx + i - 1) % 12 for i in range(1,13)}

    # Per-planet attributes
    p_sign_idx = {p: sign_index(lon) for p, lon in planet_lon_sid.items()}
    p_sign_name = {p: sign_name(idx) for p, idx in p_sign_idx.items()}
    p_house = {p: get_sripati_house(lon, house_boundaries) for p, lon in planet_lon_sid.items()}
    p_nak_idx = {p: nakshatra_index(lon) for p, lon in planet_lon_sid.items()}
    p_nak_name = {p: nakshatra_name(idx) for p, idx in p_nak_idx.items()}
    p_nav_idx = {p: navamsa_sign_index(lon) for p, lon in planet_lon_sid.items()}
    p_nav_name = {p: sign_name(idx) for p, idx in p_nav_idx.items()}

    # Planetary orbs and aspects
    PLANET_ORBS = {
        "Sun": 15, "Moon": 12, "Venus": 7, "Mercury": 7,
        "Saturn": 9, "Mars": 9, "Jupiter": 9, "Rahu": 15, "Ketu": 15
    }

    PLANET_ASPECTS = {
        "Sun": [7], "Moon": [7], "Mercury": [7], "Venus": [7],
        "Mars": [4, 7, 8], "Jupiter": [5, 7, 9], "Saturn": [3, 7, 10],
        "Rahu": [5, 7, 9], "Ketu": [5, 7, 9]
    }

    # Aspect calculations (simplified version)
    def get_planetary_aspects(planet_name, planet_lon, planet_house):
        if planet_house is None:
            return {}
        
        aspects = {}
        orb = PLANET_ORBS[planet_name] 
        aspect_distances = PLANET_ASPECTS.get(planet_name, [7])
        
        for aspect_distance in aspect_distances:
            if aspect_distance == 7:
                aspect_point = norm_deg(planet_lon + 180)
            elif aspect_distance == 4:
                aspect_point = norm_deg(planet_lon + 90)
            elif aspect_distance == 8:
                aspect_point = norm_deg(planet_lon + 210)
            elif aspect_distance == 3:
                aspect_point = norm_deg(planet_lon + 60)
            elif aspect_distance == 10:
                aspect_point = norm_deg(planet_lon + 270)
            elif aspect_distance == 5:
                aspect_point = norm_deg(planet_lon + 120)
            elif aspect_distance == 9:
                aspect_point = norm_deg(planet_lon + 240)
            else:
                continue
            
            aspect_start = norm_deg(aspect_point - orb)
            aspect_end = norm_deg(aspect_point + orb)
            
            for house in range(1, 13):
                cusp_lon = cusps_sid[house]
                
                in_orb = False
                if aspect_start <= aspect_end:
                    in_orb = aspect_start <= cusp_lon <= aspect_end
                else:
                    in_orb = cusp_lon >= aspect_start or cusp_lon <= aspect_end
                
                if in_orb:
                    strength = 100.0
                    aspects[house] = max(aspects.get(house, 0), strength)
                else:
                    dist_to_start = abs(cusp_lon - aspect_start)
                    if dist_to_start > 180:
                        dist_to_start = 360 - dist_to_start
                    
                    dist_to_end = abs(cusp_lon - aspect_end)  
                    if dist_to_end > 180:
                        dist_to_end = 360 - dist_to_end
                    
                    min_boundary_dist = min(dist_to_start, dist_to_end)
                    
                    if min_boundary_dist <= orb * 2:
                        strength = math.exp(-min_boundary_dist / orb) * 100
                        aspects[house] = max(aspects.get(house, 0), strength)
        
        return aspects

    p_aspects = {p: get_planetary_aspects(p, lon, p_house[p]) for p, lon in planet_lon_sid.items()}

    # Calculate controlling aspects (one-sided aspects between planets)
    def get_controlling_aspects(planet_name, planet_lon):
        """Find planets that this planet controls via one-sided aspects"""
        controlled_planets = []
        orb = PLANET_ORBS[planet_name]
        aspect_distances = PLANET_ASPECTS.get(planet_name, [7])
        
        for other_planet, other_lon in planet_lon_sid.items():
            if other_planet == planet_name:
                continue
                
            # Check if this planet aspects the other planet
            this_aspects_other = False
            for aspect_distance in aspect_distances:
                # Calculate aspect point
                if aspect_distance == 7:
                    aspect_point = norm_deg(planet_lon + 180)
                elif aspect_distance == 4:
                    aspect_point = norm_deg(planet_lon + 90)
                elif aspect_distance == 8:
                    aspect_point = norm_deg(planet_lon + 210)
                elif aspect_distance == 3:
                    aspect_point = norm_deg(planet_lon + 60)
                elif aspect_distance == 10:
                    aspect_point = norm_deg(planet_lon + 270)
                elif aspect_distance == 5:
                    aspect_point = norm_deg(planet_lon + 120)
                elif aspect_distance == 9:
                    aspect_point = norm_deg(planet_lon + 240)
                else:
                    continue
                
                # Check if other planet falls within this aspect's orb
                diff = abs(other_lon - aspect_point)
                if diff > 180:
                    diff = 360 - diff
                    
                if diff <= orb + 2:  # Add 2-degree grace period
                    this_aspects_other = True
                    break
            
            if this_aspects_other:
                # Check if the reverse is also true (other planet aspects this planet)
                other_orb = PLANET_ORBS[other_planet]
                other_aspect_distances = PLANET_ASPECTS.get(other_planet, [7])
                other_aspects_this = False
                
                for other_aspect_distance in other_aspect_distances:
                    # Calculate other planet's aspect point
                    if other_aspect_distance == 7:
                        other_aspect_point = norm_deg(other_lon + 180)
                    elif other_aspect_distance == 4:
                        other_aspect_point = norm_deg(other_lon + 90)
                    elif other_aspect_distance == 8:
                        other_aspect_point = norm_deg(other_lon + 210)
                    elif other_aspect_distance == 3:
                        other_aspect_point = norm_deg(other_lon + 60)
                    elif other_aspect_distance == 10:
                        other_aspect_point = norm_deg(other_lon + 270)
                    elif other_aspect_distance == 5:
                        other_aspect_point = norm_deg(other_lon + 120)
                    elif other_aspect_distance == 9:
                        other_aspect_point = norm_deg(other_lon + 240)
                    else:
                        continue
                    
                    # Check if this planet falls within other planet's aspect orb
                    diff = abs(planet_lon - other_aspect_point)
                    if diff > 180:
                        diff = 360 - diff
                        
                    if diff <= other_orb + 2:  # Add 2-degree grace period
                        other_aspects_this = True
                        break
                
                # If this planet aspects the other but not vice versa = controlling aspect
                if not other_aspects_this:
                    controlled_planets.append(other_planet)
        
        return controlled_planets
    
    # Calculate controlling aspects for all planets
    p_controlling = {p: get_controlling_aspects(p, lon) for p, lon in planet_lon_sid.items()}

    # Sign and nakshatra lords
    SIGN_LORD = {
        "Sun": [4], "Moon": [3], "Mars": [0,7], "Mercury": [2,5],
        "Jupiter": [8,11], "Venus": [1,6], "Saturn": [9,10],
        "Rahu": [5], "Ketu": [11],
    }

    NAKSHATRA_LORD = {
        "Ketu": [0, 9, 18], "Venus": [1, 10, 19], "Sun": [2, 11, 20],
        "Moon": [3, 12, 21], "Mars": [4, 13, 22], "Rahu": [5, 14, 23],
        "Jupiter": [6, 15, 24], "Saturn": [7, 16, 25], "Mercury": [8, 17, 26],
    }

    planet_names = [p for p, _ in PLANETS]

    # Just store data, display is handled outside this block
    
    analysis_data = []
    for planet in planet_names:
        # Houses ruling
        ruled_signs = SIGN_LORD[planet]
        lord_houses = [house for house in range(1,13) if house_sign_idx[house] in ruled_signs]
        
        # Houses aspecting
        aspects = p_aspects[planet]
        if aspects:
            aspect_str = ", ".join([f"H{h}({strength:.0f}%)" for h, strength in sorted(aspects.items())])
        else:
            aspect_str = "None"
        
        # Planets in its signs
        planets_in_signs = [q for q in planet_names if q != planet and p_sign_idx[q] in ruled_signs]
        
        # Planets in its nakshatras
        ruled_nakshatras = NAKSHATRA_LORD.get(planet, [])
        planets_in_nakshatras = [q for q in planet_names if q != planet and p_nak_idx[q] in ruled_nakshatras]
        
        # Planets in its navamsa
        planets_in_navamsa = [q for q in planet_names if q != planet and p_nav_idx[q] in ruled_signs]
        
        # Controlling
        controlling = p_controlling[planet]
        controlling_str = ", ".join(controlling) if controlling else "None"
        
        analysis_data.append({
            "Planet": planet,
            "House Placed In": p_house[planet],
            "Houses Ruled": ", ".join(str(h) for h in lord_houses) if lord_houses else "None",
            "Houses Aspecting": aspect_str,
            "Planets in Its Sign": ", ".join(planets_in_signs) if planets_in_signs else "None",
            "Planets in Its Nakshatra": ", ".join(planets_in_nakshatras) if planets_in_nakshatras else "None",
            "Planets in Its Navamsa": ", ".join(planets_in_navamsa) if planets_in_navamsa else "None",
            "Planets It's Controlling": controlling_str
        })
    
    # Store calculated data in session state for dasha analysis
    st.session_state.chart_data = {
        'planet_names': planet_names,
        'p_house': p_house,
        'p_aspects': p_aspects,
        'p_controlling': p_controlling,
        'p_sign_idx': p_sign_idx,
        'p_nak_idx': p_nak_idx,
        'p_nav_idx': p_nav_idx,
        'house_sign_idx': house_sign_idx,
        'SIGN_LORD': SIGN_LORD,
        'NAKSHATRA_LORD': NAKSHATRA_LORD,
        # Store birth details for display
        'birth_local': birth_local,
        'ayanamsa_deg': ayanamsa_deg,
        'cusps_sid': cusps_sid,
        'ascendant_sign_idx': ascendant_sign_idx
    }
    st.session_state.chart_generated = True

# Display chart results if available
if st.session_state.chart_generated and 'chart_data' in st.session_state:
    st.success("Chart generated successfully!")
    
    # Get stored data
    chart_data = st.session_state.chart_data
    
    # Define helper functions first
    def sign_name(idx):
        return ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
                "Sagittarius","Capricorn","Aquarius","Pisces"][idx % 12]
    
    def nakshatra_name(idx):
        names = ["Ashvini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha",
                "Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
                "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
                "Uttara Bhadrapada","Revati"]
        return names[idx % 27]
    
    # Chart info (from stored data)
    birth_local = chart_data['birth_local']
    ayanamsa_deg = chart_data['ayanamsa_deg']
    cusps_sid = chart_data['cusps_sid']
    ascendant_sign_idx = chart_data['ascendant_sign_idx']
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Birth Details**\n\n"
                f"📅 Date: {birth_local.strftime('%B %d, %Y')}\n\n"
                f"🕐 Time: {birth_local.strftime('%I:%M %p %Z')}\n\n"
                f"📍 Location: {location_name if location_name else 'Custom'} ({latitude:.3f}°, {longitude:.3f}°)")
    
    with col2:
        st.info(f"**Calculation Details**\n\n"
                f"🔢 Ayanamsa: {ayanamsa_deg:.2f}°\n\n"
                f"🏠 House System: Sripati (Porphyry)\n\n"
                f"🌟 Ascendant: {sign_name(ascendant_sign_idx)} ({cusps_sid[1]:.1f}°)")

    # Recreate planetary analysis table from stored data
    st.subheader("🪐 Planetary Analysis")
    
    planet_names = chart_data['planet_names']
    p_house = chart_data['p_house']
    p_aspects = chart_data['p_aspects']
    p_controlling = chart_data['p_controlling']
    p_sign_idx = chart_data['p_sign_idx']
    p_nak_idx = chart_data['p_nak_idx']
    p_nav_idx = chart_data['p_nav_idx']
    house_sign_idx = chart_data['house_sign_idx']
    SIGN_LORD = chart_data['SIGN_LORD']
    NAKSHATRA_LORD = chart_data['NAKSHATRA_LORD']
    
    # Recreate the analysis data
    analysis_data = []
    for p in planet_names:
        ruled_signs = SIGN_LORD[p]
        lord_houses = [house for house in range(1,13) if house_sign_idx[house] in ruled_signs]
        planets_in_signs = [q for q in planet_names if q != p and p_sign_idx[q] in ruled_signs]
        
        ruled_nakshatras = NAKSHATRA_LORD.get(p, [])
        planets_in_nakshatras = [q for q in planet_names if q != p and p_nak_idx[q] in ruled_nakshatras]
        
        planets_in_navamsa = [q for q in planet_names if q != p and p_nav_idx[q] in ruled_signs]
        
        # Add aspects and controlling aspects
        aspects = p_aspects[p]
        if aspects:
            aspect_str = ", ".join([f"H{h}({strength:.0f}%)" for h, strength in sorted(aspects.items())])
        else:
            aspect_str = "None"
        
        controlling = p_controlling[p]
        controlling_str = ", ".join(controlling) if controlling else "None"
        
        analysis_data.append({
            "Planet": p,
            "House Placed In": p_house[p],
            "Houses Ruled": ", ".join(str(h) for h in lord_houses) if lord_houses else "None",
            "Houses Aspecting": aspect_str,
            "Planets in Its Sign": ", ".join(planets_in_signs) if planets_in_signs else "None",
            "Planets in Its Nakshatra": ", ".join(planets_in_nakshatras) if planets_in_nakshatras else "None",
            "Planets in Its Navamsa": ", ".join(planets_in_navamsa) if planets_in_navamsa else "None",
            "Planets It's Controlling": controlling_str
        })
    
    df_analysis = pd.DataFrame(analysis_data)
    st.dataframe(df_analysis, use_container_width=True)

else:
    st.info("👈 Enter your birth details in the sidebar and click 'Generate Chart' to begin!")
    
    # Example/demo section
    with st.expander("ℹ️ How to use this calculator"):
        st.markdown("""
        **Step 1:** Enter your birth details in the sidebar:
        - Birth date and time
        - Birth location (latitude/longitude)
        - Timezone offset from UTC
        
        **Step 2:** Click "Generate Chart" to calculate your Vedic astrology chart
        
        **Features included:**
        - 🪐 Planetary analysis with comprehensive relationships
        - 🕐 Dasha period analysis for timing predictions
        - 🎯 Planetary aspects with strength calculations
        - 🔗 House activation priority system
        
        **Note:** This calculator uses the traditional Lahiri ayanamsa and Swiss Ephemeris for accurate calculations.
        """)

# Dasha Period Analysis (Available after chart generation)
if st.session_state.chart_generated and 'chart_data' in st.session_state:
    st.subheader("🕐 Dasha Period Analysis")
    
    chart_data = st.session_state.chart_data
    planet_names = chart_data['planet_names']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mahadasha = st.selectbox(
            "Mahadasha Planet",
            planet_names,
            index=0,
            key="maha_select"
        )
    
    with col2:
        antardasha = st.selectbox(
            "Antardasha Planet", 
            planet_names,
            index=1 if len(planet_names) > 1 else 0,
            key="antar_select"
        )
    
    with col3:
        pratyantardasha = st.selectbox(
            "Pratyantardasha Planet",
            planet_names, 
            index=2 if len(planet_names) > 2 else 0,
            key="pratyantar_select"
        )
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_aspects = st.checkbox(
            "Show only aspect-based activations", 
            value=False,
            key="filter_aspects",
            help="Filter out placement and lordship activations, keeping only houses activated by aspects"
        )
    
    with col2:
        show_priority = st.checkbox(
            "Show priority order", 
            value=True,
            key="show_priority",
            help="Display activations in priority order: Aspects > Placement > Lordship"
        )

    if st.button("🔍 Analyze Dasha Period", type="primary"):
        
        def get_planet_active_houses(planet, data, filter_aspects_only=False, show_priority_order=True):
            """Get all houses activated by a planet in priority order"""
            active_houses = []
            
            # Priority 1: Houses it aspects (HIGHEST PRIORITY)
            aspects = data['p_aspects'][planet]
            if aspects:
                aspect_houses = sorted(aspects.keys())
                active_houses.extend([(h, f"Aspects H{h}", 1) for h in aspect_houses])
            
            # If filtering for aspects only, skip non-aspect activations
            if not filter_aspects_only:
                # Priority 2: House it is placed in
                if data['p_house'][planet]:
                    active_houses.append((data['p_house'][planet], f"Placed in H{data['p_house'][planet]}", 2))
                
                # Priority 3: Houses it rules (lordship)
                ruled_signs = data['SIGN_LORD'][planet]
                lord_houses = [house for house in range(1,13) if data['house_sign_idx'][house] in ruled_signs]
                active_houses.extend([(h, f"Rules H{h}", 3) for h in lord_houses])
            
            # Priority 4-6: Houses influenced by planets in its signs
            ruled_signs = data['SIGN_LORD'][planet]
            planets_in_signs = [q for q in data['planet_names'] if q != planet and data['p_sign_idx'][q] in ruled_signs]
            for other_planet in planets_in_signs:
                # Other planet's aspects (Priority 4 - always include as it's aspect-based)
                other_aspects = data['p_aspects'][other_planet]
                if other_aspects:
                    other_aspect_houses = sorted(other_aspects.keys())
                    active_houses.extend([(h, f"Via {other_planet} in {planet}'s sign (aspects H{h})", 4) for h in other_aspect_houses])
                
                if not filter_aspects_only:
                    # Other planet's placement (Priority 5)
                    if data['p_house'][other_planet]:
                        active_houses.append((data['p_house'][other_planet], f"Via {other_planet} in {planet}'s sign (placed in H{data['p_house'][other_planet]})", 5))
                    
                    # Other planet's lordship (Priority 6)
                    other_ruled_signs = data['SIGN_LORD'][other_planet]
                    other_lord_houses = [house for house in range(1,13) if data['house_sign_idx'][house] in other_ruled_signs]
                    active_houses.extend([(h, f"Via {other_planet} in {planet}'s sign (rules H{h})", 6) for h in other_lord_houses])
            
            # Priority 7-9: Houses influenced by planets in its nakshatras
            ruled_nakshatras = data['NAKSHATRA_LORD'].get(planet, [])
            planets_in_nakshatras = [q for q in data['planet_names'] if q != planet and data['p_nak_idx'][q] in ruled_nakshatras]
            for other_planet in planets_in_nakshatras:
                # Other planet's aspects (Priority 7 - always include as it's aspect-based)
                other_aspects = data['p_aspects'][other_planet]
                if other_aspects:
                    other_aspect_houses = sorted(other_aspects.keys())
                    active_houses.extend([(h, f"Via {other_planet} in {planet}'s nakshatra (aspects H{h})", 7) for h in other_aspect_houses])
                
                if not filter_aspects_only:
                    # Other planet's placement (Priority 8)
                    if data['p_house'][other_planet]:
                        active_houses.append((data['p_house'][other_planet], f"Via {other_planet} in {planet}'s nakshatra (placed in H{data['p_house'][other_planet]})", 8))
                    
                    # Other planet's lordship (Priority 9)
                    other_ruled_signs = data['SIGN_LORD'][other_planet]
                    other_lord_houses = [house for house in range(1,13) if data['house_sign_idx'][house] in other_ruled_signs]
                    active_houses.extend([(h, f"Via {other_planet} in {planet}'s nakshatra (rules H{h})", 9) for h in other_lord_houses])
            
            # Priority 10-12: Houses influenced by planets in its navamsa  
            ruled_signs = data['SIGN_LORD'][planet]  # Re-declare for navamsa section
            planets_in_navamsa = [q for q in data['planet_names'] if q != planet and data['p_nav_idx'][q] in ruled_signs]
            for other_planet in planets_in_navamsa:
                # Other planet's aspects (Priority 10 - always include as it's aspect-based)
                other_aspects = data['p_aspects'][other_planet]
                if other_aspects:
                    other_aspect_houses = sorted(other_aspects.keys())
                    active_houses.extend([(h, f"Via {other_planet} in {planet}'s navamsa (aspects H{h})", 10) for h in other_aspect_houses])
                
                if not filter_aspects_only:
                    # Other planet's placement (Priority 11)
                    if data['p_house'][other_planet]:
                        active_houses.append((data['p_house'][other_planet], f"Via {other_planet} in {planet}'s navamsa (placed in H{data['p_house'][other_planet]})", 11))
                    
                    # Other planet's lordship (Priority 12)
                    other_ruled_signs = data['SIGN_LORD'][other_planet]
                    other_lord_houses = [house for house in range(1,13) if data['house_sign_idx'][house] in other_ruled_signs]
                    active_houses.extend([(h, f"Via {other_planet} in {planet}'s navamsa (rules H{h})", 12) for h in other_lord_houses])
            
            # Sort by priority (lower number = higher priority) then by house number
            if show_priority_order:
                active_houses.sort(key=lambda x: (x[2], x[0]))
            else:
                # Just sort by house number if priority order is disabled
                active_houses.sort(key=lambda x: x[0])
                
            return active_houses
        
        # Get active houses for each dasha level
        maha_houses = get_planet_active_houses(mahadasha, chart_data, filter_aspects, show_priority)
        antar_houses = get_planet_active_houses(antardasha, chart_data, filter_aspects, show_priority)
        pratyantar_houses = get_planet_active_houses(pratyantardasha, chart_data, filter_aspects, show_priority)
        
        # Find common houses (intersection)
        maha_house_nums = set([h[0] for h in maha_houses])
        antar_house_nums = set([h[0] for h in antar_houses])
        pratyantar_house_nums = set([h[0] for h in pratyantar_houses])
        
        common_houses = maha_house_nums & antar_house_nums & pratyantar_house_nums
        
        # Display results
        st.success(f"Analysis for {mahadasha} MD → {antardasha} AD → {pratyantardasha} PD")
        
        if common_houses:
            st.write(f"**🎯 Common Active Houses: {', '.join([f'H{h}' for h in sorted(common_houses)])}**")
            
            # Show detailed breakdown for common houses
            st.subheader("📋 Detailed House Activation")
            
            for house in sorted(common_houses):
                st.write(f"**House {house}:**")
                
                # Show why each planet activates this house (extract reason from tuple)
                maha_reasons = [reason[1] for reason in maha_houses if reason[0] == house]
                antar_reasons = [reason[1] for reason in antar_houses if reason[0] == house]
                pratyantar_reasons = [reason[1] for reason in pratyantar_houses if reason[0] == house]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**{mahadasha} (MD):**")
                    for reason in maha_reasons[:3]:  # Limit to top 3 reasons
                        st.write(f"• {reason}")
                
                with col2:
                    st.write(f"**{antardasha} (AD):**")
                    for reason in antar_reasons[:3]:  # Limit to top 3 reasons
                        st.write(f"• {reason}")
                
                with col3:
                    st.write(f"**{pratyantardasha} (PD):**") 
                    for reason in pratyantar_reasons[:3]:  # Limit to top 3 reasons
                        st.write(f"• {reason}")
                
                st.write("---")
        else:
            st.warning("⚠️ No common houses found for this dasha combination.")
            
            # Show individual house activations
            st.write("**Individual House Activations:**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**{mahadasha} (MD):** {', '.join([f'H{h}' for h in sorted(maha_house_nums)])}")
            
            with col2:
                st.write(f"**{antardasha} (AD):** {', '.join([f'H{h}' for h in sorted(antar_house_nums)])}")
            
            with col3:
                st.write(f"**{pratyantardasha} (PD):** {', '.join([f'H{h}' for h in sorted(pratyantar_house_nums)])}")

        # Footer
        st.markdown("---")
        st.markdown("*Generated using Swiss Ephemeris and traditional Vedic astrology calculations*")
