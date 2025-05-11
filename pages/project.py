import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc, MATCH
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto

from flask import session
from flask_login import current_user, logout_user

import functions
import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


def GetEdgeCheckboxes(source_node, element_data, project_data):
    nodes_df, edges_df = functions.ElementsToDfs(element_data["elements"])

    checked_count = 0

    lowerlevel_df = nodes_df.loc[nodes_df["level"] == source_node["data"]["level"] + 1]
    accessable_nodes = list(edges_df.loc[(edges_df["source"] == source_node["data"]["id"]) & ~(edges_df["id"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]["target"])
    cascade_accessable_nodes = list(edges_df.loc[(edges_df["source"] == source_node["data"]["id"]) & (edges_df["id"].isin(list(element_data["state"]["cascade_deleted"].keys())))]["target"])

    edge_checkboxes = []
    for index, row in lowerlevel_df.iterrows():
        edge_checkbox = dmc.Checkbox(py = "xs", pl = "xs")

        edge_checkbox.id = {"type": "edge_checkbox", "index": row["id"]}
        edge_checkbox.label = row["name"]
        edge_checkbox.checked = row["id"] in accessable_nodes
        if row["id"] in accessable_nodes:
            edge_checkbox.checked = True
            checked_count += 1
        else:
            edge_checkbox.checked = False

        edge_checkbox.disabled = row["id"] in cascade_accessable_nodes or project_data["status"]["stage"] != 2 or project_data["role"]["access_level"] < 2

        if element_data["state"]["selected"] and "target" in element_data["state"]["selected"]["data"] and element_data["state"]["selected"]["data"]["target"] == row["id"]: edge_checkbox.style = {"background-color": "#e8f3fc"}

        edge_checkboxes.append(edge_checkbox)

    return edge_checkboxes, checked_count

def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    #page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "project"}, pathname = "/login")
    elif not "page_project" in session:
        return dcc.Location(id = {"type": "redirect", "index": "project"}, pathname = "/projects")
    else:
        page_project = json.loads(session["page_project"])

        layout = dmc.AppShell(
            children = [
                dcc.Location(id = {"type": "redirect", "index": "project"}, pathname = "/project"),
                dcc.Store(id="project_data_store", storage_type='session', clear_data=True),
                dcc.Store(id="element_data_store", storage_type='session', clear_data=True),
                dcc.Store(id="comp_data_store", storage_type='session', clear_data=True),
                dcc.Store(id = {"type": "init_store", "index": "project"}, storage_type = "memory"),
                dcc.Store(id = "prev_action", storage_type = "memory", data = False),
                dcc.Interval(id={'type': 'load_interval', 'index': 'project'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Flex(
                                    children=
                                    dmc.Menu(
                                        children = [
                                            dmc.MenuTarget(dmc.NavLink(label = dmc.Text("Проект"), leftSection = DashIconify(icon = "mingcute:menu-line", width=25))),
                                            dmc.MenuDropdown(
                                                children = [
                                                    dmc.MenuItem(id = {"type":"menu_navlink", "index":"/settings"}, children = dmc.Text("Настройки"), leftSection = DashIconify(icon = "mingcute:settings-3-line", width=20), disabled = True),
                                                    dmc.MenuItem(id = {"type":"menu_navlink", "index":"/analytics"}, children = dmc.Text("Аналитика"), leftSection = DashIconify(icon = "mingcute:chart-line-fill", width=20), disabled = True),
                                                    dmc.MenuItem(id = "restore_initial_hierarchy", children = dmc.Text("Восстановить базовую иерархию"), leftSection = DashIconify(icon = "mingcute:refresh-3-fill", width=20), disabled = True),
                                                    dmc.MenuDivider(),
                                                    dmc.MenuItem(children = dmc.Checkbox(
                                                        id = {"type": "stage_completed", "index": "de_completed"}, 
                                                        label = dmc.Text("Оценка зависимостей завершена"), 
                                                        checked = False, 
                                                        disabled=True
                                                        ),
                                                    ),
                                                    dmc.MenuItem(children = dmc.Checkbox(
                                                        id = {"type": "stage_completed", "index": "ce_completed"}, 
                                                        label = dmc.Text("Сравнительная оценка завершена"), 
                                                        checked = False, 
                                                        disabled = True
                                                        ), 
                                                    ),
                                                    dmc.MenuDivider(),
                                                    dmc.MenuItem(id = {"type":"menu_navlink", "index":"/projects"}, leftSection = DashIconify(icon = "mingcute:list-check-line", width=20), children = "Список проектов")
                                                ]
                                            )
                                        ],
                                        trigger="hover",
                                    ),
                                ),
                                dmc.Center(dmc.Text(id="project_name_header_text", size='lg')),
                                dmc.Group(
                                    children=[
                                        dmc.Center(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                        dmc.Flex(children=dmc.NavLink(id = {"type": "logout_button", "index": "project"}, leftSection = DashIconify(icon = "mingcute:exit-fill", width=25), c='red')),
                                    ]
                                ),
                            ],
                            px = "md",
                            style = {"display":"flex", "justify-content":"space-between"}
                        )
                    ]
                ),
                dmc.AppShellAside(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Group(
                                    children = [
                                        dmc.ActionIcon(id = {"type": "step_button", "index": "rollback"}, children = DashIconify(icon = "mingcute:corner-down-left-fill", width = 20), size = "input-sm", variant = "default", disabled = True),
                                        dmc.ActionIcon(id = {"type": "step_button", "index": "cancelrollback"}, children = DashIconify(icon = "mingcute:corner-down-right-fill", width = 20), size = "input-sm", variant = "default", disabled = True),
                                        dmc.ActionIcon(id = "locate", children = DashIconify(icon = "mingcute:location-line", width = 20), size = "input-sm", variant = "default"),
                                        dmc.ActionIcon(id = "add_node", children = DashIconify(icon = "mingcute:cross-line", width = 20), size = "input-sm", variant = "light", disabled = True, color = "green"),
                                        dmc.ActionIcon(id = "save_graph", children = DashIconify(icon = "mingcute:save-2-line", width = 20), size = "input-sm", variant = "light", disabled = True),
                                    ],
                                    grow=True,
                                    preventGrowOverflow=False,
                                    p = "md"
                                ),
                                dmc.Divider()
                            ]
                        ),
                        dmc.Box(
                            children = [
                                dmc.Box(
                                    dmc.Text(
                                        children = "Выберите элемент",
                                        ta = "center",
                                        pt = "md"
                                    ),
                                    id = "toolbar_placeholder",
                                    display = "block"
                                ),
                                dmc.Box(
                                    children = [
                                        dmc.Stack(
                                            children = [
                                                dmc.Stack(
                                                    children = [
                                                        dmc.Flex(
                                                            children = [
                                                                dmc.TextInput(debounce=500, id = "name_input", label = "Название", disabled = True),
                                                                dmc.Checkbox(id = "node_checkbox", size = 36, checked = True)
                                                            ],
                                                            gap = "md",
                                                            align = "flex-end",
                                                        ),
                                                        dmc.Button(id = "compdata_button", children = "Оценить", display = "none")
                                                    ],
                                                    p = "md",
                                                    gap = 5
                                                ),
                                                dmc.Text("Элементы нижнего уровня", pl=20),
                                                dmc.ScrollArea(dmc.Stack(id = "edge_checkboxes", children = [], gap = 0), h="100%", w="100%"),
                                            ],
                                        ),
                                        dcc.Store(id = "current_node_id", storage_type = "memory", data = None)
                                    ],
                                    display = "none",
                                    id = "toolbar",
                                ),
                            ]
                        )
                    ]
                ),
                dmc.AppShellMain(
                    children=[
                        cyto.Cytoscape(
                            id="graph",
                            layout={"name": "preset"},
                            style={
                                "width": "100%",
                                "height": "calc(100vh - 50px)",
                                "position": "relative",
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
                                    "selector": ".manually_deleted",
                                    'style': { #mantine red.6
                                        "border-color": "#fa5252",
                                        "line-color": "#fa5252"
                                    }
                                },
                                {
                                    "selector": ".cascade_deleted",
                                    'style': { #mantine orange.6
                                        "border-color": "#fd7e14",
                                        "line-color": "#fd7e14"
                                    }
                                },
                                {
                                    "selector": ".added",
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
            header={"height": "50px"},
            aside={"width": "300px"},
        )
        layout = dmc.MantineProvider(layout)
        return layout


#Однократный запуск при обновлении страницы
@dash.callback(
    output = {
        "redirect": Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
        "project_data_store": Output("project_data_store", "data", allow_duplicate = True),
        "element_data_store": Output("element_data_store", "data", allow_duplicate = True),
        "graph": Output("graph", "elements", allow_duplicate = True),
        "current_node_id": Output("current_node_id", "data", allow_duplicate = True),
        "project_name_header_text": Output("project_name_header_text", "children"),
        "settings_disabled": Output({"type":"menu_navlink", "index":"/settings"}, "disabled"),
        "analytics_disabled": Output({"type":"menu_navlink", "index":"/analytics"}, "disabled"),
        "restore_initial_hierarchy_disabled": Output("restore_initial_hierarchy", "disabled"),
        "de_completed_checked": Output({"type": "stage_completed", "index": "de_completed"}, "checked"),
        "de_completed_disabled": Output({"type": "stage_completed", "index": "de_completed"}, "disabled"),
        "ce_completed_checked": Output({"type": "stage_completed", "index": "ce_completed"}, "checked"),
        "ce_completed_disabled": Output({"type": "stage_completed", "index": "ce_completed"}, "disabled"),
        "name_input_disabled": Output("name_input", "disabled"),
    },
    inputs = {
        "input": {
            "n_intervals": Input(component_id={'type': 'load_interval', 'index': 'project'}, component_property="n_intervals"),
        }
    },
    prevent_initial_call = True
)
def update_store(input):
    output = {}
    output["redirect"] = "/project"
    output["project_data_store"] = None
    output["element_data_store"] = None
    output["graph"] = []
    output["current_node_id"] = None
    output["project_name_header_text"] = ""
    output["settings_disabled"] = True
    output["analytics_disabled"] = True
    output["restore_initial_hierarchy_disabled"] = True
    output["de_completed_checked"] = False
    output["de_completed_disabled"] = True
    output["ce_completed_checked"] = False
    output["ce_completed_disabled"] = True
    output["name_input_disabled"] = True

    page_project = json.loads(session["page_project"])
    project_data = functions.GetProjectData(current_user.userdata["id"], page_project["project_id"])
    element_data = functions.GetElementData(project_data, current_user.userdata["id"])

    output["project_name_header_text"] = project_data["name"] + " (" + project_data["status"]["name"] + ")"
    output["settings_disabled"] = project_data["role"]["access_level"] < 3
    output["analytics_disabled"] = project_data["status"]["stage"] < 4
    output["restore_initial_hierarchy_disabled"] = not (project_data["status"]["stage"] == 2 and project_data["role"]["access_level"] > 1)

    output["de_completed_checked"] = project_data["completed"]["de_completed"] 
    output["de_completed_disabled"] = project_data["status"]["stage"] != 2 or project_data["role"]["access_level"] < 2
    output["ce_completed_checked"] = project_data["completed"]["ce_completed"] 
    output["ce_completed_disabled"] = project_data["status"]["stage"] != 3 or project_data["role"]["access_level"] < 2

    output["name_input_disabled"] = bool(project_data["status"]["stage"] > 1) or bool(project_data["role"]["access_level"] < 3)

    if "current_node_id" in page_project:
        output["current_node_id"] = page_project["current_node_id"]
        #current_node_name = page_project["current_node_name"]

    if 1==0:
        output["redirect"] = "/projects"
        return output

    output["graph"] = element_data["elements"]
    output["project_data_store"] = json.dumps(project_data, cls = functions.NpEncoder)
    output["element_data_store"] = json.dumps(element_data, cls = functions.NpEncoder)
    return output




#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Навигация ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": "project"}, "n_clicks"),
    State("project_data_store", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def Logout(clickdata, project_data_store, element_data_store):
    if not clickdata: raise PreventUpdate
    if project_data_store == None or element_data_store == None: raise PreventUpdate

    project_data = json.loads(project_data_store)
    element_data = json.loads(element_data_store)
    SaveGraphToBD(project_data, element_data)
    session.clear()
    logout_user()
    return "/login"


@dash.callback(
    Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
    Output("current_node_id", "data", allow_duplicate = True),
    Input({"type": "menu_navlink", "index": ALL}, "n_clicks"),
    State("project_data_store", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def RedirectMenuItems(clickdata, project_data_store, element_data_store):
    
    if project_data_store == None or element_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    element_data = json.loads(element_data_store)

    if ctx.triggered_id["index"] == "/settings":
        SaveGraphToBD(project_data, element_data)
        page_project = json.loads(session["page_project"])
        page_settings = {}
        page_settings["project_id"] = page_project["project_id"]
        session["page_settings"] = json.dumps(page_settings, cls = functions.NpEncoder)

    elif ctx.triggered_id["index"] == "/analytics":
        SaveGraphToBD(project_data, element_data)
        page_project = json.loads(session["page_project"])
        page_analytics = {}
        page_analytics["project_id"] = page_project["project_id"]
        session["page_analytics"] = json.dumps(page_analytics, cls = functions.NpEncoder)

    return ctx.triggered_id["index"], None


@dash.callback(
    Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
    Input("compdata_button", "n_clicks"),
    State("current_node_id", "data"),
    State("name_input", "value"),
    State("project_name_header_text", "children"),
    prevent_initial_call = True
)
def RedirectToNodeCompEval(clickdata, current_node_id, current_node_name, project_name_header_text):
    if clickdata is None:
        raise PreventUpdate
    else:
        page_project = json.loads(session["page_project"])
        page_compeval = {}
        page_compeval["project_id"] = page_project["project_id"]
        page_compeval["project_name"] = project_name_header_text
        page_compeval["current_node_id"] = current_node_id
        page_compeval["current_node_name"] = current_node_name
        page_compeval["cursor"] = 0
        session["page_compeval"] = json.dumps(page_compeval, cls = functions.NpEncoder)
        return "/compeval"




#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Граф и панель инструментов -------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def SaveGraphToBD(project_data, element_data):
    if project_data["status"]["stage"] == 1 and project_data["role"]["access_level"] > 2: return functions.SaveInitialGraphToDB(element_data, project_data["id"])
    if project_data["status"]["stage"] == 2 and project_data["role"]["access_level"] > 1: return functions.SaveEdgedataToDB(element_data, project_data["id"], current_user.userdata["id"])


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Output("element_data_store", "data", allow_duplicate = True),
    Input("save_graph", "n_clicks"),
    State("project_data_store", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def SaveGraph(clickdata, project_data_store, element_data_store):
    
    if project_data_store == None or element_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    element_data = json.loads(element_data_store)

    if SaveGraphToBD(project_data, element_data):
        functions.ColorElements(element_data)
        functions.RefreshNodePositionsSizes(element_data["elements"])

    return element_data["elements"], True, json.dumps(element_data, cls = functions.NpEncoder)


@dash.callback(
    output = {
        "current_node_id": Output("current_node_id", "data", allow_duplicate = True),
        "name_input_value": Output("name_input", "value"),
        "node_checkbox_checked": Output("node_checkbox", "checked"),
        "node_checkbox_disabled": Output("node_checkbox", "disabled"),
        "edge_checkboxes": Output("edge_checkboxes", "children"),
        "elements": Output("graph", "elements", allow_duplicate = True),
        "prev_action": Output("prev_action", "data", allow_duplicate = True),
        "element_data": Output("element_data_store", "data", allow_duplicate = True),
        "compdata_button": Output("compdata_button", "display"),
    },
    inputs = {
        "input": {
            "tapNodeData": Input("graph", "tapNodeData"),
            "tapEdgeData": Input("graph", "tapEdgeData"),
            "current_node_id": Input("current_node_id", "data"),
        }
    },
    state=dict(
        project_data_store=State("project_data_store", "data"),
        element_data_store=State("element_data_store", "data"),
    ),
    prevent_initial_call = True
)
def SelectElement(input, project_data_store, element_data_store):
    #trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[-1], "value": ctx.triggered[0]["value"]}

    if project_data_store == None or element_data_store == None: raise PreventUpdate
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[-1], "value": ctx.triggered[0]["value"]}
    project_data = json.loads(project_data_store)
    element_data = json.loads(element_data_store)

    if trigger["property"] == "tapNodeData":
        current_node = functions.GetElementById(input["tapNodeData"]["id"], element_data["elements"])
    elif trigger["property"] == "tapEdgeData":
        current_node = functions.GetElementById(input["tapEdgeData"]["source"], element_data["elements"])
    else:
        current_node = functions.GetElementById(input["current_node_id"], element_data["elements"])

    if not current_node: raise PreventUpdate

    if trigger["property"] == "tapEdgeData":
        element_data["state"]["selected"] = functions.GetElementById(input["tapEdgeData"]["id"], element_data["elements"])
        element_data["state"]["cascade_selected"] = {}
    else:
        element_data["state"]["selected"] = current_node
        functions.CascadeSelect(current_node["data"]["id"], element_data)

    functions.ColorElements(element_data)

    edge_checkboxes, checked_count = GetEdgeCheckboxes(current_node, element_data, project_data)

    output = {}
    output["current_node_id"] = current_node["data"]["id"]
    output["name_input_value"] = current_node["data"]["name"]
    output["node_checkbox_checked"] = current_node["data"]["id"] not in list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys())
    output["node_checkbox_disabled"] = current_node["data"]["id"] in element_data["state"]["cascade_deleted"].keys() or project_data["status"]["stage"] > 2 or (project_data["role"]["access_level"] < 3 and project_data["status"]["stage"] == 1) or (project_data["role"]["access_level"] < 2 and project_data["status"]["stage"] == 2)
    output["edge_checkboxes"] = edge_checkboxes
    output["elements"] = element_data["elements"]
    output["prev_action"] = False
    output["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)
    output["compdata_button"] = "block" if project_data["status"]["stage"] == 3 and checked_count > 1 else "none"

    return output


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Output("element_data_store", "data", allow_duplicate = True),
    Input("node_checkbox", "checked"),
    Input({"type": "edge_checkbox", "index": ALL}, "checked"),
    State("current_node_id", "data"),
    State("prev_action", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def CheckboxClick(node_checked, edge_checked, current_node_id, prev_action, element_data_store):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}
    
    if element_data_store == None: raise PreventUpdate
    element_data = json.loads(element_data_store)

    if prev_action:
        current_node = functions.GetElementById(current_node_id, element_data["elements"])
        if trigger["id"] != "node_checkbox": element = functions.GetEdge(current_node["data"]["id"], trigger["id"]["index"], element_data["elements"])
        else: element = current_node

        if element:
            if trigger["value"]:
                functions.CancelDeleteElement(element, element_data)
                functions.AddStep(element, element_data, "canceldelete")
            else:
                functions.DeleteElement(element, element_data)
                functions.AddStep(element, element_data, "delete")
        else:
            edge_object = functions.CreateEdgeObject(current_node["data"]["id"], trigger["id"]["index"])
            functions.AddElement(edge_object, element_data)
            functions.AddStep(edge_object, element_data, "add")

        functions.ColorElements(element_data)
        
    return element_data["elements"], True, json.dumps(element_data, cls = functions.NpEncoder)


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Output("element_data_store", "data", allow_duplicate = True),
    Input("name_input", "value"),
    State("current_node_id", "data"),
    State("prev_action", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def ChangeNodeName(new_name, current_node_id, prev_action, element_data_store):
    
    if element_data_store == None: raise PreventUpdate
    element_data = json.loads(element_data_store)

    if prev_action:
        current_node = functions.GetElementById(current_node_id, element_data["elements"])

        strlen = len(new_name)
        if strlen > 100: strlen = 100
        current_node["data"]["name"] = new_name[:strlen]

        functions.RefreshNodePositionsSizes(element_data["elements"])

    return element_data["elements"], True, json.dumps(element_data, cls = functions.NpEncoder)


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Output("element_data_store", "data", allow_duplicate = True),
    Input({"type": "step_button", "index": ALL}, "n_clicks"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def StepButtons(clickdata, element_data_store):
    
    if element_data_store == None: raise PreventUpdate
    element_data = json.loads(element_data_store)

    if ctx.triggered_id["index"] == "rollback": 
        used_list = "history"
        store_list = "canceled"
    else: 
        used_list = "canceled"
        store_list = "history"

    if len(element_data["steps"][used_list]) > 0:
        action = element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["action"]
        element = functions.GetElementById(element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["element"]["data"]["id"], element_data["elements"])
        if not element: element = element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["element"]

        if action == "delete":
            element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["action"] = "canceldelete"
            functions.CancelDeleteElement(element, element_data)
        if action == "canceldelete":
            element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["action"] = "delete"
            functions.DeleteElement(element, element_data)
        if action == "add":
            element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["action"] = "canceladd"
            functions.CancelAddElement(element, element_data)
        if action == "canceladd":
            element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["action"] = "add"
            functions.AddElement(element, element_data)

        element_data["steps"][store_list].append(element_data["steps"][used_list].pop())

    functions.ColorElements(element_data)
    functions.RefreshNodePositionsSizes(element_data["elements"])
    
    return element_data["elements"], True, json.dumps(element_data, cls = functions.NpEncoder)


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("current_node_id", "data", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Output("element_data_store", "data", allow_duplicate = True),
    Input("add_node", "n_clicks"),
    State("current_node_id", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def AddNewNode(clickdata, current_node_id, element_data_store):
    
    if element_data_store == None: raise PreventUpdate
    element_data = json.loads(element_data_store)

    node_object = functions.CreateNodeObject(functions.GetElementById(current_node_id, element_data["elements"]))
    functions.AddElement(node_object, element_data)
    functions.AddStep(node_object, element_data, "add")
    element_data["state"]["selected"] = node_object

    functions.ColorElements(element_data)
    functions.RefreshNodePositionsSizes(element_data["elements"])
    
    return element_data["elements"], node_object["data"]["id"], True, json.dumps(element_data, cls = functions.NpEncoder)


@dash.callback(
    output = {
        "placeholder_display": Output("toolbar_placeholder", "display"),
        "toolbar_display": Output("toolbar", "display"),
        "current_node_id": Output("current_node_id", "data", allow_duplicate = True),
        "rollback_disabled": Output({"type": "step_button", "index": "rollback"}, "disabled"),
        "cancelrollback_disabled": Output({"type": "step_button", "index": "cancelrollback"}, "disabled"),
        "addnode_disabled": Output("add_node", "disabled"),
        "save_graph": Output("save_graph", "disabled"),
    },
    inputs = {
        "input": {
            "elements": Input("graph", "elements"),
            "current_node_id": State("current_node_id", "data"),
        }
    },
    state=dict(
        project_data_store=State("project_data_store", "data"),
        element_data_store=State("element_data_store", "data"),
    ),
    prevent_initial_call = True 
)
def ElementChangeProcessing(input, project_data_store, element_data_store):

    if project_data_store == None or element_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    element_data = json.loads(element_data_store)
    
    current_node = functions.GetElementById(input["current_node_id"], input["elements"])

    output = {}
    output["rollback_disabled"] = not bool(len(element_data["steps"]["history"]))
    output["cancelrollback_disabled"] = not bool(len(element_data["steps"]["canceled"]))
    output["addnode_disabled"] = not ((bool(element_data["state"]["selected"]) or not bool(len(element_data["elements"]))) and project_data["status"]["stage"] == 1 and project_data["role"]["access_level"] > 2)

    #k = project_data["status"]["stage"] != 1 or project_data["role"]["access_level"] < 3
    

    output["save_graph"] = (project_data["status"]["stage"] == 1 and project_data["role"]["access_level"] < 3) or (project_data["status"]["stage"] == 2 and project_data["role"]["access_level"] < 2) or project_data["status"]["stage"] > 2

    if current_node: 
        output["placeholder_display"] = "none"
        output["toolbar_display"] = "block"
        output["current_node_id"] = input["current_node_id"]
    else:
        output["placeholder_display"] = "block"
        output["toolbar_display"] = "none"
        output["current_node_id"] = None

    return output




#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Выпадающее меню ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    Output("current_node_id", "data", allow_duplicate = True),
    Output("element_data_store", "data", allow_duplicate = True),
    Input("restore_initial_hierarchy", "n_clicks"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def RestoreInitialHierarchy(clickdata, project_data_store):
    
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)

    if functions.DiscardEdgedataChanges(project_data["id"], current_user.userdata["id"]):
        element_data = functions.GetElementData(project_data, current_user.userdata["id"])
    else: raise PreventUpdate

    return None, json.dumps(element_data, cls = functions.NpEncoder)


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("project_data_store", "data", allow_duplicate = True),
    Input({"type": "stage_completed", "index": ALL}, "checked"),
    State("project_data_store", "data"),
    State("element_data_store", "data"),
    prevent_initial_call = True
)
def CompletedCheckboxes(checked, project_data_store, element_data_store):

    if project_data_store == None or element_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    element_data = json.loads(element_data_store)

    option = ctx.triggered_id["index"]
    checked = ctx.triggered[0]["value"]

    if functions.ChangeCompleteState(project_data["id"], current_user.userdata["id"], option, checked):
        project_data["completed"][option] = checked
    else: raise PreventUpdate()

    return element_data["elements"], json.dumps(project_data, cls = functions.NpEncoder)

