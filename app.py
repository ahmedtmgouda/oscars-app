import os
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from dotenv import load_dotenv
from db import get_db
import mysql.connector
from collections import OrderedDict

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")



@app.before_request
def load_logged_in_user():
    g.user = session.get("username")


def login_required(view):
    @wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped



@app.route("/")
def index():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Movie;")
    movie_count = cur.fetchone()[0]
    cur.close(); conn.close()
    return render_template("index.html", movie_count=movie_count)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # required
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        # optional
        gender     = request.form.get("gender") or None
        age_str    = request.form.get("age", "").strip()
        birth_date = request.form.get("birthDate", "").strip()
        country    = request.form.get("country", "").strip() or None

        # validation
        if not username or not email:
            flash("Username and email are required.", "danger")
            return redirect(url_for("register"))

        # age
        age = None
        if age_str:
            try:
                age = int(age_str)
                if age < 0:
                    raise ValueError()
            except ValueError:
                flash("Age must be a non‑negative integer.", "danger")
                return redirect(url_for("register"))

        # birth date
        if birth_date:
            try:
                datetime.datetime.strptime(birth_date, "%Y-%m-%d")
            except ValueError:
                flash("Birth date must be in YYYY‑MM‑DD format.", "danger")
                return redirect(url_for("register"))

        conn = get_db(); cur = conn.cursor()
        # uniqueness
        cur.execute(
            "SELECT 1 FROM Users WHERE username=%s OR email=%s",
            (username, email)
        )
        if cur.fetchone():
            flash("That username or email is already taken.", "warning")
            cur.close(); conn.close()
            return redirect(url_for("register"))

        # insert
        cur.execute(
            """
            INSERT INTO Users
              (username, email, gender, age, birthDate, country)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (username, email, gender, age, birth_date, country)
        )
        conn.commit()
        cur.close(); conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Username is required.", "danger")
            return redirect(url_for("login"))

        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT username FROM Users WHERE username=%s", (username,))
        row = cur.fetchone()
        cur.close(); conn.close()

        if row:
            session.clear()
            session["username"] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Username not found.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=g.user)


@app.route("/nominate", methods=["GET", "POST"])
@login_required
def nominate():
    conn = get_db(); cur = conn.cursor()

    if request.method == "POST":
        userUsername    = g.user
        person_key      = request.form["person"]
        movie_key       = request.form["movie"]
        category        = request.form["category"]

        firstName, lastName, birthDate = person_key.split("|")
        movieTitle, movieReleaseDate   = movie_key.split("|")

        if not all([userUsername, firstName, lastName, birthDate, movieTitle, movieReleaseDate, category]):
            flash("All fields are required.", "danger")
            cur.close(); conn.close()
            return redirect(url_for("nominate"))

        try:
            cur.execute(
                """
                INSERT INTO UserNomination
                  (userUsername,
                   personFirstName, personLastName, personBirthDate,
                   movieTitle, movieReleaseDate,
                   category)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    userUsername,
                    firstName, lastName, birthDate,
                    movieTitle, movieReleaseDate,
                    category
                )
            )
            conn.commit()
            flash("Nomination submitted!", "success")
        except mysql.connector.IntegrityError:
            flash(
                "Failed to submit nomination. Duplicate or invalid selection.",
                "danger"
            )
        finally:
            cur.close(); conn.close()

        return redirect(url_for("nominate"))

    # load choice lists
    cur.execute("""
      SELECT
        CONCAT(firstName, '|', lastName, '|', birthDate) AS person_key,
        CONCAT(firstName, ' ', lastName, ' (', birthDate, ')') AS person_label
      FROM Person
      ORDER BY lastName, firstName
    """)
    persons = cur.fetchall()

    cur.execute("""
      SELECT
        CONCAT(Title, '|', releaseDate) AS movie_key,
        CONCAT(Title, ' (', releaseDate, ')') AS movie_label
      FROM Movie
      ORDER BY Title
    """)
    movies = cur.fetchall()

    cur.execute("""
      SELECT DISTINCT Category
      FROM AcademyNomination
      ORDER BY Category
    """)
    categories = [row[0] for row in cur.fetchall()]

    cur.close(); conn.close()

    return render_template(
        "nominate.html",
        persons=persons,
        movies=movies,
        categories=categories
    )

