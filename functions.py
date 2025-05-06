from PIL import ImageFont
import dash_mantine_components as dmc
import pandas as pd
import uuid
import psycopg2
import numpy as np
import json
from flask_login import UserMixin

#Соединение с БД
#connection = psycopg2.connect(host='localhost', database='hierarchy', user='postgres', password='228228', port = 5432)
connection = psycopg2.connect(host='192.168.1.102', database='hierarchy', user='postgres', password='228228', port = 5432)
cursor = connection.cursor()

#Класс пользователя для аутентификации
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.userdata = GetUserData(username)

#Кодировка для json
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


font_props = {
    "font-family": "times.ttf",
    "font-size": 16,
    "font-height": 16
}

nodebox_props = {
    "width": 100,
    "height": 50,
    "margin-x": 25,
    "margin-y": 25,
    "padding-x": 10,
    "padding-y": 10
}


cons_coef_data = {
    1: 0,
    2: 0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49
}




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Получение данных для построения иерархии ----------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Получить датафрейм вершин из базы
def GetNodes(project_id):
    query = f"""select uuid, node_name from tbl_nodes
        where project_id = {project_id}
        order by node_name, id"""
    cursor.execute(query)
    nodes = pd.DataFrame(cursor.fetchall(), columns = ["id", "name"])

    return nodes

#Получить ребра базовой иерархии
def GetEdges(project_id):
    query = f"""select 
        tbl_edges.uuid, 
        source.uuid as source_id, 
        target.uuid as target_id,
        false as deleted
        from
        tbl_edges
        inner join tbl_nodes as source on source.id = tbl_edges.source_id
        inner join tbl_nodes as target on target.id = tbl_edges.target_id
        where 
        tbl_edges.project_id = {project_id}
        order by source.node_name, source.id, target.node_name, target.id"""
        
    cursor.execute(query)
    edges = pd.DataFrame(cursor.fetchall(), columns = ["id", "source", "target", "deleted"])

    return edges

#Получить ребра иерархии, созданной пользователем на этапе оценки зависимостей
def GetEdgedata(project_id, user_id):
    query = f"""select 
        tbl_edges.uuid, 
        source.uuid as source_id, 
        target.uuid as target_id,
        tbl_edgedata.deleted
        from
        tbl_edgedata 
        inner join tbl_edges on tbl_edges.id = tbl_edgedata.edge_id
        inner join tbl_nodes as source on source.id = tbl_edges.source_id
        inner join tbl_nodes as target on target.id = tbl_edges.target_id
        where
        tbl_edges.project_id = {project_id} and
        tbl_edgedata.user_id = {user_id}
        order by source.node_name, source.id, target.node_name, target.id"""
        
    cursor.execute(query)
    edgedata = pd.DataFrame(cursor.fetchall(), columns = ["id", "source", "target", "deleted"])
    return edgedata

#Получить ребра с коэффициентом объединения
def GetMergedEdges(project_id):
    query = f"""select 
        rated_edges.uuid, 
        source.uuid as source_id, 
        target.uuid as target_id,
        rated_edges.deleted,
        rated_edges.merge_coef
        from
        (
            select
            sum(tbl_edgedata.competence * (not deleted)::int) / sum(tbl_edgedata.competence) as merge_coef,
            uuid,
            case 
                when 0.8 > 0 and sum(tbl_edgedata.competence * (not deleted)::int) / sum(tbl_edgedata.competence) < 0.8 then true
                when 0.8 > 0 and sum(tbl_edgedata.competence * (not deleted)::int) / sum(tbl_edgedata.competence) >= 0.8 then false
                when 0.8 = 0 and sum(tbl_edgedata.competence * (not deleted)::int) / sum(tbl_edgedata.competence) = 0.8 then true
            end as deleted
            from
            tbl_edgedata
            inner join tbl_userdata on tbl_userdata.user_id = tbl_edgedata.user_id
            inner join tbl_edges on tbl_edges.id = tbl_edgedata.edge_id
            where
            tbl_edges.project_id = {project_id} and
            tbl_userdata.de_completed = true
            group by uuid
        ) as rated_edges
        inner join tbl_edges on tbl_edges.uuid = rated_edges.uuid
        inner join tbl_nodes as source on source.id = tbl_edges.source_id
        inner join tbl_nodes as target on target.id = tbl_edges.target_id
        order by source.node_name, source.id, target.node_name, target.id"""
    
    cursor.execute(query)
    merged_edges = pd.DataFrame(cursor.fetchall(), columns = ["id", "source", "target", "deleted", "merge_coef"])
    return merged_edges

#Получить датафрейм ребер из базы в зависимости от этапа проекта
def GetProjectEdges(project_data, user_id):
    if project_data["status"]["code"] == "initial": 
        edges = GetEdges(project_data["id"])
    elif project_data["status"]["code"] == "dep_eval": 
        edges = GetEdgedata(project_data["id"], user_id)
        if not len(edges): edges = GetEdges(project_data["id"])
    else:
        edges = GetMergedEdges(project_data["id"])

    return edges

#Получить датафреймы вершин и ребер из базы
def GetProjectDfs(project_data, user_id = None):
    nodes_df = GetNodes(project_data["id"])
    edges_df = GetProjectEdges(project_data, user_id)

    nodes_df, edges_df = ExcludeDeletedElements(nodes_df, edges_df, "delete")
    nodes_df = GetNodeLevels(nodes_df, edges_df)

    return nodes_df, edges_df

def GetAnalyticsGraphDfs(project_id, user_id = None):
    nodes_df = GetNodes(project_id)

    if user_id: edges_df = GetEdgedata(project_id, user_id)
    else: edges_df = GetMergedEdges(project_id)

    nodes_df, edges_df = ExcludeDeletedElements(nodes_df, edges_df, "highlight")
    nodes_df = GetNodeLevels(nodes_df, edges_df)

    return nodes_df, edges_df

#Очистить датафреймы вершин и ребер от удаленных элементов
def ExcludeDeletedElements(nodes_df, edges_df, type):
    if len(nodes_df):
        head_id = nodes_df.loc[~nodes_df["id"].isin(edges_df["target"])].iloc[0]["id"]

        if type == "highlight":
            nodes_df["classes"] = "default"
            edges_df["classes"] = "default"

            edges_df.loc[edges_df["deleted"] == True, "classes"] = "deleted"
            nodes_df.loc[~nodes_df["id"].isin(edges_df[edges_df["deleted"] == False]["target"]) & (nodes_df["id"] != head_id), "classes"] = "deleted"

        if type == "delete":
            edges_df.drop(edges_df.loc[edges_df["deleted"] == True].index, inplace = True)
            nodes_df.drop(nodes_df.loc[~nodes_df["id"].isin(edges_df["target"]) & (nodes_df["id"] != head_id)].index, inplace = True)


    return nodes_df, edges_df

#Дополнить датафрейм с элементами иерархии колонкой с их уровнями
def GetNodeLevels(nodes_df, edges_df):
    nodes_df["level"] = 0

    if len(nodes_df):
        head_id = nodes_df.loc[~nodes_df["id"].isin(edges_df["target"])].iloc[0]["id"]
        source_id = head_id
        nodes_df.loc[nodes_df["id"] == head_id, "level"] = 1

        visited = []
        while len(visited) < len(nodes_df):
            source_id = nodes_df.loc[~nodes_df["id"].isin(visited) & (nodes_df["level"] != 0)].iloc[0]["id"]
            children = list(edges_df[edges_df["source"] == source_id]["target"])
            for child_id in children: nodes_df.loc[nodes_df["id"] == child_id, "level"] = nodes_df.loc[nodes_df["id"] == source_id, "level"].values[0] + 1
            visited.append(source_id)
        
    return nodes_df.sort_values(by = ["level", "name"])




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Построение иерархии -------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Получить элементы для отрисовки при инициализации
def GetHierarchyPreset(nodes_df, edges_df):
    node_list = []
    edge_list = []

    if len(nodes_df):
        for level in range(1, nodes_df["level"].max() + 1):
            nodelevel_df = nodes_df.loc[nodes_df["level"] == level]
            for index, row in nodelevel_df.iterrows():
                node_data = {}
                node_data["id"] = row["id"]
                node_data["name"] = row["name"]
                node_data["width"] = 0
                node_data["height"] = 0
                node_data["level"] = level

                if "priority" in row: 
                    node_data["priority"] = row["priority"]
                    node_data["cons_coef"] = row["cons_coef"]
                    node_data["full_name"] = row["name"] + f"\n (Вес: {row['priority']}, ОС: {row['cons_coef']})"

                node_position = {}
                node_position["x"] = 0
                node_position["y"] = 0

                node_object = {}
                node_object["data"] = node_data
                node_object["position"] = node_position

                if "classes" in row: node_object["classes"] = row["classes"]
                else: node_object["classes"] = "default"

                node_list.append(node_object)

        node_list = RefreshNodePositionsSizes(node_list)

        for index, row in edges_df.iterrows():
            edge_data = {}
            edge_data["id"] = row["id"]
            edge_data["source"] = row["source"]
            edge_data["target"] = row["target"]

            if "local_priority" in row: edge_data["local_priority"] = row["local_priority"]
            if "merge_coef" in row: edge_data["merge_coef"] = row["merge_coef"]

            edge_object = {}
            edge_object["data"] = edge_data
            edge_object["classes"] = "default"

            if "classes" in row: edge_object["classes"] = row["classes"]
            else: edge_object["classes"] = "default"

            edge_list.append(edge_object)
        
    return node_list + edge_list

