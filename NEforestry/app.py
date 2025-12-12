from dash import Dash, dcc, html, Input, Output, State
import dash
import plotly.graph_objects as go
import sqlite3
import pandas as pd
import dash_daq as daq
import dash_bootstrap_components as dbc
import numpy as np
import json
import hashlib
from flask import session, redirect
import datetime
import os

def format_question(question):
    if "bold" in question and question["bold"] in question["text"]:
        parts = question["text"].split(question["bold"])
        return html.P([
            parts[0],
            html.Span(question["bold"], style={"fontWeight": "bold"}),
            parts[1]
        ])
    else:
        return html.P(question["text"])


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def lerp(a, b, t):
    return int(a + (b - a) * t)


def color_from_diff(v, default):
    if v < 1.1:
        return "rgba(0,0,0,0)"  # transparent for tiny values

    diff = (v - default) / default

    # scale diff into [0,1] smoothly but not too fast
    t = min(1.0, abs(diff) ** 0.5)

    # Neutral grey
    gray = (180, 180, 180)

    if diff > 0:
        # grey → bright green
        target = (0, 255, 0)
    else:
        # grey → bright red
        target = (255, 0, 0)

    r = lerp(gray[0], target[0], t)
    g = lerp(gray[1], target[1], t)
    b = lerp(gray[2], target[2], t)

    return f"rgb({r},{g},{b})"
# total forest area (constant)

organization_options = [
    {"label": "Forest management organization", "value": "forest_mgmt"},
    {"label": "Foundation (e.g., forestry or conservation foundation)", "value": "foundation"},
    {"label": "Wood product manufacturer", "value": "manufacturer"},
    {"label": "State or regional government agency", "value": "state_gov"},
    {"label": "National government agency", "value": "national_gov"},
    {"label": "Design or engineering firm (e.g., structural or architectural)", "value": "design_firm"},
    {"label": "Contractor", "value": "contractor"},
    {"label": "University or Research institute", "value": "research"},
    {"label": "Other...", "value": "other"},
]

organization_size = [
    "1-10",
    "11-50",
    "51-250",
    "251+"
]

role_options = [
    {"label": "Logger / forestry contractor", "value": "logger"},
    {"label": "Director / manager", "value": "director"},
    {"label": "Sales representative", "value": "sales_rep"},
    {"label": "Civil servant / public officer", "value": "civil_servant"},
    {"label": "Forester", "value": "forester"},
    {"label": "Researcher / academic", "value": "researcher"},
    {"label": "Consultant", "value": "consultant"},
    {"label": "Designer / engineer", "value": "designer"},
    {"label": "Student", "value": "student"},
    {"label": "Other...", "value": "other"},
]

new_england_states = [
    "Connecticut",
    "Maine",
    "Massachusetts",
    "New Hampshire",
    "Rhode Island",
    "Vermont",
    "Other..."
]

TOTAL_FOREST = 31.6

TOTAL_DEMAND = 382452.3

DEFAULTS = {
    "protWoodlands": 21, #20.94,
    "unprotectedForest": 57, #58.49,
    "wildlands": 2, #1.52,
    "farmland": 5, #5.25,
    "developed": 10, #9.9,
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
    "import_lumber": 150000,
    "import_paper": 115000,
    "construction_multistory": 5,
    "construction_multistory_val": round(TOTAL_DEMAND * 0.05,- 2),
    "construction_single": 26,
    "construction_single_val": round(TOTAL_DEMAND * 0.26, -2),
    "manufacturing": 12,
    "manufacturing_val": round(TOTAL_DEMAND * 0.12, -2),
    "packaging": 13,
    "packaging_val": round(TOTAL_DEMAND * 0.13, -2),
    "other": 9,
    "other_val": round(TOTAL_DEMAND * 0.09, -2),
    "other_construction": 28,   #residential repair and remodeling
    "other_construction_val": round(TOTAL_DEMAND * 0.28, -2),
    "non_res_construction": 7,
    "non_res_construction_val": round(TOTAL_DEMAND * 0.07, -2),
    "recovery_timber": 8000,
    "logging_intensity": 27
}

DEFAULTS_NUMERIC = [
    DEFAULTS["lumber"],
    DEFAULTS["paper"],
    DEFAULTS["fuelwood"],
    DEFAULTS["import_lumber"],
    DEFAULTS["import_paper"],
    DEFAULTS["construction_multistory_val"],
    DEFAULTS["construction_single_val"],
    DEFAULTS["manufacturing_val"],
    DEFAULTS["packaging_val"],
    DEFAULTS["other_val"],
    DEFAULTS["other_construction_val"],
    DEFAULTS["non_res_construction_val"],  # tämä puuttui alkuperästä!
    1,   # placeholder default
    1,   # placeholder default
    DEFAULTS["recovery_timber"],
    DEFAULTS["from_lumber_to_pulp"]
]


logging_intensity_values = {1: 10, 2: 17, 3: 27, 4: 35, 5: 45}  # example mapping


# CSS
input_style = {
    "width": "120px",
    "padding": "5px 10px",
    "fontSize": "14px",
    "border": "1px solid #ccc",
    "borderRadius": "5px",
    "textAlign": "right",
    "transition": "all 0.2s",
    "outline": "none"
}

likert_questions = [
    {"id": "regional_economy",
     "text": "…the forest-based sector strengthens its role in regional economies, for example by generating revenues, creating jobs, and maintaining profitable operations? ",
     "bold": "strengthens its role in regional economies"},
    {"id": "local_owners",
     "text": "…the forest-based sector supports local forest owners by prioritizing the use of locally sourced wood and services?",
     "bold": "supports local forest owners"},
    {"id": "carbon_substitution",
     "text": "…future end-use applications emphasize the use of wood as a substitute for other materials — for example in construction or through innovative bioeconomy solutions?",
     "bold": "wood as a substitute"},
    {"id": "carbon_storage",
     "text": "…the forest-based sector actively enhances forest growth and increases carbon storage in forests to reduce overall environmental impacts (for example greenhouse gas emissions)?",
     "bold": "enhances forest growth and increases carbon storage"},
    {"id": "biodiversity",
     "text": "…forest management activities should avoid negative impacts on biodiversity and to actively protect or restore forest habitats?",
     "bold": "biodiversity and to actively protect or restore forest habitats?"},
    {"id": "local_sourcing",
     "text": "…forest-based sector and wood construction favor local sourcing and production to reduce transport-related environmental impacts?",
     "bold": "to reduce transport-related environmental impacts"},
    {"id": "employment_conditions",
     "text": "…the forest-based sector provides stable employment opportunities and promotes fair working conditions in the region?",
     "bold": "provides stable employment opportunities and promotes fair working conditions"},
    {"id": "training_development",
     "text": "…the forest-based sector strengthens regional capacity by providing professional development, training, and career advancement opportunities for its employees?",
     "bold": "strengthens regional capacity by providing"},
    {"id": "community_engagement",
     "text": "…the forest-based sector actively collaborates with local communities?",
     "bold": "collaborates with local communities?"}
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

server = app.server
server.secret_key = "supersecretkey123"

# app = Dash(__name__)
app.title = "VISION 2060 for New England Forests"

# Tarkistetaan ympäristö
ENV = os.getenv("FLASK_ENV", "development")  # oletus development

if ENV == "production":
    landcover_data = "/home/hulicupter/flask_app/NEforestry/landcover_data_031125.csv"
else:
    landcover_data = "landcover_data_031125.csv"

if ENV == "production":
    USERS_DB_FILE = "/home/hulicupter/flask_app/NEforestry/users.db"
    DATA_DB_FILE = "/home/hulicupter/flask_app/NEforestry/data.db"
else:
    USERS_DB_FILE = "users.db"
    DATA_DB_FILE = "data.db"


def render_question(question):
    """Render a question with optional bold text."""
    text = question["text"]
    bold_phrase = question.get("bold")

    if bold_phrase and bold_phrase in text:
        parts = text.split(bold_phrase)
        return html.P([
            parts[0],
            html.Span(bold_phrase, style={"fontWeight": "bold"}),
            parts[1]
        ])
    else:
        return html.P(text)


def check_user(email, password):
    conn = sqlite3.connect(USERS_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    if row and hash_password(password) == row[0]:
        return True
    return False

def make_sankey(values):
    labels = [
        "Woodlands (million acres)",  # 0
        "Timber harvesting in New England",                  # 1
        "Wildlands (million acres)",  # 2
        "Lumber",      # 3  (thousand ft³)
        "Pulp",  # 4
        "Fuelwood",    # 5
        "Lumber import",            # 6
        "Pulp import",             # 7
        "Conservation",                # 8
        "Construction multistory",      #9
        "Construction single family", # 10
        "Manufacturing",              # 11
        "Packaging",                  # 12
        "Other uses",                      # 13
        "Residential repair and remodeling",         # 14
        "Nonresidential construction", # 15
       # "",          # 16 paper placeholder
        "",             # 17 fuelwood placeholder
        "",             # 18 placeholder for wildlands
        ""             # 19
        ]


    woodlands = values.get("woodlands") or 0

    sources = [
        1, 1, 1, 6, 7, 3, 3, 3, 3, 3, 3, 3, 4, 5, 3, 3
    ]
    targets = [
        3, 4, 5, 3, 4, 9, 10, 11, 12, 13, 14, 15, 17, 18, 3, 4
    ]

    woodlands_volume = values.get("intensity_volume", 0)

    values_list = [
        values.get("lumber", 0),  # Intensity → Lumber
        values.get("paper",0),  # Intensity → Paper
        values.get("fuelwood",0),  # Intensity → Fuelwood
        values.get("import_lumber", 0),
        values.get("import_paper", 0),
        values.get("construction_multistory_val", 0),
        values.get("construction_single_val", 0),
        values.get("manufacturing_val", 0),
        values.get("packaging_val", 0),
        values.get("other_val", 0),
        values.get("other_construction_val", 0),
        values.get("non_res_construction_val", 0),
    #    1,
        1,
        1,
        values.get("recovery_timber", 0),
        values.get("from_lumber_to_pulp", 0)
    ]


#6D4C41 < tumma
#D2B48C < med. tumma
#F5DEB3 < vaalea
    node_colors = [
        # --- SOURCES (metsät + tuonti) ---
        "#6D4C41",  # 0: Woodlands
        "#6D4C41",  # 1: Intensity (lähde)
        "#6D4C41",  # 2: Wildlands

        "#D2B48C",  # 3: Lumber (source view)
        "#D2B48C",  # 4: Raw material for paper (source view)
        "#D2B48C",  # 5: Fuelwood (source view)

        "#6D4C41",  # 6: Import Lumber
        "#6D4C41",  # 7: Import Paper

        "#4CAF50",  # 8: Conservation (jos katsot lähteeksi)

        # --- PRODUCTS (massaräätälöinnin tuotetyypit) ---
        "#F5DEB3",  # 9: Construction multistory (tuoteryhmä)
        "#F5DEB3",  # 10: Construction single family
        "#F5DEB3",  # 11: Manufacturing
        "#F5DEB3",  # 12: Packaging

        # --- END USE / OTHER USES ---
        "#F5DEB3",  # 13: Other
        "#F5DEB3",  # 14: Other Construction
        "#F5DEB3",  # 15: Other Construction (duplikaatti node)

        # --- PLACEHOLDERS ---
        "rgba(0,0,0,0)",  # 16: Paper placeholder
        "rgba(0,0,0,0)",  # 17: Fuelwood placeholder
        "rgba(0,0,0,0)",  # 18: Paper placeholder

        # --- LOOP NODE (sama väri kuin lumber) ---
        "#4CAF50",  # 19: Lumber (loop)
    ]

    link_colors = [color_from_diff(v, default) for v, default in zip(values_list, DEFAULTS_NUMERIC)]

    special_flow_index = len(link_colors) - 1  # viimeinen linkki, lumber loop
    # customdata for every link

    labels_for_links = []
    for i in range(len(link_colors)):
        if i == special_flow_index:
            labels_for_links.append(
                "This flow is constant and follows lumber harvesting volumes linearly."
            )
        else:
            labels_for_links.append("")

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=30, thickness=20,
            label=labels,
            color=node_colors,
        ),
        link=dict(source=sources, target=targets, value=values_list, color=link_colors, label=labels_for_links)
    )])

    fig.add_annotation(
        text=(
            "Graph 2. Gray color indicates no change from 2020 values. Red indicates a decrease in values and green indicates an increase in values in 2060 compared to 2020. <br>"
            "Supply source: USDA Forest Service's Forest Inventory and Analysis program. Demand source: Brandeis et al. 2021. Status and trends for the U.S. forest products sector: a technical document supporting the Forest Service 2020 RPA Assessment."
        ),        xref="paper", yref="paper",
        x=0, y=-0.15,  # outside bottom left of plot
        showarrow=False,
        align="left",
        font=dict(size=12, color="gray"),
        xanchor="left", yanchor="top"
    )

    fig.add_annotation(
        x=0.3, y=-0.04,  # koordinaatit käsin
        text="Recovered timber",
        showarrow=False,
        font=dict(size=16)
    )

    fig.update_layout(title_text="", font_size=16,
                      height=550,
                      margin=dict(l=50, r=50, t=50, b=100),
                      )

    # remove borders
    fig.update_traces(node=dict(
        line=dict(color="rgba(0,0,0,0)", width=0)
    ))



    return fig


