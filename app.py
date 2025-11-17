from dash import Dash, dcc, html, Input, Output, State
import dash
import plotly.graph_objects as go
import sqlite3
import pandas as pd
import dash_daq as daq
import dash_bootstrap_components as dbc
import numpy as np

# --- Default values ---
# total forest area (constant)

organization_options = [
    {"label": "Forest management organization", "value": "forest_mgmt"},
    {"label": "Foundation (e.g., forestry or conservation foundation)", "value": "foundation"},
    {"label": "Wood product manufacturer", "value": "manufacturer"},
    {"label": "State or regional government agency", "value": "state_gov"},
    {"label": "National government agency", "value": "national_gov"},
    {"label": "Design or engineering firm (e.g., structural or architectural)", "value": "design_firm"},
    {"label": "Other", "value": "other"}
]

role_options = [
    {"label": "Logger / forestry contractor", "value": "logger"},
    {"label": "Director / manager", "value": "director"},
    {"label": "Sales representative", "value": "sales_rep"},
    {"label": "Civil servant / public officer", "value": "civil_servant"},
    {"label": "Forester", "value": "forester"},
    {"label": "Researcher / academic", "value": "researcher"},
    {"label": "Designer / engineer", "value": "designer"},
    {"label": "Other", "value": "other"}
]

new_england_states = [
    "Connecticut",
    "Maine",
    "Massachusetts",
    "New Hampshire",
    "Rhode Island",
    "Vermont"
]

TOTAL_FOREST = 31.6

DEFAULTS = {
    "protWoodlands": 21, #20.94,
    "unprotectedForest": 57, #58.49,
    "wildlands": 2, #1.52,
    "farmland": 5, #5.25,
    "developed": 10, #9.9,
    "waterAndWetlands": 5,
    "woodlands_area": 30.31,
    "wildlands_area": 1.29,
    "lumber": 326800,
    "lumbershare": 40,
    "paper": 326800,
    "papershare": 40,
    "from_lumber_to_pulp": 109000,
    "fuelwood": 163500,
    "fuelshare": 20,
    "import_lumber": 149700,
    "import_paper": 114900,
    "construction_multistory": 5,
    "construction_multistory_val": 45072,
    "construction_single": 26,
    "construction_single_val": 97656,
    "manufacturing": 12,
    "manufacturing_val": 45072,
    "packaging": 13,
    "packaging_val": 48828,
    "other": 9,
    "other_val": 33804,
    "other_construction": 28,   #residential repair and remodeling
    "other_construction_val": 105168,
    "non_res_construction": 7,
    "non_res_construction_val": 26292,
    "recovery_timber": 8000,
    "logging_intensity": 27
}

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
     "text": "…is the forest-based sector’s strengthening role in regional economies — by generating revenues, creating jobs, and maintaining profitable operations that support local livelihoods — compared to the current situation?"},
    {"id": "local_owners",
     "text": "…is it that the forest-based sector supports local forest owners by prioritizing the use of locally sourced wood and services, thereby strengthening local livelihoods and forest management capacity?"},
    {"id": "carbon_substitution",
     "text": "…is it that future end-use applications emphasize the use of wood as a substitute for more carbon-intensive materials — for example in construction or through innovative bioeconomy solutions?"},
    {"id": "carbon_storage",
     "text": "…is it that the forest-based sector actively enhances forest growth and increases carbon storage in forests to reduce overall environmental impacts (e.g., greenhouse gas emissions)?"},
    {"id": "biodiversity",
     "text": "…is it for forestry activities to avoid negative impacts on biodiversity and to actively protect or restore forest habitats?"},
    {"id": "local_sourcing",
     "text": "…is it that forest industry and wood construction favor local sourcing and production to reduce transport-related environmental impacts?"},
    {"id": "employment_conditions",
     "text": "…is it that the forest-based sector provides stable employment opportunities and promotes fair working conditions in the region and occupational groups?"},
    {"id": "training_development",
     "text": "…is it that the forest-based sector strengthens regional capacity by providing professional development, training, and career advancement opportunities for its employees, particularly in rural areas?"},
    {"id": "community_engagement",
     "text": "…is it that the forest-based sector actively engages with local communities, assesses social and environmental impacts, and contributes to local well-being through transparent collaboration?"}
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# app = Dash(__name__)
app.title = "Forest Flow Dashboard"

