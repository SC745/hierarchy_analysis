import dash
import dash_mantine_components as dmc
from dash import Dash, Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
import dash_cytoscape as cyto
import functions
import page_content


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__, path = "/login")

layout = dmc.Box(
    children = [
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
                            dmc.Box(id="redirect_trigger", display = "none")
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

@dash.callback(
    Output("redirect_trigger", "children"),
    Output("error_message", "display"),
    Input("login_button", "n_clicks"),
    State("login_input", "value"),
    State("password_input", "value"),
    prevent_initial_call = True
)
def Login(click, login, password):
    successful_login = functions.CheckUserCredentials(login, password)
    if successful_login: return dcc.Location(pathname="/project", id = "tmp"), "none"
    return "", "block"