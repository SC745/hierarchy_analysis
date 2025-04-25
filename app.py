import dash
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State, MATCH
import dash_mantine_components as dmc
from dash import _dash_renderer
import functions

from dash.exceptions import PreventUpdate
import os
from flask import Flask, request, redirect, session
from flask_login import login_user, LoginManager, UserMixin, logout_user, current_user


_dash_renderer._set_react_version("18.2.0")

server = Flask(__name__)



app = dash.Dash(
    server=server,
    url_base_pathname='/',
    suppress_callback_exceptions=False,
    title='Hierarchy analysis',
    use_pages=True,
    pages_folder='pages',
    external_stylesheets=dmc.styles.ALL
)


a = os.getenv("SECRET_KEY")
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.userdata = functions.GetUserData(username)

@login_manager.user_loader
def load_user(username):
    return User(username)


@dash.callback(
    output = {
        "redirect_trigger": Output({"type": "redirect", "index": "login"}, "pathname"),
        "error_state": Output("error_message", "display"),
    },
    inputs = {
        "input": {
            "clickdata": Input("login_button", "n_clicks"),
            "login": State("login_input", "value"),
            "password": State("password_input", "value")
        }
    },
    prevent_initial_call = True
)
def Login(input):
    if not input["clickdata"]: raise PreventUpdate
    successful_login = functions.CheckUserCredentials(input["login"], input["password"])

    output = {}
    if successful_login:
        login_user(User(input["login"]))
        output["redirect_trigger"] = "/projects"
        output["error_state"] = "none"
    else:
        output["redirect_trigger"] = "/login"
        output["error_state"] = "block"
        
    return output

@dash.callback(
    Output({"type": "redirect", "index": MATCH}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": MATCH}, "n_clicks"),
    prevent_initial_call = True
)
def Logout(clickdata):
    if clickdata:
        session.clear()
        logout_user()
        return "/login"


if __name__ == '__main__':
    server.run(debug=True,port=9662,use_reloader=True)