import streamlit as st
import io
import zipfile

class VersionController:
    def load_from_session(self):
        if 'uploaded_files' not in st.session_state:
            st.session_state['uploaded_files'] = {}
        if 'selected_upload' not in st.session_state:
            st.session_state['selected_upload'] = None
        if 'dataframe_versions' not in st.session_state:
            st.session_state['dataframe_versions'] = {}
        if 'selected_version' not in st.session_state:
            st.session_state['selected_version'] = None

    def add_uploaded_file(self, name, df):
        base_name = name.rsplit('.', 1)[0]
        st.session_state['uploaded_files'][name] = base_name
        st.session_state['dataframe_versions'][name] = df
        st.session_state['selected_upload'] = name
        st.session_state['selected_version'] = name

    def get_uploaded_files(self):
        return list(st.session_state['uploaded_files'].keys())

    def get_versions_for_upload(self, upload_name=None):
        if upload_name is None:
            upload_name = st.session_state['selected_upload']
        if not upload_name:
            return []
        base_name = st.session_state['uploaded_files'][upload_name]
        return [v for v in st.session_state['dataframe_versions'].keys()
                if v.startswith(f'{base_name}')]

    def get_dataframes(self):
        return st.session_state['dataframe_versions']

    def get_selected_upload(self):
        return st.session_state['selected_upload']

    def set_selected_upload(self, upload):
        st.session_state['selected_upload'] = upload
        versions = self.get_versions_for_upload(upload)
        if versions:
            st.session_state['selected_version'] = versions[0]

    def get_selected_version(self):
        return st.session_state['selected_version']

    def set_selected_version(self, version):
        st.session_state['selected_version'] = version
        if 'df' in st.session_state and version in self.get_dataframes():
            st.session_state['df'] = self.get_dataframes()[version].copy(deep=True)

    def add_version(self, name, df, upload_name=None):
        if upload_name is None:
            upload_name = st.session_state['selected_upload']
        base_name = st.session_state['uploaded_files'][upload_name]
        if not name.startswith(f'{base_name}'):
            name = f'{base_name}_{name}'
        st.session_state['dataframe_versions'][name] = df
        self.set_selected_version(name)
        st.rerun()

    def remove_versions(self, versions_to_remove, cannot_remove_message, last_version_message):
        versions = self.get_versions_for_upload()
        if len(versions) > 1:
            original_version = versions[0]
            for version in versions_to_remove:
                if version == original_version:
                    st.warning(cannot_remove_message)
                    return
                del st.session_state['dataframe_versions'][version]
            if st.session_state['selected_version'] not in st.session_state['dataframe_versions']:
                self.set_selected_version(original_version)
            st.rerun()
        else:
            st.warning(last_version_message)


    def sync_versions_with_session(self):
        selected_version = self.get_selected_version()
        if selected_version in self.get_dataframes():
            current_df = self.get_dataframes()[selected_version]
            st.session_state['df'] = current_df.copy(deep=True)
            if 'scruffy' in st.session_state:
                st.session_state['scruffy'].curr_df = current_df.copy(deep=True)

    def create_zip_of_all_versions(self):
        zip_buffer = io.BytesIO()
        versions = self.get_versions_for_upload()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for version in versions:
                df = st.session_state['dataframe_versions'][version]
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                zip_file.writestr(version, csv_buffer.getvalue())
        zip_buffer.seek(0)
        return zip_buffer