@app.route("/nominations")
@login_required
def nominations():
    
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT
          un.category,
          m.Title,
          CONCAT(p.firstName, ' ', p.lastName) AS person
        FROM UserNomination AS un
        JOIN Movie   AS m ON m.Title = un.movieTitle
                          AND m.releaseDate = un.movieReleaseDate
        JOIN Person  AS p ON p.firstName = un.personFirstName
                          AND p.lastName = un.personLastName
                          AND p.birthDate = un.personBirthDate
        WHERE un.userUsername = %s
        ORDER BY un.category;
        """,
        (g.user,)
    )
    nominations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("nominations.html", nominations=nominations)

@app.route("/top_nominated", methods=["GET","POST"])
@login_required
def top_nominated():
    conn = get_db(); cur = conn.cursor()

    # Load filter lists
    cur.execute("SELECT DISTINCT category FROM UserNomination ORDER BY category")
    categories = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT YEAR(movieReleaseDate) FROM UserNomination ORDER BY 1 DESC")
    years = [r[0] for r in cur.fetchall()]

    results = None
    if request.method == "POST":
        cat = request.form.get("category")
        yr  = request.form.get("year")
        if cat:
            cur.execute(
                """
                SELECT movieTitle, movieReleaseDate, COUNT(*) AS nomination_count
                FROM UserNomination
                WHERE category = %s
                GROUP BY movieTitle, movieReleaseDate
                ORDER BY nomination_count DESC
                """,
                (cat,)
            )
            results = cur.fetchall()
        elif yr:
            cur.execute(
                """
                SELECT movieTitle, movieReleaseDate, COUNT(*) AS nomination_count
                FROM UserNomination
                WHERE YEAR(movieReleaseDate) = %s
                GROUP BY movieTitle, movieReleaseDate
                ORDER BY nomination_count DESC
                """,
                (yr,)
            )
            results = cur.fetchall()
        else:
            flash("Please choose a category or a year.", "warning")

    cur.close(); conn.close()
    return render_template(
        "top_nominated.html",
        categories=categories,
        years=years,
        results=results
    )


ROLE_CATEGORIES = {
    "director": [
        "Best Director",
        "Best Directing",
        "Best Directing (Comedy Picture)",
        "Best Directing (Dramatic Picture)"
    ],
    "actor": [
        "Best Actor",
        "Best Actor in a Leading Role",
        "Best Actor in a Supporting Role",
        "Best Actress",
        "Best Actress in a Leading Role",
        "Best Actress in a Supporting Role"
    ],
    "singer": [
        "Best Music (Adaptation Score)",
        "Best Music (Music Score of a Dramatic or Comedy Picture)",
        "Best Music (Music Score of a Dramatic Picture)",
        "Best Music (Original Dramatic Score)",
        "Best Music (Original Musical or Comedy Score)",
        "Best Music (Original Score)",
        "Best Music (Original Song Score and Its Adaptation)",
        "Best Music (Original Song Score or Adaptation Score)",
        "Best Music (Original Song Score)",
        "Best Music (Original Song)",
        "Best Music (Scoring of a Musical Picture)",
        "Best Music (Scoring)",
        "Best Music (Song)"
    ]
}

@app.route("/stats/<role>", methods=["GET", "POST"])
@login_required
def stats(role):
    if role not in ROLE_CATEGORIES:
        flash("Unknown role.", "danger")
        return redirect(url_for("index"))

    patterns = ROLE_CATEGORIES[role]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
          CONCAT(personFirstName, '|', personLastName, '|', personBirthDate) AS person_key,
          CONCAT(personFirstName, ' ', personLastName)                 AS person_label
        FROM AcademyNomination
        WHERE category IN ({})
        GROUP BY personFirstName, personLastName, personBirthDate
        ORDER BY personLastName, personFirstName
    """.format(", ".join("%s" for _ in patterns)), tuple(patterns))
    persons = cur.fetchall()

    stats = None
    nominations = None

    if request.method == "POST":
        key = request.form.get("person")
        if not key:
            flash("Please select a person.", "warning")
        else:
            first, last, bdate = key.split("|")

            # totals
            cur.execute("""
              SELECT
                COUNT(*)                   AS nominations,
                SUM(grantedOrNot = 1)      AS wins
              FROM AcademyNomination
              WHERE personFirstName = %s
                AND personLastName  = %s
                AND personBirthDate = %s
                AND category IN ({})
            """.format(", ".join("%s" for _ in patterns)),
            (first, last, bdate, *patterns))
            stats = cur.fetchone()

            # detailed list
            cur.execute("""
              SELECT
                movieTitle,
                movieReleaseDate,
                category,
                grantedOrNot
              FROM AcademyNomination
              WHERE personFirstName = %s
                AND personLastName  = %s
                AND personBirthDate = %s
                AND category IN ({})
              ORDER BY movieReleaseDate DESC, movieTitle
            """.format(", ".join("%s" for _ in patterns)),
            (first, last, bdate, *patterns))
            nominations = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
      "stats.html",
      role=role,
      persons=persons,
      stats=stats,
      nominations=nominations
    )



