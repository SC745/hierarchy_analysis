import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, dcc, html
import page_content

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__, path = "/login")


layout = page_content.login_layout
layout = dmc.MantineProvider(layout)

