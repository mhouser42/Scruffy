import base64
import functools
import os
import io
import json
import zipfile

import streamlit as st

from config import CONFIG


def get_image_as_base64(image_path: str) -> str:
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def load_system_prompt() -> str:
    try:
        with open('data/system_prompt.md', 'r') as f:
            return f.read()
    except FileNotFoundError:
        st.error('System prompt file not found.')
        return None
    except Exception as e:
        st.error(CONFIG['errors'].FILE_UPLOAD_ERROR.format(e))
        return None


def load_example_schemas():
    '''
    Loads schema examples from JSON files in the data/commands/example directory.
    Returns a dictionary mapping the filename (without extension) to the schema content.
    '''
    examples = {}
    example_path = 'data/commands/example'

    try:
        if not os.path.exists(example_path):
            os.makedirs(example_path, exist_ok=True)
            return examples

        for filename in os.listdir(example_path):
            if filename.endswith('.json'):
                with open(os.path.join(example_path, filename), 'r') as f:
                    key = filename.replace('.json', '')
                    examples[key] = json.load(f)
        return examples
    except Exception as e:
        st.error(f'Error loading example schemas: {str(e)}')
        return {}


def get_OPS_mapping():
    return {
        '==': 'equals',
        '!=': 'not equals',
        '<': 'less than',
        '<=': 'less than or equal',
        '>': 'greater than',
        '>=': 'greater than or equal',
        'in': 'in',
        'not in': 'not in',
        'isna': 'is null',
        'notna': 'is not null',
        'between': 'between',
        'contains': 'contains',
        '+': 'add',
        '-': 'subtract',
        '*': 'multiply',
        '/': 'divide',
        '//': 'floor divide',
        '%': 'modulo',
        '**': 'power',
        '&': 'and',
        '|': 'or',
        '^': 'xor',
        '~': 'not',
        '<<': 'left shift',
        '>>': 'right shift'
    }


def get_default_template():
    return {
        'filename': 'filter_data.csv',
        'description': 'Empty default JSON structure',
        'filters': {

        },
        'scruff': {

        }
    }


def error_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            st.error(f'{error_type}: {error_msg}')
            return None
    return wrapper


def create_zip_of_all_versions():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for version, df in st.session_state['dataframe_versions'].items():
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            zip_file.writestr(f'{version}', csv_buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

def create_zip_of_all_results():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, result_df in enumerate(st.session_state.get('result_df', [])):
            csv_buffer = io.StringIO()
            result_df.to_csv(csv_buffer, index=False)
            filename = st.session_state['commands'][i]['filename']
            zip_file.writestr(filename, csv_buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer
