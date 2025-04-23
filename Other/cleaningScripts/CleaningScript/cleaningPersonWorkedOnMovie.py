#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

# Default values
DEFAULT_DATE = "1999-09-19"
DEFAULT_FIRST_NAME = "UnknownFirst"
DEFAULT_LAST_NAME = "UnknownLast"
DEFAULT_MOVIE_TITLE = "UnknownMovie"
DEFAULT_ROLE = "UnknownRole"

def robust_parse_date(date_str):
    """
    Attempts to parse a date string into YYYY-MM-DD using several formats.
    If parsing fails or the string is incomplete, returns None.
    """
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    date_str = str(date_str).strip()
    
    date_formats = [
        '%Y-%m-%d',      # e.g. 1980-05-16
        '%d %B %Y',      # e.g. 16 May 1980
        '%d %b %Y',      # e.g. 16 May 1980 (short month)
        '%d/%m/%Y',      # e.g. 16/05/1980
        '%m/%d/%Y'       # e.g. 05/16/1980
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def clean_person_worked_on_movie_csv(input_file, output_file):
    """
    Cleans PersonWorkedOnMovie.csv so that:
      - personFirstName, personLastName, personBirthDate, movieTitle, movieReleaseDate are non-empty.
      - If missing or unparseable, defaults are used:
          * personBirthDate, movieReleaseDate -> 1999-09-19
          * personFirstName -> UnknownFirst
          * personLastName -> UnknownLast
          * movieTitle -> UnknownMovie
      - roleInMovie can be set to a default if empty (UnknownRole).
      - Removes duplicates based on 
        (personFirstName, personLastName, personBirthDate, movieTitle, movieReleaseDate).
      - Prints initial and final row counts.
    """
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # 1) Potentially rename columns if they are capitalized differently.
    rename_map = {}
    if "PersonFirstName" in df.columns and "personFirstName" not in df.columns:
        rename_map["PersonFirstName"] = "personFirstName"
    if "PersonLastName" in df.columns and "personLastName" not in df.columns:
        rename_map["PersonLastName"] = "personLastName"
    if "PersonBirthDate" in df.columns and "personBirthDate" not in df.columns:
        rename_map["PersonBirthDate"] = "personBirthDate"
    if "MovieTitle" in df.columns and "movieTitle" not in df.columns:
        rename_map["MovieTitle"] = "movieTitle"
    if "MovieReleaseDate" in df.columns and "movieReleaseDate" not in df.columns:
        rename_map["MovieReleaseDate"] = "movieReleaseDate"
    if "RoleInMovie" in df.columns and "roleInMovie" not in df.columns:
        rename_map["RoleInMovie"] = "roleInMovie"
    
    df.rename(columns=rename_map, inplace=True)
    
    # 2) Clean personFirstName
    if 'personFirstName' in df.columns:
        df['personFirstName'] = df['personFirstName'].astype(str).str.strip()
        df['personFirstName'].replace('', DEFAULT_FIRST_NAME, inplace=True)
        df['personFirstName'].fillna(DEFAULT_FIRST_NAME, inplace=True)
    else:
        df['personFirstName'] = DEFAULT_FIRST_NAME
    
    # 3) Clean personLastName
    if 'personLastName' in df.columns:
        df['personLastName'] = df['personLastName'].astype(str).str.strip()
        df['personLastName'].replace('', DEFAULT_LAST_NAME, inplace=True)
        df['personLastName'].fillna(DEFAULT_LAST_NAME, inplace=True)
    else:
        df['personLastName'] = DEFAULT_LAST_NAME
    
    # 4) Clean personBirthDate
    if 'personBirthDate' in df.columns:
        df['personBirthDate_clean'] = df['personBirthDate'].apply(robust_parse_date)
        df['personBirthDate_clean'].fillna(DEFAULT_DATE, inplace=True)
        df['personBirthDate'] = df['personBirthDate_clean']
        df.drop(columns=['personBirthDate_clean'], inplace=True)
    else:
        df['personBirthDate'] = DEFAULT_DATE
    
    # 5) Clean movieTitle
    if 'movieTitle' in df.columns:
        df['movieTitle'] = df['movieTitle'].astype(str).str.strip()
        df['movieTitle'].replace('', DEFAULT_MOVIE_TITLE, inplace=True)
        df['movieTitle'].fillna(DEFAULT_MOVIE_TITLE, inplace=True)
    else:
        df['movieTitle'] = DEFAULT_MOVIE_TITLE
    
    # 6) Clean movieReleaseDate
    if 'movieReleaseDate' in df.columns:
        df['movieReleaseDate_clean'] = df['movieReleaseDate'].apply(robust_parse_date)
        df['movieReleaseDate_clean'].fillna(DEFAULT_DATE, inplace=True)
        df['movieReleaseDate'] = df['movieReleaseDate_clean']
        df.drop(columns=['movieReleaseDate_clean'], inplace=True)
    else:
        df['movieReleaseDate'] = DEFAULT_DATE
    
    # 7) Clean roleInMovie
    if 'roleInMovie' in df.columns:
        df['roleInMovie'] = df['roleInMovie'].astype(str).str.strip()
        df['roleInMovie'].replace('', DEFAULT_ROLE, inplace=True)
        df['roleInMovie'].fillna(DEFAULT_ROLE, inplace=True)
    else:
        df['roleInMovie'] = DEFAULT_ROLE
    
    # 8) Remove duplicates
    df.drop_duplicates(subset=[
        'personFirstName',
        'personLastName',
        'personBirthDate',
        'movieTitle',
        'movieReleaseDate'
    ], inplace=True)
    
    final_count = len(df)
    print(f"Initial rows in {input_file}: {initial_count}")
    print(f"Final rows after cleaning: {final_count}")
    
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_csv = "PersonWorkedOnMovie.csv"          # Original CSV
    output_csv = "PersonWorkedOnMovie_clean.csv"   # Cleaned CSV
    clean_person_worked_on_movie_csv(input_csv, output_csv)
