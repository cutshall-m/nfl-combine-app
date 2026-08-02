import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & DATABASE CONNECTION
# -------------------------------------------------------------
st.set_page_config(page_title="NFL Combine Reference", layout="wide")

@st.cache_resource
def get_db_engine():
    """
    Using SQLAlchemy to create an engine once and caches it to prevent reconnecting 
    every time a UI element changes.
    """
    try:
        db_config = st.secrets["mysql"]
        # Format: mysql+pymysql://user:password@host:port/database
        connection_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        return create_engine(connection_url)
    except KeyError:
        st.error("Database credentials not found in secrets!")
        st.stop()
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        st.stop()

engine = get_db_engine()

# Data Caching for global properties
@st.cache_data(ttl=3600)
def get_draft_year_bounds():
    query = "SELECT MIn(draft_year) AS min_yr, MAX(draft_year)  AS max_yr FROM draft_result;"
    df = pd.read_sql(query, engine)
    
    # Handle possible empty result
    if df.empty or pd.isna(df['min_yr'].iloc[0]):
        return 2000, 2026
    
    return int(df['min_yr'].iloc[0]), int(df['max_yr'].iloc[0])

min_yr, max_yr = get_draft_year_bounds()



# -------------------------------------------------------------
# VERTICAL NAVIGATION SIDEBAR
# -------------------------------------------------------------
st.sidebar.title("NFL Combine")

nav_options = [
    "Welcome",
    "Draft Results by Year",
    "Top Athletic Performers",
    "Draft Volume by Conference & School",
    "NFL Team Drafting Tendencies",
    "Personalized Draft Predictor",
]

def navigate_to_predictor():
    st.session_state["nav_selection"] = "Personalized Draft Predictor"

selected_nav = st.sidebar.radio(
    label="Navigation",
    options=nav_options,
    label_visibility="collapsed",
    key="nav_selection",
)

# -------------------------------------------------------------
# PAGE 1: WELCOME
# -------------------------------------------------------------
if selected_nav == "Welcome":
    st.title("NFL Combine Reference")
    st.markdown("---")

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown("### **Welcome to the NFL Draft Combine Reference**")
        st.write(
            f"This platform offers an analytical workspace featuring"
            f" historic scouting data, metric distributions, and outcome metrics"
            f" recorded across every official NFL Scouting Combine from **{min_yr}**"
            f" through **{max_yr}**."
        )

        st.markdown("#### **Key Features Included:**")
        st.markdown("""
            * **Draft Results Search:** Query official draft selections by year.
            * **Top Athletic Performers:** Identify historic drill leaders filtered across positions.
            * **Conference & School Volume:** Evaluate positional production by college program.
            * **NFL Team Tendencies:** Analyze franchise draft strategies and primary target schools.
            * **Personalized Draft Predictor:** Test your own combine metrics against trained linear regression models!
            """)

        st.write("")

        with st.container(border=True):
            st.markdown("### **Where Would You Be Drafted?**")
            st.write(
                "Test your athletic numbers in our regression modeling tool to"
                " calculate your projected NFL draft round and overall pick number."
            )
            st.button(
                "Go to Personalized Draft Predictor",
                type="primary",
                use_container_width=True,
                on_click=navigate_to_predictor,
            )

    with col_right:
        st.write("")
        st.write("")
        logo_path = "assets/NFL_Scouting_Combine_logo.svg.webp"
        
        try:
            st.image(
                logo_path,
                caption="Official NFL Scouting Combine Data Hub",
                use_container_width=True,
            )
        except Exception as img_err:
            st.warning("Please ensure the 'assets' folder contains 'NFL_Scouting_Combine_logo.svg.webp'.")

