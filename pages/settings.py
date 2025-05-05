import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc, no_update
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import pandas as pd

from flask import session
from flask_login import current_user, logout_user

import functions
import json

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

role_data = functions.GetSelectData("role_select")

merge_radiogroupdata = {
    "Большинство": {"description": "Связь остается если за нее проголосовало большинство экспертов", "value": 0.5},
    "Все": {"description": "Связь остается только если за нее проголосовали все эксперты", "value": 1},
    "Хотя бы один": {"description": "Связь остается если за нее проголосовал хотя бы один эксперт", "value": 0},
    "Настроить": {"description": "Установить долю голосов экспертов, необходимую для оставления связи", "value": None},
}

competence_radiogroupdata = {
    "Постоянный": {"description": "Компетентность эксперта при оценке связей одинакова"},
    "Настраиваемый": {"description": "Установить компетентность эксперта для оценки каждой связи"},
}

groupmanage_radiogroupdata = {
    "Список групп": {"description": "Добавить или удалить группы из проекта"},
    "Состав групп": {"description": "Редактировать состав групп"},
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
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    #page_settings = session.pop("page_settings", None)
    page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)

    #Очистка данных
    #project_data = session.pop("project_data", None)
    #element_data = session.pop("element_data", None)
    #comp_data = session.pop("comp_data", None)
    
    if not current_user.is_authenticated: 
        return dcc.Location(id = {"type": "unauthentificated", "index": "settings"}, pathname = "/login")
    elif not "page_settings" in session:
        return dcc.Location(id = {"type": "redirect", "index": "project"}, pathname = "/project")
    else:
        page_settings = json.loads(session["page_settings"])
        project_data = functions.GetProjectData(current_user.userdata["id"], page_settings["project_id"])

        if project_data["role"]["access_level"] < 3: 
            return dcc.Location(id = {"type": "access_denied", "index": "settings"}, pathname = "/project")
        
        project_data_store = json.dumps(project_data, cls = functions.NpEncoder)

        layout = dmc.AppShell(
            children = [
                dcc.Location(id = {"type": "redirect", "index": "settings"}, pathname = "/settings"),
                dcc.Store(id = "project_data_store", storage_type='session', data=project_data_store),
                dcc.Store(id = "element_data_store", storage_type='session', clear_data=True),
                dcc.Store(id = "comp_data_store", storage_type='session', clear_data=True),
                #dcc.Interval(id={'type': 'load_interval', 'index': 'settings'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
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
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "groups"},
                                    label = "Управление группами",
                                    leftSection = DashIconify(icon = "mingcute:group-line"),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = "settings_to_project",
                                    label = "Вернуться к проекту",
                                    leftSection = DashIconify(icon = "mingcute:arrow-left-line"),
                                ),
                            ],
                        ),
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
                                            children = [MakeRadioCard(key, merge_radiogroupdata[key]["description"]) for key in merge_radiogroupdata.keys()],
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
                                        dmc.Select(id = "user_select", data = functions.GetSelectData("user_select"), label = "Пользователь", searchable = True, clearable = False, size = "md", w = 350),
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
                                    children = functions.CreateTableContent(["Имя", "Роль", "Удалить пользователя"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"])),
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
                                dmc.Flex(
                                    children = [
                                        dmc.Text("Управление компетентностью", fz = 24, fw = 500, pb = "sm"),
                                        dmc.ActionIcon(id = "save_project_competence", children = DashIconify(icon = "mingcute:save-2-line", width = 26), disabled = not project_data["const_comp"], size = "input-md"),
                                    ],
                                    align = "flex-end",
                                    justify = "space-between"
                                ),
                                dmc.Box(
                                    children = [
                                        dmc.Text("Тип компетентности", fz = "xl", fw = 500, pb = "sm"),
                                        dmc.RadioGroup(
                                            id = "competence_radiogroup",
                                            value = "Постоянный" if project_data["const_comp"] else "Настраиваемый",
                                            children = [MakeRadioCard(key, competence_radiogroupdata[key]["description"]) for key in competence_radiogroupdata.keys()],
                                            w = 550
                                        ),
                                    ]
                                ),
                                dmc.Text("Настройка постоянной компетентности пользователей" if project_data["const_comp"] else "Настройка компетентности пользователя при оценке связи", fz = "xl", fw = 500, pb = "xs", id = "competence_type_message"),
                                dmc.Box(
                                    children = [
                                        dmc.Checkbox(id = "group_checkbox_project", label = "Использовать группы", size = "md", fw = 500, pb = "xs"),
                                        dmc.Table(
                                            id = "project_competence_table",
                                            children = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"])),
                                            highlightOnHover = True,
                                            withTableBorder = True,
                                            fz = "md"
                                        )
                                    ],
                                    id = "user_competence_container",
                                    display = "block" if project_data["const_comp"] else "none"
                                ),
                                dmc.Box(
                                    children = [
                                        dmc.Text("Настройка данного типа недоступна на этапе построения базовой иерархии", id = "edge_competence_message", fz = "lg", fw = 500, pb = "xs", display = "block" if project_data["status"]["code"] == "initial" else "none"),
                                        dmc.Box(
                                            children = [
                                                dmc.Checkbox(id = "group_checkbox_edge", label = "Использовать группы", size = "md", fw = 500, pb = "xs"),
                                                dmc.Flex(
                                                    children = [
                                                        dmc.Select(id = "competence_select", data = functions.GetSelectData("competence_select", project_data["id"]), label = "Пользователь", searchable = True, clearable = False, size = "md", w = 350),
                                                        dmc.Select(id = "source_node_select", data = functions.GetSelectData("source_node_select", project_data["id"]), label = "Группа критериев", searchable = True, clearable = False, size = "md", w = 350),
                                                        dmc.Button("Сохранить", id = "save_edge_competence", disabled = True, size = "md", w = 150)
                                                    ],
                                                    gap = "md",
                                                    align = "flex-end",
                                                    pb = "sm"
                                                ),
                                                dmc.Table(
                                                    id = "edge_competence_table",
                                                    children = functions.CreateTableContent(["Критерий", "Компетентность"], []),
                                                    highlightOnHover = True,
                                                    withTableBorder = True,
                                                    fz = "md"
                                                ),
                                            ],
                                            id = "edge_competence_data",
                                            display = "block" if project_data["status"]["code"] != "initial" else "none"
                                        )
                                    ],
                                    id = "edge_competence_container",
                                    display = "block" if not project_data["const_comp"] else "none"
                                )
                            ],
                            id = {"type": "settings_page", "index": "competence"},
                            display = "none",
                            p = "sm",
                        ),
                        dmc.Box(
                            children = [
                                dmc.Text("Управление группами", fz = 24, fw = 500, pb = "sm"),
                                dmc.Box(
                                    children = [
                                        dmc.Tabs(
                                            children = [
                                                dmc.TabsList(
                                                    children = [
                                                        dmc.TabsTab("Список групп", value = "group_list", pb = "sm", fz = "lg", fw = 500),
                                                        dmc.TabsTab("Состав групп", value = "group_users", pb = "sm", fz = "lg", fw = 500),
                                                    ],
                                                ),
                                                dmc.TabsPanel(
                                                    children = [
                                                        dmc.Flex(
                                                            children = [
                                                                dmc.Select(id = {"type": "grouplist_select", "index": "group_list"}, data = functions.GetSelectData("grouplist_select", project_data["id"]), clearable = True, label = "Группа", size = "md", w = 350),
                                                                dmc.TextInput(id = "groupname_input", label = "Название группы", size = "md", debounce = 500, w = 350),
                                                                dmc.Button(children = "Создать", id = "edit_group_button", disabled = True, size = "md", w = 180)
                                                            ],
                                                            gap = "md",
                                                            align = "flex-end",
                                                            pb = "sm"
                                                        ),
                                                        dmc.Table(
                                                            id = "group_list_table",
                                                            children = functions.CreateTableContent(["Группа", "Удалить группу"], functions.GetGroupListTableData(project_data["id"])),
                                                            highlightOnHover = True,
                                                            withTableBorder = True,
                                                            fz = "md"
                                                        )
                                                    ], 
                                                    value = "group_list",
                                                    pt = "sm"
                                                ),
                                                dmc.TabsPanel(
                                                    children = [
                                                        dmc.Flex(
                                                            children = [
                                                                dmc.Select(id = {"type": "grouplist_select", "index": "group_users"}, data = functions.GetSelectData("grouplist_select", project_data["id"]), label = "Группа", size = "md", w = 350),
                                                                dmc.Select(id = "groupuser_select", data = functions.GetSelectData("competence_select", project_data["id"]), label = "Пользователь", size = "md", w = 350),
                                                                dmc.Button(children = "Добавить", id = "groupadd_user", disabled = True, size = "md", w = 150)
                                                            ],
                                                            gap = "md",
                                                            align = "flex-end",
                                                            pb = "sm"
                                                        ),
                                                        dmc.Table(
                                                            id = "group_users_table",
                                                            children = functions.CreateTableContent(["Пользователь", "Удалить из группы"], functions.GetGroupUsersTableData(project_data["id"])),
                                                            highlightOnHover = True,
                                                            withTableBorder = True,
                                                            fz = "md"
                                                        )
                                                    ], 
                                                    value = "group_users",
                                                    pt = "sm"
                                                ),
                                            ],
                                            orientation = "horizontal", 
                                            variant = "default",
                                            value = "group_list"
                                        ),
                                    ]
                                ),
                            ],
                            id = {"type": "settings_page", "index": "groups"},
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




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Навигация -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": "settings"}, "n_clicks"),
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
            "project": Output({"type": "settings_navlink", "index": "project"}, "active"),
            "users": Output({"type": "settings_navlink", "index": "users"}, "active"),
            "competence": Output({"type": "settings_navlink", "index": "competence"}, "active"),
            "groups": Output({"type": "settings_navlink", "index": "groups"}, "active"),
        },
        "page_display": {
            "project": Output({"type": "settings_page", "index": "project"}, "display"),
            "users": Output({"type": "settings_page", "index": "users"}, "display"),
            "competence": Output({"type": "settings_page", "index": "competence"}, "display"),
            "groups": Output({"type": "settings_page", "index": "groups"}, "display"),
        }
    },
    inputs = {
        "input": {
            "navlink_click": Input({"type": "settings_navlink", "index": ALL}, "n_clicks"),
            "page_ids": Input({"type": "settings_page", "index": ALL}, "id"),
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

    return output

@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Input("settings_to_project", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProject(clickdata):
    if clickdata is None:
        raise PreventUpdate
    else:
        page_settings = json.loads(session["page_settings"])
        page_project = {}
        page_project["project_id"] = page_settings["project_id"]
        session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)
    
        return "/project"




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление проектом ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    Output("mergevalue_slider", "value"),
    Output("mergevalue_slider", "disabled"),
    Input("mergemethod_radiogroup", "value"),
    State("mergevalue_slider", "value"),
    prevent_initial_call = True
)
def MergemethodChoice(method, slider_value):
    slider_disabled = bool(method != "Настроить")
    if method != "Настроить": slider_value = merge_radiogroupdata[method]["value"]

    return slider_value, slider_disabled

@dash.callback(
    Output("project_data_store", "data", allow_duplicate = True),
    Input("mergevalue_slider", "value"),
    State("project_data_store", "data"),
    running = [Output("mergevalue_slider", "disabled"), True],
    prevent_initial_call = True
)
def MergevalueChoice(slider_value, project_data_store):
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    if functions.UpdateMergevalue(slider_value, project_data["id"]):
        project_data["merge_coef"] = slider_value
    
    return json.dumps(project_data, cls = functions.NpEncoder)

@dash.callback(
    Output("project_data_store", "data", allow_duplicate = True),
    Input("rename_project", "n_clicks"),
    State("project_name_input", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def RenameProject(clickdata, project_name, project_data_store):
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    if functions.UpdateProjectName(project_name, project_data["id"]):
        project_data["name"] = project_name

    return json.dumps(project_data, cls = functions.NpEncoder)

@dash.callback(
    Output("status_select", "value", allow_duplicate = True),
    Output("task_table", "children"),
    Output("project_data_store", "data", allow_duplicate = True),
    Input({"type": "status_change", "index": ALL}, "n_clicks"),
    State("status_select", "value"),
    State("status_select", "data"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def ChangeProjectStatus(clickdata, old_status, select_data, project_data_store):
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    select_data = pd.DataFrame(select_data)

    direction = 0
    if ctx.triggered_id["index"] == "prev": direction = -1
    if ctx.triggered_id["index"] == "next": direction = 1

    new_status_code = select_data.loc[select_data.loc[select_data["value"] == old_status].index[0] + direction, "value"]
    new_status = functions.GetStatusByCode(new_status_code)
    if functions.UpdateProjectStatus(new_status, project_data, current_user.userdata["id"]):
        project_data["status"] = new_status
    else: raise PreventUpdate

    task_table_content = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))

    return new_status_code, task_table_content, json.dumps(project_data, cls = functions.NpEncoder)

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
    Output("project_data_store", "data", allow_duplicate = True),
    Input("delete_project", "n_clicks"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def DeleteProject(clickdata, project_data_store):
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    if functions.DeleteProject(project_data["id"]):
        project_data = {}
        return "/projects", json.dumps(project_data, cls = functions.NpEncoder)
    
    raise PreventUpdate




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление пользователями ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    Output("role_select", "value", allow_duplicate = True),
    Output("role_select", "data"),
    Output("role_select", "disabled"),
    Output("add_user", "disabled"),
    Output("change_role", "disabled"),
    Input("user_select", "value"),
    Input("role_select", "value"),
    State("role_select", "data"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def SelectUser(user_id, role_code, role_select_data, project_data_store):
    user_id = int(user_id)

    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)

    userdata_id = functions.GetUserdataId(user_id, project_data["id"])
    user_role = functions.GetUserRole(userdata_id) if userdata_id else None

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
    Output("competence_select", "data", allow_duplicate = True),
    Input("change_role", "n_clicks"),
    State("user_select", "value"),
    State("role_select", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def ChangeRole(clickdata, user_id, role_code, project_data_store):
    user_id = int(user_id)

    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    userdata_id = functions.GetUserdataId(user_id, project_data["id"])

    prev_role_code = functions.GetUserRole(userdata_id)["role_code"]
    if not functions.UpdateUserRole(userdata_id, role_code): raise PreventUpdate
    if project_data["status"]["stage"] > 1 and "spectator" in [prev_role_code, role_code]:
        if role_code == "spectator": functions.DeleteUserFromAllProjectGroups(int(user_id), project_data["id"])
        if not functions.InsertUserEdgedata(userdata_id): raise PreventUpdate
        if project_data["status"]["stage"] > 2:
            if not functions.InsertUserCompdata(userdata_id, project_data): raise PreventUpdate
    
    table_content = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"]))
    select_data = functions.GetSelectData("competence_select", project_data["id"])
    return table_content, select_data


@dash.callback(
    Output("user_table", "children", allow_duplicate = True),
    Output("task_table", "children", allow_duplicate = True),
    Output("competence_select", "data", allow_duplicate = True),
    Output("role_select", "value", allow_duplicate = True),
    Input("add_user", "n_clicks"),
    State("user_select", "value"),
    State("role_select", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def AddUser(clickdata, user_id, role_code, project_data_store):
    user_id = int(user_id)

    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    userdata_id = functions.InsertUserdata(user_id, role_code, project_data["id"])

    if project_data["status"]["stage"] > 1:
        if not functions.InsertUserEdgedata(userdata_id): raise PreventUpdate
        if project_data["status"]["stage"] > 2:
            if not functions.InsertUserCompdata(userdata_id, project_data): raise PreventUpdate
                
    user_table_content = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"]))
    task_table_content = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))
    select_data = functions.GetSelectData("competence_select", project_data["id"])

    return user_table_content, task_table_content, select_data, role_code


@dash.callback(
    Output("user_table", "children", allow_duplicate = True),
    Output("task_table", "children", allow_duplicate = True),
    Output("competence_select", "data", allow_duplicate = True),
    Output("role_select", "value", allow_duplicate = True),
    Input({"type": "delete_button", "index": ALL}, "n_clicks"),
    State("project_data_store", "data"),
    State("role_select", "value"),
    prevent_initial_call = True
)
def DeleteUser(clickdata, project_data_store, role_code):
    if ctx.triggered[0]["value"]:
        if project_data_store == None: raise PreventUpdate
        project_data = json.loads(project_data_store)
        userdata_id = int(ctx.triggered_id["index"])

        if project_data["status"]["stage"] > 1:
            if not functions.DeleteUserEdgedata(userdata_id): raise PreventUpdate
            if project_data["status"]["stage"] > 2:
                if not functions.DeleteUserCompdata(userdata_id): raise PreventUpdate
        if not functions.DeleteUserdata(userdata_id): raise PreventUpdate

        user_table_content = functions.CreateTableContent(["Имя", "Роль", "Удалить"], functions.GetUserTableData(project_data["id"], project_data["role"]["access_level"]))
        task_table_content = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))
        select_data = functions.GetSelectData("competence_select", project_data["id"])

        return user_table_content, task_table_content, select_data, role_code
    
    raise PreventUpdate




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление компетентностью --------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    output = {
        "display": {
            "user_competence_container": Output("user_competence_container", "display"),
            "edge_competence_container": Output("edge_competence_container", "display"),
            "edge_competence_message": Output("edge_competence_message", "display"),
            "edge_competence_data": Output("edge_competence_data", "display"),
        },
        "value": {
            "competence_select": Output("competence_select", "value", allow_duplicate = True),
            "source_node_select": Output("source_node_select", "value"),
        },
        "message": Output("competence_type_message", "children"),
        "project_data_store": Output("project_data_store", "data", allow_duplicate = True),
        "user_competence_disabled": Output("save_project_competence", "disabled"),
    },
    inputs = {
        "input": {
            "competence_type": Input("competence_radiogroup", "value"),
            "project_data_store": State("project_data_store", "data"),
        }
    },
    prevent_initial_call = True
)
def CompetenceTypeChoice(input):

    if input["project_data_store"] == None: raise PreventUpdate
    project_data = json.loads(input["project_data_store"])

    display = {}
    if input["competence_type"] == "Постоянный":
        display["user_competence_container"] = "block"
        display["edge_competence_container"] = "none"

        if functions.SetCompetenceType(project_data["id"], True): 
            project_data["const_comp"] = True

    if input["competence_type"] == "Настраиваемый":
        display["user_competence_container"] = "none"
        display["edge_competence_container"] = "block"

        if functions.SetCompetenceType(project_data["id"], False):
            project_data["const_comp"] = False

    display["edge_competence_message"] = "block" if project_data["status"]["code"] == "initial" else "none"
    display["edge_competence_data"] = "block" if project_data["status"]["code"] != "initial" else "none"

    value = {}
    value["competence_select"] = None
    value["source_node_select"] = None

    output = {}
    output["display"] = display
    output["value"] = value
    output["message"] = "Настройка постоянной компетентности пользователей" if project_data["const_comp"] else "Настройка компетентности пользователя при оценке связи"
    output["project_data_store"] = json.dumps(project_data, cls = functions.NpEncoder)
    output["user_competence_disabled"] = True if input["competence_type"] == "Настраиваемый" else False
    
    return output

@dash.callback(
    Output("competence_select", "data", allow_duplicate = True),
    Output("competence_select", "label"),
    Output("competence_select", "value", allow_duplicate = True),
    Input("group_checkbox_edge", "checked"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def GroupCheckboxEdge(checked, project_data_store):
    if project_data_store == None: raise PreventUpdate

    project_data = json.loads(project_data_store)
    data = functions.GetSelectData("competence_select", project_data["id"], checked)
    label = "Группа пользователей" if checked else "Пользователь"

    return data, label, None

@dash.callback(
    Output("project_competence_table", "children"),
    Input("group_checkbox_project", "checked"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def GroupCheckboxProject(checked, project_data_store):
    if project_data_store == None: raise PreventUpdate

    project_data = json.loads(project_data_store)
    if checked: table_content = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"]))
    else: table_content = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"]))

    return table_content
        
@dash.callback(
    Output("edge_competence_table", "children", allow_duplicate = True),
    Output("save_edge_competence", "disabled"),
    Input("competence_select", "value"),
    Input("source_node_select", "value"),
    State("group_checkbox_edge", "checked"),
    prevent_initial_call = True
)
def EdgeCompetenceChoice(table_id, source_node_id, checked):
    edge_competence_data = []

    save_button_disabled = not (table_id and source_node_id)
    if not save_button_disabled:
        if checked: edge_competence_data = functions.GetGroupEdgeCompetenceData(int(source_node_id), int(table_id))
        else: edge_competence_data = functions.GetUserEdgeCompetenceData(int(source_node_id), int(table_id))

    return functions.CreateTableContent(["Критерий", "Компетентность"], edge_competence_data), save_button_disabled

@dash.callback(
    Output("edge_competence_table", "children", allow_duplicate = True),
    Input("save_edge_competence", "n_clicks"),
    State({"type": "edge_competence", "index": ALL}, "value"),
    State({"type": "edge_competence", "index": ALL}, "id"),
    State("competence_select", "value"),
    State("group_checkbox_edge", "checked"),
    prevent_initial_call = True
)
def SaveEdgeCompetence(clickdata, edge_competence_values, edge_competence_ids, table_id, checked):
    competence_data = pd.DataFrame(list(zip(edge_competence_values, [id["index"] for id in edge_competence_ids])), columns = ["competence", "id"])
    competence_data.drop(competence_data[competence_data["competence"] == ""].index, inplace = True)
    competence_data = list(competence_data.itertuples(index = False, name = None))

    if checked: functions.SetGroupEdgeCompetence(competence_data, int(table_id))
    else: functions.SetUserEdgeCompetence(competence_data, int(table_id))

    raise PreventUpdate

@dash.callback(
    Output("project_competence_table", "children", allow_duplicate = True),
    Input("save_project_competence", "n_clicks"),
    State({"type": "project_competence", "index": ALL}, "value"),
    State({"type": "project_competence", "index": ALL}, "id"),
    State("group_checkbox_project", "checked"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def SaveProjectCompetence(clickdata, project_competence_values, project_competence_ids, checked, project_data_store):
    competence_data = pd.DataFrame(list(zip(project_competence_values, [id["index"] for id in project_competence_ids])), columns = ["competence", "id"])
    competence_data.drop(competence_data[competence_data["competence"] == ""].index, inplace = True)
    competence_data = list(competence_data.itertuples(index = False, name = None))

    project_data = json.loads(project_data_store)
    if checked: functions.SetGroupProjectCompetence(competence_data, project_data["id"])
    else: functions.SetUserProjectCompetence(competence_data)
    functions.SetDefaultEdgeCompetence(project_data["id"])

    raise PreventUpdate




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление группами ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@dash.callback(
    Output("groupname_input", "value"),
    Input({"type": "grouplist_select", "index": "group_list"}, "value"),
    State({"type": "grouplist_select", "index": "group_list"}, "data"),
    prevent_initial_call = True
)
def SelectGroupOnGrouplistTab(groupselect_value, groupselect_data):
    groupselect_data = pd.DataFrame(groupselect_data)
    if groupselect_value: group_name = groupselect_data.loc[groupselect_data["value"] == groupselect_value, "label"][0]
    else: group_name = None

    return group_name

@dash.callback(
    Output("edit_group_button", "children", allow_duplicate = True),
    Output("edit_group_button", "disabled"),
    Input("groupname_input", "value"),
    State({"type": "grouplist_select", "index": "group_list"}, "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def SetButtonState(group_name, groupselect_value, project_data_store):
    project_data = json.loads(project_data_store)

    button_label = "Переименовать" if groupselect_value else "Создать"
    button_disabled = not bool(group_name) or (functions.CheckExistingGroups(group_name, project_data["id"]) and not groupselect_value)

    return button_label, button_disabled

@dash.callback(
    output = {
        "group_list_table": Output("group_list_table", "children", allow_duplicate = True),
        "project_competence_table": Output("project_competence_table", "children", allow_duplicate = True),
        "competence_select": Output("competence_select", "data", allow_duplicate = True),
        "group_select_list": Output({"type": "grouplist_select", "index": "group_list"}, "data", allow_duplicate = True),
        "group_select_users": Output({"type": "grouplist_select", "index": "group_users"}, "data", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "edit_button_click": Input("edit_group_button", "n_clicks"),
            "delete_button_click": Input({"type":"group_delete_button", "index": ALL}, "n_clicks"),
            "groupselect_value": State({"type": "grouplist_select", "index": "group_list"}, "value"),
            "project_data_store": State("project_data_store", "data"),
            "group_name": State("groupname_input", "value"),
            "group_checkbox_state": {
                "project": State("group_checkbox_project", "checked"),
                "edge": State("group_checkbox_edge", "data"),
            },
            "table_data": {
                "project_competence": State("project_competence_table", "children"),
                "competence_select": State("competence_select", "data"),
                "grouplist_select": State({"type": "grouplist_select", "index": "group_users"}, "data"),
            },
        }
    },
    prevent_initial_call = True
)
def GrouplistButtonClick(input):
    project_data = json.loads(input["project_data_store"])

    if ctx.triggered[0]["value"]:
        if "index" in ctx.triggered_id:
            if not functions.DeleteGroup(ctx.triggered_id["index"]): raise PreventUpdate
        else: 
            if input["groupselect_value"]: 
                if not functions.RenameGroup(input["group_name"], int(input["groupselect_value"])): raise PreventUpdate
            else: 
                if not functions.AddGroup(input["group_name"], project_data["id"]): raise PreventUpdate
            
        output = {}
        output["group_list_table"] = functions.CreateTableContent(["Группа", "Удалить группу"], functions.GetGroupListTableData(project_data["id"]))
        output["project_competence_table"] = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"])) if input["group_checkbox_state"]["project"] else input["table_data"]["project_competence"]
        
        output["group_select_list"] = functions.GetSelectData("competence_select", project_data["id"], True)
        output["group_select_users"] = output["group_select_list"]
        output["competence_select"] = output["group_select_list"] if input["group_checkbox_state"]["edge"] else input["table_data"]["competence_select"]

        return output
    
    raise PreventUpdate
    
@dash.callback(
    Output("group_users_table", "children", allow_duplicate = True),
    Output("groupadd_user", "disabled"),
    Input({"type": "grouplist_select", "index": "group_users"}, "value"),
    Input("groupuser_select", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def SelectUserGroups(groupselect_value, userselect_value, project_data_store):
    project_data = json.loads(project_data_store)

    add_button_disabled = not groupselect_value or not userselect_value
    if not add_button_disabled: add_button_disabled = functions.CheckIfUserInGroup(int(groupselect_value), int(userselect_value))

    table_data = functions.CreateTableContent(["Пользователь", "Удалить из группы"], functions.GetGroupUsersTableData(project_data["id"]))

    return table_data, add_button_disabled

@dash.callback(
    Output("group_users_table", "children", allow_duplicate = True),
    Output("groupuser_select", "value"),
    Input("groupadd_user", "n_clicks"),
    Input({"type": "groupdata_button", "index": ALL}, "n_clicks"),
    State({"type": "grouplist_select", "index": "group_users"}, "value"),
    State("groupuser_select", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def EditGroupUsers(add_user, delete_user, groupselect_value, userselect_value, project_data_store):
    project_data = json.loads(project_data_store)

    if ctx.triggered[0]["value"]:
        if "index" in ctx.triggered_id:
            if not functions.DeleteUserFromGroup(ctx.triggered_id["index"]): raise PreventUpdate
        else: 
            if not functions.AddUserToGroup(int(groupselect_value), int(userselect_value)): raise PreventUpdate

        table_data = functions.CreateTableContent(["Пользователь", "Удалить из группы"], functions.GetGroupUsersTableData(project_data["id"]))

        return table_data, groupselect_value
    
    raise PreventUpdate
       