def make_sankey(values):
    labels = [
        "Woodlands (million acres)",  # 0
        "Timber harvesting in New England",                  # 1
        "Wildlands (million acres)",  # 2
        "Lumber (thousand ft³)",      # 3
        "Raw material for paper (thousand ft³)",  # 4
        "Fuelwood (thousand ft³)",    # 5
        "Import (Lumber)",            # 6
        "Import (Paper)",             # 7
        "Conservation",                # 8
        "Construction multistory",      #9
        "Construction single family", # 10
        "Manufacturing",              # 11
        "Packaging",                  # 12
        "Other",                      # 13
        "Residential repair and remodeling",         # 14
        "Nonresidential construction", # 15
        "",          # 16 paper placeholder
        "",             # 17 fuelwood placeholder
        "",             # 18 placeholder for wildlands
        "Sawmill waste"             # 19
        ]


    woodlands = values.get("woodlands") or 0

    sources = [
        1, 1, 1, 6, 7, 3, 3, 3, 3, 3, 3, 3, 3, 4, 5, 3, 3
    ]
    targets = [
        3, 4, 5, 3, 4, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 3, 4
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
        1,
        1,
        1,
        values.get("recovery_timber", 0),
        values.get("from_lumber_to_pulp", 0)
    ]

    node_colors = [
        "#4CAF50",  # 0: Woodlands
        "#81C784",  # 1: Intensity
        "#8D6E63",  # 2: Wildlands
        "#4CAF50",  # 3: Lumber (visible)
        "#81C784",  # 4: Raw material for paper (visible)
        "#C0CA33",  # 5: Fuelwood (visible)
        "#BDBDBD",  # 6: Import Lumber
        "#BDBDBD",  # 7: Import Paper
        "#9E9E9E",  # 8: Conservation
        "#42A5F5",  # 9: Construction multistory
        "#64B5F6",  # 10: Construction single family
        "#7E57C2",  # 11: Manufacturing
        "#FFB300",  # 12: Packaging
        "#BDBDBD",  # 13: Other
        "#BDBDBD",  # 14: Other Construction
        "#BDBDBD",  # 14: Other Construction
        "rgba(0,0,0,0)",  # 15: Paper placeholder (fully transparent)
        "rgba(0,0,0,0)",  # 16: fuelwood placeholder (fully transparent)
        "rgba(0,0,0,0)",  # 15: Paper placeholder (fully transparent)
        "#4CAF50",  # 3: Lumber (loop)

    ]

    link_colors = [
        "#4CAF50",  # 1 → 3 (Intensity → Lumber)
        "#81C784",  # 1 → 4 (Intensity → Paper)
        "#C0CA33",  # 1 → 5 (Intensity → Fuelwood)
        "#BDBDBD",  # 6 → 3 (Import Lumber)
        "#BDBDBD",  # 7 → 4 (Import Paper)
        "#42A5F5",  # 3 → 9 (Construction multistory)
        "#64B5F6",  # 3 → 10 (Construction single family)
        "#7E57C2",  # 3 → 11 (Manufacturing)
        "#FFB300",  # 3 → 12 (Packaging)
        "#BDBDBD",  # 3 → 13 (Other)
        "#BDBDBD",  # 3 → 14 (Other Construction)
        "#BDBDBD",  # 14: Other Construction
        "rgba(0,0,0,0)",  # 4 → 15 (Paper placeholder) fully transparent
        "rgba(0,0,0,0)",  #  (fuelwood placeholder) fully transparent
        "rgba(0,0,0,0)",  # 4 → 15 (Paper placeholder) fully transparent
        "#4CAF50",  # lumber loop)

    ]


    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20,
            label=labels,
            color=node_colors
        ),
        link=dict(source=sources, target=targets, value=values_list, color=link_colors)
    )])

    fig.add_annotation(
        text="Graph 2. Source: USDA Forest Service, ",
        xref="paper", yref="paper",
        x=0, y=-0.15,  # outside bottom left of plot
        showarrow=False,
        font=dict(size=12, color="gray"),
        xanchor="left", yanchor="top"
    )

    fig.update_layout(title_text="", font_size=10,
                      height=550,
                      margin=dict(l=50, r=50, t=50, b=100)
                      )

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
        "protWoodlands": "Protected Woodlands",
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
    df = pd.read_csv("landcover_data_031125.csv", sep=None, engine="python")

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
        title="Forest and Land Use Distribution (% of total area)",
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

