import sqlite3
import os
from datetime import date
from flask import Flask, g, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "battery-tracker-dev-key"
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batteries.db")

# ── Brand configurations ──

BRANDS = {
    "Makita": {
        "voltages": [12, 18, 40],
        "primary": "#00b2a9",
        "bright": "#00cec3",
        "dim": "#008a83",
        "dark": "#1b2d2b",
        "ghost": "rgba(0, 178, 169, 0.08)",
        "glow": "rgba(0, 178, 169, 0.22)",
        "text_on_brand": "#ffffff",
    },
    "DeWalt": {
        "voltages": [12, 20, 60],
        "primary": "#febd17",
        "bright": "#ffd54f",
        "dim": "#d49a00",
        "dark": "#1a1a1a",
        "ghost": "rgba(254, 189, 23, 0.10)",
        "glow": "rgba(254, 189, 23, 0.25)",
        "text_on_brand": "#1a1a1a",
    },
    "Milwaukee": {
        "voltages": [12, 18],
        "primary": "#db0032",
        "bright": "#ff1744",
        "dim": "#b0002a",
        "dark": "#1a1a1a",
        "ghost": "rgba(219, 0, 50, 0.08)",
        "glow": "rgba(219, 0, 50, 0.22)",
        "text_on_brand": "#ffffff",
    },
    "AEG": {
        "voltages": [12, 18],
        "primary": "#ff6600",
        "bright": "#ff8533",
        "dim": "#cc5200",
        "dark": "#1a1a1a",
        "ghost": "rgba(255, 102, 0, 0.08)",
        "glow": "rgba(255, 102, 0, 0.22)",
        "text_on_brand": "#ffffff",
    },
    "Ryobi": {
        "voltages": [18, 36, 40],
        "primary": "#9bc53d",
        "bright": "#b0d95f",
        "dim": "#7da32e",
        "dark": "#1a1a1a",
        "ghost": "rgba(155, 197, 61, 0.10)",
        "glow": "rgba(155, 197, 61, 0.25)",
        "text_on_brand": "#1a1a1a",
    },
    "Bosch": {
        "voltages": [12, 18],
        "primary": "#005ca9",
        "bright": "#0077cc",
        "dim": "#004080",
        "dark": "#0d1b2a",
        "ghost": "rgba(0, 92, 169, 0.08)",
        "glow": "rgba(0, 92, 169, 0.22)",
        "text_on_brand": "#ffffff",
    },
    "Hikoki": {
        "voltages": [18, 36],
        "primary": "#00a651",
        "bright": "#00c965",
        "dim": "#008040",
        "dark": "#0d1f12",
        "ghost": "rgba(0, 166, 81, 0.08)",
        "glow": "rgba(0, 166, 81, 0.22)",
        "text_on_brand": "#ffffff",
    },
}

VALID_AH_RATINGS = [1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0, 12.0]
VALID_STATUSES = ["New", "In Use", "For Repair", "Repaired", "Dead"]


# ── Database helpers ──

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS batteries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            voltage INTEGER NOT NULL,
            ah_rating REAL NOT NULL,
            is_oem INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'In Use',
            status_changed TEXT,
            purchase_date TEXT,
            price REAL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    db.commit()


def get_setting(key, default=None):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    db.commit()


with app.app_context():
    init_db()


# ── Context processor: inject brand into all templates ──

@app.context_processor
def inject_brand():
    brand_name = get_setting("brand", "Makita")
    brand = BRANDS.get(brand_name, BRANDS["Makita"])
    return {
        "brand_name": brand_name,
        "brand": brand,
        "all_statuses": VALID_STATUSES,
    }


# ── Template filters ──

@app.template_filter('audate')
def au_date_filter(value):
    if not value:
        return ""
    try:
        parts = value.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except (IndexError, AttributeError):
        return value


@app.template_filter('age')
def age_filter(value):
    if not value:
        return ""
    try:
        purchased = date.fromisoformat(value)
        today = date.today()
        total_months = (today.year - purchased.year) * 12 + (today.month - purchased.month)
        if today.day < purchased.day:
            total_months -= 1
        if total_months < 0:
            return ""
        years = total_months // 12
        months = total_months % 12
        if years > 0 and months > 0:
            return f"{years}y {months}m"
        elif years > 0:
            return f"{years}y"
        elif months > 0:
            return f"{months}m"
        else:
            return "< 1m"
    except (ValueError, AttributeError):
        return ""


def _today_au():
    d = date.today()
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _append_history(existing_notes, entry):
    line = f"{_today_au()} - {entry}"
    if existing_notes:
        return existing_notes.rstrip() + "\n" + line
    return line


# ── Routes ──

