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
roles_code_dict =  functions.GetRolesCodeDict()
status_stage_dict = functions.GetStatusStageDict()

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


#Вернуть таблицу групп проекта
def GetTableProjectUserGroups(project_id):
    head = dmc.TableThead(
                children=[
                    dmc.TableTr(
                        children=[
                            dmc.TableTh("Наименование группы"),
                            dmc.TableTh(children="Изменить", w=80),
                            dmc.TableTh(children="Удалить", w=80),
                        ]
                    ),
                ],
                bg="var(--mantine-color-gray-2)",
            )

    table_data = functions.GetGroupListTableData(project_id)
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in table_data])

    return [head, body]


#Вернуть таблицу пользователей группы
def GetTableGroupUsers(group_id):
    head = dmc.TableThead(
                children=[
                    dmc.TableTr(
                        children=[
                            dmc.TableTh("Пользователь"),
                            dmc.TableTh(children="Удалить", w=80),
                        ]
                    ),
                ],
                bg="var(--mantine-color-gray-2)",
            )

    table_data = functions.GetGroupUsersTableData(int(group_id))
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in table_data])

    return [head, body]


#Вернуть таблицу всех пользователей проекта
def GetTableProjectUsers(project_id, access_level):
    head = dmc.TableThead(
                children=[
                    dmc.TableTr(
                        children=[
                            dmc.TableTh("Пользователь"),
                            dmc.TableTh("Роль", w=150),
                            dmc.TableTh(children="Изменить", w=80),
                            dmc.TableTh(children="Удалить", w=80),
                        ]
                    ),
                ],
                bg="var(--mantine-color-gray-2)",
            )

    table_data = functions.GetUserTableData(project_id, access_level)
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in table_data])

    return [head, body]





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
                dcc.Store(id = "project_data_store", storage_type='session', clear_data=True),
                dcc.Store(id = "element_data_store", storage_type='session', clear_data=True),
                dcc.Store(id = "comp_data_store", storage_type='session', clear_data=True),
                dcc.Interval(id={'type': 'load_interval', 'index': 'settings'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                dmc.Modal(
                    title=dmc.Text("Удаление проекта", fz = 20),
                    id="dialog_settings_delete_project",
                    opened = False,
                    children=[
                        dmc.Text("Удалить проект?"),
                        dmc.Space(h=20),
                        dmc.Group(
                            [
                                dmc.Button(id="dialog_settings_delete_project_button_ok", children="Да", color = "red"),
                                dmc.Button(id="dialog_settings_delete_project_button_cancel", children="Отмена"),
                            ],
                            justify="flex-end",
                        ),
                    ],
                ),
                dmc.Modal(
                    title=dmc.Text(id="settings_dialog_edit_user_title", fz = 20),
                    id="settings_dialog_edit_user",
                    opened = False,
                    size=750,
                    children=[
                        dmc.Flex(
                            children = [
                                dmc.Select(id = "settings_dialog_edit_user_select_user", data = [], label = "Пользователь", searchable = True, clearable = False, withCheckIcon=False, size = "md", w = 350),
                                dmc.Select(id = "settings_dialog_edit_user_select_role", data = [], label = "Роль", searchable = False, clearable = False, withCheckIcon=False, size = "md", w = 350),
                            ],
                            gap = "md",
                            align = "flex-end",
                            pb = "sm"
                        ),
                        dmc.Space(h=20),
                        dmc.VisuallyHidden(id="settings_dialog_edit_user_id"),
                        dmc.Group(
                            [
                                dmc.Button(id="settings_dialog_edit_user_button_ok", children="Добавить / изменить роль"),
                            ],
                            justify="flex-end",
                        ),
                    ],
                ),
                dmc.Modal(
                    title=dmc.Text("Удаление пользователя из проекта", fz = 20),
                    id="settings_dialog_delete_user",
                    opened = False,
                    children=[
                        dmc.Text(id="settings_dialog_delete_user_text"),
                        dmc.Space(h=20),
                        dmc.VisuallyHidden(id="settings_dialog_delete_user_userdata_id"),
                        dmc.Group(
                            [
                                dmc.Button(id={"type":"settings_dialog_delete_user_button","index":"ok"}, children="Да", color = "red"),
                                dmc.Button(id={"type":"settings_dialog_delete_user_button","index":"cancel"}, children="Отмена"),
                            ],
                            justify="flex-end",
                        ),
                    ],
                ),
                dmc.Modal(
                    title=dmc.Text(id="settings_dialog_edit_usergroup_title", fz = 20),
                    id="settings_dialog_edit_usergroup",
                    opened = False,
                    children=[
                        dmc.TextInput(debounce=500, id = "settings_dialog_edit_usergroup_input", label = "Наименование"),
                        dmc.Space(h=20),
                        dmc.VisuallyHidden(id="settings_dialog_edit_usergroup_id"),
                        dmc.Group(
                            [
                                dmc.Button(id="settings_dialog_edit_usergroup_button_ok", children="Создать / переименовать группу"),
                            ],
                            justify="flex-end",
                        ),
                    ],
                ),
                dmc.Modal(
                    title=dmc.Text("Удаление группы экспертов", fz = 20),
                    id="settings_dialog_delete_usergroup",
                    opened = False,
                    children=[
                        dmc.Text(id="settings_dialog_delete_usergroup_text"),
                        dmc.Space(h=20),
                        dmc.VisuallyHidden(id="settings_dialog_delete_usergroup_id"),
                        dmc.Group(
                            [
                                dmc.Button(id="settings_dialog_delete_usergroup_button_ok", children="Да", color = "red"),
                                dmc.Button(id="settings_dialog_delete_usergroup_button_cancel", children="Отмена"),
                            ],
                            justify="flex-end",
                        ),
                    ],
                ),
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children=[
                                dmc.Flex(children=dmc.NavLink(label = dmc.Text("Настройки", fz = "lg"), leftSection = DashIconify(icon = "mingcute:menu-line", width=25))),
                                dmc.Center(dmc.Text(id="settings_project_caption", fz = "lg")),
                                dmc.Box(
                                    children = [
                                        dmc.Group(
                                            children=[
                                                dmc.Center(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]), fz = "lg")),
                                                dmc.Flex(children=dmc.NavLink(id = {"type": "logout_button", "index": "settings"}, leftSection = DashIconify(icon = "mingcute:exit-fill", width=25), c='red')),
                                            ]
                                        ),
                                    ],
                                    px = "md",
                                    style = {"display":"flex", "justify-content":"end"}
                                ),
                            ],
                            px = "md",
                            style = {"display":"flex", "justify-content":"space-between"}
                        ),
                    ]
                ),
                dmc.AppShellNavbar(
                    children = [
                        #dmc.Box(children = dmc.Text("Настройки", fz = 24, fw = 500), p = "sm"),
                        #dmc.Divider(),
                        dmc.Box(
                            children = [
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "project"},
                                    label = dmc.Text("Управление проектом"),
                                    leftSection = DashIconify(icon = "mingcute:settings-3-line", width=20),
                                    active = True
                                ),
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "users"},
                                    label = dmc.Text("Управление пользователями"),
                                    leftSection = DashIconify(icon = "mingcute:user-1-line", width=20),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "competence"},
                                    label = dmc.Text("Управление компетентностью"),
                                    leftSection = DashIconify(icon = "mingcute:certificate-line", width=20),
                                    active = False
                                ),
                                dmc.NavLink(
                                    id = {"type": "settings_navlink", "index": "groups"},
                                    label = dmc.Text("Управление группами"),
                                    leftSection = DashIconify(icon = "mingcute:group-line", width=20),
                                    active = False
                                ),
                                dmc.Divider(),
                                dmc.NavLink(
                                    id = "settings_to_project",
                                    label = dmc.Text("Вернуться к проекту"),
                                    leftSection = DashIconify(icon = "mingcute:arrow-left-line", width=20),
                                ),
                            ],
                        ),
                    ]
                ),
                dmc.AppShellMain(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Flex(
                                    children = [
                                        dmc.Text("Управление проектом", fz = 24, fw = 500, pb = "sm"),
                                        dmc.Button("Удалить проект",
                                            id = "settings_delete_project_button",
                                            disabled = bool(project_data["role"]["code"] != "owner"),
                                            color = "red"
                                        ),
                                    ],
                                    align = "flex-end",
                                    justify = "space-between"
                                ),
                                dmc.Flex(
                                    children = [
                                        dmc.Box(
                                            children = [
                                                dmc.Text("Название", fz = "xl", fw = 500, pb = "xs"),
                                                dmc.TextInput(id = "settings_project_name_input", size = "md", w = 350),
                                            ]
                                        ),
                                        dmc.Button("Сохранить", id = "settings_rename_project_button", disabled=True, size = "md", w = 130),
                                    ],
                                    gap = "md",
                                    align = "flex-end",
                                    pb = "xl"
                                ),
                                dmc.Box(
                                    children=[
                                        dmc.Box(
                                            children = [
                                                dmc.Text("Метод слияния", fz = "xl", fw = 500, pb = "sm"),
                                                dmc.RadioGroup(
                                                    id = "settings_mergemethod_radiogroup",
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
                                    ],
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
                                dmc.Text("Этап проекта", fz = "xl", fw = 500, pb = "sm"),
                                dmc.Space(h=10),
                                dmc.Stepper(
                                            id="settings_project_stepper",
                                            active=0,
                                            allowNextStepsSelect=False,
                                            children=[
                                                dmc.StepperStep(
                                                    label="Первый этап",
                                                    description="Построение базовой иерархии",
                                                    children=dmc.Text("Этап 1: Построение базовой иерархии", ta="center", size="lg"),
                                                    allowStepClick=False,
                                                    allowStepSelect=False,
                                                ),
                                                dmc.StepperStep(
                                                    label="Второй этап",
                                                    description="Оценка зависимостей",
                                                    children=dmc.Text("Этап 2: Эксперты провоизводят оценку зависимостей", ta="center", size="lg"),
                                                    allowStepClick=False,
                                                    allowStepSelect=False,
                                                ),
                                                dmc.StepperStep(
                                                    label="Третий этап",
                                                    description="Сравнительная оценка",
                                                    children=dmc.Text("Этап 3: Эксперты проводят сравнительную оценку", ta="center", size="lg"),
                                                    allowStepClick=False,
                                                    allowStepSelect=False,
                                                ),
                                                dmc.StepperCompleted(
                                                    children=dmc.Text("Проект завершён. Результат доступен в разделе 'Аналитика'", ta="center", fw=700, size="lg")
                                                ),
                                            ],
                                        ),
                                        dmc.Group(
                                            justify="center",
                                            mt="xl",
                                            children=[
                                                dmc.Button("Предыдущий", id = {"type": "status_change", "index": "prev"}, disabled = True, size = "md", w = 180),
                                                dmc.Button("Следующий", id = {"type": "status_change", "index": "next"}, disabled = True, size = "md", w = 180),
                                            ],
                                        ),


                            ],
                            id = {"type": "settings_page", "index": "project"},
                            display = "block",
                            p = "sm",
                        ),
                        dmc.Box(
                            children = [
                                dmc.Flex(
                                    children=[
                                        dmc.Text("Управление пользователями", fz = 24, fw = 500, pb = "sm"),
                                        dmc.Button(children = "Добавить пользователя", id = {"type":"user_edit_button", "index": "0"}, size = "sm", w = 200),
                                    ],
                                    align = "flex-end",
                                    justify = "space-between",
                                ),
                                dmc.Space(h=20),
                                dmc.Table(
                                    id = "user_table",
                                    children = GetTableProjectUsers(project_data["id"], project_data["role"]["access_level"]),
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
                                        dmc.ActionIcon(id = "save_project_competence", children = DashIconify(icon = "mingcute:save-2-line", width = 25), disabled = not project_data["const_comp"], size = "input-md"),
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
                                            children = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"])),
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
                                dmc.Flex(
                                    children=[
                                        dmc.Text("Управление группами", fz = 24, fw = 500, pb = "sm"),
                                        dmc.Button(children = "Добавить группу", id = {"type":"group_edit_button", "index": "0"}, size = "sm", w = 150),
                                    ],
                                    align = "flex-end",
                                    justify = "space-between",
                                ),
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
                                                        dmc.Table(
                                                            id = "group_list_table",
                                                            children = GetTableProjectUserGroups(project_data["id"]),
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
                                                            children = [],
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
            header={"height": "45px"},
            navbar={"width": "300px"},
        )
    
    layout = dmc.MantineProvider(layout)
    return layout


#Однократный запуск при обновлении страницы
@dash.callback(
    output = {
        "redirect": Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
        "project_data_store": Output("project_data_store", "data", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "n_intervals": Input(component_id={'type': 'load_interval', 'index': 'settings'}, component_property="n_intervals"),
        }
    },
    prevent_initial_call = True
)
def PageUpdateOnInterval(input):
    page_settings = json.loads(session["page_settings"])
    project_data = functions.GetProjectData(current_user.userdata["id"], page_settings["project_id"])

    output = {}
    output["redirect"] = "/settings"
    output["project_data_store"] = None

    if 1==0:
        page_project = {}
        page_project["project_id"] = page_settings["project_id"]
        session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)
        output["redirect"] = "/project"
        return output

    output["project_data_store"] = json.dumps(project_data, cls = functions.NpEncoder)
    
    return output

#При изменении project_data_store
@dash.callback(
    output = {
        "project_name": Output("settings_project_name_input", "value", allow_duplicate = True),
        "project_caption": Output("settings_project_caption", "children", allow_duplicate = True),
        "project_stepper": Output("settings_project_stepper", "active", allow_duplicate = True),
        "status_change_prev": Output({"type": "status_change", "index": "prev"}, "disabled", allow_duplicate = True),
        "status_change_next": Output({"type": "status_change", "index": "next"}, "disabled", allow_duplicate = True),
        
        "merge_radiogroup_disabled": Output("settings_mergemethod_radiogroup", "readOnly", allow_duplicate = True),
        "merge_slider_disabled": Output("mergevalue_slider", "disabled", allow_duplicate = True),
        "save_project_competence_disabled": Output("save_project_competence", "disabled", allow_duplicate = True),
        "save_edge_competence_disabled": Output("save_edge_competence", "disabled", allow_duplicate = True),
        "project_competence_table": Output("project_competence_table", "children", allow_duplicate = True),
        "edge_competence_table": Output("edge_competence_table", "children", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "project_data_store": Input("project_data_store", "data"),
            "group_competence_project_checkbox": State("group_checkbox_project", "checked"),
            "group_competence_edge_checkbox": State("group_checkbox_edge", "checked"),
            "competence_select_value": State("competence_select", "value"),
            "source_node_value": State("source_node_select", "value"),
            "mergemethod_value": State("settings_mergemethod_radiogroup", "value"),

        }
    },
    prevent_initial_call = True
)
def ProjectDataStoreOnChange(input):
    if not "project_data_store" in input: raise PreventUpdate
    project_data_store = input["project_data_store"]
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)

    project_status = project_data["status"]["code"]

    competence_disable = True if project_data["status"]["stage"] > 2 else False

    project_competence_table = []
    if input["group_competence_project_checkbox"]:
        project_competence_table = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))
    else:
        project_competence_table = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))

    edge_competence_data = []
    if input["competence_select_value"] and input["source_node_value"]:
        if input["group_competence_edge_checkbox"]:
            edge_competence_data = functions.GetGroupEdgeCompetenceData(int(input["source_node_value"]), int(input["competence_select_value"]), project_data["status"]["stage"])
        else:
            edge_competence_data = functions.GetUserEdgeCompetenceData(int(input["source_node_value"]), int(input["competence_select_value"]), project_data["status"]["stage"])



    output = {}
    output["project_name"] = project_data["name"]
    output["project_caption"] = project_data["name"] + " (" + project_data["status"]["name"] + ")"
    output["project_stepper"] = project_data["status"]["stage"]-1
    output["status_change_prev"] = bool(project_status == "initial")
    output["status_change_next"] = bool(project_status == "completed")
    
    output["merge_radiogroup_disabled"] = competence_disable
    output["merge_slider_disabled"] = competence_disable or input["mergemethod_value"] != "Настроить"
    output["save_project_competence_disabled"] = competence_disable
    #output["competence_radiogroup_disabled"] = competence_disable
    #output["group_checkbox_project_disabled"] = competence_disable
    #output["group_checkbox_edge_disabled"] = competence_disable
    #output["competence_select_disabled"] = competence_disable
    #output["source_node_disabled"] = competence_disable
    output["save_edge_competence_disabled"] = competence_disable
    output["project_competence_table"] = project_competence_table
    output["edge_competence_table"] = functions.CreateTableContent(["Критерий", "Компетентность"], edge_competence_data)

    return output



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
    Input("settings_mergemethod_radiogroup", "value"),
    State("mergevalue_slider", "value"),
    prevent_initial_call = True
)
def MergemethodChoice(method, slider_value):
    if not method: raise PreventUpdate
    if method != "Настроить": slider_value = merge_radiogroupdata[method]["value"]

    return slider_value

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
    Output("settings_rename_project_button", "disabled", allow_duplicate = True),
    Input("settings_project_name_input", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def InputProjectNameChange(project_name, project_data_store):
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    if project_data["name"] == project_name:
        return True
    else:
        return False


@dash.callback(
    Output("project_data_store", "data", allow_duplicate = True),
    Output("settings_rename_project_button", "disabled", allow_duplicate = True),
    Input("settings_rename_project_button", "n_clicks"),
    State("settings_project_name_input", "value"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def ButtonRenameProjectClick(clickdata, project_name, project_data_store):
    if not clickdata: raise PreventUpdate
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    if project_data["name"] == project_name: raise PreventUpdate
    if not functions.UpdateProjectName(project_name, project_data["id"]): raise PreventUpdate
    project_data["name"] = project_name
    return json.dumps(project_data, cls = functions.NpEncoder), True

@dash.callback(
    #Output("status_select", "value", allow_duplicate = True),
    Output("task_table", "children"),
    Output("project_data_store", "data", allow_duplicate = True),
    #Output("settings_project_stepper", "active", allow_duplicate = True),
    Input({"type": "status_change", "index": ALL}, "n_clicks"),
    #State("status_select", "value"),
    #State("status_select", "data"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def ChangeProjectStatus(clickdata, project_data_store): #old_status, select_data
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    #select_data = pd.DataFrame(select_data)

    direction = 0
    if ctx.triggered_id["index"] == "prev": direction = -1
    if ctx.triggered_id["index"] == "next": direction = 1

    old_status_code= project_data["status"]["stage"]
    new_status_code = old_status_code + direction
    if not new_status_code in status_stage_dict: raise PreventUpdate
    new_status = status_stage_dict[new_status_code]

    #new_status_code = select_data.loc[select_data.loc[select_data["value"] == old_status].index[0] + direction, "value"]
    #new_status = functions.GetStatusByCode(new_status_code)
    if functions.UpdateProjectStatus(new_status, project_data, current_user.userdata["id"]):
        project_data["status"] = new_status
    else: raise PreventUpdate

    task_table_content = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))

    return task_table_content, json.dumps(project_data, cls = functions.NpEncoder) #, new_status["stage"]-1


#Открыть диалог запроса удаления проекта по кнопке "Удалить проект"
@dash.callback(
    Output("dialog_settings_delete_project", "opened", allow_duplicate = True), #Открыть диалог удаления
    Input("settings_delete_project_button", "n_clicks"),
    prevent_initial_call=True,
)
def modal_demo(clickdata):
    if not clickdata: raise PreventUpdate
    return True

#Кнопки диалога удаления проекта - отмена и удаление проекта
@dash.callback(
    Output({"type": "redirect", "index": "settings"}, "pathname", allow_duplicate = True),
    Output("dialog_settings_delete_project", "opened", allow_duplicate = True), #Закрыть диалог удаления
    Input("dialog_settings_delete_project_button_ok", "n_clicks"),
    Input("dialog_settings_delete_project_button_cancel", "n_clicks"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def DeleteProject(ok_click, cancel_click, project_data_store):
    if cancel_click: return "/settings", False
    if not ok_click: raise PreventUpdate
    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)
    if not functions.DeleteProject(project_data["id"]): raise PreventUpdate
    return "/projects", False


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление пользователями ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Открыть диалог добавления пользователя / изменения роли
@dash.callback(
    output = {
        "dialog_opened": Output("settings_dialog_edit_user", "opened", allow_duplicate = True), #Открыть диалог
        "dialog_title": Output("settings_dialog_edit_user_title", "children"),
        "ok_caption": Output("settings_dialog_edit_user_button_ok", "children"),
        "user_select_data": Output("settings_dialog_edit_user_select_user", "data"),
        "user_select_value": Output("settings_dialog_edit_user_select_user", "value"),
        "user_select_disabled": Output("settings_dialog_edit_user_select_user", "disabled"),
        "role_select_data": Output("settings_dialog_edit_user_select_role", "data"),
        "role_select_value": Output("settings_dialog_edit_user_select_role", "value"),
        "role_select_disabled": Output("settings_dialog_edit_user_select_role", "disabled"),
    },
    inputs = {
        "input": {
            "edit_click": Input({"type":"user_edit_button", "index": ALL}, "n_clicks"),
            "project_data_store": State("project_data_store", "data"),
        }
    },
    prevent_initial_call = True
)
def modal_user_edit(input):
    #if not clickdata: raise PreventUpdate

    output = {}
    output["dialog_opened"] = False
    output["dialog_title"] = ""
    output["ok_caption"] = ""
    output["user_select_data"] = []
    output["user_select_value"] = None
    output["user_select_disabled"] = False
    output["role_select_data"] = []
    output["role_select_value"] = None
    output["role_select_disabled"] = False
    
    edit_click = input["edit_click"]
    if len(edit_click) == edit_click.count(None): raise PreventUpdate
    if not ctx.triggered_id: raise PreventUpdate

    if input["project_data_store"] == None: raise PreventUpdate
    project_data = json.loads(input["project_data_store"])

    if ctx.triggered_id["type"] != "user_edit_button": raise PreventUpdate
    userdata_id = ctx.triggered_id["index"]
    if userdata_id == "0":
        output["dialog_title"] = "Добавление пользователя"
        output["user_select_data"] = functions.GetSelectData("not_project_user", project_data["id"]) # Пользователи, которых нет в проекте
        output["user_select_value"] = None
        output["user_select_disabled"] = False
        output["ok_caption"] = "Добавить"
        output["dialog_opened"] = True
    else:
        edit_click.pop(0)
        if len(edit_click) == edit_click.count(None): raise PreventUpdate

        user_role = functions.GetUserRole(userdata_id)
        output["dialog_title"] = "Изменение роли пользователя"
        output["role_select_value"] = user_role["role_code"]
        output["role_select_disabled"] = bool(user_role["access_level"] >= project_data["role"]["access_level"])
        output["user_select_data"] = functions.GetSelectData("project_user", project_data["id"]) # Все, или пользователи проекта, а может и не надо никого?
        output["user_select_value"] = str(user_role["user_id"])
        output["user_select_disabled"] = True
        output["ok_caption"] = "Сохранить"
        output["dialog_opened"] = True

    role_select_data = pd.DataFrame(role_data)
    output["role_select_data"] = role_select_data.loc[role_select_data["access_level"] < project_data["role"]["access_level"]].to_dict("records")

    return output

#Доступность кнопки ОК диалога добавления пользователя / изменения роли
@dash.callback(
    Output("settings_dialog_edit_user_button_ok", "disabled"),
    Input("settings_dialog_edit_user_select_user", "value"),
    Input("settings_dialog_edit_user_select_role", "value"),
    prevent_initial_call = True
)
def modal_user_edit_ok_disable(user_value, role_value):
    if user_value and role_value:
        return False
    else:
        return True

#Обработка нажатия кнопки ОК диалога добавления пользователя / изменения роли
@dash.callback(
    output = {
        "dialog_opened": Output("settings_dialog_edit_user", "opened", allow_duplicate = True), #Закрыть диалог
        "user_table": Output("user_table", "children", allow_duplicate = True),
        "task_table": Output("task_table", "children", allow_duplicate = True),
        "project_competence_table": Output("project_competence_table", "children", allow_duplicate = True),
        "competence_select_data": Output("competence_select", "data", allow_duplicate = True),
        "competence_select_value": Output("competence_select", "value", allow_duplicate = True),
        "groupuser_select_data": Output("groupuser_select", "data", allow_duplicate = True),
        "groupuser_select_value": Output("groupuser_select", "value", allow_duplicate = True),
        "grouplist_select_value": Output({"type": "grouplist_select", "index": "group_users"}, "value", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "ok_click": Input("settings_dialog_edit_user_button_ok", "n_clicks"),
            "user_select_value": State("settings_dialog_edit_user_select_user", "value"),
            "role_select_value": State("settings_dialog_edit_user_select_role", "value"),
            "project_data_store": State("project_data_store", "data"),
            "group_competence_project_checkbox": State("group_checkbox_project", "checked"),
            "group_competence_edge_checkbox": State("group_checkbox_edge", "checked"),
        }
    },
    prevent_initial_call = True
)
def modal_user_edit_button_click(input):
    output = {}
    output["dialog_opened"] = False
    output["user_table"] = no_update
    output["task_table"] = no_update
    output["project_competence_table"] = no_update
    output["competence_select_data"] = no_update
    output["competence_select_value"] = no_update
    output["groupuser_select_data"] = no_update
    output["groupuser_select_value"] = no_update
    output["grouplist_select_value"] = no_update
    
    user_id = input["user_select_value"]
    role_code = input["role_select_value"]
    if input["project_data_store"] == None: raise PreventUpdate
    project_data = json.loads(input["project_data_store"])

    user_data = functions.GetUserInProjectData(user_id, project_data["id"])
    if not user_data: #Добавление пользователя
        userdata_id = functions.InsertUserdata(user_id, role_code, project_data["id"])
        if project_data["status"]["stage"] > 1:
            if not functions.InsertUserEdgedata(userdata_id): raise PreventUpdate
            if project_data["status"]["stage"] > 2:
                if not functions.InsertUserCompdata(userdata_id, project_data): raise PreventUpdate
    else: # Изменение роли
        if role_code == user_data["role_code"]:
            return output
        else:
            prev_role_code = user_data["role_code"]
            if not functions.UpdateUserRole(user_data["id"], role_code): raise PreventUpdate
            if project_data["status"]["stage"] > 1 and "spectator" in [prev_role_code, role_code]:
                if role_code == "spectator": functions.DeleteUserFromAllProjectGroups(int(user_id), project_data["id"])
                if not functions.InsertUserEdgedata(user_data["id"]): raise PreventUpdate
                if project_data["status"]["stage"] > 2:
                    if not functions.InsertUserCompdata(user_data["id"], project_data): raise PreventUpdate

    if input["group_competence_project_checkbox"]:
        project_competence_table = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))
    else:
        project_competence_table = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))

    output["user_table"] = GetTableProjectUsers(project_data["id"], project_data["role"]["access_level"])
    output["task_table"] = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))
    output["project_competence_table"] = project_competence_table
    output["competence_select_data"] = functions.GetSelectData("competence_select", project_data["id"], input["group_competence_edge_checkbox"])
    output["competence_select_value"] = None
    output["groupuser_select_data"] = output["competence_select_data"]
    output["groupuser_select_value"] = None
    output["grouplist_select_value"] = None

    return output


