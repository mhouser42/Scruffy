import streamlit as st
import pandas as pd
from config import CONFIG
from utils.command import create_command, generate_scruff_command
from utils.general import get_image_as_base64

def render_header():
    logo_path = 'assets/logo.png'
    favicon_path = 'assets/favicon.png'
    def load_favicon():
        try:
            return f'data:image/png;base64,{get_image_as_base64(favicon_path)}'
        except FileNotFoundError:
            return '📊'
    st.set_page_config(page_title='Scruffy: SLM Data Janitor', page_icon=load_favicon(), layout='wide')
    left_col, right_col = st.columns([3, 1])
    with left_col:
        st.title('Scruffy: The Small Language Model Data Janitor')
    with right_col:
        try:
            st.image(logo_path, width=242)
        except FileNotFoundError:
            st.write('📊')

def render_data_preview(df):
    st.subheader('📈 Data Preview:')
    st.dataframe(df.head())

class TabView:
    def __init__(self):
        self.config = CONFIG['ui']
    def render(self):
        raise NotImplementedError('Render method must be implemented by subclass.')


class NaturalLanguageView(TabView):
    def render(self):
        st.markdown('### Describe Your Data Manipulation Command')
        user_input = st.text_area('📝 Enter your instructions here:')
        if st.button('🤖 Generate Commands', key='nl_generate_commands') and user_input.strip():
            def generate_commands():
                try:
                    scruffy = st.session_state['scruffy']
                    new_commands = scruffy.llm.generate_response(user_input)
                    if st.session_state.get('is_default_template', True):
                        st.session_state['commands'] = new_commands
                        st.session_state['is_default_template'] = False
                    else:
                        st.session_state['commands'].extend(new_commands)
                    st.success('Commands generated successfully.')
                    st.rerun()
                except Exception as e:
                    st.error(f'Error generating commands: {str(e)}')
            with st.spinner('Generating commands...'):
                generate_commands()


class FilterBuilderView(TabView):
    def render(self, df=None):
        if df is None:
            df = st.session_state['df']
        filename, description = self._render_command_settings()
        self._render_filter_group(df)
        if st.button('✨ Create Command', key='cm_create_command'):
            if any(group['filters'] for group in st.session_state['filter_groups']):
                create_command(description, filename)
            else:
                st.warning('Please add at least one filter before creating a command.')
    def _render_command_settings(self):
        st.markdown('### Construct Your Own Command')
        from config import CONFIG
        filename = st.text_input('Filename', value=CONFIG['data'].DEFAULT_FILENAME)
        description = st.text_input('Description')
        return filename, description
    def _render_filter_group(self, df):
        from utils.general import get_OPS_mapping
        OPS = get_OPS_mapping()
        def initialize_session_state():
            if 'filter_groups' not in st.session_state:
                st.session_state['filter_groups'] = [{'filters': []}]
            if 'filter_actions' not in st.session_state:
                st.session_state['filter_actions'] = {}
        initialize_session_state()
        st.markdown('### Filter Groups')
        for group_idx, group in enumerate(st.session_state['filter_groups']):
            with st.expander(f'Filter Group {group_idx + 1}', expanded=True):
                cols = st.columns([1, 2, 1, 1])
                with cols[0]:
                    if len(group['filters']) >= 1:
                        group['logical_op'] = st.selectbox(
                            '',
                            options=['AND', 'OR', 'XOR'],
                            key=f'logical_op_{group_idx}',
                            index=['AND', 'OR', 'XOR'].index(group.get('logical_op', 'AND'))
                        )
                with cols[1]:
                    if st.button('➕ Add Filter', key=f'add_filter_{group_idx}'):
                        current_filters = len(group['filters'])
                        group['filters'].append({'column': None, 'op': None, 'value': None})
                        if current_filters == 1 and group.get('logical_op') in ['OR', 'XOR']:
                            group['filters'].append({'column': None, 'op': None, 'value': None})
                with cols[2]:
                    if st.button('❌ Remove Group', key=f'remove_group_{group_idx}'):
                        st.session_state['filter_groups'].pop(group_idx)
                        st.rerun()
                for filter_idx, filter_dict in enumerate(group['filters']):
                    filter_cols = st.columns([3, 2, 3, 1])
                    with filter_cols[0]:
                        column = st.selectbox(
                            'Column',
                            options=df.columns,
                            key=f'column_{group_idx}_{filter_idx}'
                        )
                        if column != filter_dict['column']:
                            filter_dict['column'] = column
                            filter_dict['value'] = None
                    with filter_cols[1]:
                        filter_dict['op'] = st.selectbox(
                            'Operation',
                            options=OPS.keys(),
                            format_func=lambda x: OPS[x],
                            key=f'op_{group_idx}_{filter_idx}'
                        )
                    with filter_cols[2]:
                        if filter_dict['op'] not in ['isna', 'notna']:
                            self._render_value_input(filter_dict, df, f'{group_idx}_{filter_idx}')
                        else:
                            st.text('No value needed')
                    with filter_cols[3]:
                        min_filters = 2 if group.get('logical_op') in ['OR', 'XOR'] else 1
                        if len(group['filters']) > min_filters:
                            if st.button('❌', key=f'remove_filter_{group_idx}_{filter_idx}'):
                                group['filters'].pop(filter_idx)
                                st.rerun()
                if group.get('logical_op') in ['OR', 'XOR'] and len(group['filters']) < 2:
                    group['filters'].append({'column': None, 'op': None, 'value': None})
        if st.button('➕ Add Filter Group', key='add_filter_group'):
            st.session_state['filter_groups'].append({'filters': []})
            st.rerun()
        st.divider()

    def _render_value_input(self, filter_dict, df, key_suffix):
        if not filter_dict['column'] or not filter_dict['op']:
            return

        column = filter_dict['column']
        column_type = df[column].dtype
        unique_values = df[column].nunique()

        if filter_dict['op'] in ['isna', 'notna']:
            filter_dict['value'] = None
            return
        elif filter_dict['op'] == 'between':
            unique_values_list = sorted(df[column].dropna().unique().tolist())
            col1, col2 = st.columns(2)
            with col1:
                if pd.api.types.is_numeric_dtype(column_type):
                    value1 = st.selectbox('From', options=unique_values_list, key=f'value1_{key_suffix}')
                else:
                    value1 = st.date_input('From', key=f'value1_{key_suffix}')
            with col2:
                if pd.api.types.is_numeric_dtype(column_type):
                    value2 = st.selectbox('To', options=unique_values_list, key=f'value2_{key_suffix}')
                else:
                    value2 = st.date_input('To', key=f'value2_{key_suffix}')
            filter_dict['value'] = [value1, value2]
        else:
            if filter_dict['op'] == 'contains':
                filter_dict['value'] = st.text_input('Value', key=f'value_{key_suffix}')
            else:
                unique_values_list = sorted(df[column].dropna().unique().tolist())
                if pd.api.types.is_numeric_dtype(column_type):
                    filter_dict['value'] = st.selectbox('Value', options=unique_values_list, key=f'value_{key_suffix}')
                elif pd.api.types.is_datetime64_any_dtype(column_type):
                    filter_dict['value'] = st.selectbox('Value', options=unique_values_list, key=f'value_{key_suffix}')
                else:
                    filter_dict['value'] = st.selectbox('Value', options=unique_values_list, key=f'value_{key_suffix}')


