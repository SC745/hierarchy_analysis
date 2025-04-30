import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import pandas as pd

from flask import session
from flask_login import current_user

import functions
import json

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

role_data = functions.GetSelectData("role_select")

radiogroup_data = {
    "Большинство": {"description": "Связь остается если за нее проголосовало большинство экспертов", "value": 0.5},
    "Все": {"description": "Связь остается только если за нее проголосовали все эксперты", "value": 1},
    "Хотя бы один": {"description": "Связь остается если за нее проголосовал хотя бы один эксперт", "value": 0},
    "Настроить": {"description": "Установить долю голосов экспертов, необходимую для оставления связи", "value": None},
}

def MakeRadioCard(label, description):
    return dmc.RadioCard(
        children=[
            dmc.Group(
                children = [
                    dmc.RadioIndicator(),
                    dmc.Box(
                        children = [
                            dmc.Text(label, lh = "1.3", fz = "md", fw = "bold"),
                            dmc.Text(description, size = "sm", c = "dimmed"),
                            
                        ]
                    )
                ], 
                wrap="nowrap", 
                align="flex-start"
            ),
        ],
        withBorder = False,
        value = label,
        pb = "lg"
    )

def GetMergemethod(merge_coef):
    if merge_coef == 0.5: return "Большинство"
    if merge_coef == 1: return "Все"
    if merge_coef == 0: return "Хотя бы один"
    return "Настроить"


