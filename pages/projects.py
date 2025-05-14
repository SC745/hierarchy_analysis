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


def GetTableProjects(user_id):
    head = dmc.TableThead(
                children=[
                    dmc.TableTr(
                        children=[
                            dmc.TableTh("Наименование"),
                            dmc.TableTh("Этап", w=350),
                            dmc.TableTh("Роль в проекте",w=250),
                            dmc.TableTh(children="Открыть", w=80),
                        ]
                    ),
                ],
                bg="var(--mantine-color-gray-2)",
            )
        
    table_data = functions.GetUserProjectsTableData(current_user.userdata["id"])
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in table_data])

    return [head, body]


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
                dcc.Interval(id={'type': 'load_interval', 'index': 'projects'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                dmc.Modal(
                    title="Создание нового проекта",
                    id="dialog_create_project",
                    opened = False,
                    children=[
                        #dmc.Space(h=10),
                        dmc.TextInput(debounce=500, id = {"page": "projects", "name":"project_name_text"}, label = "Наименование"),
                        dmc.Space(h=20),
                        dmc.Group(
                            [
                                dmc.Button(id="dialog_create_project_button", children="Создать проект"),
                            ],
                            justify="flex-end",
                        ),
                    ],
                ),
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children=[
                                dmc.Flex(children=dmc.NavLink(id = "create_project_dialog", label = dmc.Text("Создать проект", fz = "lg"), leftSection = DashIconify(icon = "mingcute:file-new-line", width=25))),
                                dmc.Box(dmc.Text(children="Список проектов", fz = "lg")),
                                dmc.Group(
                                    children=[
                                        dmc.Center(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]), fz = "lg")),
                                        dmc.Flex(children=dmc.NavLink(id = {"type": "logout_button", "index": "projects"}, leftSection = DashIconify(icon = "mingcute:exit-fill", width=25), c='red')),
                                    ]
                                ),
                            ],
                            style = {"display":"flex", "justify-content":"space-between", "align-items":"center"},
                        )
                    ], withBorder=True
                ),
                dmc.AppShellMain(
                    children = [
                        dmc.Table(id = "projects_table", children = [], highlightOnHover = True, withTableBorder = True, withColumnBorders=True, fz = "lg")
                    ],
                    mt = "sm",
                    px = "md"
                ),
            ],
            header={"height": "45px"},
        )
    
        layout = dmc.MantineProvider(layout)
        return layout


#Однократный запуск при обновлении страницы
@dash.callback(
    output = {
        "redirect": Output({"type": "redirect", "index": "projects"}, "pathname", allow_duplicate = True),
        "projects_table": Output("projects_table", "children", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "n_intervals": Input(component_id={'type': 'load_interval', 'index': 'projects'}, component_property="n_intervals"),
        }
    },
    prevent_initial_call = True
)
def update_store(input):
    output = {}
    output["redirect"] = "/projects"
    output["projects_table"] = []

    if 1==0:
        output["redirect"] = "/projects"
        return output

    #output["projects_table"] = functions.CreateTableContent(["Название", "Этап", "Роль в проекте", "Перейти к проекту"], functions.GetUserProjectsTableData(current_user.userdata["id"]))
    output["projects_table"] = GetTableProjects(current_user.userdata["id"])


    return output


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
    Output("dialog_create_project", "opened", allow_duplicate = True),
    Input("create_project_dialog", "n_clicks"),
    prevent_initial_call=True,
)
def modal_demo(clickdata):
    if not clickdata: raise PreventUpdate
    return True


@dash.callback(
    Output("projects_table", "children", allow_duplicate = True),
    Output("dialog_create_project", "opened", allow_duplicate = True),
    Input("dialog_create_project_button", "n_clicks"),
    State({"page": "projects", "name":"project_name_text"},"value"),
    prevent_initial_call = True
)
def CreateProject(clickdata, project_name):
    if not clickdata: raise PreventUpdate
    if not project_name: raise PreventUpdate
    if len(project_name.strip())<3: raise PreventUpdate
    if not functions.InsertNewProject(current_user.userdata["id"], project_name): raise PreventUpdate
    table_data = GetTableProjects(current_user.userdata["id"])
    return table_data, False

