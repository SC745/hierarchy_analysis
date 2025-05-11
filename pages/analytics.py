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


def GetTreeSelectedItem(selected):
    if selected == "project": item_data = {"type": "project", "id": None}
    else:
        item_id = int(selected.split("/")[-1])
        if "user" in selected: item_data = {"type": "user", "id": item_id}
        elif "group" in selected: item_data = {"type": "group", "id": item_id}

    return item_data


def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    #page_analytics = session.pop("page_analytics", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "analytics"}, pathname = "/login")
    elif not "page_analytics" in session:
        return dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/project")
    else:
        page_analytics = json.loads(session["page_analytics"])

        layout = dmc.AppShell(
            children = [
                dcc.Location(id = {"type": "redirect", "index": "analytics"}, pathname = "/analytics"),
                dcc.Store(id = {"type": "element_data_store", "index": "dep_eval"}, storage_type='session', clear_data = True),
                dcc.Store(id = {"type": "element_data_store", "index": "comp_eval"}, storage_type='session', clear_data = True),
                dcc.Store(id = {"type": "element_data_store", "index": "incons_coef"}, storage_type='session', clear_data = True),
                dcc.Store(id= "project_data_store", storage_type='session', clear_data = True),
                dcc.Store(id= "element_data_store", storage_type='session', clear_data = True),
                dcc.Store(id = "comp_data_store", storage_type='session', clear_data = True),
                dcc.Download(id="download-table-xlsx"),
                dcc.Interval(id={'type': 'load_interval', 'index': 'analytics'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children=[
                                dmc.Flex(children=dmc.NavLink(label = dmc.Text("Аналитика"), leftSection = DashIconify(icon = "mingcute:menu-line", width=25))),
                                dmc.Box(
                                    children = [
                                        dmc.Group(
                                            children=[
                                                dmc.Center(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                                dmc.Flex(children=dmc.NavLink(id = {"type": "logout_button", "index": "analytics"}, leftSection = DashIconify(icon = "mingcute:exit-fill", width=25), c='red')),
                                            ]
                                        ),

                                    ],
                                    px = "md",
                                    style = {"display":"flex", "justify-content":"end"}
                                )
                            ],
                            px = "md",
                            style = {"display":"flex", "justify-content":"space-between"}
                        ),
                    ]
                ),
                dmc.AppShellNavbar(
                    children = [
                        #dmc.Box(children = dmc.Text("Аналитика", fz = 24, fw = 500), p = "sm"),
                        dmc.Divider(),
                        dmc.Box(
                            children = [
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "dep_eval"},
                                    label = dmc.Text("Результат оценки связей"),
                                    leftSection = DashIconify(icon = "mingcute:directory-line", width=20),
                                    active = True,
                                ),
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "comp_eval"},
                                    label = dmc.Text("Результат сравнительной оценки"),
                                    leftSection = DashIconify(icon = "mingcute:chart-bar-line", width=20),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = {"type": "analytics_navlink", "index": "incons_coef"},
                                    label = dmc.Text("Коэффициент противоречивости"),
                                    leftSection = DashIconify(icon = "mingcute:certificate-line", width=20),
                                    active = False,
                                    display = "none"
                                ),
                                dmc.Divider(),
                                dmc.NavLink(
                                    id = "analytics_to_project",
                                    label = dmc.Text("Вернуться к проекту"),
                                    leftSection = DashIconify(icon = "mingcute:arrow-left-line", width=20),
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
                                    data = functions.GetAnalyticsTreeDataUsers(page_analytics["project_id"]),
                                    selected = ["project"],
                                    display = "block",
                                ),
                                dmc.Tree(
                                    id = {"type": "project_tree", "index": "comp_eval"},
                                    selectOnClick = True,
                                    expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                                    collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                                    data = functions.GetAnalyticsTreeData(page_analytics["project_id"], True),
                                    selected = ["project"],
                                    display = "none",
                                ),
                                dmc.Tree(
                                    id = {"type": "project_tree", "index": "incons_coef"},
                                    selectOnClick = True,
                                    expandedIcon=DashIconify(icon="fa6-regular:folder-open"),
                                    collapsedIcon=DashIconify(icon="fa6-solid:folder-plus"),
                                    data = functions.GetAnalyticsTreeData(page_analytics["project_id"], True),
                                    selected = ["project"],
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
                                    elements = []
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
                                    elements = []
                                ),
                                dmc.Divider(),
                                dmc.Box(
                                    children = [
                                        dmc.Text("Выберите матрицу"),
                                        dmc.Space(h=10),
                                        dmc.Flex(
                                            children = [
                                                dmc.Select(id = "matrix_select", data = matrix_select_data, clearable = False, value = "comparison_matrix", size = "md", w = 350),
                                                dmc.ActionIcon(DashIconify(icon = "mingcute:file-import-line", width=25), size=40, id = "analytics_table_tofile_button", disabled=True, variant="outline", color="var(--mantine-color-gray-7)"),
                                            ],
                                            gap = "md",
                                            align = "flex-end",
                                            #pb = "sm"
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Box(
                                            children = [
                                                dmc.Table(
                                                    id = "comp_eval_table",
                                                    data = {"body": []},
                                                    highlightOnHover = True,
                                                    withTableBorder = True,
                                                    withRowBorders = True,
                                                    withColumnBorders = True,
                                                    fz = "md",
                                                    
                                                ),
                                            ],
                                            display = "none",
                                            id = "matrix_container"
                                        ),
                                        dmc.Center(
                                            children = [
                                                dmc.Space(h=20),
                                                dmc.Text("Выберите элемент", fz = "xl", fw = 500),
                                                ],
                                                display = "block", ta = "center", id = "comp_eval_placeholder")
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
                                    stylesheet = [
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
                                    elements = []
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
            header={"height": "50px"},
            navbar={"width": "310px"},
        )
        layout = dmc.MantineProvider(layout)
        return layout



#Однократный запуск при обновлении страницы
@dash.callback(
    output = {
        "store": {
            "dep_eval": Output({"type": "element_data_store", "index": "dep_eval"}, 'data', allow_duplicate = True),
            "comp_eval": Output({"type": "element_data_store", "index": "comp_eval"}, 'data', allow_duplicate = True),
            "incons_coef": Output({"type": "element_data_store", "index": "incons_coef"}, 'data', allow_duplicate = True),
            "project_data_store": Output("project_data_store", 'data', allow_duplicate = True),
        },
        "graph": {
            "dep_eval": Output({"type": "analytics_graph", "index": "dep_eval"}, "elements",  allow_duplicate = True),
            "comp_eval": Output({"type": "analytics_graph", "index": "comp_eval"}, "elements", allow_duplicate = True),
            "incons_coef": Output({"type": "analytics_graph", "index": "incons_coef"}, "elements", allow_duplicate = True),
        },
        "redirect": Output({"type": "redirect", "index": "analytics"}, "pathname", allow_duplicate = True)
    },
    inputs = {
        "input": {
            "n_intervals": Input(component_id={'type': 'load_interval', 'index': 'analytics'}, component_property="n_intervals"),
        }
    },
    prevent_initial_call = True
)
def update_store(input):
    page_analytics = json.loads(session["page_analytics"])
    project_data = functions.GetProjectData(current_user.userdata["id"], page_analytics["project_id"])

    output = {}

    output["store"] = {}
    output["store"]["dep_eval"] = None
    output["store"]["comp_eval"] = None
    output["store"]["incons_coef"] = None
    output["store"]["project_data_store"] = None

    output["graph"] = {}
    output["graph"]["dep_eval"] = []
    output["graph"]["comp_eval"] = []
    output["graph"]["incons_coef"] = []
    output["redirect"] = "/analytics"

    if project_data["status"]["stage"] < 4:
        page_project = {}
        page_project["project_id"] = page_analytics["project_id"]
        session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)

        output["redirect"] = "/project"
        return output

    element_data = {}

    element_data["dep_eval"] = {}
    element_data["dep_eval"]["elements"] = functions.GetHierarchyPreset(*functions.GetDepEvalGraphDfs(project_data["id"]))
    element_data["dep_eval"]["selected"] = None

    element_data["comp_eval"] = {}
    element_data["comp_eval"]["elements"] = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data))
    element_data["comp_eval"]["selected"] = None
    
    element_data["incons_coef"] = {}
    element_data["incons_coef"]["elements"] = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data))
    element_data["incons_coef"]["selected"] = None

    functions.ColorAnalyticsElements(element_data["comp_eval"], project_data["cons_coef"])
    functions.ColorAnalyticsElements(element_data["incons_coef"], project_data["cons_coef"])

    output["store"]["dep_eval"] = json.dumps(element_data["dep_eval"], cls = functions.NpEncoder)
    output["store"]["comp_eval"] = json.dumps(element_data["comp_eval"], cls = functions.NpEncoder)
    output["store"]["incons_coef"] = json.dumps(element_data["incons_coef"], cls = functions.NpEncoder)
    output["store"]["project_data_store"] = json.dumps(project_data, cls = functions.NpEncoder)

    output["graph"]["dep_eval"] = element_data["dep_eval"]["elements"]
    output["graph"]["comp_eval"] = element_data["comp_eval"]["elements"]
    output["graph"]["incons_coef"] = element_data["incons_coef"]["elements"]

    return output




