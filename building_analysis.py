import gradio as gr
import pandas as pd
import plotly.express as px
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
from config import speckle_token
# import matplotlib.pyplot as plt

# # Default project and model IDs
# project_id = "d3e86261bf"  # Default to Farnsworth House
# model_id = "3a724a3d22"

# Initialize Speckle client and credentials
speckle_server = "macad.speckle.xyz"
client = SpeckleClient(host=speckle_server)
account = get_account_from_token(speckle_token, speckle_server)
client.authenticate_with_account(account)

model_name = 'kunsthaus zurich'
project_id = "daeb18ed0a"
model_id = "aab87740df"

def set_model_data(model_name):
    model_map = {
        'farnsworth house': ("d3e86261bf", "3a724a3d22"),
        'kunsthaus zurich': ("daeb18ed0a", "aab87740df")
    }
    
    if model_name in model_map:
        project_id, model_id = model_map[model_name]
    else:
        # Handle invalid model_name
        raise ValueError(f"Invalid model name: {model_name}. Valid options are: {list(model_map.keys())}")
    
    return project_id, model_id

# def set_model_data(model_name):
#     global project_id, model_id
#     if model_name == 'farnsworth house': 
#         project_id = "d3e86261bf", 
#         model_id = "3a724a3d22",
#     if model_name == 'kunsthaus zurich':
#         project_id = "daeb18ed0a", 
#         model_id = "aab87740df",
    
#     return project_id, model_id


def create_viewer_url(project_id, model_id):
    # print(f"Creating viewer URL for project_id: {project_id}, model_id: {model_id}")
    versions = client.version.get_versions(model_id=model_id, project_id=project_id, limit=100).items
    if not versions:
        return "<p>Error: No versions found for this model.</p>"
    selected_version = versions[0]
    
    embed_src = f"https://macad.speckle.xyz/projects/{project_id}/models/{model_id}@{selected_version.id}#embed=%7B%22isEnabled%22%3Atrue%2C%7D"
    return embed_src

def get_model_data(model_name):
    
    # Set the global project_id and model_id based on selection
    project_id, model_id = set_model_data(model_name)

    # Get version details
    versions = client.version.get_versions(model_id=model_id, project_id=project_id, limit=100).items
    selected_version = versions[0]
    referenced_obj_id = selected_version.referencedObject
    
    # Create a fresh transport for each request
    transport = ServerTransport(project_id, client)
    
    # Get object data
    objData = operations.receive(referenced_obj_id, transport)
    
    return objData


def analyze_building_data(objData):
    child_obj = objData
    data = {"element": [], "volume": [], "mass": [], "embodied carbon": []}
    
    # get the attributes on the level object
    names = child_obj.get_dynamic_member_names()
    # iterate through and find the elements with a `volume` attribute
    for name in names:
        prop = child_obj[name]
        if isinstance(prop, list):
                for p in prop:
                    volume = 0
                    mass = 0
                    carbon = 0
                    if name == '@Windows':
                        volume += p.area * 70
                        mass += p.area * 70 * p["@density"]
                        carbon += p.area * 70 * p["@density"] * p["@embodied_carbon"]
                    else:
                        volume += p.volume
                        mass += p.volume * p["@density"]
                        carbon += p.volume * p["@density"] * p["@embodied_carbon"]
        else:
            volume = prop.volume
            mass = prop.volume * prop["@density"]
            carbon = prop.volume * prop["@density"] * prop["@embodied_carbon"]
        data["volume"].append(volume)
        data["mass"].append(mass)
        data["embodied carbon"].append(carbon)
        data["element"].append(name[1:])  # removing the prepending `@`
    
    vertices = []
    for name in names:
        for element in child_obj[name]:
            for p in element.Vertices:
                vertices.append({"x": p.x, "y": p.y, "z": p.z, "element": name[1:]})
    
    return data, vertices