#Перезаписать позиции и размеры вершин после изменения
def RefreshNodePositionsSizes(elements):
    nodes_df, edges_df = ElementsToDfs(elements)
    nodebox_df = GetHierarchyInfo(nodes_df)

    element_counter = {}
    for index, row in nodebox_df.iterrows(): element_counter[row["level"]] = 0

    for element in elements:
        if "source" not in element["data"]:
            element["data"]["width"] = nodebox_df.iloc[element["data"]["level"] - 1]["node_width"]
            element["data"]["height"] = nodebox_df.iloc[element["data"]["level"] - 1]["node_height"]
            element["position"]["x"] = (nodebox_df["level_width"].max() - nodebox_df.iloc[element["data"]["level"] - 1]["level_width"] + element["data"]["width"] + 2 * nodebox_props["margin-x"]) / 2 + (element["data"]["width"] + 2 * nodebox_props["margin-x"]) * element_counter[element["data"]["level"]] + 600
            element["position"]["y"] = nodebox_df[:element["data"]["level"] - 1]["node_height"].sum() + element["data"]["height"] / 2 + nodebox_props["margin-y"] * 2 * (element["data"]["level"] - 1) + 30
            element_counter[element["data"]["level"]] += 1

    return elements

#Покрасить элементы
def ColorElements(element_data):
    for element in element_data["elements"]:
        if element_data["state"]["selected"] and element_data["state"]["selected"]["data"]["id"] == element["data"]["id"]: 
            element["classes"] = "selected"
            continue

        if element["data"]["id"] in element_data["state"]["manually_deleted"].keys(): 
            element["classes"] = "manually_deleted"
            continue

        if element["data"]["id"] in element_data["state"]["cascade_deleted"].keys(): 
            element["classes"] = "cascade_deleted"
            continue

        if element["data"]["id"] in element_data["state"]["added"].keys(): 
            element["classes"] = "added"
            continue
        
        element["classes"] = "default"

#Покрасить элементы
def ColorAnalyticsElements(element_data, cons_coef = None):
    for element in element_data["elements"]:
        if element_data["selected"] and element_data["selected"]["data"]["id"] == element["data"]["id"]: 
            element["classes"] = "selected"
            continue

        if cons_coef:
            if cons_coef in element["data"]:
                if element["data"]["cons_coef"] > cons_coef: 
                    element["classes"] = "bad"
                    continue
                else:
                    element["classes"] = "good"
                    continue

        if element["data"]["deleted"]: 
            element["classes"] = "deleted"
            continue

        element["classes"] = "default"

#Получить ширину текста в пикселях
def GetTextWidth(font, line):
    left, top, right, bottom = font.getbbox(line)
    width = right - left
    return width

#Получить ширину и высоту элемента иерархии по его названию
def GetNodebox(text):
    global font_props
    global nodebox_props

    textbox_width = nodebox_props["width"] - nodebox_props["padding-x"] * 2
    textbox_height = nodebox_props["height"] - nodebox_props["padding-y"] * 2

    font = ImageFont.truetype(font_props["font-family"], font_props["font-size"])
    
    line = ""
    height_counter = 0
    if "\n" in text: height_counter += font_props["font-height"]

    words = text.split(" ")

    for word in words:
        line += " " + word
        line = line.strip()

        width = GetTextWidth(font, line)
        if width > textbox_width:
            if " " not in line: textbox_width = width
            line = word
            width = GetTextWidth(font, line)
            if width > textbox_width: textbox_width = width
            else: height_counter += font_props["font-height"]

    if textbox_height < height_counter: textbox_height = height_counter

    nodebox_width = nodebox_props["width"]
    nodebox_height = nodebox_props["height"]

    required_width = textbox_width + nodebox_props["padding-x"] * 2
    required_height = textbox_height + nodebox_props["padding-y"] * 2
      
    if required_width > nodebox_props["width"]: nodebox_width = required_width
    if required_height > nodebox_props["height"]: nodebox_height = required_height

    return nodebox_width, nodebox_height

#Информация об уровне иерархии
def GetLevelInfo(nodes_df, level):
    nodebox = {"level": level, "level_width": 0, "node_width": nodebox_props["width"], "node_height": nodebox_props["height"]}
    
    nodelevel_df = nodes_df.loc[nodes_df["level"] == level]
    for index, row in nodelevel_df.iterrows():
        if "full_name" in row: width, height = GetNodebox(row["full_name"])
        else: width, height = GetNodebox(row["name"])
        if nodebox["node_width"] < width: nodebox["node_width"] = width
        if nodebox["node_height"] < height: nodebox["node_height"] = height

    nodebox["level_width"] = (nodebox["node_width"] + 2 * nodebox_props["margin-x"]) * (len(nodelevel_df))
    nodebox["level"] = level

    return nodebox

#Информация о иерархии
def GetHierarchyInfo(nodes_df):
    if len(nodes_df):
        nodebox_list = []
        for level in range(1, nodes_df["level"].max() + 1):
            nodebox = GetLevelInfo(nodes_df, level)
            nodebox_list.append(nodebox)
        nodebox_df = pd.DataFrame(nodebox_list).sort_values(by="level")
    else: nodebox_df = pd.DataFrame()

    return nodebox_df




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Редактирование иерархии ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Удалить ребро
def DeleteEdge(nodes_df, edges_df, edge_id, element_data):
    root_edge = GetElementById(edge_id, element_data["elements"])
    if root_edge["data"]["id"] not in element_data["state"]["manually_deleted"].keys():
        element_data["state"]["cascade_deleted"][root_edge["data"]["id"]] = root_edge

    if root_edge["data"]["target"] in element_data["state"]["added"].keys(): incoming_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & ~(edges_df["id"].isin(list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys())))]
    else: 
        incoming_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & ~(edges_df["id"].isin(list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys()))) & ~(edges_df["id"].isin(element_data["state"]["added"].keys()))]
        if len(incoming_edges) > 0: return
        else:
            added_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & (edges_df["id"].isin(element_data["state"]["added"].keys()))]
            for index, row in added_edges.iterrows(): element_data["state"]["cascade_deleted"][row["id"]] = GetElementById(row["id"], element_data["elements"])

    if len(incoming_edges) > 0: return

    current_node = GetElementById(root_edge["data"]["target"], element_data["elements"])
    if current_node["data"]["id"] not in element_data["state"]["manually_deleted"].keys():
        element_data["state"]["cascade_deleted"][current_node["data"]["id"]] = current_node

    outcoming_edges = edges_df.loc[edges_df["source"] == current_node["data"]["id"]]
    for index, row in outcoming_edges.iterrows():
        DeleteEdge(nodes_df, edges_df, row["id"], element_data)

