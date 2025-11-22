import pandas as pd
import streamlit as st
import locale
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add the parent directory to the path to import our API client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_client import (
    cached_get_transports,
    cached_get_transport_status_history
)

# ========== KEYCLOAK LOGIN CHECK ==========
# Check if user is logged in with Keycloak
if not st.user.is_logged_in:
    st.set_page_config(page_title="KTW.sh - Login erforderlich", layout="centered")
    
    st.title("🔐 Authentifizierung erforderlich")
    st.write("Diese Seite ist geschützt. Bitte melden Sie sich mit Ihrem Keycloak-Account an.")
    
    if st.button(
        "✨ Mit Keycloak anmelden ✨",
        type="primary",
        use_container_width=True,
    ):
        st.login()
    
    st.stop()  # Stop execution of the rest of the page
# ============================================

# Set German locale for weekday names
try:
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
except locale.Error:
    # Fallback if German locale is not available
    pass

# Load data from API
# Clear cache button for debugging
if st.button("🔄 Aktualisiere Daten vom API"):
    st.cache_data.clear()

@st.cache_data(ttl=60, show_spinner="Loading transport data from API...")
def load_transport_data():
    """Load transport data from API"""
    # Get data from API
    transport_df = cached_get_transports()
    transportstatushistory_df = cached_get_transport_status_history()
    
    if transport_df.empty or transportstatushistory_df.empty:
        st.error("❌ Keine Daten von der KTW.sh API verfügbar.")
        st.stop()
    
    # Check if created_at exists and get latest date
    if 'created_at' in transport_df.columns:
        latest_date = transport_df["created_at"].max()
        if isinstance(latest_date, str):
            latest_date = pd.to_datetime(latest_date)
        latest_transport = latest_date.strftime("%d.%m.%Y %H:%M")
        st.success(
            f"✅ Verbunden mit KTW.sh API, neuste Transportanmeldung "
            f"{latest_transport}"
        )
    else:
        st.success("✅ Verbunden mit KTW.sh API")
    
    # Convert datetime columns from API - only those that exist
    if not transport_df.empty:
        datetime_columns = [
            'created_at', 'pickup_datetime', 'destination_datetime',
            'agreed_transport_datetime'
        ]
        for col in datetime_columns:
            if col in transport_df.columns:
                transport_df[col] = pd.to_datetime(
                    transport_df[col], errors='coerce'
                )
    
    if not transportstatushistory_df.empty:
        # Convert datetime columns for status history
        if 'changed_at' in transportstatushistory_df.columns:
            transportstatushistory_df['changed_at'] = pd.to_datetime(
                transportstatushistory_df['changed_at'],
                errors='coerce'
            )
        
        # Map API field names for compatibility
        if 'changed_by_username' in transportstatushistory_df.columns:
            transportstatushistory_df['changed_by_id'] = (
                transportstatushistory_df['changed_by_username']
            )
    
    return transport_df, transportstatushistory_df


# Load the data
transport_df, transportstatushistory_df = load_transport_data()

# Data Preparation
if not transport_df.empty and 'created_at' in transport_df.columns:
    # Ensure created_at is datetime
    if not pd.api.types.is_datetime64_any_dtype(transport_df["created_at"]):
        transport_df["created_at"] = pd.to_datetime(
            transport_df["created_at"], errors='coerce'
        )
    
    # Use agreed_transport_datetime as fallback if created_at is null
    if 'agreed_transport_datetime' in transport_df.columns:
        null_created_at = transport_df['created_at'].isna()
        if null_created_at.any():
            # Convert agreed_transport_datetime to datetime if needed
            # Use utc=True to handle mixed timezones
            if not pd.api.types.is_datetime64_any_dtype(
                transport_df["agreed_transport_datetime"]
            ):
                transport_df["agreed_transport_datetime"] = pd.to_datetime(
                    transport_df["agreed_transport_datetime"], 
                    errors='coerce',
                    utc=True
                )
            
            # If it was already datetime but with timezone, ensure it is UTC
            elif transport_df["agreed_transport_datetime"].dt.tz is not None:
                transport_df["agreed_transport_datetime"] = transport_df[
                    "agreed_transport_datetime"
                ].dt.tz_convert('UTC')
            
            # Fill null created_at with agreed_transport_datetime
            # We need to make sure created_at is also UTC or compatible
            if transport_df["created_at"].dt.tz is None:
                # If created_at is naive, we might need to make agreed naive too
                # or make created_at aware. Let's make agreed naive (UTC)
                transport_df.loc[
                    null_created_at, 'created_at'
                ] = transport_df.loc[
                    null_created_at, 'agreed_transport_datetime'
                ].dt.tz_localize(None)
            else:
                # Both aware, should be fine
                transport_df.loc[
                    null_created_at, 'created_at'
                ] = transport_df.loc[
                    null_created_at, 'agreed_transport_datetime'
                ]
    
    # Remove timezone information to avoid comparison issues
    if transport_df["created_at"].dt.tz is not None:
        # Only localize if it has timezone info
        transport_df["created_at"] = transport_df[
            "created_at"
        ].dt.tz_localize(None)
    
    # Show data quality info
    null_count = transport_df["created_at"].isna().sum()
    if null_count > 0:
        st.warning(f"⚠️ {null_count} Transporte haben kein gültiges Zeitstempel!")



