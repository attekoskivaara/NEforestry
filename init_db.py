import sqlite3
import json

# --- Likert questions ---
likert_questions = [
    {"id": "regional_economy", "text": "...the forest-based sector strengthens its role in regional economies …"},
    {"id": "local_owners", "text": "...the forest-based sector supports local forest owners …"},
    {"id": "carbon_substitution", "text": "...future end-use applications emphasize the use of wood as a substitute …"},
    {"id": "carbon_storage", "text": "...the forest-based sector actively enhances forest growth …"},
    {"id": "biodiversity", "text": "...forest management activities should avoid negative impacts on biodiversity …"},
    {"id": "local_sourcing", "text": "...forest-based sectors and wood construction favor local sourcing …"},
    {"id": "employment_conditions", "text": "...the forest-based sector provides stable employment opportunities …"},
    {"id": "training_development",
     "text": "...the forest-based sector strengthens regional capacity by providing professional development …"},
    {"id": "community_engagement", "text": "...the forest-based sector actively engages with local communities …"}
]

organization_options = [
    {"label": "Forest management organization", "value": "forest_mgmt"},
    {"label": "Foundation (e.g., forestry or conservation foundation)", "value": "foundation"},
    {"label": "Wood product manufacturer", "value": "manufacturer"},
    {"label": "State or regional government agency", "value": "state_gov"},
    {"label": "National government agency", "value": "national_gov"},
    {"label": "Design or engineering firm (e.g., structural or architectural)", "value": "design_firm"},
    {"label": "Contractor", "value": "contractor"},
    {"label": "University or Research institute", "value": "research"},
    {"label": "Other", "value": "other"},
]

role_options = [
    {"label": "Logger / forestry contractor", "value": "logger"},
    {"label": "Director / manager", "value": "director"},
    {"label": "Sales representative", "value": "sales_rep"},
    {"label": "Civil servant / public officer", "value": "civil_servant"},
    {"label": "Forester", "value": "forester"},
    {"label": "Researcher / academic", "value": "researcher"},
    {"label": "Designer / engineer", "value": "designer"},
    {"label": "Student", "value": "student"},
    {"label": "Other", "value": "other"},
]

new_england_states = [
    "Connecticut", "Maine", "Massachusetts", "New Hampshire", "Rhode Island", "Vermont"
]

# DEFAULTS (käyttäjän syöttämät muuttujat)
DEFAULTS = {
    "protWoodlands": 21,
    "unprotectedForest": 57,
    "wildlands": 2,
    "farmland": 5,
    "developed": 10,
    "waterAndWetlands": 5,
    "woodlands_area": 30.31,
    "wildlands_area": 1.29,
    "lumber": 336960,
    "lumbershare": 40,
    "paper": 336960,
    "papershare": 40,
    "from_lumber_to_pulp": 112207.68,
    "fuelwood": 168480,
    "fuelshare": 20,
    "import_lumber": 149700,
    "import_paper": 114900,
    "construction_multistory": 5,
    "construction_multistory_val": 0,  # Täydennä tarpeen mukaan
    "construction_single": 26,
    "construction_single_val": 0,
    "manufacturing": 12,
    "manufacturing_val": 0,
    "packaging": 13,
    "packaging_val": 0,
    "other": 9,
    "other_val": 0,
    "other_construction": 28,
    "other_construction_val": 0,
    "non_res_construction": 7,
    "non_res_construction_val": 0,
    "recovery_timber": 8000,
    "logging_intensity": 27,
    "regional_economy_cannot_answer": 0,
    "local_owners_cannot_answer": 0,
    "carbon_substitution_cannot_answer": 0,
    "carbon_storage_cannot_answer": 0,
    "biodiversity_cannot_answer": 0,
    "local_sourcing_cannot_answer": 0,
    "employment_conditions_cannot_answer": 0,
    "training_development_cannot_answer": 0,
    "community_engagement_cannot_answer": 0,

    }


def create_database():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # --- Yksi taulu kaikki vastaukset ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        email TEXT UNIQUE,

        -- Monivalinnat (JSON)
        state_checklist TEXT,
        organization_type TEXT,
        organization_type_other TEXT,
        prof_position TEXT,
        prof_position_other TEXT,
        years_experience INTEGER,

        -- Muuttujat / kuvaajien arvot
        protWoodlands REAL,
        unprotectedForest REAL,
        wildlands REAL,
        farmland REAL,
        developed REAL,
        waterAndWetlands REAL,
        lumbershare REAL,
        papershare REAL,
        from_lumber_to_pulp REAL,
        fuelshare REAL,
        import_lumber REAL,
        import_paper REAL,
        construction_multistory_val REAL,
        construction_single_val REAL,
        manufacturing_val REAL,
        packaging_val REAL,
        other_val REAL,
        other_construction_val REAL,
        non_res_construction_val REAL,
        recovery_timber REAL,
        logging_intensity REAL,
        
        -- Likert-kysymykset
        regional_economy INTEGER,
        local_owners INTEGER,
        carbon_substitution INTEGER,
        carbon_storage INTEGER,
        biodiversity INTEGER,
        local_sourcing INTEGER,
        employment_conditions INTEGER,
        training_development INTEGER,
        community_engagement INTEGER,
        
        regional_economy_cannot_answer INTEGER,
        local_owners_cannot_answer INTEGER,
        carbon_substitution_cannot_answer INTEGER,
        carbon_storage_cannot_answer INTEGER,
        biodiversity_cannot_answer INTEGER,
        local_sourcing_cannot_answer INTEGER,
        employment_conditions_cannot_answer INTEGER,
        training_development_cannot_answer INTEGER,
        community_engagement_cannot_answer INTEGER,
        
        reset_btn_1 INTEGER,
        reset_btn_2 INTEGER
    )
    """)

    conn.commit()
    conn.close()
    print("Database created successfully.")


if __name__ == "__main__":
    create_database()