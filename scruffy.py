import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import requests
import streamlit as st
import json
import os
import io
import logging
import sys
from datetime import datetime
import re
import operator
import unicodedata
from typing import Dict, Any, List, Optional
from config.config import CONFIG


class Broom:
    def __init__(self):
        self._initialize_nltk()

    def _initialize_nltk(self):
        try:
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('stopwords')
            nltk.download('wordnet')

    @staticmethod
    def _is_monetary(series):
        if series.dtype == object:
            pattern = r'^\s*[$£€¥]\s*\d+\.?\d*|\d+\.?\d*\s*[$£€¥]\s*$'
            return series.str.match(pattern, na=False).any()
        return False

    @staticmethod
    def _clean_monetary(series):
        if series.dtype == object:
            cleaned = series.replace(r'[$£€¥,]', '', regex=True)
            return pd.to_numeric(cleaned, errors='coerce')
        return series

    @staticmethod
    def _normalize_numeric(series):
        if series.std() == 0:
            return series
        return (series - series.min()) / (series.max() - series.min())

    def _standardize_column_names(self, df):
        def to_snake_case(name):
            name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in str(name))
            return '_'.join(name.lower().split())
        df.columns = [to_snake_case(col) for col in df.columns]
        return df

    def _convert_numeric_types(self, df, conversion_options):
        df_copy = df.copy()
        for column, target_type in conversion_options.items():
            try:
                if target_type == 'int':
                    df_copy[column] = df_copy[column].astype('int64')
                elif target_type == 'float':
                    df_copy[column] = df_copy[column].astype('float64')
                elif target_type == 'string':
                    df_copy[column] = df_copy[column].astype(str)
            except Exception as e:
                st.warning(f'Could not convert {column} to {target_type}: {str(e)}')
        return df_copy

    def _clean_text(self, text, remove_accents=True, to_lowercase=True,
                    remove_special_chars=True, remove_stopwords=True, lemmatize=True):
        if pd.isna(text) or not isinstance(text, str):
            return ''
        if remove_accents:
            text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        if to_lowercase:
            text = text.lower()
        if remove_special_chars:
            text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        words = text.split()
        if remove_stopwords:
            stop_words = set(stopwords.words('english'))
            words = [word for word in words if word not in stop_words]
        if lemmatize:
            lemmatizer = WordNetLemmatizer()
            words = [lemmatizer.lemmatize(word) for word in words]
        return ' '.join(words)

    def _handle_column_operations(self, df, options):
        if options.get('standardize_columns'):
            df = self._standardize_column_names(df)
        if options.get('drop_empty_columns'):
            df = df.dropna(axis=1, how='all')
        if options.get('drop_duplicate_columns'):
            df = df.loc[:, ~df.columns.duplicated()]
        return df

    def _handle_row_operations(self, df, options):
        if options.get('drop_na_rows'):
            df = df.dropna(how='any')
        elif options.get('drop_na_threshold') is not None:
            threshold = options['drop_na_threshold'] / 100
            df = df.loc[df.isna().mean(axis=1) <= threshold]
        if options.get('drop_duplicate_rows'):
            df = df.drop_duplicates()
        return df

    def _handle_numeric_operations(self, df, options):
        if options.get('normalize_numeric') or options.get('handle_outliers') or options.get('fill_numeric_na'):
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for column in numeric_columns:
                if options.get('handle_outliers'):
                    z_threshold = options.get('z_score_threshold', 3.0)
                    z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
                    df = df[z_scores < z_threshold]
                if options.get('fill_numeric_na'):
                    fill_method = options.get('fill_method', 'mean')
                    if fill_method == 'mean':
                        df[column].fillna(df[column].mean(), inplace=True)
                    elif fill_method == 'median':
                        df[column].fillna(df[column].median(), inplace=True)
                    elif fill_method == 'zero':
                        df[column].fillna(0, inplace=True)
                    elif fill_method == 'forward':
                        df[column].fillna(method='ffill', inplace=True)
                    elif fill_method == 'backward':
                        df[column].fillna(method='bfill', inplace=True)
                if options.get('normalize_numeric'):
                    df[column] = self._normalize_numeric(df[column])
        if options.get('numeric_conversion') and options['numeric_conversion'] != 'None':
            conversion = options['numeric_conversion']
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if conversion == 'Int to Float':
                df[numeric_columns] = df[numeric_columns].astype(float)
            elif conversion == 'Float to Int':
                df[numeric_columns] = df[numeric_columns].astype(int)
            elif conversion == 'Numeric to String':
                df[numeric_columns] = df[numeric_columns].astype(str)
        return df

    def _handle_text_operations(self, df, options):
        text_columns = df.select_dtypes(include=[object]).columns
        for column in text_columns:
            df[column] = df[column].apply(
                lambda x: self._clean_text(
                    x,
                    remove_accents=options.get('remove_accents', False),
                    to_lowercase=options.get('to_lowercase', False),
                    remove_special_chars=options.get('remove_special_chars', False),
                    remove_stopwords=options.get('remove_stopwords', False),
                    lemmatize=options.get('lemmatize', False)
                )
            )
        return df

    def _handle_value_replacement(self, df, options):
        if options.get('replace_values'):
            replacements = options['replace_values']
            for column, value_map in replacements.items():
                if column in df.columns:
                    df[column] = df[column].replace(value_map)

        if options.get('replace_all_values'):
            value_map = options['replace_all_values']
            df = df.replace(value_map)

        return df

    def scruff(self, df_to_clean, options=None):
        excluded_columns = options.get('excluded_columns', []) if options else []
        columns_to_process = [col for col in df_to_clean.columns if col not in excluded_columns]

        df_to_clean_excluded = df_to_clean[excluded_columns].copy() if excluded_columns else pd.DataFrame()
        df_to_clean_processed = df_to_clean[columns_to_process].copy()

        cleaned_df_processed = (
            df_to_clean_processed
            .pipe(lambda x: self._handle_column_operations(x, options))
            .pipe(lambda x: self._handle_row_operations(x, options))
            .pipe(lambda x: self._handle_numeric_operations(x, options))
            .pipe(lambda x: self._handle_text_operations(x, options))
            .pipe(lambda x: self._handle_value_replacement(x, options))
        )

        cleaned_df = pd.concat([cleaned_df_processed, df_to_clean_excluded], axis=1)
        return cleaned_df

