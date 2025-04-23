#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

DEFAULT_DATE = "1999-09-19"
DEFAULT_TITLE = "UnknownTitle"
DEFAULT_COUNTRY = "UnknownCountry"

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

def clean_movie_country_csv(input_file, output_file):
    """
    Cleans the MovieCountry.csv file such that:
      - 'title', 'releaseDate', and 'country' are not null.
      - If missing, assign defaults:
          * title -> DEFAULT_TITLE
          * releaseDate -> DEFAULT_DATE (parsed to YYYY-MM-DD if possible)
          * country -> DEFAULT_COUNTRY
      - Removes duplicates based on (title, releaseDate, country).
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
        # Replace invalid or missing date with DEFAULT_DATE
        df['releaseDate_clean'] = df['releaseDate_clean'].fillna(DEFAULT_DATE)
        df['releaseDate'] = df['releaseDate_clean']
        df.drop(columns=['releaseDate_clean'], inplace=True)
    
    # Clean 'country'
    if 'country' not in df.columns:
        df['country'] = DEFAULT_COUNTRY
    else:
        df['country'] = df['country'].astype(str).str.strip()
        df['country'] = df['country'].replace('', DEFAULT_COUNTRY)
        df['country'] = df['country'].fillna(DEFAULT_COUNTRY)
        # If you want to limit to 99 characters (similar to productionCompany),
        # uncomment the line below:
        # df['country'] = df['country'].str.slice(0, 99)
    
    # Remove duplicates based on (title, releaseDate, country)
    df = df.drop_duplicates(subset=['title', 'releaseDate', 'country'])
    
    final_count = len(df)
    print(f"Initial rows in {input_file}: {initial_count}")
    print(f"Final rows after cleaning: {final_count}")
    
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_csv = "MovieCountry.csv"          # Original CSV
    output_csv = "MovieCountry_clean.csv"   # Cleaned CSV
    clean_movie_country_csv(input_csv, output_csv)
