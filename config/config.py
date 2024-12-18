import configparser
from typing import Dict, List

config = configparser.ConfigParser()
config.read('config/config.ini')

class UIConfig:
    TABS: Dict[str, str] = {
        'natural_language': 'Natural Language',
        'filter_builder': 'Filter Builder',
        'scruff_options': 'Scruff Options',
    }
    DEFAULT_TAB: str = config.get('UI', 'DEFAULT_TAB')
    SCHEMA_TABS: List[str] = [
        'Basic AND',
        'OR & XOR',
        'Nested Logic',
        'Data Cleaning',
        'Combined Ops',
        'Batch Processing'
    ]
    SCHEMA_EXAMPLES: Dict[str, str] = {
        'Basic AND': 'and_operations',
        'OR & XOR': 'or_xor_operations',
        'Nested Logic': 'nested_operations',
        'Data Cleaning': 'scruffy_operations',
        'Combined Ops': 'combined_filter_scruff',
        'Batch Processing': 'batch_processing'
    }
    SCHEMA_DESCRIPTIONS: Dict[str, str] = {
        'Basic AND': '''
        AND operations combine multiple conditions that all must be true.
        When working with different columns, you can list conditions directly in the filters object - they will
        automatically be combined with AND logic. If you are filtering the same column multiple times, use an
        explict AND clause to avoid duplicate keys.
        ''',
        'OR & XOR': '''
        OR operations let you specify alternative conditions - any one condition can be true.
        XOR (exclusive OR) requires exactly one condition to be true, perfect for mutually exclusive categories.
        ''',
        'Nested Logic': '''
        Complex business rules often require combining different types of operations.
        Use explicit AND arrays to group conditions together within OR and XOR operations.
        This example shows how to build sophisticated nested logic.
        ''',
        'Data Cleaning': '''
        Scruff operations help you clean and standardize your data.
        You can standardize column names, handle missing values, clean text data,
        and normalize numeric values.
        ''',
        'Combined Ops': '''
        You can combine filtering and cleaning in a single command.
        First filter your data to select the records you want,
        then apply cleaning operations to standardize and improve the filtered data.
        ''',
        'Batch Processing': '''
        When you need multiple output files from the same input data,
        use an array of operations. Each operation creates its own output file,
        letting you generate multiple views of your data in one command.
        '''
    }

class DataConfig:
    DEFAULT_FILENAME: str = config.get('DATA', 'DEFAULT_FILENAME')
    SUPPORTED_FILE_TYPES: List[str] = config.get('DATA', 'SUPPORTED_FILE_TYPES').split(',')
    EXAMPLE_SCHEMAS_PATH: str = config.get('DATA', 'EXAMPLE_SCHEMAS_PATH')

class ErrorMessages:
    FILE_UPLOAD_ERROR: str = config.get('ERRORS', 'FILE_UPLOAD_ERROR')
    COMMAND_EXECUTION_ERROR: str = config.get('ERRORS', 'COMMAND_EXECUTION_ERROR')
    JSON_PARSE_ERROR: str = config.get('ERRORS', 'JSON_PARSE_ERROR')
    VALIDATION_ERROR: str = config.get('ERRORS', 'VALIDATION_ERROR')

class LLMConfig:
    MODEL_ID: str = config.get('LLM', 'MODEL_ID')
    API_URI: str = config.get('LLM', 'API_URI')
    MAX_TOKENS: int = config.getint('LLM', 'MAX_TOKENS')
    TEMPERATURE: float = config.getfloat('LLM', 'TEMPERATURE')
    TOP_P: float = config.getfloat('LLM', 'TOP_P')

class ScruffDefaults:
    COLUMN_OPTIONS: Dict[str, bool] = {
        'standardize_columns': config.getboolean('SCRUFF', 'STANDARDIZE_COLUMNS'),
        'drop_empty_columns': config.getboolean('SCRUFF', 'DROP_EMPTY_COLUMNS'),
        'drop_duplicate_columns': config.getboolean('SCRUFF', 'DROP_DUPLICATE_COLUMNS')
    }
    ROW_OPTIONS: Dict[str, bool] = {
        'drop_na_rows': config.getboolean('SCRUFF', 'DROP_NA_ROWS'),
        'drop_duplicate_rows': config.getboolean('SCRUFF', 'DROP_DUPLICATE_ROWS')
    }
    NA_THRESHOLD: int = config.getint('SCRUFF', 'NA_THRESHOLD')
    NUMERIC_OPTIONS: Dict[str, bool] = {
        'normalize_numeric': config.getboolean('SCRUFF', 'NORMALIZE_NUMERIC'),
        'handle_outliers': config.getboolean('SCRUFF', 'HANDLE_OUTLIERS'),
        'fill_numeric_na': config.getboolean('SCRUFF', 'FILL_NUMERIC_NA')
    }
    Z_SCORE_THRESHOLD: float = config.getfloat('SCRUFF', 'Z_SCORE_THRESHOLD')
    FILL_METHOD: str = config.get('SCRUFF', 'FILL_METHOD')
    NUMERIC_CONVERSION: str = config.get('SCRUFF', 'NUMERIC_CONVERSION')
    TEXT_OPTIONS: Dict[str, bool] = {
        'clean_text': config.getboolean('SCRUFF', 'CLEAN_TEXT'),
        'remove_accents': config.getboolean('SCRUFF', 'REMOVE_ACCENTS'),
        'to_lowercase': config.getboolean('SCRUFF', 'TO_LOWERCASE'),
        'remove_special_chars': config.getboolean('SCRUFF', 'REMOVE_SPECIAL_CHARS'),
        'remove_stopwords': config.getboolean('SCRUFF', 'REMOVE_STOPWORDS'),
        'lemmatize': config.getboolean('SCRUFF', 'LEMMATIZE')
    }

CONFIG = {
    'ui': UIConfig(),
    'data': DataConfig(),
    'errors': ErrorMessages(),
    'llm': LLMConfig(),
    'scruff': ScruffDefaults()
}