@app.route("/top_actor_countries")
@login_required
def top_actor_countries():
    """
    Show two top-5 lists:
      • winners → Best Actor Oscar wins by country
      • nominees → Best Actor nominations by country
    """
    conn = get_db()
    cur  = conn.cursor()

    # winners: Best Actor Oscar wins by country
    cur.execute("""
        SELECT
          p.countryOfBirth,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName     = an.personFirstName
         AND p.lastName      = an.personLastName
         AND p.birthDate     = an.personBirthDate
        WHERE (an.category = 'Best Actor'
               OR an.category = 'Best Actor in a Leading Role'
               OR an.category = 'Best Actor in a Supporting Role')
          AND an.grantedOrNot = 1
          AND p.countryOfBirth IS NOT NULL
          AND p.countryOfBirth <> ''
        GROUP BY p.countryOfBirth
        ORDER BY wins DESC
        LIMIT 5
    """)
    winners = cur.fetchall()  # [(country, wins), ...]

    # nominees: Best Actor nominations by country
    cur.execute("""
        SELECT
          p.countryOfBirth,
          COUNT(*) AS nominations
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName     = an.personFirstName
         AND p.lastName      = an.personLastName
         AND p.birthDate     = an.personBirthDate
        WHERE (an.category = 'Best Actor'
               OR an.category = 'Best Actor in a Leading Role'
               OR an.category = 'Best Actor in a Supporting Role')
          AND p.countryOfBirth IS NOT NULL
          AND p.countryOfBirth <> ''
        GROUP BY p.countryOfBirth
        ORDER BY nominations DESC
        LIMIT 5
    """)
    nominees = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "top_actor_countries.html",
        winners=winners,
        nominees=nominees
    )



@app.route("/staff_by_country", methods=["GET", "POST"])
@login_required
def staff_by_country():
    """
    Show all nominated staff born in a selected country,
    with their categories, number of nominations, and Oscar wins,
    ordered by wins desc, then nominations desc.
    """
    conn = get_db()
    cur  = conn.cursor()

    # Load all distinct, non‑empty birth countries
    cur.execute("""
      SELECT DISTINCT countryOfBirth
      FROM Person
      WHERE countryOfBirth IS NOT NULL
        AND countryOfBirth <> ''
      ORDER BY countryOfBirth
    """)
    countries = [row[0] for row in cur.fetchall()]

    results = None
    if request.method == "POST":
        country = request.form.get("country")
        if not country:
            flash("Please select a country.", "warning")
        else:
            cur.execute("""
              SELECT
                p.firstName,
                p.lastName,
                an.category,
                COUNT(*)                   AS nomination_count,
                SUM(an.grantedOrNot = 1)   AS win_count
              FROM AcademyNomination AS an
              JOIN Person AS p
                ON p.firstName    = an.personFirstName
               AND p.lastName     = an.personLastName
               AND p.birthDate    = an.personBirthDate
              WHERE p.countryOfBirth = %s
              GROUP BY
                p.firstName, p.lastName, an.category
              ORDER BY
                win_count DESC,
                nomination_count DESC
            """, (country,))
            results = cur.fetchall() 

    cur.close()
    conn.close()

    return render_template(
      "staff_by_country.html",
      countries=countries,
      results=results
    )