class Vacuum:
    def __init__(self):
        self.OPS = self._get_OPS()

    def _get_OPS(self):
        return {
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            'in': lambda x, y: x.isin(y if isinstance(y, list) else [y]),
            'not in': lambda x, y: ~x.isin(y if isinstance(y, list) else [y]),
            'isna': lambda x: x.isna(),
            'notna': lambda x: x.notna(),
            'between': lambda x, y: x.between(y[0], y[1]),
            'contains': lambda x, y: x.str.contains(y, case=False, na=False),
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '//': operator.floordiv,
            '%': operator.mod,
            '**': operator.pow,
            '&': operator.and_,
            '|': operator.or_,
            '^': operator.xor,
            '~': operator.invert,
            '<<': operator.lshift,
            '>>': operator.rshift
        }

    def _convert_date_series(self, series, value):
        try:
            series = pd.to_datetime(series, format='mixed')
            value = pd.to_datetime(value)
            return series, value, True
        except:
            return series, value, False

    def apply_filter(self, df, column, condition):
        if column not in df.columns:
            raise ValueError(f'Column "{column}" not found in DataFrame.')
        op = condition['op']
        value = condition.get('value')
        if op not in self.OPS:
            raise ValueError(f'Unsupported operation "{op}"')
        series = df[column]
        if 'date' in column.lower():
            series, value, is_date = self._convert_date_series(series, value)
        if op in ['isna', 'notna']:
            return self.OPS[op](series)
        elif value is not None:
            return self.OPS[op](series, value)
        else:
            raise ValueError(f'Missing value for operation "{op}" on column "{column}"')

    def build_mask(self, df, filters):
        if isinstance(filters, dict):
            if any(op in filters for op in ['OR', 'XOR', 'AND']):
                for logical_op in ['OR', 'XOR', 'AND']:
                    if logical_op in filters:
                        conditions = filters[logical_op]
                        if isinstance(conditions, list):
                            masks = [self.build_mask(df, condition) for condition in conditions]
                        elif isinstance(conditions, dict):
                            masks = [self.build_mask(df, conditions)]
                        else:
                            raise ValueError(f'Invalid format for {logical_op} conditions: {conditions}')
                        if logical_op == 'OR':
                            return pd.concat(masks, axis=1).any(axis=1)
                        elif logical_op == 'XOR':
                            sum_masks = pd.concat(masks, axis=1).sum(axis=1)
                            return sum_masks == 1
                        elif logical_op == 'AND':
                            return pd.concat(masks, axis=1).all(axis=1)
            else:
                masks = []
                for key, condition in filters.items():
                    if key in ['OR', 'XOR', 'AND']:
                        mask = self.build_mask(df, {key: condition})
                        masks.append(mask)
                    elif isinstance(condition, dict) and 'op' in condition:
                        masks.append(self.apply_filter(df, key, condition))
                    else:
                        masks.append(self.build_mask(df, condition))
                return pd.concat(masks, axis=1).all(axis=1)
        else:
            raise ValueError(f'Invalid filter format: {filters}')

    def apply_command(self, df, command, get_count=False):
        filters = command.get('filters')
        if filters is None:
            filtered_df = df
        else:
            mask = self.build_mask(df, filters)
            filtered_df = df[mask]
        return (filtered_df, len(filtered_df)) if get_count else filtered_df

    def report_command(self, filter_df, row_count=0):
        report = '\nCommand results:\n'
        if filter_df is not None and not filter_df.empty:
            report += 'First five rows of filtered DataFrame:\n'
            report += filter_df.head().to_string() + '\n'
            report += f'Total number of rows for filtered DataFrame: {row_count}\n\n'
            report += 'Summary statistics:\n'
            report += filter_df.describe(include='all').to_string() + '\n\n'
            report += 'Data types:\n'
            report += filter_df.dtypes.to_string() + '\n\n'
            report += 'Missing values per column:\n'
            report += filter_df.isna().sum().to_string() + '\n\n'
            report += 'Unique values per column:\n'
            for column in filter_df.columns:
                unique_values = filter_df[column].nunique()
                report += f'{column}: {unique_values} unique values\n'
        else:
            report += 'No rows match the given criteria.\n'
        if row_count > 0:
            report += f'\nTotal number of rows for filtered DataFrame: {row_count}\n'
        return report

    def apply_commands(self, df, commands, get_counts=False, report_commands=False, save_dfs=False):
        dfs = []
        counts = [] if get_counts else None
        for command in commands:
            filename = command.get('filename', f'{command.get("description", "no_description")}.csv')
            description = command.get('description', 'No description provided')
            result = self.apply_command(df, command=command, get_count=get_counts)
            if get_counts:
                filter_df, count = result
                counts.append(count)
            else:
                filter_df = result
            dfs.append(filter_df)
            if report_commands:
                report = self.report_command(filter_df, count) if get_counts else self.report_command(filter_df)
                dfs.append(report)
            if save_dfs:
                output_dir = 'data/output_dfs'
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)
                filter_df.to_csv(output_path, index=False)
        return (dfs, counts) if get_counts else dfs

