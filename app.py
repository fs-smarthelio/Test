import dash
import numpy as np
from dash import html, callback, Input, Output, dash_table, dcc
from datetime import date, datetime
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from helper import function_to_call  # Ensure this function is defined in your 'helper.py'

# Initialize app with Bootstrap theme
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP])

cycle_of_data = {"5 Minutes": '5min', "Daily": 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y', 'Quarterly': 'Q'}

# Set app layout with Bootstrap components for better layout and responsiveness
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Actual/Expected Energies", className="text-center"), width=12)),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.Input(
            id="enter_plant_id",
            type="text",
            placeholder="Enter Plant ID",
            value=1,
            className="mb-3"), width={'size': 6, 'offset': 3}),
    ]),
    dbc.Row([
        dbc.Col(dcc.DatePickerRange(
            id='my-date-picker-range',
            min_date_allowed=date(2000, 1, 1),
            max_date_allowed=date(2050, 12, 31),
            initial_visible_month=datetime.now().date(),
            start_date=datetime.now().date() - pd.Timedelta(days=4),
            end_date=datetime.now().date() - pd.Timedelta(days=3),
            className="mb-3"), width={'size': 6, 'offset': 3}),
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id="cycle-of-data",
            options=[{'label': k, 'value': v} for k, v in cycle_of_data.items()],
            value='D',  # Default value
            className="mb-3"), width={'size': 6, 'offset': 3}),
    ]),
    dbc.Row([
        dbc.Col(
            dash_table.DataTable(id="output-container-date-picker-range", export_format="csv",
                                 # Enables CSV download
                                 export_headers="display",
                                 # Enable horizontal scrolling ,
                                 style_cell={
                                     'textAlign': 'left',
                                     'padding': '10px',
                                     'backgroundColor': '#f8f9fa',
                                 },
                                 style_table={
                                     'overflowX': 'auto',  # Enable horizontal scrolling
                                     'overflowY': 'auto',  # Enable vertical scrolling
                                     'height': '300px',  # Set the height of the table (adjust as needed)
                                 },
                                 style_header={
                                     'backgroundColor': '#007bff',
                                     'color': 'white',
                                     'fontWeight': 'bold',
                                     'textAlign': 'center',
                                 }, ), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='line-plot-container'), width=12)
    ]),
    html.Div(id='out-all-types'),
], fluid=True)


@callback(
    [Output('output-container-date-picker-range', 'data'),
     Output('line-plot-container', 'figure')],
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input("enter_plant_id", "value"),
     Input("cycle-of-data", "value")])
def update_output(start_date, end_date, vals, cycle_of_data):
    string_prefix = 'You have selected: '
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string

    if isinstance(vals, int):
        vals = str(vals)

    result = function_to_call(start_date=str(start_date), end_date=str(end_date),
                              plants_ids=[int(val) for val in vals.split(",")], cycle_of_data=cycle_of_data)
    result.dropna(inplace=True)
    result['Datetime'] = result.index

    result = result[[result.columns[-1]] + result.columns[:-1].tolist()]

    fig = go.Figure()

    for i in result.columns[1:]:
        fig.add_trace(go.Scatter(
            x=result.index,
            y=result[i].replace({0: np.nan}),
            mode="lines+markers",
            name=str(i),
            showlegend=True
        ))

    if len(string_prefix) == len('You have selected: '):
        return {}
    else:
        return result.to_dict('records'), fig


if __name__ == "__main__":
    app.run_server(debug=True)
