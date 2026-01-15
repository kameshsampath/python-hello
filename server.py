import os

import snowflake.connector
import streamlit as st
from snowflake.connector import SnowflakeConnection

DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "LOCAL")

# Connection timeout in seconds (fail quickly instead of waiting 60+ seconds)
CONNECTION_TIMEOUT = int(os.getenv("SNOWFLAKE_CONNECTION_TIMEOUT", "15"))

# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title="Palmer Penguins",
    page_icon="🐧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Database Connection
# =============================================================================


@st.cache_resource
def get_db_connection() -> SnowflakeConnection:
    """
    Connects to Snowflake based on DEPLOYMENT_ENV:
    - AWS:    Workload Identity (secretless) for App Runner
    - DOCKER: Environment variables with PAT auth for local container testing
    - LOCAL:  secrets.toml for local development
    """

    if DEPLOYMENT_ENV == "AWS":
        return snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            authenticator="WORKLOAD_IDENTITY",
            workload_identity_provider="AWS",
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            role=os.getenv("SNOWFLAKE_ROLE"),
            user=os.getenv("SNOWFLAKE_USER"),
            login_timeout=CONNECTION_TIMEOUT,
            network_timeout=CONNECTION_TIMEOUT,
        )

    elif DEPLOYMENT_ENV == "DOCKER":
        return snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            role=os.getenv("SNOWFLAKE_ROLE"),
            database=os.getenv("DEMO_DATABASE"),
            login_timeout=CONNECTION_TIMEOUT,
            network_timeout=CONNECTION_TIMEOUT,
        )

    else:
        return snowflake.connector.connect(
            **st.secrets["snowflake"],
            login_timeout=CONNECTION_TIMEOUT,
            network_timeout=CONNECTION_TIMEOUT,
        )


@st.cache_data(ttl=300)
def load_penguins_data():
    """Load penguins data from Snowflake."""
    conn = get_db_connection()
    table_name = f"{os.getenv('DEMO_DATABASE', 'DEMO_DB')}.PUBLIC.PENGUINS"
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    return cur.fetch_pandas_all()


# =============================================================================
# UI Components
# =============================================================================


def render_header():
    """Render the app header with environment badge."""
    # Environment badge styles
    badge_config = {
        "AWS": ("☁️ AWS App Runner", "#FF9900", "#FFF8E7"),
        "DOCKER": ("🐳 Docker", "#2496ED", "#E7F5FF"),
        "LOCAL": ("💻 Local Dev", "#22C55E", "#E7FFF0"),
    }
    label, color, bg_color = badge_config.get(
        DEPLOYMENT_ENV, ("🔧 Unknown", "#666", "#F5F5F5")
    )

    st.markdown(
        f"""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <div style="margin-bottom: 1rem;">
                <span style="
                    background: {bg_color};
                    color: {color};
                    padding: 0.3rem 0.8rem;
                    border-radius: 1rem;
                    font-size: 0.85rem;
                    font-weight: 600;
                    border: 1px solid rgba(0,0,0,0.1);
                ">{label}</span>
            </div>
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">
                🐧 Palmer Penguins Explorer
            </h1>
            <p style="font-size: 1.1rem; color: #666; max-width: 600px; margin: 0 auto;">
                Explore penguin measurements from the Palmer Archipelago, Antarctica.
                Data includes three species: Adelie, Chinstrap, and Gentoo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(df):
    """Render key metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Penguins", f"{len(df):,}")
    with col2:
        st.metric("Species", df["SPECIES"].nunique())
    with col3:
        st.metric("Islands", df["ISLAND"].nunique())
    with col4:
        avg_mass = df["BODY_MASS_G"].mean()
        st.metric("Avg Body Mass", f"{avg_mass:,.0f}g")


def render_sidebar(df):
    """Render sidebar filters and return filtered dataframe."""
    st.sidebar.markdown("### 🔍 Filters")

    # Species filter
    species = st.sidebar.multiselect(
        "Species",
        options=sorted(df["SPECIES"].unique()),
        default=sorted(df["SPECIES"].unique()),
    )

    # Island filter
    islands = st.sidebar.multiselect(
        "Island",
        options=sorted(df["ISLAND"].unique()),
        default=sorted(df["ISLAND"].unique()),
    )

    # Sex filter
    sexes = df["SEX"].dropna().unique()
    sex_filter = st.sidebar.multiselect(
        "Sex",
        options=sorted(sexes),
        default=sorted(sexes),
    )

    # Apply filters
    filtered = df[
        (df["SPECIES"].isin(species))
        & (df["ISLAND"].isin(islands))
        & (df["SEX"].isin(sex_filter))
    ]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Showing {len(filtered):,}** of {len(df):,} penguins")

    return filtered


def render_charts(df):
    """Render data visualizations."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Species Distribution")
        species_counts = df["SPECIES"].value_counts()
        st.bar_chart(species_counts)

    with col2:
        st.markdown("#### 🏝️ Penguins by Island")
        island_counts = df["ISLAND"].value_counts()
        st.bar_chart(island_counts)

    st.markdown("#### 📏 Body Mass vs Flipper Length")
    chart_data = df[["FLIPPER_LENGTH_MM", "BODY_MASS_G", "SPECIES"]].dropna()
    st.scatter_chart(
        chart_data,
        x="FLIPPER_LENGTH_MM",
        y="BODY_MASS_G",
        color="SPECIES",
        height=400,
    )


def render_data_table(df):
    """Render the data table."""
    st.markdown("#### 📋 Data Table")
    st.dataframe(
        df,
        width="stretch",
        height=400,
        column_config={
            "SPECIES": st.column_config.TextColumn("Species", width="medium"),
            "ISLAND": st.column_config.TextColumn("Island", width="medium"),
            "BILL_LENGTH_MM": st.column_config.NumberColumn(
                "Bill Length (mm)", format="%.1f"
            ),
            "BILL_DEPTH_MM": st.column_config.NumberColumn(
                "Bill Depth (mm)", format="%.1f"
            ),
            "FLIPPER_LENGTH_MM": st.column_config.NumberColumn(
                "Flipper Length (mm)", format="%.0f"
            ),
            "BODY_MASS_G": st.column_config.NumberColumn("Body Mass (g)", format="%d"),
            "SEX": st.column_config.TextColumn("Sex", width="small"),
        },
    )


# =============================================================================
# Main App
# =============================================================================


def main():
    render_header()

    try:
        with st.spinner("Loading penguin data..."):
            df = load_penguins_data()

        # Sidebar filters
        filtered_df = render_sidebar(df)

        # Metrics
        render_metrics(filtered_df)

        st.markdown("---")

        # Charts
        render_charts(filtered_df)

        st.markdown("---")

        # Data table
        render_data_table(filtered_df)

        # Footer
        st.markdown("---")
        st.caption(
            f"🚀 Running on **{DEPLOYMENT_ENV}** | "
            "Data: [Palmer Penguins](https://allisonhorst.github.io/palmerpenguins/)"
        )

    except Exception as e:
        st.error(f"Failed to load data: {e}")
        if DEPLOYMENT_ENV == "AWS":
            st.warning(
                "**AWS Workload Identity Check:**\n"
                "- Is the instance role attached to the App Runner service?\n"
                "- Is Snowflake WIDF configured for this role?\n"
                "- Can the VPC reach Snowflake? (Check egress/PrivateLink settings)"
            )
        st.info("Please check your database connection and try again.")


if __name__ == "__main__":
    main()
