import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate

from flask import session
from flask_login import current_user

import functions
import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "compeval"}, pathname = "/login")
    elif not "comp_eval" in session:
        return dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/project")
    else:
        comp_eval = json.loads(session["comp_eval"])

        layout = dmc.Box(
            children = [
                functions.MakeSimpleGrid(comp_eval["compdata"])
            ]
        )

        layout = dmc.MantineProvider(layout)
        return layout