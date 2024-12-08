<div align="center">
  <img src="assets/logo.png" alt="Scruffy the Data Janitor" width="200">
</div>

# Scruffy: The SLM Data Janitor  
##### `Scruffy 1.0.0-alpha`
## Serialized Data Transformation with Grammar-Constrained Small Language Models

Scruffy is a lightweight data preparation tool [built with the Python library Streamlit](https://streamlit.io/) which allows users to easily clean, transform, and prepare data using natural language requests. It leverages small language models (SLM) combined with constrained grammar files and dynamic system prompts to create consistent, serialized, JSON data operations which can be saved, shared, and reused across similar datasets. 

The models used in this application integrates with the SLM [Mistral-Nemo-12B-Instruct-2407](https://huggingface.co/mistralai/Mistral-Nemo-Instruct-2407), through [the API provided by Arli AI](https://www.arliai.com/quick-start) , but can be adapted/configured for other APIs or local models. This demonstration of the app uses a relatively small model to highlight the efficacy of restrictive grammars and system prompts that are automatically updated with real-time dataset information - including column names, data types, and sample values - ensuring the model has current context about the data structure it's working with. This app fills an important niche in the data processing landscape, combining a simplistic graphic user interface constructed using the open-source Python framework [Streamlit](https://streamlit.io/), with the capabilities of more complex programmatic tools. Scruffy can help data scientist and analysts who need to:
- Create reproducible data cleaning pipelines without writing code
- Document and share data transformation workflows saved in a standard, portable, JSON format
- Apply consistent data preparation steps across similar datasets
- Avoid the resource cost and infrastructure overhead of enterprise ETL software or large language models


# [Table of Contents](#table-of-contents)
- [**Installation and Configuration**](#installation-and-configuration)
  - [System Requirements](#system-requirements)
  - [Step by Step Installation](#step-by-step-installation)
  - [Configuration Files](#configuration-files)
    - [`config.py`](#configpy)
      - [Customizing Default Scruff Operations](#customizing-default-scruff-operations)
        - [Column Options](#column-options)
        - [Row Options](#row-options)
        - [Numeric Data Options](#numeric-data-options)
        - [Text Processing Options](#text-processing-options)
      - [Change and Modifying the Language Model](#change-and-modifying-the-language-model)
      - [Using Different LLMs or APIs](#using-different-llms-or-apis)
    - [`data/grammar.gbnf`](#datagrammargbnf)
    - [`data/system_prompt.md`](#datasystem_promptmd)
-  [Usage](#usage)
  - [Running Scruffy](#running-scruffy)
  - [Working with Data](#working-with-data)
    - [Uploading Files](#uploading-files)
    - [Creating Transformations](#creating-transformations)
    - [Applying Transformations](#applying-transformations)
    - [Saving and Sharing](#saving-and-sharing)
- [Command Schema Examples](#command-schema-examples)
  - [Basic AND Operations](#basic-and-operations)
  - [OR and XOR Operations](#or-and-xor-operations)
  - [Nested Logical Operations](#nested-logical-operations)
  - [Data Cleaning Operations](#data-cleaning-operations)
  - [Combined Filter and Clean Operations](#combined-filter-and-clean-operations)
  - [Batch Processing Operations](#batch-processing-operations)
- [Grammar Specification](#grammar-specification)
	- [Overview](#overview)
	- [Structure](#structure)
	- [Core Components](#core-components)
		- [Command Object](#command-object)
		- [Filter Operations](#filter-operations)
		- [Logical Operators](#logical-operators)
		- [Scruff Operations](#scruff-operations)
- [System Prompt Design](#system-prompt-design)
	- [Static Instructions](#static-instructions)
	- [Dynamic Context Generation](#dynamic-context-generation)
- [Additional Information](#additional-information)
	- [License](#license)
	- [Acknowledgments](#acknowledgements)
	- [Contact](#contact)
	
___
# Installation and Configuration
## System Requirements:
- Windows, macOS, or Linux
- Python Version: 3.7 or higher, earlier versions would require the [dataclasses backport](https://pypi.org/project/dataclasses/) available on PyPI:
- Dependencies: Listed in `requirements.txt`

### Step by Step Installation
#### 1. **Clone the Repository**:
   Open your terminal or command prompt and clone the Scruffy repo:
    ```bash
   git clone https://github.com/mhouser42/scruffy.git
     ```

#### 2. **Navigate to the Project Directory**:
   ```bash
   cd scruffy
   ```
#### 3. **Create a Virtual Environment (Recommended)**:
   You can use either `venv` or `conda` to create a virtual environment, then activate it.
##### Option 1: Using `venv`
###### **Create the Virtual Environment**:
```bash
python3 -m venv scruffy
```
###### **Activate the Virtual Environment:**
- macOS/Linux
```bash
  source scruffy/bin/activate
```
- Windows
```bash
scruffy\Scripts\activate
 ```
##### **Option 2: Using Conda**
###### Create the Conda Environment
```bash
conda create -n scruffy python=3.10
```
Be sure to replace with whatever python version (>3.7) you are currently using. 
###### Activate Conda Environment
```bash
conda activate scruffy
```
    
#### 4. **Install Dependencies**
   Install all required python packages using pip
   ```bash
   pip install -r requirements.txt
   ```

#### 5. **Set up an Arli AI API Key**
   - Obtain an API Key by signing up at [Arli AI](https://www.arliai.com/quick-start)
   - Create a file named `auth.txt` in the project root directory, and paste your API key into it.
   ```bash
   echo <YOUR_ARLI_AI_API_KEY> > auth.txt
   ```
   Replace `<YOUR_ARLI_AI_API_KEY>` with the one provided by Arli AI.
   - **Secure the `auth.txt` File:**
	   - Ensure that `auth.txt` is listed in your `.gitignore` file to prevent it from being tracked by Git.
#### 6. Download NLTK Data (If Required)
  - Scruffy uses the [NLTK](https://www.nltk.org/) Python library for text cleaning. Download the necessary datasets:
```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"
```

### Configuration Files
Scruffy's behavior can be customized through `config.py`, `data/grammar.gbnf`, and `data/system_prompt.md`. 

#### `config.py`:
##### **Customizing Default Scruff Operations**:
Modify the `ScruffDefaults` class to set default values for all cleaning operations
  
  1. **Column Options:** Control defaults for column standardization and handling
  ```python
    COLUMN_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'standardize_columns': True,     # Standardize column names to snake_case
            'drop_empty_columns': False,     # Keep empty columns by default
            'drop_duplicate_columns': True   # Remove duplicate columns
        }
    )
```
    

2. **Row Options:** Set defaults for handling missing values and duplicates
    ```python
    ROW_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'drop_na_rows': False,          # Keep rows with some NA values
            'drop_duplicate_rows': True     # Remove duplicate rows
        }
    )
    NA_THRESHOLD: int = 75                  # Drop rows with >75% missing values
    ```
    
3. **Numeric Data Options:** Configure numeric data processing
  ```python
    NUMERIC_OPTIONS: Dict[str, bool] = field(
        default_factory=lambda: {
            'normalize_numeric': False,      # Don't normalize by default
            'handle_outliers': False,        # Keep outliers by default
            'fill_numeric_na': True         # Fill missing numeric values
        }
    )
    Z_SCORE_THRESHOLD: float = 3.0          # Standard outlier threshold
    FILL_METHOD: str = 'median'             # Use median for filling NA values
    NUMERIC_CONVERSION: str = 'None'         # No automatic type conversion
 ```
4. **Text Processing Options:**
    ```python
    TEXT_OPTIONS: Dict[str, bool] = field(
      default_factory=lambda: {
          'remove_accents': False,         # Keep accents by default
          'to_lowercase': True,            # Convert to lowercase
          'remove_special_chars': False,   # Keep special characters
          'remove_stopwords': False,       # Keep stopwords
          'lemmatize': False              # No lemmatization by default
      }
    )
   ```
    
##### **Change and Modifying the Language Model**
  1.  Change the `MODEL_ID` under the `LLMConfig` class to switch between models available through the Arli API.
  2.  You can adjust models parameters by changing `MAX_TOKENS`, `TEMPERATURE`, `TOP_P` in the `LLMConfig` class.
##### **Using Different LLMs or APIs:**
  - Update the `LLM_HANDLER` to switch between different language model handlers (e.g., `arli`, `local`, `openai`).
  - **NOT CURRENTLY FUNCTIONAL IN ALPHA**

#### `data/grammar.gbnf`:
- Defines the JSON structure of the language model's output.
- **Editing the Grammar** 
  - **Not Recommended:** Modifying this file is not advised unless necessary. 
  - **Important:** The grammar ensures that the outputs from the language model are consistent and can be correctly parsed by the application. 
  - **Potential Issues:** 
    - Changes can lead to parsing errors. 
    - May result in unpredictable application behavior. Especially If not combined with System Prompt modification.

#### `data/system_prompt.md`:
- Contains instructions and examples provided to the language model.
- You can customize this to modify the influence of how the model interprets instructions and commands.

# Usage
## Running Scruffy

After completing the installation and configuration steps, you can start Scruffy by navigating to the project root directory and running:

```bash
streamlit run app.py
```

This will launch the Scruffy web interface in your default browser. If it doesn't open automatically, you can access it at `http://localhost:8501`.

## Working with Data

### Uploading Files
1.  **Upload Data**
    - Click the "Upload your CSV file" button in the main interface
    - Select your CSV file from your local system
    - The file will be loaded and analyzed, with column information and data previews displayed automatically
2. **Upload Schemas** (Optional):
   - Use the "Upload Command Schema" button in the command sidebar
   - Select a JSON file containing one or more transformation schemas
   - Valid schemas will be automatically added to your command list
   - Upload previously saved schemas to recreate transformations or share workflows

### Creating Transformations
Scruffy offers three main methods for creating commands for data manipulation:

1. **Natural Language Interface**:
   - Type your data transformation requirements in plain English
   - Scruffy will generate the appropriate JSON schema
   - Review and modify the generated schema if needed

2. **Filter Builder**:
   - Use the graphical interface to construct filters
   - Add conditions using dropdown menus and input fields
   - Combine conditions using AND, OR, and XOR operators

3. **Scruff Operations**:
   - A graphical interface to perform cleaning operations (Scruff).
   - This allows for either direct execution of the Scruff, or generating a command for later.

5. **Direct Schema Editing**:
   - Write or paste JSON schemas directly
   - Use the provided examples as templates
   - Validate schemas automatically before execution

### Applying Transformations
1. Select your desired transformation method
2. Configure the transformation parameters
3. Click "Execute" to apply the transformation
4. Review the results in the preview panel
5. Download the transformed data or continue with additional transformations

### Saving and Sharing
- Download transformed datasets as CSV files
- Export transformation schemas as JSON files
- Share schemas with team members for consistent data processing

# Command Schema Examples

Scruffy uses a JSON-based schema system to define data transformations. Below are examples of different operations you can perform, from basic filtering to complex data processing pipelines.

## AND Operations

AND operations allow you to combine multiple conditions where all must be true. When working with different columns, conditions can be listed directly in the filters object - they will automatically be combined with AND logic. For columns that need multiple filters, an explicit AND clause prevents duplicate keys.

```json
{
    "filename": "high_rated_episodes.csv",
    "description": "Find episodes with high viewership directed by specific directors",
    "filters": {
        "Directed By": {
            "op": "in",
            "value": ["Rich Moore", "Peter Avanzino"]
        },
        "AND": [
            {
                "U.S Viewers": {
                    "op": ">=",
                    "value": 10.0
                }
            },
            {
                "Air Date": {
                    "op": "<=",
                    "value": "1999-12-31"
                }
            }
        ]
    }
    }
```

## OR and XOR Operations

OR operations let you specify alternative conditions where any one condition can be true. XOR (exclusive OR) requires exactly one condition to be true, making it perfect for mutually exclusive categories.

```json
{
    "filename": "filtered_episodes.csv",
    "description": "Select episodes based on either high viewership or specific directors",
    "filters": {
        "Air Date": {
            "op": ">=",
            "value": "2000-01-01"
        },
        "OR": [
            {
                "U.S Viewers": {
                    "op": ">=",
                    "value": 8.0
                }
            },
            {
                "Directed By": {
                    "op": "in",
                    "value": ["Brian Sheesley", "Bret Haaland"]
                }
            }
        ],
        "XOR": [
            {
                "Episode Title": {
                    "op": "contains",
                    "value": "Part 1"
                }
            },
            {
                "Episode Title": {
                    "op": "contains",
                    "value": "Part 2"
                }
            }
        ]
    }
}
```

## Nested Logical Operations

For complex commands, you can nest conditional logic inside clauses. This allows for sophisticated combinations of logical operations. Use AND clauses inside OR or XOR clauses to group filters together and cluster conditions.

```json
{
    "filename": "complex_episode_filter.csv",
    "description": "Select specific episodes based on complex viewership and director patterns",
    "filters": {
        "OR": [
            {
                "U.S Viewers": {
                    "op": ">",
                    "value": 15.0
                }
            },
            {
                "AND": [
                    {
                        "Directed By": {
                            "op": "contains",
                            "value": "Avanzino"
                        }
                    },
                    {
                        "U.S Viewers": {
                            "op": "between",
                            "value": [8.0, 12.0]
                        }
                    }
                ]
            }
        ]
    }
}
```

## Data Cleaning Operations

Scruffy operations help you clean and standardize your data through a variety of transformations, including column standardization, missing value handling, text cleaning, and numeric normalization.

```json
    {
        "filename": "cleaned_futurama.csv",
        "description": "Clean and standardize Futurama episode data using default settings",
        "scruff": {
            "standardize_columns": true,
            "drop_empty_columns": false,
            "drop_duplicate_columns": true,
            "drop_na_rows": false,
            "drop_na_threshold": 50,
            "drop_duplicate_rows": true,
            "normalize_numeric": false,
            "handle_outliers": false,
            "z_score_threshold": 3.0,
            "fill_numeric_na": true,
            "fill_method": "median",
            "remove_accents": false,
            "to_lowercase": true,
            "remove_special_chars": false,
            "remove_stopwords": false,
            "lemmatize": false,
            "excluded_columns": ["Episode Title", "Air Date"],
            "numeric_conversion": "None"
        }
    }
``` 

## Combined Filter and Clean Operations

You can combine filtering and cleaning in a single command, first selecting the records you want, then applying cleaning operations to standardize and improve the filtered data.

```json
{
    "filename": "early_episodes_cleaned.csv",
    "description": "Filter early episodes and clean data format",
    "filters": {
        "Air Date": {
            "op": "<=",
            "value": "2000-12-31"
        },
        "U.S Viewers": {
            "op": "notna"
        }
    },
    "scruff": {
        "standardize_columns": true,
        "normalize_numeric": true,
        "fill_numeric_na": true,
        "fill_method": "mean",
        "remove_special_chars": true
    }
}
```

## Batch Processing Operations

When you need multiple output files from the same input data, you can specify an array of operations. Each operation creates its own output file, enabling multiple views of your data in a single command.

```json
[
    {
        "filename": "high_viewership.csv",
        "description": "Episodes with over 10 million viewers",
        "filters": {
            "U.S Viewers": {
                "op": ">=",
                "value": 10.0
            }
        },
        "scruff": {
            "standardize_columns": true,
            "normalize_numeric": true
        }
    },
    {
        "filename": "rich_moore_episodes.csv",
        "description": "Episodes directed by Rich Moore",
        "filters": {
            "Directed By": {
                "op": "contains",
                "value": "Rich Moore"
            }
        },
        "scruff": {
            "standardize_columns": true,
            "normalize_numeric": true
        }
    }
]
```

# Grammar Specification
## Overview

Grammar-constrained generation is a method that enforces strict output formatting rules during text generation, precluding the need for post-processing validation.
This approach can be particularly powerful when working with SLMs, as it allows them to spend resources on understanding and responding to commands versus managing output format compliance.

The Scruffy grammar file (`data/grammar.gbnf`) defines the formal structure of JSON used in Commands.  This ensures that all generated responses follow a consistent, parseable format compatible with Scruffy's processing engine.
More information on GBNF files and their specifications can be found [here](https://github.com/ggerganov/llama.cpp/tree/master/grammars).

## Structure

The grammar specifies:
- Valid schema structure and required fields
- Allowed operations and their syntax
- Data types and value formats
- Logical operation combinations and nesting rules

## Core Components

### Command Object

The root specifies the pattern for the overall output. Must be at beginning of file.
```gbnf
root ::= "[" ws? (command-object ws? ("," ws? command-object ws?)*)? ws? "]"
```

The base unit of a transformation schema:
```gbnf
command-object ::= "{" ws?
    "\"filename\"" ws? ":" ws? string ws? "," ws?
    "\"description\"" ws? ":" ws? string
    (ws? "," ws? filters-section)?
    (ws? "," ws? scruff-section)?
ws? "}"
```
### Filter Operations

Valid filtering operations
```gbnf
operation-type ::= "\"==\"" | "\"!=\"" | "\"<\"" | "\"<=\"" | "\">\"" | "\">=\"" |
    "\"in\"" | "\"not in\"" | "\"isna\"" | "\"notna\"" | "\"between\"" |
    "\"contains\"" | "\"+\"" | "\"-\"" | "\"*\"" | "\"/\"" | "\"//\"" |
    "\"%\"" | "\"**\"" | "\"&\"" | "\"|\"" | "\"^\"" | "\"~\"" | "\"<<\"" | "\">>\""
```
### Logical Operators

Rules for combining filters
```gbnf
logical-filter ::=
    ("\"AND\"" ws? ":" ws? "[" ws? filter-list ws? "]") |
    ("\"OR\"" ws? ":" ws? "[" ws? filter-list ws? "]") |
    ("\"XOR\"" ws? ":" ws? "[" ws? filter-list ws? "]")
```
### Scruff Operations

Cleaning operation specifications:
```gbnf
scruff-option ::= "\"" scruff-key "\"" ws? ":" ws? scruff-value

scruff-key ::= "standardize_columns" | "drop_empty_columns" | "drop_duplicate_columns" |
               "drop_na_rows" | "drop_duplicate_rows" | "normalize_numeric" |
               "handle_outliers" | "z_score_threshold" | "fill_numeric_na" | "fill_method" |
               "clean_text" | "remove_accents" | "to_lowercase" | "remove_special_chars" |
               "remove_stopwords" | "lemmatize" | "excluded_columns" | "numeric_conversion" |
               "drop_na_threshold"

scruff-value ::= boolean | number | string | array | null
```

# System Prompt Design

Scruffy employs a carefully designed system prompt that consists of two components: a static instruction set and dynamic context section. 
## Static Instructions

The static portion of the system prompt provides some foundational rules, operation definitions, and minimal examples that demonstrate the concepts outlined in the [command example section](#command-schema-examples) The entire static instructions can be viewed in `data/system_prompt.md`.
## Dynamic Context Generation

Each time a natural language query is processed, Scruffy automatically enhances the base system prompt with the selected DataFrame information. This gives the language model crucial context that helps it better construct commands. For example, when working with a television episode dataset, the dynamic context would appear as:

```
Current DataFrame Information:
<class "pandas.core.frame.DataFrame">
RangeIndex: 100 entries (0 to 99)
Data columns (total 5 columns):
 #   Column         Non-Null Count  Dtype  
---  ------         --------------  -----  
 0   Episode Title  100 non-null    object 
 1   Directed By    100 non-null    object 
 2   Air Date       100 non-null    object 
 3   U.S Viewers    84 non-null     float64
 4   index          100 non-null    int64  

DataFrame Shape: (100, 5)
Column Names: ['Episode Title', 'Directed By', 'Air Date', 'U.S Viewers', 'index']

Column Value Examples:
Episode Title: ['Proposition Infinity', 'Obsoletely Fabulous', 'The Route of All Evil', 'Bendless Love', 'Xmas Story']
Directed By: ['Crystal Chesney-Thompson', 'Dwayne Carey', 'Brian Sheesley', 'Swinton O. Scott III', 'Peter Avanzino']
Air Date: ['8-Jul-10', '27-Jul-03', '8-Dec-02', '11-Feb-01', '19-Dec-99']
U.S Viewers: [2.01, 4.57, 4.21, 8.2, 12.45]
index: [91, 67, 43, 37, 16]
```

In addition to basic column and data type information, random sample values are included for each column, so the model has concrete examples to work with while keeping the system prompt relatively concise. This assists the model in generating appropriate transformations, like handling missing values or date format validation.

The code for this can be found in the `LLMHandler` Class of `scruffy.py`:

```python
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
```

# Additional Information 
## License
Scruffy is available under the MIT License.
```
Scruffy: The SLM Data Janitor

Copyright (c) 2024 Matt Adam-Houser

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
## Acknowledgments 
- [Arli AI](https://www.arliai.com/) - For providing the API and language model integration. 
- [Streamlit](https://streamlit.io/) - For the flexible and user-friendly UI framework.
- [Georgi Gerganov](https://github.com/ggerganov) - For his [GBNF Guide](https://github.com/ggerganov/llama.cpp/tree/master/grammars).
- Kaggle
  - [Arian Mahin](https://www.kaggle.com/arianmahin) - For his [Futurama Dataset on Kaggle](https://www.kaggle.com/datasets/arianmahin/the-futurama-dataset)
  - [Waqar Ali](https://www.kaggle.com/waqi786) - For his [Cats Dataset](https://www.kaggle.com/datasets/waqi786/cats-dataset)

# References:

Beurer-Kellner, L., Fischer, M., & Vechev, M. (2024). _Guiding LLMs The Right Way: Fast, Non-Invasive Constrained Generation_ (arXiv:2403.06988; Version 1). arXiv. [https://doi.org/10.48550/arXiv.2403.06988](https://doi.org/10.48550/arXiv.2403.06988)

Eldan, R., & Li, Y. (2023). _TinyStories: How Small Can Language Models Be and Still Speak Coherent English?_ (arXiv:2305.07759). arXiv. [https://doi.org/10.48550/arXiv.2305.07759](https://doi.org/10.48550/arXiv.2305.07759)

Geng, S., Josifoski, M., Peyrard, M., & West, R. (2023, December 1). _Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning_. The 2023 Conference on Empirical Methods in Natural Language Processing. [https://openreview.net/forum?id=KkHY1WGDII](https://openreview.net/forum?id=KkHY1WGDII)

Hillier, D., Guertler, L., Tan, C., Agrawal, P., Ruirui, C., & Cheng, B. (2024). _Super Tiny Language Models_ (arXiv:2405.14159; Version 1). arXiv. [https://doi.org/10.48550/arXiv.2405.14159](https://doi.org/10.48550/arXiv.2405.14159)

Wang, B., Wang, Z., Wang, X., Cao, Y., Saurous, R. A., & Kim, Y. (n.d.). _Grammar Prompting for Domain-Specific Language Generation with Large Language Models_.

Zhang, L., Ergen, T., Logeswaran, L., Lee, M., & Jurgens, D. (2024). _SPRIG: Improving Large Language Model Performance by System Prompt Optimization_ (arXiv:2410.14826). arXiv. [https://doi.org/10.48550/arXiv.2410.14826](https://doi.org/10.48550/arXiv.2410.14826)
## Contact
For questions, feedback, or suggestions, feel free to reach out: 
- **Email:** [mhouser42@gmail.com](mailto:mhouser42@gmail.com) 
- **GitHub:** [@mhouser42](https://github.com/mhouser42)
