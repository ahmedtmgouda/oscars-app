#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

DEFAULT_BIRTH_DATE = "1999-09-19"

def robust_parse_date(date_str):
    """
    Attempt to parse a date string into YYYY-MM-DD.
    Handles:
      - '1980-05-16'
      - '16 May 1980' or '16 May 1980'
      - If only a 4-digit year is provided, returns DEFAULT_BIRTH_DATE.
    If the date cannot be parsed, returns None.
    """
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    
    date_str = str(date_str).strip()
    
    # If exactly a 4-digit year is provided, use default instead.
    if len(date_str) == 4 and date_str.isdigit():
        return DEFAULT_BIRTH_DATE

    date_formats = [
        '%Y-%m-%d',      # 1980-05-16
        '%d %B %Y',      # 16 May 1980
        '%d %b %Y',      # 16 May 1980 (short month)
        '%d/%m/%Y',      # 16/05/1980
        '%m/%d/%Y'       # 05/16/1980
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_country(value):
    """
    Check if the country value consists of letters, spaces, or common punctuation.
    If it contains unexpected symbols or numbers, return an empty string.
    """
    if pd.isna(value):
        return ""
    value = str(value).strip()
    # If the value matches a pattern of letters, spaces, and maybe hyphens, keep it.
    if re.fullmatch(r"[A-Za-z\s\-]+", value):
        return value
    else:
        return ""

def clean_person_csv(input_file, output_file):
    """
    Cleans Person.csv:
      - Ensures person_first and person_last are non-empty (trims whitespace).
      - Parses person_birth_date; if missing or unparseable, uses DEFAULT_BIRTH_DATE.
      - Parses death_date similarly (if provided); leaves as None if unparseable.
      - Cleans person_country_of_birth: if it doesn't match allowed characters, set to empty.
      - Drops duplicates based on (person_first, person_last, person_birth_date).
      - Prints initial and final row counts.
    """
    # Load the CSV into a DataFrame, specifying encoding to avoid ascii errors.
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    initial_count = len(df)
    
    # Trim first and last names
    df['person_first'] = df['person_first'].astype(str).str.strip()
    df['person_last'] = df['person_last'].astype(str).str.strip()
    
    # Replace missing or empty names with NaN and drop rows where names are empty
    df.replace("", pd.NA, inplace=True)
    df.dropna(subset=['person_first', 'person_last'], inplace=True)
    
    # Clean the birth date:
    # Try to parse; if fails, assign default.
    df['person_birth_date'] = df['person_birth_date'].apply(lambda x: robust_parse_date(x) or DEFAULT_BIRTH_DATE)
    
    # Clean the death date if present: if unparseable, set to None.
    if 'death_date' in df.columns:
        df['death_date'] = df['death_date'].apply(lambda x: robust_parse_date(x) if pd.notna(x) and str(x).strip() != "" else None)
    
    # Clean the country column if it exists
    if 'person_country_of_birth' in df.columns:
        df['person_country_of_birth'] = df['person_country_of_birth'].apply(clean_country)
    
    # Remove duplicate rows based on (person_first, person_last, person_birth_date)
    df = df.drop_duplicates(subset=['person_first', 'person_last', 'person_birth_date'])
    
    final_count = len(df)
    print(f"Initial rows in {input_file}: {initial_count}")
    print(f"Final rows after cleaning: {final_count}")
    
    # Save cleaned DataFrame to CSV
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_csv = "/Users/ahmedgouda/Desktop/DatabaseM2/cleaningScripts/DirtyCsvFiles/Person.csv"           # Original CSV file name
    output_csv = "/Users/ahmedgouda/Desktop/DatabaseM2/csvFilesClean/Person_clean.csv"    # Output cleaned CSV file name
    clean_person_csv(input_csv, output_csv)
