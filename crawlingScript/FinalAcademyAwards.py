import os
import requests
from bs4 import BeautifulSoup
import csv
import re
import pandas as pd
from datetime import datetime


def ordinal(n):
    """
    Convert an integer (e.g., 1, 2, 3, 4, 21, 22) to its ordinal string.
      1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', etc.
    """
    return ("%d%s" % (n, "tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]))


nom_csv_filename = "AcademyNomination.csv"
person_csv_filename = "Person.csv"
movie_csv_filename = "movie.csv"
production_csv_filename = "MovieProductionCompany.csv"
country_csv_filename = "MovieCountry.csv"
person_movie_csv_filename = "PersonWorkedOnMovie.csv"
final_academy_csv_filename = "FinalAcademyNomination.csv"

# Nominations and Person CSV Fieldnames
nom_fieldnames = [
    "iteration", 
    "category", 
    "movie", 
    "person_first", 
    "person_last", 
    "winner", 
    "movie_link", 
    "person_link"
]
person_fieldnames = [
    "person_link", 
    "person_first", 
    "person_last", 
    "person_birth_date", 
    "person_country_of_birth", 
    "death_date"
]

# Movie related CSV fieldnames
movie_fieldnames = [
    "title", 
    "releasedate", 
    "budget", 
    "boxOffice", 
    "runtime", 
    "movieLanguage"
]
production_fieldnames = ["title", "releaseDate", "productionCompany"]
country_fieldnames = ["title", "releaseDate", "country"]
person_movie_fieldnames = [
    "PersonFirstName", 
    "PersonLastName", 
    "PersonBirthDate", 
    "MovieTitle", 
    "MovieReleaseDate", 
    "RoleInMovie"
]
final_academy_fieldnames = [
    "PersonFirstName", 
    "PersonLastName", 
    "PersonBirthDate", 
    "MovieTitle", 
    "MovieReleaseDate", 
    "category", 
    "iteration", 
    "grantedOrNot"
]

def ensure_csv_with_header(filename, fieldnames):
    """Create a CSV with header row if it doesn't already exist."""
    if not os.path.exists(filename):
        with open(filename, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

ensure_csv_with_header(nom_csv_filename, nom_fieldnames)
ensure_csv_with_header(person_csv_filename, person_fieldnames)
ensure_csv_with_header(movie_csv_filename, movie_fieldnames)
ensure_csv_with_header(production_csv_filename, production_fieldnames)
ensure_csv_with_header(country_csv_filename, country_fieldnames)
ensure_csv_with_header(person_movie_csv_filename, person_movie_fieldnames)
ensure_csv_with_header(final_academy_csv_filename, final_academy_fieldnames)


start_iteration = 1
end_iteration = 96

category_mapping = {
    "Outstanding Picture": "Best Picture",
    "Outstanding Production": "Best Picture",
    "Outstanding Motion Picture": "Best Picture",
    "Best Motion Picture": "Best Picture",
    "Best Picture": "Best Picture",
    "Best Art Direction": "Best Production Design",
    "Best Production Design": "Best Production Design"
}

# Helper functions
def split_name(full_name):
    if not full_name:
        return None, None
    parts = full_name.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return full_name, ""

def parse_date(date_str):
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str

def extract_nomination(li, category, iteration_str, winner_override=None):
    winner = winner_override if winner_override is not None else bool(li.find("b"))
    movie, movie_link = None, None
    person_full, person_link = None, None

    italic_tag = li.find("i")
    if italic_tag:
        movie = italic_tag.get_text(strip=True)
        a_movie = italic_tag.find("a")
        if a_movie and a_movie.has_attr("href"):
            # Only build a full link if it's from wikipedia
            link_href = a_movie["href"]
            if link_href.startswith("/wiki/"):
                movie_link = "https://en.wikipedia.org" + link_href

    for a in li.find_all("a"):
        if a.find_parent("i"):
            continue
        person_full = a.get_text(strip=True)
        if a.has_attr("href"):
            link_href = a["href"]
            if link_href.startswith("/wiki/"):
                person_link = "https://en.wikipedia.org" + link_href
        break

    person_first, person_last = split_name(person_full)
    return {
        "iteration": iteration_str,
        "category": category,
        "movie": movie,
        "person_first": person_first,
        "person_last": person_last,
        "winner": winner,
        "movie_link": movie_link,
        "person_link": person_link
    }

def format_date(date_str):
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
    if m:
        year, month, day = m.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str

def extract_person_details(person_url):
    """
    Attempt to get the person's data. 
    Skip if the URL isn't en.wikipedia.org or if requests.get fails.
    """
    # Skip if link not from en.wikipedia.org
    if not person_url or not person_url.startswith("https://en.wikipedia.org/"):
        return None

    try:
        response = requests.get(person_url, timeout=15)
    except Exception as e:
        
        print(f"Skipping person link {person_url} due to error: {e}")
        return None

    if not response.ok:
        print(f"Skipping person link {person_url}, status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    infobox = soup.find("table", class_="infobox biography vcard")
    if not infobox:
        return None

    fn_div = infobox.find("div", class_="fn")
    if fn_div:
        full_name = fn_div.get_text(strip=True)
        person_first, person_last = split_name(full_name)
    else:
        person_first, person_last = None, None

    # Birth date
    bday_span = infobox.find("span", class_="bday")
    person_birth_date = None
    if bday_span:
        person_birth_date = bday_span.get_text(strip=True)
    else:
        born_row = infobox.find("th", string=lambda s: s and "Born" in s)
        if born_row:
            born_td = born_row.find_next_sibling("td")
            if born_td:
                born_text = born_td.get_text(" ", strip=True)
                m2 = re.search(r'(\d{1,2} \w+ \d{4})', born_text)
                if m2:
                    person_birth_date = parse_date(m2.group(1))

    # Country of birth
    country_of_birth = None
    born_row = infobox.find("th", string=lambda s: s and "Born" in s)
    if born_row:
        born_td = born_row.find_next_sibling("td")
        if born_td:
            birthplace_div = born_td.find("div", class_="birthplace")
            if birthplace_div:
                birthplace_text = birthplace_div.get_text(separator=",", strip=True)
                parts = birthplace_text.split(",")
                if parts:
                    last_part = parts[-1].strip()
                    if last_part.upper().replace(".", "").strip() in ["USA", "US"]:
                        last_part = "United States"
                    country_of_birth = last_part

    # Death date
    death_date = None
    died_row = infobox.find("th", string=lambda s: s and "Died" in s)
    if died_row:
        died_td = died_row.find_next_sibling("td")
        if died_td:
            death_span = died_td.find("span", class_="bday")
            if death_span:
                death_date = death_span.get_text(strip=True)
            else:
                died_text = died_td.get_text(" ", strip=True)
                m3 = re.search(r'(\d{1,2} \w+ \d{4})', died_text)
                if m3:
                    death_date = parse_date(m3.group(1))

    return {
        "person_first": person_first,
        "person_last": person_last,
        "person_birth_date": person_birth_date,
        "person_country_of_birth": country_of_birth,
        "death_date": death_date
    }

def extract_movie_data(url):
    """
    Attempt to get the movie data from an en.wikipedia.org link. 
    Skip if not valid or if requests fails.
    """
    # Skip if link is not from en.wikipedia.org
    if not url or not url.startswith("https://en.wikipedia.org/"):
        return None

    try:
        response = requests.get(url, timeout=15)
    except Exception as e:
        print(f"Skipping movie link {url} due to error: {e}")
        return None

    if not response.ok:
        print(f"Skipping movie link {url}, status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    infobox = soup.find('table', class_='infobox vevent')
    if not infobox:
        return None

    movie_data = {
        "MovieTitle": None,
        "ReleaseDate": None,
        "ProductionCompany": [],
        "Runtime": None,
        "Country": [],
        "Language": None,
        "Budget": None,
        "BoxOffice": None
    }

    title_cell = infobox.find('th', class_='infobox-above summary')
    if title_cell:
        movie_data["MovieTitle"] = title_cell.get_text(strip=True)

    rows = infobox.find_all('tr')
    for row in rows:
        header = row.find('th')
        if not header:
            continue
        label = " ".join(header.stripped_strings).lower()
        data_cell = row.find('td')
        if not data_cell:
            continue

        for sup in data_cell.find_all('sup'):
            sup.decompose()
        data_text = data_cell.get_text(" ", strip=True)
        data_text = re.sub(r'\s+', ' ', data_text)

        if "release date" in label:
            bday_span = data_cell.find('span', class_='bday')
            if bday_span:
                raw_date = bday_span.get_text(strip=True)
                movie_data["ReleaseDate"] = format_date(raw_date)
            else:
                date_part = data_text.split('(')[0].strip()
                movie_data["ReleaseDate"] = format_date(date_part)

        elif "production company" in label or "production companies" in label:
            ul = data_cell.find('ul') or data_cell.select_one("div.plainlist ul")
            comps = []
            if ul:
                for li_tag in ul.find_all('li'):
                    txt = li_tag.get_text(" ", strip=True)
                    txt = re.sub(r'\[.*?\]', '', txt).strip()
                    if txt and txt not in comps:
                        comps.append(txt)
            else:
                txt = re.sub(r'\[.*?\]', '', data_text).strip()
                if txt:
                    comps = [txt]
            movie_data["ProductionCompany"] = comps

        elif "running time" in label or "duration" in label:
            lis = data_cell.find_all('li')
            chosen = None
            if lis:
                for li_tag in lis:
                    t = li_tag.get_text(strip=True).lower()
                    if "original release:" in t:
                        chosen = t.replace("original release:", "").strip()
                        break
                if not chosen:
                    chosen = lis[0].get_text(strip=True)
            else:
                chosen = data_text
            if chosen:
                m_ = re.search(r'(\d+)', chosen)
                if m_:
                    movie_data["Runtime"] = m_.group(1)

        elif "country" in label or "countries" in label:
            ul = data_cell.find('ul') or data_cell.select_one("div.plainlist ul")
            c_list = []
            if ul:
                for li_tag in ul.find_all('li'):
                    txt = li_tag.get_text(" ", strip=True)
                    txt = re.sub(r'\[.*?\]', '', txt).strip()
                    def normalize_usa(s):
                        s_norm = s.upper().replace(".", "").strip()
                        return "United States" if s_norm in ["USA", "US"] else s
                    norm_txt = normalize_usa(txt)
                    if norm_txt and norm_txt not in c_list:
                        c_list.append(norm_txt)
            else:
                txt = re.sub(r'\[.*?\]', '', data_text).strip()
                if txt:
                    def normalize_usa(s):
                        s_norm = s.upper().replace(".", "").strip()
                        return "United States" if s_norm in ["USA", "US"] else s
                    norm_txt = normalize_usa(txt)
                    c_list = [norm_txt]
            movie_data["Country"] = c_list

        elif "language" in label:
            lis = data_cell.find_all('li')
            languages = [li_tag.get_text(strip=True) for li_tag in lis] if lis else [data_text]
            if languages:
                first_lang = languages[0]
                first_word = first_lang.split()[0]
                if first_word.lower() in ["american", "british", "australian"]:
                    movie_data["Language"] = "English"
                else:
                    movie_data["Language"] = first_word

        elif "budget" in label:
            budget_clean = re.sub(r'\[.*?\]', '', data_text).strip()
            movie_data["Budget"] = budget_clean

        elif "box office" in label:
            box_clean = re.sub(r'\[.*?\]', '', data_text).strip()
            box_clean = re.sub(r'\(.*?\)', '', box_clean).strip()
            movie_data["BoxOffice"] = box_clean

    return movie_data

# main loop

processed_person_links = {}
processed_movie_links = {}

for i in range(start_iteration, end_iteration + 1):
    iteration_str = ordinal(i) 

    iteration_results = []
    iteration_person_links = {}
    iteration_movie_links = {}

    url = f"https://en.wikipedia.org/wiki/{iteration_str}_Academy_Awards"
    try:
        resp = requests.get(url, timeout=15)
    except Exception as e:
        print(f"Could not fetch {url} due to error: {e}. Skipping.")
        continue

    if not resp.ok:
        print(f"Skipping {iteration_str} Academy Awards. Status code: {resp.status_code}")
        continue

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        print(f"No wikitable found for {iteration_str} Academy Awards. Skipping.")
        continue

    # Extract nominations
    for tr in table.find_all("tr"):
        for td in tr.find_all("td", recursive=False):
            cat_div = td.find("div")
            if not cat_div:
                continue
            raw_cat = cat_div.get_text(strip=True)
            category = category_mapping.get(raw_cat, raw_cat)

            ul = td.find("ul")
            if not ul:
                continue

            top_li = ul.find_all("li", recursive=False)
            for li in top_li:
                nom = extract_nomination(li, category, iteration_str)
                iteration_results.append(nom)

                nested_ul = li.find("ul")
                if nested_ul:
                    nested_li = nested_ul.find_all("li", recursive=False)
                    for nli in nested_li:
                        nom2 = extract_nomination(nli, category, iteration_str, winner_override=False)
                        iteration_results.append(nom2)

    # Gather new person details
    for nom in iteration_results:
        p_link = nom["person_link"]
        # Only fetch if we haven't fetched in a previous iteration or this iteration
        if p_link and (p_link not in processed_person_links) and (p_link not in iteration_person_links):
            d_ = extract_person_details(p_link)
            if d_:
                iteration_person_links[p_link] = d_

    # Gather new movie details
    for nom in iteration_results:
        m_link = nom["movie_link"]
        if m_link and (m_link not in processed_movie_links) and (m_link not in iteration_movie_links):
            d_ = extract_movie_data(m_link)
            iteration_movie_links[m_link] = d_

    # Everything is in memory. Now let's append to CSVs.
    # AcademyNomination.csv
    with open(nom_csv_filename, "a", newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=nom_fieldnames)
        for n_ in iteration_results:
            w.writerow(n_)

    # Person.csv
    with open(person_csv_filename, "a", newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=person_fieldnames)
        for link, det in iteration_person_links.items():
            row = {
                "person_link": link,
                "person_first": det["person_first"],
                "person_last": det["person_last"],
                "person_birth_date": det["person_birth_date"],
                "person_country_of_birth": det["person_country_of_birth"],
                "death_date": det["death_date"]
            }
            w.writerow(row)

    # Mark persons as processed
    processed_person_links.update(iteration_person_links)

    # Build partial data for the 5 other CSVs
    movie_rows = []
    production_rows = []
    country_rows = []
    person_movie_rows = []
    final_academy_rows = []

    for n_ in iteration_results:
        m_link = n_.get("movie_link")
        if m_link:
            m_info = iteration_movie_links.get(m_link) or processed_movie_links.get(m_link)
            if m_info:
                # movie.csv
                movie_rows.append({
                    "title": m_info["MovieTitle"],
                    "releasedate": m_info["ReleaseDate"],
                    "budget": m_info["Budget"],
                    "boxOffice": m_info["BoxOffice"],
                    "runtime": m_info["Runtime"],
                    "movieLanguage": m_info["Language"]
                })
                # MovieProductionCompany.csv
                for comp in m_info["ProductionCompany"]:
                    production_rows.append({
                        "title": m_info["MovieTitle"],
                        "releaseDate": m_info["ReleaseDate"],
                        "productionCompany": comp
                    })
                # MovieCountry.csv
                for c_ in m_info["Country"]:
                    country_rows.append({
                        "title": m_info["MovieTitle"],
                        "releaseDate": m_info["ReleaseDate"],
                        "country": c_
                    })
                # PersonWorkedOnMovie & FinalAcademyNomination
                p_link = n_.get("person_link")
                if p_link and (p_link in iteration_person_links or p_link in processed_person_links):
                    det = iteration_person_links.get(p_link) or processed_person_links[p_link]
                    role = re.sub(r'\s*\(.*?\)', '', re.sub(r'(?i)^best\s+', '', n_["category"])).strip()
                    person_movie_rows.append({
                        "PersonFirstName": det["person_first"],
                        "PersonLastName": det["person_last"],
                        "PersonBirthDate": det["person_birth_date"],
                        "MovieTitle": m_info["MovieTitle"],
                        "MovieReleaseDate": m_info["ReleaseDate"],
                        "RoleInMovie": role
                    })
                    iteration_num = int(re.sub(r'\D', '', n_["iteration"])) if n_["iteration"] else None
                    final_academy_rows.append({
                        "PersonFirstName": det["person_first"],
                        "PersonLastName": det["person_last"],
                        "PersonBirthDate": det["person_birth_date"],
                        "MovieTitle": m_info["MovieTitle"],
                        "MovieReleaseDate": m_info["ReleaseDate"],
                        "category": n_["category"],
                        "iteration": iteration_num,
                        "grantedOrNot": bool(n_["winner"])
                    })

    # Mark movies as processed
    processed_movie_links.update(iteration_movie_links)

    # append rows to the 5 CSVs
    if movie_rows:
        with open(movie_csv_filename, "a", newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=movie_fieldnames)
            for row_ in movie_rows:
                w.writerow(row_)
    if production_rows:
        with open(production_csv_filename, "a", newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=production_fieldnames)
            for row_ in production_rows:
                w.writerow(row_)
    if country_rows:
        with open(country_csv_filename, "a", newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=country_fieldnames)
            for row_ in country_rows:
                w.writerow(row_)
    if person_movie_rows:
        with open(person_movie_csv_filename, "a", newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=person_movie_fieldnames)
            for row_ in person_movie_rows:
                w.writerow(row_)
    if final_academy_rows:
        with open(final_academy_csv_filename, "a", newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=final_academy_fieldnames)
            for row_ in final_academy_rows:
                w.writerow(row_)

    print(f"Completed scraping for {iteration_str} Academy Awards. Data appended to CSV files.")

print("\nAll done! If it crashed mid-iteration, re-run and it will start from scratch on that iteration.")
