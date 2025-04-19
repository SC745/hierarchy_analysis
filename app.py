import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from flask import Flask
from dash.dependencies import Input,Output,State
import dash_mantine_components as dmc
from dash import _dash_renderer


_dash_renderer._set_react_version("18.2.0")

server = Flask(__name__)

app = dash.Dash(
    server=server,
    url_base_pathname='/',
    suppress_callback_exceptions=False,
    assets_folder='assets',
    title='Hierarchy analysis',
    use_pages=True,
    pages_folder='pages',
    external_stylesheets=dmc.styles.ALL
)
                            
if __name__ == '__main__':
    server.run(debug=True,port=9662,use_reloader=True)