from PIL import ImageFont
import dash_mantine_components as dmc
import pandas as pd
import uuid
import psycopg2

connection = psycopg2.connect(host='localhost', database='hierarchy', user='postgres', password='228228', port = 5432)
cursor = connection.cursor()


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


#Построение иерархии

#Получить элементы для отрисовки при инициализации
def GetHierarchyPreset(nodes_df, edges_df):
    nodes_df, edges_df = ExcludeDeletedElements(nodes_df, edges_df)

    node_list = []
    edge_list = []

    for level in range(1, nodes_df["level"].max() + 1):
        nodelevel_df = nodes_df.loc[nodes_df["level"] == level]
        for index, row in nodelevel_df.iterrows():
            node_data = {}
            node_data["id"] = row["id"]
            node_data["name"] = row["name"]
            node_data["width"] = 0
            node_data["height"] = 0
            node_data["level"] = level

            node_position = {}
            node_position["x"] = 0
            node_position["y"] = 0

            node_object = {}
            node_object["data"] = node_data
            node_object["position"] = node_position
            node_object["classes"] = "default"

            node_list.append(node_object)

    node_list = RefreshNodePositionsSizes(node_list)

    for index, row in edges_df.iterrows():
        edge_data = {}
        edge_data["id"] = row["id"]
        edge_data["source"] = row["source"]
        edge_data["target"] = row["target"]

        edge_object = {}
        edge_object["data"] = edge_data
        edge_object["classes"] = "default"

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
            element["position"]["x"] = (nodebox_df["level_width"].max() - nodebox_df.iloc[element["data"]["level"] - 1]["level_width"] + element["data"]["width"] + 2 * nodebox_props["margin-x"]) / 2 + (element["data"]["width"] + 2 * nodebox_props["margin-x"]) * element_counter[element["data"]["level"]]
            element["position"]["y"] = nodebox_df[:element["data"]["level"] - 1]["node_height"].sum() + element["data"]["height"] / 2 + nodebox_props["margin-y"] * 2 * (element["data"]["level"] - 1)
            element_counter[element["data"]["level"]] += 1

    return elements

#Покрасить элементы
def ColorElements(element_data):
    for element in element_data["list"]:
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


#Редактирование иерархии

#Удалить ребро
def DeleteEdge(nodes_df, edges_df, edge_id, element_data):
    root_edge = GetElementById(edge_id, element_data["list"])
    if root_edge["data"]["id"] not in element_data["state"]["manually_deleted"].keys():
        element_data["state"]["cascade_deleted"][root_edge["data"]["id"]] = root_edge

    if root_edge["data"]["target"] in element_data["state"]["added"].keys(): incoming_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & ~(edges_df["id"].isin(list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys())))]
    else: 
        incoming_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & ~(edges_df["id"].isin(list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys()))) & ~(edges_df["id"].isin(element_data["state"]["added"].keys()))]
        if len(incoming_edges) > 0: return
        else:
            added_edges = edges_df.loc[(edges_df["target"] == root_edge["data"]["target"]) & (edges_df["id"].isin(element_data["state"]["added"].keys()))]
            for index, row in added_edges.iterrows(): element_data["state"]["cascade_deleted"][row["id"]] = GetElementById(row["id"], element_data["list"])

    if len(incoming_edges) > 0: return

    current_node = GetElementById(root_edge["data"]["target"], element_data["list"])
    if current_node["data"]["id"] not in element_data["state"]["manually_deleted"].keys():
        element_data["state"]["cascade_deleted"][current_node["data"]["id"]] = current_node

    outcoming_edges = edges_df.loc[edges_df["source"] == current_node["data"]["id"]]
    for index, row in outcoming_edges.iterrows():
        DeleteEdge(nodes_df, edges_df, row["id"], element_data)

