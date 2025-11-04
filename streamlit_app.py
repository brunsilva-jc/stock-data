"""
Streamlit Dashboard for Cryptocurrency Data Visualization
Enhanced with candlestick charts, comparison views, and advanced analytics
Now with Historical DB mode powered by TimescaleDB!
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.services.alphavantage import alphavantage_service
from app.models.currency import CurrencyDataProcessor
from app.database.session import SessionLocal
from app.database.repository import (
    CryptoCurrencyRepository,
    CryptoPriceRepository,
)


# Page configuration
st.set_page_config(
    page_title="Crypto Data Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive {
        color: #00b300;
        font-weight: bold;
    }
    .negative {
        color: #ff0000;
        font-weight: bold;
    }
    .volatility-high {
        color: #ff6600;
        font-weight: bold;
    }
    .volatility-low {
        color: #006600;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes to respect API rate limits
def fetch_crypto_data(symbol: str, market: str):
    """
    Fetch cryptocurrency data from API with caching.

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH)
        market: Market currency (e.g., USD)

    Returns:
        Processed currency response or error message
    """
    try:
        # Run async function in sync context
        raw_data = asyncio.run(
            alphavantage_service.get_digital_currency_daily(symbol, market)
        )
        processed_data = CurrencyDataProcessor.process_response(raw_data)
        return processed_data, None
    except ValueError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Error fetching data: {str(e)}"


@st.cache_data(ttl=60)  # Cache for 1 minute (database queries are fast)
def fetch_crypto_data_from_db(
    symbol: str, market: str, start_date: datetime, end_date: datetime
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Fetch cryptocurrency data from database.

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH)
        market: Market currency (e.g., USD)
        start_date: Start date for data range
        end_date: End date for data range

    Returns:
        DataFrame with OHLCV data or error message
    """
    db = SessionLocal()
    try:
        # Get currency record
        currency = CryptoCurrencyRepository.get_by_symbol_and_market(
            db, symbol, market
        )

        if not currency:
            return None, f"No data found for {symbol}/{market} in database. Please run the seed script first."

        # Fetch price data
        prices = CryptoPriceRepository.get_by_date_range(
            db, currency.id, start_date, end_date
        )

        if not prices:
            return None, f"No price data found for {symbol}/{market} between {start_date.date()} and {end_date.date()}"

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'date': price.timestamp.date(),
                'timestamp': price.timestamp,
                'open': price.open,
                'high': price.high,
                'low': price.low,
                'close': price.close,
                'volume': price.volume,
            }
            for price in prices
        ])

        return df, None

    except Exception as e:
        return None, f"Database error: {str(e)}"
    finally:
        db.close()


def get_db_stats(symbol: str, market: str, start_date: datetime, end_date: datetime) -> Optional[dict]:
    """Get statistics from database for a date range."""
    db = SessionLocal()
    try:
        currency = CryptoCurrencyRepository.get_by_symbol_and_market(db, symbol, market)
        if not currency:
            return None

        stats = CryptoPriceRepository.get_stats(db, currency.id, start_date, end_date)
        return stats
    except Exception as e:
        st.error(f"Error getting stats: {str(e)}")
        return None
    finally:
        db.close()


def format_number(num, prefix="", suffix=""):
    """Format numbers with commas and optional prefix/suffix."""
    if num is None:
        return "N/A"
    return f"{prefix}{num:,.2f}{suffix}"


def create_candlestick_chart(recent_data, market="USD"):
    """Create an interactive candlestick chart with volume bars from API data."""
    df = pd.DataFrame([
        {
            'date': data.date,
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume
        }
        for data in recent_data
    ])

    # Reverse order for chronological display
    df = df.iloc[::-1]

    return create_candlestick_chart_from_df(df, market)


def create_candlestick_chart_from_df(df: pd.DataFrame, market: str = "USD"):
    """Create an interactive candlestick chart with volume bars from DataFrame."""
    # Create subplots: candlestick on top, volume on bottom
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=('Price (OHLC)', 'Volume')
    )

    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC',
            increasing_line_color='#00b300',
            decreasing_line_color='#ff0000'
        ),
        row=1, col=1
    )

    # Add volume bars with color based on price movement
    colors = ['#00b300' if row['close'] >= row['open'] else '#ff0000'
              for _, row in df.iterrows()]

    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            marker_line_color=colors,
            marker_line_width=0.5,
            opacity=0.7
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        title=f"Price & Volume Analysis ({len(df)} Days)",
        xaxis2_title="Date",
        yaxis_title=f"Price ({market})",
        yaxis2_title="Volume",
        hovermode='x unified',
        template='plotly_white',
        height=600,
        showlegend=False,
        xaxis_rangeslider_visible=False
    )

    return fig


