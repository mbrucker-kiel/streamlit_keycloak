


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from data_loading import data_loading

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
        st.login(
    
    st.stop()  # Stop execution of the rest of the page

st.set_page_config(
    page_title="S-KTW Jahresbericht 2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Details data
details_df = data_loading("Details", limit=15000)

# Header section with improved styling
st.title("🚑 S-KTW Jahresbericht 2025")
st.markdown("---")

# Executive Summary
st.markdown("""
## 📋 **Zusammenfassung**

Dieser Jahresbericht analysiert die Einsatzdaten der **Sofort Krankentransportwagen (S-KTW)** 
für das Jahr 2025. Die S-KTW-Flotte stellt eine zentrale Säule der präklinischen Notfallversorgung.

### **Analysierte Fahrzeuge:**
""")

# Selected vehicles with updated IDs
selected_vehicles = ["10-85-11", "11-85-11", "20-85-11",  "12-85-15"]

# Display selected vehicles in a nice format
cols = st.columns(len(selected_vehicles))
for i, vehicle in enumerate(selected_vehicles):
    with cols[i]:
        st.info(f"🚐 **{vehicle}**")


# Filter for selected vehicles
if 'content_callSign' in details_df.columns:
    selected_df = details_df[details_df['content_callSign'].isin(selected_vehicles)]
else:
    st.warning("Spalte 'content_callSign' nicht gefunden. Verfügbare Spalten:")
    st.write(details_df.columns.tolist())
    selected_df = pd.DataFrame()

## 📊 **Kernkennzahlen der S-KTW-Flotte**

if not selected_df.empty:
    # Calculate key metrics
    total_missions = len(selected_df)
    unique_days = selected_df['content_dateStatus1'].nunique() if 'content_dateStatus1' in selected_df.columns else 1
    avg_daily_missions = total_missions / unique_days if unique_days > 0 else 0
    
    # Calculate total fleet hours (sum of all vehicle working hours)
    total_fleet_hours = 0
    vehicle_stats = []
    
    for vehicle in selected_vehicles:
        vehicle_data = selected_df[selected_df['content_callSign'] == vehicle]
        vehicle_missions = len(vehicle_data)
        vehicle_stats.append({
            'Fahrzeug': vehicle,
            'Einsätze': vehicle_missions,
            'Anteil (%)': (vehicle_missions / total_missions * 100) if total_missions > 0 else 0
        })
    
    # Display main KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚑 Gesamte Einsätze",
            value=f"{total_missions:,}",
            help="Alle registrierten Einsätze der S-KTW-Flotte"
        )
    
    with col2:
        st.metric(
            label="📅 Aktive Tage",
            value=f"{unique_days:,}",
            help="Anzahl Tage mit registrierten Einsätzen"
        )
    
    with col3:
        st.metric(
            label="📈 Ø Tägliche Einsätze",
            value=f"{avg_daily_missions:.1f}",
            help="Durchschnittliche Einsätze pro Tag"
        )
    

    st.markdown("---")
    
    ### **Fahrzeugspezifische Leistungsübersicht**
    
    # Total transports per vehicle
    transport_stats = selected_df['content_callSign'].value_counts().reset_index()
    transport_stats.columns = ['Fahrzeug', 'Gesamt Transporte']
    
    # Calculate time working between StatusAlarm and StatusEnd
    time_working_stats = []
    
    for vehicle in selected_vehicles:
        vehicle_data = selected_df[selected_df['content_callSign'] == vehicle]
        
        # Try to calculate time difference using Status1 and StatusEnd
        total_working_time = 0
        
        # Check if we have the datetime columns for Status1 and StatusEnd
        if ('content_dateStatus1' in details_df.columns and 'content_timeStatus1' in details_df.columns and
            'content_dateStatusEnd' in details_df.columns and 'content_timeStatusEnd' in details_df.columns):
            
            vehicle_data_copy = vehicle_data.copy()
            
            # Combine date and time for Status1 (start time)
            vehicle_data_copy['status1_datetime'] = pd.to_datetime(
                vehicle_data_copy['content_dateStatus1'].astype(str) + ' ' + 
                vehicle_data_copy['content_timeStatus1'].astype(str), 
                errors='coerce'
            )
            
            # Combine date and time for StatusEnd
            vehicle_data_copy['statusend_datetime'] = pd.to_datetime(
                vehicle_data_copy['content_dateStatusEnd'].astype(str) + ' ' + 
                vehicle_data_copy['content_timeStatusEnd'].astype(str), 
                errors='coerce'
            )
            
            # Calculate time differences where both timestamps are valid
            valid_times = (vehicle_data_copy['status1_datetime'].notna() & 
                          vehicle_data_copy['statusend_datetime'].notna())
            
            if valid_times.any():
                time_diffs = (vehicle_data_copy.loc[valid_times, 'statusend_datetime'] - 
                             vehicle_data_copy.loc[valid_times, 'status1_datetime']).dt.total_seconds() / 3600
                total_working_time = time_diffs.sum()
        
        # Fallback: try using StatusAlarm column if it exists as datetime
        elif 'StatusAlarm' in details_df.columns and 'StatusEnd' in details_df.columns:
            vehicle_data_copy = vehicle_data.copy()
            vehicle_data_copy['StatusAlarm'] = pd.to_datetime(vehicle_data_copy['StatusAlarm'], errors='coerce')
            vehicle_data_copy['StatusEnd'] = pd.to_datetime(vehicle_data_copy['StatusEnd'], errors='coerce')
            
            valid_times = (vehicle_data_copy['StatusAlarm'].notna() & 
                          vehicle_data_copy['StatusEnd'].notna())
            
            if valid_times.any():
                time_diffs = (vehicle_data_copy.loc[valid_times, 'StatusEnd'] - 
                             vehicle_data_copy.loc[valid_times, 'StatusAlarm']).dt.total_seconds() / 3600
                total_working_time = time_diffs.sum()
        
        time_working_stats.append({
            'Fahrzeug': vehicle,
            'Gesamt Einsatzstunden': round(total_working_time, 2) if total_working_time > 0 else 'N/A'
        })
    
    # Merge statistics
    stats_df = transport_stats.merge(pd.DataFrame(time_working_stats), on='Fahrzeug', how='left')
    st.dataframe(stats_df)

    # Add collapsed detail field for individual vehicle analysis
    with st.expander("🔍 Detaillierte S-KTW Fahrzeug-Analyse", expanded=False):
        st.markdown("### Einzelfahrzeug-Statistiken")
        
        # Find date column for charts
        chart_date_col = None
        for col in details_df.columns:
            if 'content_dateStatus1' in col:
                chart_date_col = col
                break
            elif 'date' in col.lower() and 'alarm' in col.lower():
                chart_date_col = col
                break
            elif 'date' in col.lower():
                chart_date_col = col
        
        
        for vehicle in selected_vehicles:
            vehicle_data = selected_df[selected_df['content_callSign'] == vehicle]
            
            if not vehicle_data.empty:
                st.markdown(f"#### 🚐 **{vehicle}**")
                
                # Create columns for metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    vehicle_missions = len(vehicle_data)
                    st.metric("Einsätze", f"{vehicle_missions:,}")
                
                with col2:
                    # Calculate percentage of total fleet missions
                    percentage = (vehicle_missions / total_missions * 100) if total_missions > 0 else 0
                    st.metric("Flotten-Anteil", f"{percentage:.1f}%")
                
                with col3:
                    # Active days for this vehicle
                    if 'content_dateStatus1' in vehicle_data.columns:
                        vehicle_active_days = vehicle_data['content_dateStatus1'].nunique()
                        st.metric("Aktive Tage", f"{vehicle_active_days}")
                    else:
                        st.metric("Aktive Tage", "N/A")
                
                with col4:
                    # Average missions per active day
                    if 'content_dateStatus1' in vehicle_data.columns:
                        vehicle_active_days = vehicle_data['content_dateStatus1'].nunique()
                        avg_per_day = vehicle_missions / vehicle_active_days if vehicle_active_days > 0 else 0
                        st.metric("Ø Einsätze/Tag", f"{avg_per_day:.1f}")
                    else:
                        st.metric("Ø Einsätze/Tag", "N/A")
                
                # Mission type distribution for this vehicle
                if 'content_missionType' in vehicle_data.columns:
                    mission_types = vehicle_data['content_missionType'].value_counts()
                    if not mission_types.empty:
                        st.write("**Top Einsatztypen:**")
                        for mission_type, count in mission_types.head(3).items():
                            percentage = (count / vehicle_missions * 100) if vehicle_missions > 0 else 0
                            st.write(f"- {mission_type}: {count} ({percentage:.1f}%)")
                
                # Time analysis if possible
                if ('content_dateStatus1' in vehicle_data.columns and 
                    'content_timeStatus1' in vehicle_data.columns and
                    'content_dateStatusEnd' in vehicle_data.columns and 
                    'content_timeStatusEnd' in vehicle_data.columns):
                    
                    vehicle_time_data = vehicle_data.copy()
                    
                    # Create datetime columns
                    vehicle_time_data['start_datetime'] = pd.to_datetime(
                        vehicle_time_data['content_dateStatus1'].astype(str) + ' ' + 
                        vehicle_time_data['content_timeStatus1'].astype(str), 
                        errors='coerce'
                    )
                    
                    vehicle_time_data['end_datetime'] = pd.to_datetime(
                        vehicle_time_data['content_dateStatusEnd'].astype(str) + ' ' + 
                        vehicle_time_data['content_timeStatusEnd'].astype(str), 
                        errors='coerce'
                    )
                    
                    # Calculate mission durations
                    valid_durations = (vehicle_time_data['start_datetime'].notna() & 
                                     vehicle_time_data['end_datetime'].notna())
                    
                    if valid_durations.any():
                        durations = (vehicle_time_data.loc[valid_durations, 'end_datetime'] - 
                                   vehicle_time_data.loc[valid_durations, 'start_datetime']).dt.total_seconds() / 60
                        
                        avg_duration = durations.mean()
                        total_hours = durations.sum() / 60
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Ø Einsatzdauer:** {avg_duration:.1f} Min")
                        with col2:
                            st.write(f"**Gesamt Einsatzzeit:** {total_hours:.1f} Std")
                
                st.markdown("---")
            else:
                st.warning(f"Keine Daten für Fahrzeug {vehicle} gefunden")

# 2. Calculate transports where Status1 is filled but not Status2
st.write("### Alarm Analyse")

# Add total Einsätze from the selected vehicles
total_selected_missions = len(selected_df)
st.metric("Gesamt Einsätze der ausgewählten S-KTW Fahrzeuge", total_selected_missions)

status1_col = None
status2_col = None

# Look for Status1 and Status2 columns
for col in details_df.columns:
    if 'Status1' in col or 'status1' in col.lower():
        status1_col = col
    elif 'Status2' in col or 'status2' in col.lower():
        status2_col = col

if status1_col and status2_col:
    # Filter: Status1 filled but Status2 not filled - only for selected vehicles
    status1_filled = selected_df[status1_col].notna() & (selected_df[status1_col] != '')
    status2_not_filled = selected_df[status2_col].isna() | (selected_df[status2_col] == '')
    
    alerted_but_not_status2_selected = selected_df[status1_filled & status2_not_filled]
    
    st.metric("Anzahl S-KTW: Alarmiert aus Status1 aber nicht Status2", len(alerted_but_not_status2_selected))

    # hi i want to add a calculation metric to calculate the time between status 2 and the next status alarm for each vehicle inside StatusAlarm


else:
    st.warning("Status1 oder Status2 Spalten nicht gefunden. Verfügbare Spalten:")
    st.write([col for col in details_df.columns if 'status' in col.lower()])

# 3. Einsatzaufkommen über Zeit - Vergleich
st.write("### Einsatzaufkommen über Zeit - Vergleich")

# Find date column
date_col = None
for col in details_df.columns:
    if 'content_dateStatus1' in col:
        date_col = col
        break
    elif 'date' in col.lower() and 'alarm' in col.lower():
        date_col = col
        break
    elif 'date' in col.lower():
        date_col = col

if 'content_callSign' in details_df.columns and date_col:
    # Filter vehicles with -83- pattern
    vehicles_83 = details_df[details_df['content_callSign'].str.contains('-83-', na=False)]
    
    # Filter vehicles with -85- pattern  
    vehicles_85 = details_df[details_df['content_callSign'].str.contains('-85-', na=False)]
    
    # Filter -85- vehicles excluding selected vehicles (S-KTW)
    vehicles_85_excluding_selected = vehicles_85[~vehicles_85['content_callSign'].isin(selected_vehicles)]
    
    # Prepare data for all three groups
    details_df_copy = details_df.copy()
    details_df_copy[date_col] = pd.to_datetime(details_df_copy[date_col], errors='coerce')
    details_df_copy = details_df_copy.dropna(subset=[date_col])
    
    # Group by date for each vehicle type
    daily_83 = vehicles_83.copy()
    daily_83[date_col] = pd.to_datetime(daily_83[date_col], errors='coerce')
    daily_83 = daily_83.dropna(subset=[date_col])
    daily_83_counts = daily_83.groupby(daily_83[date_col].dt.date).size().reset_index()
    daily_83_counts.columns = ['Datum', 'Anzahl']
    daily_83_counts['Typ'] = 'Fahrzeuge mit **-83-**'
    
    daily_selected = selected_df.copy()
    daily_selected[date_col] = pd.to_datetime(daily_selected[date_col], errors='coerce')
    daily_selected = daily_selected.dropna(subset=[date_col])
    daily_selected_counts = daily_selected.groupby(daily_selected[date_col].dt.date).size().reset_index()
    daily_selected_counts.columns = ['Datum', 'Anzahl']
    daily_selected_counts['Typ'] = 'S-KTW Fahrzeuge'
    
    daily_85 = vehicles_85_excluding_selected.copy()
    daily_85[date_col] = pd.to_datetime(daily_85[date_col], errors='coerce')
    daily_85 = daily_85.dropna(subset=[date_col])
    daily_85_counts = daily_85.groupby(daily_85[date_col].dt.date).size().reset_index()
    daily_85_counts.columns = ['Datum', 'Anzahl']
    daily_85_counts['Typ'] = 'Fahrzeuge mit **-85-** ausgenommen S-KTW'
    
    # Combine all data
    all_daily_counts = pd.concat([daily_83_counts, daily_selected_counts, daily_85_counts], ignore_index=True)
    
    if not all_daily_counts.empty:
        # Find the maximum value across all datasets for consistent Y-axis scaling
        max_y_value = all_daily_counts['Anzahl'].max()
        
        fig_comparison = px.line(all_daily_counts, x='Datum', y='Anzahl', color='Typ',
                               title='Einsatzaufkommen über Zeit - Fahrzeugtyp Vergleich')
        
        # Set consistent Y-axis range for all lines
        fig_comparison.update_layout(
            yaxis=dict(range=[0, max_y_value * 1.05])  # Add 5% padding at top
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.warning("Keine gültigen Daten für die Zeitreihen-Vergleichsgrafik gefunden")

    # Add collapsed section for individual S-KTW vehicle comparison
    with st.expander("📊 Individuelle S-KTW Fahrzeug-Vergleich", expanded=False):
        st.markdown("### Vergleich der einzelnen S-KTW Fahrzeuge")
        
        if not selected_df.empty and date_col:
            # Prepare data for individual vehicle comparison
            individual_vehicle_data = []
            individual_max_value = 0
            
            for vehicle in selected_vehicles:
                vehicle_subset = selected_df[selected_df['content_callSign'] == vehicle].copy()
                
                if not vehicle_subset.empty:
                    # Create datetime column
                    if 'StatusAlarm' in vehicle_subset.columns:
                        vehicle_subset['alarm_datetime'] = pd.to_datetime(vehicle_subset['StatusAlarm'], errors='coerce')
                    elif date_col in vehicle_subset.columns:
                        vehicle_subset['alarm_datetime'] = pd.to_datetime(vehicle_subset[date_col], errors='coerce')
                    else:
                        continue
                    
                    # Remove invalid dates
                    vehicle_subset = vehicle_subset.dropna(subset=['alarm_datetime'])
                    
                    if not vehicle_subset.empty:
                        # Group by date and count missions
                        daily_vehicle_counts = vehicle_subset.groupby(
                            vehicle_subset['alarm_datetime'].dt.date
                        ).size().reset_index()
                        daily_vehicle_counts.columns = ['Datum', 'Anzahl']
                        daily_vehicle_counts['Fahrzeug'] = vehicle
                        daily_vehicle_counts['Datum'] = pd.to_datetime(daily_vehicle_counts['Datum'])
                        
                        individual_vehicle_data.append(daily_vehicle_counts)
                        
                        # Track maximum value for consistent Y-axis
                        if len(daily_vehicle_counts) > 0:
                            individual_max_value = max(individual_max_value, daily_vehicle_counts['Anzahl'].max())
            
            # Combine all individual vehicle data
            if individual_vehicle_data:
                all_individual_data = pd.concat(individual_vehicle_data, ignore_index=True)
                
                # Create comparison chart for individual vehicles
                fig_individual = px.line(
                    all_individual_data, 
                    x='Datum', 
                    y='Anzahl', 
                    color='Fahrzeug',
                    title='S-KTW Fahrzeuge - Individueller Vergleich',
                    markers=True
                )
                
                # Set consistent Y-axis and customize appearance
                fig_individual.update_layout(
                    yaxis=dict(range=[0, individual_max_value * 1.05]) if individual_max_value > 0 else {},
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                # Customize line appearance
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Distinct colors for each vehicle
                for i, trace in enumerate(fig_individual.data):
                    if i < len(colors):
                        trace.line.color = colors[i]
                        trace.marker.color = colors[i]
                
                st.plotly_chart(fig_individual, use_container_width=True, key="individual_vehicles_comparison")
                
                # Add summary statistics table
                st.markdown("#### Fahrzeug-Vergleichsstatistiken")
                
                # Calculate statistics for each vehicle
                vehicle_summary = []
                for vehicle in selected_vehicles:
                    vehicle_data_subset = all_individual_data[all_individual_data['Fahrzeug'] == vehicle]
                    if not vehicle_data_subset.empty:
                        total_days = len(vehicle_data_subset)
                        total_missions = vehicle_data_subset['Anzahl'].sum()
                        avg_daily = vehicle_data_subset['Anzahl'].mean()
                        max_daily = vehicle_data_subset['Anzahl'].max()
                        
                        vehicle_summary.append({
                            'Fahrzeug': vehicle,
                            'Gesamt Einsätze': total_missions,
                            'Aktive Tage': total_days,
                            'Ø Einsätze/Tag': round(avg_daily, 1),
                            'Max Einsätze/Tag': max_daily
                        })
                
                if vehicle_summary:
                    summary_df = pd.DataFrame(vehicle_summary)
                    st.dataframe(summary_df, use_container_width=True)
            else:
                st.warning("Keine Daten für individuellen Fahrzeugvergleich verfügbar")
        else:
            st.warning("Keine S-KTW Daten oder Datumsspalte für Fahrzeugvergleich verfügbar")
        
else:
    st.error("Erforderliche Spalten nicht gefunden für die Vergleichsgrafik")

# for each vehicle:
## calculate: zeit zwischen Status2 and next status alarm for each vehicle


# rtm_vorhaltung = data_loading("RTM_Vorhaltung")

# st.dataframe(rtm_vorhaltung)

## existing: auslastung in Prozent & Absolut mit vorhaltung

st.markdown("---")

## 🕐 **Zeitpunkt-Analyse der S-KTW-Einsätze**

st.markdown("""
Die folgende Heatmap visualisiert die Verteilung der S-KTW-Einsätze über 
Wochentage und Tageszeiten. Diese Analyse unterstützt die optimale 
Personalplanung und Ressourcenallokation.
""")

# Use selected_df for the hourly analysis
if not selected_df.empty:
    heatmap_df = selected_df.copy()

    # Check if StatusAlarm column exists, otherwise try to create it from Status1
    if "StatusAlarm" in heatmap_df.columns:
        alarm_col = "StatusAlarm"
        heatmap_df[alarm_col] = pd.to_datetime(heatmap_df[alarm_col], errors='coerce')
    elif 'content_dateStatus1' in heatmap_df.columns and 'content_timeStatus1' in heatmap_df.columns:
        # Create StatusAlarm from date and time columns
        alarm_col = "StatusAlarm"
        heatmap_df[alarm_col] = pd.to_datetime(
            heatmap_df['content_dateStatus1'].astype(str) + ' ' + 
            heatmap_df['content_timeStatus1'].astype(str), 
            errors='coerce'
        )
    else:
        st.warning("Keine geeignete Alarm-Zeit Spalte gefunden für Stundenintervall Analyse.")
        heatmap_df = pd.DataFrame()

    if alarm_col in heatmap_df.columns and not heatmap_df.empty:
        # Remove rows with invalid dates
        heatmap_df = heatmap_df.dropna(subset=[alarm_col])
        
        if not heatmap_df.empty:
            # Create German weekday names
            weekday_german = {
                0: "Montag",
                1: "Dienstag", 
                2: "Mittwoch",
                3: "Donnerstag",
                4: "Freitag",
                5: "Samstag",
                6: "Sonntag"
            }
            
            heatmap_df["weekday"] = heatmap_df[alarm_col].dt.dayofweek.map(weekday_german)
            heatmap_df["hour"] = heatmap_df[alarm_col].dt.hour
            
            heatmap_data = (
                heatmap_df.groupby(["weekday", "hour"]).size().reset_index(name="counts")
            )
            
            if not heatmap_data.empty:
                heatmap_data = heatmap_data.pivot(
                    index="weekday", columns="hour", values="counts"
                ).fillna(0)
                
                # Ensure all hours from 0 to 23 are included
                all_hours = list(range(24))
                heatmap_data = heatmap_data.reindex(columns=all_hours, fill_value=0)
                
                # Reorder weekdays (German names)
                weekdays_order = [
                    "Montag",
                    "Dienstag", 
                    "Mittwoch",
                    "Donnerstag",
                    "Freitag",
                    "Samstag",
                    "Sonntag",
                ]
                heatmap_data = heatmap_data.reindex(weekdays_order)
                
                # Create enhanced heatmap
                fig = px.imshow(
                    heatmap_data,
                    labels=dict(
                        x="Stunde des Tages", 
                        y="Wochentag", 
                        color="Anzahl Einsätze"
                    ),
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    title="S-KTW Einsätze nach Wochentag und Uhrzeit",
                    color_continuous_scale="RdYlBu_r",
                    aspect="auto"
                )
                
                fig.update_layout(
                    title_font_size=16,
                    xaxis_title="Uhrzeit (24h-Format)",
                    yaxis_title="Wochentag"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add insights about peak times
                col1, col2 = st.columns(2)
                
                with col1:
                    # Find peak hour
                    total_by_hour = heatmap_data.sum(axis=0)
                    peak_hour = total_by_hour.idxmax()
                    peak_count = total_by_hour.max()
                    
                    st.info(f"""
                    **🔥 Haupteinsatzzeit:** {peak_hour}:00 Uhr  
                    **Anzahl Einsätze:** {peak_count:.0f}
                    """)
                
                with col2:
                    # Find busiest day
                    total_by_day = heatmap_data.sum(axis=1)
                    busiest_day = total_by_day.idxmax()
                    busiest_count = total_by_day.max()
                    
                    st.info(f"""
                    **📅 Intensivster Wochentag:** {busiest_day}  
                    **Anzahl Einsätze:** {busiest_count:.0f}
                    """)
                
            else:
                st.warning("Keine Daten für Heatmap gefunden.")
        else:
            st.warning("Keine gültigen Alarm-Zeiten für Analyse gefunden.")
else:
    st.warning("Keine S-KTW Daten für Stundenintervall Analyse verfügbar.")


# Load holiday data
wochenfeiertage = data_loading("Feiertage", limit=100)

if not selected_df.empty and 'content_missionType' in selected_df.columns:
    # Create working dataframe with datetime
    mission_analysis_df = selected_df.copy()
    
    # Create datetime column for analysis
    if "StatusAlarm" in mission_analysis_df.columns:
        datetime_col = "StatusAlarm"
        mission_analysis_df[datetime_col] = pd.to_datetime(mission_analysis_df[datetime_col], errors='coerce')
    elif 'content_dateStatus1' in mission_analysis_df.columns and 'content_timeStatus1' in mission_analysis_df.columns:
        datetime_col = "mission_datetime"
        mission_analysis_df[datetime_col] = pd.to_datetime(
            mission_analysis_df['content_dateStatus1'].astype(str) + ' ' + 
            mission_analysis_df['content_timeStatus1'].astype(str), 
            errors='coerce'
        )
    else:
        st.warning("Keine geeignete Datum-Zeit Spalte für Mission Type Analyse gefunden.")
        mission_analysis_df = pd.DataFrame()
    
    if datetime_col in mission_analysis_df.columns and not mission_analysis_df.empty:
        # Remove invalid dates
        mission_analysis_df = mission_analysis_df.dropna(subset=[datetime_col])
        
        if not mission_analysis_df.empty:
            # Extract date information
            mission_analysis_df['date'] = mission_analysis_df[datetime_col].dt.date
            mission_analysis_df['weekday'] = mission_analysis_df[datetime_col].dt.day_name()
            
            # Create holiday date set for comparison
            holiday_dates = set()
            if not wochenfeiertage.empty and 'date' in wochenfeiertage.columns:
                holiday_dates = set(pd.to_datetime(wochenfeiertage['date'], errors='coerce').dt.date)
            
            # Function to classify weekday groups
            def classify_weekday_group(row):
                date_obj = row['date']
                weekday = row['weekday']
                
                # Check if it's a holiday first
                if date_obj in holiday_dates:
                    return 'Wochenfeiertag'
                elif weekday in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']:
                    return 'Mo-Do'
                elif weekday == 'Friday':
                    return 'Fr'
                elif weekday == 'Saturday':
                    return 'Sa'
                elif weekday == 'Sunday':
                    return 'So'
                else:
                    return 'Unbekannt'
            
            # Apply classification
            mission_analysis_df['weekday_group'] = mission_analysis_df.apply(classify_weekday_group, axis=1)
            
            # Handle empty mission types - replace empty strings with "Unbekannter Missionstyp"
            mission_analysis_df['content_missionType'] = mission_analysis_df['content_missionType'].fillna("Unbekannter Missionstyp")
            mission_analysis_df['content_missionType'] = mission_analysis_df['content_missionType'].replace("", "Unbekannter Missionstyp")
            
            # Get available mission types
            available_mission_types = sorted(mission_analysis_df['content_missionType'].unique())
            
            st.markdown("### 📊 Einsatztypen-Analyse")
                        
            # Create cross-tabulation
            mission_crosstab = pd.crosstab(
                mission_analysis_df['content_missionType'], 
                mission_analysis_df['weekday_group'], 
                margins=True
            )
            
            # Reorder columns in desired sequence
            desired_order = ['Mo-Do', 'Fr', 'Sa', 'So', 'Wochenfeiertag', 'All']
            available_cols = [col for col in desired_order if col in mission_crosstab.columns]
            mission_crosstab = mission_crosstab[available_cols]
            
            # Rename 'All' to 'Gesamt' for German users
            if 'All' in mission_crosstab.columns:
                mission_crosstab = mission_crosstab.rename(columns={'All': 'Gesamt'})
            
            st.write("#### Absolute Zahlen - Mission Types nach Wochentag-Gruppen")
            st.dataframe(mission_crosstab)
            
            # Calculate percentages
            mission_pct = pd.crosstab(
                mission_analysis_df['content_missionType'], 
                mission_analysis_df['weekday_group'], 
                normalize='columns'
            ) * 100
            
            # Reorder percentage table
            available_cols_pct = [col for col in desired_order[:-1] if col in mission_pct.columns]  # Exclude 'All'
            mission_pct = mission_pct[available_cols_pct]
            
            st.write("#### Prozentuale Verteilung - Mission Types nach Wochentag-Gruppen")
            st.dataframe(mission_pct.round(1).applymap(lambda x: f"{x:.1f}%"))
            
            # Create visualization - always show chart, but handle many types differently
            if len(available_mission_types) <= 15:  # Increased limit
                # Prepare data for plotting
                plot_data = []
                for mission_type in available_mission_types:
                    for weekday_group in available_cols_pct:
                        if mission_type in mission_crosstab.index and weekday_group in mission_crosstab.columns:
                            count = mission_crosstab.loc[mission_type, weekday_group]
                            plot_data.append({
                                'Mission Type': mission_type,
                                'Wochentag-Gruppe': weekday_group,
                                'Anzahl': count
                            })
                
                plot_df = pd.DataFrame(plot_data)
                
                if not plot_df.empty:
                    # Adjust chart height based on number of mission types
                    chart_height = min(600, max(400, len(available_mission_types) * 30))
                    
                    fig = px.bar(
                        plot_df, 
                        x='Wochentag-Gruppe', 
                        y='Anzahl', 
                        color='Mission Type',
                        title='Mission Types Verteilung nach Wochentag-Gruppen',
                        labels={'Wochentag-Gruppe': 'Wochentag-Gruppe', 'Anzahl': 'Anzahl Einsätze'}
                    )
                    
                    # Update layout for better readability with many mission types
                    fig.update_layout(
                        height=chart_height,
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=1,
                            xanchor="left",
                            x=1.02
                        ) if len(available_mission_types) > 8 else {}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Zu viele Mission Types ({len(available_mission_types)}) für Balkendiagramm.")
                
                # Create a heatmap instead for many mission types
                st.write("#### Alternative Visualisierung - Heatmap")
                
                # Prepare heatmap data (exclude Gesamt column for cleaner view)
                heatmap_data = mission_crosstab.copy()
                if 'Gesamt' in heatmap_data.columns:
                    heatmap_data = heatmap_data.drop('Gesamt', axis=1)
                
                fig_heatmap = px.imshow(
                    heatmap_data.values,
                    labels=dict(x="Wochentag-Gruppe", y="Mission Type", color="Anzahl"),
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    title=f"Mission Types Heatmap ({len(available_mission_types)} Typen)",
                    color_continuous_scale="Blues",
                    aspect="auto"
                )
                
                fig_heatmap.update_layout(
                    height=max(400, len(available_mission_types) * 20),
                    yaxis_title="Mission Type",
                    xaxis_title="Wochentag-Gruppe"
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Add collapsed section with detailed mission type breakdown
            with st.expander("📋 Detaillierte Mission Type Aufschlüsselung", expanded=False):
                st.markdown("### Einzelne Mission Types im Detail")
                
                # Sort mission types by total count (descending)
                mission_totals = mission_analysis_df['content_missionType'].value_counts()
                
                col1, col2 = st.columns(2)
                
                for i, (mission_type, total_count) in enumerate(mission_totals.items()):
                    with col1 if i % 2 == 0 else col2:
                        st.markdown(f"#### 🚐 {mission_type}")
                        
                        # Get data for this specific mission type
                        mission_data = mission_analysis_df[
                            mission_analysis_df['content_missionType'] == mission_type
                        ]
                        
                        # Calculate percentage of total missions
                        percentage = (total_count / len(mission_analysis_df) * 100)
                        
                        st.metric("Gesamt Einsätze", f"{total_count:,}", 
                                f"{percentage:.1f}% aller Einsätze")
                        
                        # Weekday distribution for this mission type
                        weekday_dist = mission_data['weekday_group'].value_counts()
                        
                        st.write("**Verteilung nach Wochentag-Gruppen:**")
                        for weekday, count in weekday_dist.items():
                            pct = (count / total_count * 100) if total_count > 0 else 0
                            st.write(f"- {weekday}: {count} ({pct:.1f}%)")
                        
                        st.markdown("---")
            
            # Summary statistics
            st.write("#### Zusammenfassung")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_missions = len(mission_analysis_df)
                st.metric("Gesamt analysierte Einsätze", total_missions)
            
            with col2:
                most_common_type = mission_analysis_df['content_missionType'].value_counts().index[0]
                st.metric("Häufigster Mission Type", most_common_type)
            
            with col3:
                busiest_group = mission_analysis_df['weekday_group'].value_counts().index[0]
                st.metric("Aktivste Wochentag-Gruppe", busiest_group)
                
        else:
            st.warning("Keine gültigen Daten nach Datums-Bereinigung gefunden.")
    else:
        st.warning("Datetime-Spalte konnte nicht erstellt werden.")
else:
    if selected_df.empty:
        st.warning("Keine S-KTW Daten für Mission Type Analyse verfügbar.")
    else:
        st.warning("Spalte 'content_missionType' nicht in den Daten gefunden.")
        st.write("Verfügbare Spalten:", selected_df.columns.tolist())

st.markdown("---")

## 🎯 **Fazit und Jahresauswertung 2025**

# Calculate comprehensive year-end statistics
if not selected_df.empty:
    # Time-based analysis
    if 'content_dateStatus1' in selected_df.columns:
        selected_df_with_date = selected_df.copy()
        selected_df_with_date['content_dateStatus1'] = pd.to_datetime(
            selected_df_with_date['content_dateStatus1'], errors='coerce'
        )
        selected_df_with_date = selected_df_with_date.dropna(subset=['content_dateStatus1'])
        
        if not selected_df_with_date.empty:
            start_date = selected_df_with_date['content_dateStatus1'].min()
            end_date = selected_df_with_date['content_dateStatus1'].max()
            analysis_period_days = (end_date - start_date).days + 1
            
            # Monthly mission distribution
            monthly_stats = selected_df_with_date.groupby(
                selected_df_with_date['content_dateStatus1'].dt.to_period('M')
            ).size()
            
            peak_month = monthly_stats.idxmax() if len(monthly_stats) > 0 else "N/A"
            peak_month_missions = monthly_stats.max() if len(monthly_stats) > 0 else 0

st.markdown(f"""
### **Jahresbilanz der S-KTW-Flotte**

#### 📈 **Leistungskennzahlen:**
- **Gesamteinsätze 2025:** {total_missions:,} Einsätze
- **Analysezeitraum:** {analysis_period_days if 'analysis_period_days' in locals() else 'N/A'} Tage
- **Durchschnittliche Tagesleistung:** {avg_daily_missions:.1f} Einsätze/Tag
- **Spitzenmonat:** {peak_month if 'peak_month' in locals() else 'N/A'} ({peak_month_missions if 'peak_month_missions' in locals() else 0} Einsätze)



### **Ausblick 2026**

Die S-KTW-Flotte hat 2025 ihre zentrale Rolle in der präklinischen Notfallversorgung 
erfolgreich erfüllt. Die kontinuierliche Datenerfassung und -analyse bildet die 
Grundlage für weitere Optimierungen und gewährleistet eine bedarfsgerechte, 
qualitativ hochwertige Patientenversorgung.

---

*Dieser Bericht basiert auf Einsatzdaten der S-KTW-Flotte für das Jahr 2025.  
Letzte Aktualisierung: {pd.Timestamp.now().strftime('%d.%m.%Y')}*
""")

# Add final success message
st.success("""
🏆 **Die S-KTW-Flotte gewährleistet als Rückgrat der Notfallversorgung eine 
zuverlässige, schnelle und qualitativ hochwertige Patientenbetreuung im gesamten 
Versorgungsgebiet. Die systematische Datenauswertung unterstützt kontinuierliche 
Verbesserungen und Effizienzsteigerungen.**
""")