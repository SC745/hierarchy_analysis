import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, MATCH, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto

from flask import session
from flask_login import current_user, logout_user

import functions
import json

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


matrix_select_data = [
    {"label": "Матрица сравнений", "value": "comparison_matrix"},
    {"label": "Матрица компетентности", "value": "competence_matrix"},
]



def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    #page_analytics = session.pop("page_analytics", None)

    #Очистка данных
    #project_data = session.pop("project_data", None)
    #element_data = session.pop("element_data", None)
    #comp_data = session.pop("comp_data", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "analytics"}, pathname = "/login")
    elif not "page_analytics" in session:
        return dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/project")
    else:
        page_analytics = json.loads(session["page_analytics"])
        project_data = functions.GetProjectData(current_user.userdata["id"], page_analytics["project_id"])
        if project_data["status"]["stage"] < 4:
            return dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/project"),
        
        project_data_store = json.dumps(project_data, cls = functions.NpEncoder)

        element_data = {}

        element_data["dep_eval"] = {}
        element_data["dep_eval"]["elements"] = functions.GetHierarchyPreset(*functions.GetAnalyticsGraphDfs(project_data["id"]))
        element_data["dep_eval"]["selected"] = None

        element_data["comp_eval"] = {}
        element_data["comp_eval"]["elements"] = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data))
        element_data["comp_eval"]["selected"] = None
        
        element_data["incons_coef"] = {}
        element_data["incons_coef"]["elements"] = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data))
        element_data["incons_coef"]["selected"] = None


        layout = dmc.AppShell(
            children = [
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/analytics"),
                                dcc.Store(id = "project_data_store", storage_type='session', data = project_data_store),
                                dcc.Store(id = {"type": "element_data_store", "index": "dep_eval"}, storage_type='session', data = json.dumps(element_data["dep_eval"], cls = functions.NpEncoder)),
                                dcc.Store(id = {"type": "element_data_store", "index": "comp_eval"}, storage_type='session', data = json.dumps(element_data["comp_eval"], cls = functions.NpEncoder)),
                                dcc.Store(id = {"type": "element_data_store", "index": "incons_coef"}, storage_type='session', data = json.dumps(element_data["incons_coef"], cls = functions.NpEncoder)),
                                dcc.Store(id = "comp_data_store", storage_type='session', clear_data=True),
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
                                    id = {"type": "analytics_navlink", "index": "dep_eval"},
                                    label = "Результат оценки связей",
                                    leftSection = DashIconify(icon = "mingcute:user-1-line"),
                                    active = True
                                ),
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "comp_eval"},
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
                        dmc.Box(
                            children = [
                                dmc.Tree(
                                    id = {"type": "project_tree", "index": "dep_eval"},
                                    selectOnClick = True,
                                    expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                                    collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                                    data = functions.GetAnalyticsTreeData(project_data["id"], False),
                                    selected = "project",
                                    display = "block",
                                ),
                                dmc.Tree(
                                    id = {"type": "project_tree", "index": "comp_eval"},
                                    selectOnClick = True,
                                    expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                                    collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                                    data = functions.GetAnalyticsTreeData(project_data["id"], True),
                                    selected = "project",
                                    display = "none",
                                ),
                                dmc.Tree(
                                    id = {"type": "project_tree", "index": "incons_coef"},
                                    selectOnClick = True,
                                    expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                                    collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                                    data = functions.GetAnalyticsTreeData(project_data["id"], True),
                                    selected = "project",
                                    display = "none",  
                                ),
                            ],
                            p = "sm"
                        )
                    ]
                ),
                dmc.AppShellMain(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Text("Результат оценки связей", fz = 24, fw = 500, p = "sm"),
                                cyto.Cytoscape(
                                    id = {"type": "analytics_graph", "index": "dep_eval"},
                                    layout = {"name": "preset"},
                                    style = {
                                        "width": "100%",
                                        "height": "calc(100vh - 100px)",
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
                                            "selector": ".deleted",
                                            "style": { #mantine orange.6
                                                "border-color": "#fd7e14",
                                                "line-color": "#fd7e14"
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
                                    elements = element_data["dep_eval"]["elements"]
                                ),
                            ],
                            id = {"type": "analytics_page", "index": "dep_eval"},
                            display = "block",
                        ),
                        dmc.Box(
                            children = [
                                dmc.Text("Результат сравнительной оценки", fz = 24, fw = 500, p = "sm"),
                                cyto.Cytoscape(
                                    id = {"type": "analytics_graph", "index": "comp_eval"},
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
                                                "content": "data(full_name)",
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
                                    elements = element_data["comp_eval"]["elements"]
                                ),
                                dmc.Divider(),
                                dmc.Box(
                                    children = [
                                        dmc.Box(
                                            children = [
                                                dmc.Select(id = "matrix_select", data = matrix_select_data, label = "Матрица", clearable = False, value = "competence_matrix", size = "md", w = 350, pb = "sm"),
                                                dmc.Table(
                                                    id = "comp_eval_table",
                                                    data = [],
                                                    highlightOnHover = True,
                                                    withTableBorder = True,
                                                    withRowBorders = True,
                                                    fz = "md",
                                                ),
                                            ],
                                            id = "comp_eval_table_container",
                                            display = "none"
                                        ),
                                        dmc.Center(children = dmc.Text("Выберите элемент", fz = 24, fw = 500), display = "block", id = "comp_eval_placeholder")
                                    ],
                                    p = "sm"
                                )
                            ],
                            id = {"type": "analytics_page", "index": "comp_eval"},
                            display = "none",
                        ),
                        dmc.Box(
                            children = [
                                dmc.Text("Коэффициент значимости противоречивости экспертов", fz = 24, fw = 500, p = "sm"),
                                cyto.Cytoscape(
                                    id = {"type": "analytics_graph", "index": "incons_coef"},
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
                                                "content": "data(full_name)",
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
                                    elements = element_data["incons_coef"]["elements"]
                                ),
                                dmc.Divider(),
                                dmc.Box("table_section")
                            ],
                            id = {"type": "analytics_page", "index": "incons_coef"},
                            display = "none",
                        )
                    ]
                ),
            ],
            header={"height": "30px"},
            navbar={"width": "300px"},
        )
        layout = dmc.MantineProvider(layout)
        return layout