# -------------------------------------------------------------
# PAGE 2: DRAFT RESULTS BY YEAR
# -------------------------------------------------------------
elif selected_nav == "Draft Results by Year":
    st.title("Historical Draft Results")
    st.markdown("---")

    years_list = list(range(max_yr, min_yr - 1, -1))
    selected_year = st.selectbox("Select Draft Year", years_list, index=0)

    # Cached function for retrieving year data
    @st.cache_data(ttl=3600)
    def get_draft_results_by_year(year):
        query = text("""SELECT  d.draft_year, d.draft_round, d.draft_pick, d.drafting_team, p.first_name, p.last_name, p.position_abr, p.school, c.forty_yd_dash, c.vert_jump, c.bench_press, c.broad_jump, c.cone_drill, c.twenty_yd_dash
            FROM draft_result d
            JOIN player p on d.player_id = p.player_id
            LEFT JOIN combine_result c on p.player_id =  c.player_id
            WHERE d.draft_year = :year
            ORDER BY  d.draft_pick ASC;""")
        return pd.read_sql(query, engine, params={"year": year})

    df_year = get_draft_results_by_year(selected_year)

    st.subheader(f"Draft Selections for {selected_year}")
    st.dataframe(df_year, use_container_width=True)

# -------------------------------------------------------------
# PAGE 3: TOP ATHLETIC PERFORMERS
# -------------------------------------------------------------
elif selected_nav == "Top Athletic Performers":
    st.title(f"Top Athletic Performers ({min_yr}–{max_yr})")
    st.markdown("---")

    @st.cache_data(ttl=3600)
    def get_all_positions():
        return pd.read_sql(
            "SELECT DISTINCT Position_desc  FROM fb_position WHERE Position_desc IS NOT NULL ORDER By Position_desc;",
            engine
        )

    all_positions = list(get_all_positions()["Position_desc"])

    col_sel1, col_sel2 = st.columns([4, 1])
    with col_sel2:
        st.write("")
        st.write("")
        select_all = st.checkbox("Select All Positions", value=True)

    with col_sel1:
        if select_all:
            selected_positions = st.multiselect(
                "Filter by Position(s):", all_positions, default=all_positions
            )
        else:
            selected_positions = st.multiselect(
                "Filter by Position(s):", all_positions, default=[]
            )

    @st.cache_data(ttl=3600)
    def get_top_performers(metric_col, sort_order, positions_tuple):
        # Format string for IN clause securely (whitelist from the multiselect)
        placeholders = ", ".join([f"'{p}'" for p in positions_tuple])
        query = f"""SELECT p.first_name, p.last_name, pos.Position_desc AS position, d.draft_year, d.draft_round, d.draft_pick, c.{metric_col}
            FROM combine_result c
            JOIN player p On c.player_id = p.player_id
            LEFT JOIN fb_position pos ON p.position_abr = pos.position_abr
             LEFT JOIN draft_result d on p.player_id = d.player_id
            WHERE c.{metric_col} IS NOT NULL AND pos.Position_desc IN ({placeholders})
            ORDER BY c.{metric_col} {sort_order} LIMIT 5;"""
        return pd.read_sql(query, engine)

    if not selected_positions:
        st.warning("Please select at least one position to view top performers.")
    else:
        # Convert list to tuple so it can be cached
        pos_tuple = tuple(selected_positions)

        st.subheader("Top 5 Fastest by 40-Yard Dash")
        st.dataframe(get_top_performers("forty_yd_dash", "ASC", pos_tuple), use_container_width=True)

        st.markdown("---")
        st.subheader("Top 5 Strongest by Bench Press")
        st.dataframe(get_top_performers("bench_press", "DESC", pos_tuple), use_container_width=True)

        st.markdown("---")
        st.subheader("Top 5 Quickest by 3 Cone Drill")
        st.dataframe(get_top_performers("cone_drill", "ASC", pos_tuple), use_container_width=True)

        st.markdown("---")
        st.subheader("Top 5 Leapers by Vertical Jump")
        # Include broad jump for this table just as the original code did
        df_leapers = get_top_performers("vert_jump", "DESC", pos_tuple)
        st.dataframe(df_leapers, use_container_width=True)


