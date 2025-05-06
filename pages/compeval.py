import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, MATCH, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate

from flask import session
from flask_login import current_user, logout_user

import functions
import json

_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)


#Построить таблицу сравнительной оценки
def GetSimpleGrid(comp_data):
    superiority_data = comp_data["data"]
    source_node_name = superiority_data[0]["source_node_name"]
    targret_node_names = comp_data["node_names"]
    
    superior_check = True
    selected_table_id = comp_data["table_id"]
    for data in comp_data["data"]:
        if data["table_id"] == selected_table_id:
            superior_check = data["superior"]
            break

    matrix_dim = len(targret_node_names)

    simple_grid_children = [0] * pow(matrix_dim + 1, 2)
    for index, value in enumerate(simple_grid_children):
        simple_grid_children[index]=dmc.Box("")

    simple_grid_children[0] = dmc.Center(dmc.Text(source_node_name, truncate='end', pl=5), className="hi-cell-root") #корень 
    for index, targret_node_name in enumerate(targret_node_names): 
        simple_grid_children[index + 1] = dmc.Center(dmc.Text(targret_node_name, truncate='end', pl=5), className="hi-cell-up") #верхние 
        simple_grid_children[(matrix_dim + 2) * (index + 1)] = dmc.Center(dmc.Text("1"), className="hi-cell-ro") #диагональ
        simple_grid_children[(matrix_dim + 1) * (index + 1)] = dmc.Center(dmc.Text(targret_node_name, truncate='end', pl=5), className="hi-cell-left") #слева
    
    maxtrix_offset = 3
    list_index = matrix_dim + maxtrix_offset
    opp_index = matrix_dim + maxtrix_offset - 1
    for index, superiority_data_item in enumerate(superiority_data):
        
        opp_index += matrix_dim + 1
        
        table_id = superiority_data_item["table_id"]
        superiority_val = superiority_data_item["code"]

        if superiority_data_item["superior"]: 
            simple_grid_children[list_index] = dmc.Box(dmc.Button(
                id = {"type": "usercomp_button", "node_type": "upper_node", "table_id": table_id}, 
                children = str(superiority_val), 
                radius=0,
                className="hi-cell-btn" if selected_table_id!=table_id else "hi-cell-btn-sel" if superior_check else "hi-cell-btn-opp"),
                className="hi-cell")
            simple_grid_children[opp_index] = dmc.Box(dmc.Button(
                id = {"type": "usercomp_button", "node_type":"lower_node", "table_id": table_id}, 
                children = "1/" + str(superiority_val) if str(superiority_val) != "1" else "1", 
                radius=0, 
                className="hi-cell-btn" if selected_table_id!=table_id else "hi-cell-btn-sel" if not superior_check else "hi-cell-btn-opp"),
                className="hi-cell")
        else:
            simple_grid_children[list_index] = dmc.Box(dmc.Button(
                id = {"type": "usercomp_button", "node_type": "upper_node", "table_id": table_id}, 
                children = "1/" + str(superiority_val) if str(superiority_val) != "1" else "1", 
                radius=0, 
                className="hi-cell-btn" if selected_table_id!=table_id else "hi-cell-btn-sel" if superior_check else "hi-cell-btn-opp"),
                className="hi-cell")
            simple_grid_children[opp_index] = dmc.Box(dmc.Button(
                id = {"type": "usercomp_button", "node_type":"lower_node", "table_id": table_id}, 
                children = str(superiority_val),
                radius=0, 
                className="hi-cell-btn" if selected_table_id!=table_id else "hi-cell-btn-sel" if not superior_check else "hi-cell-btn-opp"),
                className="hi-cell")

        list_index += 1
        if list_index % (matrix_dim + 1) == 0:
            maxtrix_offset+=1 
            list_index += maxtrix_offset-1
            opp_index = list_index - 1


    return dmc.SimpleGrid(cols = matrix_dim + 1, spacing = '0', verticalSpacing = '0', children = simple_grid_children)