#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Навигация ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


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
    output = {
        "element_data_store": Output({"type": "element_data_store", "index": "comp_eval"}, "data", allow_duplicate = True),
        "elements": Output({"type": "analytics_graph", "index": "comp_eval"}, "elements", allow_duplicate = True),
        "table_data": Output("comp_eval_table", "data"),
        "matrix_display": Output("matrix_container", "display"),
        "placeholder_display": Output("comp_eval_placeholder", "display"),
        "download_file_disabled": Output("analytics_table_tofile_button", "disabled"),
    },
    inputs = {
        "input": {
            "tapNodeData": Input({"type": "analytics_graph", "index": "comp_eval"}, "tapNodeData"),
            "matrix_select_value": Input("matrix_select", "value"),
            "tree_selected_item": Input({"type": "project_tree", "index": "comp_eval"}, "selected"),
            "element_data_store": State({"type": "element_data_store", "index": "comp_eval"}, "data"),
            "project_data_store": State("project_data_store", "data"),
            "table_data": State("comp_eval_table", "data"),
        }
    },
    prevent_initial_call = True
)
def CompEvalGraphProcessing(input):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[-1], "value": ctx.triggered[0]["value"]}

    element_data = json.loads(input["element_data_store"])
    project_data = json.loads(input["project_data_store"])
    tree_item = GetTreeSelectedItem(input["tree_selected_item"][0])

    if trigger["property"] == "tapNodeData": 
        element_data["selected"] = functions.GetElementById(input["tapNodeData"]["id"], element_data["elements"])
    elif trigger["property"] == "selected":
        group = bool(tree_item["type"] == "group")
        element_data["elements"] = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data, tree_item["id"], group))
    
    table_body = input["table_data"]["body"]
    if element_data["selected"]:
        if tree_item["type"] == "group":
            compdata = functions.GetGroupCalculatedCompdata(element_data["selected"]["data"]["id"], tree_item["id"])
        else:
            compdata = functions.GetCalculatedCompdata(element_data["selected"]["data"]["id"], tree_item["id"])
        
        if len(compdata) != 0:
            if input["matrix_select_value"] == "comparison_matrix":
                matrix = functions.MakeMatrix(compdata)
                local_priorities = functions.GetLocalPriorities(matrix)
                table_body = functions.MakeTableData(element_data["selected"]["data"]["name"], functions.GetUserNodesForSimpleGrid(element_data["selected"]["data"]["id"], project_data, element_data["elements"]), matrix, local_priorities, round_values = True)
            else:
                matrix = functions.MakeMatrix(compdata, property = "competence_data", asymmetrical = False)
                table_body = functions.MakeTableData(element_data["selected"]["data"]["name"], functions.GetUserNodesForSimpleGrid(element_data["selected"]["data"]["id"], project_data, element_data["elements"]), matrix, round_values = True)
            input["table_data"] = {"body": table_body}
        else:
            input["table_data"] = {"body": []}

    functions.ColorAnalyticsElements(element_data, project_data["cons_coef"])

    output = {}
    output["element_data_store"] = json.dumps(element_data, cls = functions.NpEncoder)
    output["elements"] = element_data["elements"]
    output["table_data"] = input["table_data"]
    output["matrix_display"] = "block" if element_data["selected"] else "none"
    output["placeholder_display"] = "none" if element_data["selected"] else "block"
    output["download_file_disabled"]  = False if element_data["selected"] else True
           
    return output