# -------------------------------------------------------------
# PAGE 4: DRAFT VOLUME BY CONFERENCE & SCHOOL
# -------------------------------------------------------------
elif selected_nav == "Draft Volume by Conference & School":
    st.title(f"Draft Volume by Conference & School ({min_yr}–{max_yr})")
    st.markdown("---")

    @st.cache_data(ttl=3600)
    def get_school_volume():
        volume_query = text("""SELECT 
                    CASE 
                     WHEN conf.school_power IS NULL THEN 'FBS'
                    WHEN LOWER(conf.school_power) LIKE '%ncaa div iii%' THEN 'Division III'
                    WHEN LOWER(conf.school_power) LIKE '%ncaa div ii%' THEN 'Division II'
                    WHEN LOWER(conf.school_power) LIKE  '%fcs%' THEN 'FCS'
                    WHEN LOWER(conf.school_power)  LIKE '%naia%' OR LOWER(conf.school_power) LIKE '%defunct%' THEN 'Other' ELSE 'FBS'
                END as Division,
                conf.school_power AS Conference, p.school AS School,
                COUNT(d.draft_pick) AS Total_Players_Drafted,
                COUNT(CASE WHEN d.draft_round = 1 THEN 1 END) AS First_Round_Players_Drafted
            FROM draft_result d
            JOIN player p ON d.player_id = p.player_id
            LEFT JOIN conference conf on p.school = conf.school
             GROUP BY Division, conf.school_power, p.school
             ORDER BY Total_Players_Drafted  DESC, First_Round_Players_Drafted  DESC;""")
        return pd.read_sql(volume_query, engine)

    df_all_volume = get_school_volume()

    st.subheader("Filter by Classification")
    div_order = ["FBS", "FCS", "Division II", "Division III", "Other"]
    selected_division = st.selectbox(
        "Select Division:", div_order, index=0, key="division_select"
    )

    df_div = df_all_volume[df_all_volume["Division"] == selected_division]

    st.write("")

    schools_in_div = sorted(df_div["School"].dropna().unique().tolist())

    col_school1, col_school2 = st.columns([4, 1])
    with col_school2:
        st.write("")
        st.write("")
        select_all_schools = st.checkbox(
            "Select All Schools", value=True, key="school_all"
        )

    with col_school1:
        if select_all_schools:
            selected_schools = st.multiselect(
                "Filter by School(s):",
                schools_in_div,
                default=schools_in_div,
                key="school_select",
            )
        else:
            selected_schools = st.multiselect(
                "Filter by School(s):",
                schools_in_div,
                default=[],
                key="school_select",
            )

    if not selected_schools:
        st.warning(
            f"Please select at least one school from {selected_division} to view"
            " draft volume."
        )
    else:
        df_final = df_div[df_div["School"].isin(selected_schools)]

        tot_players = df_final["Total_Players_Drafted"].sum()
        tot_1st = df_final["First_Round_Players_Drafted"].sum()

        st.markdown("---")

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Selected Schools", len(selected_schools))
        metric_col2.metric("Total Drafted Players", f"{tot_players:,}")
        metric_col3.metric("Total 1st Round Picks", f"{tot_1st:,}")

        st.markdown("---")
        st.subheader(f"School Draft Volume Summary ({selected_division})")

        display_cols = [
            "Division",
            "Conference",
            "School",
            "Total_Players_Drafted",
            "First_Round_Players_Drafted",
        ]
        st.dataframe(df_final[display_cols], use_container_width=True)