def GetSuperiorSet(source_node_name):
    dmc_SuperiorSet = dmc.Box(
    children = [
        dmc.Text(id = "poll_string", 
            children = [
                dmc.Text("Согласно критерию ", span = True, inherit = True),
                dmc.Text(id = "source_node_text", children = source_node_name, span = True, inherit = True, fw=500),
                dmc.Text(" значимость элемента ", span = True, inherit = True),
                dmc.Text(id = "target_node1_text", children = "t1_name", span = True, inherit = True, c = "var(--mantine-color-orange-6)"),
                dmc.Text(" ", span = True, inherit = True),
                dmc.Text(id = "superiority_text", children = "superiority name", span = True, inherit = True, c = "blue"),
                dmc.Text(" превосходит значимость элемента ", span = True, inherit = True),
                dmc.Text(id = "target_node2_text", children = "t2_name", span = True, inherit = True, c = "var(--mantine-color-orange-6)"),
            ],
            fz = 24,
            fw = 400,
        ),
        dmc.Slider(
            id = "superiority_slider",
            value = 1,
            min = 1, 
            max = 9, 
            restrictToMarks = True,
            thumbSize = 30,
            marks= [{"value": index, "label": str(index)} for index in range(1,10)],
        ),
    ], p = "lg",)
    
    return dmc_SuperiorSet

def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    #page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "compeval"}, pathname = "/login")
    elif not "page_compeval" in session:
        return dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/project")
    else:
        page_compeval = json.loads(session["page_compeval"])
        project_name_header_text = page_compeval["project_name"]
        source_node_id = page_compeval["current_node_id"]
        source_node_name = page_compeval["current_node_name"]

        layout = dmc.AppShell(
            children = [
                dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/compeval"),
                dcc.Store(id="project_data_store", storage_type='session', clear_data=True),
                dcc.Store(id="element_data_store", storage_type='session', clear_data=True),
                dcc.Store(id="comp_data_store", storage_type='session', clear_data=True),
                dcc.Interval(id={'type': 'load_interval', 'index': 'compeval'}, n_intervals=0, max_intervals=1, interval=1), # max_intervals=0 - запустится 1 раз
                dmc.AppShellHeader(
                    children = [
                        dmc.Box(
                            children = [
                                dmc.Flex(children=[dmc.NavLink(
                                    id = "compeval_to_project",
                                    label = "Вернуться к проекту",
                                    leftSection = DashIconify(icon = "mingcute:arrow-left-line"),
                                    )]),
                                dmc.Center(dmc.Text(project_name_header_text, size='lg')),
                                dmc.Group(children=[
                                dmc.Center(dmc.Text(functions.GetShortUsername(current_user.userdata["name"]))),
                                dmc.Flex(children=[dmc.NavLink(
                                    id = {"type": "logout_button", "index": "compeval"},
                                    label = "",
                                    leftSection = DashIconify(icon = "mingcute:exit-fill"),
                                    c='red'
                                    )]),
                                ]),
                            ],
                            px = "md",
                            style = {"display":"flex", "justify-content":"space-between"}
                        )
                    ], withBorder=False
                ),
                dmc.AppShellMain(children=[
                    dmc.Container(id="comp_simple_grid", children=[], size='90%'),
                    dmc.Container(id="comp_superior_set", children=GetSuperiorSet(source_node_name), size='90%', display='none')
                ])
            ],
            header={"height": "50px"},
        )

        layout = dmc.MantineProvider(layout)
        return layout

