import streamlit as st
from streamlit_ace import st_ace
import pandas as pd
from config.config import CONFIG
from utils.general import get_OPS_mapping, get_default_template, load_example_schemas
import json


def render_command_settings():
    st.markdown('### Construct Your Own Command')
    filename = st.text_input('Filename', value=CONFIG['data'].DEFAULT_FILENAME)
    description = st.text_input('Description')
    return filename, description


def render_filter_group(df):
    OPS = get_OPS_mapping()

    def initialize_session_state():
        if 'filter_groups' not in st.session_state:
            st.session_state['filter_groups'] = [{'filters': []}]
        if 'filter_actions' not in st.session_state:
            st.session_state['filter_actions'] = {}

    def render_logical_operator(group, group_idx):
        if len(group['filters']) >= 1:
            group['logical_op'] = st.selectbox(
                '',
                options=['AND', 'OR', 'XOR'],
                key=f'logical_op_{group_idx}',
                index=['AND', 'OR', 'XOR'].index(group.get('logical_op', 'AND')),
                help='Logical operator to combine filters'
            )

    def handle_add_filter(group, group_idx):
        if st.button('➕ Add Filter', key=f'add_filter_{group_idx}'):
            current_filters = len(group['filters'])
            group['filters'].append({'column': None, 'op': None, 'value': None})
            if current_filters == 1 and group.get('logical_op') in ['OR', 'XOR']:
                group['filters'].append({'column': None, 'op': None, 'value': None})

    def handle_remove_group(group_idx):
        if st.button('❌ Remove Group', key=f'remove_group_{group_idx}'):
            st.session_state['filter_groups'].pop(group_idx)

    def render_filter_controls(filter_dict, df, group_idx, filter_idx):
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
                options=get_OPS_mapping().keys(),
                format_func=lambda x: get_OPS_mapping()[x],
                key=f'op_{group_idx}_{filter_idx}'
            )

        with filter_cols[2]:
            if filter_dict['op'] not in ['isna', 'notna']:
                render_value_input(filter_dict, df, f'{group_idx}_{filter_idx}')
            else:
                st.text('No value needed for this operation')

        return filter_cols[3]

    def handle_remove_filter(group, group_idx, filter_idx, col):
        min_filters = 2 if group.get('logical_op') in ['OR', 'XOR'] else 1
        if len(group['filters']) > min_filters:
            if col.button('❌', key=f'remove_filter_{group_idx}_{filter_idx}'):
                group['filters'].pop(filter_idx)

    def ensure_minimum_filters(group):
        if group.get('logical_op') in ['OR', 'XOR'] and len(group['filters']) < 2:
            group['filters'].append({'column': None, 'op': None, 'value': None})

    initialize_session_state()
    st.markdown('### Filter Groups')

    for group_idx, group in enumerate(st.session_state['filter_groups']):
        with st.expander(f'Filter Group {group_idx + 1}', expanded=True):
            cols = st.columns([1, 2, 1, 1])

            with cols[0]:
                render_logical_operator(group, group_idx)

            with cols[1]:
                handle_add_filter(group, group_idx)

            with cols[2]:
                handle_remove_group(group_idx)

            for filter_idx, filter_dict in enumerate(group['filters']):
                last_col = render_filter_controls(filter_dict, df, group_idx, filter_idx)
                with last_col:
                    handle_remove_filter(group, group_idx, filter_idx, last_col)

            ensure_minimum_filters(group)

    if st.button('➕ Add Filter Group', key='add_filter_group'):
        st.session_state['filter_groups'].append({'filters': []})
    st.divider()


def render_value_input(filter_dict, df, key_suffix):
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
                value1 = st.selectbox('From',
                                      options=unique_values_list,
                                      key=f'value1_{key_suffix}')
            else:
                value1 = st.date_input('From', key=f'value1_{key_suffix}')
        with col2:
            if pd.api.types.is_numeric_dtype(column_type):
                value2 = st.selectbox('To',
                                      options=unique_values_list,
                                      key=f'value2_{key_suffix}')
            else:
                value2 = st.date_input('To', key=f'value2_{key_suffix}')
        filter_dict['value'] = [value1, value2]
    else:
        unique_values_list = sorted(df[column].dropna().unique().tolist())
        if pd.api.types.is_numeric_dtype(column_type):
            filter_dict['value'] = st.selectbox(
                'Value',
                options=unique_values_list,
                key=f'value_{key_suffix}'
            )
        elif pd.api.types.is_datetime64_any_dtype(column_type):
            filter_dict['value'] = st.selectbox(
                'Value',
                options=unique_values_list,
                key=f'value_{key_suffix}'
            )
        else:
            filter_dict['value'] = st.selectbox(
                'Value',
                options=unique_values_list,
                key=f'value_{key_suffix}'
            )


