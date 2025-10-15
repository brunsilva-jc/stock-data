"""
Streamlit Dashboard for Cryptocurrency Data Visualization
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import asyncio
from datetime import datetime
from app.services.alphavantage import alphavantage_service
from app.models.currency import CurrencyDataProcessor


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
    }
    .negative {
        color: #ff0000;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes to respect API rate limits
def fetch_crypto_data(symbol: str, market: str):
    """
    Fetch cryptocurrency data with caching.

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


def format_number(num, prefix="", suffix=""):
    """Format numbers with commas and optional prefix/suffix."""
    if num is None:
        return "N/A"
    return f"{prefix}{num:,.2f}{suffix}"


def create_price_chart(recent_data):
    """Create an interactive line chart for price trends."""
    df = pd.DataFrame([
        {
            'date': data.date,
            'close': data.close,
            'high': data.high,
            'low': data.low,
            'open': data.open
        }
        for data in recent_data
    ])

    # Reverse order for chronological display
    df = df.iloc[::-1]

    fig = go.Figure()

    # Add close price line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines+markers',
        name='Close Price',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6)
    ))

    # Add high/low range
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['high'],
        mode='lines',
        name='High',
        line=dict(color='rgba(0,255,0,0.3)', width=1, dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['low'],
        mode='lines',
        name='Low',
        line=dict(color='rgba(255,0,0,0.3)', width=1, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(200,200,200,0.2)'
    ))

    fig.update_layout(
        title="Price Trend (Last 10 Days)",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def create_volume_chart(recent_data):
    """Create a bar chart for trading volume."""
    df = pd.DataFrame([
        {'date': data.date, 'volume': data.volume}
        for data in recent_data
    ])

    # Reverse order for chronological display
    df = df.iloc[::-1]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color='rgba(55, 128, 191, 0.7)',
        marker_line_color='rgba(55, 128, 191, 1.0)',
        marker_line_width=1.5
    ))

    fig.update_layout(
        title="Trading Volume (Last 10 Days)",
        xaxis_title="Date",
        yaxis_title="Volume",
        hovermode='x',
        template='plotly_white',
        height=300
    )

    return fig


def main():
    """Main Streamlit application."""

    # Sidebar logo and configuration
    #st.sidebar.image("assets/crypto.png", width=100)
    st.sidebar.markdown("---")
    st.sidebar.header("Configuration")

    # Title
    st.title("📈 Cryptocurrency Data Dashboard")
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

    selected_crypto_name = st.sidebar.selectbox(
        "Select Cryptocurrency",
        options=list(crypto_options.keys()),
        index=0
    )

    selected_symbol = crypto_options[selected_crypto_name]

    # Market selection
    market_options = ["USD", "EUR", "GBP", "JPY", "CNY"]
    selected_market = st.sidebar.selectbox(
        "Select Market Currency",
        options=market_options,
        index=0
    )

    # Info box
    st.sidebar.info(
        "📊 Data is cached for 5 minutes to respect API rate limits.\n\n"
    )

    # Fetch button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Fetch and display data
    with st.spinner(f"Fetching {selected_crypto_name} ({selected_symbol}) data..."):
        data, error = fetch_crypto_data(selected_symbol, selected_market)

    if error:
        st.error(f"❌ {error}")
        st.info("💡 Tip: Check your API key in the .env file or try again later if you've hit rate limits.")
        return

    if not data:
        st.error("❌ No data available")
        return

    # Display metadata header
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.header(f"{data.metadata.digital_currency_name} ({data.metadata.digital_currency_code})")
        st.caption(f"Market: {data.metadata.market_name} ({data.metadata.market_code})")

    with col2:
        st.metric("Last Updated", data.metadata.last_refreshed)

    with col3:
        st.metric("Time Zone", data.metadata.time_zone)

    st.markdown("---")

    # Key metrics in cards
    st.subheader("📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Latest Price",
            format_number(data.metrics.latest_price, f"{selected_market} "),
            delta=format_number(data.metrics.daily_change) if data.metrics.daily_change else None
        )

    with col2:
        change_pct = data.metrics.daily_change_percent
        st.metric(
            "Daily Change",
            format_number(change_pct, suffix="%") if change_pct else "N/A",
            delta=f"{change_pct:.2f}%" if change_pct else None
        )

    with col3:
        st.metric(
            "Trading Volume",
            format_number(data.metrics.latest_volume)
        )

    with col4:
        st.metric(
            "Latest Date",
            data.metrics.latest_date
        )

    st.markdown("---")

    # Charts section
    st.subheader("📈 Price & Volume Analysis")

    # Price chart
    price_chart = create_price_chart(data.recent_data)
    st.plotly_chart(price_chart, use_container_width=True)

    # Volume chart
    volume_chart = create_volume_chart(data.recent_data)
    st.plotly_chart(volume_chart, use_container_width=True)

    st.markdown("---")

    # Statistics section
    st.subheader("📉 Statistical Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Weekly Statistics (7 Days)")
        weekly_stats = pd.DataFrame({
            "Metric": ["Average Price", "Highest Price", "Lowest Price"],
            "Value": [
                format_number(data.metrics.weekly_avg, f"{selected_market} "),
                format_number(data.metrics.weekly_high, f"{selected_market} "),
                format_number(data.metrics.weekly_low, f"{selected_market} ")
            ]
        })
        st.dataframe(weekly_stats, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("#### Monthly Statistics (30 Days)")
        monthly_stats = pd.DataFrame({
            "Metric": ["Average Price", "Highest Price", "Lowest Price"],
            "Value": [
                format_number(data.metrics.monthly_avg, f"{selected_market} "),
                format_number(data.metrics.monthly_high, f"{selected_market} "),
                format_number(data.metrics.monthly_low, f"{selected_market} ")
            ]
        })
        st.dataframe(monthly_stats, hide_index=True, use_container_width=True)

    st.markdown("---")

    # Recent data table
    #st.subheader("📋 Recent OHLCV Data (Last 10 Days)")

    # Create DataFrame from recent data
    # recent_df = pd.DataFrame([
    #     {
    #         "Date": data.date,
    #         "Open": format_number(data.open, f"{selected_market} "),
    #         "High": format_number(data.high, f"{selected_market} "),
    #         "Low": format_number(data.low, f"{selected_market} "),
    #         "Close": format_number(data.close, f"{selected_market} "),
    #         "Volume": format_number(data.volume)
    #     }
    #     for data in data.recent_data
    # ])

    # st.dataframe(recent_df, hide_index=True, use_container_width=True)

    # Footer
    st.markdown("---")
    st.caption("Data provided by AlphaVantage API | Dashboard built with Streamlit")


if __name__ == "__main__":
    main()