#Открыть диалог удаления пользователя проекта
@dash.callback(
    Output("settings_dialog_delete_user", "opened", allow_duplicate = True), #Открыть диалог
    Output("settings_dialog_delete_user_text", "children"),
    Output("settings_dialog_delete_user_userdata_id", "children"),
    Input({"type":"user_delete_button", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def modal_delete(clickdata):
    if len(clickdata) == clickdata.count(None): raise PreventUpdate
    if not ctx.triggered_id: raise PreventUpdate
    if ctx.triggered_id["type"] != "user_delete_button": raise PreventUpdate
    userdata_id = ctx.triggered_id["index"]
    user_role = functions.GetUserRole(userdata_id)
    #group_data = functions.GetGroupDict(group_id)
    return True, "Удалить пользователя '" + user_role["user_name"] + "'?", userdata_id

#Обработка нажатия кнопки ОК диалога удаления пользователя из проекта
@dash.callback(
    output = {
        "dialog_opened": Output("settings_dialog_delete_user", "opened", allow_duplicate = True), #Закрыть диалог
        "user_table": Output("user_table", "children", allow_duplicate = True),
        "task_table": Output("task_table", "children", allow_duplicate = True),
        "project_competence_table": Output("project_competence_table", "children", allow_duplicate = True),
        "competence_select_data": Output("competence_select", "data", allow_duplicate = True),
        "competence_select_value": Output("competence_select", "value", allow_duplicate = True),
        "groupuser_select_data": Output("groupuser_select", "data", allow_duplicate = True),
        "groupuser_select_value": Output("groupuser_select", "value", allow_duplicate = True),
        "grouplist_select_value": Output({"type": "grouplist_select", "index": "group_users"}, "value", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "click": Input({"type":"settings_dialog_delete_user_button","index":ALL}, "n_clicks"),
            "project_data_store": State("project_data_store", "data"),
            "userdata_id": State("settings_dialog_delete_user_userdata_id", "children"),
            "group_competence_project_checkbox": State("group_checkbox_project", "checked"),
            "group_competence_edge_checkbox": State("group_checkbox_edge", "checked"),
        }
    },
    prevent_initial_call = True
)
def modal_user_delete_button_click(input):
    output = {}
    output["dialog_opened"] = False
    output["user_table"] = no_update
    output["task_table"] = no_update
    output["project_competence_table"] = no_update
    output["competence_select_data"] = no_update
    output["competence_select_value"] = no_update
    output["groupuser_select_data"] = no_update
    output["groupuser_select_value"] = no_update
    output["grouplist_select_value"] = no_update

    clickdata = input["click"]
    if len(clickdata) == clickdata.count(None): raise PreventUpdate
    if not ctx.triggered_id: raise PreventUpdate
    if ctx.triggered_id["type"] != "settings_dialog_delete_user_button": raise PreventUpdate
    click_button = ctx.triggered_id["index"]

    if click_button == "cancel":
        output["dialog_opened"] = False
        return output

    if input["project_data_store"] == None: raise PreventUpdate
    project_data = json.loads(input["project_data_store"])

    userdata_id = input["userdata_id"]

    if not functions.DeleteUserData(userdata_id): raise PreventUpdate

    if input["group_competence_project_checkbox"]:
        project_competence_table = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))
    else:
        project_competence_table = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))

    output["user_table"] = GetTableProjectUsers(project_data["id"], project_data["role"]["access_level"])
    output["task_table"] = functions.CreateTableContent(["Имя", "Оценка зависимостей", "Сравнительная оценка"], functions.GetTaskTableData(project_data["id"]))
    output["project_competence_table"] = project_competence_table
    output["competence_select_data"] = functions.GetSelectData("competence_select", project_data["id"], input["group_competence_edge_checkbox"])
    output["competence_select_value"] = None
    output["groupuser_select_data"] = output["competence_select_data"]
    output["groupuser_select_value"] = None
    output["grouplist_select_value"] = None

    return output


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
    if checked: 
        table_content = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))
    else: 
        table_content = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))

    return table_content
        