def render_tab_content(title, description, example_key, examples):
    '''Renders a standard tab with title, description, and JSON example.'''
    st.markdown(f'### {title}')
    st.markdown(description)
    if example_key in examples:
        st.json(examples[example_key])


def render_and_operations_tab(examples):
    '''Renders the Basic AND Operations tab content.'''
    render_tab_content(
        'AND Operations',
        '''
        AND operations combine multiple conditions that all must be true.
        When working with different columns, you can list conditions directly in the filters object - 
        they will automatically be combined with AND logic. If you are filtering the same column multiple times,
        an explict AND clause will be used to prevent duplicate keys in the JSON file.
        ''',
        'and_operations',
        examples
    )


def render_or_xor_tab(examples):
    '''Renders the OR and XOR Operations tab content.'''
    render_tab_content(
        'OR and XOR Operations',
        '''
        OR operations let you specify alternative conditions - any one condition can be true.
        XOR (exclusive OR) requires exactly one condition to be true, perfect for mutually exclusive categories.
        ''',
        'or_xor_operations',
        examples
    )


def render_nested_operations_tab(examples):
    '''Renders the Nested Logical Operations tab content.'''
    render_tab_content(
        'Nested Logical Operations',
        '''
        For more complex operations you can nest your conditional logic inside clauses.
        Use explicit AND arrays to group conditions together within OR and XOR operations.
        ''',
        'nested_operations',
        examples
    )


def render_data_cleaning_tab(examples):
    '''Renders the Data Cleaning Operations tab content.'''
    render_tab_content(
        'Data Cleaning Operations',
        '''
        Scruff operations help you clean and standardize your data.
        You can standardize column names, handle missing values, clean text data,
        and normalize numeric values - all in a single operation.
        ''',
        'scruffy_operations',
        examples
    )


def render_combined_operations_tab(examples):
    '''Renders the Combined Filter & Clean tab content.'''
    render_tab_content(
        'Combined Filter & Clean',
        '''
        You can combine filtering and cleaning in a single command.
        First filter your data to select the records you want,
        then apply cleaning operations to standardize and improve the filtered data.
        ''',
        'combined_filter_scruff',
        examples
    )


def render_batch_processing_tab(examples):
    '''Renders the Batch Processing tab content.'''
    render_tab_content(
        'Batch Processing',
        '''
        When you need multiple output files from the same input data,
        use an array of operations. Each operation creates its own output file,
        letting you generate multiple views of your data in one command.
        ''',
        'batch_processing',
        examples
    )


def render_schema_examples(examples):
    '''Renders the schema examples section with tabs.'''
    st.markdown('''
    ### Understanding Schema Operations

    Our schema system allows you to transform data through filtering and cleaning operations. 
    These examples demonstrate how to build operations from simple to complex:

    - Use AND operations for basic filtering where all conditions must be true
    - Add OR and XOR operations when you need more sophisticated logic
    - Combine operations with nesting for complex business rules
    - Apply data cleaning to standardize and improve data quality
    - Mix filtering and cleaning for complete data transformations
    - Process multiple outputs in a single command
    ''')

    tabs = st.tabs([
        'Basic AND',
        'OR & XOR',
        'Nested Logic',
        'Data Cleaning',
        'Combined Ops',
        'Batch Processing'
    ])

    tab_renderers = [
        render_and_operations_tab,
        render_or_xor_tab,
        render_nested_operations_tab,
        render_data_cleaning_tab,
        render_combined_operations_tab,
        render_batch_processing_tab
    ]

    for tab, renderer in zip(tabs, tab_renderers):
        with tab:
            renderer(examples)