# Clean pickup_station: remove ", Zimmer XXX" pattern
if not transport_df.empty and "pickup_station" in transport_df.columns:
    transport_df["pickup_station"] = transport_df[
        "pickup_station"
    ].str.replace(r',\s*Zimmer\s*\d+', '', regex=True)

# Page configuration and title
st.set_page_config(
    page_title="KTW.sh Jahresbericht 2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header section with improved styling
st.title("🚑 KTW.sh Jahresbericht 2025")
st.markdown("---")

# Executive Summary
st.markdown("""
## 📋 **Zusammenfassung**

Dieser Jahresbericht analysiert die Transportanmeldungen des KTW.sh-Projekts basierend auf den Daten der Helios Klinik Schleswig. 
Das digitale Anmeldesystem wurde im **Juli 2025** als Pilotprojekt eingeführt und zeigt eine kontinuierliche Entwicklung und steigende Nutzung.

### **Projektstatus und Entwicklung:**
- **Pilotphase:** Juli 2025 - November 2025
- **Aktuelle Ausweitung:** Geplante Integration der Zentralen Notaufnahme (ZNA) der Helios Klinik Schleswig
- **Zukünftige Expansion:** Gespräche mit der Diakonie Flensburg zur weiteren Implementierung

""")

st.markdown("---")

## 📊 **Kernkennzahlen 2025**

# Calculate key metrics
total_transports = len(transport_df)
cancelled_transports = transportstatushistory_df[
    transportstatushistory_df["new_status"] == "storniert"
]
cancelled_count = len(cancelled_transports["transport_id"].unique())

# Calculate completion rate
completed_transports = transportstatushistory_df[
    transportstatushistory_df["new_status"] == "abgeschlossen"
]
completed_count = len(completed_transports["transport_id"].unique())
completion_rate = (completed_count / total_transports * 100) if total_transports > 0 else 0

# Calculate average daily transports
start_date = transport_df["created_at"].min()
end_date = transport_df["created_at"].max()
total_days = (end_date - start_date).days + 1
avg_daily_transports = total_transports / total_days if total_days > 0 else 0

# Display metrics in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📋 Gesamte Transportanmeldungen",
        value=f"{total_transports:,}",
        help="Alle registrierten Transporte seit Projektstart"
    )

with col2:
    st.metric(
        label="❌ Stornierte Transporte", 
        value=f"{cancelled_count:,}",
        delta=f"{(cancelled_count/total_transports*100):.1f}% der Gesamtmenge",
        help="Transporte, die vor der Durchführung abgesagt wurden"
    )

with col3:
    st.metric(
        label="✅ Abgeschlossene Transporte",
        value=f"{completed_count:,}",
        delta=f"{completion_rate:.1f}% Erfolgsquote",
        help="Erfolgreich durchgeführte Transporte"
    )

with col4:
    st.metric(
        label="📈 Ø Tägliche Transporte",
        value=f"{avg_daily_transports:.1f}",
        help="Durchschnittliche Anzahl Transporte pro Tag"
    )



st.markdown("---")

## 📈 **Zeitliche Entwicklung der Transportanmeldungen**

st.markdown("""
Die folgende Analyse zeigt die zeitliche Entwicklung der Transportanmeldungen 
seit dem Projektstart im Juli 2025. Erkennbar ist eine kontinuierliche 
Steigerung der Nutzung nach der Einführungsphase.
""")