#Удалить элемент
def DeleteElement(deleted_element, element_data):
    if deleted_element not in element_data["elements"]: deleted_element = GetEdge(deleted_element["data"]["source"], deleted_element["data"]["target"], element_data["elements"])

    element_data["state"]["manually_deleted"][deleted_element["data"]["id"]] = deleted_element
    nodes_df, edges_df = ElementsToDfs(element_data["elements"])

    if "source" in deleted_element["data"]:
        DeleteEdge(nodes_df, edges_df, deleted_element["data"]["id"], element_data)
    else:
        incoming_edges = edges_df.loc[(edges_df["target"] == deleted_element["data"]["id"]) & ~(edges_df["id"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]
        for index, row in incoming_edges.iterrows():
            element_data["state"]["cascade_deleted"][row["id"]] = GetElementById(row["id"], element_data["elements"])

        outcoming_edges = edges_df.loc[(edges_df["source"] == deleted_element["data"]["id"]) & ~(edges_df["id"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]
        for index, row in outcoming_edges.iterrows():
            DeleteEdge(nodes_df, edges_df, row["id"], element_data)

#Отменить удаление ребра
def CancelDeleteEdge(nodes_df, edges_df, edge_id, element_data):
    root_edge = GetElementById(edge_id, element_data["elements"])

    if root_edge["data"]["target"] not in element_data["state"]["manually_deleted"].keys():

        cascade_deleted_incoming_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & (edges_df["id"].isin(element_data["state"]["cascade_deleted"].keys())) & ~(edges_df["source"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]
        for index, row in cascade_deleted_incoming_edges.iterrows(): del element_data["state"]["cascade_deleted"][row["id"]]

        if len(cascade_deleted_incoming_edges) > 0 and root_edge["data"]["target"] in element_data["state"]["cascade_deleted"].keys():
            del element_data["state"]["cascade_deleted"][root_edge["data"]["target"]]

            cascade_deleted_outcoming_edges = edges_df.loc[(edges_df["source"] == root_edge["data"]["target"]) & (edges_df["id"].isin(element_data["state"]["cascade_deleted"].keys()))]
            for index, row in cascade_deleted_outcoming_edges.iterrows():
                if (row["source"] in element_data["state"]["added"].keys() and row["target"] in element_data["state"]["added"].keys()) or row["source"] not in element_data["state"]["added"].keys() or row["target"] not in list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys()):
                    CancelDeleteEdge(nodes_df, edges_df, row["id"], element_data)

#Отменить удаление элемента
def CancelDeleteElement(deleted_element, element_data):
    if deleted_element not in element_data["elements"]: deleted_element = GetEdge(deleted_element["data"]["source"], deleted_element["data"]["target"], element_data["elements"])

    if deleted_element["data"]["id"] in element_data["state"]["manually_deleted"].keys(): del element_data["state"]["manually_deleted"][deleted_element["data"]["id"]]
    element_data["state"]["cascade_deleted"][deleted_element["data"]["id"]] = deleted_element
    nodes_df, edges_df = ElementsToDfs(element_data["elements"])

    if "source" in deleted_element["data"]:
        CancelDeleteEdge(nodes_df, edges_df, deleted_element["data"]["id"], element_data)
    else:
        cascade_deleted_incoming_edges = edges_df.loc[(edges_df["target"] == deleted_element["data"]["id"]) & (edges_df["id"].isin(element_data["state"]["cascade_deleted"].keys())) & ~(edges_df["source"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]
        for index, row in cascade_deleted_incoming_edges.iterrows():
            del element_data["state"]["cascade_deleted"][row["id"]]

        if len(cascade_deleted_incoming_edges) > 0 or deleted_element["data"]["level"] == 1: 
            del element_data["state"]["cascade_deleted"][deleted_element["data"]["id"]]

            cascade_deleted_outcoming_edges = edges_df.loc[(edges_df["source"] == deleted_element["data"]["id"]) & (edges_df["id"].isin(element_data["state"]["cascade_deleted"].keys()))]
            for index, row in cascade_deleted_outcoming_edges.iterrows():
                if (row["source"] in element_data["state"]["added"].keys() and row["target"] in element_data["state"]["added"].keys()) or row["source"] not in element_data["state"]["added"].keys() or row["target"] not in list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys()):
                    CancelDeleteEdge(nodes_df, edges_df, row["id"], element_data)

#Добавить новое ребро
def AddEdge(edge_object, element_data):
    element_data["elements"].append(edge_object)
    element_data["state"]["added"][edge_object["data"]["id"]] = edge_object

    deleted_ids = list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())
    if edge_object["data"]["source"] in deleted_ids or edge_object["data"]["target"] in deleted_ids: element_data["state"]["cascade_deleted"][edge_object["data"]["id"]] = edge_object

#Добавить новую вершину
def AddElement(element, element_data):
    if "source" in element["data"]:
        AddEdge(element, element_data)
    else:
        nodes_df, edges_df = ElementsToDfs(element_data["elements"])

        element_data["elements"].append(element)
        element_data["state"]["added"][element["data"]["id"]] = element

        deleted = True
        upper_level_nodes = nodes_df.loc[nodes_df["level"] == element["data"]["level"] - 1]
        for index, row in upper_level_nodes.iterrows():
            AddEdge(CreateEdgeObject(row["id"], element["data"]["id"]), element_data)
            if row["id"] not in list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys()): deleted = False

        if deleted and len(upper_level_nodes): element_data["state"]["cascade_deleted"][element["data"]["id"]] = element

        lower_level_nodes = nodes_df.loc[nodes_df["level"] == element["data"]["level"] + 1]
        for index, row in lower_level_nodes.iterrows():
            AddEdge(CreateEdgeObject(element["data"]["id"], row["id"]), element_data)

#Отменить добавление элемента
def CancelAddElement(added_element, element_data):
    del element_data["state"]["added"][added_element["data"]["id"]]
    if added_element["data"]["id"] in element_data["state"]["manually_deleted"].keys(): del element_data["state"]["manually_deleted"][added_element["data"]["id"]]
    if added_element["data"]["id"] in element_data["state"]["cascade_deleted"].keys(): del element_data["state"]["cascade_deleted"][added_element["data"]["id"]]

    if "source" not in added_element["data"]:
        nodes_df, edges_df = ElementsToDfs(element_data["elements"])
        node_edges = edges_df.loc[(edges_df["source"] == added_element["data"]["id"]) | (edges_df["target"] == added_element["data"]["id"])]
        for index, row in node_edges.iterrows():
            del element_data["state"]["added"][row["id"]]
            if row["id"] in element_data["state"]["manually_deleted"].keys(): del element_data["state"]["manually_deleted"][row["id"]]
            if row["id"] in element_data["state"]["cascade_deleted"].keys(): del element_data["state"]["cascade_deleted"][row["id"]]
            element_data["elements"].remove(GetElementById(row["id"], element_data["elements"]))

    element_data["elements"].remove(added_element)
    if element_data["state"]["selected"] not in element_data["elements"]: element_data["state"]["selected"] = None

#Отменить выбор элемента
def DeselectElement(element_data):
    if element_data["state"]["selected"]:
        selected_element = GetElementById(element_data["state"]["selected"]["data"]["id"], element_data["elements"])
        if selected_element["data"]["id"] in element_data["state"]["manually_deleted"].keys(): selected_element["classes"] = "manually_deleted"
        elif selected_element["data"]["id"] in element_data["state"]["cascade_deleted"].keys(): selected_element["classes"] = "cascade_deleted"
        else: selected_element["classes"] = "default"
        element_data["state"]["selected"] = None

#Создать объект "Вершина"
def CreateNodeObject(parent_node):
    node_data = {}
    node_data["id"] = str(uuid.uuid4())
    node_data["name"] = "Новая вершина"
    if parent_node: node_data["level"] = parent_node["data"]["level"] + 1
    else: node_data["level"] = 1
    node_data["width"] = 0
    node_data["height"] = 0
    
    node_position = {}
    node_position["x"] = 0
    node_position["y"] = 0

    node_object = {}
    node_object["data"] = node_data
    node_object["position"] = node_position
    node_object["classes"] = "added"

    return node_object

#Создать объект "Ребро"
def CreateEdgeObject(source_id, target_id):
    edge_data = {}
    edge_data["id"] = str(uuid.uuid4())
    edge_data["source"] = source_id
    edge_data["target"] = target_id

    edge_object = {}
    edge_object["data"] = edge_data
    edge_object["classes"] = "added"

    return edge_object

#Добавить шаг в историю
def AddStep(element, element_data, action):
    step = {}
    step["element"] = element
    step["action"] = action
    element_data["steps"]["history"].append(step)
    element_data["steps"]["canceled"] = []

#Очистить список элементов от удаленных
def RemoveDeletedElements(element_data, deleted_elements):
    element_data["state"]["manually_deleted"] = {}
    element_data["state"]["cascade_deleted"] = {}
    element_data["state"]["added"] = {}
    element_data["steps"]["history"] = []
    element_data["steps"]["canceled"] = []

    for element in deleted_elements: element_data["elements"].remove(element)

#Записать граф в базу
def SaveInitialGraphToDB(element_data, project_id):
    nodes_df, edges_df = ElementsToDfs(element_data["elements"])
    nodes_df.drop(["width", "height", "level", "classes"], axis = 1, inplace = True)
    edges_df.drop(["deleted", "classes"], axis = 1, inplace = True)

    nodes_df["project_id"] = project_id
    edges_df["project_id"] = project_id
    edges_df["source_id"] = 0
    edges_df["target_id"] = 0

    DeselectElement(element_data)

    deleted_elements = []
    for element in element_data["elements"]:
        if element["classes"] not in ["default", "added"]:
            if "source" in element["data"]: edges_df.drop(edges_df.loc[edges_df["id"] == element["data"]["id"]].index, inplace = True)
            else: nodes_df.drop(nodes_df.loc[nodes_df["id"] == element["data"]["id"]].index, inplace = True)
            deleted_elements.append(element)
        else: element["classes"] = "default"

    try:
        node_tuples = list(nodes_df.itertuples(index = False, name = None))
        node_args = ','.join(cursor.mogrify("(%s,%s,%s)", i).decode('utf-8') for i in node_tuples)

        cursor.execute(f"delete from tbl_nodes where project_id = {project_id}")
        if len(node_args): 
            cursor.execute("insert into tbl_nodes (uuid, node_name, project_id) values " + (node_args) + " returning id, uuid")

            inserted_nodes = pd.DataFrame(cursor.fetchall(), columns = ["id", "uuid"])
            for index, row in edges_df.iterrows():
                edges_df.loc[index, "source_id"] = inserted_nodes.loc[inserted_nodes["uuid"] == row["source"]].iloc[0]["id"]
                edges_df.loc[index, "target_id"] = inserted_nodes.loc[inserted_nodes["uuid"] == row["target"]].iloc[0]["id"]
            edges_df.drop(["source", "target"], axis=1, inplace = True)

            edge_tuples = list(edges_df.itertuples(index = False, name = None))
            edge_args = ','.join(cursor.mogrify("(%s,%s,%s,%s)", i).decode('utf-8') for i in edge_tuples)

            if len(edge_args): cursor.execute("insert into tbl_edges (uuid, project_id, source_id, target_id) values " + (edge_args))

        connection.commit()
        RemoveDeletedElements(element_data, deleted_elements)
    except: return False
    
    return True

#Записать информацию о статусе ребер в базу
def SaveEdgedataToDB(element_data, project_id, user_id):
    nodes_df, edges_df = ElementsToDfs(element_data["elements"])
    nodes_df.drop(["width", "height", "level", "classes"], axis = 1, inplace = True)
    edges_df.drop(["classes"], axis = 1, inplace = True)

    nodes_df["project_id"] = project_id
    edges_df["project_id"] = project_id
    edges_df["source_id"] = 0
    edges_df["target_id"] = 0

    DeselectElement(element_data)

    deleted_edges = []
    added_edges = []
    
    deleted_elements = []
    for element in element_data["elements"]:
        if element["classes"] not in ["default", "added"]:
            if "source" in element["data"]: 
                edges_df.loc[edges_df["id"] == element["data"]["id"], "deleted"] = True
                deleted_edges.append(element)
            deleted_elements.append(element)
        else: 
            if element["classes"] == "added" and "source" in element["data"]: added_edges.append(element)
            element["classes"] = "default"

        edges_df = GetEdges(project_id)

        deleted_edge_ids = []
        for edge in deleted_edges:
            found_edge_id = edges_df.loc[(edges_df["source"] == edge["data"]["source"]) & (edges_df["target"] == edge["data"]["target"])].iloc[0]["id"]
            deleted_edge_ids.append(found_edge_id)
        
        added_edge_ids = []
        for edge in added_edges:
            found_edge_id = edges_df.loc[(edges_df["source"] == edge["data"]["source"]) & (edges_df["target"] == edge["data"]["target"])].iloc[0]["id"]
            added_edge_ids.append(found_edge_id)

    try:
        query = f"""update tbl_edgedata set deleted = true
            from tbl_edges
            where 
            tbl_edges.id = tbl_edgedata.edge_id and
            tbl_edges.uuid = any (%s) and
            tbl_edgedata.user_id = {user_id} and
            tbl_edges.project_id = {project_id}"""
        cursor.execute(query, (deleted_edge_ids,))

        query = f"""update tbl_edgedata set deleted = false
            from tbl_edges
            where 
            tbl_edges.id = tbl_edgedata.edge_id and
            tbl_edges.uuid = any (%s) and
            tbl_edgedata.user_id = {user_id} and
            tbl_edges.project_id = {project_id}"""
        cursor.execute(query, (added_edge_ids,))

        connection.commit()

        RemoveDeletedElements(element_data, deleted_elements)
    except: return False
    
    return True

#Отменить изменения в иерархии на этапе "Оценка зависимостей"
def DiscardEdgedataChanges(project_id, user_id):
    query = f"""update tbl_edgedata
    set deleted = false
    from tbl_edges
    where
    tbl_edges.id = tbl_edgedata.edge_id and
    user_id = {user_id} and
    project_id = {project_id}"""

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Изменить статус готовности
def ChangeCompleteState(project_id, user_id, option, state):
    query = f"update tbl_userdata set {option} = {state} where user_id = {user_id} and project_id = {project_id}"

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Вход и страница проектов --------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Проверить пароль при входе
def CheckUserCredentials(login, password):
    query = f"select password from tbl_users where login = '{login}'"
    cursor.execute(query)
    correct_password = cursor.fetchone()
    if correct_password: return password == correct_password[0]

    return False

#Получить данные пользователя
def GetUserData(login):
    query = f"select id, user_name, login from tbl_users where login = '{login}'"
    cursor.execute(query)
    user_data = pd.DataFrame(cursor.fetchall(), columns = ["id", "name", "login"]).to_dict("records")[0]

    return user_data

#Получить список проектов пользователя
def GetUserProjectsTableData(user_id):
    query = f"""select
        tbl_projects.id,
        tbl_projects.project_name,
        tbl_status.status_name,
        tbl_roles.role_name
        from
        tbl_projects
        inner join tbl_status on tbl_projects.status_id = tbl_status.id
        inner join tbl_userdata on tbl_userdata.project_id = tbl_projects.id
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where tbl_userdata.user_id = {user_id}
        order by tbl_projects.project_name"""
    
    cursor.execute(query)
    res = pd.DataFrame(cursor.fetchall(), columns = ["id", "name", "status", "role"])
    res["link"] = [dmc.Button(id = {"type": "project_button", "index": row["id"]}, children = "Перейти") for index, row in res.iterrows()]
    res.drop(["id"], axis=1, inplace = True)
    res = res.to_dict("records")

    return res

#Получить список проектов пользователя
def GetProjectData(user_id, project_id):
    query = f"""select
        tbl_projects.id,
        tbl_projects.project_name,
        tbl_projects.merge_coef,
        tbl_projects.cons_coef,
        tbl_projects.incons_coef,
        tbl_projects.const_comp,
        tbl_status.id,
        tbl_status.status_name,
        tbl_status.status_code,
        tbl_status.status_stage,
        tbl_roles.id,
        tbl_roles.role_name,
        tbl_roles.role_code,
        tbl_roles.access_level,
        tbl_userdata.de_completed,
        tbl_userdata.ce_completed
        from
        tbl_projects
        inner join tbl_status on tbl_projects.status_id = tbl_status.id
        inner join tbl_userdata on tbl_userdata.project_id = tbl_projects.id
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where 
        tbl_userdata.user_id = {user_id} and
        tbl_userdata.project_id = {project_id}"""
    
    cursor.execute(query)
    res = pd.DataFrame(cursor.fetchall(), columns = ["id", "name", "merge_coef", "cons_coef", "incons_coef", "const_comp", "status_id", "status_name", "status_code", "status_stage", "role_id", "role_name", "role_code", "access_level", "de_completed", "ce_completed"])
    res = res.to_dict("records")[0]

    status = {}
    status["id"] = res["status_id"]
    status["code"] = res["status_code"]
    status["name"] = res["status_name"]
    status["stage"] = res["status_stage"]

    role = {}
    role["id"] = res["role_id"]
    role["code"] = res["role_code"]
    role["name"] = res["role_name"]
    role["access_level"] = res["access_level"]

    completed = {}
    completed["de_completed"] = res["de_completed"]
    completed["ce_completed"] = res["ce_completed"]

    project_data = {}
    project_data["id"] = res["id"]
    project_data["name"] = res["name"]
    project_data["merge_coef"] = res["merge_coef"]
    project_data["cons_coef"] = res["cons_coef"]
    project_data["incons_coef"] = res["incons_coef"]
    project_data["const_comp"] = res["const_comp"]
    project_data["status"] = status
    project_data["role"] = role
    project_data["completed"] = completed

    return project_data

#Получить статус по его коду
def GetStatusByCode(status_code):
    query = f"select id, status_name, status_code, status_stage from tbl_status where status_code = '{status_code}'"
    cursor.execute(query)
    status = pd.DataFrame(cursor.fetchall(), columns = ["id", "name", "code", "stage"]).to_dict("records")[0]

    return status

#Заполнить БД данными о новом созданном проекте
def InsertNewProject(user_id):
    try:
        query = """insert into tbl_projects (
            project_name, 
            status_id, 
            merge_coef, 
            cons_coef, 
            incons_coef,
            const_comp) 
            select
            'Новый проект' as project_name, 
            tbl_status.id as status_id,
            0.5 as merge_coef,
            0.1 as cons_coef,
            0.315 as incons_coef,
            true as const_comp
            from tbl_status
            where status_code = 'initial'
            returning id"""
        cursor.execute(query)
        project_id = cursor.fetchone()[0]
        res = InsertUserdata(user_id, "owner", project_id)
    except: return False

    return res




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Страница настроек ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Получить идентификатор пользователя в проекте
def GetUserdataId(user_id, project_id):
    query = f"select id from tbl_userdata where user_id = {user_id} and project_id = {project_id}"
    cursor.execute(query)
    try:
        return cursor.fetchone()[0]
    except: return None

#Получить пользователей, участвующих в проекте
def GetProjectUserdata(project_id):
    query = f"""select
        tbl_userdata.id,
        login,
        user_name,
        role_name,
        access_level,
        de_completed,
        ce_completed
        from tbl_userdata
        inner join tbl_users on tbl_users.id = tbl_userdata.user_id
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where project_id = {project_id}
        order by user_name"""
    
    cursor.execute(query)
    userdata = pd.DataFrame(cursor.fetchall(), columns = ["id", "login", "name", "role", "access_level", "de_completed", "ce_completed"])

    return userdata

#Получить содержимое таблицы "Прогресс по задачам"
def GetTaskTableData(project_id):
    table_data = GetProjectUserdata(project_id)

    table_data.drop(table_data[table_data["access_level"] == 1].index, inplace = True)

    table_data["de_completed"] = [dmc.Checkbox(disabled = True, checked = row["de_completed"]) for index, row in table_data.iterrows()]
    table_data["ce_completed"] = [dmc.Checkbox(disabled = True, checked = row["ce_completed"]) for index, row in table_data.iterrows()]

    table_data.drop(["role", "access_level", "login", "id"], axis = 1, inplace = True)
    table_data = table_data.to_dict("records")

    return table_data

#Получить содержимое таблицы из раздела "Управление пользователями"
def GetUserTableData(project_id, access_level):
    table_data = GetProjectUserdata(project_id)

    table_data["delete"] = [dmc.Button(id = {"type": "delete_button", "index": row["id"]}, children = "Удалить", color = "red", disabled = bool(row["access_level"] >= access_level)) for index, row in table_data.iterrows()]

    table_data.drop(["de_completed", "ce_completed", "access_level", "login", "id"], axis = 1, inplace = True)
    table_data = table_data.to_dict("records")

    return table_data

#Получить содержимое таблицы групп из раздела "Управление группами"
def GetGroupListTableData(project_id):
    query = f"select id, group_name from tbl_groups where project_id = {project_id}"

    cursor.execute(query)
    table_data = pd.DataFrame(cursor.fetchall(), columns = ["id", "name"])
    table_data["delete"] = [dmc.Button(id = {"type": "group_delete_button", "index": row["id"]}, children = "Удалить", color = "red") for index, row in table_data.iterrows()]
    table_data.drop(["id"], axis = 1, inplace = True)

    table_data = table_data.to_dict("records")

    return table_data

#Получить содержимое таблицы состава группы из раздела "Управление группами"
def GetGroupUsersTableData(group_id):
    query = f"""select tbl_groupdata.id, tbl_users.user_name
        from tbl_users
        inner join tbl_groupdata on tbl_users.id = tbl_groupdata.user_id
        where tbl_groupdata.group_id = {group_id}"""

    cursor.execute(query)
    table_data = pd.DataFrame(cursor.fetchall(), columns = ["id", "name"])
    table_data["delete"] = [dmc.Button(id = {"type": "groupdata_button", "index": row["id"]}, children = "Удалить", color = "red") for index, row in table_data.iterrows()]
    table_data.drop(["id"], axis = 1, inplace = True)

    table_data = table_data.to_dict("records")

    return table_data

#Изменить условие объединения иерархий в базе
def UpdateMergevalue(merge_coef, project_id):
    query = f"update tbl_projects set merge_coef = {merge_coef} where id = {project_id}"
    try: cursor.execute(query)
    except: return False

    connection.commit()
    return True

#Изменить имя проекта в базе
def UpdateProjectName(new_name, project_id):
    query = f"update tbl_projects set project_name = '{new_name}' where id = {project_id}"
    try: cursor.execute(query)
    except: return False

    connection.commit()
    return True

#Изменить статус проекта в базе
def UpdateProjectStatus(new_status, project_data, user_id):
    res = False
    if project_data["status"]["stage"] < new_status["stage"]:
        project_data["status"] = new_status
        if new_status["code"] == "dep_eval":
            res = InsertEdgedata(project_data["id"])
        elif new_status["code"] == "comp_eval": 
            res = ChangeCompleteState(project_data["id"], user_id, "de_completed", True)
            res = InsertCompdata(project_data)
        elif new_status["code"] == "completed": 
            res = ChangeCompleteState(project_data["id"], user_id, "ce_completed", True)
            "Вычисления весов по завершившим оценку экспертам, сбор аналитики (индекс согласованности, коэффициент значимости противоречивости)"
    else:
        project_data["status"] = new_status
        if new_status["code"] == "initial": res = DeleteEdgedata(project_data["id"])
        elif new_status["code"] == "dep_eval": res = DeleteCompdata(project_data["id"])
        res = RemoveCompletedState(project_data)

    if res:
        query = f"update tbl_projects set status_id = {new_status['id']} where id = {project_data['id']}"
        try: 
            cursor.execute(query)
            connection.commit()
        except: 
            connection.rollback()
            return False
        
    return res

#Удалить проект
def DeleteProject(project_id):
    query = f"delete from tbl_projects where id = {project_id}"

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Получить роль пользователя в проекте
def GetUserRole(userdata_id):
    query = f"""select role_code, access_level from tbl_userdata
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where tbl_userdata.id = {userdata_id}"""
    cursor.execute(query)

    role_data = pd.DataFrame(cursor.fetchall(), columns = ["role_code", "access_level"])
    if len(role_data): return role_data.to_dict("records")[0]
    else: return False

#Сформировать набор данных для сравнительной оценки и записать в базу
def CreateAndInsertCompdata(nodes_df, edges_df, edgedata):
    data = []
    user_ids = list(set(edgedata["user_id"]))
    for level in range(1, nodes_df["level"].max()):
        parent_ids = list(nodes_df[nodes_df["level"] == level]["id"])
        for parent_id in parent_ids:
            edges = edges_df[edges_df["source"] == parent_id].to_dict("records")
            for i in range(len(edges)):
                for j in range(i + 1, len(edges)):
                    for user_id in user_ids:
                        insert_row = {}
                        insert_row["superiority_id"] = 1
                        insert_row["superior"] = True
                        insert_row["edge1_id"] = edgedata.loc[(edgedata["uuid"] == edges[i]["id"]) & (edgedata["user_id"] == user_id)].iloc[0]["id"]
                        insert_row["edge2_id"] = edgedata.loc[(edgedata["uuid"] == edges[j]["id"]) & (edgedata["user_id"] == user_id)].iloc[0]["id"]
                        data.append(insert_row)

    data = pd.DataFrame(data)

    data_tuples = list(data.itertuples(index = False, name = None))
    data_args = ','.join(cursor.mogrify("(%s,%s,%s,%s)", i).decode('utf-8') for i in data_tuples)
    
    if len(data_args):
        try: 
            cursor.execute("insert into tbl_compdata (superiority_id, superior, edgedata1_id, edgedata2_id) values " + (data_args))
            connection.commit()
        except: return False

    return True




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Обработка редактирования списка пользователей и изменения ролей -----------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Добавить пользователя в проект
def InsertUserdata(user_id, role_code, project_id):
    query = f"""insert into tbl_userdata (
        user_id, 
        role_id, 
        project_id, 
        de_completed, 
        ce_completed, 
        competence)
        (select 
        tbl_users.id as user_id, 
        tbl_roles.id as role_id,
        {project_id} as project_id,
        false as de_completed,
        false as ce_completed,
        1 as competence
        from tbl_users, tbl_roles
        where tbl_users.id = {user_id} and role_code = '{role_code}')
        returning id"""
    
    try:
        cursor.execute(query)
        connection.commit()
    except: return False
    
    return cursor.fetchone()[0]

#Изменить роль пользователя
def UpdateUserRole(userdata_id, role_code):
    query = f"""update tbl_userdata set role_id = tbl_roles.id
        from tbl_roles
        where 
        role_code = '{role_code}' and 
        tbl_userdata.id = {userdata_id}"""
    
    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Удалить пользователя из проекта
def DeleteUserdata(userdata_id):
    query = f"delete from tbl_userdata where tbl_userdata.id = {userdata_id}"

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Удалить данные оценки зависимостей для выбранного эксперта по проекту
def DeleteUserEdgedata(userdata_id):
    query = f"""delete from tbl_edgedata 
        using tbl_edges, tbl_userdata
        where 
        tbl_edges.id = tbl_edgedata.edge_id and
        tbl_edges.project_id = tbl_userdata.project_id and
        tbl_userdata.user_id = tbl_edgedata.user_id and
        tbl_userdata.id = {userdata_id}"""

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Вставить данные оценки зависимостей для выбранного эксперта по умолчанию
def InsertUserEdgedata(userdata_id):
    if DeleteUserEdgedata(userdata_id):
        query = f"""insert into tbl_edgedata (competence, deleted, edge_id, user_id)
            select
            tbl_userdata.competence as competence,
            false as deleted,
            tbl_edges.id as edge_id, 
            tbl_userdata.user_id
            from
            tbl_edges
            inner join tbl_userdata on tbl_userdata.project_id = tbl_edges.project_id
            inner join tbl_users on tbl_userdata.user_id = tbl_users.id
            inner join tbl_roles on tbl_userdata.role_id = tbl_roles.id
            where
            tbl_userdata.id = {userdata_id} and tbl_roles.access_level > 1"""
        
        try: 
            cursor.execute(query)
            connection.commit()
        except: return False
    else: return False

    return True

#Удалить данные сравнительной оценки для выбранного эксперта по проекту
def DeleteUserCompdata(userdata_id):
    query = f"""delete from tbl_compdata 
        using tbl_edgedata, tbl_userdata, tbl_edges
        where 
        (tbl_edgedata.id = tbl_compdata.edgedata1_id or
        tbl_edgedata.id = tbl_compdata.edgedata2_id) and
        tbl_edges.id = tbl_edgedata.edge_id and
        tbl_edges.project_id = tbl_userdata.project_id and
        tbl_edgedata.user_id = tbl_userdata.user_id and
        tbl_userdata.id = {userdata_id}"""

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Вставить данные сравнительной оценки для выбранного эксперта по умолчанию
def InsertUserCompdata(userdata_id, project_data):
    if DeleteUserCompdata(userdata_id):
        nodes_df, edges_df = GetProjectDfs(project_data, None)

        query = f"""select tbl_edgedata.id, uuid, tbl_userdata.user_id
            from tbl_edgedata
            inner join tbl_edges on tbl_edges.id = tbl_edgedata.edge_id
            inner join tbl_userdata on tbl_userdata.project_id = tbl_edges.project_id and tbl_userdata.user_id = tbl_edgedata.user_id
            where 
            uuid = any (%s) and
            tbl_userdata.id = {userdata_id}"""
        
        edge_list = list(edges_df["id"])
        cursor.execute(query, (edge_list,))
        edgedata = pd.DataFrame(cursor.fetchall(), columns = ["id", "uuid", "user_id"])

        return CreateAndInsertCompdata(nodes_df, edges_df, edgedata)
    
    return False

#Получить данные сравнительной оценки выбранного эксперта для вывода в таблицу оценивания
def GetUserCompdataForSimpleGrid(source_node_id, user_id):
    query = f"""select n0.node_name source_node_name, n1.node_name t1_node_name, n2.node_name t2_node_name, superior, superiority_code, tbl_compdata.id
        from tbl_compdata
        inner join tbl_superiority on tbl_superiority.id = tbl_compdata.superiority_id
        inner join tbl_edgedata ed1 on ed1.id = tbl_compdata.edgedata1_id
        inner join tbl_edgedata ed2 on ed2.id = tbl_compdata.edgedata2_id
        inner join tbl_edges e1 on e1.id = ed1.edge_id
        inner join tbl_edges e2 on e2.id = ed2.edge_id
        inner join tbl_nodes n0 on n0.id = e1.source_id
        inner join tbl_nodes n1 on n1.id = e1.target_id
        inner join tbl_nodes n2 on n2.id = e2.target_id
        where ed1.user_id = {user_id} and n0.uuid = '{source_node_id}'
        order by t1_node_name, n1.id, t2_node_name, n2.id, tbl_compdata.id"""
    
    cursor.execute(query)
    compdata = pd.DataFrame(cursor.fetchall(), columns = ["source_node_name", "t1_node_name", "t2_node_name", "superior", "code", "table_id"]).to_dict("records")

    return compdata

#Получить данные сравнительной оценки (его компетентность и данные) по вершине в разрезе проекта или конкретного пользователя
def GetCalculatedCompdata(source_node_id, user_id = None):

    filter_string = ""
    if user_id: filter_string = f"and ed1.user_id = {user_id}"

    query = f"""select
        t1.node_name as t1_node_name,
        t2.node_name as t2_node_name,
        competence_data,
        weighted_data
        from
        (select 
        n1.id as t1_id, 
        n2.id as t2_id, 
        sqrt(exp(sum(ln(ed1.competence)) / count(ed1.competence)) * exp(sum(ln(ed2.competence)) / count(ed2.competence))) as competence_data,
        exp(sum(ln(case when superior = true then superiority_code ^ sqrt(ed1.competence * ed2.competence)	when superior = false then 1 / (superiority_code ^ sqrt(ed1.competence * ed2.competence)) end)) /count(n1.id)) as weighted_data
        from tbl_compdata
        inner join tbl_superiority on tbl_superiority.id = tbl_compdata.superiority_id
        inner join tbl_edgedata ed1 on ed1.id = tbl_compdata.edgedata1_id
        inner join tbl_edgedata ed2 on ed2.id = tbl_compdata.edgedata2_id
        inner join tbl_edges e1 on e1.id = ed1.edge_id
        inner join tbl_edges e2 on e2.id = ed2.edge_id
        inner join tbl_nodes n0 on n0.id = e1.source_id
        inner join tbl_nodes n1 on n1.id = e1.target_id
        inner join tbl_nodes n2 on n2.id = e2.target_id
        inner join tbl_userdata on ed1.user_id = tbl_userdata.user_id and tbl_userdata.project_id = n0.project_id
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where n0.uuid = '{source_node_id}' and access_level > 1 and ce_completed = true {filter_string}
        group by t1_id, t2_id) as grouped_data
        inner join tbl_nodes as t1 on grouped_data.t1_id = t1.id
        inner join tbl_nodes as t2 on grouped_data.t2_id = t2.id
        order by t1_node_name, t1.id, t2_node_name, t2.id"""
    
    cursor.execute(query)
    compdata = pd.DataFrame(cursor.fetchall(), columns = ["t1_name", "t2_name", "competence_data", "weighted_data"]).to_dict("records")

    return compdata

#Получить данные сравнительной оценки (его компетентность и данные) по вершине в разрезе группы пользователей
def GetGroupCalculatedCompdata(source_node_id, group_id):
    if group_id: filter_string = f"= {group_id}"
    else: filter_string = "is NULL"

    query = f"""select
        t1.node_name as t1_node_name,
        t2.node_name as t2_node_name,
        competence_data,
        weighted_data
        from
        (select 
        t1_id as t1_id, 
        t2_id as t2_id, 
        sqrt(exp(sum(ln(ed1_competence)) / count(ed1_competence)) * exp(sum(ln(ed2_competence)) / count(ed2_competence))) as competence_data,
        exp(sum(ln(case when superior = true then superiority_code ^ sqrt(ed1_competence * ed2_competence)	when superior = false then 1 / (superiority_code ^ sqrt(ed1_competence * ed2_competence)) end)) /count(t1_id)) as weighted_data
        from 
        (select 
        n1.id as t1_id, 
        n2.id as t2_id, 
        ed1.competence as ed1_competence,
        ed2.competence as ed2_competence,
        superiority_code,
        superior,
        n1.id,
        tbl_userdata.user_id,
        tbl_userdata.project_id,
        e1.project_id,
        e2.project_id
        from tbl_compdata
        inner join tbl_superiority on tbl_superiority.id = tbl_compdata.superiority_id
        inner join tbl_edgedata ed1 on ed1.id = tbl_compdata.edgedata1_id
        inner join tbl_edgedata ed2 on ed2.id = tbl_compdata.edgedata2_id
        inner join tbl_edges e1 on e1.id = ed1.edge_id
        inner join tbl_edges e2 on e2.id = ed2.edge_id
        inner join tbl_nodes n0 on n0.id = e1.source_id
        inner join tbl_nodes n1 on n1.id = e1.target_id
        inner join tbl_nodes n2 on n2.id = e2.target_id
        inner join tbl_userdata on ed1.user_id = tbl_userdata.user_id and tbl_userdata.project_id = n0.project_id
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where n0.uuid = '{source_node_id}' and access_level > 1 and ce_completed = true
        ) compdata
        inner join (
        select ud.user_id
        from tbl_userdata ud
        inner join tbl_nodes n0 on n0.project_id = ud.project_id 
        inner join tbl_roles on tbl_roles.id = ud.role_id
        left outer join tbl_groupdata gd on gd.user_id = ud.user_id
        where n0.uuid = '{source_node_id}' and access_level > 1 and ce_completed = true and gd.group_id {filter_string}
        group by ud.user_id
        ) fg on fg.user_id = compdata.user_id
        group by t1_id, t2_id) as grouped_data
        inner join tbl_nodes as t1 on grouped_data.t1_id = t1.id
        inner join tbl_nodes as t2 on grouped_data.t2_id = t2.id
        order by t1_node_name, t1.id, t2_node_name, t2.id"""
    
    cursor.execute(query)
    compdata = pd.DataFrame(cursor.fetchall(), columns = ["t1_name", "t2_name", "competence_data", "weighted_data"]).to_dict("records")

    return compdata




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Обработка изменения компетентности ----------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Получение компетентности в различных разрезах

#Получить компетентность по исходящим ребрам для пользователя
def GetUserEdgeCompetenceData(source_id, user_id):
    query = f"""select
        target_table.node_name as target_name,
        competence,
        tbl_edgedata.id
        from
        tbl_edgedata
        inner join tbl_edges on tbl_edges.id = tbl_edgedata.edge_id
        inner join tbl_nodes as source_table on source_table.id = tbl_edges.source_id
        inner join tbl_nodes as target_table on target_table.id = tbl_edges.target_id
        where 
        tbl_edges.source_id = {source_id} and
        tbl_edgedata.user_id = {user_id}
        order by target_name, target_table.id"""
    
    cursor.execute(query)
    competence_data = pd.DataFrame(cursor.fetchall(), columns = ["name", "competence", "table_id"])
    competence_data = CreateCompetenceData(competence_data, "edge_competence")

    return competence_data

#Получить компетентность по исходящим ребрам для групп пользователей
def GetGroupEdgeCompetenceData(source_id, group_id):
    query = f"""select 
        tbl_nodes.node_name, 
        case when count(distinct tbl_edgedata.competence) = 1 then max(tbl_edgedata.competence) else -1 end competence, 
        tbl_edges.id
        from 
        tbl_edges
        inner join tbl_nodes on tbl_nodes.id = tbl_edges.target_id
        left outer join tbl_edgedata on tbl_edgedata.edge_id = tbl_edges.id
        inner join tbl_groupdata on tbl_groupdata.user_id = tbl_edgedata.user_id
        where source_id = {source_id} and tbl_groupdata.group_id = {group_id}
        group by tbl_edges.id, tbl_nodes.node_name
        order by tbl_nodes.node_name, tbl_nodes.id"""
    
    cursor.execute(query)
    competence_data = pd.DataFrame(cursor.fetchall(), columns = ["name", "competence", "table_id"])
    competence_data = CreateCompetenceData(competence_data, "edge_competence")

    return competence_data

#Получить компетентность пользователей по проекту
def GetUserProjectCompetenceData(project_id):
    query = f"""select user_name, competence, tbl_userdata.id
        from tbl_users
        inner join tbl_userdata on tbl_userdata.user_id = tbl_users.id
        inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
        where access_level > 1 and project_id = {project_id}
        order by user_name"""
    
    cursor.execute(query)
    competence_data = pd.DataFrame(cursor.fetchall(), columns = ["name", "competence", "table_id"])
    competence_data = CreateCompetenceData(competence_data, "project_competence")

    return competence_data

#Получить компетентность групп пользователей по проекту
def GetGroupProjectCompetenceData(project_id):
    query = f"""select 
        tbl_groups.group_name, 
        case when count(distinct tbl_userdata.competence) = 1 then max(tbl_userdata.competence) else -1 end competence,
        tbl_groups.id
        from 
        tbl_groups
        inner join tbl_groupdata on tbl_groupdata.group_id = tbl_groups.id
        inner join tbl_userdata on tbl_userdata.user_id = tbl_groupdata.user_id
        inner join tbl_roles on tbl_userdata.role_id = tbl_roles.id
        where 
        tbl_groups.project_id = tbl_userdata.project_id and
        tbl_userdata.project_id = {project_id} and
        access_level > 1
        group by tbl_groups.id, tbl_groups.group_name"""
    
    cursor.execute(query)
    competence_data = pd.DataFrame(cursor.fetchall(), columns = ["name", "competence", "table_id"])
    competence_data = CreateCompetenceData(competence_data, "project_competence")

    return competence_data


#Установка компетентности в различных разрезах

#Установить компетентность выбранному пользователю при оценке выбранных связей
def SetUserEdgeCompetence(competence_data, user_id):
    competence_data = ','.join(cursor.mogrify("(%s,%s)", i).decode('utf-8') for i in competence_data)

    if len(competence_data):
        query = f"""update tbl_edgedata set competence = data.competence
            from (values {competence_data}) as data(competence, id), tbl_users 
            where 
            data.id = tbl_edgedata.id and
            tbl_users.id = {user_id}"""

        try: 
            cursor.execute(query)
            connection.commit()
        except: return False
    else: return False

    return True

#Установить компетентность выбранному пользователю при оценке выбранных связей
def SetGroupEdgeCompetence(competence_data, group_id):
    competence_data = ','.join(cursor.mogrify("(%s,%s)", i).decode('utf-8') for i in competence_data)

    if len(competence_data):
        query = f"""update tbl_edgedata set competence = data.competence
            from (values {competence_data}) as data(competence, id), tbl_groupdata
            where 
            data.id = tbl_edgedata.edge_id and
            tbl_edgedata.user_id = tbl_groupdata.user_id and
            tbl_groupdata.group_id = {group_id}"""
        try: 
            cursor.execute(query)
            connection.commit()
        except: return False
    else: return False

    return True

#Установить компетентность пользователей по проекту
def SetUserProjectCompetence(competence_data):
    competence_data = ','.join(cursor.mogrify("(%s,%s)", i).decode('utf-8') for i in competence_data)

    if len(competence_data):
        query = f"""update tbl_userdata set competence = data.competence
            from (values {competence_data}) as data(competence, id)
            where  data.id = tbl_userdata.id"""
        
        try: 
            cursor.execute(query)
            connection.commit()
        except: return False
    else: return False

    return True

#Установить компетентность групп пользователей по проекту
def SetGroupProjectCompetence(competence_data, project_id):
    competence_data = ','.join(cursor.mogrify("(%s,%s)", i).decode('utf-8') for i in competence_data)

    if len(competence_data):
        query = f"""update tbl_userdata set competence = data.competence
            from (values {competence_data}) as data(competence, id), tbl_groupdata, tbl_groups
            where 
            data.id = tbl_groupdata.group_id and
            tbl_userdata.user_id = tbl_groupdata.user_id and
            tbl_userdata.project_id = tbl_groups.project_id
            and tbl_userdata.project_id = {project_id}"""
        
        try: 
            cursor.execute(query)
            connection.commit()
        except: return False
    else: return False

    return True


#Служебные функции

#Установить компетентность пользователей при оценке связей по умолчанию
def SetDefaultEdgeCompetence(project_id):
    query = f"""update tbl_edgedata 
        set competence = tbl_userdata.competence
        from tbl_userdata
        where tbl_edgedata.user_id = tbl_userdata.user_id and
        tbl_userdata.project_id = {project_id}"""
    
    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Установить тип компетентности пользователей в проекте
def SetCompetenceType(project_id, const_comp):
    query = f"update tbl_projects set const_comp = {const_comp} where id = {project_id}"
    
    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Обработка переходов между этапами -----------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Удалить данные оценки зависимостей по проекту
def DeleteEdgedata(project_id):
    query = f"""delete from tbl_edgedata 
        using tbl_edges 
        where 
        tbl_edges.id = tbl_edgedata.edge_id and 
        tbl_edges.project_id = {project_id}"""

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Вставить данные оценки зависимостей для всех экспертов проекта по умолчанию
def InsertEdgedata(project_id):
    if DeleteEdgedata(project_id):
        query = f"""insert into tbl_edgedata (competence, deleted, edge_id, user_id)
            select
            t1.competence as competence,
            false as deleted,
            tbl_edges.id as edge_id, 
            t1.user_id
            from
            tbl_edges inner join
                (tbl_userdata inner join 
                tbl_roles on tbl_roles.id = tbl_userdata.role_id) as t1
            on t1.project_id = tbl_edges.project_id
            where
            tbl_edges.project_id = {project_id} and
            t1.access_level > 1"""
        
        try: 
            cursor.execute(query)
            connection.commit()
        except: return False
    else: return False

    return True

#Удалить данные сравнительной оценки по проекту
def DeleteCompdata(project_id):
    query = f"""delete from tbl_compdata 
        using tbl_edgedata, tbl_edges
        where
        (tbl_edgedata.id = tbl_compdata.edgedata1_id or
        tbl_edgedata.id = tbl_compdata.edgedata2_id) and
        tbl_edgedata.edge_id = tbl_edges.id and
        tbl_edges.project_id = {project_id}"""

    try: 
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Вставить данные сравнительной оценки для всех экспертов проекта по умолчанию
def InsertCompdata(project_data):
    if DeleteCompdata(project_data["id"]):
        nodes_df, edges_df = GetProjectDfs(project_data, None)

        query = f"""select tbl_edgedata.id, uuid, user_id from tbl_edgedata
            inner join tbl_edges on tbl_edges.id = tbl_edgedata.edge_id
            where 
            uuid = any (%s) and
            project_id = {project_data['id']}
            order by user_id, uuid"""
        
        edge_list = list(edges_df["id"])
        cursor.execute(query, (edge_list,))
        edgedata = pd.DataFrame(cursor.fetchall(), columns = ["id", "uuid", "user_id"])

        return CreateAndInsertCompdata(nodes_df, edges_df, edgedata)
    
    return False

#Снять галочки выполнения этапа при возвращении на предыдущий
def RemoveCompletedState(project_data):
    query = None
    if project_data["status"]["code"] == "initial": query = f"update tbl_userdata set de_completed = false where project_id = {project_data['id']}"
    if project_data["status"]["code"] == "dep_eval": query = f"update tbl_userdata set ce_completed = false where project_id = {project_data['id']}"

    if query:
        try: cursor.execute(query)
        except: return False

    return True


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Страница аналитики --------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Получить дерево проекта
def GetAnalyticsTreeData(project_id, use_groups):
    status = "ce" if use_groups else "de"

    query = f"""select 
        tbl_userdata.user_id,
        tbl_users.user_name,
        coalesce(gr.group_id, 0) AS group_id,
        coalesce(tbl_groups.group_name, 'Нет группы') AS group_name
        from tbl_userdata
        left outer join
        (select tbl_groupdata.user_id, tbl_groupdata.group_id from
        tbl_groupdata 
        inner join tbl_groups on tbl_groupdata.group_id = tbl_groups.id
        where tbl_groups.project_id = {project_id}) gr on gr.user_id = tbl_userdata.user_id
        left outer join tbl_users on tbl_users.id = tbl_userdata.user_id
        left outer join tbl_groups on tbl_groups.id  = gr.group_id
        where tbl_userdata.project_id = {project_id} and tbl_userdata.{status}_completed = true 
        order by group_name, user_name"""
    
    cursor.execute(query)
    treedata = pd.DataFrame(cursor.fetchall(), columns = ["user_id", "user_name", "group_id", "group_name"])

    project_children = []
    if use_groups:
        group_df = treedata.drop(["user_id", "user_name"], axis = 1).drop_duplicates()

        for index, group_row in group_df.iterrows():
            if group_row["group_id"] == 0: continue

            group_item = {}
            group_item["label"] = group_row["group_name"]
            group_item["value"] = "project/group/" + str(group_row["group_id"])
            group_item["children"] = []
            for index, user_row in treedata.loc[treedata["group_id"] == group_row["group_id"]].iterrows():
                user_item = {}
                user_item["label"] = GetShortUsername(user_row["user_name"])
                user_item["value"] = group_item["value"] + "/user/" + str(user_row["user_id"])
                group_item["children"].append(user_item)
            project_children.append(group_item)

        without_group_df = treedata[treedata["group_id"] == 0]
        if len(without_group_df):
            ungrouped = {}
            ungrouped["label"] = "Нет группы"
            ungrouped["value"] = "project/group/0"
            ungrouped["children"] = []
            for index, user_row in without_group_df.iterrows():
                user_item = {}
                user_item["label"] = GetShortUsername(user_row["user_name"])
                user_item["value"] = ungrouped["value"] + "/user/" + str(user_row["user_id"])
                ungrouped["children"].append(user_item)
            project_children.append(ungrouped)

    else:
        treedata.drop(["group_id", "group_name"], axis = 1, inplace = True)
        treedata.sort_values(by = "user_name", inplace = True)

        for index, user_row in treedata.iterrows():
            user_item = {}
            user_item["label"] = GetShortUsername(user_row["user_name"])
            user_item["value"] = "project/user/" + str(user_row["user_id"])
            project_children.append(user_item)

    root = {
        "label": "Проект",
        "value": "project",
        "children" : project_children
    }

    return [root]

#Получить матрицу значений из Compdata
def MakeMatrix(compdata, property = "weighted_data", asymmetrical = True, round = False):
    matrix = []

    matrix_dim = (1 + int(pow(1 + 8 * len(compdata), 0.5))) // 2

    for i in range(matrix_dim):
        matrix_row = []
        for j in range(matrix_dim): matrix_row.append([0])
        matrix.append(matrix_row)

    for i in range(matrix_dim): matrix[i][i] = 1.0

    i = 0
    j = 1
    for item in compdata:
        if round:
            matrix[i][j] = round(item[property] / 1, 3)
            if asymmetrical: matrix[j][i] = round(1 / item[property], 3)
            else: matrix[j][i] = matrix[i][j]
        else:
            matrix[i][j] = item[property] / 1
            if asymmetrical: matrix[j][i] = 1 / item[property]
            else: matrix[j][i] = matrix[i][j]

        j += 1
        if j == matrix_dim:
            i += 1
            j = i + 1
        
    return matrix

#Сформировать таблицу по матрице значений
def MakeTableData(source_name, target_names, matrix, local_priorities = None):
    matrix_dim = len(target_names)
    matrix.insert(0, [0] * matrix_dim)

    for i, name in enumerate(target_names): matrix[0][i] = name
    for i in range(matrix_dim + 1):
        matrix[i].insert(0, [0])
        if i == 0: 
            matrix[0][0] = source_name
            if local_priorities: matrix[i].append("Локальные приоритеты")
            continue
        matrix[i][0] = target_names[i - 1]
        if local_priorities: matrix[i].append(local_priorities[i - 1])


    return matrix

#Получить локальные приоритеты
def GetLocalPriorities(matrix):
    local_priorities = []

    for i in range(len(matrix)):
        geo_mean = 1.0
        for j in range(len(matrix)):
            geo_mean *= matrix[i][j]
        geo_mean = pow(geo_mean, 1 / len(matrix))
        local_priorities.append(geo_mean)

    sum_geo_mean = sum(local_priorities)
    for i in range(len(local_priorities)):
        local_priorities[i] = local_priorities[i] / sum_geo_mean

    return local_priorities

#Получить отношение согласованности
def GetConsCoef(matrix, local_priorities):
    matrix_dim = len(local_priorities)

    if matrix_dim in [1, 2]: return 0

    multiplied_cols = []
    for i in range(matrix_dim):
        col_sum = 0
        for j in range(matrix_dim): col_sum += matrix[j][i]
        multiplied_cols.append(col_sum * local_priorities[i])

    cons_index = abs(sum(multiplied_cols) - matrix_dim) / (matrix_dim - 1)

    global cons_coef_data
    return round(cons_index / cons_coef_data[matrix_dim], 3)

#Получить глобальные приоритеты
def GetPriorityInfo(project_data, prop_id = None, group = False):
    nodes_df, edges_df = GetProjectDfs(project_data)

    nodes_df["priority"] = 0
    nodes_df["cons_coef"] = 0

    edges_df["priority"] = 0
    edges_df["local_priority"] = 0

    for level in range(1, nodes_df["level"].max()):
        level_df = nodes_df[nodes_df["level"] == level]
        for lvl_index, lvl_row in level_df.iterrows():
            if group: compdata = GetGroupCalculatedCompdata(lvl_row["id"], prop_id)
            else: compdata = GetCalculatedCompdata(lvl_row["id"], prop_id)
            
            matrix = MakeMatrix(compdata)
            local_priorities = GetLocalPriorities(matrix)
            nodes_df.loc[lvl_index, "cons_coef"] = GetConsCoef(matrix, local_priorities)

            priority_index = 0
            outcoming_edges = edges_df.loc[edges_df["source"] == lvl_row["id"]]
            for out_index, out_row in outcoming_edges.iterrows():
                edges_df.loc[out_index, "priority"] = local_priorities[priority_index]
                edges_df.loc[out_index, "local_priority"] = local_priorities[priority_index]
                priority_index += 1

    nodes_df.loc[nodes_df["level"] == 1, "priority"] = 1
    for level in range(2, nodes_df["level"].max() + 1):
        level_df = nodes_df[nodes_df["level"] == level]
        for lvl_index, lvl_row in level_df.iterrows():
            incoming_edges = edges_df.loc[edges_df["target"] == lvl_row["id"]]
            outcoming_edges = edges_df.loc[edges_df["source"] == lvl_row["id"]]

            node_priority = 0
            for index, row in incoming_edges.iterrows(): node_priority += row["priority"]
            nodes_df.loc[lvl_index, "priority"] = node_priority

            for out_index, out_row in outcoming_edges.iterrows():
                edges_df.loc[out_index, "priority"] = out_row["local_priority"] * node_priority

    for level in range(2, nodes_df["level"].max() + 1):
        level_df = nodes_df[nodes_df["level"] == level]
        float_fix = 0
        for lvl_index, lvl_row in level_df.iterrows(): float_fix += lvl_row["priority"]
        for lvl_index, lvl_row in level_df.iterrows(): nodes_df.loc[lvl_index, "priority"] = round(lvl_row["priority"] * float_fix, 3)

    return nodes_df, edges_df




#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Служебные функции ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#Создает датафреймы вершин и ребер на основе словаря элементов
def ElementsToDfs(elements):
    node_list = []
    edge_list = []

    for element in elements:
        if "source" in element["data"]:
            df_row = {}
            df_row["id"] = element["data"]["id"]
            df_row["source"] = element["data"]["source"]
            df_row["target"] = element["data"]["target"]
            df_row["deleted"] = False
            df_row["classes"] = element["classes"]

            if "priority" in element["data"]: df_row["priority"] = element["data"]["priority"]
            if "local_priority" in element["data"]: df_row["local_priority"] = element["data"]["local_priority"]

            edge_list.append(df_row)
        else: 
            df_row = {}
            df_row["id"] = element["data"]["id"]
            df_row["name"] = element["data"]["name"]
            df_row["width"] = element["data"]["width"]
            df_row["height"] = element["data"]["height"]
            df_row["level"] = element["data"]["level"]
            df_row["classes"] = element["classes"]

            if "priority" in element["data"]: df_row["priority"] = element["data"]["priority"]
            if "cons_coef" in element["data"]: df_row["cons_coef"] = element["data"]["cons_coef"]
            if "full_name" in element["data"]: df_row["full_name"] = element["data"]["full_name"]

            node_list.append(df_row)

    if len(node_list): nodes_df = pd.DataFrame(node_list)
    else: nodes_df = pd.DataFrame(columns = ["id", "name", "width", "height", "level", "classes"])

    if len(edge_list): edges_df = pd.DataFrame(edge_list)
    else: edges_df = pd.DataFrame(columns = ["id", "source", "target", "deleted", "classes"])

    return nodes_df, edges_df

#Получить элемент из списка по его id
def GetElementById(element_id, elements):
    for element in elements:
        if element["data"]["id"] == element_id:
            return element

#Получить ребро по source и target
def GetEdge(source_id, target_id, elements):
    for element in elements:
        if "source" in element["data"]:
            if element["data"]["source"] == source_id and element["data"]["target"] == target_id:
                return element

#Получить первоначальную информацию об элементах иерархии
def GetElementData(project_data, user_id):
    elements = GetHierarchyPreset(*GetProjectDfs(project_data, user_id))

    state = {}
    state["manually_deleted"] = {}
    state["cascade_deleted"] = {}
    state["added"] = {}
    state["selected"] = None

    steps = {}
    steps["history"] = []
    steps["canceled"] = []

    element_data = {}
    element_data["elements"] = elements
    element_data["state"] = state
    element_data["steps"] = steps

    return element_data

#Получить первоначальную информацию об элементах иерархии на странице "Аналитика"
def GetAnalyticsGraphElementData(project_data, item_type, item_id, status_code):
    if status_code == "dep_eval":
        if item_type == "user":
            nodes_df = GetNodes(project_data["id"])
            edges_df = GetEdgedata(project_data["id"], item_id)

            project_data["status"]["code"] == status_code
            nodes_df, edges_df = ExcludeDeletedElements(nodes_df, edges_df, project_data, "highlight")
            nodes_df = GetNodeLevels(nodes_df, edges_df)

            elements = GetHierarchyPreset(nodes_df, edges_df)

        if item_type == "project":
            #item_id должно быть None
            elements = GetHierarchyPreset(*GetProjectDfs(project_data, item_id))

    if status_code == "comp_eval":
        if item_type == "user": 
            a = 0
            #Вывести граф с весами и отношением согласованности для конкретного пользователя
        if item_type == "group":
            a = 0
            #Вывести граф с весами и отношением согласованности для группы пользователей (состав tbl_groupdata)
        if item_type == "project":
            a = 0
            #Вывести граф с весами и отношением согласованности для всего проекта (состав tbl_userdata inner join tbl_roles где "access_level > 1" по проекту)

    element_data = {}
    element_data["elements"] = elements
    element_data["selected"] = None


    return element_data

#Получить сокращенное имя пользователя
def GetShortUsername(username):
    name_chunks = username.split(' ')
    shortname = name_chunks[0]
    for chunk in name_chunks:
        if chunk != shortname: shortname += ' ' + chunk[0] + '.'
    return shortname

#Создать данные для таблицы
def CreateTableContent(columns, data):
    head = dmc.TableThead(dmc.TableTr([dmc.TableTh(column) for column in columns]))
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in data])
    return [head, body]

#Cоздать список компетентностей
def CreateCompetenceData(competence_data, competence_type):
    competence_data["name_col"] = [row["name"] for index, row in competence_data.iterrows()]
    competence_data["competence_col"] = [dmc.NumberInput(id = {"type": competence_type, "index": row["table_id"]}, value = row["competence"] if row["competence"] > 0 else "", min = 0, max = 1, step = 0.05, clampBehavior = "strict", decimalScale = 2) for index, row in competence_data.iterrows()]
    competence_data.drop(["name", "competence", "table_id"], axis = 1, inplace = True)
    competence_data = competence_data.to_dict("records")

    return competence_data

#Получить данные выпадающего списка
def GetSelectData(select_id, project_id = 0, group_checked = False):
    if select_id == "status_select":
        query = "select status_code, status_name, status_stage from tbl_status order by status_stage"
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ["value", "label", "stage"]).to_dict("records")


    if select_id == "user_select":
        query = "select id, user_name from tbl_users order by user_name"
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ["value", "label"])
        
        data["value"] = data["value"].astype(str)
        data = data.to_dict("records")

    if select_id == "role_select":
        query = "select role_code, role_name, access_level from tbl_roles order by access_level"
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ["value", "label", "access_level"])

        data["value"] = data["value"].astype(str)
        data = data.to_dict("records")

    if select_id == "competence_select":
        if group_checked:
            query = f"select id, group_name from tbl_groups where project_id = {project_id}"
        else:
             query = f"""select tbl_users.id, user_name 
                from tbl_users 
                inner join tbl_userdata on tbl_userdata.user_id = tbl_users.id
                inner join tbl_roles on tbl_roles.id = tbl_userdata.role_id
                where tbl_roles.access_level > 1 and tbl_userdata.project_id = {project_id}
                order by user_name"""
             
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ["value", "label"])

        data["value"] = data["value"].astype(str)
        data = data.to_dict("records")

    if select_id == "source_node_select":
        query = f"""select distinct tbl_nodes.id, node_name
            from tbl_nodes inner join tbl_edges on tbl_edges.source_id = tbl_nodes.id
            where tbl_nodes.project_id = {project_id}
            order by node_name, tbl_nodes.id"""
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ["value", "label"])

        data["value"] = data["value"].astype(str)
        data = data.to_dict("records")

    if select_id == "grouplist_select":
        query = f"select id, group_name from tbl_groups where project_id = {project_id}"
        cursor.execute(query)
        data = pd.DataFrame(cursor.fetchall(), columns = ["value", "label"])

        data["value"] = data["value"].astype(str)
        data = data.to_dict("records")

    return data

