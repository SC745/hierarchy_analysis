import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, dcc, ALL, ctx
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import functions

from flask import session
from flask_login import current_user, logout_user
import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def layout():
    #Удаление ключей других страниц
    #page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)
    
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "projects"}, pathname = "/login")
    else:
        layout = dmc.AppShell(
            children = [
                dcc.Location(id = {"type": "redirect", "index": "projects"}, pathname = "/projects"),
                dcc.Store(id="project_data_store", storage_type='session', clear_data=True),
                dcc.Store(id="element_data_store", storage_type='session', clear_data=True),
                dcc.Store(id="comp_data_store", storage_type='session', clear_data=True),
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Menu(
                                    children = [
                                        dmc.MenuTarget(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                        dmc.MenuDropdown(
                                            children = [
                                                dmc.MenuItem(id = {"type": "logout_button", "index": "projects"}, leftSection = DashIconify(icon = "mingcute:exit-fill"), children = "Выйти", c = "red")
                                            ]
                                        )
                                    ],
                                    trigger="hover",
                                )
                            ],
                            px = "md",
                            style = {"display":"flex", "justify-content":"end"}
                        )
                    ]
                ),
                dmc.AppShellMain(
                    children = [
                        dmc.Stack(
                            children = [
                                dmc.Box(
                                    children = [
                                        dmc.Text("Проекты", fz = 24, fw = 500),
                                        dmc.Button("Создать", id = "create_project")
                                    ],
                                    style = {"display":"flex", "justify-content":"space-between"}
                                ),
                                dmc.Table(
                                    id = "project_table", 
                                    children = functions.CreateTableContent(["Название", "Этап", "Роль в проекте", "Ссылка"], functions.GetUserProjects(current_user.userdata["id"])),
                                    highlightOnHover = True,
                                    withTableBorder = True
                                )
                            ],
                            gap = "xs"
                        )
                    ],
                    mt = "sm",
                    px = "md"
                ),
            ],
            header={"height": "30px"},
        )
    
        layout = dmc.MantineProvider(layout)
        return layout


@dash.callback(
    Output({"type": "redirect", "index": "projects"}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": "projects"}, "n_clicks"),
    prevent_initial_call = True
)
def Logout(clickdata):
    if clickdata:
        session.clear()
        logout_user()
        return "/login"



@dash.callback(
    Output({"type": "redirect", "index": "projects"}, "pathname", allow_duplicate = True),
    Input({"type": "project_button", "index": ALL}, "n_clicks"),
    prevent_initial_call = True
)
def ProjectChoice(clickdata):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}
    if not trigger["value"]: raise PreventUpdate

    page_project = {}
    page_project["project_id"] = ctx.triggered_id["index"]
    session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)

    return "/project"


@dash.callback(
    Output("project_table", "children"),
    Input("create_project", "n_clicks"),
    State("project_table", "children"),
    prevent_initial_call = True
)
def CreateProject(clickdata, table_data):
    if functions.InsertNewProject(current_user.userdata["login"]):
        project_data = functions.GetUserProjects(current_user.userdata["id"])
        body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in project_data])
        table_data[1] = body
    return table_data