class LLMHandler:
    def __init__(self):
        self.api_key = self._load_token()
        self.api_url = CONFIG['llm'].API_URI
        self.model = CONFIG['llm'].MODEL_ID
        self.max_tokens = CONFIG['llm'].MAX_TOKENS
        self.temperature = CONFIG['llm'].TEMPERATURE
        self.top_p = CONFIG['llm'].TOP_P
        self._base_system_prompt = None
        self._current_system_prompt = None
        self.grammar = self._load_grammar()
        self.load_system_prompt()

    def _load_token(self) -> str:
        with open('auth.txt', 'r') as f:
            return f.read().strip()

    def _load_grammar(self) -> str:
        with open('data/grammar.gbnf', 'r') as f:
            return f.read()

    def load_system_prompt(self) -> None:
        with open('data/system_prompt.md', 'r') as f:
            self._base_system_prompt = f.read()
            self._current_system_prompt = self._base_system_prompt

    def get_column_context(self, df, max_samples=5):
        context = {}
        for column in df.columns:
            unique_values = df[column].dropna().unique()
            if len(unique_values) > max_samples:
                sampled_values = np.random.choice(unique_values, max_samples, replace=False)
                context[column] = sampled_values.tolist()
            else:
                context[column] = unique_values.tolist()
        return context

    def update_system_prompt_with_df(self, df) -> None:
        if df is None:
            return
        buffer = io.StringIO()
        df.info(buf=buffer)
        df_info = buffer.getvalue()
        column_context = self.get_column_context(df)
        context_str = '\nColumn Value Examples:\n'
        for column, values in column_context.items():
            context_str += f'{column}: {values}\n'
        self._current_system_prompt = (
                self._base_system_prompt +
                f'\n\nCurrent DataFrame Information:\n{df_info}\n' +
                f'\nDataFrame Shape: {df.shape}\n' +
                f'Column Names: {list(df.columns)}\n' +
                context_str
        )

    @property
    def system_prompt(self) -> str:
        return self._current_system_prompt

    def generate_response(self, user_input: str) -> List[Dict[str, Any]]:
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self._current_system_prompt},
                {'role': 'user', 'content': user_input}
            ],
            'temperature': 0.2,
            'top_p': 0.9,
            'top_k': 40,
            'max_tokens': 1024,
            'repetition_penalty': 1.1,
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code != 200:
            error_message = f'API command failed: {response.status_code}'
            try:
                error_detail = response.json()
                error_message += f' - {error_detail}'
            except:
                error_message += f' - {response.text}'
            raise ValueError(error_message)
        content = response.json()['choices'][0]['message']['content']
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError('No valid JSON array found in response')

