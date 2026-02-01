"""
Laghu Parashari Dasha Analyzer - Streamlit App

Interactive Vedic astrology dasha analysis based on Laghu Parashari principles.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from laghu_parashari import (
    analyze_chart, PLANETS, SIGNS, SIGN_ABBREV, MIN_RUPAS_REQUIRED,
    FunctionalNature, get_sign_index, get_dasha_classification_explanation
)

# Page configuration
st.set_page_config(
    page_title="Laghu Parashari Dasha Analyzer",
    page_icon="🪐",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #1e1e2e;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #313244;
    }
    
    .nature-fb { color: #a6e3a1; font-weight: bold; }
    .nature-fm { color: #f38ba8; font-weight: bold; }
    .nature-imp { color: #f9e2af; font-weight: bold; }
    
    .result-excellent { background-color: #a6e3a1; color: black; padding: 2px 8px; border-radius: 4px; }
    .result-good { background-color: #94e2d5; color: black; padding: 2px 8px; border-radius: 4px; }
    .result-mixed { background-color: #f9e2af; color: black; padding: 2px 8px; border-radius: 4px; }
    .result-bad { background-color: #fab387; color: black; padding: 2px 8px; border-radius: 4px; }
    .result-verybad { background-color: #f38ba8; color: black; padding: 2px 8px; border-radius: 4px; }
    .result-maraka { background-color: #cba6f7; color: black; padding: 2px 8px; border-radius: 4px; }
    
    .strength-strong { color: #a6e3a1; }
    .strength-medium { color: #f9e2af; }
    .strength-weak { color: #f38ba8; }
    
    .metric-card {
        background-color: #313244;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🪐 Laghu Parashari Dasha Analyzer")
st.markdown("*Vedic astrology dasha analysis based on Maharshi Parashara's principles*")

# Sidebar inputs
st.sidebar.header("Birth Details")

birth_date = st.sidebar.date_input(
    "Birth Date",
    value=datetime(1971, 12, 22),
    min_value=datetime(1800, 1, 1),
    max_value=datetime(2100, 12, 31)
)

birth_time = st.sidebar.time_input(
    "Birth Time",
    value=datetime.strptime("10:40", "%H:%M").time(),
    step=60
)

st.sidebar.subheader("Location")
latitude = st.sidebar.number_input("Latitude", value=26.85, format="%.4f")
longitude = st.sidebar.number_input("Longitude", value=80.95, format="%.4f")
timezone_offset = st.sidebar.number_input("Timezone (UTC offset)", value=5.5, format="%.1f")

st.sidebar.subheader("Dasha Period Range")
current_year = datetime.now().year
dasha_start = st.sidebar.number_input("Start Year", value=current_year, min_value=1900, max_value=2200)
dasha_end = st.sidebar.number_input("End Year", value=current_year + 5, min_value=1900, max_value=2200)

# Session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Analyze button
if st.sidebar.button("🔮 Analyze Chart", type="primary", use_container_width=True):
    with st.spinner("Calculating chart..."):
        date_str = birth_date.strftime("%Y-%m-%d")
        time_str = birth_time.strftime("%H:%M")
        
        result = analyze_chart(
            date=date_str,
            time=time_str,
            latitude=latitude,
            longitude=longitude,
            timezone_offset=timezone_offset,
            dasha_start_year=int(dasha_start),
            dasha_end_year=int(dasha_end)
        )
        st.session_state.analysis_result = result
        st.success("Chart analyzed successfully!")

# Main content
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    chart = result.chart
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Chart Overview", "💪 Shadbala", "⚡ Functional Nature", "📅 Dasha Periods"])
    
    # Tab 1: Chart Overview
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Birth Details")
            st.write(f"**Date & Time:** {chart.birth_date.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Location:** {chart.latitude:.4f}°N, {chart.longitude:.4f}°E")
            st.write(f"**Timezone:** UTC{chart.timezone_offset:+.1f}")
            st.write(f"**Ayanamsa (Lahiri):** {chart.ayanamsa:.4f}°")
        
        with col2:
            st.subheader("Ascendant")
            st.write(f"**Lagna:** {SIGNS[chart.lagna_sign]} ({chart.lagna_degree:.2f}°)")
            st.write(f"**Day Birth:** {'Yes' if chart.is_day_birth else 'No'}")
            moon_phase_desc = "Shukla (Waxing)" if chart.moon_phase < 0.5 else "Krishna (Waning)"
            st.write(f"**Moon Phase:** {moon_phase_desc} ({chart.moon_phase*100:.1f}%)")
        
        st.subheader("Planetary Positions")
        
        planet_data = []
        for name in PLANETS:
            planet = chart.planets[name]
            planet_data.append({
                "Planet": name,
                "Longitude": f"{planet.longitude:.2f}°",
                "Sign": SIGNS[planet.sign_index],
                "Degree": f"{planet.degree_in_sign:.2f}°",
                "House": planet.house,
                "Nakshatra": planet.nakshatra_name,
                "Lordships": ", ".join(str(h) for h in planet.lordships) if planet.lordships else "-"
            })
        
        df_planets = pd.DataFrame(planet_data)
        st.dataframe(df_planets, use_container_width=True, hide_index=True)
        
        # Exchanges
        if chart.exchanges:
            st.subheader("🔄 Exchanges (Parivartana)")
            for p1, p2 in chart.exchanges:
                planet1 = chart.planets[p1]
                planet2 = chart.planets[p2]
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{p1}** ({SIGN_ABBREV[planet1.sign_index]}) ↔ **{p2}** ({SIGN_ABBREV[planet2.sign_index]})")
                with col2:
                    if planet1.virtual_longitude:
                        st.write(f"Virtual: {p1}→{SIGN_ABBREV[get_sign_index(planet1.virtual_longitude)]}, {p2}→{SIGN_ABBREV[get_sign_index(planet2.virtual_longitude)]}")
    
    # Tab 2: Shadbala
    with tab2:
        st.subheader("Shadbala (Six-fold Strength)")
        st.markdown("""
        Shadbala measures planetary strength across six dimensions. Values are in **Virupas** (1 Rupa = 60 Virupas).
        """)
        
        # Component descriptions
        with st.expander("ℹ️ Shadbala Components"):
            cols = st.columns(3)
            with cols[0]:
                st.write("**Sthana:** Positional (sign dignity)")
                st.write("**Dig:** Directional (strongest house)")
            with cols[1]:
                st.write("**Kala:** Temporal (day/night, hora)")
                st.write("**Chesta:** Motional (speed, retrograde)")
            with cols[2]:
                st.write("**Naisargika:** Natural (inherent)")
                st.write("**Drig:** Aspectual (aspects received)")
        
        shadbala_data = []
        for name in PLANETS:
            planet = chart.planets[name]
            if planet.shadbala:
                sb = planet.shadbala
                min_req = MIN_RUPAS_REQUIRED.get(name, 5.0)
                shadbala_data.append({
                    "Planet": name,
                    "Sthana": f"{sb.sthana_bala:.1f}",
                    "Dig": f"{sb.dig_bala:.1f}",
                    "Kala": f"{sb.kala_bala:.1f}",
                    "Chesta": f"{sb.chesta_bala:.1f}",
                    "Naisarg": f"{sb.naisargika_bala:.1f}",
                    "Drig": f"{sb.drig_bala:.1f}",
                    "Total": f"{sb.total_virupas:.1f}",
                    "Rupas": f"{sb.total_rupas:.2f}",
                    "Required": f"{min_req:.1f}",
                    "Strength": sb.strength_class,
                    "Percent": f"{sb.strength_percent:.0f}%"
                })
        
        df_shadbala = pd.DataFrame(shadbala_data)
        st.dataframe(df_shadbala, use_container_width=True, hide_index=True)
        
        # Visual strength bars
        st.subheader("Strength Overview")
        cols = st.columns(3)
        for i, name in enumerate(PLANETS):
            planet = chart.planets[name]
            if planet.shadbala:
                sb = planet.shadbala
                min_req = MIN_RUPAS_REQUIRED.get(name, 5.0)
                progress = min(1.0, sb.total_rupas / (min_req * 1.5))
                
                with cols[i % 3]:
                    if sb.strength_class == "Strong":
                        color = "🟢"
                    elif sb.strength_class == "Weak":
                        color = "🔴"
                    else:
                        color = "🟡"
                    
                    st.write(f"{color} **{name}** ({sb.strength_class})")
                    st.progress(progress, text=f"{sb.total_rupas:.1f}R / {min_req:.1f}R required")
    
    # Tab 3: Functional Nature
    with tab3:
        st.subheader("Functional Nature Analysis")
        st.markdown("""
        Classification based on Laghu Parashari rules:
        - **FB** (Functional Benefic): Trikona lords (1, 5, 9), Yoga Karakas
        - **FM** (Functional Malefic): Trishadaya lords (3, 6, 11), 8th lord
        - **IMP** (Impressionable): Resolved based on associations
        """)
        
        nature_data = []
        for name in PLANETS:
            planet = chart.planets[name]
            lordship_str = ", ".join(str(h) for h in planet.lordships) if planet.lordships else "-"
            influences_str = "; ".join(planet.influences[:3]) if planet.influences else "-"
            
            nature_data.append({
                "Planet": name,
                "Lordships": lordship_str,
                "Base Nature": planet.base_nature.value,
                "Final Nature": planet.final_nature.value,
                "Maraka": "Yes" if planet.is_maraka else "No",
                "Maraka Reason": planet.maraka_reason if planet.is_maraka else "-",
                "Influences": influences_str
            })
        
        df_nature = pd.DataFrame(nature_data)
        
        # Color code the nature columns
        def style_nature(val):
            if val == "FB":
                return "color: #a6e3a1; font-weight: bold"
            elif val == "FM":
                return "color: #f38ba8; font-weight: bold"
            elif val == "IMP":
                return "color: #f9e2af; font-weight: bold"
            return ""
        
        styled_df = df_nature.style.applymap(style_nature, subset=["Base Nature", "Final Nature"])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Summary counts
        col1, col2, col3, col4 = st.columns(4)
        fb_count = sum(1 for p in chart.planets.values() if p.final_nature == FunctionalNature.FB)
        fm_count = sum(1 for p in chart.planets.values() if p.final_nature == FunctionalNature.FM)
        maraka_count = sum(1 for p in chart.planets.values() if p.is_maraka)
        exchange_count = len(chart.exchanges)
        
        col1.metric("Functional Benefics", fb_count)
        col2.metric("Functional Malefics", fm_count)
        col3.metric("Marakas", maraka_count)
        col4.metric("Exchanges", exchange_count)
    
    # Tab 4: Dasha Periods
    with tab4:
        st.subheader("Vimshottari Dasha Periods")
        
        periods = result.dasha_periods
        
        if not periods:
            st.warning("No dasha periods found for the selected date range.")
        else:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                result_filter = st.multiselect(
                    "Filter by Result",
                    options=["Excellent", "Good", "Mixed", "Bad", "Very Bad", "Maraka", "Ordinary"],
                    default=[]
                )
            with col2:
                md_filter = st.multiselect(
                    "Filter by Mahadasha Lord",
                    options=PLANETS,
                    default=[]
                )
            
            # Legend
            st.markdown("**Result Legend:** 🟢 Excellent | 🔵 Good | 🟡 Mixed | 🟠 Bad | 🔴 Very Bad | 🟣 Maraka")
            st.markdown("---")
            
            # Filter periods
            filtered_periods = []
            for period in periods:
                if result_filter:
                    if not any(r.lower() in period.overall_result.lower() for r in result_filter):
                        continue
                if md_filter and period.md_lord not in md_filter:
                    continue
                filtered_periods.append(period)
            
            if filtered_periods:
                st.write(f"**Showing {len(filtered_periods)} periods** (click to expand for details)")
                
                for i, period in enumerate(filtered_periods):
                    # Get result emoji
                    result_lower = period.overall_result.lower()
                    if "excellent" in result_lower:
                        emoji = "🟢"
                    elif "good" in result_lower and "very" not in result_lower:
                        emoji = "🔵"
                    elif "mixed" in result_lower:
                        emoji = "🟡"
                    elif "very bad" in result_lower:
                        emoji = "🔴"
                    elif "bad" in result_lower:
                        emoji = "🟠"
                    elif "maraka" in result_lower:
                        emoji = "🟣"
                    else:
                        emoji = "⚪"
                    
                    # Create expander header
                    header = f"{emoji} **{period.md_lord}-{period.ad_lord}-{period.pd_lord}** | {period.start_date.strftime('%Y-%m-%d')} to {period.end_date.strftime('%Y-%m-%d')} | {period.overall_result}"
                    
                    with st.expander(header):
                        # Get detailed explanation
                        explanation = get_dasha_classification_explanation(
                            chart, period.md_lord, period.ad_lord, period.pd_lord
                        )
                        
                        # Summary row
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            md_color = "#a6e3a1" if explanation["md_fb"] else "#f38ba8"
                            st.markdown(f"**MD:** <span style='color:{md_color}'>{period.md_lord} ({period.md_nature})</span>", unsafe_allow_html=True)
                        with col2:
                            ad_color = "#a6e3a1" if explanation["ad_fb"] else "#f38ba8"
                            st.markdown(f"**AD:** <span style='color:{ad_color}'>{period.ad_lord} ({period.ad_nature})</span>", unsafe_allow_html=True)
                        with col3:
                            pd_color = "#a6e3a1" if explanation["pd_fb"] else "#f38ba8"
                            st.markdown(f"**PD:** <span style='color:{pd_color}'>{period.pd_lord} ({period.pd_nature})</span>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Story/Explanation
                        st.markdown("**📖 Why this result?**")
                        st.info(explanation["story"])
                        
                        # Rule reference
                        if explanation["rule"]:
                            st.caption(f"📜 {explanation['rule']}")
                        
                        # Key factors
                        st.markdown("**🔑 Key Factors:**")
                        for factor in explanation["factors"]:
                            if "✓" in factor:
                                st.markdown(f"<span style='color:#a6e3a1'>{factor}</span>", unsafe_allow_html=True)
                            elif "❌" in factor:
                                st.markdown(f"<span style='color:#f38ba8'>{factor}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(factor)
                        
                        # Shadbala note
                        if explanation["shadbala_note"]:
                            st.markdown("---")
                            st.markdown(f"**Shadbala Impact:** {explanation['shadbala_note']}")
                        
                        # Houses affected
                        st.markdown("---")
                        st.markdown(f"**🏠 Houses Activated:** `{period.affected_houses}`")
                        st.caption("a=aspect, p=placement, l=lordship | MD/AD/PD = which dasha level activates")
            else:
                st.info("No periods match the selected filters.")

else:
    # Welcome message
    st.info("👈 Enter birth details in the sidebar and click **Analyze Chart** to begin!")
    
    with st.expander("ℹ️ About Laghu Parashari"):
        st.markdown("""
        **Laghu Parashari** (also known as Jataka Chandrika or Ududaya Pradeep) is a classical 
        Vedic astrology text that provides rules for determining:
        
        - **Functional Benefic (FB)**: Planets that bring positive results based on lordship
        - **Functional Malefic (FM)**: Planets that bring challenging results
        - **Dasha Classification**: How periods combine to give results
        
        **Key Principles:**
        1. Trikona lords (1, 5, 9) are FB
        2. Trishadaya lords (3, 6, 11) are FM
        3. Connected FB+FM gives mixed results
        4. Unconnected FB cannot help during FM period
        5. Yoga Karaka (kendra + trikona lord) is very auspicious
        
        **Shadbala Integration:**
        This analyzer also includes Shadbala (six-fold planetary strength) to refine predictions.
        Strong MD lords amplify results, weak MD lords dampen extremes.
        """)
    
    with st.expander("📊 Sample Charts"):
        st.markdown("""
        Try these example charts:
        
        | Name | Date | Time | Location | Lat | Lon | TZ |
        |------|------|------|----------|-----|-----|-----|
        | Example 1 | 1971-12-22 | 10:40 | Lucknow | 26.85 | 80.95 | +5.5 |
        | Example 2 | 1937-03-18 | 21:02 | India | 28.34 | 79.40 | +5.5 |
        """)
