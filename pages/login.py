import dash
import dash_mantine_components as dmc
from dash import _dash_renderer, dcc
from flask_login import current_user
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

    #Очистка данных
    project_data = session.pop("project_data", None)
    element_data = session.pop("element_data", None)
    comp_data = session.pop("comp_data", None)

    if current_user.is_authenticated:
        return  dcc.Location(id = {"type": "redirect", "index": "projects"}, pathname = "/projects")
    else:
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
        return layout

