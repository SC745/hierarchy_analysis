import dash_mantine_components as dmc
from dash_iconify import DashIconify


toolbar = [
    dmc.Box(
        dmc.Text(
            children = "Выберите элемент",
            ta = "center",
            pt = "md"
        ),
        style = {"display": "block"}
    ),
    dmc.Box(
        children = [
            dmc.Stack(
                children = [
                    dmc.Stack(
                        children = [
                            dmc.Text("Название"),
                            dmc.Group(
                                children = [
                                    dmc.TextInput(id = "name_input"),
                                    dmc.Checkbox(id = "node_checkbox", size = 36, checked = True)
                                ],
                                justify = "space-around",
                                grow=True,
                                preventGrowOverflow=False,
                            ),
                        ],
                        p = "md",
                        gap = 5
                    ),
                    dmc.Accordion(
                        children = [
                            dmc.AccordionItem(
                                children = [
                                    dmc.AccordionControl("Элементы нижнего уровня"),
                                    dmc.AccordionPanel(dmc.Stack(id = "edge_checkboxstack", children = [], gap = 0))
                                ],
                                value = "elements"
                            ),
                        ],
                        value="elements"
                    )
                ],
            ),
        ],
        style = {"display": "none"},
        id = {"type": "node_toolbar", "index": "default"}
    ),
]