class DataLogger:
    _instance = None
    def __new__(cls, name: str = 'data_cleaning'):
        if cls._instance is None:
            cls._instance = super(DataLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    def __init__(self, name: str = 'data_cleaning'):
        if not self._initialized:
            self.logger = self._setup_logger(name)
            self._initialized = True
    def _setup_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if logger.hasHandlers():
            logger.handlers.clear()
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(f'logs/data_cleaning_{current_time}.log')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        return logger
    def log_data_info(self, df: pd.DataFrame, operation_name: str) -> None:
        log_id = f'{operation_name}_{df.shape}'
        if hasattr(self, '_last_log_id') and self._last_log_id == log_id:
            return
        self._last_log_id = log_id
        info = {
            'operation': operation_name,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'na_counts': df.isna().sum().to_dict(),
            'memory_usage': f'{df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB'
        }
        self.logger.info(f'Data Info - {operation_name}:')
        for key, value in info.items():
            self.logger.info(f'  {key}: {value}')
    def log_operation_result(self, operation: str, initial_shape: tuple, final_shape: tuple, details: Optional[Dict[str, Any]] = None) -> None:
        self.logger.info(f'{operation} changed shape from {initial_shape} to {final_shape}')
        if details:
            for key, value in details.items():
                self.logger.info(f'  {key}: {value}')
    def log_error(self, error_message: str) -> None:
        self.logger.error(error_message)
    def get_logs(self) -> str:
        log_output = []
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                with open(handler.baseFilename, 'r') as f:
                    log_output = f.readlines()
        return ''.join(log_output)

class Scruffy:
    def __init__(self):
        from version_control.controller import VersionController
        self.broom = Broom()
        self.vacuum = Vacuum()
        self.llm = LLMHandler()
        self.logger = DataLogger()
        self.filename = None
        self.orig_df = None
        self.curr_df = None
        self.history = []
        self.version_controller = VersionController()
        self.version_controller.load_from_session()

    def _get_current_df(self):
        df_versions = self.version_controller.get_dataframes()
        selected_version = self.version_controller.get_selected_version()
        if selected_version and selected_version in df_versions:
            return df_versions[selected_version]
        return self.curr_df

    def _update_system_prompt(self, df=None):
        df_to_use = df if df is not None else self._get_current_df()
        if df_to_use is not None:
            self.llm.update_system_prompt_with_df(df_to_use)

    def load_data(self, df, filename):
        self.logger.log_data_info(df, 'Initial Load')
        self.orig_df = df.copy()
        self.curr_df = df.copy()
        self.history = []
        self.filename = filename.rsplit('.', 1)[0]
        self.version_controller.add_version(filename, self.orig_df.copy())
        self.version_controller.set_selected_version(filename)
        st.session_state['df'] = self.orig_df.copy()
        self._update_system_prompt(df)

    def scruff(self, df=None, options=None):
        self.logger.log_data_info(self._get_current_df(), 'Before Scruff')
        df_to_clean = df if df is not None else self._get_current_df()

        excluded_columns = options.get('excluded_columns', [])
        columns_to_process = [col for col in df_to_clean.columns if col not in excluded_columns]

        df_to_clean_excluded = df_to_clean[excluded_columns].copy() if excluded_columns else pd.DataFrame()
        df_to_clean_processed = df_to_clean[columns_to_process].copy()

        cleaned_df_processed = self.broom.scruff(
            df_to_clean_processed,
            options=options
        )

        cleaned_df = pd.concat([cleaned_df_processed, df_to_clean_excluded], axis=1)

        self.logger.log_operation_result(
            'Scruffing...',
            df_to_clean.shape,
            cleaned_df.shape,
            details=options
        )

        if df is None:
            self.curr_df = cleaned_df.copy()
            self.history.append(('clean', None))

            current_version = self.version_controller.get_selected_version()
            base_name = current_version.rsplit('.', 1)[0]
            scruffed_filename = f'{base_name}_scruffed.csv'

            self.version_controller.add_version(scruffed_filename, cleaned_df.copy())

        return cleaned_df


    def reset(self):
        if self.orig_df is not None:
            self.curr_df = self.orig_df.copy()
            self.history = []
            from version_control.controller import VersionController
            self.version_controller = VersionController()
            self.version_controller.load_from_session()
            st.session_state['dataframe_versions'] = {'Original': self.orig_df.copy()}
            st.session_state['selected_version'] = 'Original'
            self._update_system_prompt(self.orig_df)

    def undo(self):
        if self.history:
            self.history.pop()
            self.curr_df = self.orig_df.copy()
            from version_control.controller import VersionController
            self.version_controller = VersionController()
            self.version_controller.load_from_session()
            st.session_state['dataframe_versions'] = {'Original': self.orig_df.copy()}
            for op_type, op_data in self.history:
                if op_type == 'clean':
                    self.scruff()
                elif op_type == 'command':
                    self.apply_command(op_data)
            st.session_state['selected_version'] = list(st.session_state['dataframe_versions'].keys())[-1]
            self._update_system_prompt(self.curr_df)

    def apply_command(self, command, df=None):
        current_df = df if df is not None else self._get_current_df()

        filters = command.get('filters')
        if filters:
            current_df = self.vacuum.apply_command(current_df, command)

        scruff_options = command.get('scruff')
        if scruff_options:
            current_df = self.broom.scruff(current_df, options=scruff_options)

        if df is None:
            version_name = command.get('filename', 'unnamed_command.csv')
            self.version_controller.add_version(version_name, current_df)
            st.session_state['df'] = current_df

        return current_df


    def apply_commands(self, commands, get_counts=False):
        results = []
        counts = [] if get_counts else None
        current_df = self._get_current_df()
        for command in commands:
            df_to_use = current_df.copy()
            scruff_options = command.get('scruff')
            if scruff_options:
                df_to_use = self.broom.scruff(df_to_use, options=scruff_options)
            filters = command.get('filters')
            if filters:
                try:
                    if get_counts:
                        result = self.vacuum.apply_command(df_to_use, command, get_count=True)
                        filter_df, count = result
                        results.append(filter_df)
                        counts.append(count)
                    else:
                        filter_df = self.vacuum.apply_command(df_to_use, command)
                        results.append(filter_df)
                    if filter_df is not None:
                        version_name = command.get('filename', 'unnamed.csv')
                        self.version_controller.add_version(version_name, filter_df.copy())
                except Exception as e:
                    st.error(f'Error applying command: {str(e)}')
                    if get_counts:
                        results.append(pd.DataFrame())
                        counts.append(0)
                    else:
                        results.append(pd.DataFrame())
            else:
                if get_counts:
                    results.append(df_to_use)
                    counts.append(len(df_to_use))
                else:
                    results.append(df_to_use)
                version_name = command.get('filename', 'unnamed.csv')
                self.version_controller.add_version(version_name, df_to_use.copy())
        return (results, counts) if get_counts else results

    def generate_response(self, user_input: str) -> List[Dict[str, Any]]:
        self._update_system_prompt()
        return self.llm.generate_response(user_input)