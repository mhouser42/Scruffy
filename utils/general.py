import base64
import functools
import os
import io
import json
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
        'filters': {},
        'scruff': {}
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