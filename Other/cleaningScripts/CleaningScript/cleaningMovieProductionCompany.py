#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

DEFAULT_DATE = "1999-09-19"
DEFAULT_TITLE = "UnknownTitle"
DEFAULT_COMPANY = "UnknownProductionCompany"

def robust_parse_date(date_str):
    """
    Attempts to parse a date string into YYYY-MM-DD using several formats.
    If it cannot parse, returns None.
    """
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    
    date_str = str(date_str).strip()
    date_formats = [
        '%Y-%m-%d',      # e.g., 1980-05-16
        '%d %B %Y',      # e.g., 16 May 1980
        '%d %b %Y',      # e.g., 16 May 1980 (short month)
        '%d/%m/%Y',      # e.g., 16/05/1980
        '%m/%d/%Y'       # e.g., 05/16/1980
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_movie_production_company_csv(input_file, output_file):
    """
    Cleans the MovieProductionCompany.csv file so that:
      - 'title', 'releaseDate', and 'productionCompany' are not null.
      - If missing, assign default values:
          * title -> DEFAULT_TITLE
          * productionCompany -> DEFAULT_COMPANY (limited to 99 characters)
          * releaseDate -> DEFAULT_DATE (and parsed to YYYY-MM-DD)
      - releaseDate is parsed; if invalid, use DEFAULT_DATE.
      - Duplicate rows (same title, releaseDate, productionCompany) are removed.
      - Prints initial and final row counts.
    """
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # Strip column names of whitespace
    df.columns = df.columns.str.strip()
    
    # Clean 'title'
    if 'title' not in df.columns:
        df['title'] = DEFAULT_TITLE
    else:
        df['title'] = df['title'].astype(str).str.strip()
        df['title'] = df['title'].replace('', DEFAULT_TITLE)
        df['title'] = df['title'].fillna(DEFAULT_TITLE)
    
    # Clean 'releaseDate'
    if 'releaseDate' not in df.columns:
        df['releaseDate'] = DEFAULT_DATE
    else:
        df['releaseDate_clean'] = df['releaseDate'].apply(robust_parse_date)
        df['releaseDate_clean'] = df['releaseDate_clean'].fillna(DEFAULT_DATE)
        df['releaseDate'] = df['releaseDate_clean']
        df.drop(columns=['releaseDate_clean'], inplace=True)
    
    # Clean 'productionCompany'
    if 'productionCompany' not in df.columns:
        df['productionCompany'] = DEFAULT_COMPANY
    else:
        df['productionCompany'] = df['productionCompany'].astype(str).str.strip()
        df['productionCompany'] = df['productionCompany'].replace('', DEFAULT_COMPANY)
        df['productionCompany'] = df['productionCompany'].fillna(DEFAULT_COMPANY)
        # Limit production company name to 99 characters
        df['productionCompany'] = df['productionCompany'].str.slice(0, 99)
    
    # Remove duplicates based on (title, releaseDate, productionCompany)
    df = df.drop_duplicates(subset=['title', 'releaseDate', 'productionCompany'])
    
    final_count = len(df)
    print(f"Initial rows in {input_file}: {initial_count}")
    print(f"Final rows after cleaning: {final_count}")
    
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_csv = "MovieProductionCompany.csv"       # Original CSV file
    output_csv = "MovieProductionCompany_clean.csv" # Cleaned output
    clean_movie_production_company_csv(input_csv, output_csv)