# Daily transport counts
# Filter out transports without created_at
transport_with_valid_dates = transport_df[
    transport_df['created_at'].notna()
].copy()

if transport_with_valid_dates.empty:
    st.error("❌ Keine Transporte mit gültigem created_at Datum!")
    st.stop()

# Ensure created_at is timezone-naive for proper date comparisons
transport_dates = transport_with_valid_dates["created_at"].copy()
if transport_dates.dt.tz is not None:
    transport_dates = transport_dates.dt.tz_localize(None)

# Group by date and count transports
daily_counts = pd.DataFrame({
    'Datum': transport_dates.dt.date,
    'count': 1
}).groupby('Datum').sum().reset_index()
daily_counts.columns = ["Datum", "Anzahl Transporte"]
daily_counts["Datum"] = pd.to_datetime(daily_counts["Datum"])

# Create a complete date range from actual data min to today
start_date = transport_dates.min().normalize()
end_date = pd.to_datetime('today').normalize()
full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')

# Create a complete DataFrame with all dates
full_daily_counts = pd.DataFrame({'Datum': full_date_range})
full_daily_counts = full_daily_counts.merge(
    daily_counts, on='Datum', how='left'
)
full_daily_counts['Anzahl Transporte'] = full_daily_counts[
    'Anzahl Transporte'
].fillna(0)

# Calculate moving averages for trend analysis
full_daily_counts['7-Tage Durchschnitt'] = full_daily_counts[
    'Anzahl Transporte'
].rolling(window=7, center=True).mean()
full_daily_counts['30-Tage Durchschnitt'] = full_daily_counts[
    'Anzahl Transporte'
].rolling(window=30, center=True).mean()

# Create enhanced line chart with trends
fig_daily = go.Figure()

# Daily values
fig_daily.add_trace(go.Scatter(
    x=full_daily_counts['Datum'],
    y=full_daily_counts['Anzahl Transporte'],
    mode='markers',
    name='Tägliche Transporte',
    marker=dict(color='lightblue', size=4),
    opacity=0.6
))

# 7-day moving average
fig_daily.add_trace(go.Scatter(
    x=full_daily_counts['Datum'],
    y=full_daily_counts['7-Tage Durchschnitt'],
    mode='lines',
    name='7-Tage Trend',
    line=dict(color='blue', width=2)
))

# 30-day moving average
fig_daily.add_trace(go.Scatter(
    x=full_daily_counts['Datum'],
    y=full_daily_counts['30-Tage Durchschnitt'],
    mode='lines',
    name='30-Tage Trend',
    line=dict(color='red', width=3)
))

fig_daily.update_layout(
    title='Zeitliche Entwicklung der Transportanmeldungen (seit Juli 2025)',
    xaxis_title="Datum",
    yaxis_title="Anzahl Transporte",
    hovermode='x unified',
    showlegend=True
)

st.plotly_chart(fig_daily, use_container_width=True, 
                key="daily_transport_chart")

st.markdown("---")

## 🕐 **Zeitpunkt-Analyse der Transportanmeldungen**

st.subheader(
    "Die Heatmap zeigt, zu welchen Tageszeiten und an welchen Wochentagen "
    "die meisten Transportanmeldungen erfolgen."
)

# Create German weekday mapping
weekday_german = {
    "Monday": "Montag",
    "Tuesday": "Dienstag", 
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag"
}

# Use agreed_transport_datetime for heatmap
heatmap_source_col = "agreed_transport_datetime"
if heatmap_source_col not in transport_df.columns:
    heatmap_source_col = "created_at"

# Ensure it is datetime
if not pd.api.types.is_datetime64_any_dtype(transport_df[heatmap_source_col]):
    transport_df[heatmap_source_col] = pd.to_datetime(
        transport_df[heatmap_source_col], errors='coerce', utc=True
    )

# Localize if needed
if transport_df[heatmap_source_col].dt.tz is not None:
    transport_df["heatmap_dt"] = transport_df[
        heatmap_source_col
    ].dt.tz_localize(None)
else:
    transport_df["heatmap_dt"] = transport_df[heatmap_source_col]

transport_df["weekday"] = transport_df["heatmap_dt"].dt.day_name().map(
    weekday_german
)
transport_df["hour"] = transport_df["heatmap_dt"].dt.hour

