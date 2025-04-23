import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_cytoscape as cyto
from dash import dcc


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

login_layout = dmc.Box(
    children = [
        dmc.Center(
        children=[
            dmc.Card(
                children = [
                    dmc.Stack(
                        children=[
                            dmc.Text(children = "Вход", fz = 24, ta = "center", fw = "bold"),
                            dmc.TextInput(id = "login_input", placeholder="Логин", w="100%", size = "lg"),
                            dmc.PasswordInput(id = "password_input", placeholder="Пароль", w="100%", size = "lg"),
                            dmc.Button(id = "login_button", children = "Войти", w="100%", size = "lg"),
                            dmc.Text(id = "error_message", children ="Неверный логин или пароль!", ta = "center", c = "var(--mantine-color-red-6)", display = "none"),
                            dcc.Location(id = {"type": "redirect", "index": "login"}, pathname = "/login")
                        ],
                    )
                ],
                bg = "var(--mantine-color-white)"
            )
        ],
        style={"height": "100vh", "width": "100%"},
        )
    ],
    bg = "var(--mantine-color-dark-2)"
)

project_layout = dmc.AppShell(
    children = [
        dmc.AppShellHeader("Header"),
        dmc.AppShellNavbar("Navbar"),
        dmc.AppShellAside(
            id = "aside",
            children = [
                dmc.Box(
                    children = [
                        dmc.Group(
                            children = [
                                dmc.ActionIcon(id = {"type": "action_button", "index": "rollback"}, children = DashIconify(icon = "mingcute:corner-down-left-fill", width=20), size = "input-sm", variant = "default", disabled = True),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "cancelrollback"}, children = DashIconify(icon = "mingcute:corner-down-right-fill", width=20), size = "input-sm", variant = "default", disabled = True),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "locate"}, children = DashIconify(icon = "mingcute:location-line", width=20), size = "input-sm", variant = "default"),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "add"}, children = DashIconify(icon = "mingcute:cross-line", width=20), size = "input-sm", variant = "light", color = "green"),
                                dmc.ActionIcon(id = {"type": "action_button", "index": "save"}, children = DashIconify(icon = "mingcute:save-2-line", width=20), size = "input-sm", variant = "light"),
                            ],
                            grow=True,
                            preventGrowOverflow=False,
                            p = "md"
                        ),
                        dmc.Divider()
                    ]
                ),
                dmc.Box(
                    children = toolbar,
                    id = "toolbar_data"
                )
                
            ]
        ),
        dmc.AppShellMain([
            cyto.Cytoscape(
                id="graph",
                layout={"name": "preset"},
                style={
                    "width": "100%",
                    "height": "calc(100vh - 30px)",
                    "position": "relative",
                },
                stylesheet=[
                    #Group selectors
                    {
                        "selector": "node",
                        "style": {
                            "shape": "rectangle",
                            "content": "data(name)",
                            "width": "data(width)",
                            "height": "data(height)",
                            "text-valign": "center",
                            "background-color": "#ffffff",
                            "border-width": "3px",
                            "font-size": "14px",
                            "text-wrap": "wrap",
                            "text-max-width": "80px"
                        },
                    },
                    #Class selectors
                    {
                        "selector": ".manually_deleted",
                        'style': { #mantine red.6
                            "border-color": "#fa5252",
                            "line-color": "#fa5252"
                        }
                    },
                    {
                        "selector": ".cascade_deleted",
                        'style': { #mantine orange.6
                            "border-color": "#fd7e14",
                            "line-color": "#fd7e14"
                        }
                    },
                    {
                        "selector": ".added",
                        "style": { #mantine green.6
                            "border-color": "#40c057",
                            "line-color": "#40c057"
                        }
                    },
                    {
                        "selector": ".selected",
                        "style": { #mantine blue.6
                            "border-color": "#228be6",
                            "line-color": "#228be6"
                        }
                    },
                    {
                        "selector": ".default",
                        "style": {
                            "border-color": "black",
                            "line-color": "black"
                        }
                    },
                ],
                minZoom = 0.5,
                maxZoom = 2,
                autoungrabify = True,
                autoRefreshLayout = True,
                wheelSensitivity = 0.2,
                elements = []
            )
        ]),
    ],
    header={"height": "30px"},
    navbar={"width": "15%"},
    aside={"width": "15%"},
    id="appshell",
)