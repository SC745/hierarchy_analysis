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


def GetEdgeCheckboxes(source_node, element_data, project_data):
    nodes_df, edges_df = functions.ElementsToDfs(element_data["elements"])

    lowerlevel_df = nodes_df.loc[nodes_df["level"] == source_node["data"]["level"] + 1]
    accessable_nodes = list(edges_df.loc[(edges_df["source"] == source_node["data"]["id"]) & ~(edges_df["id"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]["target"])
    cascade_accessable_nodes = list(edges_df.loc[(edges_df["source"] == source_node["data"]["id"]) & (edges_df["id"].isin(list(element_data["state"]["cascade_deleted"].keys())))]["target"])

    edge_checkboxes = []
    for index, row in lowerlevel_df.iterrows():
        edge_checkbox = dmc.Checkbox(py = "xs", pl = "xs")

        edge_checkbox.id = {"type": "edge_checkbox", "index": row["id"]}
        edge_checkbox.label = row["name"]
        edge_checkbox.checked = row["id"] in accessable_nodes
        edge_checkbox.disabled = row["id"] in cascade_accessable_nodes or project_data["status"]["stage"] != 2 or project_data["role"]["access_level"] < 2

        if "target" in element_data["state"]["selected"]["data"] and element_data["state"]["selected"]["data"]["target"] == row["id"]: edge_checkbox.style = {"background-color": "#e8f3fc"}

        edge_checkboxes.append(edge_checkbox)

    return edge_checkboxes

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "project"}, pathname = "/login")
    else:
        project_data = json.loads(session["project_data"])

        layout = dmc.AppShell(
            children = [
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dcc.Location(id = {"type": "redirect", "index": "project"}, pathname = "/project"),
                                dcc.Store(id = {"type": "init_store", "index": "project"}, storage_type = "memory"),
                                dcc.Store(id = "prev_action", storage_type = "memory", data = False),
                                dmc.Menu(
                                    children = [
                                        dmc.MenuTarget(dmc.Text("Проект")),
                                        dmc.MenuDropdown(
                                            children = [
                                                dmc.MenuItem(id = "project_settings", leftSection = DashIconify(icon = "mingcute:settings-3-line"), children = "Настройки"),
                                                dmc.MenuItem(id = "restore_initial_hierarchy", leftSection = DashIconify(icon = "mingcute:refresh-3-fill"), children = "Восстановить базовую иерархию"),
                                                dmc.MenuItem(children = dmc.Checkbox(id = {"type": "stage_completed", "index": "de_completed"}, label = "Оценка зависимостей завершена", checked = project_data["completed"]["de_completed"]), disabled = project_data["status"]["stage"] != 2 or project_data["role"]["access_level"] < 2),
                                                dmc.MenuItem(children = dmc.Checkbox(id = {"type": "stage_completed", "index": "ce_completed"}, label = "Сравнительная оценка завершена", checked = project_data["completed"]["ce_completed"]), disabled = project_data["status"]["stage"] != 3 or project_data["role"]["access_level"] < 2),
                                                dmc.MenuDivider(),
                                                dmc.MenuItem(id = "project_list", leftSection = DashIconify(icon = "mingcute:list-check-fill"), children = "Список проектов")
                                            ]
                                        )
                                    ],
                                    trigger="hover",
                                ),
                                dmc.Text(project_data["name"] + " (" + project_data["status"]["name"] + ")"),
                                dmc.Menu(
                                    children = [
                                        dmc.MenuTarget(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                        dmc.MenuDropdown(
                                            children = [
                                                dmc.MenuItem(id = {"type": "logout_button", "index": "project"}, leftSection = DashIconify(icon = "mingcute:exit-fill"), children = "Выйти", c = "red")
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
                dmc.AppShellNavbar("Navbar"),
                dmc.AppShellAside(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Group(
                                    children = [
                                        dmc.ActionIcon(id = {"type": "step_button", "index": "rollback"}, children = DashIconify(icon = "mingcute:corner-down-left-fill", width = 20), size = "input-sm", variant = "default", disabled = True),
                                        dmc.ActionIcon(id = {"type": "step_button", "index": "cancelrollback"}, children = DashIconify(icon = "mingcute:corner-down-right-fill", width = 20), size = "input-sm", variant = "default", disabled = True),
                                        dmc.ActionIcon(id = "locate", children = DashIconify(icon = "mingcute:location-line", width = 20), size = "input-sm", variant = "default"),
                                        dmc.ActionIcon(id = "add_node", children = DashIconify(icon = "mingcute:cross-line", width = 20), size = "input-sm", variant = "light", color = "green"),
                                        dmc.ActionIcon(id = "save_graph", children = DashIconify(icon = "mingcute:save-2-line", width = 20), size = "input-sm", variant = "light"),
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
                                                        dmc.Text("Название"),
                                                        dmc.Group(
                                                            children = [
                                                                dmc.TextInput(id = "name_input", disabled = bool(project_data["status"]["stage"] > 1) or bool(project_data["role"]["access_level"] < 3)),
                                                                dmc.Checkbox(id = "node_checkbox", size = 36, checked = True)
                                                            ],
                                                            justify = "space-around",
                                                            grow=True,
                                                            preventGrowOverflow=False,
                                                            id = "node_info"
                                                        ),
                                                    ],
                                                    p = "md",
                                                    gap = 5
                                                ),
                                                dmc.Accordion(
                                                    children = [
                                                        dmc.AccordionItem(
                                                            children = [
                                                                dmc.AccordionControl("Элементы нижнего уровня"),
                                                                dmc.AccordionPanel(dmc.Stack(id = "edge_checkboxes", children = [], gap = 0))
                                                            ],
                                                            value = "elements"
                                                        ),
                                                    ],
                                                    value="elements"
                                                )
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
                dmc.AppShellMain([
                    cyto.Cytoscape(
                        id="graph",
                        layout={"name": "preset"},
                        style={
                            "width": "100%",
                            "height": "calc(100vh - 30px)",
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
            header={"height": "30px"},
            navbar={"width": "15%"},
            aside={"width": "15%"},
        )
        layout = dmc.MantineProvider(layout)
        return layout


@dash.callback(
    output = {
        "current_node_id": Output("current_node_id", "data", allow_duplicate = True),
        "name_input_value": Output("name_input", "value"),
        "node_checkbox_checked": Output("node_checkbox", "checked"),
        "node_checkbox_disabled": Output("node_checkbox", "disabled"),
        "edge_checkboxes": Output("edge_checkboxes", "children"),
        "elements": Output("graph", "elements", allow_duplicate = True),
        "prev_action": Output("prev_action", "data", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "tapNodeData": Input("graph", "tapNodeData"),
            "tapEdgeData": Input("graph", "tapEdgeData"),
        }
    },
    prevent_initial_call = True
)
def SelectElement(input):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}

    project_data = json.loads(session["project_data"])
    element_data = json.loads(session["element_data"])

    
    if trigger["property"] == "tapNodeData":
        current_node = functions.GetElementById(input["tapNodeData"]["id"], element_data["elements"])
        element_data["state"]["selected"] = current_node
    else:
        current_node = functions.GetElementById(input["tapEdgeData"]["source"], element_data["elements"])
        element_data["state"]["selected"] = functions.GetElementById(input["tapEdgeData"]["id"], element_data["elements"])

    functions.ColorElements(element_data)
    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    output = {}
    output["current_node_id"] = current_node["data"]["id"]
    output["name_input_value"] = current_node["data"]["name"]
    output["node_checkbox_checked"] = current_node["data"]["id"] not in list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys())
    output["node_checkbox_disabled"] = current_node["data"]["id"] in element_data["state"]["cascade_deleted"].keys() or project_data["status"]["stage"] > 2 or (project_data["role"]["access_level"] < 3 and project_data["status"]["stage"] == 1) or (project_data["role"]["access_level"] < 2 and project_data["status"]["stage"] == 2)
    output["edge_checkboxes"] = GetEdgeCheckboxes(current_node, element_data, project_data)
    output["elements"] = element_data["elements"]
    output["prev_action"] = False

    return output


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Input("node_checkbox", "checked"),
    Input({"type": "edge_checkbox", "index": ALL}, "checked"),
    State("current_node_id", "data"),
    State("prev_action", "data"),
    prevent_initial_call = True
)
def CheckboxClick(node_checked, edge_checked, current_node_id, prev_action):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}
    element_data = json.loads(session["element_data"])

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
        session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return element_data["elements"], True


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Input("name_input", "value"),
    State("current_node_id", "data"),
    State("prev_action", "data"),
    prevent_initial_call = True
)
def ChangeNodeName(new_name, current_node_id, prev_action):
    element_data = json.loads(session["element_data"])

    if prev_action:
        current_node = functions.GetElementById(current_node_id, element_data["elements"])

        strlen = len(new_name)
        if strlen > 100: strlen = 100
        current_node["data"]["name"] = new_name[:strlen]

        functions.RefreshNodePositionsSizes(element_data["elements"])
        session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return element_data["elements"], True


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Input({"type": "step_button", "index": ALL}, "n_clicks"),
    prevent_initial_call = True
)
def StepButtons(clickdata):
    element_data = json.loads(session["element_data"])

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
    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return element_data["elements"], True


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("current_node_id", "data", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Input("add_node", "n_clicks"),
    State("current_node_id", "data"),
    prevent_initial_call = True
)
def AddNewNode(clickdata, current_node_id):
    element_data = json.loads(session["element_data"])

    node_object = functions.CreateNodeObject(functions.GetElementById(current_node_id, element_data["elements"]))
    functions.AddElement(node_object, element_data)
    functions.AddStep(node_object, element_data, "add")
    element_data["state"]["selected"] = node_object

    functions.ColorElements(element_data)
    functions.RefreshNodePositionsSizes(element_data["elements"])
    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return element_data["elements"], node_object["data"]["id"], True


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Input("save_graph", "n_clicks"),
    prevent_initial_call = True
)
def SaveGraph(clickdata):
    element_data = json.loads(session["element_data"])
    project_data = json.loads(session["project_data"])

    if project_data["status"]["stage"] == 1: functions.SaveInitialGraphToDB(element_data, project_data["id"])
    if project_data["status"]["stage"] == 2: functions.SaveEdgedataToDB(element_data, project_data["id"], current_user.userdata["id"])

    functions.ColorElements(element_data)
    functions.RefreshNodePositionsSizes(element_data["elements"])

    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return element_data["elements"], True


@dash.callback(
    output = {
        "placeholder_display": Output("toolbar_placeholder", "display"),
        "toolbar_display": Output("toolbar", "display"),
        "current_node_id": Output("current_node_id", "data", allow_duplicate = True),
        "rollback_disabled": Output({"type": "step_button", "index": "rollback"}, "disabled"),
        "cancelrollback_disabled": Output({"type": "step_button", "index": "cancelrollback"}, "disabled"),
        "addnode_disabled": Output("add_node", "disabled"),
        "save_graph": Output("save_graph", "disabled"),
        "hierarchyrestore_disabled": Output("restore_initial_hierarchy", "disabled"),
        "projectsettings_disabled": Output("project_settings", "disabled"),
    },
    inputs = {
        "input": {
            "elements": Input("graph", "elements"),
            "current_node_id": State("current_node_id", "data"),
        }
    },
    prevent_initial_call = True 
)
def ElementChangeProcessing(input):
    element_data = json.loads(session["element_data"])
    project_data = json.loads(session["project_data"])

    current_node = functions.GetElementById(input["current_node_id"], input["elements"])

    output = {}
    output["rollback_disabled"] = not bool(len(element_data["steps"]["history"]))
    output["cancelrollback_disabled"] = not bool(len(element_data["steps"]["canceled"]))
    output["addnode_disabled"] = not ((bool(element_data["state"]["selected"]) or not bool(len(element_data["elements"]))) and project_data["status"]["stage"] == 1 and project_data["role"]["access_level"] > 2)
    output["save_graph"] = (project_data["status"]["stage"] == 1 and project_data["role"]["access_level"] < 3) or (project_data["status"]["stage"] == 2 and project_data["role"]["access_level"] < 2) or project_data["status"]["stage"] > 2
    output["hierarchyrestore_disabled"] = not (project_data["status"]["stage"] == 2 and project_data["role"]["access_level"] > 1)
    output["projectsettings_disabled"] = not (project_data["role"]["access_level"] > 2)

    if current_node: 
        output["placeholder_display"] = "none"
        output["toolbar_display"] = "block"
        output["current_node_id"] = input["current_node_id"]
    else:
        output["placeholder_display"] = "block"
        output["toolbar_display"] = "none"
        output["current_node_id"] = None

    return output


@dash.callback(
    Output("graph", "elements"),
    Input({"type": "init_store", "index": "project"}, "data")
)
def InitGraph(init):
    element_data = json.loads(session["element_data"])
    if element_data["state"]["selected"]: 
        element_data["state"]["selected"] = functions.GetElementById(element_data["state"]["selected"]["data"]["id"], element_data["elements"])
        element_data["state"]["selected"]["classes"] = "default"
        element_data["state"]["selected"] = None

    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)
    return element_data["elements"]


@dash.callback(
    Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
    Output("current_node_id", "data", allow_duplicate = True),
    Input("project_list", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProjects(clickdata):
    SaveGraph(0)
    if clickdata: return "/projects", None


@dash.callback(
    Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
    Input("project_settings", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToSettings(clickdata):
    SaveGraph(0)
    if clickdata: return "/settings"


@dash.callback(
    Output("current_node_id", "data", allow_duplicate = True),
    Input("restore_initial_hierarchy", "n_clicks"),
    prevent_initial_call = True
)
def RestoreInitialHierarchy(clickdata):
    project_data = json.loads(session["project_data"])

    if functions.DiscardEdgedataChanges(project_data["id"], current_user.userdata["id"]):
        element_data = functions.GetElementData(project_data, current_user.userdata["id"])
        session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)
    else: raise PreventUpdate

    return None


@dash.callback(
    Output("graph", "elements", allow_duplicate = True),
    Input({"type": "stage_completed", "index": ALL}, "checked"),
    prevent_initial_call = True
)
def CompletedCheckboxes(checked):
    project_data = json.loads(session["project_data"])
    element_data = json.loads(session["element_data"])
    option = ctx.triggered_id["index"]
    checked = ctx.triggered[0]["value"]

    if functions.ChangeCompleteState(project_data["id"], current_user.userdata["id"], option, checked):
        project_data["completed"][option] = checked
        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)
    else: raise PreventUpdate()

    return element_data["elements"]