@dash.callback(
    Output("edge_competence_table", "children", allow_duplicate = True),
    Output("save_edge_competence", "disabled"),
    Input("competence_select", "value"),
    Input("source_node_select", "value"),
    State("group_checkbox_edge", "checked"),
    State("project_data_store", "data"),
    prevent_initial_call = True
)
def EdgeCompetenceChoice(table_id, source_node_id, checked, project_data_store):
    edge_competence_data = []

    if project_data_store == None: raise PreventUpdate
    project_data = json.loads(project_data_store)

    competence_disable = True if project_data["status"]["stage"] > 2 else False

    save_button_disabled = not (table_id and source_node_id) or competence_disable
    #if not save_button_disabled:
    if table_id and source_node_id:
        if checked:
            edge_competence_data = functions.GetGroupEdgeCompetenceData(int(source_node_id), int(table_id), project_data["status"]["stage"])
        else:
            edge_competence_data = functions.GetUserEdgeCompetenceData(int(source_node_id), int(table_id), project_data["status"]["stage"])

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
    if not clickdata: raise PreventUpdate

    competence_data = pd.DataFrame(list(zip(edge_competence_values, [id["index"] for id in edge_competence_ids])), columns = ["competence", "id"])
    competence_data.drop(competence_data[competence_data["competence"] == ""].index, inplace = True)
    competence_data = list(competence_data.itertuples(index = False, name = None))

    if checked: 
        functions.SetGroupEdgeCompetence(competence_data, int(table_id))
    else: 
        functions.SetUserEdgeCompetence(competence_data, int(table_id))

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
    if not clickdata: raise PreventUpdate

    competence_data = pd.DataFrame(list(zip(project_competence_values, [id["index"] for id in project_competence_ids])), columns = ["competence", "id"])
    competence_data.drop(competence_data[competence_data["competence"] == ""].index, inplace = True)
    competence_data = list(competence_data.itertuples(index = False, name = None))

    project_data = json.loads(project_data_store)
    if checked:
        functions.SetGroupProjectCompetence(competence_data, project_data["id"])
    else:
        functions.SetUserProjectCompetence(competence_data)
    functions.SetDefaultEdgeCompetence(project_data["id"])

    raise PreventUpdate


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление группами ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Открыть диалог создания / редактирования группы
@dash.callback(
    Output("settings_dialog_edit_usergroup", "opened", allow_duplicate = True), #Открыть диалог
    Output("settings_dialog_edit_usergroup_title", "children"),
    Output("settings_dialog_edit_usergroup_input", "value"),
    Output("settings_dialog_edit_usergroup_id", "children"),
    Output("settings_dialog_edit_usergroup_button_ok", "children"),
    Input({"type":"group_edit_button", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def modal_edit(edit_click):
    if len(edit_click) == edit_click.count(None): raise PreventUpdate
    if not ctx.triggered_id: raise PreventUpdate
    if ctx.triggered_id["type"] != "group_edit_button": raise PreventUpdate
    group_id = ctx.triggered_id["index"]

    if group_id == "0":
        return True, "Создание новой группы экспертов", "", None, "Создать"
    else:
        edit_click.pop(0)
        if len(edit_click) == edit_click.count(None): raise PreventUpdate

        group_data = functions.GetGroupDict(group_id)
        return True, "Изменение группы экспертов", group_data["group_name"], group_id, "Изменить"

#Кнопки диалога создания / редактирования группы
@dash.callback(
    output = {
        "dialog_opened": Output("settings_dialog_edit_usergroup", "opened", allow_duplicate = True),
        "group_list_table": Output("group_list_table", "children", allow_duplicate = True),
        "group_select_users": Output({"type": "grouplist_select", "index": "group_users"}, "data", allow_duplicate = True),
        "project_competence_table": Output("project_competence_table", "children", allow_duplicate = True),
        "competence_select_data": Output("competence_select", "data", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "ok_click": Input("settings_dialog_edit_usergroup_button_ok", "n_clicks"),
            "project_data_store": State("project_data_store", "data"),
            "group_id": State("settings_dialog_edit_usergroup_id", "children"),
            "group_name": State("settings_dialog_edit_usergroup_input", "value"),
            "group_competence_project_checkbox": State("group_checkbox_project", "checked"),
            "group_competence_edge_checkbox": State("group_checkbox_edge", "checked"),
        }
    },
    prevent_initial_call = True
)
def CreateEditProjectUserGroup(input):
    if not input["ok_click"]: raise PreventUpdate
    if input["project_data_store"] == None: raise PreventUpdate
    project_data = json.loads(input["project_data_store"])
    
    group_id = input["group_id"]
    group_name = input["group_name"]
    if group_id:
        if not functions.RenameGroup(group_name, group_id): raise PreventUpdate
    else:
        if not functions.AddGroup(group_name, project_data["id"]): raise PreventUpdate
   
    if input["group_competence_project_checkbox"]:
        project_competence_table = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))
    else:
        project_competence_table = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))

    output = {}
    output["dialog_opened"] = False
    output["group_list_table"] = GetTableProjectUserGroups(project_data["id"])
    output["group_select_users"] = functions.GetSelectData("competence_select", project_data["id"], True)
    output["project_competence_table"] = project_competence_table
    output["competence_select_data"] = functions.GetSelectData("competence_select", project_data["id"], input["group_competence_edge_checkbox"])

    return output


