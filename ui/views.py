import streamlit as st
from typing import Dict, Type
from config import CONFIG
from ui.command_sidebar import (
    render_command_settings,
    render_filter_group
)
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
                    options=all_columns,
                    help='Selected columns will be excluded from all cleaning operations'
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

        return options

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

        filename, description = render_command_settings()
        render_filter_group(df)

        if st.button('✨ Create Command', key='cm_create_command'):
            if any(group['filters'] for group in st.session_state['filter_groups']):
                create_command(description, filename)
            else:
                st.warning('Please add at least one filter before creating a command.')


class ComponentRegistry:
    _components: Dict[str, Type[TabView]] = {
        'natural_language': NaturalLanguageView,
        'scruff_options': ScruffOptionsView,
        'filter_builder': FilterBuilderView,
    }

    @classmethod
    def get_component(cls, name: str) -> Type[TabView]:
        return cls._components.get(name)

    @classmethod
    def register_component(cls, name: str, component: Type[TabView]):
        cls._components[name] = component
