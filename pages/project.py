import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc

from flask import session
from flask_login import current_user

import functions
import page_content
import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "redirect", "index": "unauthentificated_project"}, pathname = "/login")
    else:
        layout = page_content.project_layout
        layout = dmc.MantineProvider(layout)
        return layout

@dash.callback(
    output = {
        "toolbar": Output("toolbar_data", "children"),
        "elements": Output("graph", "elements"),
        "button_state": {
            "rollback": Output({"type": "action_button", "index": "rollback"}, "disabled"),
            "cancelrollback": Output({"type": "action_button", "index": "cancelrollback"}, "disabled"),
            "add": Output({"type": "action_button", "index": "add"}, "disabled"),
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
    allow_duplicate = True
)
def ShowNodeToolbar(input):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}

    project_data = json.loads(session["project_data"])
    element_data = json.loads(session["element_data"])
    
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

        

        if element_data["state"]["selected"] == current_node: element_data["state"]["selected"]["data"]["name"] = trigger["value"][:strlen]
        current_node["data"]["name"] = trigger["value"][:strlen]

    #Заполнение
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

        #Индекс вершины
        input["toolbar"][1]["props"]["id"]["index"] = ""

    button_state = {}
    button_state["rollback"] = not bool(len(element_data["steps"]["history"]))
    button_state["cancelrollback"] = not bool(len(element_data["steps"]["canceled"]))
    button_state["add"] = not (bool(element_data["state"]["selected"]) or not bool(len(element_data["list"])))

    output = {}
    output["elements"] = element_data["list"]
    output["toolbar"] = input["toolbar"]
    output["button_state"] = button_state

    functions.ColorElements(element_data)
    functions.RefreshNodePositionsSizes(element_data["list"])

    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    return output

        