# --- Funktio, joka luo stacked line chartin ---
def make_stacked_bar(values):

    name_map = {
        "waterAndWetlands": "Water and Wetlands",
        "developed": "Development",
        "farmland": "Farmland",
        "unprotectedForest": "Unprotected Forest",
        "protWoodlands": "Protected Forest",
        "wildlands": "Wildlands"
    }
    """
    values = {
        "wildlands": float,
        "protwoodlands": float,
        "unprotectedForests": float,
        "farmland": float,
        "developed": float,
        "water_wetlands": float  # optional dummy
    }
    """
    # Ladataan historiadata
    df = pd.read_csv(landcover_data, sep=None, engine="python")

    categories = ["wildlands", "protWoodlands", "unprotectedForest", "farmland", "developed", "waterAndWetlands"]
    colors = ["#33691E", "#2E7D32", "#4CAF50", "#FBC02D", "#D32F2F", "#9E9E9E"]
    marker_symbols = ["circle", "square", "diamond", "triangle-up", "cross", "x"]

    years = df["year"].tolist() + [2060]  # history + projection year

    fig = go.Figure()

    for i, cat in enumerate(categories):
        # Historiallinen data
        hist_vals = df[cat].tolist() if cat in df.columns else [0] * len(df)
        # Projektiopiste 2050
        proj_val = values.get(cat, 0)

        # Yhdistetään historia ja projektiopiste
        y_values = hist_vals + [proj_val]

        fig.add_trace(go.Scatter(
            name=name_map.get(cat, cat),
            x=years,
            y=y_values,
            mode="lines+markers",
            line=dict(color=colors[i], width=3, dash="dot" if i >= 0 else "solid"),  # dot näyttää visuaalisesti proj
            marker=dict(symbol=marker_symbols[i], size=6),
            stackgroup="one"
        ))

    fig.update_layout(
        title="Land Cover Distribution (% of total area)",
      #  xaxis_title="Year",
        yaxis=dict(range=[0, 100], title="Share of total land area (%)"),
        template="plotly_white",
        legend_itemclick=False,           # estää klikkauksen
        legend_itemdoubleclick=False,
        shapes=[
            dict(
                type="line",
                x0=2020, x1=2020,       # pystysuora viiva vuonna 2020
                y0=0, y1=100,           # koko y-akselin alue
                xref="x",
                yref="y",
                line=dict(color="black", width=2, dash="dash")  # dashed viiva
            )
        ]
    )

    # Add footnote as annotation
    fig.add_annotation(
        text="Graph 1. Source: Harvard forest (Wildlands and Woodlands Report), USGS (National Land Cover Database)",
        xref="paper", yref="paper",
        x=0, y=-0.15,  # outside bottom left of plot
        showarrow=False,
        font=dict(size=12, color="gray"),
        xanchor="left", yanchor="top"
    )

    return fig


login_layout = dbc.Container(
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H3("Survey: VISION 2060 for New England Forests", className="text-center mb-4"),
                    dbc.Input(id="login-email", placeholder="Email", type="email", className="mb-3"),
                    dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-3"),
                    dbc.Button("Login", id="login-btn", color="primary", className="w-100"),
                    html.Div(id="login-msg", className="mt-3 text-danger text-center"),
                ]),
                className="shadow p-4",
            ),
            width=8,  # card width
            className="offset-md-2"  # center horizontally
        )
    ),
    className="mt-5"
)

thankyou_layout = dbc.Container(
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H3(
                        "Thank you for participating in the survey!",
                        className="text-center mb-4"
                    ),

                    html.P(
                        "Your responses have been successfully submitted.",
                        className="text-center"
                    ),

                    html.P(
                        "You may return and update your answers at any time using your email "
                        "address and the provided password until March 1st, 2026. Only your most recent submission "
                        "will be considered.",
                        className="text-center"
                    ),

                    html.Hr(className="my-4"),

                    dbc.Button(
                        "Return to Login",
                        id="thankyou-login-btn",
                        href="/login",
                        color="primary",
                        className="w-100"
                    )
                ]),
                className="shadow p-4"
            ),
            width=8,
            className="offset-md-2"
        )
    ),
    className="mt-5"
)

