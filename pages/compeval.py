import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate

from flask import session
from flask_login import current_user, logout_user

import functions
import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    #page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)

    #Очистка данных
    #project_data = session.pop("project_data", None)
    #element_data = session.pop("element_data", None)
    #comp_data = session.pop("comp_data", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "compeval"}, pathname = "/login")
    elif not "page_compeval" in session:
        return dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/project")
    else:
        page_compeval = json.loads(session["page_compeval"])
        comp_data = functions.GetUserCompdataForSimpleGrid(page_compeval["current_node_id"], current_user.userdata["id"])
        
        if len(comp_data)==0:
            return dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/project")
        else:
            
            #session["comp_data"] = json.dumps(comp_data, cls = functions.NpEncoder)
            dmc_SimpleGrid = functions.MakeSimpleGrid(comp_data)

            layout = dmc.AppShell(
                children = [
                    dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/compeval"),
                    dcc.Store(id="project_data_store", storage_type='session', clear_data=True),
                    dcc.Store(id="element_data_store", storage_type='session', clear_data=True),
                    dcc.Store(id="comp_data_store", storage_type='session', data=comp_data),
                    #dcc.Interval(id={'type': 'load_interval', 'index': 'compeval'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                    dmc.AppShellHeader(
                        children = [
                            dmc.Box(
                                children = [
                                    dmc.Flex(
                                        children = [
                                            dmc.Menu(
                                                children = [
                                                    dmc.MenuTarget(dmc.Text("Проект")),
                                                    dmc.MenuDropdown(
                                                        children = [
                                                            dmc.MenuItem(id = {"type":"menu_navlink", "index":"/projects22"},
                                                                         children = dmc.NavLink(
                                                                            id = "compeval_to_project",
                                                                            label = "Вернуться к проекту",
                                                                            leftSection = DashIconify(icon = "mingcute:arrow-left-line"),
                                                                        ),
                                                            )
                                                        ]
                                                    )
                                                ],
                                                trigger="hover",
                                            ),
                                        ],
                                        gap = "md",
                                    ),
                                    dmc.Text("name"),
                                    dmc.Menu(
                                        children = [
                                            dmc.MenuTarget(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                            dmc.MenuDropdown(
                                                children = [
                                                    dmc.MenuItem(id = {"type": "logout_button", "index": "compeval"}, leftSection = DashIconify(icon = "mingcute:exit-fill"), children = "Выйти", c = "red")
                                                ]
                                            )
                                        ],
                                        trigger="hover",
                                    )
                                ],
                                px = "md",
                                style = {"display":"flex", "justify-content":"space-between"}
                            )
                        ]
                    ),
                    dmc.AppShellMain(children=[
                        dmc.Container(dmc_SimpleGrid, size='90%'),
                    ])
                ],
                header={"height": "30px"},
            )

            layout = dmc.MantineProvider(layout)
            return layout

'''@dash.callback(
    #Output("project_data_store", "data", allow_duplicate = True),
    #Output("element_data_store", "data", allow_duplicate = True),
    Output("comp_data_store", "data", allow_duplicate = True),
    Input(component_id={'type': 'load_interval', 'index': 'compeval'}, component_property="n_intervals"),
    prevent_initial_call = True
    )
def update_spanner(n_intervals:int):
    page_compeval = json.loads(session["page_compeval"])
    comp_data = functions.GetUserCompdata(page_compeval["current_node_id"], current_user.userdata["id"])
    #project_data = functions.GetProjectData(current_user.userdata["id"], page_compeval["project_id"])
    #element_data = functions.GetElementData(project_data, current_user.userdata["id"])
    return json.dumps(comp_data, cls = functions.NpEncoder) #json.dumps(project_data, cls = functions.NpEncoder), json.dumps(element_data, cls = functions.NpEncoder)
'''

#Навигация ----------------------------------------------------------------------------------------------------

@dash.callback(
    Output({"type": "redirect", "index": "compeval"}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": "compeval"}, "n_clicks"),
    prevent_initial_call = True
)
def Logout(clickdata):
    if clickdata:
        session.clear()
        logout_user()
        return "/login"


@dash.callback(
    Output({"type": "redirect", "index": "compeval"}, "pathname", allow_duplicate = True),
    Input("compeval_to_project", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProject(clickdata):
    if clickdata is None:
        raise PreventUpdate
    else:
        page_compeval = json.loads(session["page_compeval"])
        page_project = {}
        page_project["project_id"] = page_compeval["project_id"]
        session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)
    
        return "/project"