#Однократный запуск при обновлении страницы
@dash.callback(
    output = {
        "comp_data_store": Output("comp_data_store", 'data', allow_duplicate = True),
        "comp_simple_grid": Output("comp_simple_grid", "children", allow_duplicate = True),
        "target_node1_text": Output("target_node1_text", "children", allow_duplicate = True),
        "target_node2_text": Output("target_node2_text", "children", allow_duplicate = True),
        "superiority_slider_value": Output("superiority_slider", "value", allow_duplicate = True),
        "comp_superior_set_display": Output("comp_superior_set", "display", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "n_intervals": Input(component_id={'type': 'load_interval', 'index': 'compeval'}, component_property="n_intervals"),
        }
    },
    prevent_initial_call = True
)
def update_store(input):
    page_compeval = json.loads(session["page_compeval"])
    project_data = functions.GetProjectData(current_user.userdata["id"], page_compeval["project_id"])
    source_node_id = page_compeval["current_node_id"]
    source_node_name = page_compeval["current_node_name"]

    comp_data = {}
    comp_data["source_node_name"]=source_node_name
    comp_data["cursor"]=0
    comp_data["superiority"] = functions.GetSuperiorityNames()
    comp_data["data"] = functions.GetUserCompdataForSimpleGrid(source_node_id, current_user.userdata["id"])
    node_names = functions.GetUserNodesForSimpleGrid(source_node_id, project_data)
    node_names.sort() 
    comp_data["node_names"] = node_names
    comp_data["table_id"]=None

    selected_table_id = comp_data["data"][0]["table_id"]
    selected_data = None
    for data_ in comp_data["data"]:
        if data_["table_id"] == selected_table_id:
            selected_data = data_
            break
    
    output = {}
    
    if not selected_data:
        comp_superior_set_display = "none"
        output["target_node1_text"] = ""
        output["target_node2_text"] = ""
        #output["superiority_radiogroup_value"] = "1"
        #output["superiority_radio1_text"] = ""
        #output["superiority_radio2_text"] = ""
        output["superiority_slider_value"] = 1
        output["comp_superior_set_display"] = 'none'
    else:
        comp_data["table_id"] = selected_table_id
        output["comp_superior_set_display"] = 'block'
        calc_outputs = GetOutputs(selected_data)
        output["target_node1_text"] = calc_outputs["target_node1_text"]
        output["target_node2_text"] = calc_outputs["target_node2_text"]
        #output["superiority_radiogroup_value"] = calc_outputs["superiority_radiogroup_value"]
        #output["superiority_radio1_text"] = calc_outputs["superiority_radio1_text"]
        #output["superiority_radio2_text"] = calc_outputs["superiority_radio2_text"]
        output["superiority_slider_value"] = calc_outputs["superiority_slider_value"]


    dmc_SimpleGrid = GetSimpleGrid(comp_data)

    output["comp_data_store"] = json.dumps(comp_data, cls = functions.NpEncoder)
    output["comp_simple_grid"] = dmc_SimpleGrid
    

    return output


#Навигация ----------------------------------------------------------------------------------------------------

@dash.callback(
    Output({"type": "redirect", "index": "compeval"}, "pathname", allow_duplicate = True),
    Input({"type": "logout_button", "index": "compeval"}, "n_clicks"),
    prevent_initial_call = True
)
def Logout(clickdata):
    if clickdata:
        session.clear()
        logout_user()
        return "/login"


@dash.callback(
    Output({"type": "redirect", "index": "compeval"}, "pathname", allow_duplicate = True),
    Input("compeval_to_project", "n_clicks"),
    prevent_initial_call = True
)
def RedirectToProject(clickdata):
    if clickdata is None:
        raise PreventUpdate
    else:
        page_compeval = json.loads(session["page_compeval"])
        page_project = {}
        page_project["project_id"] = page_compeval["project_id"]
        session["page_project"] = json.dumps(page_project, cls = functions.NpEncoder)
    
        return "/project"



def GetOutputs(selected_data):
    superior_value = selected_data["code"]

    radio1_text = "Превосходство " + selected_data["t1_node_name"] + " над " + selected_data["t2_node_name"]
    radio2_text = "Превосходство " + selected_data["t2_node_name"] + " над " + selected_data["t1_node_name"]
    
    if selected_data["superior"]:
        radio_value="1"
        text_from = selected_data["t1_node_name"]
        text_to = selected_data["t2_node_name"]
        superiority_type_text = radio1_text
    else:
        radio_value="2"
        text_from = selected_data["t2_node_name"]
        text_to = selected_data["t1_node_name"]
        superiority_type_text = radio2_text

    output = {}
    output["target_node1_text"] = text_from
    output["target_node2_text"] = text_to
    output["superiority_radiogroup_value"] = radio_value
    output["superiority_radio1_text"] = radio1_text
    output["superiority_radio2_text"] = radio2_text
    output["superiority_slider_value"] = superior_value
    output["superiority_type_text"] = superiority_type_text

    return output

#Обработка ----------------------------------------------------------------------------------------------------