def GetTreeSelectedItem(selected):
    if not "/" in selected: item_data = {"type": "project", "id": None}
    else:
        item_id = int(selected.split("/")[-1])
        if "user" in selected: item_data = {"type": "user", "id": item_id}
        elif "group" in selected: item_data = {"type": "group", "id": item_id}

    return item_data


#Навигация ----------------------------------------------------------------------------------------------------

@dash.callback(
    Output({"type": "redirect", "index": "analytics"}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": "analytics"}, "n_clicks"),
    prevent_initial_call = True
)
def Logout(clickdata):
    if clickdata:
        session.clear()
        logout_user()
        return "/login"
    

@dash.callback(
    output = {
        "navlink_selected": {
            "dep_eval": Output({"type": "analytics_navlink", "index": "dep_eval"}, "active"),
            "comp_eval": Output({"type": "analytics_navlink", "index": "comp_eval"}, "active"),
            "incons_coef": Output({"type": "analytics_navlink", "index": "incons_coef"}, "active"),
        },
        "page_display": {
            "dep_eval": Output({"type": "analytics_page", "index": "dep_eval"}, "display"),
            "comp_eval": Output({"type": "analytics_page", "index": "comp_eval"}, "display"),
            "incons_coef": Output({"type": "analytics_page", "index": "incons_coef"}, "display"),
        },
        "project_tree_display": {
            "dep_eval": Output({"type": "project_tree", "index": "dep_eval"}, "display"),
            "comp_eval": Output({"type": "project_tree", "index": "comp_eval"}, "display"),
            "incons_coef": Output({"type": "project_tree", "index": "incons_coef"}, "display"),
        }
    },
    inputs = {
        "input": {
            "navlink_click": Input({"type": "analytics_navlink", "index": ALL}, "n_clicks"),
            "page_ids": Input({"type": "analytics_page", "index": ALL}, "id"),
        }
    },
    prevent_initial_call = True
)
def NavlinkClick(input):
    
    page_keys = [id["index"] for id in input["page_ids"]]

    navlink_selected = {}
    page_display = {}
    for key in page_keys:
        if key == ctx.triggered_id["index"]:
            navlink_selected[key] = True
            page_display[key] = "block"
        else:
            navlink_selected[key] = False
            page_display[key] = "none"


    output = {}
    output["navlink_selected"] = navlink_selected
    output["page_display"] = page_display
    output["project_tree_display"] = page_display

    return output


@dash.callback(
    Output({"type": "redirect", "index": "analytics"}, "pathname", allow_duplicate = True),
    Input("analytics_to_project", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProject(clickdata):
    if clickdata is None:
        raise PreventUpdate
    else:
        page_analytics = json.loads(session["page_analytics"])
        page_project = {}
        page_project["project_id"] = page_analytics["project_id"]
        session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)
    
        return "/project"


@dash.callback(
    Output({"type": "element_data_store", "index": MATCH}, "data", allow_duplicate = True),
    Output({"type": "analytics_graph", "index": MATCH}, "elements", allow_duplicate = True),
    Input({"type": "project_tree", "index": MATCH}, "selected"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def TreeItemSelect(selected, project_data_store):
    if selected:
        
        selected = GetTreeSelectedItem(selected)
        project_data = json.loads(project_data_store)
        if selected["type"] in ["project", "user"]: 
            elements = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data, selected["id"]))
        else: raise PreventUpdate

        element_data = {}
        element_data["elements"] = elements
        element_data["selected"] = None

        return json.dumps(element_data, cls = functions.NpEncoder), elements
    
    else: raise PreventUpdate


@dash.callback(
    output = {
        "element_data_store": Output({"type": "element_data_store", "index": "comp_eval"}, "data", allow_duplicate = True),
        "elements": Output({"type": "analytics_graph", "index": "comp_eval"}, "elements", allow_duplicate = True),
        "table_data": Output("comp_eval_table", "data"),
        "container_display": Output("comp_eval_table_container", "display"),
        "placeholder_display": Output("comp_eval_placeholder", "display"),
    },
    inputs = {
        "input": {
            "tapNodeData": Input({"type": "analytics_graph", "index": "comp_eval"}, "tapNodeData"),
            "element_data_store": State({"type": "element_data_store", "index": "comp_eval"}, "data"),
            "project_data_store": State("project_data_store", "data"),
            "matrix_select_value": State("matrix_select", "value"),
            "tree_selected_item": State({"type": "project_tree", "index": "comp_data"}, "selected"),
        }
    },
    prevent_initial_call = True
)
def SelectCompEvalGraphElement(input):
    element_data = json.loads(input["element_data_store"])
    project_data = json.loads(input["project_data_store"])

    element_data["selected"] = functions.GetElementById(input["tapNodeData"]["id"], element_data["elements"])
    functions.ColorAnalyticsElements(element_data)

    tree_item = GetTreeSelectedItem(input["tree_selected_item"])

    if tree_item["type"] != "group": compdata = functions.GetCalculatedCompdata(element_data["selected"]["data"]["id"])
    else: compdata = functions.GetCalculatedCompdata(element_data["selected"]["data"]["id"])
    
    if input["matrix_select_value"] == "comparison_matrix":
        matrix = functions.MakeMatrix(compdata["weighted_data"], round = True)
        local_priorities = functions.GetNodeLocalPriorities(matrix)
        table_data = functions.MakeTableData(element_data["selected"]["data"]["name"], functions.GetUserNodesForSimpleGrid(element_data["selected"]["data"]["id"], project_data, element_data["elements"]), matrix, local_priorities)
    else:
        matrix = functions.MakeMatrix(compdata, property = "competence_data", round = True)
        table_data = functions.MakeTableData(element_data["selected"]["data"]["name"], functions.GetUserNodesForSimpleGrid(element_data["selected"]["data"]["id"], project_data, element_data["elements"]), matrix)

    output = {}
    output["element_data_store"] = json.dumps(element_data, cls = functions.NpEncoder)
    output["elements"] = element_data["elements"]
    output["table_data"] = table_data
    output["container_display"] = "block"
    output["placeholder_display"] = "none"

    return output