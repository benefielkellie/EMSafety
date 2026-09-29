"""Interactive incident dashboard. Run: streamlit run app.py"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Incident reports', layout='wide')
st.title('Incident reports')
st.caption('Counts of submitted reports by activity start date. Counts are not exposure-adjusted incident rates.')

@st.cache_data
def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=['activity_start_date'])
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
    return df

path = Path(__file__).with_name('incidents_clean.csv')
if not path.exists():
    st.error('Missing incidents_clean.csv. Run prepare_data.py first.')
    st.stop()
df = load(str(path))
years = sorted(df.year.dropna().astype(int).unique().tolist())
branches = sorted(df.branch.fillna('Unknown').unique().tolist())
types = sorted(df.incident_type.fillna('Unknown').unique().tolist())
with st.sidebar:
    st.header('Filters')
    chosen_years = st.multiselect('Years', years, placeholder='All years')
    chosen_branches = st.multiselect('Branches', branches, placeholder='All branches')
    chosen_types = st.multiselect('Incident types', types, placeholder='All incident types')
    st.caption('Leave a filter blank to include all values. Selections apply across the dashboard.')
active_years = chosen_years or years
active_branches = chosen_branches or branches
active_types = chosen_types or types
view = df[df.year.isin(active_years) & df.branch.isin(active_branches) & df.incident_type.isin(active_types)].copy()
a, b, c = st.columns(3)
a.metric('Reports', f'{len(view):,}')
b.metric('Everett reports', f'{(view.branch == "Everett").sum():,}')
c.metric('Years with reports', view.year.nunique())

left, right = st.columns(2)
with left:
    counts = view.groupby('incident_type', as_index=False).size().rename(columns={'size':'reports'}).sort_values('reports')
    st.subheader('Incidents by type')
    st.plotly_chart(px.bar(counts, x='reports', y='incident_type', orientation='h', labels={'incident_type':'Incident type', 'reports':'Reports'}), use_container_width=True)
with right:
    counts = view.groupby('branch', as_index=False).size().rename(columns={'size':'reports'}).sort_values('reports')
    st.subheader('Incidents by branch')
    st.plotly_chart(px.bar(counts, x='reports', y='branch', orientation='h', labels={'branch':'Branch', 'reports':'Reports'}), use_container_width=True)

st.subheader('Branch × incident type')
matrix = pd.crosstab(view.branch, view.incident_type).reindex(index=active_branches, columns=active_types, fill_value=0)
if matrix.empty or not len(active_types):
    st.info('Select at least one branch and incident type.')
else:
    st.plotly_chart(px.imshow(matrix, text_auto=True, aspect='auto', color_continuous_scale='Blues', labels={'x':'Incident type','y':'Branch','color':'Reports'}), use_container_width=True)
    with st.expander('View counts as a table'):
        st.dataframe(matrix, use_container_width=True)

st.subheader('Annual trends: all selected branches and Everett')
# Reindex to show zero-report years within the selected range; no interpolation.
annual = view.groupby('year').size().reindex(active_years, fill_value=0)
everett = view[view.branch == 'Everett'].groupby('year').size().reindex(active_years, fill_value=0)
trend = pd.DataFrame({'year':active_years, 'All selected branches':annual.to_numpy(), 'Everett':everett.to_numpy()})
long = trend.melt('year', var_name='Series', value_name='Reports')
st.plotly_chart(px.line(long, x='year', y='Reports', color='Series', markers=True, category_orders={'year':active_years}), use_container_width=True)
st.caption('The all-branches series includes Everett when selected. 2026 is a partial year. Earlier isolated records (2005 and 2018) are retained; use the year filter to focus on 2019 onward.')
with st.expander('Annual counts'):
    st.dataframe(trend, hide_index=True, use_container_width=True)
st.download_button('Download filtered records (de-identified)', view.to_csv(index=False).encode('utf-8'), 'filtered_incidents.csv', 'text/csv')

st.divider()
st.header('Everett detail')
ev = view[view.branch == 'Everett'].copy()
if ev.empty:
    st.info('Select Everett in the branch filter to explore its reports.')
else:
    a, b = st.columns(2)
    with a:
        st.subheader('Incident mechanisms')
        mech = ev.groupby('incident_category', as_index=False).size().rename(columns={'size':'reports'}).sort_values('reports')
        st.plotly_chart(px.bar(mech, x='reports', y='incident_category', orientation='h', labels={'incident_category':'Incident category', 'reports':'Reports'}), use_container_width=True)
    with b:
        st.subheader('Activities')
        activities = ev.groupby('activity_type', as_index=False).size().rename(columns={'size':'reports'}).sort_values('reports')
        st.plotly_chart(px.bar(activities, x='reports', y='activity_type', orientation='h', labels={'activity_type':'Activity', 'reports':'Reports'}), use_container_width=True)

    st.subheader('Everett activity locations (approximate)')
    st.caption('Markers show representative places named in reports, not where incidents occurred. Multiple reports at a place share coordinates; broad and multi-place titles need manual review.')
    lookup_path = Path(__file__).with_name('everett_locations.csv')
    if lookup_path.exists():
        locations = pd.read_csv(lookup_path)
        geo = ev.merge(locations, on='place', how='left')
        mapped = geo.dropna(subset=['latitude','longitude']).copy()
        st.caption(f'{len(mapped)} of {len(ev)} selected Everett reports have reviewed representative coordinates across {mapped.place.nunique()} place names.')
        if len(mapped):
            grouped = mapped.groupby(['place','latitude','longitude'], as_index=False).agg(
                reports=('report_id','size'),
                types=('incident_type', lambda s: ', '.join(f'{k}: {v}' for k, v in s.value_counts().items())),
                leading_type=('incident_type', lambda s: s.value_counts().index[0]))
            fig = px.scatter_mapbox(grouped, lat='latitude', lon='longitude', color='leading_type', size='reports',
                                 hover_name='place', hover_data={'reports':True,'types':True,'latitude':False,'longitude':False},
                                 zoom=5, center={'lat':48.0,'lon':-121.8}, height=570,
                                 labels={'leading_type':'Most common type','reports':'Reports','types':'Type counts'})
            fig.update_layout(mapbox_style='open-street-map', margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with st.expander('Locations needing review'):
            missing = geo[geo.latitude.isna()].groupby('place', dropna=False).size().reset_index(name='reports').sort_values('reports', ascending=False)
            st.dataframe(missing, hide_index=True, use_container_width=True)
    else:
        st.info('Add everett_locations.csv to enable the map.')