#Получить данные сравнительной оценки для пользователя
def GetUserNodesForSimpleGrid(source_node_id, project_data, elements = None):
    if elements: nodes_df, edges_df = ElementsToDfs(elements)
    else: nodes_df, edges_df = GetProjectDfs(project_data)
    target_ids = list(edges_df.loc[edges_df["source"] == source_node_id]["target"])
    return list(nodes_df.loc[nodes_df["id"].isin(target_ids)]["name"])

#Получить словарь SuperiorityNames
def GetSuperiorityNames():
    query = f"""select superiority_code code, superiority_name name from public.tbl_superiority order by superiority_code"""
    cursor.execute(query)
    #result = pd.DataFrame(cursor.fetchall(), columns = ["code", "name"]).to_dict("records")
    result = dict(cursor.fetchall())
    return result

#Записать в базу сравнительную оценку
def SaveCompEvalToBD(selected_data):
    #Записать в базу данных данные по selectes_table_id, но если superior_value равно 1, то поставить superior_check=True (только в базе)

    compdata_id = selected_data["table_id"]
    superiority_code = selected_data["code"]
    superior = selected_data["superior"]

    try:
        query = f"""update tbl_compdata set 
        superior = case when {superiority_code} = 1 then true else {superior} end,
        superiority_id = (select id from tbl_superiority where superiority_code = {superiority_code}) 
        where tbl_compdata.id = {compdata_id}"""
        cursor.execute(query)
        connection.commit()
    except: return False
    
    return True


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Управление группами -------------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Проверить наличие группы с таким названием в проекте
def CheckExistingGroups(group_name, project_id):
    query = f"select count(id) from tbl_groups where group_name = '{group_name}' and project_id = {project_id}"
    
    try:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        return bool(count)
    except: return None

