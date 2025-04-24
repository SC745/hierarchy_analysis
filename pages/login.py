import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, dcc, html

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


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
                            dcc.Location(id = {"type": "redirect", "index": "login"}, pathname = "/login")
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