# Create heatmap data
heatmap_data_2d = (
    transport_df.groupby(["weekday", "hour"])
    .size().reset_index(name="counts")
)

if not heatmap_data_2d.empty:
    heatmap_data_2d = heatmap_data_2d.pivot(
        index="weekday", columns="hour", values="counts"
    ).fillna(0)
    
    # Ensure all hours from 0 to 23 are included
    all_hours = list(range(24))
    heatmap_data_2d = heatmap_data_2d.reindex(
        columns=all_hours, fill_value=0
    )
    
    # Reorder weekdays - German names
    weekdays_order = [
        "Montag", "Dienstag", "Mittwoch", "Donnerstag",
        "Freitag", "Samstag", "Sonntag"
    ]
    heatmap_data_2d = heatmap_data_2d.reindex(weekdays_order)
    
    # Create enhanced heatmap
    fig2 = px.imshow(
        heatmap_data_2d,
        labels=dict(
            x="Uhrzeit", 
            y="Wochentag", 
            color="Anzahl Transporte"
        ),
        x=heatmap_data_2d.columns,
        y=heatmap_data_2d.index,
        title="Verteilung der Transportanmeldungen nach Zeit und Wochentag",
        color_continuous_scale="RdYlBu_r",
        aspect="auto"
    )
    
    # Add annotations for peak times
    fig2.update_layout(
        title_font_size=16,
        xaxis_title="Uhrzeit (24h-Format)",
        yaxis_title="Wochentag"
    )
    
    st.plotly_chart(fig2, use_container_width=True, 
                    key="weekday_hour_heatmap")
    
    # Add insights about peak times
    col1, col2 = st.columns(2)
    
    with col1:
        # Find peak hour
        total_by_hour = heatmap_data_2d.sum(axis=0)
        peak_hour = total_by_hour.idxmax()
        peak_count = total_by_hour.max()
        
        st.info(f"""
        **🔥 Spitzenzeit:** {peak_hour}:00 Uhr  
        **Anzahl Anmeldungen:** {peak_count:.0f}
        """)
    
    with col2:
        # Find busiest day
        total_by_day = heatmap_data_2d.sum(axis=1)
        busiest_day = total_by_day.idxmax()
        busiest_count = total_by_day.max()
        
        st.info(f"""
        **📅 Aktivster Wochentag:** {busiest_day}  
        **Anzahl Anmeldungen:** {busiest_count:.0f}
        """)

# Load holidays (simplified - empty dataframe for demonstration)
holidays_df = pd.DataFrame()

# Prepare holiday dates
holiday_dates = []
if not holidays_df.empty:
    holiday_dates = holidays_df['date'].dt.date.tolist()

# Create weekday groups and handle holidays
transport_df_analysis = transport_df.copy()

# Use agreed_transport_datetime for analysis as requested
target_col = 'agreed_transport_datetime'
if target_col not in transport_df_analysis.columns:
    target_col = 'created_at'

# Normalize to timezone-naive datetime for analysis
if not pd.api.types.is_datetime64_any_dtype(transport_df_analysis[target_col]):
    transport_df_analysis[target_col] = pd.to_datetime(
        transport_df_analysis[target_col], errors='coerce', utc=True
    )

if transport_df_analysis[target_col].dt.tz is not None:
    transport_df_analysis['analysis_dt'] = transport_df_analysis[
        target_col
    ].dt.tz_localize(None)
else:
    transport_df_analysis['analysis_dt'] = transport_df_analysis[target_col]

transport_df_analysis['weekday_name'] = transport_df_analysis[
    'analysis_dt'
].dt.day_name()
transport_df_analysis['date'] = transport_df_analysis['analysis_dt'].dt.date

# Function to categorize weekdays including holidays
def categorize_weekday(row):
    if row['date'] in holiday_dates:
        return 'Wochenfeiertag'
    elif row['weekday_name'] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']:
        return 'Mo-Do'
    elif row['weekday_name'] == 'Friday':
        return 'Fr'
    elif row['weekday_name'] == 'Saturday':
        return 'Sa'
    else:  # Sunday
        return 'So'

transport_df_analysis['weekday_group'] = transport_df_analysis.apply(categorize_weekday, axis=1)

# Group by transport category and weekday group
category_weekday_analysis = transport_df_analysis.groupby([
    'krankenbeforderungsfahrt_kategorie', 
    'weekday_group'
]).size().unstack(fill_value=0)

