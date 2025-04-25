import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate

from flask import session
from flask_login import current_user

import functions
import json

import dash_cytoscape as cyto


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def GetNodeInfo(node, element_data):
    if node["data"]["id"] in element_data["state"]["cascade_deleted"].keys():
        checked_state = False
        disabled_state = True
    elif node["data"]["id"] in element_data["state"]["manually_deleted"].keys():
        checked_state = False
        disabled_state = False
    else:
        checked_state = True
        disabled_state = False

    node_info = []
    node_info.append(dmc.TextInput(id = "name_input", value = node["data"]["name"]))
    node_info.append(dmc.Checkbox(id = "node_checkbox", size = 36, checked = checked_state, disabled = disabled_state))

    return node_info

def GetEdgeCheckboxes(source_node, element_data):
    element_data["state"]
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
        edge_checkbox.disabled = row["id"] in cascade_accessable_nodes
        if "target" in element_data["state"]["selected"]["data"] and element_data["state"]["selected"]["data"]["target"] == row["id"]: edge_checkbox.style = {"background-color": "#e8f3fc"}

        edge_checkboxes.append(edge_checkbox)

    return edge_checkboxes

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "project"}, pathname = "/login")
    else:
        project_data = json.loads(session["project_data"])
        user_data = current_user.userdata

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
                                                dmc.MenuItem(id = "restore_initial_hierarchy", leftSection = DashIconify(icon = "mingcute:refresh-3-fill"), children = "Восстановить исходную иерархию", disabled = True),
                                                dmc.MenuDivider(),
                                                dmc.MenuItem(id = "project_list", leftSection = DashIconify(icon = "mingcute:list-check-fill"), children = "Список проектов")
                                            ]
                                        )
                                    ],
                                    trigger="hover",
                                ),
                                dmc.Text(project_data["name"] + " (" + project_data["status"] + ")"),
                                dmc.Menu(
                                    children = [
                                        dmc.MenuTarget(dmc.Text(functions.GetShortUsername(user_data["name"]))),
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
                                        dmc.ActionIcon(id = {"type": "step_button", "index": "rollback"}, children = DashIconify(icon = "mingcute:corner-down-left-fill", width=20), size = "input-sm", variant = "default", disabled = True),
                                        dmc.ActionIcon(id = {"type": "step_button", "index": "cancelrollback"}, children = DashIconify(icon = "mingcute:corner-down-right-fill", width=20), size = "input-sm", variant = "default", disabled = True),
                                        dmc.ActionIcon(id = "locate", children = DashIconify(icon = "mingcute:location-line", width=20), size = "input-sm", variant = "default"),
                                        dmc.ActionIcon(id = "add_node", children = DashIconify(icon = "mingcute:cross-line", width=20), size = "input-sm", variant = "light", color = "green"),
                                        dmc.ActionIcon(id = "save_graph", children = DashIconify(icon = "mingcute:save-2-line", width=20), size = "input-sm", variant = "light"),
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
                                                                dmc.TextInput(id = "name_input"),
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
    Output("current_node_id", "data", allow_duplicate = True),
    Output("node_info", "children"),
    Output("edge_checkboxes", "children"),
    Output("graph", "elements", allow_duplicate = True),
    Output("prev_action", "data", allow_duplicate = True),
    Input("graph", "tapNodeData"),
    Input("graph", "tapEdgeData"),
    prevent_initial_call = True
)
def SelectElement(tapNodeData, tapEdgeData):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}

    element_data = json.loads(session["element_data"])

    if trigger["property"] == "tapNodeData":
        current_node = functions.GetElementById(tapNodeData["id"], element_data["elements"])
        element_data["state"]["selected"] = current_node
    else:
        current_node = functions.GetElementById(tapEdgeData["source"], element_data["elements"])
        element_data["state"]["selected"] = functions.GetElementById(tapEdgeData["id"], element_data["elements"])

    node_info = GetNodeInfo(current_node, element_data)
    edge_checkboxes = GetEdgeCheckboxes(current_node, element_data)

    functions.ColorElements(element_data)
    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return current_node["data"]["id"], node_info, edge_checkboxes, element_data["elements"], False


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
            functions.AddElement(edge_object, element_data["elements"])
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

    functions.SaveGraphToDB(project_data["id"], element_data)

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
    current_node = functions.GetElementById(input["current_node_id"], input["elements"])

    element_data = json.loads(session["element_data"])

    output = {}
    output["rollback_disabled"] = not bool(len(element_data["steps"]["history"]))
    output["cancelrollback_disabled"] = not bool(len(element_data["steps"]["canceled"]))
    output["addnode_disabled"] = not (bool(element_data["state"]["selected"]) or not bool(len(element_data["elements"])))

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
    return element_data["elements"]


@dash.callback(
    Output({"type": "redirect", "index": "project"}, "pathname", allow_duplicate = True),
    Output("current_node_id", "data", allow_duplicate = True),
    Input("project_list", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProjects(clickdata):
    #session.clear()
    if clickdata: return "/projects", None