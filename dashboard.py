# dashboard.py
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import json
from backtesting import run_backtest
from ga_optimization import run_optimization
from data import get_historical_data

# Create Dash app with multi-page structure; expose the Flask server.
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Default strategy parameters used for backtesting.
DEFAULT_PARAMS = {
    "longTermFastLen": 50,
    "longTermSlowLen": 200,
    "shortTermFastLen": 10,
    "shortTermSlowLen": 20,
    "fixedStopLossPct": 1,        # e.g. 1% 
    "fixedTakeProfitPct": 2,      # e.g. 2%
    "fixedTrailingPct": 1.5,      # e.g. 1.5%
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
# PAGE 1: Main Dashboard
# ------------------------
def render_dashboard():
    return html.Div(
        style={'backgroundColor': '#222', 'color': '#FFC107', 'padding': '20px', 'fontFamily': 'Arial'},
        children=[
            html.H1("Crypto Backtesting Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
            # Control Panel
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

            # Chart
            dcc.Loading(
                id="loading-chart",
                type="default",
                children=[dcc.Graph(id='price-chart')]
            ),
            html.Br(),
            # Link to go to /results page.
            html.Div([
                dcc.Link("View Backtest Results", href="/results",
                         style={'fontSize': '18px', 'padding': '10px', 'color': '#FFC107'})
            ], style={'textAlign': 'center'}),

            # Hidden stores to hold data for results page.
            dcc.Store(id='params-used-store'),    # Store the actual parameters used
            dcc.Store(id='metrics-store'),        # Store the final portfolio metrics
            dcc.Store(id='trade-log-store'),      # Store the entire trade log
        ]
    )

# ------------------------
# PAGE 2: Results Page
# ------------------------
def render_results():
    return html.Div(
        style={'backgroundColor': '#222', 'color': '#FFC107', 'padding': '20px', 'fontFamily': 'Arial'},
        children=[
            html.H1("Backtest Results", style={'textAlign': 'center', 'marginBottom': '30px'}),
            html.Div(id='results-container', style={'marginBottom': '30px'}),
            # Download CSV
            html.Div([
                html.Button("Download Trade Log CSV", id="download-btn", n_clicks=0,
                            style={'padding': '10px 20px', 'fontSize': '16px', 'marginTop': '20px'}),
                dcc.Download(id="download-trade-log")
            ], style={'textAlign': 'center'}),
            html.Br(),
            # Link to go back
            html.Div([
                dcc.Link("Back to Dashboard", href="/",
                         style={'fontSize': '18px', 'padding': '10px', 'color': '#FFC107'})
            ], style={'textAlign': 'center'})
        ]
    )

# ------------------------
# Top-Level Layout with Routing
# ------------------------
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Routing callback
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/results':
        return render_results()
    else:
        return render_dashboard()

# ------------------------
# MAIN CALLBACK: RUN BACKTEST OR OPT, UPDATE STORES & CHART
# ------------------------
@app.callback(
    [Output("params-used-store", "data"),
     Output("metrics-store", "data"),
     Output("trade-log-store", "data"),
     Output("price-chart", "figure")],
    [Input("run-backtest", "n_clicks"),
     Input("run-optimization", "n_clicks")],
    [State("symbol", "value"),
     State("timeframe", "value")]
)
def update_backtest_stores(n_backtest, n_optimization, symbol, timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return None, None, None, go.Figure()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    used_params = None
    metrics_data = None
    trade_log_data = None
    fig = go.Figure()

    if button_id == "run-backtest":
        # 1) We store the actual parameters used (for debugging)
        used_params = DEFAULT_PARAMS.copy()
        used_params["Symbol"] = symbol
        used_params["Timeframe"] = timeframe
        
        # 2) Run the backtest
        init_val, final_val, trade_log, cerebro = run_backtest(
            symbol=symbol, timeframe=timeframe, start_str='1 month ago UTC',
            strategy_params=DEFAULT_PARAMS
        )
        net_profit = final_val - init_val
        
        metrics_data = {
            "Initial Value": init_val,
            "Final Value": final_val,
            "Net Profit": net_profit,
            "Number of Trades": len(trade_log)
        }
        # Store the trade log
        trade_log_data = trade_log if trade_log else []

        # Build chart
        df = get_historical_data(symbol=symbol, interval=timeframe, start_str='1 month ago UTC')
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        fig.update_layout(template='plotly_dark', title=f"{symbol} Price Chart ({timeframe})")

    elif button_id == "run-optimization":
        used_params = {"Mode": "Optimization"}  # or store the best params if you want
        best_val, best_params = run_optimization(symbol=symbol, timeframe=timeframe)
        metrics_data = {
            "Best Portfolio Value": best_val,
            "Best Strategy Params": best_params
        }
        # We won't store a trade log here (since optimization won't produce a single trade log).
        trade_log_data = []

    return used_params, metrics_data, trade_log_data, fig

# ------------------------
# RESULTS PAGE CALLBACK
# ------------------------
@app.callback(
    Output("results-container", "children"),
    [Input("params-used-store", "data"),
     Input("metrics-store", "data"),
     Input("trade-log-store", "data")],
)
def display_backtest_results(used_params, metrics_data, trade_log_data):
    # If there's no data, show a fallback.
    if not used_params and not metrics_data and not trade_log_data:
        return html.Div([
            html.P("No backtest or optimization data is available.")
        ], style={'textAlign': 'center', 'padding': '10px', 'border': '1px solid #FFC107'})

    # Display parameters used in JSON format
    params_display = html.Div([
        html.H3("Parameters Used:"),
        html.Pre(json.dumps(used_params, indent=2))
    ], style={'marginBottom': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})

    # Display metrics
    metrics_display = html.Div()
    if metrics_data:
        if "Number of Trades" in metrics_data:
            # Means we did a backtest
            metrics_display = html.Div([
                html.H3("Backtest Metrics:"),
                html.P(f"Initial Value: {metrics_data.get('Initial Value', 0):.2f}"),
                html.P(f"Final Value: {metrics_data.get('Final Value', 0):.2f}"),
                html.P(f"Net Profit: {metrics_data.get('Net Profit', 0):.2f}"),
                html.P(f"Number of Trades: {metrics_data.get('Number of Trades', 0)}")
            ], style={'marginBottom': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})
        elif "Best Strategy Params" in metrics_data:
            # Means we did an optimization
            bval = metrics_data.get("Best Portfolio Value", 0)
            bparams = metrics_data.get("Best Strategy Params", {})
            metrics_display = html.Div([
                html.H3("Optimization Metrics:"),
                html.P(f"Best Portfolio Value: {bval:.2f}"),
                html.Pre(json.dumps(bparams, indent=2))
            ], style={'marginBottom': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})

    # Display trade log
    trades_display = html.Div()
    if trade_log_data and len(trade_log_data) > 0:
        trades_display = html.Div([
            html.H3("Complete Trade Log:"),
            dash_table.DataTable(
                columns=[{"name": col, "id": col} for col in trade_log_data[0].keys()],
                data=trade_log_data,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'backgroundColor': '#222', 'color': '#FFC107'},
                page_size=10
            )
        ], style={'marginBottom': '20px', 'padding': '10px', 'border': '1px solid #FFC107'})
    else:
        trades_display = html.Div([
            html.P("No trades were executed or no trade log is available.")
        ], style={'textAlign': 'center', 'padding': '10px', 'border': '1px solid #FFC107'})

    return html.Div([params_display, metrics_display, trades_display])

# ------------------------
# CSV Download Callback
# ------------------------
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
