# dashboard.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import json
from backtesting import run_backtest
from ga_optimization import run_optimization
from data import get_historical_data

# Create the Dash app with multi-page support and expose the Flask server.
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Default strategy parameters used for backtesting.
DEFAULT_PARAMS = {
    "longTermFastLen": 50,
    "longTermSlowLen": 200,
    "shortTermFastLen": 10,
    "shortTermSlowLen": 20,
    "fixedStopLossPct": 1,      # 1%
    "fixedTakeProfitPct": 2,    # 2%
    "fixedTrailingPct": 1.5,    # 1.5%
    "useAdxFilter": False,
    "adxPeriod": 14,
    "adxThreshold": 20.0,
    "useVolumeFilter": False,
    "volumeMALen": 20,
    "useRSIFilter": False,
    "rsiPeriod": 14,
    "rsiLongThreshold": 50.0,
    "rsiShortThreshold": 50.0,
    "useAtrFilter": False,
    "atrFilterThreshold": 0.01,
    "enableHigherTFFilter": False,
    "enableSessionFilter": False,
}

# ------------------------
# Define page layouts.
# ------------------------

# Main Dashboard Page layout.
def render_dashboard():
    return html.Div(
        style={'backgroundColor': '#222', 'color': '#FFC107', 'padding': '20px', 'fontFamily': 'Arial'},
        children=[
            html.H1("Crypto Backtesting Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
            # Control Panel Section
            html.Div([
                html.Div([
                    html.Label("Symbol:", style={'marginRight': '10px'}),
                    dcc.Input(id='symbol', type='text', value='BTCUSDT', style={'width': '120px'})
                ], style={'display': 'inline-block', 'marginRight': '30px'}),
                html.Div([
                    html.Label("Timeframe:", style={'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='timeframe',
                        options=[
                            {'label': '1 Minute', 'value': '1m'},
                            {'label': '5 Minutes', 'value': '5m'},
                            {'label': '15 Minutes', 'value': '15m'},
                            {'label': '1 Hour', 'value': '1h'},
                            {'label': '1 Day', 'value': '1d'},
                            {'label': '1 Week', 'value': '1w'},
                        ],
                        value='5m',
                        style={'width': '150px'}
                    )
                ], style={'display': 'inline-block', 'marginRight': '30px'}),
                html.Div([
                    html.Button("Run Backtest", id="run-backtest", n_clicks=0,
                                style={'padding': '10px 20px', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Button("Run Optimization", id="run-optimization", n_clicks=0,
                                style={'padding': '10px 20px', 'fontSize': '16px'})
                ], style={'display': 'inline-block'})
            ], style={'textAlign': 'center', 'marginBottom': '40px'}),
            # Chart Section (top)
            dcc.Loading(
                id="loading-chart",
                type="default",
                children=[dcc.Graph(id='price-chart')]
            ),
            html.Br(),
            # Navigation Button
            html.Div([
                dcc.Link("View Backtest Results", href="/results",
                         style={'padding': '10px 20px', 'fontSize': '18px', 'color': '#FFC107'})
            ], style={'textAlign': 'center'}),
            # Hidden stores for metrics and trade log.
            dcc.Store(id='metrics-store'),
            dcc.Store(id='trade-log-store')
        ]
    )

# Backtest Results Page layout.
def render_results():
    return html.Div(
        style={'backgroundColor': '#222', 'color': '#FFC107', 'padding': '20px', 'fontFamily': 'Arial'},
        children=[
            html.H1("Backtest Results", style={'textAlign': 'center', 'marginBottom': '30px'}),
            html.Div(id='results-metrics', style={'marginBottom': '30px'}),
            html.Div(id='results-trade-log'),
            html.Br(),
            html.Div([
                html.Button("Download Trade Log CSV", id="download-btn", n_clicks=0,
                            style={'padding': '10px 20px', 'fontSize': '16px'}),
                dcc.Download(id="download-trade-log")
            ], style={'textAlign': 'center', 'marginTop': '20px'}),
            html.Br(),
            html.Div([
                dcc.Link("Back to Dashboard", href="/",
                         style={'padding': '10px 20px', 'fontSize': '18px', 'color': '#FFC107'})
            ], style={'textAlign': 'center'})
        ]
    )

# ------------------------
# Define the top-level layout with routing.
# ------------------------
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Routing callback.
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/results':
        return render_results()
    else:
        return render_dashboard()

# ------------------------
# Main callback: Run backtest and update stores.
# ------------------------
@app.callback(
    [Output("metrics-store", "data"),
     Output("trade-log-store", "data"),
     Output("price-chart", "figure")],
    [Input("run-backtest", "n_clicks"),
     Input("run-optimization", "n_clicks")],
    [State("symbol", "value"),
     State("timeframe", "value")]
)
def update_backtest(n_backtest, n_optimization, symbol, timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return None, None, go.Figure()
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "run-backtest":
        initial_value, final_value, trade_log, cerebro = run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        net_profit = final_value - initial_value
        metrics = {
            "Initial Portfolio Value": initial_value,
            "Final Portfolio Value": final_value,
            "Net Profit": net_profit,
            "Number of Trades": len(trade_log)
        }
        df = get_historical_data(symbol=symbol, interval=timeframe, start_str='1 month ago UTC')
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        fig.update_layout(template='plotly_dark', title=f"{symbol} Price Chart ({timeframe})")
        return metrics, trade_log, fig
    elif button_id == "run-optimization":
        best_value, best_params = run_optimization(symbol=symbol, timeframe=timeframe)
        metrics = {
            "Best Portfolio Value": best_value,
            "Best Strategy Parameters": best_params
        }
        # For optimization, we don't update the chart or trade log.
        return metrics, None, go.Figure()

# Callback for the backtest results page to display metrics and trade log.
@app.callback(
    [Output("results-metrics", "children"),
     Output("results-trade-log", "children")],
    [Input("metrics-store", "data"),
     Input("trade-log-store", "data")]
)
def update_results_page(metrics_data, trade_log_data):
    metrics_display = html.Div()
    trade_log_display = html.Div()
    if metrics_data:
        metrics_display = html.Div([
            html.P(f"Initial Portfolio Value: {metrics_data.get('Initial Portfolio Value', 0):.2f}"),
            html.P(f"Final Portfolio Value: {metrics_data.get('Final Portfolio Value', 0):.2f}"),
            html.P(f"Net Profit: {metrics_data.get('Net Profit', 0):.2f}"),
            html.P(f"Number of Trades: {metrics_data.get('Number of Trades', 0)}")
        ], style={'textAlign': 'center', 'padding': '10px', 'border': '1px solid #FFC107', 'marginBottom': '20px'})
    if trade_log_data and len(trade_log_data) > 0:
        trade_log_display = html.Div([
            dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in trade_log_data[0].keys()],
                data=trade_log_data,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'backgroundColor': '#222', 'color': '#FFC107'},
                page_size=10
            )
        ], style={'marginTop': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})
    else:
        trade_log_display = html.Div([
            html.P("No trades were executed during this backtest.")
        ], style={'textAlign': 'center', 'padding': '10px', 'border': '1px solid #FFC107'})
    return metrics_display, trade_log_display

# Callback for downloading the trade log as CSV.
@app.callback(
    Output("download-trade-log", "data"),
    Input("download-btn", "n_clicks"),
    State("trade-log-store", "data"),
    prevent_initial_call=True
)
def download_trade_log(n_clicks, trade_log_data):
    if not trade_log_data or len(trade_log_data) == 0:
        return None
    df = pd.DataFrame(trade_log_data)
    return dcc.send_data_frame(df.to_csv, "trade_log.csv", index=False)

if __name__ == "__main__":
    app.run_server(debug=True)