@app.route("/")
def index():
    db = get_db()
    status_filter = request.args.get("status")

    if status_filter and status_filter in VALID_STATUSES:
        batteries = db.execute(
            "SELECT * FROM batteries WHERE status = ? ORDER BY label ASC, id DESC",
            (status_filter,),
        ).fetchall()
    else:
        status_filter = None
        batteries = db.execute(
            "SELECT * FROM batteries ORDER BY label ASC, id DESC"
        ).fetchall()

    # Stats always computed from ALL batteries (unfiltered)
    all_batteries = db.execute("SELECT * FROM batteries").fetchall()
    stats = {
        "count": len(all_batteries),
        "total_investment": sum(b["price"] for b in all_batteries if b["price"]),
        "voltages": {},
        "statuses": {},
    }
    for b in all_batteries:
        v = f"{b['voltage']}V"
        stats["voltages"][v] = stats["voltages"].get(v, 0) + 1
        s = b["status"]
        stats["statuses"][s] = stats["statuses"].get(s, 0) + 1

    filtered_investment = sum(b["price"] for b in batteries if b["price"])

    return render_template(
        "index.html",
        batteries=batteries,
        stats=stats,
        status_filter=status_filter,
        filtered_count=len(batteries),
        filtered_investment=filtered_investment,
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    brand_name = get_setting("brand", "Makita")
    brand = BRANDS.get(brand_name, BRANDS["Makita"])
    voltages = brand["voltages"]

    if request.method == "POST":
        label = request.form["label"].strip()
        voltage = request.form["voltage"]
        ah_rating = request.form["ah_rating"]
        is_oem = 1 if request.form.get("is_oem") == "1" else 0
        status = request.form.get("status", "New")
        status_changed = request.form.get("status_changed") or str(date.today())
        purchase_date = request.form.get("purchase_date") or None
        price = request.form.get("price") or None
        notes = request.form.get("notes", "").strip() or None

        if not label or not voltage or not ah_rating:
            flash("Label, voltage, and Ah rating are required.", "error")
            return render_template("form.html", battery=request.form, statuses=VALID_STATUSES, ah_ratings=VALID_AH_RATINGS, voltages=voltages)

        if float(ah_rating) not in VALID_AH_RATINGS:
            flash("Invalid Ah rating.", "error")
            return render_template("form.html", battery=request.form, statuses=VALID_STATUSES, ah_ratings=VALID_AH_RATINGS, voltages=voltages)

        if status not in VALID_STATUSES:
            flash("Invalid status.", "error")
            return render_template("form.html", battery=request.form, statuses=VALID_STATUSES, ah_ratings=VALID_AH_RATINGS, voltages=voltages)

        notes = _append_history(notes, f"Added - {status}")

        db = get_db()
        db.execute(
            """
            INSERT INTO batteries (label, voltage, ah_rating, is_oem, status, status_changed, purchase_date, price, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (label, int(voltage), float(ah_rating), is_oem, status, status_changed, purchase_date,
             float(price) if price else None, notes),
        )
        db.commit()
        flash(f"Battery {label} added.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", battery=None, statuses=VALID_STATUSES, ah_ratings=VALID_AH_RATINGS, voltages=voltages)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()
    brand_name = get_setting("brand", "Makita")
    brand = BRANDS.get(brand_name, BRANDS["Makita"])
    voltages = brand["voltages"]

    if request.method == "POST":
        label = request.form["label"].strip()
        voltage = request.form["voltage"]
        ah_rating = request.form["ah_rating"]
        is_oem = 1 if request.form.get("is_oem") == "1" else 0
        status = request.form.get("status", "In Use")
        purchase_date = request.form.get("purchase_date") or None
        price = request.form.get("price") or None
        notes = request.form.get("notes", "").strip() or None

        if not label or not voltage or not ah_rating:
            flash("Label, voltage, and Ah rating are required.", "error")
            return render_template("form.html", battery=request.form, statuses=VALID_STATUSES, ah_ratings=VALID_AH_RATINGS, voltages=voltages)

        old = db.execute("SELECT status, status_changed FROM batteries WHERE id = ?", (id,)).fetchone()
        if old and old["status"] != status:
            status_changed = str(date.today())
            notes = _append_history(notes, status)
        else:
            status_changed = request.form.get("status_changed") or (old["status_changed"] if old else str(date.today()))

        db.execute(
            """
            UPDATE batteries
            SET label = ?, voltage = ?, ah_rating = ?, is_oem = ?, status = ?,
                status_changed = ?, purchase_date = ?, price = ?, notes = ?
            WHERE id = ?
            """,
            (label, int(voltage), float(ah_rating), is_oem, status, status_changed,
             purchase_date, float(price) if price else None, notes, id),
        )
        db.commit()
        flash(f"Battery {label} updated.", "success")
        return redirect(url_for("index"))

    battery = db.execute("SELECT * FROM batteries WHERE id = ?", (id,)).fetchone()
    if battery is None:
        flash("Battery not found.", "error")
        return redirect(url_for("index"))

    # Include battery's current voltage in case brand changed
    bat_voltages = sorted(set(voltages + [battery["voltage"]]))
    return render_template("form.html", battery=battery, statuses=VALID_STATUSES, ah_ratings=VALID_AH_RATINGS, voltages=bat_voltages)


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    db = get_db()
    battery = db.execute("SELECT label FROM batteries WHERE id = ?", (id,)).fetchone()
    if battery:
        db.execute("DELETE FROM batteries WHERE id = ?", (id,))
        db.commit()
        flash(f"Battery {battery['label']} deleted.", "success")
    else:
        flash("Battery not found.", "error")
    return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        brand = request.form.get("brand")
        if brand in BRANDS:
            set_setting("brand", brand)
            flash(f"Brand set to {brand}.", "success")
        else:
            flash("Invalid brand.", "error")
        return redirect(url_for("settings"))

    current_brand = get_setting("brand", "Makita")
    return render_template("settings.html", brands=BRANDS, current_brand=current_brand)


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if not message:
            flash("Feedback message cannot be blank.", "error")
            return render_template("feedback.html")
        db = get_db()
        db.execute("INSERT INTO feedback (message) VALUES (?)", (message,))
        db.commit()
        flash("Thanks for your feedback!", "success")
        return redirect(url_for("index"))
    return render_template("feedback.html")


if __name__ == "__main__":
    app.run(debug=True)
