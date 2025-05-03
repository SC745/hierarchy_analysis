import dash
from dash import _dash_renderer, ctx, ALL, dcc

from flask import session
from flask_login import current_user, logout_user


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__, path='/logout')

def layout():
    session.clear()
    logout_user()
    return dcc.Location(id = {"type": "unauthentificated", "index": "logout"}, pathname = "/")