# -------------------------------------------------------------
# PAGE 5: NFL TEAM DRAFTING TENDENCIES
# -------------------------------------------------------------
elif selected_nav == "NFL Team Drafting Tendencies":
    st.title(f"NFL Team Drafting Tendencies ({min_yr}–{max_yr})")
    st.markdown("---")

    @st.cache_data(ttl=3600)
    def get_team_tendencies():
        team_draft_query = """SELECT d.drafting_team AS Team,
                pos.Position_desc AS Position_Desc,
                p.school AS  School,
                d.draft_round AS Draft_Round,
                d.draft_pick aS Draft_Pick
            FROM draft_result d
            JOIN player p ON d.player_id = p.player_id
            LEFT JOIN fb_position pos ON p.position_abr = pos.position_abr
            WHERE d.drafting_team IS NOT NULL AND d.drafting_team != ''
            ORDER BY d.drafting_team ASC;"""
        return pd.read_sql(team_draft_query, engine)

    raw_team_df = get_team_tendencies()

    if raw_team_df.empty:
        st.warning("No NFL team draft data available.")
    else:
        sorted_teams = sorted(raw_team_df["Team"].unique())
        selected_team = st.selectbox(
            "Select NFL Team", sorted_teams, index=0, key="team_tendencies_select"
        )

        team_group = raw_team_df[raw_team_df["Team"] == selected_team]
        total_drafted = len(team_group)

        school_counts = team_group["School"].value_counts().dropna()
        if not school_counts.empty:
            top_school_name = school_counts.index[0]
            top_school_cnt = school_counts.iloc[0]
            top_school_str = f"{top_school_name} ({top_school_cnt})"
        else:
            top_school_str = "N/A"

        r1_picks = team_group[team_group["Draft_Round"] == 1]["Draft_Pick"]
        if not r1_picks.empty:
            avg_r1_pick = int(round(r1_picks.mean()))
            avg_r1_str = f"Pick #{avg_r1_pick}"
        else:
            avg_r1_str = "No 1st Rd Picks"

        st.markdown("---")

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Top School Drafted From", top_school_str)
        metric_col2.metric("Avg 1st Round Pick Order", avg_r1_str)
        metric_col3.metric("Total Players Drafted", f"{total_drafted:,}")

        st.markdown("---")
        st.subheader(f"Draft Volume by Position ({selected_team})")

        pos_counts = team_group["Position_Desc"].value_counts().dropna()

        if not pos_counts.empty:
            pos_cols = st.columns(3)
            for idx, (pos_name, count) in enumerate(pos_counts.items()):
                col = pos_cols[idx % 3]
                col.metric(label=pos_name, value=count)
        else:
            st.info("No position volume data recorded for this team.")

