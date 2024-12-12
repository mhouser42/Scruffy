import streamlit as st
import json
from utils.general import error_handler

@error_handler
def create_command(description, filename):
    if not any(group['filters'] for group in st.session_state['filter_groups']):
        st.warning('Please add at least one filter before creating a command.')
        return
    command = {
        'description': description,
        'filename': filename,
        'filters': _create_filter_dict(),
    }
    if len(st.session_state['commands']) == 1 and not any(st.session_state['commands'][0].get('filters', {})):
        st.session_state['commands'] = []
        st.session_state['is_default_template'] = False
        st.session_state['is_first_command'] = False
    st.session_state['commands'] = [command]
    st.session_state['filter_groups'] = [{'logical_op': 'AND', 'filters': []}]
    if 'scruffy' in st.session_state and st.session_state.get('df') is not None:
        with st.spinner('Executing command...'):
            result_df = st.session_state['scruffy'].apply_command(command)
            if result_df is not None:
                if 'command_results' not in st.session_state:
                    st.session_state['command_results'] = {}
                st.session_state['command_results'][0] = result_df
                st.success('Command created and executed successfully')
    st.rerun()

def _create_filter_dict():
    result = {}
    for group in st.session_state['filter_groups']:
        if not group['filters']:
            continue
        group_filters = []
        for filter_dict in group['filters']:
            if all(v is not None for v in [filter_dict['column'], filter_dict['op']]):
                if filter_dict['op'] in ['isna', 'notna']:
                    filter_entry = {
                        filter_dict['column']: {
                            'op': filter_dict['op']
                        }
                    }
                else:
                    filter_entry = {
                        filter_dict['column']: {
                            'op': filter_dict['op'],
                            'value': filter_dict['value']
                        }
                    }
                group_filters.append(filter_entry)
        if group_filters:
            if len(group_filters) == 1:
                result.update(group_filters[0])
            else:
                logical_op = group.get('logical_op', 'AND')
                if logical_op in result:
                    if isinstance(result[logical_op], list):
                        result[logical_op].extend(group_filters)
                    else:
                        result[logical_op] = [result[logical_op]] + group_filters
                else:
                    result[logical_op] = group_filters
    return result

def generate_scruff_command(original_filename, original_description, options):
    base_filename = original_filename.rsplit('.', 1)[0]
    new_filename = f'{base_filename}_scruffed.csv'
    active_options = []
    for key, value in options.items():
        if isinstance(value, bool) and value:
            active_options.append(key)
        elif isinstance(value, (int, float)) and value is not None:
            active_options.append(f'{key}: {value}')
        elif isinstance(value, list) and value:
            active_options.append(f'{key}: {value}')
        elif isinstance(value, str) and value != 'None':
            active_options.append(f'{key}: {value}')
    scruff_description = ', '.join(active_options)
    new_description = f'{original_description}. Scruffed with: {scruff_description}'
    command = {
        'filename': new_filename,
        'description': new_description,
        'scruff': options
    }
    return command