@app.route("/dream_team")
@login_required
def dream_team():
    """
    Pick the living person with the most Oscar wins in each key role,
    by running one specialized query per role.
    """
    conn = get_db()
    cur = conn.cursor()
    team = {}

    # Director
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE (an.category       = 'Best Director'
               OR an.category    = 'Best Directing'
               OR an.category    = 'Best Directing (Comedy Picture)'
               OR an.category    = 'Best Directing (Dramatic Picture)')
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        team["director"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["director"] = {"name": "(no living winner)", "wins": 0}

    # Leading Actor
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE (an.category       = 'Best Actor'
               OR an.category    = 'Best Actor in a Leading Role')
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        team["actor"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["actor"] = {"name": "(no living winner)", "wins": 0}

    # Leading Actress
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE (an.category       = 'Best Actress'
               OR an.category    = 'Best Actress in a Leading Role')
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        team["actress"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["actress"] = {"name": "(no living winner)", "wins": 0}

    # Supporting Actor
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE an.category       = 'Best Actor in a Supporting Role'
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        team["supporting_actor"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["supporting_actor"] = {"name": "(no living winner)", "wins": 0}

    # Supporting Actress
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE an.category       = 'Best Actress in a Supporting Role'
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        team["supporting_actress"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["supporting_actress"] = {"name": "(no living winner)", "wins": 0}

    # Producer (Best Picture)
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE an.category       = 'Best Picture'
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        team["producer"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["producer"] = {"name": "(no living winner)", "wins": 0}

    # Singer/Musician
    cur.execute("""
        SELECT
          p.firstName,
          p.lastName,
          COUNT(*) AS wins
        FROM AcademyNomination AS an
        JOIN Person AS p
          ON p.firstName   = an.personFirstName
         AND p.lastName    = an.personLastName
         AND p.birthDate   = an.personBirthDate
        WHERE (an.category       = 'Best Music (Adaptation Score)'
               OR an.category    = 'Best Music (Music Score of a Dramatic or Comedy Picture)'
               OR an.category    = 'Best Music (Music Score of a Dramatic Picture)'
               OR an.category    = 'Best Music (Original Dramatic Score)'
               OR an.category    = 'Best Music (Original Musical or Comedy Score)'
               OR an.category    = 'Best Music (Original Score)'
               OR an.category    = 'Best Music (Original Song Score and Its Adaptation)'
               OR an.category    = 'Best Music (Original Song Score or Adaptation Score)'
               OR an.category    = 'Best Music (Original Song Score)'
               OR an.category    = 'Best Music (Original Song)'
               OR an.category    = 'Best Music (Scoring of a Musical Picture)'
               OR an.category    = 'Best Music (Scoring)'
               OR an.category    = 'Best Music (Song)')
          AND an.grantedOrNot    = 1
          AND p.deathDate IS NULL
        GROUP BY p.firstName, p.lastName, p.birthDate
        ORDER BY wins DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    if row:
        team["singer"] = {"name": f"{row[0]} {row[1]}", "wins": row[2]}
    else:
        team["singer"] = {"name": "(no living winner)", "wins": 0}

    cur.close()
    conn.close()

    return render_template("dream_team.html", team=team)



@app.route("/top_companies")
@login_required
def top_companies():
    """
    Top 5 production companies by Oscar wins.
    """
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
          mpc.productionCompany,
          COUNT(*) AS oscar_wins
        FROM AcademyNomination AS an
        JOIN MovieProductionCompany AS mpc
          ON mpc.title        = an.movieTitle
         AND mpc.releaseDate  = an.movieReleaseDate
        WHERE an.grantedOrNot = 1
        GROUP BY mpc.productionCompany
        ORDER BY oscar_wins DESC
        LIMIT 5
    """)
    rows = cur.fetchall()  
    cur.close()
    conn.close()
    return render_template("top_companies.html", rows=rows)

@app.route("/non_english_winners")
@login_required
def non_english_winners():
    """
    List all non-English-language movies that have ever won an Oscar,
    along with their year and language, ordered by most recent year first.
    """
    conn = get_db()
    cur  = conn.cursor()

    cur.execute("""
        SELECT DISTINCT
          m.title,
          YEAR(m.releaseDate)    AS year,
          m.movieLanguage
        FROM AcademyNomination AS an
        JOIN Movie AS m
          ON m.title       = an.movieTitle
         AND m.releaseDate = an.movieReleaseDate
        WHERE an.grantedOrNot = 1
          AND m.movieLanguage IS NOT NULL
          AND TRIM(m.movieLanguage) <> ''
          AND m.movieLanguage <> 'English'
          AND m.movieLanguage <> 'nan'
          AND m.movieLanguage <> 'No'
          AND m.movieLanguage <> 'no'
        ORDER BY year DESC, m.title
    """)
    rows = cur.fetchall()  

    cur.close()
    conn.close()
    return render_template("non_english_winners.html", rows=rows)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