def generate_graphs(data):
    
    df = pd.DataFrame(data)
    
    # Creating figures
    volumes_fig = px.pie(df, values="volume", names="element", color="element", 
                         hole=0.3, color_discrete_sequence=px.colors.sequential.Emrld)
    volumes_fig.update_layout(
        height = 600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        paper_bgcolor='rgb(15, 15, 15)',  # Graphite background color
        plot_bgcolor='rgb(15, 15, 15)',   # Graphite background color for the plot area
        font=dict(color='white'),          # Font color for better contrast
        title_font=dict(color='white')     # Title font color
    )

    carbon_bar_fig = px.bar(df, x="element", y="embodied carbon", color="element",
                            color_discrete_sequence=px.colors.sequential.Emrld)
    carbon_bar_fig.update_layout(
        height = 600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        paper_bgcolor='rgb(15, 15, 15)',  # Graphite background color
        plot_bgcolor='rgb(15, 15, 15)',   # Graphite background color for the plot area
        font=dict(color='white'),          # Font color for better contrast
        title_font=dict(color='white')     # Title font color
    )
    carbon_pie_fig = px.pie(df, values="embodied carbon", names="element", color="element", 
                            hole=0.3, color_discrete_sequence=px.colors.sequential.Emrld)
    carbon_pie_fig.update_layout(
        height = 600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        paper_bgcolor='rgb(15, 15, 15)',  # Graphite background color
        plot_bgcolor='rgb(15, 15, 15)',   # Graphite background color for the plot area
        font=dict(color='white'),          # Font color for better contrast
        title_font=dict(color='white')     # Title font color
    )
    return volumes_fig, carbon_bar_fig, carbon_pie_fig


def generate_scatterplot(vertices):
    fig = px.scatter_3d(
        vertices,
        x="x",
        y="y",
        z="z",
        color="element",
        opacity=0.7,
        title="Element Vertices (m)",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_traces(marker=dict(size=4))
    
    fig.update_layout(
        paper_bgcolor='rgb(15, 15, 15)',   # Graphite background color
        plot_bgcolor='rgb(15, 15, 15)',    # Graphite background color for the plot area
        scene=dict(
            xaxis=dict(
                backgroundcolor='rgb(30, 30, 30)',  # Dark background for the cube
                gridcolor='white',                  # White grid lines
                showbackground=True,
                zerolinecolor='white',
            ),
            yaxis=dict(
                backgroundcolor='rgb(30, 30, 30)',  # Dark background for the cube
                gridcolor='white',                  # White grid lines
                showbackground=True,
                zerolinecolor='white',
            ),
            zaxis=dict(
                backgroundcolor='rgb(30, 30, 30)',  # Dark background for the cube
                gridcolor='white',                  # White grid lines
                showbackground=True,
                zerolinecolor='white',
            ),
        ),
        font=dict(color='white'),           # Font color for better contrast
        title_font=dict(color='white'),     # Title font color
        height=1000,
        legend=dict(
            x=0,                            # Move legend to the left
            y=1,                            # Position it at the top
            xanchor='left', 
            yanchor='top',
            bgcolor='rgba(0,0,0,0)',        # Transparent background
            font=dict(color='white')        # Ensure legend text is visible
        )
    )
    return fig
    
def update_all(model_name):
    project_id, model_id = set_model_data(model_name)
    objData = get_model_data(model_name)
    data, vertices = analyze_building_data(objData)
    graphs = generate_graphs(data)
    scatter_plot = generate_scatterplot(vertices)
    viewer_url = create_viewer_url(project_id, model_id)
    
    return f'<iframe src="{viewer_url}" style="width:100%; height:750px; border:none;"></iframe>', graphs[0], graphs[2], graphs[1], scatter_plot


# Create Gradio interface
with gr.Blocks(title="Building Analysis") as demo:
    gr.Markdown("## Building CO₂ Analysis Dashboard 📈")
    
    with gr.Row():
        model_dropdown = gr.Dropdown(value='kunsthaus zurich', label="Select Model", choices = ['farnsworth house', 'kunsthaus zurich'], allow_custom_value=True)
    with gr.Row(equal_height=True):
        viewer_iframe = gr.HTML()
        

    with gr.Row():
            gr.Markdown("## Volume Distribution (m³)", container=True)
            gr.Markdown("## CO2 Distribution (kgC0₂)", container=True)
    with gr.Row():
        volume_pie = gr.Plot(container=False, show_label=False)
        carbon_pie = gr.Plot(container=False, show_label=False)
    
    carbon_bar = gr.Plot(container=False, show_label=False)
    
    with gr.Row():
        scatter = gr.Plot(container=False, show_label=False)
    

    # Event handlers

    demo.load(
        fn=update_all,
        inputs=model_dropdown,
        outputs=[viewer_iframe, volume_pie, carbon_pie, carbon_bar, scatter]
    )
    
    model_dropdown.change(
        fn=update_all,
        inputs=model_dropdown,
        outputs=[viewer_iframe, volume_pie, carbon_pie, carbon_bar, scatter]
    )

demo.launch()

# gradio building_analysis.py