#Проверить есть ли пользователь в группе
def CheckIfUserInGroup(group_id, user_id):
    query = f"select count(id) from tbl_groupdata where group_id = {group_id} and user_id = {user_id}"
    cursor.execute(query)
    try:
        count = cursor.fetchone()[0]
        return bool(count)
    except: return None

#Переименовать группу
def RenameGroup(group_name, group_id):
    query = f"update tbl_groups set group_name = '{group_name}' where id = {group_id}"

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Добавить группу
def AddGroup(group_name, project_id):
    query = f"insert into tbl_groups (group_name, project_id) values ('{group_name}', {project_id})"

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Удалить группу
def DeleteGroup(group_id):
    query = f"delete from tbl_groups where id = {group_id}"

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Добавить пользователя в группу
def AddUserToGroup(group_id, user_id):
    query = f"insert into tbl_groupdata (group_id, user_id) values ({group_id}, {user_id})"

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Удалить пользователя из группы
def DeleteUserFromGroup(groupdata_id):
    query = f"delete from tbl_groupdata where id = {groupdata_id}"

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True

#Удалить пользователя из всех групп по проекту
def DeleteUserFromAllProjectGroups(user_id, project_id):
    query = f"""delete from tbl_groupdata
        using tbl_groups
        where
        tbl_groups.id = tbl_groupdata.group_id and
        tbl_groupdata.user_id = {user_id} and
        tbl_groups.project_id = {project_id}"""

    try:
        cursor.execute(query)
        connection.commit()
    except: return False

    return True