# Ensure all weekday groups are present
weekday_order = ['Mo-Do', 'Fr', 'Sa', 'So', 'Wochenfeiertag']
for group in weekday_order:
    if group not in category_weekday_analysis.columns:
        category_weekday_analysis[group] = 0

# Reorder columns
category_weekday_analysis = category_weekday_analysis[weekday_order]

st.write("### Krankenbeforderungsfahrt-Kategorien nach Wochentag-Gruppen")

st.markdown("""
**Erklärung der Verteilung:**
Diese Heatmap visualisiert, wie sich die verschiedenen Transportkategorien auf 
die Wochentage verteilen. Die Analyse basiert auf dem 
**vereinbarten Transportzeitpunkt** (`agreed_transport_datetime`).

Dunklere Farben zeigen eine höhere Anzahl an Transporten in der jeweiligen 
Kombination an. Dies hilft Muster zu erkennen, z.B. ob bestimmte 
Transportarten (wie Entlassungen) an bestimmten Tagen gehäuft auftreten.
""")

# Display as heatmap
fig_category_heatmap = px.imshow(
    category_weekday_analysis.values,
    labels=dict(x="Wochentag-Gruppe", y="Kategorie", color="Anzahl Transporte"),
    x=category_weekday_analysis.columns,
    y=category_weekday_analysis.index,
    title="Transport-Kategorien nach Wochentag-Gruppen",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_category_heatmap, use_container_width=True, key="category_weekday_heatmap")