# -------------------------------------------------------------
# PAGE 6: PERSONALIZED DRAFT PREDICTOR
# -------------------------------------------------------------
elif selected_nav == "Personalized Draft Predictor":
    st.title("Personalized Draft Predictor")
    st.markdown("---")

    @st.cache_data(ttl=3600)
    def get_predictor_positions():
        return pd.read_sql(
               "SELECT position_abr, Position_desc FROM fb_position ORDER BY Position_desc;",
            engine
        )

    positions_df = get_predictor_positions()

    pos_map = {}
    for _, row in positions_df.iterrows():
        desc = row["Position_desc"]
        abr = row["position_abr"]

        if desc not in pos_map:
            pos_map[desc] = abr
        elif abr == "S":
            pos_map[desc] = abr

    unique_descriptions = list(pos_map.keys())

    selected_pos_desc = st.selectbox(
        "Select Position", unique_descriptions, key="predictor_pos_select"
    )

    if selected_pos_desc:
        selected_pos = pos_map[selected_pos_desc]

        @st.cache_data(ttl=3600)
        def get_model_weights(pos):
            query = text("""SELECT position_abr, Intercept, Weight_40yd_Dash, Weight_Vertical_Jump, Weight_Bench_Press, Weight_Broad_Jump, Weight_3Cone_Drill, Weight_20yd_Shuttle FROM attribute_coefficients  WHERE position_abr = :pos;""")
            df = pd.read_sql(query, engine, params={"pos": pos})
            
            # Fallback for Safeties
            if df.empty and pos == "S":
                df = pd.read_sql(query, engine, params={"pos": "SAF"})
            
            # Absolute Fallback if no weights exist
            if df.empty:
                return {
                    "position_abr": pos, "Intercept": -3.5, "Weight_40yd_Dash": 4.0,
                    "Weight_Vertical_Jump": -0.05, "Weight_Bench_Press": 0.03,
                    "Weight_Broad_Jump": -0.02, "Weight_3Cone_Drill": -0.8,
                    "Weight_20yd_Shuttle": -0.4,
                }
            return df.iloc[0].to_dict()

        weights = get_model_weights(selected_pos)

        @st.cache_data(ttl=3600)
        def get_position_ranges(pos):
            pos_tuple = ("S", "SAF") if pos in ["S", "SAF"] else (pos, pos)
            query = text("""SELECT 
                     MIN(c.forty_yd_dash) AS min_40, MAX(c.forty_yd_dash) AS max_40,
                    MIN(c.vert_jump) AS min_vert, MAX(c.vert_jump) As max_vert,
                    MIN(c.bench_press) AS min_bench, MAX(c.bench_press) AS max_bench,
                    MIN(c.broad_jump) AS min_broad, MAX(c.broad_jump) AS max_broad,
                    MIN(c.cone_drill) as min_cone, MAX(c.cone_drill)  AS max_cone,
                    MIN(c.twenty_yd_dash) AS min_shuttle, MAX(c.twenty_yd_dash) AS max_shuttle
                FROM combine_result c
                 JOIN player p on c.player_id = p.player_id
                 WHERE p.position_abr IN (:pos1, :pos2);""")
            df = pd.read_sql(query, engine, params={"pos1": pos_tuple[0], "pos2": pos_tuple[1]})
            return df.iloc[0].to_dict()

        ranges = get_position_ranges(selected_pos)

        # Update 5: Streamlining Defaults to avoid step mismatch errors in Streamlit
        min_40 = float(ranges["min_40"]) if pd.notna(ranges["min_40"]) else 4.20
        max_40 = float(ranges["max_40"]) if pd.notna(ranges["max_40"]) else 5.80
        val_40 = round((min_40 + max_40) / 2, 2)  # Fits 0.01 step

        min_v = float(ranges["min_vert"]) if pd.notna(ranges["min_vert"]) else 20.0
        max_v = float(ranges["max_vert"]) if pd.notna(ranges["max_vert"]) else 45.0
        # Formula ensures rounding strictly to the nearest 0.5 interval
        val_v = round(((min_v + max_v) / 2) * 2) / 2  

        min_b = int(ranges["min_bench"]) if pd.notna(ranges["min_bench"]) else 0
        max_b = int(ranges["max_bench"]) if pd.notna(ranges["max_bench"]) else 45
        val_b = int(round((min_b + max_b) / 2)) # Fits integer step

        min_bj = float(ranges["min_broad"]) if pd.notna(ranges["min_broad"]) else 80.0
        max_bj = float(ranges["max_broad"]) if pd.notna(ranges["max_broad"]) else 145.0
        val_bj = round(((min_bj + max_bj) / 2) * 2) / 2  # Fits 0.5 step

        min_c = float(ranges["min_cone"]) if pd.notna(ranges["min_cone"]) else 6.30
        max_c = float(ranges["max_cone"]) if pd.notna(ranges["max_cone"]) else 9.00
        val_c = round((min_c + max_c) / 2, 2) # Fits 0.01 step

        min_s = float(ranges["min_shuttle"]) if pd.notna(ranges["min_shuttle"]) else 3.80
        max_s = float(ranges["max_shuttle"]) if pd.notna(ranges["max_shuttle"]) else 5.20
        val_s = round((min_s + max_s) / 2, 2) # Fits 0.01 step

        with st.form(key="predictor_form"):
            user_name = st.text_input(
                "Prospect Name",
                placeholder="Enter prospect name (e.g., John Doe)",
                key="prospect_name_input",
            )

            st.markdown("---")
            st.subheader(
                f"Adjust Combine Drill Metrics for **{selected_pos_desc}"
                f" ({weights['position_abr']})**"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                dash_40 = st.slider(
                    "40-Yard Dash (sec)",
                    min_value=min_40, max_value=max_40, value=val_40,
                    step=0.01, format="%.2f", key="dash_40_slider",
                )
                vert_jump = st.slider(
                    "Vertical Jump (inches)",
                    min_value=min_v, max_value=max_v, value=val_v,
                    step=0.5, format="%.1f", key="vert_jump_slider",
                )

            with col2:
                bench_press = st.slider(
                    "Bench Press (reps)",
                    min_value=min_b, max_value=max_b, value=val_b,
                    step=1, key="bench_press_slider",
                )
                broad_jump = st.slider(
                    "Broad Jump (inches)",
                    min_value=min_bj, max_value=max_bj, value=val_bj,
                    step=0.5, format="%.1f", key="broad_jump_slider",
                )

            with col3:
                cone_3 = st.slider(
                    "3-Cone Drill (sec)",
                    min_value=min_c, max_value=max_c, value=val_c,
                    step=0.01, format="%.2f", key="cone_3_slider",
                )
                shuttle_20 = st.slider(
                    "20-Yard Shuttle (sec)",
                    min_value=min_s, max_value=max_s, value=val_s,
                    step=0.01, format="%.2f", key="shuttle_20_slider",
                )

            st.write("")
            submit_btn = st.form_submit_button(
                "Calculate Draft Projection", type="primary"
            )

        if submit_btn:
            raw_pick_prediction = (
                float(weights["Intercept"])
                + (dash_40 * float(weights["Weight_40yd_Dash"]))
                + (vert_jump * float(weights["Weight_Vertical_Jump"]))
                + (bench_press * float(weights["Weight_Bench_Press"]))
                + (broad_jump * float(weights["Weight_Broad_Jump"]))
                + (cone_3 * float(weights["Weight_3Cone_Drill"]))
                + (shuttle_20 * float(weights["Weight_20yd_Shuttle"]))
            )

            predicted_pick = max(1, min(256, round(raw_pick_prediction)))
            predicted_round = max(1, min(7, ((predicted_pick - 1) // 32) + 1))

            res_col1, res_col2 = st.columns(2)
            res_col1.metric("Predicted Draft Round", f"Round {predicted_round}")
            res_col2.metric("Predicted Overall Pick", f"Pick #{predicted_pick}")

            st.markdown("---")

            display_name = (
                user_name.strip() if user_name and user_name.strip() else "Prospect"
            )

            if predicted_round in [1, 2]:
                st.success(
                    f"**Great Performance!** Excellent work, **{display_name}**!"
                    " Your combine measurements project you as a high-value prospect"
                    f" going in **Round {predicted_round} (Pick #{predicted_pick})**."
                    " Keep up the great athletic training!"
                )
            elif predicted_round in [3, 4]:
                st.info(
                    f"**Average / Solid Performance!** Good job, **{display_name}**!"
                    " Your combine metrics project you as a solid mid-round selection"
                    f" in **Round {predicted_round} (Pick #{predicted_pick})**. With a"
                    " little fine-tuning, you have a great foundation for the next"
                    " level!"
                )
            else:
                st.warning(
                    f"**Below Average Result.** **{display_name}**, your projected draft"
                    f" position is **Round {predicted_round} (Pick #{predicted_pick})**."
                    " Don't be discouraged! Many NFL stars start in later rounds or as"
                    " priority free agents—focusing on core drill speed and technique"
                    " can help boost these numbers!"
                )

        with st.expander("View Model Weights & Coefficients"):
            st.json(weights)
