#!/usr/bin/env python3
import pandas as pd
import re
from datetime import datetime

DEFAULT_DATE = "1999-09-19"
DEFAULT_FIRST_NAME = "UnknownFirst"
DEFAULT_LAST_NAME = "UnknownLast"
DEFAULT_MOVIE_TITLE = "UnknownMovie"
DEFAULT_CATEGORY = "UnknownCategory"
DEFAULT_ITERATION = 0

def robust_parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    date_str = str(date_str).strip()
    date_formats = [
        '%Y-%m-%d', '%d %B %Y', '%d %b %Y',
        '%d/%m/%Y', '%m/%d/%Y'
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def parse_boolean(value):
    if pd.isna(value):
        return False
    val = str(value).strip().lower()
    if val in ["true", "1", "yes"]:
        return True
    if val in ["false", "0", "no"]:
        return False
    return False

def clean_final_academy_nomination(input_file, output_file):
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # 1) Rename columns if they're capitalized differently
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
    df.rename(columns=rename_map, inplace=True)

    # 2) personFirstName
    if 'personFirstName' in df.columns:
        df['personFirstName'] = df['personFirstName'].astype(str).str.strip()
        df['personFirstName'].replace('', DEFAULT_FIRST_NAME, inplace=True)
        df['personFirstName'].fillna(DEFAULT_FIRST_NAME, inplace=True)
    else:
        df['personFirstName'] = DEFAULT_FIRST_NAME

    # 3) personLastName
    if 'personLastName' in df.columns:
        df['personLastName'] = df['personLastName'].astype(str).str.strip()
        df['personLastName'].replace('', DEFAULT_LAST_NAME, inplace=True)
        df['personLastName'].fillna(DEFAULT_LAST_NAME, inplace=True)
    else:
        df['personLastName'] = DEFAULT_LAST_NAME

    # 4) personBirthDate
    if 'personBirthDate' in df.columns:
        df['personBirthDate_clean'] = df['personBirthDate'].apply(robust_parse_date)
        df['personBirthDate_clean'].fillna(DEFAULT_DATE, inplace=True)
        df['personBirthDate'] = df['personBirthDate_clean']
        df.drop(columns=['personBirthDate_clean'], inplace=True)
    else:
        df['personBirthDate'] = DEFAULT_DATE

    # 5) movieTitle
    if 'movieTitle' in df.columns:
        df['movieTitle'] = df['movieTitle'].astype(str).str.strip()
        df['movieTitle'].replace('', DEFAULT_MOVIE_TITLE, inplace=True)
        df['movieTitle'].fillna(DEFAULT_MOVIE_TITLE, inplace=True)
    else:
        df['movieTitle'] = DEFAULT_MOVIE_TITLE

    # 6) movieReleaseDate
    if 'movieReleaseDate' in df.columns:
        df['movieReleaseDate_clean'] = df['movieReleaseDate'].apply(robust_parse_date)
        df['movieReleaseDate_clean'].fillna(DEFAULT_DATE, inplace=True)
        df['movieReleaseDate'] = df['movieReleaseDate_clean']
        df.drop(columns=['movieReleaseDate_clean'], inplace=True)
    else:
        df['movieReleaseDate'] = DEFAULT_DATE

    # 7) category
    if 'category' in df.columns:
        df['category'] = df['category'].astype(str).str.strip()
        df['category'].replace('', DEFAULT_CATEGORY, inplace=True)
        df['category'].fillna(DEFAULT_CATEGORY, inplace=True)
        df['category'] = df['category'].str.slice(0, 50)  # limit to 50 chars
    else:
        df['category'] = DEFAULT_CATEGORY

    # 8) iteration
    if 'iteration' in df.columns:
        df['iteration'] = pd.to_numeric(df['iteration'], errors='coerce').fillna(DEFAULT_ITERATION).astype(int)
    else:
        df['iteration'] = DEFAULT_ITERATION

    # 9) grantedOrNot
    if 'grantedOrNot' in df.columns:
        df['grantedOrNot'] = df['grantedOrNot'].apply(parse_boolean)
    else:
        df['grantedOrNot'] = False

    # 10) Remove duplicates
    df.drop_duplicates(subset=[
        'personFirstName',
        'personLastName',
        'personBirthDate',
        'movieTitle',
        'movieReleaseDate',
        'category'
    ], inplace=True)

    final_count = len(df)
    print(f"Initial rows in {input_file}: {initial_count}")
    print(f"Final rows after cleaning: {final_count}")

    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    input_csv = "FinalAcademyNomination.csv"
    output_csv = "FinalAcademyNomination_clean.csv"
    clean_final_academy_nomination(input_csv, output_csv)
