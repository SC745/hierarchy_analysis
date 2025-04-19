import dash
import dash_mantine_components as dmc
from dash import Dash, Input, Output, State, _dash_renderer, ctx, ALL
from dash_iconify import DashIconify
import dash_cytoscape as cyto
import functions
import page_content


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__, path='/')

project_data = {
    "id": 1,
    "name": "Тест 1",
    "status_id": 1
}

user_data = {
    "id": 1,
    "name": "Финоженков Александр Сергеевич",
    "login": "a.finozhenkov",
}

element_data = {
    "list": functions.GetHierarchyPreset(*functions.GetProjectDfs(project_data["id"], None, True)),
    "state": {
        "manually_deleted": {},
        "cascade_deleted": {},
        "added": {},
        "selected": None
    },
    "steps": {
        "history": [],
        "canceled": []
    }
}

def GetToolbar(input, trigger, element_data):

    current_node = functions.GetElementById(input["toolbar"][1]["props"]["id"]["index"], element_data["list"])

    #Нажатия на элементы графа
    if trigger["property"] in ["tapNodeData", "tapEdgeData"]:
        if trigger["property"] == "tapNodeData":
            current_node = functions.GetElementById(input["tapNodeData"]["id"], element_data["list"])
            element_data["state"]["selected"] = current_node
        else:
            current_node = functions.GetElementById(input["tapEdgeData"]["source"], element_data["list"])
            element_data["state"]["selected"] = functions.GetElementById(input["tapEdgeData"]["id"], element_data["list"])

    #Нажатие на чекбоксы для удаления/добавления элементов графа
    if trigger["property"] == "checked":
        if trigger["id"] != "node_checkbox": element = functions.GetEdge(current_node["data"]["id"], trigger["id"]["index"], element_data["list"])
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
            functions.AddElement(edge_object, element_data["list"])
            functions.AddStep(edge_object, element_data, "add")

    if trigger["property"] == "n_clicks":
        if trigger["id"]["index"] == "add":
            node_object = functions.CreateNodeObject(current_node)
            functions.AddElement(node_object, element_data)
            functions.AddStep(node_object, element_data, "add")
            current_node = node_object
            element_data["state"]["selected"] = current_node

        if trigger["id"]["index"] == "save":
            functions.SaveGraphToDB(project_data["id"], element_data)

        if trigger["id"]["index"] in ["rollback", "cancelrollback"]:
            if trigger["id"]["index"] == "rollback": 
                used_list = "history"
                store_list = "canceled"
            else: 
                used_list = "canceled"
                store_list = "history"

            if len(element_data["steps"][used_list]) > 0:
                action = element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["action"]
                element = element_data["steps"][used_list][len(element_data["steps"][used_list]) - 1]["element"]

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
            
    #Изменение названия вершины
    if trigger["id"] == "name_input": 
        strlen = len(trigger["value"])
        if strlen > 100: strlen = 100
        current_node["data"]["name"] = trigger["value"][:strlen]

    #Смена с состояния когда вершина не выбрана
    if element_data["state"]["selected"]:
        input["toolbar"][0]["props"]["style"]["display"] = "none"
        input["toolbar"][1]["props"]["style"]["display"] = "block"

        #Индекс вершины
        input["toolbar"][1]["props"]["id"]["index"] = current_node["data"]["id"]

        #Имя вершины в поле ввода
        input["toolbar"][1]["props"]["children"][0]["props"]["children"][0]["props"]["children"][1]["props"]["children"][0]["props"]["value"] = current_node["data"]["name"]

        #Чекбоксы ребер и вершины
        node_checkbox, edge_checkboxes = functions.GetToolbarCheckboxes(current_node, element_data)
        input["toolbar"][1]["props"]["children"][0]["props"]["children"][1]["props"]["children"][0]["props"]["children"][1]["props"]["children"] = edge_checkboxes
        input["toolbar"][1]["props"]["children"][0]["props"]["children"][0]["props"]["children"][1]["props"]["children"][1] = node_checkbox

    else:
        input["toolbar"][0]["props"]["style"]["display"] = "block"
        input["toolbar"][1]["props"]["style"]["display"] = "none"

    button_state = {}
    button_state["rollback"] = not bool(len(element_data["steps"]["history"]))
    button_state["cancelrollback"] = not bool(len(element_data["steps"]["canceled"]))

    output = {}
    output["elements"] = element_data["list"]
    output["toolbar"] = input["toolbar"]
    output["button_state"] = button_state

    functions.ColorElements(element_data)
    functions.RefreshNodePositionsSizes(element_data["list"])

    """print("Manually deleted:")
    for key in element_data["state"]["manually_deleted"].keys(): print(element_data["state"]["manually_deleted"][key])
    print("Cascade deleted:")
    for key in element_data["state"]["cascade_deleted"].keys(): print(element_data["state"]["cascade_deleted"][key])
    print("Added:")
    for key in element_data["state"]["added"].keys(): print(element_data["state"]["added"][key])
    print("Selected:")
    print(element_data["state"]["selected"])
    print("---------------------------------------")"""

    return output


layout = dmc.AppShell(
    [
        dmc.AppShellHeader("Header"),
        dmc.AppShellNavbar("Navbar"),
        dmc.AppShellAside(
            id = "aside",
            children = [
                dmc.Box(
                    children = [
                        dmc.Group(
                            children = [
                                dmc.ActionIcon(id = {"type": "action_button", "index": "rollback"}, children = DashIconify(icon = "mingcute:corner-down-left-fill", width=20), size = "input-sm", variant = "default", disabled = True),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "cancelrollback"}, children = DashIconify(icon = "mingcute:corner-down-right-fill", width=20), size = "input-sm", variant = "default", disabled = True),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "locate"}, children = DashIconify(icon = "mingcute:location-line", width=20), size = "input-sm", variant = "default"),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "add"}, children = DashIconify(icon = "mingcute:cross-line", width=20), size = "input-sm", variant = "light", color = "green"),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "save"}, children = DashIconify(icon = "mingcute:save-2-line", width=20), size = "input-sm", variant = "light"),
                            ],
                            grow=True,
                            preventGrowOverflow=False,
                            p = "md"
                        ),
                        dmc.Divider()
                    ]
                ),
                dmc.Box(
                    children = page_content.toolbar,
                    id = "toolbar_data"
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
                elements = element_data["list"]
            )
        ]),
    ],
    header={"height": "30px"},
    navbar={"width": "15%"},
    aside={"width": "15%"},
    id="appshell",
)

layout = dmc.MantineProvider(layout)

@dash.callback(
    output = {
        "toolbar": Output("toolbar_data", "children"),
        "elements": Output("graph", "elements"),
        "button_state": {
            "rollback": Output({"type": "action_button", "index": "rollback"}, "disabled"),
            "cancelrollback": Output({"type": "action_button", "index": "cancelrollback"}, "disabled"),
        }
    },
    inputs = {
        "input": {
            "button_clickdata": Input({"type": "action_button", "index": ALL}, "n_clicks"),
            "node_checkbox": Input("node_checkbox", "checked"),
            "edge_checkboxes": Input({"type": "edge_checkbox", "index": ALL}, "checked"),
            "name_input": Input("name_input", "value"),
            "tapNodeData": Input("graph", "tapNodeData"),
            "tapEdgeData": Input("graph", "tapEdgeData"),
            "toolbar": State("toolbar_data", "children")
        },
    },
    prevent_initial_call = True,
    allow_duplicate = True
)
def ShowNodeToolbar(input):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}
    output = GetToolbar(input, trigger, element_data)

    return output

        