def render_command_sidebar():
    with st.sidebar:
        st.header('Command Schemas')

        examples = load_example_schemas()

        with st.expander('ℹ️ Schema Examples', expanded=False):
            render_schema_examples(examples)

        uploaded_file = st.file_uploader('Upload Command Schema', type=['json'], key='schema_uploader')
        if uploaded_file is not None and 'last_uploaded_file' not in st.session_state:
            try:
                uploaded_schema = json.load(uploaded_file)
                if isinstance(uploaded_schema, list):
                    st.session_state['commands'] = uploaded_schema
                else:
                    st.session_state['commands'] = [uploaded_schema]
                st.success('Schema(s) uploaded successfully!')
                st.session_state['last_uploaded_file'] = uploaded_file.name
            except json.JSONDecodeError:
                st.error('Invalid JSON file')
            except Exception as e:
                st.error(f'Error uploading file: {str(e)}')
        elif uploaded_file is None and 'last_uploaded_file' in st.session_state:
            del st.session_state['last_uploaded_file']

        with st.container():
            st.markdown('### Current Commands')

            if not st.session_state.get('commands'):
                st.info(
                    'No active commands. Click "Add New Command" below to start, or use the Filter Builder or Natural Language tabs to generate commands.')
            else:
                edit_commands_ui(st.session_state.get('df'))

            st.markdown('---')
            if st.button('➕ Add New Command'):
                st.session_state['commands'].append(get_default_template())
                st.rerun()
            st.markdown('---')
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.session_state.get('commands'):
                    st.download_button(
                        '💾 Save All',
                        data=json.dumps(st.session_state['commands'], indent=2),
                        file_name='all_commands.json',
                        mime='application/json',
                        key='download_all_commands'
                    )
            with col2:
                if st.button('🗑️ Delete All'):
                    st.session_state['commands'] = []
                    st.session_state['result_df'] = None
                    st.session_state['counts'] = None
                    st.session_state['commands_executed'] = False

            with col3:
                if st.button('▶️ Execute All'):
                    if st.session_state.get('commands') and st.session_state.get('df') is not None:
                        with st.spinner('Executing commands...'):
                            results, counts = st.session_state['scruffy'].apply_commands(
                                st.session_state['commands'], get_counts=True)
                            if results is not None:
                                st.session_state['result_df'] = results
                                st.session_state['counts'] = counts
                                st.session_state['commands_executed'] = True
                                if len(results) > 0:
                                    last_result = results[-1]
                                    st.session_state['df'] = last_result
                                    version_name = st.session_state['commands'][-1].get('filename', 'last_command.csv')
                                    st.session_state['dataframe_versions'][version_name] = last_result
                                    st.session_state['selected_version'] = version_name


def edit_commands_ui(df):
    for i, command in enumerate(st.session_state.get('commands', [])):
        st.markdown(f'### Command {i + 1}')

        with st.form(key=f'command_form_{i}'):
            command_str = json.dumps(command, indent=2)
            height = max(150, min(600, len(command_str.split('\n')) * 20))

            edited_command_str = st_ace(
                value=command_str,
                language='json',
                theme='github',
                key=f'command_editor_{i}',
                height=height,
                auto_update=False
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                delete = st.form_submit_button('🗑️ Delete')
            with col2:
                execute = st.form_submit_button('▶️ Execute')

            if delete:
                st.session_state['commands'].pop(i)
                if 'command_results' in st.session_state and i in st.session_state['command_results']:
                    del st.session_state['command_results'][i]
                st.rerun()

            elif execute:
                try:
                    edited_command = json.loads(edited_command_str)
                    st.session_state['commands'][i] = edited_command
                    if 'scruffy' in st.session_state:
                        with st.spinner('Executing command...'):
                            result_df = st.session_state['scruffy'].apply_command(edited_command)
                            print(result_df)
                            if result_df is not None:
                                if 'command_results' not in st.session_state:
                                    st.session_state['command_results'] = {}
                                st.session_state['command_results'][i] = result_df
                                st.success('Command executed successfully')
                except json.JSONDecodeError as e:
                    st.error(f'Invalid JSON: {str(e)}')
                except Exception as e:
                    st.error(f'Error executing command: {str(e)}')

        col1, col2 = st.columns([1, 3])
        with col1:
            try:
                edited_command = json.loads(edited_command_str)
                filename = edited_command.get('filename', f'command_{i}.json').rsplit('.', 1)[0] + '.json'
                st.download_button(
                    '💾 Save',
                    data=json.dumps(edited_command, indent=2),
                    file_name=filename,
                    mime='application/json',
                    key=f'download_command_{i}'
                )
            except json.JSONDecodeError:
                pass