import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, _dash_renderer, ctx, ALL, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate

from flask import session
from flask_login import current_user

import functions
import json


_dash_renderer._set_react_version("18.2.0")
dash.register_page(__name__)

def layout():
    #Удаление ключей других страниц
    page_projects = session.pop("page_projects", None) 
    page_project = session.pop("page_project", None)
    page_settings = session.pop("page_settings", None)
    #page_compeval = session.pop("page_compeval", None)
    page_analytics = session.pop("page_analytics", None)

    #Очистка данных
    project_data = session.pop("project_data", None)
    element_data = session.pop("element_data", None)
    comp_data = session.pop("comp_data", None)

    if not current_user.is_authenticated:
        return dcc.Location(id = {"type": "unauthentificated", "index": "compeval"}, pathname = "/login")
    elif not "page_compeval" in session:
        return dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/project")
    else:
        page_compeval = json.loads(session["page_compeval"])
        comp_data = functions.GetUserCompdata(page_compeval["current_node_id"], current_user.userdata["id"])
        
        if len(comp_data)==0:
            return dcc.Location(id = {"type": "redirect", "index": "compeval"}, pathname = "/project")
        else:
            
            session["comp_data"] = json.dumps(comp_data, cls = functions.NpEncoder)

            layout = dmc.Box(
                children=[
                dmc.Center(
                    functions.MakeSimpleGrid(comp_data)
                    )
                    ])
            layout = dmc.MantineProvider(layout)
            return layout