#Открыть диалог удаления группы проекта
@dash.callback(
    Output("settings_dialog_delete_usergroup", "opened", allow_duplicate = True), #Открыть диалог
    Output("settings_dialog_delete_usergroup_text", "children"),
    Output("settings_dialog_delete_usergroup_id", "children"),
    Input({"type":"group_delete_button", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def modal_delete(clickdata):
    if len(clickdata) == clickdata.count(None): raise PreventUpdate
    if not ctx.triggered_id: raise PreventUpdate
    if ctx.triggered_id["type"] != "group_delete_button": raise PreventUpdate
    group_id = ctx.triggered_id["index"]
    group_data = functions.GetGroupDict(group_id)
    return True, "Удалить группу '" + group_data["group_name"] + "'?", group_id

#Кнопки диалога удаления группы проекта
@dash.callback(
    output = {
        "dialog_opened": Output("settings_dialog_delete_usergroup", "opened", allow_duplicate = True),
        "group_list_table": Output("group_list_table", "children", allow_duplicate = True),
        "group_select_users": Output({"type": "grouplist_select", "index": "group_users"}, "data", allow_duplicate = True),
        "project_competence_table": Output("project_competence_table", "children", allow_duplicate = True),
        "competence_select_data": Output("competence_select", "data", allow_duplicate = True),
        "grouplist_select": Output({"type": "grouplist_select", "index": "group_users"}, "value"),
        
    },
    inputs = {
        "input": {
            "ok_click": Input("settings_dialog_delete_usergroup_button_ok", "n_clicks"),
            "cancel_click": Input("settings_dialog_delete_usergroup_button_cancel", "n_clicks"),
            "project_data_store": State("project_data_store", "data"),
            "group_id": State("settings_dialog_delete_usergroup_id", "children"),
            "group_competence_project_checkbox": State("group_checkbox_project", "checked"),
            "group_competence_edge_checkbox": State("group_checkbox_edge", "checked"),
        }
    },
    prevent_initial_call = True
)
def DeleteProjectUserGroup(input):

    output = {}
    output["dialog_opened"] = True
    output["group_list_table"] = no_update
    output["group_select_users"] = no_update
    output["project_competence_table"] = no_update
    output["competence_select_data"] = no_update
    output["grouplist_select"] = no_update

    if input["cancel_click"]:
        output["dialog_opened"] = False
        return output

    if not input["ok_click"]: raise PreventUpdate
    if input["project_data_store"] == None: raise PreventUpdate
    project_data = json.loads(input["project_data_store"])
    
    group_id = input["group_id"]
    if group_id:
        if not functions.DeleteGroup(group_id): raise PreventUpdate
   
    if input["group_competence_project_checkbox"]:
        project_competence_table = functions.CreateTableContent(["Группа", "Компетентность"], functions.GetGroupProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))
    else:
        project_competence_table = functions.CreateTableContent(["Пользователь", "Компетентность"], functions.GetUserProjectCompetenceData(project_data["id"], project_data["status"]["stage"]))

    output = {}
    output["dialog_opened"] = False
    output["group_list_table"] = GetTableProjectUserGroups(project_data["id"])
    output["group_select_users"] = functions.GetSelectData("competence_select", project_data["id"], True)
    #output["group_select_list"] = output["group_select_users"]
    output["project_competence_table"] = project_competence_table
    output["competence_select_data"] = output["group_select_users"] #if input["group_checkbox_state"]["edge"] else input["table_data"]["competence_select"]
    output["grouplist_select"] = None

    return output


#Выбор группы из списка - обновление таблицы, очистка пользователя
@dash.callback(
    Output("group_users_table", "children", allow_duplicate = True),
    Output("groupuser_select", "value", allow_duplicate = True),
    Input({"type": "grouplist_select", "index": "group_users"}, "value"),
    prevent_initial_call = True
)
def SelectUserGroups(groupselect_value):
    table_data = []
    if groupselect_value:
        table_data = GetTableGroupUsers(int(groupselect_value))
    return table_data, None

#Выбор пользователя из списка для добавления - проверяем и обновляем кнопку
@dash.callback(
    Output("groupadd_user", "disabled"),
    Input("groupuser_select", "value"),
    State({"type": "grouplist_select", "index": "group_users"}, "value"),
    prevent_initial_call = True
)
def SelectUserGroups(userselect_value, groupselect_value):
    add_button_disabled = not groupselect_value or not userselect_value
    if not add_button_disabled:
        add_button_disabled = functions.CheckIfUserInGroup(int(groupselect_value), int(userselect_value))

    return add_button_disabled

#Нажатия кнопок добавления и удаления (из табличной части)
@dash.callback(
    Output("group_users_table", "children", allow_duplicate = True),
    Output("groupuser_select", "value"),
    Input("groupadd_user", "n_clicks"),
    Input({"type": "groupdata_button", "index": ALL}, "n_clicks"),
    State({"type": "grouplist_select", "index": "group_users"}, "value"),
    State("groupuser_select", "value"),
    prevent_initial_call = True
)
def EditGroupUsers(groupadd_user, delete_click, groupselect_value, userselect_value):

    if ctx.triggered[0]["value"]:
        if "index" in ctx.triggered_id:
            if not functions.DeleteUserFromGroup(ctx.triggered_id["index"]): raise PreventUpdate
        else: 
            if not functions.AddUserToGroup(int(groupselect_value), int(userselect_value)): raise PreventUpdate

        table_data = GetTableGroupUsers(int(groupselect_value))

        return table_data, None
    
    raise PreventUpdate
       