@dash.callback(
    output = {
        "comp_data_store": Output("comp_data_store", 'data', allow_duplicate = True),
        "comp_simple_grid": Output("comp_simple_grid", "children", allow_duplicate = True),
        "target_node1_text": Output("target_node1_text", "children", allow_duplicate = True),
        "target_node2_text": Output("target_node2_text", "children", allow_duplicate = True),
        "superiority_slider_value": Output("superiority_slider", "value"),
        "comp_superior_set_display": Output("comp_superior_set", "display", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "clickdatas": Input({"type": "usercomp_button", "node_type":ALL, "table_id": ALL}, "n_clicks"),
            "comp_data_store": State("comp_data_store", 'data'),
        }
    },
    prevent_initial_call = True
)
def TableBtnClick(input): # clickdatas, values, comp_data_store
    clickdatas = input["clickdatas"]
    comp_data_store = input["comp_data_store"]

    if len(clickdatas) == clickdatas.count(None): raise PreventUpdate
    if not ctx.triggered_id: raise PreventUpdate
    if ctx.triggered_id["type"] != "usercomp_button": raise PreventUpdate
    if comp_data_store == None: raise PreventUpdate
    comp_data = json.loads(comp_data_store)
    
    selected_table_id = ctx.triggered_id["table_id"]
    selected_data = None
    for data_ in comp_data["data"]:
        if data_["table_id"] == selected_table_id:
            selected_data = data_
            break
    if not selected_data: raise PreventUpdate


    if comp_data["table_id"] == selected_table_id:
        superior_check = selected_data["superior"]

        superior_check = not superior_check #Инверсия
        superior_check_old = selected_data["superior"]
        selected_data["superior"] = superior_check

        #Записать в базу данных данные по selectes_table_id если superior_value не равно 1 (смысла нет, виртуальные переключения)
        superior_value = selected_data["code"]
        if superior_value != 1:
            if not functions.SaveCompEvalToBD(selected_data):
                selected_data["superior"] = superior_check_old
                raise PreventUpdate
    else:
        comp_data["table_id"] = selected_table_id

    calc_outputs = GetOutputs(selected_data)

    dmc_SimpleGrid = GetSimpleGrid(comp_data)
    
    output = {}
    output["comp_data_store"] = json.dumps(comp_data, cls = functions.NpEncoder)
    output["comp_simple_grid"] = dmc_SimpleGrid
    output["target_node1_text"] = calc_outputs["target_node1_text"]
    output["target_node2_text"] = calc_outputs["target_node2_text"]
    #output["superiority_radiogroup_value"] = calc_outputs["superiority_radiogroup_value"]
    #output["superiority_radio1_text"] = calc_outputs["superiority_radio1_text"]
    #output["superiority_radio2_text"] = calc_outputs["superiority_radio2_text"]
    output["superiority_slider_value"] = calc_outputs["superiority_slider_value"]
    #output["superiority_type_text"] = calc_outputs["superiority_type_text"]
    output["comp_superior_set_display"] = 'block'

    return output


@dash.callback(
    output = {
        "comp_data_store": Output("comp_data_store", 'data', allow_duplicate = True),
        "comp_simple_grid": Output("comp_simple_grid", "children", allow_duplicate = True),
        "superiority_text": Output("superiority_text", "children", allow_duplicate = True),
    },
    inputs = {
        "input": {
            "superiority_slider_value": Input("superiority_slider", "value"),
            "comp_data_store": State("comp_data_store", 'data'),
        }
    },
    prevent_initial_call = True
)
def SuperioritySlider(input):
    comp_data_store = input["comp_data_store"]
    if comp_data_store == None: raise PreventUpdate
    comp_data = json.loads(comp_data_store)
    
    selected_table_id = comp_data["table_id"]
    selected_data = None
    for data_ in comp_data["data"]:
        if data_["table_id"] == selected_table_id:
            selected_data = data_
            break
    if not selected_data: raise PreventUpdate

    value = input["superiority_slider_value"]
    value_old = selected_data["code"]
    selected_data["code"] = value

    #Записать в базу данных данные по selectes_table_id, но если superior_value равно 1, то поставить superior_check=True (только в базе)
    if value_old != value:
        if not functions.SaveCompEvalToBD(selected_data):
            selected_data["code"] = value_old
            raise PreventUpdate

    calc_outputs = GetOutputs(selected_data)
    dmc_SimpleGrid = GetSimpleGrid(comp_data)

    superiority_text = comp_data["superiority"][str(value)]

    output = {}
    output["comp_data_store"] = json.dumps(comp_data, cls = functions.NpEncoder)
    output["comp_simple_grid"] = dmc_SimpleGrid
    output["superiority_text"] = superiority_text

    return output