def calculate_volatility(recent_data):
    """Calculate price volatility (standard deviation of daily returns)."""
    df = pd.DataFrame([
        {'close': data.close}
        for data in recent_data
    ])

    if len(df) < 2:
        return None

    # Calculate daily returns
    df['returns'] = df['close'].pct_change()

    # Calculate volatility (standard deviation of returns)
    volatility = df['returns'].std() * 100  # Convert to percentage

    return volatility


def create_comparison_chart(crypto_data_dict: Dict, market: str):
    """Create a comparison chart for multiple cryptocurrencies."""
    fig = go.Figure()

    for crypto_name, data in crypto_data_dict.items():
        if data is None:
            continue

        df = pd.DataFrame([
            {'date': d.date, 'close': d.close}
            for d in data.recent_data
        ])

        # Reverse order for chronological display
        df = df.iloc[::-1]

        # Normalize prices to percentage change from first day
        if len(df) > 0:
            first_price = df['close'].iloc[0]
            df['pct_change'] = ((df['close'] - first_price) / first_price) * 100

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['pct_change'],
                mode='lines+markers',
                name=crypto_name,
                line=dict(width=2),
                marker=dict(size=5)
            ))

    fig.update_layout(
        title="Multi-Crypto Comparison (Percentage Change from Start)",
        xaxis_title="Date",
        yaxis_title="Change (%)",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_correlation_heatmap(crypto_data_dict: Dict):
    """Create a correlation heatmap for multiple cryptocurrencies."""
    # Prepare data for correlation
    price_data = {}

    for crypto_name, data in crypto_data_dict.items():
        if data is None:
            continue

        prices = [d.close for d in reversed(data.recent_data)]
        price_data[crypto_name] = prices

    if len(price_data) < 2:
        return None

    # Create DataFrame
    df = pd.DataFrame(price_data)

    # Calculate correlation matrix
    corr_matrix = df.corr()

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdYlGn',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 12},
        colorbar=dict(title="Correlation")
    ))

    fig.update_layout(
        title="Price Correlation Heatmap",
        template='plotly_white',
        height=500,
        xaxis={'side': 'bottom'}
    )

    return fig


def export_to_csv(data, filename="crypto_data.csv"):
    """Export recent data to CSV format."""
    df = pd.DataFrame([
        {
            "Date": d.date,
            "Open": d.open,
            "High": d.high,
            "Low": d.low,
            "Close": d.close,
            "Volume": d.volume
        }
        for d in data.recent_data
    ])

    return df.to_csv(index=False)


