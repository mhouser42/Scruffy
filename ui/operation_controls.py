import streamlit as st
from config import CONFIG
from utils.general import create_zip_of_all_versions
from ui.views import ComponentRegistry
import pandas as pd


def sync_dataframe_versions():
    selected_version = st.session_state.get('selected_version')
    if selected_version and selected_version in st.session_state.get('dataframe_versions', {}):
        st.session_state['df'] = st.session_state['dataframe_versions'][selected_version].copy(deep=True)
        if 'scruffy' in st.session_state:
            st.session_state['scruffy'].curr_df = st.session_state['df'].copy(deep=True)
        st.rerun()


def create_action_button(label, key=None):
    return st.button(label=label, key=key)


def create_download_button(label, data, file_name, mime, key=None):
    return st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime,
        key=key
    )


def remove_versions(versions_to_remove, cannot_remove_message, last_version_message):
    versions = list(st.session_state['dataframe_versions'].keys())
    if len(versions) > 1:
        original_version = versions[0]
        for version in versions_to_remove:
            if version == original_version:
                st.warning(cannot_remove_message)
                return
            del st.session_state['dataframe_versions'][version]
        st.session_state['selected_version'] = original_version
        sync_dataframe_versions()
    else:
        st.warning(last_version_message)


def render_file_selection():
    versions = list(st.session_state['dataframe_versions'].keys())
    selected_version = st.selectbox(
        'Choose file version:',
        options=versions,
        key='df_version_selector',
        index=versions.index(st.session_state['selected_version'])
    )

    if selected_version != st.session_state['selected_version']:
        st.session_state['selected_version'] = selected_version
        scruffy = st.session_state['scruffy']
        scruffy._update_system_prompt()
        sync_dataframe_versions()

    return selected_version


def render_file_info(selected_df):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('#### Columns/Data Types:')
        st.write(selected_df.dtypes)
        st.write(f'Shape: {selected_df.shape}')
    with col2:
        render_versioning_buttons()


def render_versioning_buttons():
    st.markdown('#### Version Options:')

    selected_version = st.session_state['selected_version']
    current_df = st.session_state['dataframe_versions'][selected_version]
    version_key = selected_version.replace('.', '_').replace(' ', '_')

    if create_action_button('Remove Current Version', key=f'remove_current_{version_key}'):
        remove_versions(
            [selected_version],
            cannot_remove_message='Cannot remove the original version.',
            last_version_message='Cannot remove the last remaining version.'
        )

    create_download_button(
        label='Download Current File',
        data=current_df.to_csv(index=False),
        file_name=f'{selected_version}.csv',
        mime='text/csv',
        key=f'download_current_{version_key}'
    )

    if create_action_button('Remove All Versions', key=f'remove_all_{version_key}'):
        versions = list(st.session_state['dataframe_versions'].keys())
        remove_versions(
            versions[1:],
            cannot_remove_message='Cannot remove the original version.',
            last_version_message='Only one version remains.'
        )

    zip_buffer = create_zip_of_all_versions()
    create_download_button(
        label='Download All Versions (ZIP)',
        data=zip_buffer.getvalue(),
        file_name='all_versions.zip',
        mime='application/zip',
        key=f'download_all_{version_key}'
    )

def render_file_preview(selected_df, version):
    print("\n=== RENDER FILE PREVIEW START ===")
    print(f"Version being previewed: {version}")
    print(f"Selected DF shape: {selected_df.shape}")

    with st.expander('Preview of Selected Version', expanded=False):
        if version in st.session_state['dataframe_versions']:
            preview_df = st.session_state['dataframe_versions'][version].copy()
            print(f"Preview DF shape: {preview_df.shape}")
            for col in preview_df.select_dtypes(['object']):
                preview_df[col] = preview_df[col].astype(str)
            st.dataframe(preview_df.head())
        else:
            print(f"Version {version} not found in dataframe_versions")
            st.write("No preview available for this version")
    print("=== RENDER FILE PREVIEW END ===\n")


def render_operation_tabs(selected_df):
    st.markdown('#### Operations')
    tab_keys = list(CONFIG['ui'].TABS.keys())
    tab_names = list(CONFIG['ui'].TABS.values())

    if 'current_tab' not in st.session_state:
        st.session_state['current_tab'] = CONFIG['ui'].DEFAULT_TAB

    tabs = st.tabs(tab_names)
    for idx, tab in enumerate(tabs):
        with tab:
            st.session_state['current_tab'] = tab_keys[idx]
            component_class = ComponentRegistry.get_component(tab_keys[idx])
            if component_class:
                component = component_class()
                if tab_keys[idx] == 'filter_builder':
                    component.render(selected_df)
                else:
                    component.render()


def render_operation_controls(df):
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_version = render_file_selection()
        selected_df = st.session_state['dataframe_versions'][selected_version].copy(deep=True)
        render_file_preview(selected_df, selected_version)

    with col2:
        render_file_info(selected_df)

    if selected_df is not None:
        render_operation_tabs(selected_df)