def layout():
    if not current_user.is_authenticated: return dcc.Location(id = {"type": "unauthentificated", "index": "settings"}, pathname = "/login")
    else:
        project_data = json.loads(session["project_data"])

        if project_data["role"]["access_level"] < 3: return dcc.Location(id = {"type": "access_denied", "index": "settings"}, pathname = "/project")

        layout = dmc.AppShell(
            children = [
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dcc.Location(id = {"type": "redirect", "index": "settings"}, pathname = "/settings"),
                                dmc.Menu(
                                    children = [
                                        dmc.MenuTarget(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                        dmc.MenuDropdown(
                                            children = [
                                                dmc.MenuItem(id = {"type": "logout_button", "index": "settings"}, leftSection = DashIconify(icon = "mingcute:exit-fill"), children = "Выйти", c = "red")
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
                        dmc.Box(children = dmc.Text("Настройки", fz = 24, fw = 500), p = "sm"),
                        dmc.Divider(),
                        dmc.Box(
                            children = [
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "project"},
                                    label = "Управление проектом",
                                    leftSection = DashIconify(icon = "mingcute:settings-3-line"),
                                    active = True
                                ),
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "users"},
                                    label = "Управление пользователями",
                                    leftSection = DashIconify(icon = "mingcute:user-1-line"),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "competence"},
                                    label = "Управление компетентностью",
                                    leftSection = DashIconify(icon = "mingcute:certificate-line"),
                                    active = False
                                ),
                            ],
                        ),
                        dmc.Flex(
                            children = [
                                dmc.Divider(),
                                dmc.NavLink(
                                    id = "to_project",
                                    label = "Вернуться к проекту",
                                    leftSection = DashIconify(icon = "mingcute:arrow-left-line"),
                                ),
                            ],
                            align = "flex-end",
                            direction = "column"
                        )
                    ]
                ),
                dmc.AppShellMain(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Text("Управление проектом", fz = 24, fw = 500, pb = "sm"),
                                dmc.Flex(
                                    children = [
                                        dmc.Box(
                                            children = [
                                                dmc.Text("Название", fz = "xl", fw = 500, pb = "xs"),
                                                dmc.TextInput(id = "project_name_input", value = project_data["name"], size = "md", w = 350),
                                            ]
                                        ),
                                        dmc.Button("Сохранить", id = "rename_project", size = "md", w = 150)
                                    ],
                                    gap = "md",
                                    align = "flex-end",
                                    pb = "xl"
                                ),
                                dmc.Box(
                                    children = [
                                        dmc.Text("Метод объединения иерархий", fz = "xl", fw = 500, pb = "sm"),
                                        dmc.RadioGroup(
                                            id = "mergemethod_radiogroup",
                                            value = GetMergemethod(project_data["merge_coef"]),
                                            children = [MakeRadioCard(key, radiogroup_data[key]["description"]) for key in radiogroup_data.keys()],
                                            w = 550
                                        ),
                                    ]
                                ),
                                dmc.Slider(
                                    id = "mergevalue_slider",
                                    value = project_data["merge_coef"],
                                    min = 0, 
                                    max = 1, 
                                    step = 0.01,
                                    marks= [
                                        {"value": 0, "label": "0"},
                                        {"value": 0.25, "label": "0.25"},
                                        {"value": 0.5, "label": "0.5"},
                                        {"value": 0.75, "label": "0.75"},
                                        {"value": 1, "label": "1"},
                                    ],
                                    disabled = bool(project_data["merge_coef"] in [0, 0.5, 1]),
                                    w = 400,
                                    ml = "xl",
                                    pb = 64
                                ),
                                dmc.Text("Прогресс по задачам", fz = "xl", fw = 500, pb = "sm"),
                                dmc.Table(
                                    id = "task_table",
                                    children = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"])),
                                    highlightOnHover = True,
                                    withTableBorder = True,
                                    withColumnBorders = True,
                                    withRowBorders = True,
                                    mb = "lg",
                                    fz = "md"
                                ),
                                dmc.Flex(
                                    children = [
                                        dmc.Box(
                                            children = [
                                                dmc.Text("Этап проекта", fz = "xl", fw = 500, pb = "xs"),
                                                dmc.Select(id = "status_select", data = functions.GetSelectData("status_select"), value = project_data["status"]["code"], disabled = True, size = "md", w = 350),
                                            ]
                                        ),
                                        dmc.Button("Предыдущий", id = {"type": "status_change", "index": "prev"}, disabled = bool(project_data["status"]["code"] == "initial"), size = "md", w = 200),
                                        dmc.Button("Следующий", id = {"type": "status_change", "index": "next"}, disabled = bool(project_data["status"]["code"] == "completed"), size = "md", w = 200),
                                    ],
                                    gap = "md",
                                    align = "flex-end",
                                    pb = "xl"
                                ),
                                dmc.Button("Удалить проект", id = "delete_project", disabled = bool(project_data["role"]["code"] != "owner"), size = "md", color = "red", w = 200),
                            ],
                            id = {"type": "settings_page", "index": "project"},
                            display = "block",
                            p = "sm",
                        ),
                        dmc.Box(
                            children = [
                                dmc.Text("Управление пользователями", fz = 24, fw = 500, pb = "sm"),
                                dmc.Flex(
                                    children = [
                                        dmc.Select(id = "user_select", data = functions.GetSelectData("user_select"), label = "Пользователь", searchable = True, size = "md", w = 350),
                                        dmc.Select(id = "role_select", data = role_data, disabled = True, label = "Роль", size = "md", w = 350),
                                        dmc.Button("Добавить", id = "add_user", disabled = True, size = "md", w = 150),
                                        dmc.Button("Изменить роль", id = "change_role", disabled = True, size = "md", w = 180),
                                    ],
                                    gap = "md",
                                    align = "flex-end",
                                    pb = "sm"
                                ),
                                dmc.Table(
                                    id = "user_table",
                                    children = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"])),
                                    highlightOnHover = True,
                                    withTableBorder = True,
                                    fz = "md"
                                )
                            ],
                            id = {"type": "settings_page", "index": "users"},
                            display = "none",
                            p = "sm",
                        ),
                        dmc.Box(
                            children = [
                                dmc.Text("Управление компетентностью", fz = 24, fw = 500, pb = "sm"),
                            ],
                            id = {"type": "settings_page", "index": "competence"},
                            display = "none",
                            p = "sm",
                        )
                    ],
                ),
                
            ],
            header={"height": "30px"},
            navbar={"width": "15%"},
        )
    
    layout = dmc.MantineProvider(layout)
    return layout


