import dash
from dash import Dash, Input, Output, State, _dash_renderer, ctx, ALL, dcc
import dash_mantine_components as dmc
from dash import Dash, _dash_renderer
import functions
from dash.exceptions import PreventUpdate

_dash_renderer._set_react_version("18.2.0")

app = Dash(external_stylesheets=dmc.styles.ALL)

def CreateProjectTable(user_id):
    columns = ["Название", "Состояние", "Роль в проекте", "Ссылка"]
    project_data = functions.GetUserProjects(user_id)

    head = dmc.TableThead(dmc.TableTr([dmc.TableTh(column) for column in columns]))
    body = dmc.TableTbody([dmc.TableTr([dmc.TableTd(element[key]) for key in element.keys()]) for element in project_data])
    table = dmc.Table([head, body])

    return table


app.layout = dmc.Box(
    children = [
        CreateProjectTable(1),
        dmc.Box(id = "tmp123")
    ]
)
app.layout = dmc.MantineProvider(app.layout)

@dash.callback(
    Output("tmp123", "children"),
    Input({"type": "project_link", "index": ALL}, "n_clicks"),
)
def test(click):
    trigger = {"id": ctx.triggered_id, "property": ctx.triggered[0]["prop_id"].split(".")[1], "value": ctx.triggered[0]["value"]}
    if not trigger["id"]: raise PreventUpdate
    project_link = ctx.triggered_id["index"]
    dash.register_page("project", path = project_link, layout = dmc.Box("123"))

    return "34234"

if __name__ == "__main__":
    app.run(debug=True)