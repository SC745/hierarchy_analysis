import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, dcc, ALL, ctx
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import functions

from flask import session
from flask_login import logout_user, current_user
import json
import pages.project


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


def CreateProjectTable(user_id):
    columns = ["Название", "Статус", "Роль в проекте", "Ссылка"]
    project_data = functions.GetUserProjects(user_id)

    head = dmc.TableThead(dmc.TableTr([dmc.TableTh(column) for column in columns]))
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in project_data])
    table = dmc.Table([head, body], id = "project_table", highlightOnHover=True, withTableBorder=True, fz = 16)

    return table

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "projects"}, pathname = "/login")
    else:
        user_data = current_user.userdata

        layout = dmc.AppShell(
            children = [
                dmc.AppShellHeader(
                    children = [
                            dmc.Box(
                                children = [
                                    dcc.Location(id = {"type": "redirect", "index": "projects"}, pathname = "/projects"),
                                    dmc.Menu(
                                        children = [
                                            dmc.MenuTarget(dmc.Text(functions.GetShortUsername(user_data["name"]))),
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
                                dmc.Text("Проекты", fz = 24, fw = 500),
                                CreateProjectTable(current_user.userdata["id"]),
                            ],
                            gap = "xs"
                        )
                    ],
                    mt = "sm",
                    px = "md",
                ),
            ],
            header={"height": "30px"},
        )
    
    layout = dmc.MantineProvider(layout)
    return layout

@dash.callback(
    Output({"type": "redirect", "index": "projects"}, "pathname", allow_duplicate = True),
    Input({"type": "project_button", "index": ALL}, "n_clicks"),
    prevent_initial_call = True
)
def ProjectChoice(clickdata):

    project_data = functions.GetUserProjectById(current_user.userdata["id"], ctx.triggered_id["index"])

    elements = functions.GetHierarchyPreset(*functions.GetProjectDfs(project_data["id"], None))

    state = {}
    state["manually_deleted"] = {}
    state["cascade_deleted"] = {}
    state["added"] = {}
    state["selected"] = None

    steps = {}
    steps["history"] = []
    steps["canceled"] = []

    element_data = {}
    element_data["elements"] = elements
    element_data["state"] = state
    element_data["steps"] = steps

    session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)
    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)


    return "/project"


