"""Incident analytics dashboard: streamlit run app.py"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Incident insights', page_icon='⛰️', layout='wide')
st.markdown('''<style>
.block-container {padding-top: 2rem; max-width: 1350px}
h1, h2, h3 {letter-spacing: -.025em}
[data-testid="stMetric"] {background: #f3f7f7; border: 1px solid #dde9e7; border-radius: 12px; padding: 12px 18px}
</style>''', unsafe_allow_html=True)
COLORS = ['#176b74','#dc8741','#775b95','#78a4a2','#b25e61','#8d9d4f','#425e7f']

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=['activity_start_date'])

@st.cache_data
def load_locations(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={'place':'string'})


def bar(data: pd.DataFrame, column: str, label: str):
    counts = data[column].fillna('Unknown').value_counts().rename_axis(column).reset_index(name='Reports')
    counts = counts.sort_values('Reports')
    fig = px.bar(counts, x='Reports', y=column, orientation='h', labels={column:label}, color_discrete_sequence=[COLORS[0]])
    fig.update_layout(height=max(280, 45 * len(counts) + 70), margin=dict(l=0,r=12,t=8,b=0), showlegend=False)
    return fig

st.title('Incident insights')
st.caption('Submitted reports by activity start date · Counts are not exposure-adjusted risk rates')
source_path = ROOT / 'data' / 'incidents_clean.csv'
location_path = ROOT / 'data' / 'locations.csv'
if not source_path.exists() or not location_path.exists():
    st.error('Missing data files. See README.md for setup.')
    st.stop()
df = load_data(source_path)
locations = load_locations(location_path)
if locations.place.duplicated().any():
    st.error('data/locations.csv contains duplicate place values. Each place must appear once.')
    st.stop()
for col in ['latitude','longitude']:
    locations[col] = pd.to_numeric(locations[col], errors='coerce')
invalid = locations[(locations.latitude.notna() ^ locations.longitude.notna()) |
                    (locations.latitude.notna() & ~locations.latitude.between(-90,90)) |
                    (locations.longitude.notna() & ~locations.longitude.between(-180,180))]
if len(invalid):
    st.warning(f'{len(invalid)} location rows have incomplete or invalid coordinates and will not be mapped.')
    locations.loc[invalid.index, ['latitude','longitude']] = float('nan')

with st.sidebar:
    st.header('Global filters')
    branches = sorted(df.branch.dropna().unique().tolist())
    types = sorted(df.incident_type.dropna().unique().tolist())
    severities = sorted(df.severity.dropna().unique().tolist())
    selected_branches = st.multiselect('Branch', branches, default=branches)
    selected_types = st.multiselect('Incident type', types, default=types,
                                    help='What happened, from the source Incident Category field.')
    selected_severities = st.multiselect('Severity', severities, default=severities,
                                         help='Source Incident Type field, including Near Miss and Safety Concern.')
    years = sorted(df.year.dropna().astype(int).unique().tolist())
    selected_years = st.multiselect('Activity start year', years, default=years)
    if st.button('Reset filters', use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.caption('All filters apply to every chart and the map.')

view = df[df.branch.isin(selected_branches) & df.incident_type.isin(selected_types) &
          df.severity.isin(selected_severities) & df.year.isin(selected_years)].copy()
if view.empty:
    st.info('No reports match the current filters. Adjust the selections on the left.')
    st.stop()

m1,m2,m3,m4 = st.columns(4)
m1.metric('Reports', f'{len(view):,}')
m2.metric('Everett reports', f'{view.branch.eq("Everett").sum():,}')
m3.metric('Branches', view.branch.nunique())
m4.metric('Named places', view.place.nunique())

overview, everett_tab, map_tab, data_tab = st.tabs(['Overview', 'Everett', 'Map', 'Data & definitions'])
with overview:
    left,right = st.columns(2)
    with left:
        st.subheader('Reports by incident type')
        st.plotly_chart(bar(view,'incident_type','Incident type'), use_container_width=True)
    with right:
        st.subheader('Reports by branch')
        st.plotly_chart(bar(view,'branch','Branch'), use_container_width=True)
    st.subheader('Branch × incident type')
    matrix = pd.crosstab(view.branch, view.incident_type).reindex(index=selected_branches, columns=selected_types, fill_value=0)
    fig = px.imshow(matrix, text_auto=True, aspect='auto', color_continuous_scale='Teal',
                    labels={'x':'Incident type','y':'Branch','color':'Reports'})
    fig.update_layout(height=max(360, 43 * len(matrix) + 100), margin=dict(l=0,r=0,t=15,b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.subheader('Annual trend')
    annual = view.groupby('year').size().reindex(selected_years,fill_value=0)
    everett = view[view.branch.eq('Everett')].groupby('year').size().reindex(selected_years,fill_value=0)
    trend = pd.DataFrame({'Year':selected_years,'Selected branches':annual.to_numpy(),'Everett':everett.to_numpy()})
    long = trend.melt('Year',var_name='Series',value_name='Reports')
    fig = px.line(long,x='Year',y='Reports',color='Series',markers=True,
                  color_discrete_map={'Selected branches':COLORS[0],'Everett':COLORS[1]})
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), xaxis=dict(dtick=1))
    st.plotly_chart(fig,use_container_width=True)
    st.caption('The selected-branches series includes Everett when selected. 2026 is partial; 2005 and 2018 contain isolated reports.')

with everett_tab:
    ev = view[view.branch.eq('Everett')]
    if ev.empty:
        st.info('Select Everett in the Branch filter to see this view.')
    else:
        a,b = st.columns(2)
        with a:
            st.subheader('Incident type')
            st.plotly_chart(bar(ev,'incident_type','Incident type'),use_container_width=True)
        with b:
            st.subheader('Severity')
            st.plotly_chart(bar(ev,'severity','Severity'),use_container_width=True)
        st.subheader('Activities')
        st.plotly_chart(bar(ev,'activity_type','Activity'),use_container_width=True)

with map_tab:
    st.subheader('Reported activity places')
    st.caption('Markers represent the named activity place, not a verified incident point. City and multi-route labels can be very broad.')
    geo = view.merge(locations, on='place', how='left', validate='many_to_one')
    mapped = geo.dropna(subset=['latitude','longitude']).copy()
    st.info(f'{len(mapped):,} of {len(view):,} filtered reports have representative coordinates at {mapped.place.nunique()} named places.')
    if len(mapped):
        grouped = mapped.groupby(['place','latitude','longitude'],as_index=False).agg(
            Reports=('report_id','size'),
            types=('incident_type',lambda s:', '.join(f'{k}: {v}' for k,v in s.value_counts().items())),
            severities=('severity',lambda s:', '.join(f'{k}: {v}' for k,v in s.value_counts().items())),
            leading_type=('incident_type',lambda s:s.value_counts().index[0]))
        fig = px.scatter_mapbox(grouped,lat='latitude',lon='longitude',color='leading_type',size='Reports',
                                hover_name='place',hover_data={'Reports':True,'types':True,'severities':True,
                                                                'latitude':False,'longitude':False},
                                color_discrete_sequence=COLORS,zoom=5,height=600,
                                labels={'leading_type':'Most common type','types':'Type counts','severities':'Severity counts'})
        fig.update_layout(mapbox_style='open-street-map', margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)
    with st.expander('Places still needing coordinates'):
        missing = geo[geo.latitude.isna() | geo.longitude.isna()].groupby('place',dropna=False).size().reset_index(name='Reports')
        st.dataframe(missing.sort_values('Reports',ascending=False),hide_index=True,use_container_width=True)
    st.caption('Edit data/locations.csv to improve coverage. Add both latitude and longitude, a precision note, and a source link; then save and refresh.')

with data_tab:
    st.subheader('Definitions')
    st.markdown('**Incident type** = source `Incident Category` (for example, slip/trip/fall). **Severity** = source `Incident Type` (Minor, Near Miss, Significant, etc.). The source labels Near Miss and Safety Concern are retained here, not forced into a severity rank.')
    st.markdown('Each row is one submitted report after exact duplicate removal. Annual counts use activity start date because there is no incident occurrence date. Counts cannot be compared as rates without activity or participant exposure data.')
    st.download_button('Download filtered, de-identified reports',view.to_csv(index=False).encode('utf-8'),
                       'filtered_incidents.csv','text/csv')
