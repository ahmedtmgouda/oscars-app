#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

# Default release date if missing or unparseable.
DEFAULT_RELEASE_DATE = "1999-09-19"

def robust_parse_release_date(date_str):
    """
    Attempts to parse a release date string into YYYY-MM-DD.
    Tries several formats; if parsing fails, returns None.
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

def clean_numeric_field(value):
    """
    Cleans a numeric field that may contain currency symbols, commas, and words like "million" or "billion".
    After detecting multipliers, it removes remaining alphabetical characters.
    Returns a float rounded to two decimals, or None if conversion fails.
    """
    if pd.isna(value):
        return None
    val = str(value)
    
    # Remove common currency symbols and whitespace
    val = val.replace("$", "").replace("€", "").replace("£", "").strip()
    
    # Set multiplier based on words.
    multiplier = 1.0
    val_lower = val.lower()
    if "million" in val_lower:
        multiplier = 1e6
        val = re.sub(r'(?i)million', '', val)
    elif "billion" in val_lower:
        multiplier = 1e9
        val = re.sub(r'(?i)billion', '', val)
    
    # Remove any alphabetical characters now.
    val = re.sub(r'[A-Za-z]', '', val)
    
    # Remove commas and extra spaces
    val = val.replace(",", "").strip()
    
    try:
        num = float(val)
        return round(num * multiplier, 2)
    except ValueError:
        return None

def clean_movie_csv(input_file, output_file):
    """
    Cleans the movie CSV file so that:
      - 'title' is non-empty.
      - 'releaseDate' is parsed to YYYY-MM-DD; if missing or unparseable, uses default.
      - 'budget' and 'boxOffice' are cleaned and converted to decimals.
      - 'runTime' is converted to an integer.
      - 'movieLanguage' is trimmed.
      - Duplicate rows (same title and releaseDate) are dropped.
    Prints the row count before and after cleaning.
    """
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # Debug: Print columns in CSV.
    print("Columns in CSV:", df.columns.tolist())
    
    # Rename columns if necessary:
    df.columns = df.columns.str.strip()  # Remove extra whitespace in column names
    if 'releasedate' in df.columns and 'releaseDate' not in df.columns:
        df.rename(columns={'releasedate': 'releaseDate'}, inplace=True)
    elif 'release_date' in df.columns and 'releaseDate' not in df.columns:
        df.rename(columns={'release_date': 'releaseDate'}, inplace=True)
    
    # Ensure title exists and trim whitespace.
    df['title'] = df['title'].astype(str).str.strip()
    df = df[df['title'] != ""]
    
    # Clean and standardize the releaseDate.
    df['releaseDate_clean'] = df['releaseDate'].apply(robust_parse_release_date)
    df['releaseDate_clean'] = df['releaseDate_clean'].fillna(DEFAULT_RELEASE_DATE)
    df['releaseDate'] = df['releaseDate_clean']
    df.drop(columns=['releaseDate_clean'], inplace=True)
    
    # Clean budget and boxOffice columns.
    if 'budget' in df.columns:
        df['budget'] = df['budget'].apply(clean_numeric_field)
    if 'boxOffice' in df.columns:
        df['boxOffice'] = df['boxOffice'].apply(clean_numeric_field)
    
    # Clean runTime: convert to numeric, fill NaN with 0, then convert to integer.
    if 'runTime' in df.columns:
        df['runTime'] = pd.to_numeric(df['runTime'], errors='coerce').fillna(0).astype(int)
    
    # Clean movieLanguage by trimming whitespace.
    if 'movieLanguage' in df.columns:
        df['movieLanguage'] = df['movieLanguage'].astype(str).str.strip()
    
    # Drop duplicates based on (title, releaseDate)
    df = df.drop_duplicates(subset=['title', 'releaseDate'])
    
    final_count = len(df)
    print(f"Initial rows in {input_file}: {initial_count}")
    print(f"Final rows after cleaning: {final_count}")
    
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_csv = "movie.csv"         # Your original CSV file name
    output_csv = "movie_clean.csv"  # Output cleaned CSV file name
    clean_movie_csv(input_csv, output_csv)
