import os
import re

import psycopg
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from psycopg.rows import dict_row


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or (
    "donorbridge-development-key-change-before-deployment"
)

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
CREATE_DONORS_TABLE = """
    CREATE TABLE IF NOT EXISTS donors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        blood_group VARCHAR(3) NOT NULL,
        city VARCHAR(100) NOT NULL,
        contact VARCHAR(20) NOT NULL,
        availability BOOLEAN NOT NULL DEFAULT TRUE
    )
"""


class DatabaseConfigurationError(Exception):
    """Raised when the required database connection setting is missing."""


def database_connection():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL is missing. Add your Neon connection string to .env."
        )
    return psycopg.connect(database_url)


def validate_donor_form():
    values = {
        "name": request.form.get("name", "").strip(),
        "blood_group": request.form.get("blood_group", "").strip().upper(),
        "city": request.form.get("city", "").strip(),
        "contact": request.form.get("contact", "").strip(),
        "availability": request.form.get("availability", "").strip(),
    }
    errors = []

    for field in ("name", "blood_group", "city", "contact", "availability"):
        if not values[field]:
            errors.append(f"{field.replace('_', ' ').title()} is required.")

    if values["blood_group"] and values["blood_group"] not in BLOOD_GROUPS:
        errors.append("Choose a valid blood group.")
    if len(values["name"]) > 100:
        errors.append("Name must be 100 characters or fewer.")
    if len(values["city"]) > 100:
        errors.append("City must be 100 characters or fewer.")
    if values["contact"]:
        if (
            len(values["contact"]) > 20
            or not re.fullmatch(r"[0-9+() .-]+", values["contact"])
            or sum(character.isdigit() for character in values["contact"]) < 5
        ):
            errors.append(
                "Enter a contact number with at least 5 digits and no more than 20 characters."
            )
    if values["availability"] not in ("true", "false"):
        errors.append("Choose whether the donor is available.")

    if values["availability"] in ("true", "false"):
        values["availability"] = values["availability"] == "true"
    return values, errors


@app.get("/")
def index():
    blood_group = request.args.get("blood_group", "").strip().upper()
    city = request.args.get("city", "").strip()
    if blood_group and blood_group not in BLOOD_GROUPS:
        flash("Choose a valid blood group filter.", "error")
        blood_group = ""

    donors = None
    summary = None
    try:
        with database_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(CREATE_DONORS_TABLE)
                cursor.execute(
                    """
                    SELECT id, name, blood_group, city, contact, availability
                    FROM donors
                    WHERE (%s = '' OR blood_group = %s)
                      AND (%s = '' OR city ILIKE %s)
                    ORDER BY id DESC
                    """,
                    (blood_group, blood_group, city, f"%{city}%"),
                )
                donors = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total,
                           COUNT(*) FILTER (WHERE availability) AS available,
                           COUNT(*) FILTER (WHERE NOT availability) AS unavailable
                    FROM donors
                    """
                )
                summary = cursor.fetchone()
    except DatabaseConfigurationError as error:
        flash(str(error), "error")
    except psycopg.Error:
        flash(
            "Could not load donor records. Check your Neon connection and try again.",
            "error",
        )

    return render_template(
        "index.html",
        donors=donors,
        summary=summary,
        blood_groups=BLOOD_GROUPS,
        selected_blood_group=blood_group,
        city_filter=city,
    )


@app.post("/add")
def add_donor():
    values, errors = validate_donor_form()
    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("index"))

    try:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_DONORS_TABLE)
                cursor.execute(
                    """
                    INSERT INTO donors (name, blood_group, city, contact, availability)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        values["name"],
                        values["blood_group"],
                        values["city"],
                        values["contact"],
                        values["availability"],
                    ),
                )
        flash("Donor added successfully.", "success")
    except DatabaseConfigurationError as error:
        flash(str(error), "error")
    except psycopg.Error:
        flash("Could not save the donor. Check your Neon connection and try again.", "error")
    return redirect(url_for("index"))


@app.route("/edit/<int:donor_id>", methods=("GET", "POST"))
def edit_donor(donor_id):
    donor = None
    form_errors = []

    if request.method == "POST":
        values, form_errors = validate_donor_form()
        if not form_errors:
            try:
                with database_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(CREATE_DONORS_TABLE)
                        cursor.execute(
                            """
                            UPDATE donors
                            SET name = %s, blood_group = %s, city = %s,
                                contact = %s, availability = %s
                            WHERE id = %s
                            """,
                            (
                                values["name"],
                                values["blood_group"],
                                values["city"],
                                values["contact"],
                                values["availability"],
                                donor_id,
                            ),
                        )
                        if cursor.rowcount == 0:
                            abort(404)
                flash("Donor updated successfully.", "success")
                return redirect(url_for("index"))
            except DatabaseConfigurationError as error:
                flash(str(error), "error")
            except psycopg.Error:
                flash("Could not update the donor. Check your Neon connection and try again.", "error")

    try:
        with database_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(CREATE_DONORS_TABLE)
                cursor.execute(
                    """
                    SELECT id, name, blood_group, city, contact, availability
                    FROM donors WHERE id = %s
                    """,
                    (donor_id,),
                )
                donor = cursor.fetchone()
    except DatabaseConfigurationError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))
    except psycopg.Error:
        flash("Could not load this donor. Check your Neon connection and try again.", "error")
        return redirect(url_for("index"))

    if donor is None:
        abort(404)
    if request.method == "POST":
        donor.update(values)
    return render_template(
        "edit.html",
        donor=donor,
        blood_groups=BLOOD_GROUPS,
        form_errors=form_errors,
    )


@app.post("/delete/<int:donor_id>")
def delete_donor(donor_id):
    try:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_DONORS_TABLE)
                cursor.execute("DELETE FROM donors WHERE id = %s", (donor_id,))
                deleted = cursor.rowcount
        if deleted:
            flash("Donor deleted successfully.", "success")
        else:
            flash("That donor no longer exists.", "error")
    except DatabaseConfigurationError as error:
        flash(str(error), "error")
    except psycopg.Error:
        flash("Could not delete the donor. Check your Neon connection and try again.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
