import dash
import dash_mantine_components as dmc
import functions
from dash.exceptions import PreventUpdate
from dash import _dash_renderer, dcc, Output, Input, State
from flask_login import current_user, UserMixin, login_user
from flask import session


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)

    if current_user.is_authenticated:
        return  dcc.Location(id = {"type": "redirect", "index": "projects"}, pathname = "/projects")
    else:
        layout = dmc.Box(
            children = [
                dcc.Location(id = {"type": "redirect", "index": "login"}, pathname = "/login"),
                dcc.Store(id={'type': 'project_data_store', 'index': 'all'}, storage_type='session', clear_data=True),
                dcc.Store(id={'type': 'element_data_store', 'index': 'all'}, storage_type='session', clear_data=True),
                dcc.Store(id={'type': 'comp_data_store', 'index': 'all'}, storage_type='session', clear_data=True),
                dmc.Center(
                children=[
                    dmc.Card(
                        children = [
                            dmc.Stack(
                                children=[
                                    dmc.Text(children = "Вход", fz = 24, ta = "center", fw = "bold"),
                                    dmc.TextInput(id = "login_input", placeholder="Логин", w="100%", size = "lg"),
                                    dmc.PasswordInput(id = "password_input", placeholder="Пароль", w="100%", size = "lg"),
                                    dmc.Button(id = "login_button", children = "Войти", w="100%", size = "lg"),
                                    dmc.Text(id = "error_message", children ="Неверный логин или пароль!", ta = "center", c = "var(--mantine-color-red-6)", display = "none"),
                                ],
                            )
                        ],
                        bg = "var(--mantine-color-white)"
                    )
                ],
                style={"height": "100vh", "width": "100%"},
                )
            ],
            bg = "var(--mantine-color-dark-2)"
        )
        layout = dmc.MantineProvider(layout)
        return layout


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
        login_user(functions.User(input["login"]))
        output["redirect_trigger"] = "/projects"
        output["error_state"] = "none"
    else:
        output["redirect_trigger"] = "/login"
        output["error_state"] = "block"
        
    return output
