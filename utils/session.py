import streamlit as st
from scruffy import Scruffy
from config.config import CONFIG
from utils.general import get_default_template

def initialize_session_state():
    if 'scruffy' not in st.session_state:
        st.session_state['scruffy'] = Scruffy()
    if 'commands' not in st.session_state:
        st.session_state['commands'] = []
    if 'filter_groups' not in st.session_state:
        st.session_state['filter_groups'] = [{'logical_op': 'AND', 'filters': []}]
    if 'df' not in st.session_state:
        st.session_state['df'] = None
    if 'current_tab' not in st.session_state:
        st.session_state['current_tab'] = CONFIG['ui'].DEFAULT_TAB
    if 'dataframe_versions' not in st.session_state:
        st.session_state['dataframe_versions'] = {}
    if 'selected_version' not in st.session_state:
        st.session_state['selected_version'] = None

def clear_session_state():
    if 'dataframe_versions' in st.session_state:
        original_version = next(iter(st.session_state['dataframe_versions'].items()))
        scruffed_version = next(
            ((k, v) for k, v in st.session_state['dataframe_versions'].items() if 'scruffed' in k.lower()),
            None
        )
        preserved = {
            'scruffy': st.session_state.get('scruffy'),
            'uploaded_filename': st.session_state.get('uploaded_filename'),
            'df': st.session_state.get('df'),
        }
        st.session_state.clear()
        for k, v in preserved.items():
            if v is not None:
                st.session_state[k] = v
        st.session_state['dataframe_versions'] = {original_version[0]: original_version[1]}
        if scruffed_version:
            st.session_state['dataframe_versions'][scruffed_version[0]] = scruffed_version[1]
        st.session_state['selected_version'] = original_version[0]
        st.session_state['commands'] = []
        st.session_state['is_default_template'] = True
        st.session_state['filter_groups'] = [{'logical_op': 'AND', 'filters': []}]
        st.session_state['result_df'] = None
        st.session_state['counts'] = None
        st.session_state['commands_executed'] = False