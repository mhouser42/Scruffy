import streamlit as st
from config import CONFIG
from ui.views import ComponentRegistry
import pandas as pd


def render_file_selection():
    from version_control.controller import VersionController
    vc = VersionController()
    vc.load_from_session()

    uploaded_files = vc.get_uploaded_files()
    if not uploaded_files:
        return None

    selected_upload = st.selectbox(
        'Uploaded Files:',
        options=uploaded_files,
        index=uploaded_files.index(vc.get_selected_upload()) if vc.get_selected_upload() in uploaded_files else 0,
        key='upload_selector'
    )

    if selected_upload != vc.get_selected_upload():
        vc.set_selected_upload(selected_upload)

    versions = vc.get_versions_for_upload(selected_upload)
    if not versions:
        return None

    selected_version = st.selectbox(
        'File Versions:',
        options=versions,
        index=versions.index(vc.get_selected_version()) if vc.get_selected_version() in versions else 0,
        key='version_selector'
    )

    if selected_version != vc.get_selected_version():
        vc.set_selected_version(selected_version)
        vc.sync_versions_with_session()

    return selected_version

def render_versioning_buttons():
    from version_control.controller import VersionController
    vc = VersionController()
    vc.load_from_session()
    versions = list(vc.get_dataframes().keys())
    if versions:
        selected_version = st.session_state['selected_version'] if 'selected_version' in st.session_state and st.session_state['selected_version'] in versions else versions[0]
        current_df = vc.get_dataframes()[selected_version]
        version_key = selected_version.replace('.', '_').replace(' ', '_')

        if st.button('Remove Current Version', key=f'remove_current_{version_key}'):
            vc.remove_versions(
                [selected_version],
                cannot_remove_message='Cannot remove the original version.',
                last_version_message='Cannot remove the last remaining version.'
            )
            if st.session_state['selected_version'] not in vc.get_dataframes():
                v = list(vc.get_dataframes().keys())
                if v:
                    st.session_state['selected_version'] = v[0]
            st.rerun()

        st.download_button(
            label='Download Current File',
            data=current_df.to_csv(index=False),
            file_name=f'{selected_version}.csv',
            mime='text/csv',
            key=f'download_current_{version_key}'
        )

        if st.button('Remove All Versions', key=f'remove_all_{version_key}'):
            vc.remove_versions(
                versions[1:],
                cannot_remove_message='Cannot remove the original version.',
                last_version_message='Only one version remains.'
            )
            v = list(vc.get_dataframes().keys())
            if v:
                st.session_state['selected_version'] = v[0]
            st.rerun()

        zip_buffer = vc.create_zip_of_all_versions()
        st.download_button(
            label='Download All Versions (ZIP)',
            data=zip_buffer.getvalue(),
            file_name='all_versions.zip',
            mime='application/zip',
            key=f'download_all_{version_key}'
        )


def render_file_info(selected_df):
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown('#### Columns/Data Types:')
        st.write(selected_df.dtypes)
        st.write(f'Shape: {selected_df.shape}')
    with col2:
        render_versioning_buttons()

def render_file_preview(selected_df, version):
    with st.expander('Preview of Selected Version', expanded=False):
        preview_df = selected_df.copy()
        for col in preview_df.select_dtypes(['object']):
            preview_df[col] = preview_df[col].astype(str)
        st.dataframe(preview_df.head())

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
        from version_control.controller import VersionController
        vc = VersionController()
        vc.load_from_session()
        dataframes = vc.get_dataframes()
        if selected_version not in dataframes and dataframes:
            selected_version = list(dataframes.keys())[0]
            st.session_state['selected_version'] = selected_version

    if selected_version in dataframes:
        selected_df = dataframes[selected_version].copy(deep=True)
        with col1:
            render_file_preview(selected_df, selected_version)
        with col2:
            render_file_info(selected_df)
        if selected_df is not None:
            render_operation_tabs(selected_df)