def survey_layout(defaults, db_data, sankey_fig=None, bar_fig=None):
    if db_data is None:
        db_data = {}
    return html.Div([
  #  dcc.Store(id="login-state", data=False),

        html.Div([
            html.H3("Survey: VISION 2060 for New England Forests", style={"fontWeight": "bold", "marginBottom": "10px"}),
            html.H4("About this survey", style={"marginTop": "20px", "marginBottom": "10px"}),

            html.P([
                "This survey asks for your views on ",
                html.Span(
                    "what the future of forests and the forest industry in New England should look like in 2060",
                    style={"fontWeight": "bold"}
                ),
                ". Your responses will be treated anonymously and analyzed only in relation to the background information you provide in this survey."
            ], style={"lineHeight": "1.5", "fontSize": "16px"}),

            html.Div(
                "Answer all the questions in a way that reflects your preferred vision for the year 2060.",
                style={
                    "fontSize": "16px",
                    "lineHeight": "1.4",
                    "fontWeight": "bold",
                    "color": "#856404",
                    "backgroundColor": "#fff3cd",
                    "padding": "8px",
                    "borderRadius": "5px",
                    "border": "1px solid #ffeeba",
                    "marginBottom": "15px"
                }
            ),

            html.P([
                "The order in which you answer the survey does not matter. However, ",
                html.Span("your adjustments may affect other variables in other parts of the study.",
                          style={"fontWeight": "bold"}),
                " For example, increasing or decreasing the area of protected or unprotected forest land in Graph 1 will impact the amount of timber harvesting in New England in Graph 2."
            ]),

            html.P([
                html.Span("You can submit your responses and log out at the end of the survey. You can login again using your credentials to change your answers until 31th of March 2026",
                        style={"fontWeight": "bold"}),
            ]),

        ], style={
            "width": "100%",
            "padding": "20px",
            "backgroundColor": "#f9f9f9",
            "border": "1px solid #ddd",
            "borderRadius": "8px",
            "maxWidth": "1200px",
            "margin": "auto",
            "minHeight": "250px"
        }),


        html.Div([
        # Otsikko omalla rivillään
        html.H3(
            "1. Background information",
            style={
                "gridColumn": "1 / -1",  # vie koko rivin
                "marginBottom": "20px",
                "marginTop": "40px",
                "fontWeight": "bold"
    #            "textAlign": "center"
            }
        ),

        # Vasemman sarakkeen sisältö (osavaltiot)
        html.Div([
            html.Label(
                "Please mark the state(s) where you work. You can select more than one:",
                style={"marginBottom": "10px", "display": "block"}
            ),
            dbc.Checklist(
                options=[{"label": state, "value": state} for state in new_england_states],
                id="state-checklist",
                value=defaults.get("state_checklist", []),
                inline=False,
                switch=False
            ),
            dcc.Input(
                id="state_other",
                type="text",
                value=defaults.get("state_other", ""),
                placeholder="Please specify if 'Other'",
                style={
                    "width": "400px",
                    "height": "80px",  # lisää korkeutta (noin 3 riviä)
                    "marginBottom": "30px",
                    "resize": "vertical"  # sallii käyttäjän venyttää kenttää tarvittaessa
                }
            ),

            dbc.Label("How many people are working in your organization?"),
            dbc.RadioItems(
                id="organization_size",
                options=organization_size,  # same options list as before
                value=defaults.get("organization_size"),  # single default value
                inline=False,
                style={"marginBottom": "20px"}
            ),

        ], style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "padding": "10px 20px"
        }),

        # Oikean sarakkeen sisältö (työtehtävä jne.)
        html.Div([
            dbc.Label("Which of the following categories best describe your organization?"),
            dbc.Checklist(
                id="organization_type",
                options=organization_options,
                value=defaults.get("organization_type", []),
                inline=False,
                style={"marginBottom": "20px"}
            ),
            dcc.Input(
                id="organization_type_other",
                type="text",
                value=defaults.get("organization_type_other", ""),
                placeholder="Please specify if 'Other'",
                style={
                    "width": "400px",
                    "height": "80px",  # lisää korkeutta (noin 3 riviä)
                    "marginBottom": "30px",
                    "resize": "vertical"  # sallii käyttäjän venyttää kenttää tarvittaessa
                }
            ),

            # --- Position / role ---
            dbc.Label("Which of the following best describes your own position or role in the organization?"),
            dbc.Checklist(
                id="prof_position",
                options=role_options,
                value=defaults.get("prof_position", []),
                inline=False,
                style={"marginBottom": "20px"}
            ),
            dcc.Input(
                id="prof_position_other",
                type="text",
                value=defaults.get("prof_position_other", ""),
                placeholder="Please specify if 'Other'",
                style={
                    "width": "400px",
                    "height": "80px",  # lisää korkeutta (noin 3 riviä)
                    "marginBottom": "30px",
                    "resize": "vertical"  # sallii käyttäjän venyttää kenttää tarvittaessa
                }
            ),

            html.Label("How many years have you worked in your current or similar position?",
                       style={"marginBottom": "5px"}),

            dcc.Input(
                id="years_experience",
                type="number",
                min=0,
                max=60,
                value=defaults.get("years_experience"),
                placeholder="Enter number of years",
                style={"width": "150px", "marginBottom": "40px"}
            ),
        ], style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "padding": "10px 20px"
        }),
    ],
        style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",  # kaksi saraketta
            "gap": "20px",
            "margin": "auto",
            "maxWidth": "1200px"
        }),


    html.Hr(style={
        "border": "none",  # remove default border
        "borderTop": "2px solid #ccc",  # grey line
        "margin": "20px 0"  # vertical spacing
    }),

    # --- Yläosa: bar chart + forest inputs (2 columns) + instructions ---
    html.Div([
        # --- Chart on top, full width ---
        html.Div([
            html.H3("2. Land Cover", style={
                "gridColumn": "1 / -1",  # vie koko rivin
                "marginBottom": "20px",
                "marginTop": "40px",
                "fontWeight": "bold"
            }),
            html.P([
                "Adjust the land area parameters individually based on ",
                html.Span("your desired future scenario in 2060", style={"fontWeight": "bold"}),
                "."
            ]),
            html.P("Click 'Set everything to default' to restore initial values in this part of the survey."),

            html.P("Please note: For the both graphs to update the land cover shares must sum to 100%.",
                   style={
                       "fontSize": "16px",
                       "lineHeight": "1.4",
                       "fontWeight": "bold",
                       "color": "#856404",  # dark brownish for readability
                       "backgroundColor": "#fff3cd",  # light yellow/orange highlight
                       "padding": "8px",
                       "borderRadius": "5px",
                       "border": "1px solid #ffeeba"  # subtle border for emphasis
                   }
                   ),
            html.P("Please note: Both Unprotected Forests and Protected Forests can be used for timber harvesting, and"
                   " their assigned land values influence timber production in Part 3 of the survey.",
                   style={
                       "fontSize": "16px",
                       "lineHeight": "1.4",
                       "fontWeight": "bold",
                       "color": "#856404",  # dark brownish for readability
                       "backgroundColor": "#fff3cd",  # light yellow/orange highlight
                       "padding": "8px",
                       "borderRadius": "5px",
                       "border": "1px solid #ffeeba"  # subtle border for emphasis
                   }
                   ),

        ], style={
            "width": "100%",
            "padding": "20px",
        #    "backgroundColor": "#f9f9f9",
        #    "border": "1px solid #ddd",
            "borderRadius": "8px",
            "maxWidth": "1200px",
            "margin": "auto",
            "minHeight": "250px"
        }),


        html.Div([
            dcc.Graph(id="forest-bar",
                figure=bar_fig if bar_fig else make_stacked_bar(form_defaults),
                      config={"displayModeBar": False, "staticPlot": True})
        ], style={
            "width": "100%",
            "padding": "20px",
            "maxWidth": "1200px",
            "margin": "auto",
            "marginBottom": "30px"
        }),

        # --- Inputs (2 columns) + instructions ---
        html.Div([
            # Vasemmalla: DAQ numeric inputs 2x3 + reset button
            html.Div([
                html.Div(id="share-warning-land", children="✅ Shares sum to 100%",
                         style={"color": "green", "fontWeight": "bold", "marginBottom": "10px"}),

                html.Div([
                    # Column 1
                    html.Div([
                        html.Label([
                            html.Span("Unprotected Forests (%) ", style={"fontWeight": "bold"}),
                            html.Span(
                                "definition ",
                                title=(
                                    "Publicly and privately owned forests that are not protected from development"
                                ),
                                style={
                                    "cursor": "help",
                                    "color": "#007BFF",
                                    "marginLeft": "5px",
                                    "fontWeight": "bold"
                                }
                            ),
                            html.Span(f"(in 2020: {DEFAULTS['unprotectedForest']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                        ], style={"display": "block", "marginBottom": "5px"}),
                        daq.NumericInput(
                            id="unprotectedForest",
                            value=get_default(defaults, "unprotectedForest"),
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        ),

                        html.Label([
                            html.Span("Developed (%) ", style={"fontWeight": "bold"}),
                            html.Span(
                                "definition ",
                                title=(
                                    "Built environment where people live and work, including cities, suburbs, towns, "
                                    "and villages"
                                ),
                                style={
                                    "cursor": "help",
                                    "color": "#007BFF",
                                    "marginLeft": "5px",
                                    "fontWeight": "bold"
                                }
                            ),
                            html.Span(f"(in 2020: {DEFAULTS['developed']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                        ], style={"display": "block", "marginBottom": "5px"}),
                        daq.NumericInput(
                            id="developed",
                            value=get_default(defaults, "developed"),
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        ),

                        html.Label([
                            html.Span("Preserved Wildlands (%) ", style={"fontWeight": "bold"}),
                            html.Span(
                                "definition ",
                                title=(
                                    "Publicly and privately owned forests in which no active management occurs. "
                                    "Natural processes shape the landscape over time"
                                ),
                                style={
                                    "cursor": "help",
                                    "color": "#007BFF",
                                    "marginLeft": "5px",
                                    "fontWeight": "bold"
                                }
                            ),
                            html.Span(f"(in 2020: {DEFAULTS['wildlands']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                        ], style={"display": "block", "marginBottom": "5px"}),
                        daq.NumericInput(
                            id="wildlands",
                            value=get_default(defaults, "wildlands"),
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        )
                    ], style={"flex": "1", "display": "flex", "flexDirection": "column"}),

                    # Column 2
                    html.Div([
                        html.Label([
                            html.Span("Protected Forests (%) ", style={"fontWeight": "bold"}),
                            html.Span(
                                "definition ",
                                title=(
                                    "Protected forests are voluntarily protected from development and "
                                    "managed for forest products, water supply, wildlife habitat, "
                                    "recreation, aesthetics, and other objectives."
                                ),
                                style={
                                    "cursor": "help",
                                    "color": "#007BFF",
                                    "marginLeft": "5px",
                                    "fontWeight": "bold"
                                }
                            ),
                            html.Span(f"(in 2020: {DEFAULTS['protWoodlands']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                        ], style={"display": "block", "marginBottom": "5px"}),
                        daq.NumericInput(
                            id="protWoodlands",
                            value=get_default(defaults, "protWoodlands"),
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        ),

                        html.Label([
                            html.Span("Farmland (%) ", style={"fontWeight": "bold"}),
                            html.Span(
                                "definition ",
                                title=(
                                    "Non-forested land that is used as farmland (conserved or unconserved)"
                                ),
                                style={
                                    "cursor": "help",
                                    "color": "#007BFF",
                                    "marginLeft": "5px",
                                    "fontWeight": "bold"
                                }
                            ),
                            html.Span(f"(in 2020: {DEFAULTS['farmland']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                        ], style={"display": "block", "marginBottom": "5px"}),
                        daq.NumericInput(
                            id="farmland",
                            value=get_default(defaults, "farmland"),
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        ),

                        html.Label([
                            html.Span("Water & Wetlands (%) ", style={"fontWeight": "bold"}),
                            html.Span(f"(in 2020: {DEFAULTS['waterAndWetlands']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"}),
                            html.Span(" Constant or considered insignificant in the study",
                            style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"}),
                        ], style={"display": "block", "marginBottom": "5px"}),

                        daq.NumericInput(
                            id="waterAndWetlands",
                            value=get_default(defaults, "waterAndWetlands"),
                            min=0, max=100, size=70,
                            disabled=True,
                            style={
                                "display": "block",
                                "marginBottom": "20px",
                                "textAlign": "right",
                                "backgroundColor": "#e0e0e0",
                                "color": "#000"
                            }
                        ),
                    ], style={"flex": "1", "display": "flex", "flexDirection": "column", "marginLeft": "20px"})
                ], style={"display": "flex", "flexDirection": "row"}),
            ], style={"flex": "1", "display": "flex", "flexDirection": "column"}),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "1fr",
            "gap": "20px",
            "margin": "auto",
            "maxWidth": "1200px"
        })
    ], style={"width": "100%"}),
    # Alempi osa: Sankey ja syöttökentät
    dcc.Store(id="model-data"),
    dcc.Store(id="wildlands_area"),
    dcc.Store(id="woodlands_area"),

    html.Div([
        html.Button("Set land cover variables to default", id="reset-btn-1", n_clicks=0,
                    style={
                        "marginTop": "20px",
                        "padding": "12px 26px",
                        "fontWeight": "bold",
                        "fontSize": "16px",
                        "color": "white",
                        "background": "linear-gradient(135deg, #007BFF 0%, #0056D2 100%)",
                        "border": "none",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "boxShadow": "0 4px 8px rgba(0,0,0,0.15)",
                        "transition": "all 0.2s ease-in-out",
                    }),
        ], style={
        "flex": "1",
        "display": "flex",
        "flexDirection": "column",
        "marginLeft": "20px",
        "alignItems": "center"}
        ),

    html.Hr(style={
        "border": "none",  # remove default border
        "borderTop": "2px solid #ccc",  # grey line
        "margin": "20px 0"  # vertical spacing
    }),

        # Sankey diagram

    html.Div([
        html.H3("3. Material flow chart", style={
            "gridColumn": "1 / -1",  # vie koko rivin
            "marginBottom": "20px",
            "marginTop": "40px",
            "fontWeight": "bold"
        }),
        html.P([
            "For each stage of the forest and wood product value chain, indicate ",
            html.Span(
                "how you would like annual wood supply and demand to change from 2020 to 2060",
                style={"fontWeight": "bold"}
            ),
            " based on your preferred future situation."
        ]),
        html.P([
            html.B("3.1 Timber sources in New England:"),
            " Adjust the slider to reflect your average harvesting intensity in New England forests. "
            "Additionally, set lumber and pulpwood imports to your desired levels."
        ]),

        html.P([
            html.B("3.2 Timber supply by assortments:"),
            " Adjust the percentages of harvests allocated to lumber, pulpwood, and fuelwood."
        ]),

        html.P([
            html.B("3.3 Lumber demand by enduse:      "),
            " Use the input fields below to define how the end-use distribution should develop until 2060."
        ]),

        html.P("Click “Set everything to default” to restore the initial values in this part of the survey."),
        html.P("Please note: Product type percentages must sum up to 100%.",
               style={
                   "fontSize": "16px",
                   "lineHeight": "1.4",
                   "fontWeight": "bold",
                   "color": "#856404",  # dark brownish for readability
                   "backgroundColor": "#fff3cd",  # light yellow/orange highlight
                   "padding": "8px",
                   "borderRadius": "5px",
                   "border": "1px solid #ffeeba"  # subtle border for emphasis
               }
               ),
        html.P("Please note: Demand must match supply with an accuracy of 5,000 mcf.",
               style={
                   "fontSize": "16px",
                   "lineHeight": "1.4",
                   "fontWeight": "bold",
                   "color": "#856404",  # dark brownish for readability
                   "backgroundColor": "#fff3cd",  # light yellow/orange highlight
                   "padding": "8px",
                   "borderRadius": "5px",
                   "border": "1px solid #ffeeba"  # subtle border for emphasis
               }
               ),
        html.P("Please note: The unit mcf refers to thousand cubic feet of wood-based products (e.g., timber, lumber, pulpwood, and fuelwood)",
               style={
                   "fontSize": "16px",
                   "lineHeight": "1.4",
                   "fontWeight": "bold",
                   "color": "#856404",  # dark brownish for readability
                   "backgroundColor": "#fff3cd",  # light yellow/orange highlight
                   "padding": "8px",
                   "borderRadius": "5px",
                   "border": "1px solid #ffeeba"  # subtle border for emphasis
               }
               )
    ], className='col-3', style={
        "width": "100%",
        "padding": "20px",
       # "backgroundColor": "#f9f9f9",
       # "border": "1px solid #ddd",
        "borderRadius": "8px",
        "maxWidth": "1200px",
        "margin": "auto",
        "minHeight": "150px",
        "marginTop": "30px"
    }),



html.Div([
    html.Div(
    [
        # Title ylhäällä
        html.Div("Change from 2020", style={"fontWeight": "bold", "marginBottom": "5px"}),

        # Gradient bar
        html.Div(
            style={
                "width": "250px",
                "height": "20px",
                "background": "linear-gradient(to right, red, #b4b4b4, lime)",
                "border": "1px solid #aaa",
                "borderRadius": "4px",
            }
        ),

        # Legend text
        html.Div(
            [
                html.Span("Lower", style={"color": "red", "display": "inline-block", "width": "80px", "textAlign": "left"}),
                html.Span("Not changed", style={"color": "black", "display": "inline-block", "width": "90px", "textAlign": "center"}),
                html.Span("Higher", style={"color": "green", "display": "inline-block", "width": "80px", "textAlign": "right"}),
            ],
            style={"fontSize": "12px", "marginTop": "5px"}
        ),
    ],
        style={
            "position": "absolute",   # 🔹 Absoluuttinen sijainti
            "top": "60px",           # 🔹 Nosta legendiä Sankeyn päälle
            "left": "0",              # 🔹 Vasempaan reunaan
            "zIndex": "10",           # 🔹 Varmistaa, että se näkyy päällekkäin
            "background": "rgba(255,255,255,0.8)",  # 🔹 Hieman läpinäkyvä tausta
            "padding": "5px",
            "borderRadius": "4px",
        }),


            dcc.Graph(id="sankey",
                figure=sankey_fig if sankey_fig else make_sankey(form_defaults),
                      config={"displayModeBar": False})
        ], style={
            "position": "relative",
            "marginTop": "40px",
            "paddingTop": "60px",
            "gap": "20px",
            "margin": "auto",
            "maxWidth": "1500px",
            "width": "100%",

        }),

      #  html.Hr(style={"borderTop": "2px solid #ccc", "margin": "15px 0"}),

        # four-column input grid
    html.Div([
        # --- Column 1: Logging + Imports ---
        html.Div([
            html.H4("3.1. Timber sources in New England ", style={"fontWeight": "bold", "marginBottom": "10px"}),

            html.Div([

             #   html.Label("Total roundwood market size = ", style={"fontWeight": "bold"}),
                html.Label([
                    html.Span("Timber harvesting per acre (mcf / acre) ", style={"fontWeight": "bold"}),
                    html.Span(f"(in 2020: {DEFAULTS['logging_intensity']} mcf/acre)",
                                style={"fontWeight": "normal"})
                    ]),
                dcc.Slider(
                    id="logging_intensity", min=10, max=45, step=0.5,
                    value=defaults.get("logging_intensity", 27),
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={i: str(i) for i in range(10, 46, 10)}
                ),

                html.Div(id="total_logging", style={"marginTop": "5px", "fontWeight": "bold", "marginBottom": "10px"}),

                html.Div([
                    html.Label([
                        html.Span("+ Import lumber* ", style={"fontWeight": "bold", "display": "inline-block"}),
                        html.Span(f"(in 2020: {DEFAULTS['import_lumber']:,})",
                                    style={"fontWeight": "normal", "marginLeft": "5px"})
                    ], style={"display": "block", "marginBottom": "10px"}),  # varmistaa block-tason spacing
                dbc.InputGroup(
                    [
                        dbc.Input(
                            id="import_lumber",
                            type="number",
                            min=0,
                            max=500000,
                            step=100,
                            value=defaults.get("import_lumber", int(150000)),
                            required=False,
                            style={
                                "width": "120px",
                                "textAlign": "right"
                            }
                        ),
                        dbc.InputGroupText("mcf")
                    ],
                    style={"marginBottom": "20px"})


                ], style={"paddingTop": "40px", "width": "100%"}),


                html.Label([
                    html.Span("+ Import wood for pulp* ", style={"fontWeight": "bold"}),
                    html.Span(f"(in 2020: {DEFAULTS['import_paper']:,})", style={"fontWeight": "normal"})
                ]),
                dbc.InputGroup(
                    [
                        dbc.Input(
                            id="import_paper",
                            type="number",
                            min=0,
                            max=500000,
                            step=100,
                            value=defaults.get("import_paper", int(115000)),
                            required=False,
                            style={
                                "width": "120px",
                                "textAlign": "right"
                            }
                        ),
                        dbc.InputGroupText("mcf")
                    ],
                    style={"marginBottom": "20px"}),

                html.Div(id="timber_supply", className="bottom-line"),
                html.P(""),
                html.P("*Please note: enter values rounded to the nearest hundred."),


            ], style={
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "flex-start",
                "width": "100%",
                "minWidth": "0",
                "border": "1px solid #ddd",
                "borderRadius": "12px",
                "padding": "12px",
                "marginBottom": "20px",
                "backgroundColor": "#fafafa",
                "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
            }),
        ], className='col-3', style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
            "width": "100%",
            "minWidth": "0",
            #"maxWidth": "200px"
        }),

            # --- Column 2: Products ---
            html.Div([
                html.H4("3.2. Timber supply by assortments*",
                           style={'fontWeight': 'bold', "marginBottom": "10px"}),

                html.Div([

                    # Lumber
               #     html.Label("Lumber total", style={"fontWeight": "bold"}),
                    html.Div(id="capacity-status", children="100% ✅ Balanced", className="top-item",
                             style={"color": "green", "marginTop": "10px", "marginBottom": "10px"}),

                    # Lumber share
                    html.Label([
                        html.Span("Lumber share (%) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['lumbershare']}%)", style={"fontWeight": "normal"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    dbc.InputGroup([
                          dbc.Input(
                                id="lumbershare",
                                type="number",
                                min=0,
                                max=100,
                                step=1,
                                value=defaults.get("lumbershare", (40)),
                                size="sm",
                                style={
                                    "textAlign": "right",
                                    "width": "70px",
                                    "flex": "0 0 70px",
                                }
                            ),
                            dbc.InputGroupText("%")
                        ],
                        style={"marginBottom": "20px"}),

                    html.Label([
                        html.Span("Recovered lumber**", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition",
                            title="Recovered from construction and demolition for example",
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),


                    ], style={"display": "block", "marginBottom": "5px"}),

                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id="recovery_timber",
                                type="number",
                                min=0,
                                max=20000,
                                step=100,
                                value=defaults.get("recovery_timber", 8000),
                                style={"width": "80px", "textAlign": "right"}
                            ),
                            dbc.InputGroupText("mcf")
                        ],
                        className="d-flex flex-wrap justify-content-end align-items-center",
                        style={"marginBottom": "2px"}
                    ),
                    html.Span("Maximum 20,000", style={"fontSize": "13px", "marginLeft": "auto"}),

                    html.Div(id="lumber_supply_text", className="line-item", style={"marginTop": "20px", "marginBottom": "20px"}
),

                    dcc.Store(id="lumber", data=DEFAULTS["lumber"]),
                    dcc.Store(id="paper", data=DEFAULTS["paper"]),
                    dcc.Store(id="fuelwood", data=DEFAULTS["fuelwood"]),

                    # Pulp
             #       html.Label("Pulp total", style={"fontWeight": "bold"}),
                    html.Div(id="paper_total"),

                    html.Label([
                        html.Span("Pulpwood share (%) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['papershare']}%)", style={"fontWeight": "normal"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    dbc.InputGroup([
                          dbc.Input(
                                id="papershare",
                                type="number",
                                min=0,
                                max=100,
                                step=1,
                                value=defaults.get("papershare", (40)),
                                size="sm",
                                style={
                                    "textAlign": "right",
                                    "width": "70px",
                                    "flex": "0 0 70px",
                                }
                            ),
                            dbc.InputGroupText("%")
                        ],
                        style={"marginBottom": "20px"}),


                    html.Div(id="pulp_supply_text", className="line-item",
                             style={"marginTop": "20px", "marginBottom": "20px"}),


                    dcc.Store(id="from_lumber_to_pulp", data=DEFAULTS["from_lumber_to_pulp"]),

                    # Fuelwood
                #    html.Label("Fuelwood total", style={"fontWeight": "bold"}),
                    html.Div(id="fuel_total"),

                    html.Label([
                        html.Span("Fuelwood share (%) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['fuelshare']}%)", style={"fontWeight": "normal"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    dbc.InputGroup([
                          dbc.Input(
                                id="fuelshare",
                                type="number",
                                min=0,
                                max=100,
                                step=1,
                                value=defaults.get("fuelshare", (20)),
                                size="sm",
                                style={
                                    "textAlign": "right",
                                    "width": "70px",
                                    "flex": "0 0 70px",
                                }
                            ),
                            dbc.InputGroupText("%")
                        ],
                        style={"marginBottom": "20px"}),

                    html.Div(id="fuel_supply_text", className="line-item",
                             style={"marginTop": "20px", "marginBottom": "20px"}),

                    html.P(""),
                    html.P("*Please note: Please consider your preferred long-term level, acknowledging that harvested wood cannot be allocated disproportionately to a single product category, especially over extended periods."),
                    html.P("**Please note: For recovered lumber, enter values rounded to the nearest hundred."),

                    # Share status box
                    html.Div(id="share-warning", style={"fontWeight": "bold", "marginTop": "10px"})
                ], id="share_style_box",

            ),

            ], className='col-3', style={
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
                "width": "100%",
                "minWidth": "0",


            }),

            # --- Column 3: End uses ---
            html.Div([
                html.H4("3.3. Lumber demand by enduse", style={'fontWeight': 'bold', "marginBottom": "10px"}),
                html.Div([
                    # Construction (multifamily)
                    html.Label([
                        html.Span("Construction (multifamily) ", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "Includes also mobile and modular housing units"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),
                        html.Span(f"(in 2020: {DEFAULTS['construction_multistory_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    html.Div([
                        dbc.Input(
                            id="construction_multistory_val",
                            type="number",
                            value=defaults.get("construction_multistory_val", (DEFAULTS["construction_multistory_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={
                                "width": "100px",
                                "margin": "0 5px 0 0",  # pieni väli Spanin ja Inputin väliin
                                "textAlign": "right",
                            },
                        ),
                        html.Span(id="construction_multistory_change", style={"fontWeight": "normal"})
                    ],
                        style={
                            "display": "flex",
                            "alignItems": "center",  # keskittää vaakasuoraan
                            "marginBottom": "20px"
                        }),

                    # daq.NumericInput(
                    #     id="construction_multistory_val",
                    #     value=DEFAULTS["construction_multistory_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),

                    # Construction (single-family)
                    html.Label([
                        html.Span("Construction (single-family) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['construction_single_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    html.Div([
                        dbc.Input(
                            id="construction_single_val",
                            type="number",
                            value=defaults.get("construction_single_val", (DEFAULTS["construction_single_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={
                                "width": "100px",
                                "margin": "0 5px 0 0",  # pieni väli Spanin ja Inputin väliin
                                "textAlign": "right",
                            },
                        ),
                        html.Span(id="construction_single_change", style={"fontWeight": "normal"})
                    ],
                        style={
                            "display": "flex",
                            "alignItems": "center",  # keskittää vaakasuoraan
                            "marginBottom": "20px"
                        }),


                    # daq.NumericInput(
                    #     id="construction_single_val",
                    #     value=DEFAULTS["construction_single_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),

                    # Manufacturing
                    html.Label([
                        html.Span("Manufacturing", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "Includes for example furniture production for household, commercial, and"
                                " institutional uses"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),
                        html.Span(f"(in 2020: {DEFAULTS['manufacturing_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    # Manufacturing
                    html.Div([
                        dbc.Input(
                            id="manufacturing_val",
                            type="number",
                            value=defaults.get("manufacturing_val", (DEFAULTS["manufacturing_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={"width": "100px", "margin": "0 5px 0 0", "textAlign": "right"},
                        ),
                        html.Span(id="manufacturing_change", style={"fontWeight": "normal"})
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),


                    # daq.NumericInput(
                    #     id="manufacturing_val",
                    #     value=DEFAULTS["manufacturing_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),

                    # Packaging
                    html.Label([
                        html.Span("Packaging ", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "Includes for example pallets, wood boxes, crates, hampers, baskets, and other"
                                " wooden containers"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),
                        html.Span(f"(in 2020: {DEFAULTS['packaging_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    # Packaging
                    html.Div([
                        dbc.Input(
                            id="packaging_val",
                            type="number",
                            value=defaults.get("packaging_val", (DEFAULTS["packaging_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={"width": "100px", "margin": "0 5px 0 0", "textAlign": "right"},
                        ),
                        html.Span(id="packaging_change", style={"fontWeight": "normal"})
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

                    # daq.NumericInput(
                    #     id="packaging_val",
                    #     value=DEFAULTS["packaging_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),

                    # Other
                    html.Label([
                        html.Span("Other uses ", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "Includes wood usage by hobbyist woodworkers and DIY projects; advertising and display"
                                " structures, wood shingles; fencing; and other miscellaneous items"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),

                        html.Span(f"(in 2020: {DEFAULTS['other_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    # Other
                    html.Div([
                        dbc.Input(
                            id="other_val",
                            type="number",
                            value=defaults.get("other_val", (DEFAULTS["other_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={"width": "100px", "margin": "0 5px 0 0", "textAlign": "right"},
                        ),
                        html.Span(id="other_change", style={"fontWeight": "normal"})
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

                    # daq.NumericInput(
                    #     id="other_val",
                    #     value=DEFAULTS["other_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),

                    html.Label([
                        html.Span("Nonresidential construction ", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "Includes for example lodging, office, commercial, healthcare, educational, religious, "
                                "public safety, as well as infrastructure related construction"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),
                        html.Span(f"(in 2020: {DEFAULTS['non_res_construction_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    html.Div([
                        dbc.Input(
                            id="non_res_construction_val",
                            type="number",
                            value=defaults.get("non_res_construction_val", (DEFAULTS["non_res_construction_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={"width": "100px", "margin": "0 5px 0 0", "textAlign": "right"},
                        ),
                        html.Span(id="non_res_construction_change", style={"fontWeight": "normal"})
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),




                    # daq.NumericInput(
                    #     id="non_res_construction_val",
                    #     value=DEFAULTS["non_res_construction_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),

                    # Other construction (repair)
                    html.Label([
                        html.Span("Residential repair and remodeling ", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "upkeep and improvements and/or renovation of existing residential housing stock"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),

                        html.Span(f"(in 2020: {DEFAULTS['other_construction_val']:,.0f})",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    # nonres Construction
                    html.Div([
                        dbc.Input(
                            id="other_construction_val",
                            type="number",
                            value=defaults.get("other_construction_val", int(DEFAULTS["other_construction_val"])),
                            min=0,
                            max=600000,
                            step=100,
                            style={"width": "100px", "margin": "0 5px 0 0", "textAlign": "right"},
                        ),
                        html.Span(id="other_construction_change", style={"fontWeight": "normal"})
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

                    html.P(""),
                    html.Hr(style={
                        "border": "none",       # remove default border
                        "borderTop": "2px solid black",  # grey line
                        "margin": "20px 0"      # vertical spacing
                    }),
                    html.P("*Please note: enter values rounded to the nearest hundred."),

                    # daq.NumericInput(
                    #     id="other_construction_val",
                    #     value=DEFAULTS["other_construction_val"],
                    #     min=0,
                    #     max=100,
                    #     size=70,
                    #     style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    # ),



                    #prosentit
                    dcc.Store(id="construction_multistory", data=DEFAULTS["construction_multistory"]),
                    dcc.Store(id="construction_single", data=DEFAULTS["construction_single"]),
                    dcc.Store(id="manufacturing", data=DEFAULTS["manufacturing"]),
                    dcc.Store(id="packaging", data=DEFAULTS["packaging"]),
                    dcc.Store(id="other", data=DEFAULTS["other"]),
                    dcc.Store(id="other_construction", data=DEFAULTS["other_construction"]),
                    dcc.Store(id="non_res_construction", data=DEFAULTS["non_res_construction"]),


                ], style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start",
                    "width": "100%",
                    "minWidth": "0",
                    "border": "1px solid #ddd",
                    "borderRadius": "12px",
                    "padding": "12px",
                    "marginBottom": "20px",
                    "backgroundColor": "#fafafa",
                    "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
                })
            ], className='col-3', style={
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
                "width": "100%",
                "minWidth": "0",
            }),


# Column 4

        html.Div([
            html.Div(id="lumber_supply_status"),


                html.Div([

                html.Div(id="lumber_supply_text2", style={"marginTop": "20px", "marginBottom": "10px"}),
                html.Div(id="lumber_demand_status", style={"marginTop": "20px", "marginBottom": "10px"}),
          #      html.Div(id="lumber_demand_status",
           #              style={"color": "green", "fontSize": "18px", "marginBottom": "10px"}),
             #   html.Div(id="lumber_supply_status_text"),

                    html.P(""),
                    html.Hr(style={
                        "border": "none",       # remove default border
                        "borderTop": "2px solid black",  # grey line
                        "margin": "20px 0"      # vertical spacing
                    }),
                    html.P(
                        "*Please note: Supply and demand must match with an accuracy of 5,000 mcf."),

                ],
                    id="sd_style_box"),

            html.Div([
                html.Button("Set section 3 variables to default", id="reset-btn-2", n_clicks=0,
                            style={
                                "marginTop": "20px",
                                "padding": "12px 26px",
                                "fontWeight": "bold",
                                "fontSize": "16px",
                                "color": "white",
                                "background": "linear-gradient(135deg, #007BFF 0%, #0056D2 100%)",
                                "border": "none",
                                "borderRadius": "8px",
                                "cursor": "pointer",
                                "boxShadow": "0 4px 8px rgba(0,0,0,0.15)",
                                "transition": "all 0.2s ease-in-out",
                            }),
            ], style={
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "marginLeft": "20px",
                "alignItems": "center"}
            ),
        ]),

        ], style={
        "gap": "30px",
        "display": "grid",
        "gridTemplateColumns": "repeat(4, minmax(0, 1fr))",
        "margin": "auto",
        "maxWidth": "1600px",
        "width": "100%",
        "marginTop": "50px",
    }),



    html.Hr(style={
        "border": "none",       # remove default border
        "borderTop": "2px solid #ccc",  # grey line
        "margin": "20px 0"      # vertical spacing
    }),

# likert scale GRI questions
    html.Div([
        # Otsikko koko gridin levyinen
        html.H3("4. Future role and contributions of the forest-based sector in New England",
        style={
            "gridColumn": "1 / -1",  # vie koko rivin
            "marginBottom": "20px",
            "marginTop": "40px",
            "fontWeight": "bold"
        }),

        html.P(""),
        html.H3("In your vision, how important is it that...", style={"gridColumn": "1 / -1", "marginBottom": "20px"}),
     #   html.H5("(1 = not at all important, 2 = slightly important, 3 = moderately important, 4 = imporant, 5 = very important)"),
        # Kysymykset gridissä
        html.Div([
html.Div([
    format_question(q),

    html.Div(
        dcc.Slider(
            id={'type': 'importance-slider', 'index': q["id"]},
            min=1,
            max=9,
            step=1,
            value=defaults.get(q["id"], 3),
            marks={
                1: {
                    "label": "Not at all important",
                    "style": {
                        "whiteSpace": "normal",
                        "textAlign": "center",
                        "maxWidth": "60px",   # << riittävä tila monirivelle
                      #  "marginLeft": "-20px" # << hienosäätö: siirtää labelia vasemmalle jotta osuu numeron päälle
                    }},
                2: "2",
                3: "3",
                4: "4",
                5: "5",
                6: "6",
                7: "7",
                8: "8",
                9: "Very important"
            },
            tooltip={"placement": "top", "always_visible": True},
            updatemode='drag'
        ),
        style={"width": "100%"}
    ),

    # ⭐ Keskitetään BooleanSwitch sliderin alle ⭐
    html.Div(
        daq.BooleanSwitch(
            id={'type': 'cannot-answer', 'index': q["id"]},
            on=bool(defaults.get(f"{q['id']}_cannot_answer", 0)),
            label="Cannot answer",
            labelPosition="right",
        ),
        style={
            "marginTop": "10px",
            "display": "flex",
            "justifyContent": "center",  # <-- Keskittää vaakasuunnassa
            "width": "100%"
        }
    ),

], style={
    "display": "flex",
    "flexDirection": "column",
    "alignItems": "flex-start",
    "marginBottom": "20px",
    "width": "100%"
})

            for q in likert_questions
        ], style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr 1fr",
            "gap": "20px",
            "width": "100%"
        }),



    ], style={
        "display": "grid",
        "gridTemplateColumns": "1fr",
        "gap": "20px",
        "margin": "auto",
        "maxWidth": "1200px",
        "width": "100%",
        "marginTop": "50px"
    }),

            html.Hr(style={
            "border": "none",  # remove default border
            "borderTop": "2px solid #ccc",  # grey line
            "margin": "20px 0"  # vertical spacing
        }),

        html.Div([
            html.Label("Voluntary: Please let us know about your experience with the survey", style={"fontWeight": "bold"}),

        dcc.Textarea(
            id="general_comment",
            value=defaults.get("general_comment", ""),
            placeholder="Enter your comments here...",
            style={"width": "100%", "height": 150},
            ),
        ], style={
        "display": "grid",
        "gridTemplateColumns": "1fr",
        "gap": "20px",
        "margin": "auto",
        "maxWidth": "1200px",
        "width": "100%",
        "marginTop": "50px"
    }),

    html.Hr(style={
        "border": "none",  # remove default border
        "borderTop": "2px solid #ccc",  # grey line
        "margin": "20px 0"  # vertical spacing
    }),

    html.Div([
    # --- Submit-painike ---
    html.Button("Submit your responses and logout", id="submit-btn", n_clicks=0,
                style={
                    "padding": "12px 0",
                    "fontWeight": "bold",
                    "fontSize": "16px",
                    "color": "white",
                    "background": "linear-gradient(135deg, #007BFF 0%, #0056D2 100%)",
                    "border": "none",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "boxShadow": "0 4px 8px rgba(0,0,0,0.15)",
                    "transition": "all 0.2s ease-in-out",
                    "flex": "1",
                    "marginRight": "10px"

                }),

    html.Button("Logout without updating responses", id="logout-btn", n_clicks=0,
                style={
                    "padding": "12px 0",
                    "fontWeight": "bold",
                    "fontSize": "16px",
                    "color": "white",
                    "background": "linear-gradient(135deg, #FF4B4B 0%, #D20000 100%)",
                    "border": "none",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "boxShadow": "0 4px 8px rgba(0,0,0,0.15)",
                    "transition": "all 0.2s ease-in-out",
                    "flex": "1"
                }),

    ], style={
        "display": "flex",
        "flexDirection": "row",
        "alignItems": "center",
        "marginTop": "20px",
        "maxWidth": "800px",
        "marginLeft": "auto",
        "marginRight": "auto"
    }
        ),

    # --- Placeholder for message returned by callback ---
    html.Div(
        html.Div(id="submit-msg", style={"marginTop": "10px", "color": "green", "fontWeight": "bold"})
        , style={
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "marginTop": "20px",
            "maxWidth": "800px",
            "marginLeft": "auto",
            "marginRight": "auto"
        }),
        html.P(""),
        html.P("")

    ], style={"padding": "20px", "fontFamily": "Arial, sans-serif"})


app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    dcc.Store(id="last-active-ts", data=datetime.datetime.now().timestamp()),
    dcc.Interval(id="activity-interval", interval=30 * 1000, n_intervals=0),
    dcc.Store(id="login-state", data={}, storage_type="session"),
    dcc.Store(id="user-email", data="", storage_type="session"),
    html.Div(id="page-content"),  # will be either login_layout or survey_layout
    dcc.Store(id="dummy-output"),


    dcc.ConfirmDialog(
        id="submit-confirm",
        message="✅ Responses submitted successfully! You can now close this survey."
    )
])

# --- Callbacks ---
# Login callback
# --- Login callback ---
@app.callback(
    Output("login-state", "data"),
    Output("user-email", "data"),
    Output("url", "pathname", allow_duplicate=True),  # Ohjataan käyttäjä suoraan survey-sivulle
    Output("login-msg", "children"),
    Input("login-btn", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def login_callback(n_clicks, email, password):
    if not email or not password:
        return False, "", dash.no_update, "Please enter your email and password"
    if check_user(email, password):
        session["logged_in"] = True
        session["email"] = email
        ensure_user_defaults(email)
        increment_login_count(email)
        return True, email, "/survey", ""
    return False, "", dash.no_update, "Invalid email or password"


def ensure_user_defaults(email):
    """
    Lisää käyttäjän rivin kantaan, jos sitä ei ole, ja täyttää DEFAULTS-arvot + nollakentät.
    """
    likert_columns = [
        "regional_economy",
        "local_owners",
        "carbon_substitution",
        "carbon_storage",
        "biodiversity",
        "local_sourcing",
        "employment_conditions",
        "training_development",
        "community_engagement"
    ]

    text_boxes = [
        "state_other",
        "organization_size",
        "organization_type_other",
        "prof_position_other",
        "general_comment",
    ]

    conn = sqlite3.connect(DATA_DB_FILE)
    c = conn.cursor()

    # Tarkistetaan onko käyttäjä jo olemassa
    c.execute("SELECT 1 FROM responses WHERE email = ?", (email,))
    exists = c.fetchone()

    if not exists:
        # Kaikki kantataulun sarakkeet paitsi id ja timestamp
        columns = [
            "email",
            "state_checklist",
            "state_other",
            "organization_size",
            "organization_type",
            "organization_type_other",
            "general_comment",
            "prof_position",
            "prof_position_other",
            "years_experience",
            "protWoodlands",
            "unprotectedForest",
            "wildlands",
            "farmland",
            "developed",
            "waterAndWetlands",
            "lumbershare",
            "papershare",
            "from_lumber_to_pulp",
            "fuelshare",
            "import_lumber",
            "import_paper",
            "construction_multistory_val",
            "construction_single_val",
            "manufacturing_val",
            "packaging_val",
            "other_val",
            "other_construction_val",
            "non_res_construction_val",
            "recovery_timber",
            "logging_intensity",
            "regional_economy",
            "local_owners",
            "carbon_substitution",
            "carbon_storage",
            "biodiversity",
            "local_sourcing",
            "employment_conditions",
            "training_development",
            "community_engagement",
            "regional_economy_cannot_answer",
            "local_owners_cannot_answer",
            "carbon_substitution_cannot_answer",
            "carbon_storage_cannot_answer",
            "biodiversity_cannot_answer",
            "local_sourcing_cannot_answer",
            "employment_conditions_cannot_answer",
            "training_development_cannot_answer",
            "community_engagement_cannot_answer",
            "reset_btn_1",
            "reset_btn_2",
            "submit_count",
            "logout_without_responding",
            "elapsed_time_seconds",
            "logins"
        ]

        # Rakennetaan arvot: käytetään DEFAULTS jos olemassa, muuten 0
        values = []
        for col in columns:
            if col == "email":
                values.append(email)
            elif col in likert_columns:
                values.append(3)  # Likert default
            elif col.endswith("_cannot_answer"):
                values.append(0)  # cannot answer default
            elif col in text_boxes:
                values.append("")
            elif col == "years_experience":
                values.append(None)
            else:
                values.append(DEFAULTS.get(col, 0))  # muut DEFAULTS-arvot tai 0

        placeholders = ", ".join(["?"] * len(columns))
        c.execute(f"""
            INSERT INTO responses ({', '.join(columns)})
            VALUES ({placeholders})
        """, values)
        conn.commit()

    conn.close()
# Page switching
# --- Display correct page based on URL ---
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    State("user-email", "data"),
    State("login-state", "data"),
    prevent_initial_call=True
)
def display_page(pathname, email, logged_in):
    if pathname == "/survey":
        if logged_in:
            db_data = fetch_user_data(email)
            print(db_data)
            # 1️⃣ Lasketaan derived values
            data_with_calcs = calculate_derived_values(db_data)

            # 2️⃣ Form defaults (Likertit, muut inputit)
            form_defaults = populate_form_from_db(data_with_calcs, likert_questions)
            print(form_defaults)
            # 3️⃣ Chartit heti laskettujen arvojen perusteella
            sankey_fig = make_sankey(data_with_calcs)
            bar_fig = make_stacked_bar(data_with_calcs)

            return survey_layout(form_defaults, data_with_calcs, sankey_fig=sankey_fig, bar_fig=bar_fig)
        else:
            return login_layout
    elif pathname == "/thankyou":
        return thankyou_layout
    else:
        return login_layout


def calculate_derived_values(data):
    """
    Laskee kaikki derived values user-datasta.
    Palauttaa uuden dictin, jossa myös laskelmat mukana.
    """
    data = data.copy()  # välttää muuttamasta alkuperäistä
    data["total_logging"] = data.get("logging_intensity",0) * ((data.get("protWoodlands",0) + data.get("unprotectedForest",0))/100 * 40000)
    data["lumber"] = data["total_logging"] * (data.get("lumbershare",0)/100)
    data["from_lumber_to_pulp"] = 0.333 * data["lumber"]
    data["paper"] = data["total_logging"] * (data.get("papershare",0)/100)
    data["fuelwood"] = data["total_logging"] * (data.get("fuelshare",0)/100)
    # muut laskelmat tarvittaessa
    return data

@app.callback(
    Output("login-state", "data", allow_duplicate=True),
    Output("url", "pathname"),
    Input("logout-btn", "n_clicks"),
    State("user-email", "data"),
    prevent_initial_call=True
)
def logout(n_clicks, email):
    if n_clicks:
        conn = sqlite3.connect(DATA_DB_FILE)
        c = conn.cursor()

        c.execute("""
            UPDATE responses
            SET logout_without_responding = COALESCE(logout_without_responding, 0) + 1
            WHERE email = ?
        """, (email,))

        conn.commit()
        conn.close()

        session.clear()
        return False, "/"
    return dash.no_update, dash.no_update



@app.callback(
        Output("protWoodlands", "value"),
        Output("unprotectedForest", "value"),
        Output("developed", "value"),
        Output("farmland", "value"),
        Output("wildlands", "value"),
        Input("reset-btn-1", "n_clicks")
)

def reset_defaults(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if n_clicks:
        # Kaikki muut paitsi excluded
        values = []
        # Lisätään data-kenttien arvot oikeassa järjestyksessä
        values += [
            DEFAULTS["protWoodlands"],
            DEFAULTS["unprotectedForest"],
            DEFAULTS["developed"],
            DEFAULTS["farmland"],
            DEFAULTS["wildlands"]
        ]

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    user_email = session.get("email")

    # 🔥 Päivitä oikea laskuri kantaan
    if user_email:
        if triggered_id == "reset-btn-1":
            increment_reset_counter(user_email, "reset_btn_1")


    return values


def increment_reset_counter(email, column):
    conn = sqlite3.connect(DATA_DB_FILE)
    c = conn.cursor()
    print("+ increment")
    print(column)
    c.execute(f"""
        UPDATE responses
        SET {column} = COALESCE({column}, 0) + 1
        WHERE email = ?
    """, (email,))

    conn.commit()
    conn.close()


def increment_login_count(user_email):
    conn = sqlite3.connect(DATA_DB_FILE)
    c = conn.cursor()

    c.execute("""
        UPDATE responses
        SET logins = COALESCE(logins, 0) + 1
        WHERE email = ?
    """, (user_email,))

    conn.commit()
    conn.close()

@app.callback(
    [
        Output("construction_multistory_val", "value"),
        Output("construction_single_val", "value"),
        Output("manufacturing_val", "value"),
        Output("packaging_val", "value"),
        Output("other_val", "value"),
        Output("other_construction_val", "value"),
        Output("non_res_construction_val", "value"),
        Output("lumbershare", "value"),
        Output("papershare", "value"),
        Output("fuelshare", "value"),
        Output("logging_intensity", "value"),
        Output("import_lumber", "value"),
        Output("import_paper", "value"),
        Output("recovery_timber", "value"),
    ],
    [Input("reset-btn-2", "n_clicks")],
    prevent_initial_call=True
)
def reset_input_fields(n_clicks2):
    if not n_clicks2:
        raise dash.exceptions.PreventUpdate

    # --- Kerätään palautusarvot listaan (kuten reset_defaults) ---
    values = []
    values += [
        int(DEFAULTS["construction_multistory_val"]),
        int(DEFAULTS["construction_single_val"]),
        int(DEFAULTS["manufacturing_val"]),
        int(DEFAULTS["packaging_val"]),
        int(DEFAULTS["other_val"]),
        int(DEFAULTS["other_construction_val"]),
        int(DEFAULTS["non_res_construction_val"]),
        int(DEFAULTS["lumbershare"]),
        int(DEFAULTS["papershare"]),
        int(DEFAULTS["fuelshare"]),
        int(DEFAULTS["logging_intensity"]),
        int(DEFAULTS["import_lumber"]),
        int(DEFAULTS["import_paper"]),
        int(DEFAULTS["recovery_timber"]),
    ]

    # --- callback context tarkistus ---
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    user_email = session.get("email")

    # 🔥 Päivitä oikea laskuri kantaan
    if user_email and triggered_id == "reset-btn-2":
        increment_reset_counter(user_email, "reset_btn_2")

    return values

def format_demand_change(current_val, default_val):
    """
    Laskee prosenttimuutoksen ja palauttaa tekstin nuolen kanssa.
    ▲ = kasvu, ▼ = lasku, ■ = ei merkittävää muutosta
    """
    pct_change = ((current_val - int(default_val)) / int(default_val)) * 100
    if pct_change > 0.1:
        arrow = "▲"
    elif pct_change < 0:
        arrow = "▼"
    else:
        arrow = "■"
    return f"Demand change in % from 2020: {arrow} {pct_change:+.1f}%", pct_change


'''
"woodlands_area", "wildlands_area", "from_lumber_to_pulp", "lumber", "paper", "fuelwood",
"construction_multistory_val", "construction_single_val",
"manufacturing_val", "packaging_val", "other_val",
"other_construction_val"


    values += [
        DEFAULTS["woodlands_area"],
        DEFAULTS["wildlands_area"],
        DEFAULTS["lumber"],
        DEFAULTS["paper"],
        DEFAULTS["fuelwood"],
        DEFAULTS["construction_multistory_val"],
        DEFAULTS["construction_single_val"],
        DEFAULTS["manufacturing_val"],
        DEFAULTS["packaging_val"],
        DEFAULTS["other_val"],
        DEFAULTS["other_construction_val"],
    ]
'''

'''
@app.callback(
    Output("wildlands", "value", allow_duplicate=True),
    Input("woodlands", "value"),
    prevent_initial_call=True
)


def update_wildlands(woodlands):
    if woodlands is None:
        raise dash.exceptions.PreventUpdate
    new_wildlands = max(0, TOTAL_FOREST - woodlands)
    return round(new_wildlands, 2)

'''

INPUT_ORDER = [
    "logging_intensity",
    "protWoodlands",
    "unprotectedForest",
    "wildlands",
    "farmland",
    "developed",
    "lumbershare",
    "papershare",
    "fuelshare",
    "import_lumber",
    "import_paper",
  #  "construction_multistory",
  #  "construction_single",
  #  "manufacturing",
  #  "packaging",
  #  "other",
  #  "other_construction",
  #  "non_res_construction",
    "recovery_timber",
    "woodlands_area",
    "wildlands_area",
    "lumber",
    "paper",
    "fuelwood",
    "from_lumber_to_pulp",
    "construction_multistory_val",
    "construction_single_val",
    "manufacturing_val",
    "packaging_val",
    "other_val",
    "non_res_construction_val",
    "other_construction_val",

]

@app.callback(
    [
        Output("model-data", "data"),
        Output("sankey", "figure"),
        Output("capacity-status", "children"),
        Output("capacity-status", "style"),
        Output("share_style_box", "style"),
        Output("sd_style_box", "style"),
        Output("lumber_demand_status", "children"),
        Output("lumber_supply_status", "children"),
        Output("lumber_supply_status", "style"),
        Output("lumber_supply_text", "children"),
        Output("lumber_supply_text2", "children"),
        Output("pulp_supply_text", "children"),
        Output("fuel_supply_text", "children"),
        Output("total_logging", "children"),
        Output("timber_supply", "children"),
        Output("construction_multistory_val", "max"),
        Output("construction_single_val", "max"),
        Output("manufacturing_val", "max"),
        Output("packaging_val", "max"),
        Output("other_val", "max"),
        Output("other_construction_val", "max"),
        Output("non_res_construction_val", "max"),
        Output("construction_multistory_change", "children"),
        Output("construction_single_change", "children"),
        Output("manufacturing_change", "children"),
        Output("packaging_change", "children"),
        Output("other_change", "children"),
        Output("non_res_construction_change", "children"),
        Output("other_construction_change", "children")

        #     Output("construction_multistory", "children")
    ],
    [
        Input("logging_intensity", "value"),
        Input("protWoodlands", "value"),
        Input("unprotectedForest", "value"),
        Input("wildlands", "value"),
        Input("farmland", "value"),
        Input("developed", "value"),
        Input("lumbershare", "value"),
        Input("papershare", "value"),
        Input("fuelshare", "value"),
        Input("import_lumber", "value"),
        Input("import_paper", "value"),
        Input("recovery_timber", "value"),
    #    Input("construction_multistory", "value"),
   #     Input("construction_single", "value"),
   #     Input("manufacturing", "value"),
   #     Input("packaging", "value"),
   #     Input("other", "value"),
   #     Input("other_construction", "value"),
   #     Input("non_res_construction", "value"),
        State("woodlands_area", "data"),
        State("wildlands_area","data"),
        State("lumber", "data"),
        State("paper", "data"),
        State("fuelwood", "data"),
        State("from_lumber_to_pulp", "data"),
        Input("construction_multistory_val", "value"),
        Input("construction_single_val", "value"),
        Input("manufacturing_val", "value"),
        Input("packaging_val", "value"),
        Input("other_val", "value"),
        Input("non_res_construction_val", "value"),
        Input("other_construction_val", "value"),
        Input("reset-btn-1", "n_clicks"),
        Input("reset-btn-2", "n_clicks")
    ],
)
def update_all_charts(*vals):
    ctx = dash.callback_context

    # Detect if reset was pressed
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]


    vals_int = [float(v) if v is not None else 0 for v in vals]

    data = dict(zip(INPUT_ORDER, vals_int))

    keys_btn1 = ["protWoodlands", "unprotectedForest", "developed", "farmland", "wildlands"]
    keys_btn2 = [
        "logging_intensity",
        "lumbershare",
        "papershare",
        "fuelshare",
        "import_lumber",
        "import_paper",
        "recovery_timber",
        "construction_multistory_val",
        "construction_single_val",
        "manufacturing_val",
        "packaging_val",
        "other_val",
        "other_construction_val",
        "non_res_construction_val"
    ]

    total_shares = data["lumbershare"] + data["papershare"] + data["fuelshare"]

    total_enduse = round(
        data["construction_multistory_val"] +
        data["construction_single_val"] +
        data["manufacturing_val"] +
        data["packaging_val"] +
        data["other_val"] +
        data["other_construction_val"] +
        data["non_res_construction_val"]
    , -2)

    total_logging = data["logging_intensity"] * (((data["unprotectedForest"] + data["protWoodlands"]))/100 * 40000)

    from_lumber_to_pulp = 0.333 * data["lumber"]

    lumber_supply = round((data["lumbershare"] / 100 * total_logging) + data["import_lumber"] - data["from_lumber_to_pulp"] + data["recovery_timber"], -2)

    # --- Alustetaan figuurit ---
    bar_fig = dash.no_update
    sankey_fig = dash.no_update  # aluksi None, luodaan vain validien osien perusteella

    share_style_box = {
        "flex": "1",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",  # <--- FIX
        "width": "100%",
        "minWidth": "0",
        "border": "1px solid #ddd",
        "borderRadius": "12px",
        "padding": "12px",
        "marginBottom": "20px",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
     #   "borderBottom": "3px double black",
        "backgroundColor": "#d4f4dd"  # light red
    }

    sd_style_box_r = {
        "flex": "1",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",  # <--- FIX
        "width": "100%",
        "minWidth": "0",
        "border": "4px solid #000",
        "borderRadius": "12px",
        "padding": "12px",
        "marginBottom": "20px",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
       # "borderBottom": "3px double black",
        "backgroundColor": "#f4d4d4"
    }

    sd_style_box_g = {
        "flex": "1",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",  # <--- FIX
        "width": "100%",
        "minWidth": "0",
        "border": "4px solid #000",
        "borderRadius": "12px",
        "padding": "12px",
        "marginBottom": "20px",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
     #   "borderBottom": "3px double black",
        "backgroundColor": "#d4f4dd"
    }

    # --- 1️⃣ Capacity (lumber/paper/fuel) ---
    if abs(total_shares - 100) > 0.01:
        total_logging = data["logging_intensity"] * (((data["unprotectedForest"] + data["protWoodlands"]))/100 * 40000)
        timber_supply = total_logging + data["import_lumber"] + data["import_paper"]
        data["lumber"] = total_logging * (data["lumbershare"] / 100)

        from_lumber_to_pulp = 0.333 * data["lumber"]
        data["from_lumber_to_pulp"] = 0.333 * data["lumber"]
        lumber_supply = round((data["lumbershare"] / 100 * total_logging) + data["import_lumber"] - data["from_lumber_to_pulp"] + data["recovery_timber"], -2)
        status_text = f"{total_shares:.0f}% ❌ shares must equal 100%"
        status_style = {"color": "red"}

        share_style_box = {
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",  # <--- FIX
            "width": "100%",
            "minWidth": "0",
            "border": "1px solid #ddd",
            "borderRadius": "12px",
            "padding": "12px",
            "marginBottom": "20px",
            "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
         #   "borderBottom": "3px double black",
            "backgroundColor": "#f4d4d4"  # light red
        }


      #  pulp_supply = (
      #      (vals[INPUT_ORDER.index("paper")] or 0)
      #                 + (vals[INPUT_ORDER.index("import_paper")] or 0)
      #                 + (vals[INPUT_ORDER.index("from_lumber_to_pulp")] or 0)
      #  )

    #    fuel_supply = vals[INPUT_ORDER.index("fuelwood")] or 0

      #  data["lumber"] = vals[INPUT_ORDER.index("lumber")] or 0
       # data["paper"] = vals[INPUT_ORDER.index("paper")] or 0
       # data["fuelwood"] = vals[INPUT_ORDER.index("fuelwood")] or 0
        total_logging = dash.no_update
        total_logging_text = dash.no_update
        timber_supply = dash.no_update
        timber_supply_text = dash.no_update
       # lumber_supply = dash.no_update
        lumber_supply_text = dash.no_update
        pulp_supply = dash.no_update
        pulp_supply_text = dash.no_update
        fuel_supply = dash.no_update
        fuel_supply_text = dash.no_update
       # lumber_supply_text2 = dash.no_update
    else:
        total_logging = data["logging_intensity"] * (((data["unprotectedForest"] + data["protWoodlands"]))/100 * 40000)
        total_logging_text = f"Total timber harvesting: {total_logging:,.0f} mcf"
        timber_supply = total_logging + data["import_lumber"] + data["import_paper"]
        timber_supply_text = f"Total roundwood market size: {timber_supply:,.0f} mcf"
        data["lumber"] = total_logging * (data["lumbershare"] / 100)

        from_lumber_to_pulp = 0.333 * data["lumber"]
        data["from_lumber_to_pulp"] = 0.333 * data["lumber"]
        lumber_supply = round((data["lumbershare"] / 100 * total_logging) + data["import_lumber"] - data["from_lumber_to_pulp"] + data["recovery_timber"], -2)
        pulp_supply = round((data["papershare"] / 100 * total_logging) + data["import_paper"] + data["from_lumber_to_pulp"], -3)
        fuel_supply = round((data["fuelshare"] / 100 * total_logging), -3)

        data["paper"] = total_logging * (data["papershare"] / 100)
        data["fuelwood"] = total_logging * (data["fuelshare"] / 100)

        #bar_fig = make_stacked_bar(data)
        status_text = f"{total_shares:.0f}% ✅ Balanced"
        status_style = {"color": "green"}

        lumber_supply_text = html.Span([
            html.B("Lumber supply: "),
            f"(after deduction of residues for pulp production): {round(lumber_supply, -2):,.0f} mcf"
        ])
       # lumber_demand_text = f"Demand {round(total_enduse, -2):,.0f}"
        pulp_supply_text = html.Span([
            html.B("Pulpwood supply: "),
            f"{round(pulp_supply, -3):,.0f} mcf"
        ])

        fuel_supply_text = html.Span([
            html.B("Fuelwood supply: "),
            f"{round(fuel_supply, -3):,.0f} mcf"
        ])



    # --- 2 End-use (loppukäyttö) ---
    if abs(total_enduse - lumber_supply) > 5000:
        lumber_supply_status_text = dash.no_update
        lumber_supply_status_style = dash.no_update


    else:

        data["construction_multistory_val"] = int(data["construction_multistory_val"])
        data["construction_single_val"] = int(data["construction_single_val"])
        data["manufacturing_val"] = int(data["manufacturing_val"])
        data["packaging_val"] = int(data["packaging_val"])
        data["other_val"] = int(data["other_val"])
        data["other_construction_val"] = int(data["other_construction_val"])
        data["non_res_construction_val"] = int(data["non_res_construction_val"])
      #  lumber_demand_text = f"Demand {round(total_enduse, -2):,.0f}"
     #   lumber_demand_style = {"color": "red"}

        lumber_supply_status_text = ("✅ Lumber supply and demand are in balance")
        lumber_supply_status_style = {"color": "green"}

     # --- Sankey-päivitys vain, jos molemmat balanssissa ---
    if abs((total_shares - 100)) <= 0.01 and abs((total_enduse - lumber_supply)) > 5000:
        sankey_fig = make_sankey(data)
    else:
        sankey_fig = make_sankey(data)




    # 1. Construction multistory
    construction_multistory_str, inc_construction_multistory_pct = format_demand_change(
        data["construction_multistory_val"], DEFAULTS["construction_multistory_val"]
    )

    # 2. Construction single
    construction_single_str, inc_construction_single_pct = format_demand_change(
        data["construction_single_val"], DEFAULTS["construction_single_val"]
    )

    # 3. Manufacturing
    manufacturing_str, inc_manufacturing_pct = format_demand_change(
        data["manufacturing_val"], DEFAULTS["manufacturing_val"]
    )

    # 4. Packaging
    packaging_str, inc_packaging_pct = format_demand_change(
        data["packaging_val"], DEFAULTS["packaging_val"]
    )

    # 5. Other
    other_str, inc_other_pct = format_demand_change(
        data["other_val"], DEFAULTS["other_val"]
    )

    # 6. Non res. Construction
    non_res_construction_str, inc_non_res_construction_pct = format_demand_change(
        data["non_res_construction_val"], DEFAULTS["non_res_construction_val"]
    )

    # 7. Other Construction
    other_construction_str, inc_other_construction_pct = format_demand_change(
        data["other_construction_val"], DEFAULTS["other_construction_val"]
    )

    diff = total_enduse - lumber_supply
    balanced_thousand = abs(diff) <= 5000

    # --- Päivitä numerot aina ---
    if balanced_thousand:
        lumber_demand_text = html.Span([
            html.B("Lumber demand: "),
            f"{round(total_enduse, -2):,.0f} mcf balanced"
        ])
        lumber_supply_text2 = html.Span([
            html.B("Lumber supply: "),
            f"{round(lumber_supply, -2):,.0f} mcf balanced"
        ])

    else:
        if diff > 5000:
            # demand higher, supply lower
            lumber_demand_text = html.Span([
                html.B("Lumber demand: "),
                f"{round(total_enduse, -2):,.0f} mcf 🟢 higher"
            ])
            lumber_supply_text2 = html.Span([
                html.B("Lumber supply: "),
                f"{round(lumber_supply, -2):,.0f} mcf 🔴 lower"
            ])

        else:
            # demand lower, supply higher
            lumber_demand_text = html.Span([
                html.B("Lumber demand: "),
                f"{round(total_enduse, -2):,.0f} mcf 🔴 lower"
            ])
            lumber_supply_text2 = html.Span([
                html.B("Lumber supply: "),
                f"{round(lumber_supply, -2):,.0f} mcf 🟢 higher"
            ])

    # --- Päivitä sd_style_box ja status aina diffin mukaan ---
    if balanced_thousand:
        sd_style_box = sd_style_box_g
        lumber_supply_status_text = html.H4("✅ Lumber supply and demand balanced", style = {"color": "green"})
    else:
        sd_style_box = sd_style_box_r
        lumber_supply_status_text = html.H4("❌ Lumber supply and demand not in balance", style= {"color": "red"})

    if triggered_id == "reset-btn-1":
        reset_btn_1 =+ 1
        for key in keys_btn1:
            data[key] = DEFAULTS[key]
        data["construction_multistory_val"] = (DEFAULTS["construction_multistory_val"])
        # Recalculate dependent values
        total_logging = data["logging_intensity"] * ((data["unprotectedForest"] + data["protWoodlands"]) / 100 * 40000)
        print(total_logging)
        data["lumber"] = total_logging * (data["lumbershare"] / 100)
        data["from_lumber_to_pulp"] = 0.333 * data["lumber"]
        data["paper"] = total_logging * (data["papershare"] / 100)
        data["fuelwood"] = total_logging * (data["fuelshare"] / 100)
        sankey_fig = make_sankey(data)

    elif triggered_id == "reset-btn-2":
        reset_btn_2 =+ 1
        for key in keys_btn2:
            data[key] = DEFAULTS[key]
        # Recalculate dependent values if needed
        total_logging = data["logging_intensity"] * ((data["unprotectedForest"] + data["protWoodlands"]) / 100 * 40000)
        data["lumber"] = total_logging * (data["lumbershare"] / 100)
        data["from_lumber_to_pulp"] = 0.333 * data["lumber"]
        data["paper"] = total_logging * (data["papershare"] / 100)
        data["fuelwood"] = total_logging * (data["fuelshare"] / 100)
        sankey_fig = make_sankey(data)

    return (
        data,
        sankey_fig,
        status_text,
        status_style,
        share_style_box,
        sd_style_box,
        lumber_demand_text,
        lumber_supply_status_text,
        lumber_supply_status_style,
        lumber_supply_text,
        lumber_supply_text2,
        pulp_supply_text,
        fuel_supply_text,
        total_logging_text,
        timber_supply_text,
        lumber_supply,
        lumber_supply,
        lumber_supply,
        lumber_supply,
        lumber_supply,
        lumber_supply,
        lumber_supply,
        html.Span(construction_multistory_str),
        html.Span(construction_single_str),
        html.Span(manufacturing_str),
        html.Span(packaging_str),
        html.Span(other_str),
        html.Span(non_res_construction_str),
        html.Span(other_construction_str),

    )


'''
@app.callback(
    Output("woodlands", "value", allow_duplicate=True),
    Input("wildlands", "value"),
    prevent_initial_call=True
)
def update_woodlands(wildlands):
    if wildlands is None:
        raise dash.exceptions.PreventUpdate
    new_woodlands = max(0, TOTAL_FOREST - wildlands)
    return round(new_woodlands, 2)
'''

# States for callback
states = [State(k, "value") for k in DEFAULTS.keys()
          if k not in ["woodlands_area", "wildlands_area", "from_lumber_to_pulp", "lumber", "paper", "fuelwood","construction_multistory",
                         "construction_single", "manufacturing", "packaging", "other",
                         "other_construction", "non_res_construction"]]

# Add lumber, paper, fuelwood as separate States
states += [
    State("woodlands_area", "data"),
    State("wildlands_area", "data"),
    State("lumber", "data"),
    State("paper", "data"),
    State("fuelwood", "data"),
    State("from_lumber_to_pulp", "data"),
    State("construction_multistory", "data"),
    State("construction_single", "data"),
    State("manufacturing", "data"),
    State("packaging", "data"),
    State("other", "data"),
    State("other_construction", "data"),
    State("non_res_construction", "data")
]





@app.callback(
    [
        Output("forest-bar", "figure", allow_duplicate=True),
        Output("share-warning-land", "children"),
        Output("share-warning-land", "style")
    ],
    [
        Input("wildlands", "value"),
        Input("protWoodlands", "value"),
        Input("unprotectedForest", "value"),
        Input("farmland", "value"),
        Input("developed", "value"),
        Input("waterAndWetlands", "value")
    ],
    prevent_initial_call=True,

)
# --- Funktio Dash callbackiin ---
def update_forest_chart(wild, prot, unprot, farm, dev, water):
    """
    Tarkistaa, että syötettyjen osien summa + water_wetlands on 100 %.
    Palauttaa kaavion ja viestin.
    """
    values_list = [wild or 0, prot or 0, unprot or 0, farm or 0, dev or 0, water]
    total = sum(values_list)
    if round(total, 1) != 100:
        warning = f"⚠️ The shares must sum to 100% (now {total:.1f}%,)."
        return dash.no_update, warning, {"color": "red", "fontWeight": "bold", "marginBottom": "10px"}
    else:
        values = {
            "wildlands": wild,
            "protWoodlands": prot,
            "unprotectedForest": unprot,
            "farmland": farm,
            "developed": dev,
            "waterAndWetlands": water
        }
        warning = f"✅ Shares sum to 100%",

        fig = make_stacked_bar(values)
        return fig, warning, {"color": "green", "fontWeight": "bold", "marginBottom": "10px"}


# Callback to disable slider if "Cannot answer" is on
@app.callback(
    Output({'type': 'importance-slider', 'index': dash.ALL}, 'disabled'),
    Input({'type': 'cannot-answer', 'index': dash.ALL}, 'on')
)
def disable_slider(cannot_answer_values):
    return cannot_answer_values



'''
@app.callback(
        Output("import_lumber", "value", allow_duplicate=True),
    [
        Input("lumber", "value"),
        Input("recovery_timber", "value"),
        Input("construction_multistory", "value"),
        Input("construction_single", "value"),
        Input("manufacturing", "value"),
        Input("packaging", "value"),
        Input("other", "value"),
        Input("other_construction", "value"),
        Input("import_lumber", "value")
    ], prevent_initial_call=True
)


def enforce_lumber_import(lumber, recovery_timber, construction_multistory, construction_single, manufacturing, packaging, other,
                           other_construction, import_lumber):

    if None in (lumber, import_lumber, recovery_timber):
        raise dash.exceptions.PreventUpdate

    consumption = (construction_multistory + construction_single + manufacturing + packaging + other
                               + other_construction)
    print(consumption)
    import_lumber = consumption - recovery_timber - lumber

    return import_lumber
'''

def save_responses_to_db(user_inputs, likert_answers, cannot_flags_dict):
    conn = sqlite3.connect(DATA_DB_FILE)
    c = conn.cursor()

    # Convert lists or dicts to JSON strings
    for key, value in list(user_inputs.items()):
        if isinstance(value, (list, dict)):
            user_inputs[key] = json.dumps(value)

    full_data = {}

    full_data.update(user_inputs)
    full_data.update(likert_answers)
    full_data.update({f"{k}_cannot_answer": v for k, v in cannot_flags_dict.items()})

    email = full_data.get("email")
    if not email:
        raise ValueError("Missing email")


    cols = list(full_data.keys())
    placeholders = ", ".join(["?"] * len(cols))
    values = [full_data[cname] for cname in cols]

    protected = {"reset_btn_1", "reset_btn_2", "id"}
    update_cols = [cname for cname in cols if cname not in protected and cname != "email"]

    update_clause = ", ".join([f"{col}=excluded.{col}" for col in update_cols])
    update_clause += ", submit_count = COALESCE(responses.submit_count, 0) + 1"

    sql = f"""
        INSERT INTO responses ({', '.join(cols)})
        VALUES ({placeholders})
        ON CONFLICT(email) DO UPDATE SET
        {update_clause}
    """

    c.execute(sql, values)
    conn.commit()
    conn.close()



@app.callback(
    Output("submit-msg", "children", allow_duplicate=True),
    Output("login-state", "data", allow_duplicate=True),
    Output("url", "pathname", allow_duplicate=True),
    Input("submit-btn", "n_clicks"),
    [
    State("user-email", "data"),
    State("lumber", "data"),
    State("lumbershare", "value"),
     State("papershare", "value"),
     State("fuelshare", "value"),
     State("import_lumber", "value"),
     State("import_paper", "value"),
     State("construction_multistory_val", "value"),
     State("construction_single_val", "value"),
     State("manufacturing_val", "value"),
     State("packaging_val", "value"),
     State("other_val", "value"),
     State("other_construction_val", "value"),
     State("non_res_construction_val", "value"),
     State("recovery_timber", "value"),
     State("logging_intensity", "value"),
    State("state-checklist", "value"),
    State("state_other", "value"),
    State("organization_size", "value"),
    State("organization_type", "value"),
    State("organization_type_other", "value"),
    State("general_comment", "value"),
    State("prof_position", "value"),
    State("prof_position_other", "value"),
    State("years_experience", "value"),
     State("protWoodlands", "value"),
     State("unprotectedForest", "value"),
     State("wildlands", "value"),
     State("farmland", "value"),
     State("developed", "value"),
     State("waterAndWetlands", "value"),
     State("from_lumber_to_pulp", "data"),

    ] +
    [State({'type': 'importance-slider', 'index': q["id"]}, 'value') for q in likert_questions] +
    [State({'type': 'cannot-answer', 'index': q["id"]}, 'on') for q in likert_questions],
    prevent_initial_call=True,

)
def submit_responses_callback(
    n_clicks,
    user_email,
    lumber,
    lumbershare,
    papershare,
    fuelshare,
    import_lumber,
    import_paper,
    construction_multistory_val,
    construction_single_val,
    manufacturing_val,
    packaging_val,
    other_val,
    other_construction_val,
    non_res_construction_val,
    recovery_timber,
    logging_intensity,
    state_checklist,
    state_other,
    organization_size,
    organization_type,
    organization_type_other,
    general_comment,
    prof_position,
    prof_position_other,
    years_experience,
    protwoodlands,
    unprotectedforest,
    wildland,
    farmland,
    developed,
    waterandwetlands,
    from_lumber_to_pulp,



    *args
):
    if n_clicks is None or n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # Erotellaan Likert-sliderit ja cannot-answer -flagit
    num_sliders = len(likert_questions)
    slider_values = args[:num_sliders]
    cannot_flags = args[num_sliders:]

    # Käyttäjän antamat inputit (vihreä on kannan sarake)
    user_inputs = {
        "email": user_email,
        "lumbershare": lumbershare,
        "papershare": papershare,
        "fuelshare": fuelshare,
        "import_lumber": import_lumber,
        "import_paper": import_paper,
        "construction_multistory_val": construction_multistory_val,
        "construction_single_val": construction_single_val,
        "manufacturing_val": manufacturing_val,
        "packaging_val": packaging_val,
        "other_val": other_val,
        "other_construction_val": other_construction_val,
        "non_res_construction_val": non_res_construction_val,
        "recovery_timber": recovery_timber,
        "logging_intensity": logging_intensity,
        "state_checklist": state_checklist,
        "state_other": state_other,
        "organization_size": organization_size,
        "organization_type": organization_type,
        "organization_type_other": organization_type_other,
        "prof_position": prof_position,
        "prof_position_other": prof_position_other,
        "years_experience": years_experience,
        "protWoodlands": protwoodlands,
        "unprotectedForest": unprotectedforest,
        "wildlands": wildland,
        "farmland": farmland,
        "developed": developed,
        "waterAndWetlands": waterandwetlands,
        "from_lumber_to_pulp": from_lumber_to_pulp,
        "general_comment": general_comment,
    }

    # Likert-slider arvot
    likert_answers = {q["id"]: val for q, val in zip(likert_questions, slider_values)}

    # Likert “cannot answer” flagit (0/1)
    cannot_flags_dict = {q["id"]: int(flag) for q, flag in zip(likert_questions, cannot_flags)}


    # 1. Check land cover sum == 100
    landcover_sum = (
            (protwoodlands or 0)
            + (unprotectedforest or 0)
            + (wildland or 0)
            + (farmland or 0)
            + (developed or 0)
            + (waterandwetlands or 0)
    )

    total_enduse = construction_multistory_val + construction_single_val + manufacturing_val + packaging_val + other_val + other_construction_val +non_res_construction_val
    total_lumber_logging = (logging_intensity * (protwoodlands + unprotectedforest) / 100 * 40000) * (lumbershare/100)
    from_lumber_to_pulp = total_lumber_logging * 0.333
    print(total_lumber_logging)
    lumber_supply = round(total_lumber_logging + import_lumber + recovery_timber - from_lumber_to_pulp, -2)


    diff = (lumber_supply or 0) - (total_enduse or 0)

    # 2. Check fuel + pulp + lumber share == 100


    failed_landcover = False
    failed_share = False
    failed_supply = False

    # 1. Check landcover sum
    if landcover_sum != 100:
        failed_landcover = True

    # 2. Check fuel + pulp + lumber share
    share_sum = (fuelshare or 0) + (papershare or 0) + (lumbershare or 0)
    if share_sum != 100:
        failed_share = True

    # 3. Check supply vs demand
    if abs(diff) > 5000:
        failed_supply = True

    # Log to DB for each failed check
    conn = sqlite3.connect(DATA_DB_FILE)
    cur = conn.cursor()
    if failed_landcover:
        cur.execute("""
            UPDATE responses
            SET failed_attempts_landcover = failed_attempts_landcover + 1
            WHERE email = ?
        """, (user_email,))
    if failed_share:
        cur.execute("""
            UPDATE responses
            SET failed_attempts_share = failed_attempts_share + 1
            WHERE email = ?
        """, (user_email,))
    if failed_supply:
        cur.execute("""
            UPDATE responses
            SET failed_attempts_supply = failed_attempts_supply + 1
            WHERE email = ?
        """, (user_email,))
    conn.commit()
    conn.close()


    if landcover_sum != 100:
        return (html.Div("❌ Land cover values must sum to 100%",
                        style={"color": "red", "fontWeight": "bold", "marginTop": "10px"}),
                         False,
                         dash.no_update
                         )


    if share_sum != 100:
        return (html.Div("❌ Fuelwood, pulpwood and sawnwood shares must sum to 100%",
                        style={"color": "red", "fontWeight": "bold", "marginTop": "10px"}),
                        False,
                        dash.no_update
                        )

    # 3. Check supply = demand
    if abs(diff) > 5000:
        return (html.Div(f"❌ Supply ({lumber_supply:,.0f}) and demand ({total_enduse:,.0f}) differ by more than 5,000 mcf. Fix the inputs.",
        style={"color": "red", "fontWeight": "bold", "marginTop": "10px"}),
               False,
               dash.no_update)



    # --- Validation passed → Save ---
    if n_clicks is None or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    print(user_inputs)
    # Validation checks...
    save_responses_to_db(user_inputs, likert_answers, cannot_flags_dict)
    session.clear()
    return "", False, "/thankyou"


def check_email(email, db_path=DATA_DB_FILE):
    """Hakee käyttäjän tiedot SQLite-kannasta sähköpostin perusteella."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM responses WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()


    if row:
        # Jos email löytyy, haetaan kaikki tiedot
        return fetch_user_data(email, db_path)
    else:
        # Jos ei löydy, palautetaan app_layout (tai mikä tahansa oletus)
        return survey_layout


def fetch_user_data(email, db_path=DATA_DB_FILE):
    """Hakee käyttäjän tiedot SQLite-kannasta sähköpostin perusteella ja dekoodaa JSON-kentät."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM responses WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    # JSON-dekoodaus automaattisesti
    for key, value in data.items():
        if isinstance(value, str):
            try:
                data[key] = json.loads(value)
            except:
                pass

    return data

def populate_form_from_db(db_data, likert_questions):
    """
    Luo yhden dictin, jossa kaikki oletusarvot survey-kentille.
    db_data = fetch_user_data(email) tulos (dict tai None)
    """
    if not db_data:
        db_data = {}

    defaults = {
        "lumbershare": db_data.get("lumbershare"),
        "papershare": db_data.get("papershare"),
        "fuelshare": db_data.get("fuelshare"),
        "import_lumber": db_data.get("import_lumber"),
        "import_paper": db_data.get("import_paper"),
        "construction_multistory_val": db_data.get("construction_multistory_val"),
        "construction_single_val": db_data.get("construction_single_val"),
        "manufacturing_val": db_data.get("manufacturing_val"),
        "packaging_val": db_data.get("packaging_val"),
        "other_val": db_data.get("other_val"),
        "other_construction_val": db_data.get("other_construction_val"),
        "non_res_construction_val": db_data.get("non_res_construction_val"),
        "recovery_timber": db_data.get("recovery_timber"),
        "logging_intensity": db_data.get("logging_intensity"),

        # 🔹 Nämä listat/dictit voivat olla JSON — varmistetaan dekoodaus
        "state_checklist": db_data.get("state_checklist") or [],
        "state_other": db_data.get("state_other"),
        "organization_size": db_data.get("organization_size"),
        "organization_type": db_data.get("organization_type"),
        "organization_type_other": db_data.get("organization_type_other"),
        "general_comment": db_data.get("general_comment") or "",
        "prof_position": db_data.get("prof_position"),
        "prof_position_other": db_data.get("prof_position_other"),
        "years_experience": db_data.get("years_experience"),

        # Kartat / alueet
        "protWoodlands": db_data.get("protWoodlands"),
        "unprotectedForest": db_data.get("unprotectedForest"),
        "wildlands": db_data.get("wildlands"),
        "farmland": db_data.get("farmland"),
        "developed": db_data.get("developed"),
        "waterAndWetlands": db_data.get("waterAndWetlands"),

        "from_lumber_to_pulp": db_data.get("from_lumber_to_pulp"),

    }

    # 🔥 Lisätään myös kaikki Likert-kysymykset automaattisesti
    for q in likert_questions:
        q_id = q["id"]
        defaults[q_id] = db_data.get(q_id)

        # mahdollinen *_cannot_answer
        cannot_key = f"{q_id}_cannot_answer"
        defaults[cannot_key] = db_data.get(cannot_key, 0)

    return defaults


def get_default(defaults, key):
    """Palauttaa DB-arvon jos se ei ole None, muuten DEFAULTS-arvon"""
    val = defaults.get(key)
    return val if val is not None else DEFAULTS[key]


# JS: päivittää viimeisimmän aktiivisuuden timestampin
app.clientside_callback(
    """
function(n_intervals) {
    if (!window.lastActive) {
        window.lastActive = Date.now() / 1000;
    }

    function updateLastActive() {
        window.lastActive = Date.now() / 1000;
    }

    document.onmousemove = updateLastActive;
    document.onkeypress = updateLastActive;
    document.onclick = updateLastActive;
    document.onscroll = updateLastActive;

    return window.lastActive;
}
    """,
    Output("last-active-ts", "data"),
    Input("activity-interval", "n_intervals"),
)


@app.callback(
    Output("dummy-output", "data"),  # piilotettu placeholder
    Input("activity-interval", "n_intervals"),
    State("last-active-ts", "data"),
    State("user-email", "data"),
    prevent_initial_call=True
)
def check_user_activity(n, last_active_ts, user_email):
    """Update DB with elapsed time every interval"""
    print("ollaan oltu aktiivisia")
    if not last_active_ts or not user_email:
        raise dash.exceptions.PreventUpdate

    now_ts = datetime.datetime.now().timestamp()
    last_active_ts = float(last_active_ts)

    inactivity_sec = now_ts - last_active_ts

    # Päivitä responses-tauluun vain, jos ei liian pitkä passiivisuus
    interval_sec = 30  # päivitys 30s välein
    if inactivity_sec < 10 * 60:  # >10min pidetään passiivisena
        conn = sqlite3.connect(DATA_DB_FILE)
        c = conn.cursor()
        c.execute("""
            UPDATE responses
            SET elapsed_time_seconds = COALESCE(elapsed_time_seconds, 0) + ?
            WHERE email = ?
        """, (interval_sec, user_email))
        conn.commit()
        conn.close()
    else:
        print(f"User {user_email} inactive for {int(inactivity_sec/60)} min")

    return dash.no_update



if __name__ == "__main__":
    app.run(debug=True)