app.layout = html.Div([

    html.Div([
        html.H3("Vision for forestry in New England survey", style={"marginBottom": "10px"}),
        html.H4("About this survey"),
        html.P("This survey asks for your views on what the future of forests and the forest industry in New England"
               " should look like in 2060. Your responses will be treated anonymously and will only be analyzed"
               " in relation to the background information you provide in this survey."),
        html.P("The order in which you answer the survey does not matter. However, your adjustments will affect other "
               "variables in different graphs. For example, increasing or decreasing the area of protected or "
               "unprotected forest land in Graph 1 will impact the amount of timber harvesting in New England "
               "in Graph 2."),
        html.P("This survey consists of four main sections: "),
        html.P("1. Background information about you and your organization"),
        html.P("2. Questions about your views on how land cover should develop in New England"),
        html.P("3. Questions about your views on the utilization of forest and wood at different stages: "),
        html.Ul([
            html.P("3.1. Preferred intensity of forest harvesting in New England"),
            html.P("3.2. Preferred focus of production across product groups (lumber, fiber, fuel)"),
            html.P("3.3. Preferred distribution of demand across different end uses")
        ], style={"marginLeft": "20px", "marginTop": "2px"}),
        html.P("4. Questions about views about the desired future role and contributions of the forest based-sector in New England")

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
                "marginTop": "40px"
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
                value=[],
                inline=False,
                switch=False
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
                value=[],
                inline=False,
                style={"marginBottom": "20px"}
            ),
            dcc.Input(
                id="organization_type_other",
                type="text",
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
                value=[],
                inline=False,
                style={"marginBottom": "20px"}
            ),
            dcc.Input(
                id="prof_position_other",
                type="text",
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
            html.H4("2. Land Cover", style={"marginBottom": "20px"}),
            html.P("Adjust the land area parameters individually based on your desired future scenario in 2060."),
            html.P("— the graph will update when shares sum to 100%."),
            html.P("Click 'Set everything to default' to restore initial values."),
            html.P(
                "Note: Your selections here will influence the production volumes displayed in the second graph (Sankey chart).",
                style={
                    "fontSize": "16px",
                    "lineHeight": "1.4",
                    "fontWeight": "bold",
                    "color": "#d9534f",
                    "backgroundColor": "#fff3f0",
                    "padding": "5px",
                    "borderRadius": "4px"
                }
            )
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
            dcc.Graph(id="forest-bar", figure=make_stacked_bar(DEFAULTS))
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
                         style={"color": "green", "marginTop": "10px"}),

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
                            value=DEFAULTS["unprotectedForest"],
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
                            value=DEFAULTS["developed"],
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        ),

                        html.Label([
                            html.Span("Wildlands (%) ", style={"fontWeight": "bold"}),
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
                            value=DEFAULTS["wildlands"],
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        )
                    ], style={"flex": "1", "display": "flex", "flexDirection": "column"}),

                    # Column 2
                    html.Div([
                        html.Label([
                            html.Span("Protected Woodlands (%) ", style={"fontWeight": "bold"}),
                            html.Span(
                                "definition ",
                                title=(
                                    "Woodlands are voluntarily protected from development and "
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
                            value=DEFAULTS["protWoodlands"],
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
                            value=DEFAULTS["farmland"],
                            min=0, max=100, size=70,
                            style={"display": "block", "marginBottom": "20px", "textAlign": "right"}
                        ),

                        html.Label([
                            html.Span("Water & Wetlands (%) ", style={"fontWeight": "bold"}),
                            html.Span(f"(in 2020: {DEFAULTS['waterAndWetlands']}%)",
                                      style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                        ], style={"display": "block", "marginBottom": "5px"}),
                        daq.NumericInput(
                            id="waterAndWetlands",
                            value=DEFAULTS["waterAndWetlands"],
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
                        "padding": "10px 20px",
                        "fontWeight": "bold",
                        "backgroundColor": "#e0e0e0",
                        "borderRadius": "6px",
                        "cursor": "pointer"
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
        html.H4("3. Material flow chart", style={"marginBottom": "10px"}),
        html.P("For each stage of the forest and wood product value chain, indicate how you would like utilization to "
               "change from the 2020 situation to your preferred levels in 2060"),
        html.P("Click 'Set everything to default' to restore initial values."),
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
            dcc.Graph(id="sankey", figure=make_sankey(DEFAULTS))
        ], style={
            "paddingTop": "60px",
            "gap": "20px",
            "margin": "auto",
            "maxWidth": "1200px",
            "width": "100%",

        }),

      #  html.Hr(style={"borderTop": "2px solid #ccc", "margin": "15px 0"}),

        # Three-column input grid
    html.Div([
        # --- Column 1: Logging + Imports ---
        html.Div([
            html.Div([
                html.Label("Material Source", style={"fontWeight": "bold", "marginBottom": "10px"}),

                html.Label([
                    html.Span("Timber harvesting intensity (thousand cubic feets / acre) ", style={"fontWeight": "bold"}),
                    html.Span(f"(in 2020: {DEFAULTS['logging_intensity']} mcf/acre)",
                                style={"fontWeight": "normal"})
                    ]),
                dcc.Slider(
                    id="logging_intensity", min=10, max=45, step=0.5, value=27,
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={i: str(i) for i in range(10, 46, 10)}
                ),

                html.Div(id="total_logging", style={"marginTop": "5px", "fontWeight": "bold", "marginBottom": "10px"}),

                html.Div([
                    html.Label([
                        html.Span("Import lumber ", style={"fontWeight": "bold", "display": "inline-block"}),
                        html.Span(f"(in 2020: {DEFAULTS['import_lumber']:,})",
                                    style={"fontWeight": "normal", "marginLeft": "5px"})
                    ], style={"display": "block", "marginBottom": "10px"}),  # varmistaa block-tason spacing
                    dcc.Slider(
                        id="import_lumber",
                        min=0,
                        max=500000,
                        step=5000,
                        value=149700,
                        tooltip={"placement": "bottom", "always_visible": True},
                        marks={i: f"{i:,}" for i in range(0, 500001, 200000)}
                    )
                ], style={"paddingTop": "40px", "width": "100%"}),


                html.Label([
                    html.Span("Import pulp ", style={"fontWeight": "bold"}),
                    html.Span(f"(in 2020: {DEFAULTS['import_paper']:,})", style={"fontWeight": "normal"})
                ]),
                dcc.Slider(
                    id="import_paper", min=0, max=500000, step=5000, value=114900,
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks={i: f"{i:,}" for i in range(0, 500001, 200000)}
                ),

            ]),
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
                html.Div([
                    html.Label("Product Type", style={'fontWeight': 'bold', "marginBottom": "10px"}),
                    html.Div(id="capacity-status", children="100% ✅ Balanced", style={"color": "green", "marginBottom": "10px"}),

                    # Lumber
               #     html.Label("Lumber total", style={"fontWeight": "bold"}),
                    html.Div(id="lumber_total"),

                    # Lumber share
                    html.Label([
                        html.Span("Lumber share (%) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['lumbershare']}%)", style={"fontWeight": "normal"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    daq.NumericInput(
                        id="lumbershare",
                        value=40,
                        min=0,
                        max=100,
                        size=70,
                        style={
                            "display": "block",
                            "width": "70px",
                            "margin": "0 0 20px 0",
                            "textAlign": "right"
                        }
                    ),

                    # Recovered timber sisennettynä DAQ:nä
                    html.Div([
                        html.Span("• ", style={"color": "#666"}),  # bullet
                        html.Label("Recovered timber (thousand ft³)",
                                   style={"display": "inline-block", "marginLeft": "5px"})
                    ], style={"marginLeft": "20px", "marginBottom": "5px"}),

                    daq.NumericInput(
                        id="recovery_timber",
                        value=DEFAULTS["recovery_timber"],
                        min=100,
                        max=16000,
                        size=70,
                        style={
                            "display": "block",
                            "margin": "0 0 20px 40px",  # Input sisennetty hiukan enemmän
                            "textAlign": "right"
                        }
                    ),

                    dcc.Store(id="lumber", data=DEFAULTS["lumber"]),
                    dcc.Store(id="paper", data=DEFAULTS["paper"]),
                    dcc.Store(id="fuelwood", data=DEFAULTS["fuelwood"]),

                    # Pulp
             #       html.Label("Pulp total", style={"fontWeight": "bold"}),
                    html.Div(id="paper_total"),

                    html.Label([
                        html.Span("Pulp share (%) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['papershare']}%)", style={"fontWeight": "normal"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    daq.NumericInput(
                        id="papershare",
                        value=40,
                        min=0,
                        max=100,
                        size=70,
                        style={
                            "display": "block",
                            "width": "70px",
                            "margin": "0",
                            "marginBottom": "20px",
                            "textAlign": "right"
                        }
                    ),
                    dcc.Store(id="from_lumber_to_pulp", data=DEFAULTS["from_lumber_to_pulp"]),

                    # Fuelwood
                #    html.Label("Fuelwood total", style={"fontWeight": "bold"}),
                    html.Div(id="fuel_total"),

                    html.Label([
                        html.Span("Fuelwood share (%) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['fuelshare']}%)", style={"fontWeight": "normal"})
                    ], style={"display": "block", "marginBottom": "5px"}),

                    daq.NumericInput(
                        id="fuelshare",
                        value=20,
                        min=0,
                        max=100,
                        size=70,
                        style={
                            "display": "block",
                            "width": "70px",
                            "margin": "0",
                            "marginBottom": "10px",
                            "textAlign": "right"
                        }
                    ),

                    html.Div(id="share-warning", style={"fontWeight": "bold", "marginTop": "10px"})
                ]),

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
                html.Div([
                    html.Label("Application / End use", style={'fontWeight': 'bold', "marginBottom": "10px"}),
                    html.Div(id="enduse-status", children="100% ✅ Balanced",
                             style={"color": "green", "fontSize": "18px", "marginBottom": "10px"}),

                    # Construction (multistory)
                    html.Label([
                        html.Span("Construction (multistory) ", style={"fontWeight": "bold"}),
                        html.Span(
                            "definition ",
                            title=(
                                "Includes mobile and modular housing units"
                            ),
                            style={
                                "cursor": "help",
                                "color": "#007BFF",
                                "marginLeft": "5px",
                                "fontWeight": "bold"
                            }
                        ),
                        html.Span(f"(in 2020: {DEFAULTS['construction_multistory']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="construction_multistory",
                        value=DEFAULTS["construction_multistory"],
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

                    # Construction (single-family)
                    html.Label([
                        html.Span("Construction (single-family) ", style={"fontWeight": "bold"}),
                        html.Span(f"(in 2020: {DEFAULTS['construction_single']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="construction_single",
                        value=26,
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

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
                        html.Span(f"(in 2020: {DEFAULTS['manufacturing']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="manufacturing",
                        value=12,
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

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
                        html.Span(f"(in 2020: {DEFAULTS['packaging']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="packaging",
                        value=13,
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

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
                        html.Span(f"(in 2020: {DEFAULTS['other']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="other",
                        value=9,
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

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
                        html.Span(f"(in 2020: {DEFAULTS['non_res_construction']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="non_res_construction",
                        value=7,
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

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

                        html.Span(f"(in 2020: {DEFAULTS['other_construction']}%)",
                                  style={"fontWeight": "normal", "color": "#666", "fontSize": "13px"})
                    ], style={"display": "block", "marginBottom": "5px"}),
                    daq.NumericInput(
                        id="other_construction",
                        value=28,
                        min=0,
                        max=100,
                        size=70,
                        style={"display": "block", "margin": "0", "marginBottom": "20px", "textAlign": "right"}
                    ),

                    # Stores for the values
                    dcc.Store(id="construction_multistory_val", data=DEFAULTS["construction_multistory_val"]),
                    dcc.Store(id="construction_single_val", data=DEFAULTS["construction_single_val"]),
                    dcc.Store(id="manufacturing_val", data=DEFAULTS["manufacturing_val"]),
                    dcc.Store(id="packaging_val", data=DEFAULTS["packaging_val"]),
                    dcc.Store(id="other_val", data=DEFAULTS["other_val"]),
                    dcc.Store(id="other_construction_val", data=DEFAULTS["other_construction_val"]),
                    dcc.Store(id="non_res_construction_val", data=DEFAULTS["non_res_construction_val"])

                ])
            ], className='col-3', style={
                "flex": "1",
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "space-between",
                "width": "100%",
                "minWidth": "0",

            }),
        ], style={
        "gap": "60px",
        "display": "grid",
        "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
        "margin": "auto",
        "maxWidth": "1200px",
        "width": "100%",
        "marginTop": "50px"
    }),

    html.Div([
        html.Button("Set material flow variables to default", id="reset-btn-2", n_clicks=0,
                    style={
                        "marginTop": "20px",
                        "padding": "10px 20px",
                        "fontWeight": "bold",
                        "backgroundColor": "#e0e0e0",
                        "borderRadius": "6px",
                        "cursor": "pointer"
                    }),
    ], style={
        "flex": "1",
        "display": "flex",
        "flexDirection": "column",
        "marginLeft": "20px",
        "alignItems": "center"}
    ),

    html.Hr(style={
        "border": "none",       # remove default border
        "borderTop": "2px solid #ccc",  # grey line
        "margin": "20px 0"      # vertical spacing
    }),

# likert scale GRI questions
    html.Div([
        # Otsikko koko gridin levyinen
        html.H3("In your vision, how important...", style={"gridColumn": "1 / -1", "marginBottom": "20px"}),

        # Kysymykset gridissä
        html.Div([
            html.Div([
                html.Label(q["text"], style={"marginBottom": "5px"}),

                html.Div(
                    dcc.Slider(
                        id={'type': 'importance-slider', 'index': q["id"]},  # 🔑 käytetään tekstipohjaista ID:tä
                        min=1,
                        max=5,
                        step=1,
                        value=3,
                        marks={j: str(j) for j in range(1, 6)},
                        tooltip={"placement": "bottom", "always_visible": True},
                        updatemode='drag'
                    ),
                    style={"width": "100%"}
                ),

                daq.BooleanSwitch(
                    id={'type': 'cannot-answer', 'index': q["id"]},
                    on=False,
                    label="Cannot answer",
                    labelPosition="right",
                    style={"marginTop": "5px"}
                )
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
        })

    ], style={
        "display": "grid",
        "gridTemplateColumns": "1fr",
        "gap": "20px",
        "margin": "auto",
        "maxWidth": "1200px",
        "width": "100%",
        "marginTop": "50px"
    }),

    html.Div([
    # --- Submit-painike ---
    html.Button("Submit your responses", id="submit-btn", n_clicks=0,
                style={"marginTop": "15px", "padding": "10px 20px", "fontWeight": "bold"}),
    ], style={
        "flex": "1",
        "marginRight": "20px",
        "minWidth": "300px"
    }),

    # --- Placeholder for message returned by callback ---
    html.Div(id="submit-msg", style={"marginTop": "10px", "color": "green", "fontWeight": "bold"})

], style={"padding": "20px", "fontFamily": "Arial, sans-serif"})


# --- Callbacks ---
@app.callback(
        Output("protWoodlands", "value"),
        Output("unprotectedForest", "value"),
        Output("developed", "value"),
        Output("farmland", "value"),
        Output("wildlands", "value"),
        Input("reset-btn-1", "n_clicks"),
)

def reset_defaults(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

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
    return values


@app.callback(
        Output("logging_intensity", "value"),
        Output("import_lumber", "value"),
        Output("import_paper", "value"),
        Output("lumbershare", "value"),
        Output("papershare", "value"),
        Output("fuelshare", "value"),
        Output("construction_multistory", "value"),
        Output("construction_single", "value"),
        Output("manufacturing", "value"),
        Output("packaging", "value"),
        Output("other", "value"),
        Output("other_construction", "value"),
        Output("non_res_construction", "value"),
        Input("reset-btn-2", "n_clicks"),
)

def reset_defaults(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    # Kaikki muut paitsi excluded
    values = []

    # Lisätään data-kenttien arvot oikeassa järjestyksessä
    values += [
        DEFAULTS["logging_intensity"],
        DEFAULTS["import_lumber"],
        DEFAULTS["import_paper"],
        DEFAULTS["lumbershare"],
        DEFAULTS["papershare"],
        DEFAULTS["fuelshare"],
        DEFAULTS["construction_multistory"],
        DEFAULTS["construction_single"],
        DEFAULTS["manufacturing"],
        DEFAULTS["packaging"],
        DEFAULTS["other"],
        DEFAULTS["other_construction"],
        DEFAULTS["non_res_construction"]
    ]

    return values

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
    "construction_multistory",
    "construction_single",
    "manufacturing",
    "packaging",
    "other",
    "other_construction",
    "non_res_construction",
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
    "other_construction_val",
    "non_res_construction_val"
]

@app.callback(
    [
        Output("model-data", "data"),
        Output("sankey", "figure"),
        #Output("forest-bar", "figure"),
        Output("capacity-status", "children"),
        Output("capacity-status", "style"),
        Output("enduse-status", "children"),
        Output("enduse-status", "style"),
        Output("total_logging", "children"),
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
        Input("construction_multistory", "value"),
        Input("construction_single", "value"),
        Input("manufacturing", "value"),
        Input("packaging", "value"),
        Input("other", "value"),
        Input("other_construction", "value"),
        Input("non_res_construction", "value"),
        Input("recovery_timber", "value"),
        State("woodlands_area", "data"),
        State("wildlands_area","data"),
        State("lumber", "data"),
        State("paper", "data"),
        State("fuelwood", "data"),
        State("from_lumber_to_pulp", "data"),
        State("construction_multistory_val", "data"),
        State("construction_single_val", "data"),
        State("manufacturing_val", "data"),
        State("packaging_val", "data"),
        State("other_val", "data"),
        State("other_construction_val", "data"),
        State("non_res_construction_val", "data")
    ],
)
def update_all_charts(*vals):
    data = dict(zip(INPUT_ORDER, vals))
    total_shares = data["lumbershare"] + data["papershare"] + data["fuelshare"]

    total_enduse = (
        data["construction_multistory"] +
        data["construction_single"] +
        data["manufacturing"] +
        data["packaging"] +
        data["other"] +
        data["other_construction"] +
        data["non_res_construction"]
    )

    # --- Alustetaan figuurit ---
    bar_fig = dash.no_update
    sankey_fig = dash.no_update  # aluksi None, luodaan vain validien osien perusteella

    # --- 1️⃣ Capacity (lumber/paper/fuel) ---
    if abs(total_shares - 100) > 0.01:
        status_text = f"{total_shares:.0f}% ❌ Must equal 100%"
        status_style = {"color": "red"}
        lumber_demand = vals[INPUT_ORDER.index("lumber")] + vals[INPUT_ORDER.index("import_lumber")] - vals[
            INPUT_ORDER.index("from_lumber_to_pulp")]
        data["lumber"] = vals[INPUT_ORDER.index("lumber")]
        data["paper"] = vals[INPUT_ORDER.index("paper")]
        data["fuelwood"] = vals[INPUT_ORDER.index("fuelwood")]
        total_logging = dash.no_update
        total_logging_text = dash.no_update
    else:
        total_logging = data["logging_intensity"] * (((data["unprotectedForest"] + data["protWoodlands"]))/100 * 40000)
        total_logging_text = f"{total_logging:,.0f} (thousand ft³)"
        print(total_logging)
        data["lumber"] = total_logging * (data["lumbershare"] / 100)

        from_pulp_to_paper = 0.333 * data["lumber"]
        data["from_lumber_to_pulp"] = 0.333 * data["lumber"]
        lumber_demand = (data["lumbershare"] / 100 * total_logging) + data["import_lumber"] - from_pulp_to_paper + data["recovery_timber"]
        data["paper"] = total_logging * (data["papershare"] / 100)
        data["fuelwood"] = total_logging * (data["fuelshare"] / 100)

        #bar_fig = make_stacked_bar(data)
        status_text = f"{total_shares:.0f}% ✅ Balanced"
        status_style = {"color": "green"}

    # --- 2️⃣ End-use (loppukäyttö) ---
    if abs(total_enduse - 100) > 0.01:
        enduse_text = f"{total_enduse:.0f}% ❌ Must equal 100%"
        enduse_style = {"color": "red"}
    else:
        data["construction_multistory_val"] = (data["construction_multistory"] / 100) * lumber_demand
        data["construction_single_val"] = (data["construction_single"] / 100) * lumber_demand
        data["manufacturing_val"] = (data["manufacturing"] / 100) * lumber_demand
        data["packaging_val"] = (data["packaging"] / 100) * lumber_demand
        data["other_val"] = (data["other"] / 100) * lumber_demand
        data["other_construction_val"] = (data["other_construction"] / 100) * lumber_demand
        data["non_res_construction_val"] = (data["non_res_construction"] / 100) * lumber_demand
        enduse_text = f"{total_enduse:.0f}% ✅ Balanced"
        enduse_style = {"color": "green"}

    # --- Sankey-päivitys vain, jos molemmat balanssissa ---
    if abs(total_shares - 100) <= 0.01 and abs(total_enduse - 100) <= 0.01:
        sankey_fig = make_sankey(data)
    else:
        sankey_fig = dash.no_update

    return (
        data,
        sankey_fig,
        # bar_fig,
        status_text,
        status_style,
        enduse_text,
        enduse_style,
        total_logging_text,
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
          if k not in ["woodlands_area", "wildlands_area", "from_lumber_to_pulp", "lumber", "paper", "fuelwood","construction_multistory_val",
                         "construction_single_val", "manufacturing_val", "packaging_val", "other_val",
                         "other_construction_val", "non_res_construction_val"]]

# Add lumber, paper, fuelwood as separate States
states += [
    State("woodlands_area", "data"),
    State("wildlands_area", "data"),
    State("lumber", "data"),
    State("paper", "data"),
    State("fuelwood", "data"),
    State("from_lumber_to_pulp", "data"),
    State("construction_multistory_val", "data"),
    State("construction_single_val", "data"),
    State("manufacturing_val", "data"),
    State("packaging_val", "data"),
    State("other_val", "data"),
    State("other_construction_val", "data"),
    State("non_res_construction_val", "data")
]

@app.callback(
    Output("submit-msg", "children"),
    Input("submit-btn", "n_clicks"),
    states
)
def submit_to_db(n_clicks, *vals):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    # Open DB connection
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

  # Insert all values (15 placeholders)
    c.execute("""
    INSERT INTO responses 
    (woodlands_area, wildlands_area, lumber, paper, fuelwood, import_lumber, import_paper,
     construction_multistory, construction_single, manufacturing, packaging, other, other_construction, non_res_construction,
     recovery_timber, from_lumber_to_pulp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, vals)

    conn.commit()
    conn.close()

    return "✅ Responses saved successfully!"


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
    print(wild)
    values_list = [wild or 0, prot or 0, unprot or 0, farm or 0, dev or 0, water]
    total = sum(values_list)
    if round(total, 1) != 100:
        warning = f"⚠️ The shares must sum to 100% (now {total:.1f}%)."
        return dash.no_update, warning, {"color": "red", "fontWeight": "bold"}
    else:
        values = {
            "wildlands": wild,
            "protWoodlands": prot,
            "unprotectedForest": unprot,
            "farmland": farm,
            "developed": dev,
            "waterAndWetlands": water
        }

        fig = make_stacked_bar(values)
        return fig, "✅ Shares sum to 100%", {"color": "green", "fontWeight": "bold"}


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


if __name__ == "__main__":
    app.run(debug=True)