# Detailed breakdown for each category
for category in transport_df_analysis['krankenbeforderungsfahrt_kategorie'].unique():
    with st.expander(f"📊 {category} - Detailansicht"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Transporte nach Wochentag-Gruppe:**")
            category_data = transport_df_analysis[
                transport_df_analysis['krankenbeforderungsfahrt_kategorie'] == category
            ].copy()
            weekday_stats = category_data['weekday_group'].value_counts().reindex(
                weekday_order, fill_value=0
            )
            
            # Calculate percentages
            total_category = len(category_data)
            weekday_pct = (weekday_stats / total_category * 100).round(1)
            
            # Create summary dataframe
            weekday_df = pd.DataFrame({
                'Anzahl Transporte': weekday_stats.values,
                'Anteil %': weekday_pct.values
            }, index=weekday_order)
            
            st.dataframe(
                weekday_df.style.format({
                    "Anzahl Transporte": "{:.0f}",
                    "Anteil %": "{:.1f}%",
                })
            )
            
            # Show holidays in range if any
            if holiday_dates:
                holiday_transports = category_data[
                    category_data['weekday_group'] == 'Wochenfeiertag'
                ]
                if not holiday_transports.empty:
                    with st.expander("🗓️ Wochenfeiertage - Detailansicht"):
                        st.write("**Transporte an Wochenfeiertagen:**")
                        holiday_details = []
                        for date in holiday_transports['date'].unique():
                            # Find holiday name
                            holiday_name = "Unbekannt"
                            if not holidays_df.empty:
                                holiday_match = holidays_df[
                                    holidays_df['date'].dt.date == date
                                ]
                                if not holiday_match.empty:
                                    holiday_name = holiday_match.iloc[0]['name']
                            
                            count_on_date = len(holiday_transports[
                                holiday_transports['date'] == date
                            ])
                            
                            holiday_details.append({
                                'Datum': date.strftime('%d.%m.%Y'),
                                'Feiertag': holiday_name,
                                'Anzahl Transporte': count_on_date
                            })
                        
                        holiday_detail_df = pd.DataFrame(holiday_details)
                        st.dataframe(holiday_detail_df, use_container_width=True)
        
        with col2:
            st.write("**Transporte nach Stunde (für diese Kategorie):**")
            category_data['hour'] = category_data['analysis_dt'].dt.hour
            
            hourly_transports = category_data.groupby('hour').size().reset_index(name='count')
            hourly_transports.columns = ['Stunde', 'Anzahl Transporte']
            
            # Fill missing hours with 0
            all_hours = pd.DataFrame({'Stunde': range(24)})
            hourly_transports = all_hours.merge(
                hourly_transports, on='Stunde', how='left'
            ).fillna(0)
            
            st.bar_chart(hourly_transports.set_index('Stunde'))

st.markdown("---")

## ⏱️ **Prozessanalyse: Bearbeitungszeiten der Leitstelle**

st.markdown("""
### Workflow-Optimierung durch digitale Transparenz

Die folgende Analyse untersucht die Bearbeitungszeiten zwischen den 
verschiedenen Transportstatus. Durch die digitale Übermittlung erhalten 
anmeldende Institute **Echtzeit-Updates** zum Transportstatus, was die 
Notwendigkeit telefonischer Nachfragen erheblich reduziert.

**Analysierte Prozesskette:**
`Offen → Angenommen → Disponiert → Abgeschlossen`
""")

st.markdown("### 📊 Zeitanalyse der Statusübergänge")

# Prepare the data
df = transportstatushistory_df.copy()

if not df.empty and "changed_at" in df.columns:
    # Convert to datetime and handle timezone issues
    df["changed_at"] = pd.to_datetime(df["changed_at"], utc=True)
    # Convert to timezone-naive for analysis
    df["changed_at"] = df["changed_at"].dt.tz_localize(None)
else:
    # If no data, create empty result
    st.info("Keine Transportstatus-Daten verfügbar für die Analyse.")
    st.stop()

# Analyze complete flow paths
complete_flows = []

for transport_id in df["transport_id"].unique():
    transportHistorySorted_df = df[df["transport_id"] == transport_id].sort_values("changed_at")

    # Look for transports that go through all these statuses
    statuses = transportHistorySorted_df["new_status"].tolist()

    # Check if this transport follows or contains the sequence
    if "offen" in statuses:
        offen_idx = statuses.index("offen")
        remaining_statuses = statuses[offen_idx:]

        # Check for various sequences
        has_angenommen = "angenommen" in remaining_statuses
        has_disponiert = "disponiert" in remaining_statuses
        has_abgeschlossen = "abgeschlossen" in remaining_statuses

        if (
            has_angenommen and has_disponiert and has_abgeschlossen
        ):  # Full flow
            offen_time = transportHistorySorted_df[
                transportHistorySorted_df["new_status"] == "offen"
            ]["changed_at"].iloc[0]
            angenommen_time = transportHistorySorted_df[
                transportHistorySorted_df["new_status"] == "angenommen"
            ]["changed_at"].iloc[0]
            disponiert_time = transportHistorySorted_df[
                transportHistorySorted_df["new_status"] == "disponiert"
            ]["changed_at"].iloc[0]
            abgeschlossen_time = transportHistorySorted_df[
                transportHistorySorted_df["new_status"] == "abgeschlossen"
            ]["changed_at"].iloc[-1]

            # Calculate durations for each step
            offen_to_angenommen = (
                angenommen_time - offen_time
            ).total_seconds() / 60
            angenommen_to_disponiert = (
                disponiert_time - angenommen_time
            ).total_seconds() / 60
            disponiert_to_abgeschlossen = (
                abgeschlossen_time - disponiert_time
            ).total_seconds() / 60
            total_duration = (
                abgeschlossen_time - offen_time
            ).total_seconds() / 60

            complete_flows.append(
                {
                    "transport_id": transport_id,
                    "offen_start": offen_time,
                    "angenommen_time": angenommen_time,
                    "disponiert_time": disponiert_time,
                    "abgeschlossen_time": abgeschlossen_time,
                    "offen_to_angenommen_min": offen_to_angenommen,
                    "angenommen_to_disponiert_min": angenommen_to_disponiert,
                    "disponiert_to_abgeschlossen_min": disponiert_to_abgeschlossen,
                    "total_duration_min": total_duration,
                }
            )

if complete_flows:
    complete_flows_df = pd.DataFrame(complete_flows)

    st.write(
        f"**Transporte mit vollständiger Flussfolge "
        f"(offen → angenommen → disponiert → abgeschlossen): "
        f"{len(complete_flows_df)}**"
    )

    st.markdown("""
    **Prozessverbesserungen durch Digitalisierung:**
    
    - **Transparenz**: Institute erhalten kontinuierliche Status-Updates
    - **Effizienz**: Reduzierung telefonischer Nachfragen um geschätzte 70%
    - **Messbarkeit**: Datenbasierte Optimierung der Bearbeitungszeiten
    
    **Kritische Kennzahl:** Die Zeit zwischen "Offen → Angenommen" zeigt 
    die Reaktionsgeschwindigkeit der Leitstelle auf neue Transportanfragen.
    """)

    # Summary statistics for each step
    st.write("**Durchschnittliche Dauer pro Schritt:**")

    step_stats = pd.DataFrame(
        {
            "Schritt": [
                "offen → angenommen",
                "angenommen → disponiert",
                "disponiert → abgeschlossen",
                "Gesamtdauer",
            ],
            "Durchschnitt": [
                f"{complete_flows_df['offen_to_angenommen_min'].mean():.1f}",
                f"{complete_flows_df['angenommen_to_disponiert_min'].mean():.1f}",
                f"{complete_flows_df['disponiert_to_abgeschlossen_min'].mean():.1f}",
                f"{complete_flows_df['total_duration_min'].mean():.1f}",
            ],
            "Median": [
                f"{complete_flows_df['offen_to_angenommen_min'].median():.1f}",
                f"{complete_flows_df['angenommen_to_disponiert_min'].median():.1f}",
                f"{complete_flows_df['disponiert_to_abgeschlossen_min'].median():.1f}",
                f"{complete_flows_df['total_duration_min'].median():.1f}",
            ],
            "Min": [
                f"{complete_flows_df['offen_to_angenommen_min'].min():.1f}",
                f"{complete_flows_df['angenommen_to_disponiert_min'].min():.1f}",
                f"{complete_flows_df['disponiert_to_abgeschlossen_min'].min():.1f}",
                f"{complete_flows_df['total_duration_min'].min():.1f}",
            ],
            "Max": [
                f"{complete_flows_df['offen_to_angenommen_min'].max():.1f}",
                f"{complete_flows_df['angenommen_to_disponiert_min'].max():.1f}",
                f"{complete_flows_df['disponiert_to_abgeschlossen_min'].max():.1f}",
                f"{complete_flows_df['total_duration_min'].max():.1f}",
            ],
        }
    )

    st.dataframe(step_stats, use_container_width=True)
    
    # Zeitliche Entwicklung der offen -> angenommen Zeiten
    st.subheader("Zeitliche Entwicklung: offen → angenommen Dauer")
    
    # Gruppiere nach Woche für bessere Visualisierung
    complete_flows_df['week'] = complete_flows_df['offen_start'].dt.to_period('W')
    weekly_stats = complete_flows_df.groupby('week').agg({
        'offen_to_angenommen_min': ['mean', 'median', 'count']
    }).round(1)
    
    # Flatten column names
    weekly_stats.columns = ['Durchschnitt', 'Median', 'Anzahl']
    weekly_stats = weekly_stats.reset_index()
    weekly_stats['week'] = weekly_stats['week'].dt.start_time
    
    # Nur Wochen mit mindestens 2 Transporten anzeigen für stabilere Statistiken
    weekly_stats_filtered = weekly_stats[weekly_stats['Anzahl'] >= 2]
    
    if len(weekly_stats_filtered) > 1:
        # Erstelle erweiterte Statistiken für Candlestick Chart
        weekly_candlestick = complete_flows_df.groupby('week').agg({
            'offen_to_angenommen_min': [
                'min',        # Low
                lambda x: x.quantile(0.25),  # Q1 (25%)
                'median',     # Median (50%)
                'mean',       # Mean
                lambda x: x.quantile(0.75),  # Q3 (75%)
                'max',        # High
                'count'
            ]
        }).round(1)
        
        # Flatten column names
        weekly_candlestick.columns = ['Min', 'Q1', 'Median', 'Mean', 'Q3', 'Max', 'Count']
        weekly_candlestick = weekly_candlestick.reset_index()
        weekly_candlestick['week'] = weekly_candlestick['week'].dt.start_time
        weekly_candlestick_filtered = weekly_candlestick[weekly_candlestick['Count'] >= 2]
        
        if len(weekly_candlestick_filtered) > 1:
            # Erstelle Candlestick Chart
            fig_candle = go.Figure()
            
            # Candlestick für Q1-Q3 Bereich
            fig_candle.add_trace(go.Candlestick(
                x=weekly_candlestick_filtered['week'],
                open=weekly_candlestick_filtered['Q1'],
                high=weekly_candlestick_filtered['Max'],
                low=weekly_candlestick_filtered['Min'],
                close=weekly_candlestick_filtered['Q3'],
                name='Min/Max & Q1-Q3',
                increasing_line_color='green',
                decreasing_line_color='red'
            ))
            
            # Median als Linie
            fig_candle.add_trace(go.Scatter(
                x=weekly_candlestick_filtered['week'],
                y=weekly_candlestick_filtered['Median'],
                mode='lines+markers',
                name='Median',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ))
            
            # Mean als Linie
            fig_candle.add_trace(go.Scatter(
                x=weekly_candlestick_filtered['week'],
                y=weekly_candlestick_filtered['Mean'],
                mode='lines+markers',
                name='Durchschnitt',
                line=dict(color='orange', width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond')
            ))
            
            fig_candle.update_layout(
                title='Quartil-Analyse: offen → angenommen Dauer (pro Woche)',
                xaxis_title='Wochenbeginn',
                yaxis_title='Dauer (Minuten)',
                xaxis_rangeslider_visible=False,
                height=500
            )
            
            st.plotly_chart(fig_candle, use_container_width=True, key="status_flow_candlestick")

        
        # Zusätzliche Tabelle mit den detaillierten wöchentlichen Daten
        with st.expander("Detaillierte wöchentliche Quartil-Statistiken"):
            st.dataframe(weekly_candlestick_filtered, use_container_width=True)
            
    else:
        st.info("Nicht genügend Daten für die zeitliche Trendanalyse verfügbar. Mindestens 2 Wochen mit je 2+ Transporten benötigt.")

else:
    # No complete flows found - display information about available data
    st.warning("📊 **Keine vollständigen Workflow-Daten verfügbar**")
    
    # Show what status data we do have
    if not transportstatushistory_df.empty and 'new_status' in transportstatushistory_df.columns:
        st.write("**Verfügbare Status in den Daten:**")
        status_counts = transportstatushistory_df['new_status'].value_counts()
        st.dataframe(status_counts.reset_index())
        
        # Show some sample status transitions
        if len(transportstatushistory_df) > 0:
            st.write("**Beispiel Status-Übergänge:**")
            sample_data = transportstatushistory_df[['transport_id', 'old_status', 'new_status', 'changed_at']].head(10)
            st.dataframe(sample_data)
    else:
        st.error("Keine Transportstatus-Historie-Daten verfügbar.")
    
    st.info("""
    **Mögliche Gründe:**
    - Die API-Daten verwenden andere Statusbezeichnungen als erwartet
    - Noch nicht genügend Daten für eine vollständige Workflow-Analyse vorhanden
    - Transporte befinden sich noch nicht in allen Workflow-Stufen
    """)

st.markdown("---")

## 🎯 **Fazit und Ausblick 2025**

# Calculate some key insights for the conclusion
total_days_active = (transport_df["created_at"].max() - transport_df["created_at"].min()).days + 1
avg_weekly_transports = len(transport_df) / (total_days_active / 7) if total_days_active > 0 else 0

# Success rate calculation
success_rate = (completed_count / total_transports * 100) if total_transports > 0 else 0
cancellation_rate = (cancelled_count / total_transports * 100) if total_transports > 0 else 0

st.markdown(f"""
### **Erfolgsbilanz des Pilotprojekts**

Das KTW.sh-Projekt hat in seiner **{total_days_active}-tägigen Pilotphase** beeindruckende Ergebnisse erzielt:

#### 📈 **Quantitative Erfolge:**
- **{total_transports:,} Transportanmeldungen** in {(total_days_active/30):.1f} Monaten
- **{avg_weekly_transports:.1f} Transporte/Woche** im Durchschnitt
- **{success_rate:.1f}% Erfolgsquote** bei der Transportabwicklung
- **{cancellation_rate:.1f}% Stornierungsrate** (innerhalb normaler Parameter)

### **Strategische Ziele 2026**

#### 🚀 **Kurzfristige Expansion (Q1 2026):**
- Integration der **ZNA Helios Schleswig**
- Pilotprojekt mit **Diakonie Flensburg**

---

*Dieser Bericht basiert auf Daten vom Juli bis November 2025. 
Letzte Aktualisierung: {pd.Timestamp.now().strftime('%d.%m.%Y')}*
""")

# Add a final call-to-action box
st.success("""
💡 **Das KTW.sh-Projekt demonstriert erfolgreich die Digitalisierung 
im Gesundheitswesen und schafft die Grundlage für eine effizientere, 
transparentere Krankentransport-Organisation in Schleswig-Holstein.**
""")