@dash.callback(
    Output({"type": "element_data_store", "index": "dep_eval"}, "data"),
    Output({"type": "analytics_graph", "index": "dep_eval"}, "elements", allow_duplicate = True),
    Input({"type": "project_tree", "index": "dep_eval"}, "selected"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def DepEvalGraphProcessing(selected, project_data_store):
    project_data = json.loads(project_data_store)
    tree_item = GetTreeSelectedItem(selected[0])

    element_data = {}
    element_data["elements"] = functions.GetHierarchyPreset(*functions.GetDepEvalGraphDfs(project_data["id"], tree_item["id"]))
    element_data["selected"] = None

    return json.dumps(element_data, cls = functions.NpEncoder), element_data["elements"]

#analytics_table_tofile_button
#download-table-xlsx

@dash.callback(
    output = {
        "download_file": Output("download-table-xlsx", "data"),
    },
    inputs = {
        "input": {
            "button_click": Input("analytics_table_tofile_button", "n_clicks"),
            "tapNodeData": State({"type": "analytics_graph", "index": "comp_eval"}, "tapNodeData"),
            "matrix_select_value": State("matrix_select", "value"),
            "tree_selected_item": State({"type": "project_tree", "index": "comp_eval"}, "selected"),
            "element_data_store": State({"type": "element_data_store", "index": "comp_eval"}, "data"),
            "project_data_store": State("project_data_store", "data"),
            "table_data": State("comp_eval_table", "data"),
        }
    },
    prevent_initial_call = True
)
def GetFile(input):
    button_click = input["button_click"]
    if not button_click: raise PreventUpdate
    
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[-1], "value": ctx.triggered[0]["value"]}

    element_data = json.loads(input["element_data_store"])
    project_data = json.loads(input["project_data_store"])
    tree_item = GetTreeSelectedItem(input["tree_selected_item"][0])

    if trigger["property"] == "tapNodeData": 
        element_data["selected"] = functions.GetElementById(input["tapNodeData"]["id"], element_data["elements"])
    elif trigger["property"] == "selected":
        group = bool(tree_item["type"] == "group")
        element_data["elements"] = functions.GetHierarchyPreset(*functions.GetPriorityInfo(project_data, tree_item["id"], group))
    
    table_body = input["table_data"]["body"]
    if element_data["selected"]:
        if tree_item["type"] == "group": 
            compdata = functions.GetGroupCalculatedCompdata(element_data["selected"]["data"]["id"], tree_item["id"])
        else: 
            compdata = functions.GetCalculatedCompdata(element_data["selected"]["data"]["id"], tree_item["id"])

        if len(compdata) == 0: raise PreventUpdate

        if input["matrix_select_value"] == "comparison_matrix":
            matrix = functions.MakeMatrix(compdata)
            local_priorities = functions.GetLocalPriorities(matrix)
            table_body = functions.MakeTableData(element_data["selected"]["data"]["name"], functions.GetUserNodesForSimpleGrid(element_data["selected"]["data"]["id"], project_data, element_data["elements"]), matrix, local_priorities, round_values = True)
        else:
            matrix = functions.MakeMatrix(compdata, property = "competence_data", asymmetrical = False)
            table_body = functions.MakeTableData(element_data["selected"]["data"]["name"], functions.GetUserNodesForSimpleGrid(element_data["selected"]["data"]["id"], project_data, element_data["elements"]), matrix, round_values = True)
        input["table_data"] = {"body": table_body}


    df = functions.GetTestDF(table_body)
    output = {}
    output["download_file"] = dcc.send_data_frame(df.to_excel, "matrix_xx_yy.xlsx", sheet_name="Matrix")

    return output