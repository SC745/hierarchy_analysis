import dash
from dash import _dash_renderer, ctx, ALL, dcc

from flask import session
from flask_login import current_user


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__, path='/')

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "home"}, pathname = "/login")
    else:
        return  dcc.Location(id = {"type": "redirect", "index": "home"}, pathname = "/projects")