def main():
    """Main Streamlit application with enhanced features."""

    # Sidebar configuration
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Configuration")

    # Title
    st.title("📈 Cryptocurrency Data Dashboard")
    st.caption("Enhanced with candlestick charts, comparison views, and advanced analytics")
    st.markdown("---")

    # Popular cryptocurrencies
    crypto_options = {
        "Bitcoin": "BTC",
        "Ethereum": "ETH",
        "Litecoin": "LTC",
        "Ripple": "XRP",
        "Bitcoin Cash": "BCH",
        "Cardano": "ADA",
        "Polkadot": "DOT",
        "Chainlink": "LINK"
    }

    # Market currency (fixed to USD - all data in database is USD)
    selected_market = "USD"

    # DATA MODE TOGGLE
    st.sidebar.subheader("🎯 Data Source")
    data_mode = st.sidebar.radio(
        "Choose data source:",
        options=["Live API", "Historical DB"],
        index=0,
        help="Live API: Fetch fresh data from AlphaVantage (limited to ~10 days)\n\n"
             "Historical DB: Query stored data from TimescaleDB (supports custom date ranges)"
    )

    # DATE RANGE SELECTOR (only show for Historical DB mode)
    start_date = None
    end_date = None

    if data_mode == "Historical DB":
        st.sidebar.markdown("#### 📅 Date Range")

        date_preset = st.sidebar.selectbox(
            "Quick Select:",
            options=["Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 60 Days", "Custom Range"],
            index=0
        )

        end_date = datetime.now()

        if date_preset == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif date_preset == "Last 14 Days":
            start_date = end_date - timedelta(days=14)
        elif date_preset == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif date_preset == "Last 60 Days":
            start_date = end_date - timedelta(days=60)
        elif date_preset == "Custom Range":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=30),
                    max_value=datetime.now()
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now(),
                    max_value=datetime.now()
                )

            # Convert date to datetime
            if isinstance(start_date, datetime):
                pass
            else:
                start_date = datetime.combine(start_date, datetime.min.time())

            if isinstance(end_date, datetime):
                pass
            else:
                end_date = datetime.combine(end_date, datetime.max.time())

        st.sidebar.info(
            f"📊 Showing data from:\n"
            f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n\n"
            f"({(end_date - start_date).days} days)"
        )

    st.sidebar.markdown("---")

    # Info box
    if data_mode == "Live API":
        st.sidebar.info(
            "🌐 **Live API Mode**\n\n"
            "Fetching fresh data from AlphaVantage API\n\n"
            "⚠️ Limited to ~10 days\n"
            "⚠️ Rate limits: 5 requests/min\n\n"
            "💡 Switch to Historical DB for longer ranges!"
        )
    else:
        st.sidebar.success(
            "💾 **Historical DB Mode**\n\n"
            "Querying TimescaleDB (fast!)\n\n"
            "✓ Custom date ranges\n"
            "✓ No rate limits\n"
            "✓ Compressed storage\n\n"
            "💡 Run seed script to populate data!"
        )

    # Fetch button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔀 Comparison", "📈 Statistics"])

    # TAB 1: OVERVIEW - Single Cryptocurrency Detailed View
    with tab1:
        selected_crypto_name = st.selectbox(
            "Select Cryptocurrency",
            options=list(crypto_options.keys()),
            index=0,
            key="overview_crypto"
        )

        selected_symbol = crypto_options[selected_crypto_name]

        # Fetch data based on selected mode
        if data_mode == "Live API":
            # Fetch from API
            with st.spinner(f"🌐 Fetching {selected_crypto_name} from API..."):
                data, error = fetch_crypto_data(selected_symbol, selected_market)

            if error:
                st.error(f"❌ {error}")
                st.info("💡 Tip: Check your API key in the .env file or try again later if you've hit rate limits.")
                return

            if not data:
                st.error("❌ No data available")
                return

            # Use API data (existing format)
            df = pd.DataFrame([
                {
                    'date': d.date,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                }
                for d in data.recent_data
            ]).iloc[::-1]  # Reverse for chronological order

        else:  # Historical DB mode
            # Fetch from database
            with st.spinner(f"💾 Querying {selected_crypto_name} from database..."):
                df, error = fetch_crypto_data_from_db(
                    selected_symbol, selected_market, start_date, end_date
                )

            if error:
                st.error(f"❌ {error}")
                if "No data found" in error:
                    st.info(
                        "💡 **Tip:** Run the seed script to populate your database:\n\n"
                        "```bash\n"
                        "source venv/bin/activate\n"
                        "DATABASE_URL=\"postgresql://crypto_user:admincrypto321@localhost:5434/crypto_db\" python scripts/seed_database.py\n"
                        "```"
                    )
                return

            if df is None or df.empty:
                st.error("❌ No data available for the selected date range")
                return

        # Display metadata header
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.header(f"{selected_crypto_name} ({selected_symbol})")
            st.caption(f"Market: {selected_market}")

        with col2:
            if data_mode == "Live API":
                st.metric("Last Updated", data.metadata.last_refreshed)
            else:
                st.metric("Date Range", f"{len(df)} days")

        with col3:
            if data_mode == "Live API":
                st.metric("Time Zone", data.metadata.time_zone)
            else:
                st.metric("Data Source", "TimescaleDB")

        st.markdown("---")

        # Enhanced Key metrics with volatility
        st.subheader("📊 Key Metrics")

        # Calculate metrics from DataFrame
        latest_price = df['close'].iloc[-1]
        latest_volume = df['volume'].iloc[-1]

        # Daily change (compare last two days if available)
        if len(df) >= 2:
            previous_close = df['close'].iloc[-2]
            daily_change = latest_price - previous_close
            daily_change_pct = (daily_change / previous_close) * 100
        else:
            daily_change = None
            daily_change_pct = None

        # Volatility calculation
        if len(df) >= 2:
            df_temp = df.copy()
            df_temp['returns'] = df_temp['close'].pct_change()
            volatility = df_temp['returns'].std() * 100
        else:
            volatility = None

        # Price range
        price_high = df['high'].max()
        price_low = df['low'].min()
        price_range = price_high - price_low

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Latest Price",
                format_number(latest_price, f"{selected_market} "),
                delta=format_number(daily_change) if daily_change else None
            )

        with col2:
            if daily_change_pct is not None:
                delta_color = "normal" if daily_change_pct >= 0 else "inverse"
                st.metric(
                    "Daily Change",
                    f"{daily_change_pct:.2f}%",
                    delta=f"{abs(daily_change_pct):.2f}%",
                    delta_color=delta_color
                )
            else:
                st.metric("Daily Change", "N/A")

        with col3:
            st.metric(
                "Trading Volume",
                format_number(latest_volume)
            )

        with col4:
            if volatility:
                volatility_label = "High" if volatility > 5 else "Moderate" if volatility > 2 else "Low"
                st.metric(
                    "Volatility",
                    f"{volatility:.2f}%",
                    delta=volatility_label,
                    delta_color="off"
                )
            else:
                st.metric("Volatility", "N/A")

        with col5:
            st.metric(
                f"{len(df)}-Day Range",
                format_number(price_range, f"{selected_market} ")
            )

        st.markdown("---")

        # Candlestick chart with volume
        st.subheader("📈 Price & Volume Analysis")
        candlestick_chart = create_candlestick_chart_from_df(df, selected_market)
        st.plotly_chart(candlestick_chart, use_container_width=True)

        st.markdown("---")

        # Statistics section
        st.subheader("📉 Statistical Analysis")

        # Calculate statistics from DataFrame
        avg_price = df['close'].mean()
        high_price = df['high'].max()
        low_price = df['low'].min()
        avg_volume = df['volume'].mean()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"#### Price Statistics ({len(df)} Days)")
            stats_df = pd.DataFrame({
                "Metric": ["Average Price", "Highest Price", "Lowest Price"],
                "Value": [
                    format_number(avg_price, f"{selected_market} "),
                    format_number(high_price, f"{selected_market} "),
                    format_number(low_price, f"{selected_market} ")
                ]
            })
            st.dataframe(stats_df, hide_index=True, use_container_width=True)

        with col2:
            st.markdown(f"#### Volume Statistics ({len(df)} Days)")
            volume_stats = pd.DataFrame({
                "Metric": ["Average Volume", "Max Volume", "Min Volume"],
                "Value": [
                    format_number(avg_volume),
                    format_number(df['volume'].max()),
                    format_number(df['volume'].min())
                ]
            })
            st.dataframe(volume_stats, hide_index=True, use_container_width=True)

        # Export data button
        st.markdown("---")
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv_data,
            file_name=f"{selected_symbol}_{selected_market}_data.csv",
            mime="text/csv",
            use_container_width=True
        )

    # TAB 2: COMPARISON - Multi-Crypto Comparison
    with tab2:
        st.subheader("🔀 Multi-Cryptocurrency Comparison")
        st.caption(f"Compare performance across multiple cryptocurrencies ({data_mode})")

        # Multi-select for cryptocurrencies
        selected_cryptos = st.multiselect(
            "Select Cryptocurrencies to Compare (2-5)",
            options=list(crypto_options.keys()),
            default=["Bitcoin", "Ethereum", "Cardano"],
            max_selections=5
        )

        if len(selected_cryptos) < 2:
            st.warning("⚠️ Please select at least 2 cryptocurrencies to compare.")
        else:
            # Fetch data for all selected cryptos based on mode
            crypto_data_dict = {}

            if data_mode == "Live API":
                # Fetch from API (original logic)
                with st.spinner("🌐 Loading comparison data from API..."):
                    progress_bar = st.progress(0)
                    for idx, crypto_name in enumerate(selected_cryptos):
                        symbol = crypto_options[crypto_name]
                        data, error = fetch_crypto_data(symbol, selected_market)

                        # Convert API data to DataFrame format for consistency
                        if data and not error:
                            df_temp = pd.DataFrame([
                                {
                                    'date': d.date,
                                    'close': d.close,
                                    'volume': d.volume
                                }
                                for d in data.recent_data
                            ]).iloc[::-1]
                            crypto_data_dict[crypto_name] = df_temp
                        else:
                            crypto_data_dict[crypto_name] = None

                        progress_bar.progress((idx + 1) / len(selected_cryptos))

            else:  # Historical DB mode
                with st.spinner("💾 Loading comparison data from database..."):
                    progress_bar = st.progress(0)
                    for idx, crypto_name in enumerate(selected_cryptos):
                        symbol = crypto_options[crypto_name]
                        df_temp, error = fetch_crypto_data_from_db(
                            symbol, selected_market, start_date, end_date
                        )
                        crypto_data_dict[crypto_name] = df_temp if not error else None
                        progress_bar.progress((idx + 1) / len(selected_cryptos))

            # Filter out failed fetches
            valid_data = {k: v for k, v in crypto_data_dict.items() if v is not None and not v.empty}

            if len(valid_data) < 2:
                st.error("❌ Not enough data available for comparison.")
                if data_mode == "Historical DB":
                    st.info("💡 Make sure you've run the seed script to populate data for all cryptocurrencies.")
            else:
                # Display comparison metrics
                st.markdown("#### Price Comparison")
                cols = st.columns(len(valid_data))

                for idx, (crypto_name, df_temp) in enumerate(valid_data.items()):
                    with cols[idx]:
                        latest_price = df_temp['close'].iloc[-1]

                        # Calculate daily change if data available
                        if len(df_temp) >= 2:
                            previous_close = df_temp['close'].iloc[-2]
                            change_pct = ((latest_price - previous_close) / previous_close) * 100
                        else:
                            change_pct = None

                        st.metric(
                            crypto_name,
                            format_number(latest_price, f"{selected_market} "),
                            delta=f"{change_pct:.2f}%" if change_pct is not None else None
                        )

                st.markdown("---")

                # Comparison chart - percentage change from first day
                st.markdown("#### Performance Comparison")
                fig = go.Figure()

                for crypto_name, df_temp in valid_data.items():
                    if len(df_temp) > 0:
                        first_price = df_temp['close'].iloc[0]
                        df_temp['pct_change'] = ((df_temp['close'] - first_price) / first_price) * 100

                        fig.add_trace(go.Scatter(
                            x=df_temp['date'],
                            y=df_temp['pct_change'],
                            mode='lines+markers',
                            name=crypto_name,
                            line=dict(width=2),
                            marker=dict(size=5)
                        ))

                fig.update_layout(
                    title="Multi-Crypto Comparison (Percentage Change from Start)",
                    xaxis_title="Date",
                    yaxis_title="Change (%)",
                    hovermode='x unified',
                    template='plotly_white',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")

                # Correlation heatmap
                st.markdown("#### Price Correlation Matrix")
                st.caption("Shows how cryptocurrencies move together (1 = perfect correlation, -1 = inverse correlation)")

                # Prepare data for correlation
                price_data = {}
                for crypto_name, df_temp in valid_data.items():
                    price_data[crypto_name] = df_temp['close'].values

                if len(price_data) >= 2:
                    # Create DataFrame and calculate correlation
                    corr_df = pd.DataFrame(price_data)
                    corr_matrix = corr_df.corr()

                    # Create heatmap
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.index,
                        colorscale='RdYlGn',
                        zmid=0,
                        text=corr_matrix.values,
                        texttemplate='%{text:.2f}',
                        textfont={"size": 12},
                        colorbar=dict(title="Correlation")
                    ))

                    fig.update_layout(
                        title="Price Correlation Heatmap",
                        template='plotly_white',
                        height=500,
                        xaxis={'side': 'bottom'}
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Not enough data to generate correlation heatmap.")

    # TAB 3: STATISTICS - Advanced Analytics
    with tab3:
        st.subheader("📈 Advanced Statistics & Analytics")
        st.caption(f"Data Source: {data_mode}")

        selected_crypto_name_stats = st.selectbox(
            "Select Cryptocurrency",
            options=list(crypto_options.keys()),
            index=0,
            key="stats_crypto"
        )

        selected_symbol_stats = crypto_options[selected_crypto_name_stats]

        # Fetch data based on mode
        if data_mode == "Live API":
            with st.spinner(f"🌐 Loading {selected_crypto_name_stats} from API..."):
                data, error = fetch_crypto_data(selected_symbol_stats, selected_market)

            if error or not data:
                st.error("❌ Unable to load data for statistics.")
            else:
                # Create detailed statistics from API data
                df = pd.DataFrame([
                    {
                        'Date': d.date,
                        'Open': d.open,
                        'High': d.high,
                        'Low': d.low,
                        'Close': d.close,
                        'Volume': d.volume
                    }
                    for d in reversed(data.recent_data)
                ])
        else:  # Historical DB mode
            with st.spinner(f"💾 Loading {selected_crypto_name_stats} from database..."):
                df, error = fetch_crypto_data_from_db(
                    selected_symbol_stats, selected_market, start_date, end_date
                )

            if error or df is None or df.empty:
                st.error("❌ Unable to load data for statistics.")
                if "No data found" in str(error):
                    st.info("💡 Run the seed script to populate your database.")
                df = None

        if df is not None and not df.empty:
            # Rename columns for display
            df_display = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            # Calculate additional metrics
            df_display['Daily_Change'] = df_display['Close'].diff()
            df_display['Daily_Change_Pct'] = df_display['Close'].pct_change() * 100
            df_display['Range'] = df_display['High'] - df_display['Low']
            df_display['Average_Price'] = (df_display['High'] + df_display['Low'] + df_display['Close']) / 3

            # Display comprehensive statistics
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Price Statistics")
                price_stats = pd.DataFrame({
                    "Metric": [
                        "Current Price",
                        "Mean Price",
                        "Median Price",
                        "Std Deviation",
                        "Min Price",
                        "Max Price"
                    ],
                    "Value": [
                        format_number(df_display['Close'].iloc[-1], f"{selected_market} "),
                        format_number(df_display['Close'].mean(), f"{selected_market} "),
                        format_number(df_display['Close'].median(), f"{selected_market} "),
                        format_number(df_display['Close'].std(), f"{selected_market} "),
                        format_number(df_display['Close'].min(), f"{selected_market} "),
                        format_number(df_display['Close'].max(), f"{selected_market} ")
                    ]
                })
                st.dataframe(price_stats, hide_index=True, use_container_width=True)

            with col2:
                st.markdown("#### Volume Statistics")
                volume_stats = pd.DataFrame({
                    "Metric": [
                        "Latest Volume",
                        "Mean Volume",
                        "Median Volume",
                        "Std Deviation",
                        "Min Volume",
                        "Max Volume"
                    ],
                    "Value": [
                        format_number(df_display['Volume'].iloc[-1]),
                        format_number(df_display['Volume'].mean()),
                        format_number(df_display['Volume'].median()),
                        format_number(df_display['Volume'].std()),
                        format_number(df_display['Volume'].min()),
                        format_number(df_display['Volume'].max())
                    ]
                })
                st.dataframe(volume_stats, hide_index=True, use_container_width=True)

            st.markdown("---")

            # Detailed data table
            st.markdown("#### Recent OHLCV Data")
            st.dataframe(
                df_display[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Daily_Change_Pct']].style.format({
                    'Open': '{:.2f}',
                    'High': '{:.2f}',
                    'Low': '{:.2f}',
                    'Close': '{:.2f}',
                    'Volume': '{:.0f}',
                    'Daily_Change_Pct': '{:.2f}%'
                }),
                hide_index=True,
                use_container_width=True
            )

    # Footer
    st.markdown("---")
    if data_mode == "Live API":
        st.caption("📊 Data: AlphaVantage API | Dashboard: Streamlit | Database: TimescaleDB | 🌐 Live Mode")
    else:
        st.caption("📊 Data: AlphaVantage API | Dashboard: Streamlit | Database: TimescaleDB | 💾 Historical Mode")


if __name__ == "__main__":
    main()