class ScruffOptionsView(TabView):
    def __init__(self):
        super().__init__()
        self.scruff_defaults = CONFIG['scruff']
    def render(self):
        st.subheader('Scruff Options')
        scruff_options = self._get_scruff_options()
        col1, col2 = st.columns(2)
        with col1:
            if st.button('SCRUFF'):
                st.session_state['scruffy'].scruff(options=scruff_options)
                st.success('Data cleaned using Scruff options.')
        with col2:
            if st.button('Generate Scruff Command'):
                selected_version = st.session_state.get('selected_version', '')
                if selected_version:
                    original_description = next(
                        (command.get('description', '')
                         for command in st.session_state.get('commands', [])
                         if command.get('filename') == selected_version),
                        'Dataset transformation'
                    )
                    command = generate_scruff_command(
                        selected_version,
                        original_description,
                        scruff_options
                    )
                    if 'commands' not in st.session_state:
                        st.session_state['commands'] = []
                    st.session_state['commands'].append(command)
                    st.success('Scruff command added to sidebar.')
                    st.rerun()
    def _get_scruff_options(self):
        options = {}
        with st.expander('Column Options', expanded=False):
            options['standardize_columns'] = st.checkbox(
                'Standardize Column Names',
                value=self.scruff_defaults.COLUMN_OPTIONS['standardize_columns']
            )
            options['drop_empty_columns'] = st.checkbox(
                'Drop Empty Columns',
                value=self.scruff_defaults.COLUMN_OPTIONS['drop_empty_columns']
            )
            options['drop_duplicate_columns'] = st.checkbox(
                'Drop Duplicate Columns',
                value=self.scruff_defaults.COLUMN_OPTIONS['drop_duplicate_columns']
            )
            if 'df' in st.session_state:
                all_columns = st.session_state['df'].columns.tolist()
                options['excluded_columns'] = st.multiselect(
                    'Exclude columns from operations',
                    options=all_columns
                )
            else:
                options['excluded_columns'] = []
        with st.expander('Row Operations', expanded=False):
            options['drop_na_rows'] = st.checkbox(
                'Drop rows with any NA values',
                value=self.scruff_defaults.ROW_OPTIONS['drop_na_rows']
            )
            options['drop_na_threshold'] = None
            if not options['drop_na_rows']:
                options['drop_na_threshold'] = st.slider(
                    'Drop rows with NA percentage greater than:',
                    0, 100, self.scruff_defaults.NA_THRESHOLD, 5
                )
            options['drop_duplicate_rows'] = st.checkbox(
                'Drop Duplicate Rows',
                value=self.scruff_defaults.ROW_OPTIONS['drop_duplicate_rows']
            )
        with st.expander('Numeric Data Options', expanded=False):
            options['normalize_numeric'] = st.checkbox(
                'Normalize Numeric Data',
                value=self.scruff_defaults.NUMERIC_OPTIONS['normalize_numeric']
            )
            options['handle_outliers'] = st.checkbox(
                'Remove Outliers',
                value=self.scruff_defaults.NUMERIC_OPTIONS['handle_outliers']
            )
            if options['handle_outliers']:
                options['z_score_threshold'] = st.slider(
                    'Z-score threshold for outliers',
                    1.0, 5.0, self.scruff_defaults.Z_SCORE_THRESHOLD, 0.1
                )
            options['fill_numeric_na'] = st.checkbox(
                'Fill Numeric NA Values',
                value=self.scruff_defaults.NUMERIC_OPTIONS['fill_numeric_na']
            )
            if options['fill_numeric_na']:
                options['fill_method'] = st.selectbox(
                    'Fill method',
                    options=['mean', 'median', 'zero', 'forward', 'backward'],
                    index=['mean', 'median', 'zero', 'forward', 'backward'].index(self.scruff_defaults.FILL_METHOD)
                )
            options['numeric_conversion'] = st.selectbox(
                'Numeric Type Conversion',
                options=['None', 'Int to Float', 'Float to Int', 'Numeric to String'],
                index=['None', 'Int to Float', 'Float to Int', 'Numeric to String'].index(
                    self.scruff_defaults.NUMERIC_CONVERSION)
            )
        with st.expander('Text Data Options', expanded=False):
            options['remove_accents'] = st.checkbox(
                'Remove Accents',
                value=self.scruff_defaults.TEXT_OPTIONS['remove_accents']
            )
            options['to_lowercase'] = st.checkbox(
                'Convert to Lowercase',
                value=self.scruff_defaults.TEXT_OPTIONS['to_lowercase']
            )
            options['remove_special_chars'] = st.checkbox(
                'Remove Special Characters',
                value=self.scruff_defaults.TEXT_OPTIONS['remove_special_chars']
            )
            options['remove_stopwords'] = st.checkbox(
                'Remove Stopwords',
                value=self.scruff_defaults.TEXT_OPTIONS['remove_stopwords']
            )
            options['lemmatize'] = st.checkbox(
                'Lemmatize Text',
                value=self.scruff_defaults.TEXT_OPTIONS['lemmatize']
            )

        with st.expander('Value Replacement Options', expanded=False):
            if st.checkbox('Replace values in specific columns'):
                options['replace_values'] = {}
                if 'df' in st.session_state:
                    columns = st.session_state['df'].columns.tolist()
                    selected_columns = st.multiselect('Select columns for value replacement', options=columns)
                    for column in selected_columns:
                        st.subheader(f'Replacements for {column}')
                        num_replacements = st.number_input(f'Number of replacements for {column}', min_value=1,
                                                           max_value=10, value=1, key=f'num_rep_{column}')
                        column_replacements = {}
                        for i in range(num_replacements):
                            col1, col2 = st.columns(2)
                            with col1:
                                old_value = st.text_input(f'Old value {i + 1}', key=f'old_{column}_{i}')
                            with col2:
                                new_value = st.text_input(f'New value {i + 1}', key=f'new_{column}_{i}')
                            if old_value and new_value:
                                column_replacements[old_value] = new_value
                        if column_replacements:
                            options['replace_values'][column] = column_replacements

            if st.checkbox('Replace values across all columns'):
                options['replace_all_values'] = {}
                num_global_replacements = st.number_input('Number of global replacements', min_value=1, max_value=10,
                                                          value=1)
                for i in range(num_global_replacements):
                    col1, col2 = st.columns(2)
                    with col1:
                        old_value = st.text_input(f'Old value {i + 1}', key=f'global_old_{i}')
                    with col2:
                        new_value = st.text_input(f'New value {i + 1}', key=f'global_new_{i}')
                    if old_value and new_value:
                        options['replace_all_values'][old_value] = new_value

        return options


class ComponentRegistry:
    _components = {
        'natural_language': NaturalLanguageView,
        'scruff_options': ScruffOptionsView,
        'filter_builder': FilterBuilderView,
    }
    @classmethod
    def get_component(cls, name: str):
        return cls._components.get(name)
    @classmethod
    def register_component(cls, name: str, component):
        cls._components[name] = component