@dash.callback(
    output = {
        "navlink_selected": {
            "project": Output({"type": "settings_navlink", "index": "project"}, "active"),
            "users": Output({"type": "settings_navlink", "index": "users"}, "active"),
            "competence": Output({"type": "settings_navlink", "index": "competence"}, "active"),
        },
        "page_display": {
            "project": Output({"type": "settings_page", "index": "project"}, "display"),
            "users": Output({"type": "settings_page", "index": "users"}, "display"),
            "competence": Output({"type": "settings_page", "index": "competence"}, "display"),
        },
        "task_table": Output("task_table", "children", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "navlink_click": Input({"type": "settings_navlink", "index": ALL}, "n_clicks"),
        }
    },
    prevent_initial_call = True
)
def NavlinkClick(input):
    project_data = json.loads(session["project_data"])
    page_keys = ["project", "users", "competence"]

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
    output["task_table"] = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))

    return output


@dash.callback(
    Output("mergevalue_slider", "value"),
    Output("mergevalue_slider", "disabled"),
    Input("mergemethod_radiogroup", "value"),
    State("mergevalue_slider", "value"),
    prevent_initial_call = True
)
def MergemethodChoice(method, slider_value):
    slider_disabled = bool(method != "Настроить")
    if method != "Настроить": slider_value = radiogroup_data[method]["value"]

    return slider_value, slider_disabled


@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Input("mergevalue_slider", "value"),
    running = [Output("mergevalue_slider", "disabled"), True],
    prevent_initial_call = True
)
def MergevalueChoice(slider_value):
    project_data = json.loads(session["project_data"])
    if functions.UpdateMergevalue(slider_value, project_data["id"]):
        project_data["merge_coef"] = slider_value
        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)

    raise PreventUpdate


@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Input("rename_project", "n_clicks"),
    State("project_name_input", "value"),
    prevent_initial_call = True
)
def RenameProject(clickdata, project_name):
    project_data = json.loads(session["project_data"])
    if functions.UpdateProjectName(project_name, project_data["id"]):
        project_data["name"] = project_name
        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)

    raise PreventUpdate


@dash.callback(
    Output("status_select", "value", allow_duplicate = True),
    Output("task_table", "children"),
    Input({"type": "status_change", "index": ALL}, "n_clicks"),
    State("status_select", "value"),
    State("status_select", "data"),
    prevent_initial_call = True
)
def ChangeProjectStatus(clickdata, old_status, select_data):
    project_data = json.loads(session["project_data"])
    select_data = pd.DataFrame(select_data)

    direction = 0
    if ctx.triggered_id["index"] == "prev": direction = -1
    if ctx.triggered_id["index"] == "next": direction = 1

    new_status_code = select_data.loc[select_data.loc[select_data["value"] == old_status].index[0] + direction, "value"]
    new_status = functions.GetStatusByCode(new_status_code)
    if functions.UpdateProjectStatus(new_status, project_data):
        project_data["status"] = new_status
        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)
    else: raise PreventUpdate

    task_table_content = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))

    return new_status_code, task_table_content


@dash.callback(
    Output({"type": "status_change", "index": "prev"}, "disabled"),
    Output({"type": "status_change", "index": "next"}, "disabled"),
    Input("status_select", "value"),
    prevent_initial_call = True
)
def StatusButtonState(project_status):
    prev_status_disabled = bool(project_status == "initial")
    next_status_disabled = bool(project_status == "completed")

    return prev_status_disabled, next_status_disabled


@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Input("delete_project", "n_clicks"),
    prevent_initial_call = True
)
def DeleteProject(clickdata):
    project_data = json.loads(session["project_data"])

    if functions.DeleteProject(project_data["id"]):
        project_data = {}
        session["project_data"] = json.dumps(project_data, cls = functions.NpEncoder)
        return "/projects"
    
    raise PreventUpdate


