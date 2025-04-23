import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, dcc, ALL, ctx
from dash.exceptions import PreventUpdate
import functions

from flask import session
from flask_login import logout_user, current_user


import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


def CreateProjectTable(user_id):
    columns = ["Название", "Состояние", "Роль в проекте", "Ссылка"]
    project_data = functions.GetUserProjects(user_id)

    head = dmc.TableThead(dmc.TableTr([dmc.TableTh(column) for column in columns]))
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in project_data])
    table = dmc.Table([head, body], id = "project_table")

    return table

def layout():
    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "redirect", "index": "unauthentificated_projects"}, pathname = "/login")

    return dmc.AppShell(
        children = [
            dmc.AppShellHeader(
                children = [
                    dmc.Button("logout", id = "logout")
                ]
            ),
            dmc.AppShellMain(
                children = [
                    dmc.Stack(
                        children = [
                            dmc.Text("Проекты"),
                            CreateProjectTable(current_user.userdata["id"]),
                            dcc.Location(id = {"type": "redirect", "index": "projects"}, pathname = "/projects")
                        ]
                    )
                ]
            ),
        ],

        header={"height": "30px"},
        id="appshell123",
    )

@dash.callback(
    output = {
        "redirect_trigger": Output({"type": "redirect", "index": "projects"}, "pathname"),
    },
    inputs = {
        "input": {
            "clickdata": Input({"type": "project_button", "index": ALL}, "n_clicks"),
            "logout": Input("logout", "n_clicks"),
            "project_table": State("project_table", "data"),
        }
    },
    prevent_initial_call = True
)
def ProjectChoice(input):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}

    output = {}
    if trigger["id"] == "logout":
        logout_user()
        output["redirect_trigger"] = "/login"
    else:
        project_data = functions.GetUserProjectById(current_user.userdata["id"], ctx.triggered_id["index"])

        elements = functions.GetHierarchyPreset(*functions.GetProjectDfs(project_data["id"], None))

        state = {}
        state["manually_deleted"] = {}
        state["cascade_deleted"] = {}
        state["added"] = {}
        state["selected"] = None

        steps = {}
        steps["history"] = []
        steps["canceled"] = []

        element_data = {}
        element_data["list"] = elements
        element_data["state"] = state
        element_data["steps"] = steps

        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)
        session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

        output["redirect_trigger"] = "/project"
    return output


