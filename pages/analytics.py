import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto

from flask import session
from flask_login import current_user

import functions
import json

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    #page_analytics = session.pop("page_analytics", None)

    #Очистка данных
    project_data = session.pop("project_data", None)
    element_data = session.pop("element_data", None)
    comp_data = session.pop("comp_data", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "analytics"}, pathname = "/login")
    elif not "page_analytics" in session:
        return dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/project")
    else:
        page_analytics = json.loads(session["page_analytics"])
        project_data = functions.GetProjectData(current_user.userdata["id"], page_analytics["project_id"])
        if project_data["status"]["stage"] < 3:
            return dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/project"),
        
        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)

        layout = dmc.AppShell(
            children = [
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/analytics"),
                                dcc.Store(id = {"type": "init_store", "index": "analytics"}, storage_type = "memory"),
                                dcc.Store(id = "prev_action", storage_type = "memory", data = False),
                                dmc.Menu(
                                    children = [
                                        dmc.MenuTarget(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                        dmc.MenuDropdown(
                                            children = [
                                                dmc.MenuItem(id = {"type": "logout_button", "index": "analytics"}, leftSection = DashIconify(icon = "mingcute:exit-fill"), children = "Выйти", c = "red")
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
                dmc.AppShellNavbar(
                    children = [
                        dmc.Box(children = dmc.Text("Аналитика", fz = 24, fw = 500), p = "sm"),
                        dmc.Divider(),
                        dmc.Box(
                            children = [
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "dep_eval_result"},
                                    label = "Результат оценки связей",
                                    leftSection = DashIconify(icon = "mingcute:user-1-line"),
                                    active = True
                                ),
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "comp_eval_result"},
                                    label = "Результат сравнительной оценки",
                                    leftSection = DashIconify(icon = "mingcute:settings-3-line"),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "incons_coef"},
                                    label = "Коэффициент противоречивости",
                                    leftSection = DashIconify(icon = "mingcute:certificate-line"),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = "analytics_to_project",
                                    label = "Вернуться к проекту",
                                    leftSection = DashIconify(icon = "mingcute:arrow-left-line"),
                                ),
                            ],
                        ),
                        dmc.Divider(),
                        dmc.Tree(
                            id = "project_tree",
                            selectOnClick = True,
                            expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                            collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                            data = functions.GetProjectTreeData(project_data["id"], False),
                            p = "sm"
                        ),
                        dmc.Box(id = "test123123")
                    ]
                ),
                dmc.AppShellMain([
                    cyto.Cytoscape(
                        id = "analytics_graph",
                        layout = {"name": "preset"},
                        style = {
                            "width": "100%",
                            "height": "calc(50vh - 30px)",
                            "position": "relative"
                        },
                        stylesheet=[
                            #Group selectors
                            {
                                "selector": "node",
                                "style": {
                                    "shape": "rectangle",
                                    "content": "data(name)",
                                    "width": "data(width)",
                                    "height": "data(height)",
                                    "text-valign": "center",
                                    "background-color": "#ffffff",
                                    "border-width": "3px",
                                    "font-size": "14px",
                                    "text-wrap": "wrap",
                                    "text-max-width": "80px"
                                },
                            },
                            #Class selectors
                            {
                                "selector": ".bad",
                                'style': { #mantine red.6
                                    "border-color": "#fa5252",
                                    "line-color": "#fa5252"
                                }
                            },
                            {
                                "selector": ".deleted",
                                'style': { #mantine orange.6
                                    "border-color": "#fd7e14",
                                    "line-color": "#fd7e14"
                                }
                            },
                            {
                                "selector": ".good",
                                "style": { #mantine green.6
                                    "border-color": "#40c057",
                                    "line-color": "#40c057"
                                }
                            },
                            {
                                "selector": ".selected",
                                "style": { #mantine blue.6
                                    "border-color": "#228be6",
                                    "line-color": "#228be6"
                                }
                            },
                            {
                                "selector": ".default",
                                "style": {
                                    "border-color": "black",
                                    "line-color": "black"
                                }
                            },
                        ],
                        minZoom = 0.5,
                        maxZoom = 2,
                        autoungrabify = True,
                        autoRefreshLayout = True,
                        wheelSensitivity = 0.2,
                        elements = []
                    )
                ]),
            ],
            header={"height": "30px"},
            navbar={"width": "300px"},
        )
        layout = dmc.MantineProvider(layout)
        return layout
    

@dash.callback(
    Output("test123123", "children"),
    Input("project_tree", "selected"),
)
def TreeItemSelect(selected):
    return selected