#Удалить элемент
def DeleteElement(deleted_element, element_data):
    if deleted_element not in element_data["list"]: deleted_element = GetEdge(deleted_element["data"]["source"], deleted_element["data"]["target"], element_data["list"])

    element_data["state"]["manually_deleted"][deleted_element["data"]["id"]] = deleted_element
    nodes_df, edges_df = ElementsToDfs(element_data["list"])

    if "source" in deleted_element["data"]:
        DeleteEdge(nodes_df, edges_df, deleted_element["data"]["id"], element_data)
    else:
        incoming_edges = edges_df.loc[(edges_df["target"] == deleted_element["data"]["id"]) & ~(edges_df["id"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]
        for index, row in incoming_edges.iterrows():
            element_data["state"]["cascade_deleted"][row["id"]] = GetElementById(row["id"], element_data["list"])

        outcoming_edges = edges_df.loc[(edges_df["source"] == deleted_element["data"]["id"]) & ~(edges_df["id"].isin(list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())))]
        for index, row in outcoming_edges.iterrows():
            DeleteEdge(nodes_df, edges_df, row["id"], element_data)

#Отменить удаление ребра
def CancelDeleteEdge(nodes_df, edges_df, edge_id, element_data):
    root_edge = GetElementById(edge_id, element_data["list"])

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
    if deleted_element not in element_data["list"]: deleted_element = GetEdge(deleted_element["data"]["source"], deleted_element["data"]["target"], element_data["list"])

    if deleted_element["data"]["id"] in element_data["state"]["manually_deleted"].keys(): del element_data["state"]["manually_deleted"][deleted_element["data"]["id"]]
    element_data["state"]["cascade_deleted"][deleted_element["data"]["id"]] = deleted_element
    nodes_df, edges_df = ElementsToDfs(element_data["list"])

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
    element_data["list"].append(edge_object)
    element_data["state"]["added"][edge_object["data"]["id"]] = edge_object

    deleted_ids = list(element_data["state"]["manually_deleted"].keys()) + list(element_data["state"]["cascade_deleted"].keys())
    if edge_object["data"]["source"] in deleted_ids or edge_object["data"]["target"] in deleted_ids: element_data["state"]["cascade_deleted"][edge_object["data"]["id"]] = edge_object

#Добавить новую вершину
def AddElement(element, element_data):
    if "source" in element["data"]:
        AddEdge(element, element_data)
    else:
        nodes_df, edges_df = ElementsToDfs(element_data["list"])

        element_data["list"].append(element)
        element_data["state"]["added"][element["data"]["id"]] = element

        deleted = True
        upper_level_nodes = nodes_df.loc[nodes_df["level"] == element["data"]["level"] - 1]
        for index, row in upper_level_nodes.iterrows():
            AddEdge(CreateEdgeObject(row["id"], element["data"]["id"]), element_data)
            if row["id"] not in list(element_data["state"]["cascade_deleted"].keys()) + list(element_data["state"]["manually_deleted"].keys()): deleted = False

        if deleted: element_data["state"]["cascade_deleted"][element["data"]["id"]] = element

        lower_level_nodes = nodes_df.loc[nodes_df["level"] == element["data"]["level"] + 1]
        for index, row in lower_level_nodes.iterrows():
            AddEdge(CreateEdgeObject(element["data"]["id"], row["id"]), element_data)

#Отменить добавление элемента
def CancelAddElement(added_element, element_data):
    del element_data["state"]["added"][added_element["data"]["id"]]
    if added_element["data"]["id"] in element_data["state"]["manually_deleted"].keys(): del element_data["state"]["manually_deleted"][added_element["data"]["id"]]
    if added_element["data"]["id"] in element_data["state"]["cascade_deleted"].keys(): del element_data["state"]["cascade_deleted"][added_element["data"]["id"]]

    if "source" not in added_element["data"]:
        nodes_df, edges_df = ElementsToDfs(element_data["list"])
        node_edges = edges_df.loc[(edges_df["source"] == added_element["data"]["id"]) | (edges_df["target"] == added_element["data"]["id"])]
        for index, row in node_edges.iterrows():
            del element_data["state"]["added"][row["id"]]
            if row["id"] in element_data["state"]["manually_deleted"].keys(): del element_data["state"]["manually_deleted"][row["id"]]
            if row["id"] in element_data["state"]["cascade_deleted"].keys(): del element_data["state"]["cascade_deleted"][row["id"]]
            element_data["list"].remove(GetElementById(row["id"], element_data["list"]))

    element_data["list"].remove(added_element)
    if element_data["state"]["selected"] not in element_data["list"]: element_data["state"]["selected"] = None

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


#Служебные функции

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

            edge_list.append(df_row)
        else: 
            df_row = {}
            df_row["id"] = element["data"]["id"]
            df_row["name"] = element["data"]["name"]
            df_row["width"] = element["data"]["width"]
            df_row["height"] = element["data"]["height"]
            df_row["level"] = element["data"]["level"]
            df_row["classes"] = element["classes"]

            node_list.append(df_row)

    nodes_df = pd.DataFrame(node_list)
    edges_df = pd.DataFrame(edge_list)

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




#Запросы и их обработка

#Получить датафрейм вершин из базы
def GetNodes(project_id):
    query = f"""select uuid, node_name from tbl_nodes
        where project_id = {project_id}
        order by node_name"""
    cursor.execute(query)
    nodes = pd.DataFrame(cursor.fetchall(), columns = ["id", "name"])

    return nodes

#Получить датафрейм ребер из базы
def GetEdges(project_id, user_id):
    edges = pd.DataFrame()

    if user_id:
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
            tbl_edgedata.user_id = {user_id}"""
        
        cursor.execute(query)
        edges = pd.DataFrame(cursor.fetchall(), columns = ["id", "source", "target", "deleted"])
    else:
        query = f"""select 
            tbl_edges.uuid, 
            source.uuid as source_id, 
            target.uuid as target_id
            from
            tbl_edges
            inner join tbl_nodes as source on source.id = tbl_edges.source_id
            inner join tbl_nodes as target on target.id = tbl_edges.target_id
            where 
            tbl_edges.project_id = {project_id}"""
        
        cursor.execute(query)
        edges = pd.DataFrame(cursor.fetchall(), columns = ["id", "source", "target"])
        deleted = [False] * len(edges)
        edges["deleted"] = deleted

    return edges

#Получить датафреймы вершин и ребер из базы с опциональной очисткой от удаленных элементов
def GetProjectDfs(project_id, expert_id, exclude_deleted):
    nodes_df = GetNodes(project_id)
    edges_df = GetEdges(project_id, expert_id)

    if exclude_deleted: nodes_df, edges_df = ExcludeDeletedElements(nodes_df, edges_df)

    nodes_df = GetNodeLevels(nodes_df, edges_df)

    return nodes_df, edges_df

#Очистить датафреймы вершин и ребер от удаленных элементов
def ExcludeDeletedElements(nodes_df, edges_df):
    head_id = nodes_df.loc[~nodes_df["id"].isin(edges_df["target"])].iloc[0]["id"]

    edges_df.drop(edges_df.loc[edges_df["deleted"] == True].index, inplace = True)
    nodes_df.drop(nodes_df.loc[~nodes_df["id"].isin(edges_df["target"]) & (nodes_df["id"] != head_id)].index, inplace = True)

    return nodes_df, edges_df

#Дополнить датафрейм с элементами иерархии колонкой с их уровнями
def GetNodeLevels(nodes_df, edges_df):
    levels = [0] * len(nodes_df)
    nodes_df["level"] = levels

    visited = []

    head_id = nodes_df.loc[~nodes_df["id"].isin(edges_df["target"])].iloc[0]["id"]
    source_id = head_id
    nodes_df.loc[nodes_df["id"] == head_id, "level"] = 1

    while len(visited) < len(nodes_df):
        source_id = nodes_df.loc[~nodes_df["id"].isin(visited) & (nodes_df["level"] != 0)].iloc[0]["id"]


        children = list(edges_df[edges_df["source"] == source_id]["target"])
        for child_id in children: nodes_df.loc[nodes_df["id"] == child_id, "level"] = nodes_df.loc[nodes_df["id"] == source_id, "level"].values[0] + 1

        visited.append(source_id)
        
    return nodes_df.sort_values(by="level")

#Записать граф в базу
def SaveGraphToDB(project_id, element_data):
    nodes_df, edges_df = ElementsToDfs(element_data["list"])
    nodes_df.drop(["width", "height", "level", "classes"], axis=1, inplace = True)
    edges_df.drop(["deleted", "classes"], axis=1, inplace = True)

    nodes_df["project_id"] = project_id
    edges_df["project_id"] = project_id
    edges_df["source_id"] = 0
    edges_df["target_id"] = 0

    if element_data["state"]["selected"]:
        if element_data["state"]["selected"]["data"]["id"] in element_data["state"]["manually_deleted"].keys(): element_data["state"]["selected"]["classes"] = "manually_deleted"
        elif element_data["state"]["selected"]["data"]["id"] in element_data["state"]["cascade_deleted"].keys(): element_data["state"]["selected"]["classes"] = "cascade_deleted"
        else: element_data["state"]["selected"]["classes"] = "default"
        element_data["state"]["selected"] = None

    deleted_elements = []
    for element in element_data["list"]:
        if element["classes"] not in ["default", "added"]:
            if "source" in element["data"]: edges_df.drop(edges_df.loc[edges_df["id"] == element["data"]["id"]].index, inplace = True)
            else: nodes_df.drop(nodes_df.loc[nodes_df["id"] == element["data"]["id"]].index, inplace = True)
            deleted_elements.append(element)
        else: element["classes"] = "default"

    try:
        node_tuples = list(nodes_df.itertuples(index = False, name = None))
        node_args = ','.join(cursor.mogrify("(%s,%s,%s)", i).decode('utf-8') for i in node_tuples)

        cursor.execute(f"delete from tbl_nodes where project_id = {project_id}")
        cursor.execute("insert into tbl_nodes (uuid, node_name, project_id) values " + (node_args) + " returning id, uuid")


        inserted_nodes = pd.DataFrame(cursor.fetchall(), columns = ["id", "uuid"])
        for index, row in edges_df.iterrows():
            edges_df.loc[index, "source_id"] = inserted_nodes.loc[inserted_nodes["uuid"] == row["source"]].iloc[0]["id"]
            edges_df.loc[index, "target_id"] = inserted_nodes.loc[inserted_nodes["uuid"] == row["target"]].iloc[0]["id"]
        edges_df.drop(["source", "target"], axis=1, inplace = True)

        edge_tuples = list(edges_df.itertuples(index = False, name = None))
        edge_args = ','.join(cursor.mogrify("(%s,%s,%s,%s)", i).decode('utf-8') for i in edge_tuples)

        cursor.execute("insert into tbl_edges (uuid, project_id, source_id, target_id) values " + (edge_args))
        connection.commit()

        element_data["state"]["manually_deleted"] = {}
        element_data["state"]["cascade_deleted"] = {}
        element_data["state"]["added"] = {}
        element_data["steps"]["history"] = []
        element_data["steps"]["canceled"] = []

        for element in deleted_elements: element_data["list"].remove(element)
    except: return False
    
    return True


#Формирование элементов страницы

#Определение состава, состояния, возможности изменения чекбоксов элементов нижнего уровня и вершины
def GetToolbarCheckboxes(source_node, element_data):
    element_data["state"]
    nodes_df, edges_df = ElementsToDfs(element_data["list"])

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

    node_checkbox = dmc.Checkbox(id = "node_checkbox", size = 36)
    if source_node["data"]["id"] in element_data["state"]["cascade_deleted"].keys():
        node_checkbox.checked = False
        node_checkbox.disabled = True
    elif source_node["data"]["id"] in element_data["state"]["manually_deleted"].keys():
        node_checkbox.checked = False
        node_checkbox.disabled = False
    else:
        node_checkbox.checked = True
        node_checkbox.disabled = False

    return node_checkbox, edge_checkboxes


#Определение размеров и позиций вершин

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
        width, height = GetNodebox(row["name"])
        if nodebox["node_width"] < width: nodebox["node_width"] = width
        if nodebox["node_height"] < height: nodebox["node_height"] = height

    nodebox["level_width"] = (nodebox["node_width"] + 2 * nodebox_props["margin-x"]) * (len(nodelevel_df))
    nodebox["level"] = level

    return nodebox

#Информация о иерархии
def GetHierarchyInfo(nodes_df):
    nodebox_list = []
    for level in range(1, nodes_df["level"].max() + 1):
        nodebox = GetLevelInfo(nodes_df, level)
        nodebox_list.append(nodebox)
    nodebox_df = pd.DataFrame(nodebox_list).sort_values(by="level")

    return nodebox_df





