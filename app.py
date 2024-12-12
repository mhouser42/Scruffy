import streamlit as st
import pandas as pd
import os
os.environ['STREAMLIT_SERVER_MAXSIZE'] = '1'

from ui import (
    render_header,
    render_operation_controls,
    render_command_sidebar
)
from utils.session import initialize_session_state
from utils.general import error_handler

@error_handler
def handle_file_upload():
    uploaded_file = st.file_uploader('📁 Upload your CSV file', type=['csv'])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            from version_control.controller import VersionController
            vc = VersionController()
            vc.load_from_session()
            vc.add_uploaded_file(uploaded_file.name, df)
            st.session_state['df'] = df
            st.session_state['uploaded_filename'] = uploaded_file.name
            return True
        except Exception as e:
            st.error(f'Error uploading file: {str(e)}')
    return False

if __name__ == '__main__':
    initialize_session_state()
    render_header()
    render_command_sidebar()

    should_render = handle_file_upload() or 'uploaded_filename' in st.session_state
    if should_render and st.session_state.get('df') is not None:
        render_operation_controls(st.session_state['df'])