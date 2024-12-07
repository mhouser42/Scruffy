from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class UIConfig:
    TABS: Dict[str, str] = field(
        default_factory=lambda: {
            'natural_language': '️Natural Language',
            'filter_builder': 'Filter Builder',
            'scruff_options': 'Scruff Options',
        }
    )

    DEFAULT_TAB: str = 'natural_language'

    SCHEMA_TABS: List[str] = field(
        default_factory=lambda: [
            'Basic AND',
            'OR & XOR',
            'Nested Logic',
            'Data Cleaning',
            'Combined Ops',
            'Batch Processing'
        ]
    )

    SCHEMA_EXAMPLES: Dict[str, str] = field(
        default_factory=lambda: {
            'Basic AND': 'and_operations',
            'OR & XOR': 'or_xor_operations',
            'Nested Logic': 'nested_operations',
            'Data Cleaning': 'scruffy_operations',
            'Combined Ops': 'combined_filter_scruff',
            'Batch Processing': 'batch_processing'
        }
    )

    SCHEMA_DESCRIPTIONS: Dict[str, str] = field(
        default_factory=lambda: {
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
    )

@dataclass
class DataConfig:
    DEFAULT_FILENAME: str = 'filtered_data.csv'
    SUPPORTED_FILE_TYPES: List[str] = field(
        default_factory=lambda: ['csv']
    )
    EXAMPLE_SCHEMAS_PATH: str = 'data/commands/example'

@dataclass
class ErrorMessages:
    FILE_UPLOAD_ERROR: str = 'Error reading CSV file: {}'
    COMMAND_EXECUTION_ERROR: str = 'Error executing command: {}'
    JSON_PARSE_ERROR: str = 'Invalid JSON: {}'
    VALIDATION_ERROR: str = 'Validation error: {}'

@dataclass
class LLMConfig:
    MODEL_ID: str = 'Mistral-Nemo-12B-Instruct-2407'
    API_URI: str = 'https://api.arliai.com/v1/chat/completions'
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.6
    TOP_P: float = 0.9


@dataclass
class ScruffDefaults:
    COLUMN_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'standardize_columns': True,
            'drop_empty_columns': False,
            'drop_duplicate_columns': True
        }
    )

    ROW_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'drop_na_rows': False,
            'drop_duplicate_rows': True
        }
    )

    NA_THRESHOLD: int = 50

    NUMERIC_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'normalize_numeric': False,
            'handle_outliers': False,
            'fill_numeric_na': True
        }
    )

    Z_SCORE_THRESHOLD: float = 3.0

    FILL_METHOD: str = 'median'
    NUMERIC_CONVERSION: str = 'None'

    TEXT_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'clean_text': False,
            'remove_accents': False,
            'to_lowercase': True,
            'remove_special_chars': False,
            'remove_stopwords': False,
            'lemmatize': False
        }
    )

CONFIG = {
    'ui': UIConfig(),
    'data': DataConfig(),
    'errors': ErrorMessages(),
    'llm': LLMConfig(),
    'scruff': ScruffDefaults()
}