@dash.callback(
    Output("role_select", "value"),
    Output("role_select", "data"),
    Output("role_select", "disabled"),
    Output("add_user", "disabled"),
    Output("change_role", "disabled"),
    Input("user_select", "value"),
    Input("role_select", "value"),
    State("role_select", "data"),
    prevent_initial_call = True
)
def SelectUser(user_login, role_code, role_select_data):
    project_data = json.loads(session["project_data"])

    user_role = functions.GetUserRole(user_login, project_data["id"])
    if user_role:
        if ctx.triggered_id != "role_select": role_code = user_role["role_code"]
        role_select_disabled = bool(user_role["access_level"] >= project_data["role"]["access_level"])
    else: 
        if ctx.triggered_id == "user_select": role_code = None
        role_select_disabled = False

    if role_select_disabled: 
        role_select_data = role_data
    else:
        role_select_data = pd.DataFrame(role_data)
        role_select_data = role_select_data.loc[role_select_data["access_level"] < project_data["role"]["access_level"]].to_dict("records")
        
    add_user_disabled = not bool(role_code) or bool(user_role)
    change_role_disabled = not (bool(role_code) and not role_select_disabled and bool(user_role))

    return role_code, role_select_data, role_select_disabled, add_user_disabled, change_role_disabled


@dash.callback(
    Output("user_table", "children", allow_duplicate = True),
    Output("role_select", "value", allow_duplicate = True),
    Input("add_user", "n_clicks"),
    State("user_select", "value"),
    State("role_select", "value"),
    prevent_initial_call = True
)
def AddUser(clickdata, user_login, role_code):
    project_data = json.loads(session["project_data"])
    res = functions.InsertUserdata(user_login, role_code, project_data["id"])
    if project_data["status"]["stage"] > 1 and res:
        res = functions.InsertUserEdgedata(user_login, project_data["id"])
        if project_data["status"]["stage"] > 2 and res:
            res = functions.InsertUserCompdata(user_login, project_data)
                
    if res: 
        table_content = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"]))
        return table_content, role_code

    raise PreventUpdate


@dash.callback(
    Output("user_table", "children", allow_duplicate = True),
    Input("change_role", "n_clicks"),
    State("user_select", "value"),
    State("role_select", "value"),
    prevent_initial_call = True
)
def ChangeRole(clickdata, user_login, role_code):
    project_data = json.loads(session["project_data"])
    prev_role_code = functions.GetUserRole(user_login, project_data["id"])["role_code"]

    res = functions.UpdateUserRole(user_login, role_code, project_data["id"])
    if project_data["status"]["stage"] > 1 and "spectator" in [prev_role_code, role_code] and res:
        res = functions.InsertUserEdgedata(user_login, project_data["id"])
        if project_data["status"]["stage"] > 2 and res:
            res = functions.InsertUserCompdata(user_login, project_data)

    if res: 
        table_content = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"]))
        return table_content

    raise PreventUpdate


@dash.callback(
    Output("user_table", "children", allow_duplicate = True),
    Output("role_select", "value", allow_duplicate = True),
    Input({"type": "delete_button", "index": ALL}, "n_clicks"),
    State("user_select", "value"),
    State("role_select", "value"),
    prevent_initial_call = True
)
def DeleteUser(clickdata, user_login, role_code):
    if ctx.triggered[0]["value"]:
        project_data = json.loads(session["project_data"])
        user_login = ctx.triggered_id["index"]

        res = functions.DeleteUserdata(user_login, project_data["id"])
        if project_data["status"]["stage"] > 1 and res:
            res = functions.DeleteUserEdgedata(user_login, project_data["id"])
            if project_data["status"]["stage"] > 2 and res:
                res = functions.DeleteUserCompdata(user_login, project_data["id"])

        if res: 
            table_content = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"]))
            return table_content, role_code

    raise PreventUpdate


@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Input("to_project", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProject(clickdata):
    project_data = json.loads(session["project_data"])

    element_data = functions.GetElementData(project_data, current_user.userdata["id"])
    session["element_data"] = json.dumps(element_data, cls = functions.NpEncoder)

    if clickdata: return "/project"