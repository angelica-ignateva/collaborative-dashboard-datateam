import gradio as gr
import pandas as pd
import plotly.express as px
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from config import speckle_token

from residential_page import r_demo
# from gradio_page import b_demo
# from space_calculator import sc_demo

# CSS to remove all scrollbars in gradio
custom_css = """
/* Hide scrollbars for Chrome, Safari and Opera */
.gradio-container *::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

/* Hide scrollbars for IE, Edge and Firefox */
.gradio-container * {
  -ms-overflow-style: none !important;  /* IE and Edge */
  scrollbar-width: none !important;  /* Firefox */
}

/* Fix potential overflow issues while ensuring content is still accessible */
.gradio-container [data-testid="table"] {
  overflow: hidden !important;
}

.gradio-container .gradio-dataframe {
  overflow: hidden !important;
}

/* Target additional selectors that might contain scrollbars */
.gradio-container .table-wrap {
  overflow: hidden !important;
}

.gradio-container .scroll-container {
  overflow: hidden !important;
}

/* Handle any fixed height elements that might trigger scrollbars */
.gradio-container .fixed-height {
  max-height: none !important;
}
"""

js_func = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""



# Initialize Speckle client and credentials
speckle_server = "macad.speckle.xyz"
client = SpeckleClient(host=speckle_server)
account = get_account_from_token(speckle_token, speckle_server)
client.authenticate_with_account(account)

# Project ID
project_id = "28a211b286"
project = client.project.get_with_models(project_id=project_id, models_limit=100)

# Add this function to filter models by team selection
def update_model_selection_by_team(team_selection):
    models = project.models.items

    if team_selection == "Residential":
        filtered_models = [m.name for m in models if m.name.startswith('residential')]
    elif team_selection == "Structure":
        filtered_models = [m.name for m in models if m.name.startswith('structure')]
    elif team_selection == "Service":
        filtered_models = [m.name for m in models if m.name.startswith('service')]
    elif team_selection == "Facade":
        filtered_models = [m.name for m in models if m.name.startswith('facade')]
    elif team_selection == "Industrial":
        filtered_models = [m.name for m in models if m.name.startswith('industrial')]
    elif team_selection == "Data":
        filtered_models = [m.name for m in models if m.name.startswith('data')]

    return gr.Dropdown(choices=filtered_models, label="Select Model", value=filtered_models[0] if filtered_models else None)


def get_all_versions_in_project():
    all_versions = []
    for model in project.models.items:
        versions = client.version.get_versions(model_id=model.id, project_id=project.id, limit=100).items
        all_versions.extend(versions)
    return all_versions

# def update_model_selection(model_name):
#     models = project.models.search(name=model_name)[0]
#     return models

# def version_name(version):
#         timestamp = version.createdAt.strftime("%Y-%m-%d %H:%M:%S")
#         return ' - '.join([version.authorUser.name, timestamp, version.message])

# def update_version_selection(model):
#     versions = client.version.get_versions(model_id=model.id, project_id=project.id, limit=100).items
    
#     return [version_name(version) for version in versions]


# Function to update viewer and stats
def create_viewer_url(model_name):
    # Find the model in the project
    model = next((m for m in project.models.items if m.name == model_name), None)
    if model:
        versions = client.version.get_versions(model_id=model.id, project_id=project_id, limit=1).items
        if versions:
            version = versions[0]
            embed_src = f"https://macad.speckle.xyz/projects/{project_id}/models/{model.id}@{version.id}#embed=%7B%22isEnabled%22%3Atrue%2C%7D"
            return f'<iframe src="{embed_src}" style="width:100%; height:850px; border:none;"></iframe>'
        else:
            return "No versions found for this model."
    else:
        return "Model not found."

def generate_model_statistics():
    models = project.models.items
    data = [{"Model Name": m.name, "Total Commits": len(client.version.get_versions(model_id=m.id, project_id=project.id, limit=100).items)} for m in models]
    df = pd.DataFrame(data)
    df = df.sort_values(by="Model Name")
    return df

def generate_connector_statistics(all_versions):
    connector_list = [v.sourceApplication for v in all_versions]
    df = pd.DataFrame(connector_list, columns=["Connector"])
    df = df["Connector"].value_counts().reset_index()
    df.columns = ["Connector", "Usage Count"]
    return df

def generate_contributor_statistics(all_versions):
    contributors = [v.authorUser.name for v in all_versions]
    df = pd.DataFrame(contributors, columns=["Contributor"])
    df = df["Contributor"].value_counts().reset_index()
    df.columns = ["Contributor", "Contributions"]
    return df


# def generate_statistics():
all_versions = get_all_versions_in_project()
model_stats_df = generate_model_statistics()
connector_stats_df = generate_connector_statistics(all_versions)
contributor_stats_df = generate_contributor_statistics(all_versions)
    
#     return model_stats_df, connector_stats_df, contributor_stats_df

# def create_graphs():
models = project.models.items
# Extract models and their commit counts
model_counts = pd.DataFrame([
    [m.name, len(client.version.get_versions(model_id=m.id, project_id=project.id, limit=100).items)] for m in models], columns=["modelName", "totalCommits"])

# Define function to categorize models
def categorize_model(name):
    if name.startswith("residential"):
        return "Residential"
    elif name.startswith("facade"):
        return "Facade"
    elif name.startswith("structure"):
        return "Structure"
    elif name.startswith("service"):
        return "Service"
    elif name.startswith("industrial"):
        return "Industrial"
    elif name.startswith("data"):
        return "Data"
    else:
        return "Other"

# Apply categorization
model_counts["team"] = model_counts["modelName"].apply(categorize_model)
model_counts["modelName"] = model_counts["modelName"].apply(lambda x: x.split('/', 1)[1] if '/' in x else x)

# Create bar plot grouped by category
model_graph = px.bar(
    model_counts, 
    x="modelName", 
    y="totalCommits", 
    color="team",  # Grouped by category
    color_discrete_map={
        "Residential": "#338547",
        "Facade": "#652cb3",
        "Structure": "#1864b5",
        "Service": "#ff8800",
        "Industrial": "#b50709",
        "Data": "white",         
        "Other": "gray"
    }
)

# Update layout for dark mode
model_graph.update_layout(
    height=800,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    paper_bgcolor='rgb(15, 15, 15)',
    plot_bgcolor='rgb(15, 15, 15)',
    font=dict(color='white'),
    title_font=dict(color='white')
)

# Connector distribution
version_frame = pd.DataFrame.from_dict([{"sourceApplication": v.sourceApplication} for v in all_versions])
apps = version_frame["sourceApplication"].value_counts().reset_index()
apps.columns = ["app", "count"]
connector_graph = px.pie(apps, names="app", values="count", hole=0.3, color_discrete_sequence=px.colors.sequential.Emrld)
connector_graph.update_layout(
    height = 600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    paper_bgcolor='rgb(15, 15, 15)',  # Background color of the entire chart
    plot_bgcolor='rgb(15, 15, 15)',    # Background color of the plot area
    font=dict(color='white'),          # Font color for better contrast
    title_font=dict(color='white'))
connector_graph.update_traces(textposition='outside', sort = False, pull=[0.1] * len(apps))  # Display values outside bars

# Contributor distribution
version_user_names = [v.authorUser.name for v in all_versions]
authors = pd.DataFrame(version_user_names).value_counts().reset_index()
authors.columns = ["author", "count"]
contributor_graph = px.pie(authors, names="author", values="count", hole=0.3, color_discrete_sequence=px.colors.sequential.Sunsetdark)
contributor_graph.update_layout(
    height = 600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    paper_bgcolor='rgb(15, 15, 15)',  # Background color of the entire chart
    plot_bgcolor='rgb(15, 15, 15)',    # Background color of the plot area
    font=dict(color='white'),          # Font color for better contrast
    title_font=dict(color='white'))
    
#     return model_graph, connector_graph, contributor_graph

# model_graph, connector_graph, contributor_graph = create_graphs()

# Aggregate commits per team
team_commit_counts = model_counts.groupby("team")["totalCommits"].sum().reset_index()
custom_order = ['Data', 'Residential', 'Service', 'Structure', 'Industrial', 'Facade', 'Others']

# Convert 'team' to a categorical type with the custom order
team_commit_counts['team'] = pd.Categorical(
    team_commit_counts['team'], 
    categories=custom_order, 
    ordered=True
)

# Sort the DataFrame by the 'team' column
team_commit_counts = team_commit_counts.sort_values('team')

team_graph = px.bar(
    team_commit_counts, 
    x="team", 
    y="totalCommits", 
    color="team", 
    title="Total Commits per Team",
    color_discrete_map={
        "Residential": "#338547",
        "Facade": "#652cb3",
        "Structure": "#1864b5",
        "Service": "#ff8800",
        "Industrial": "#b50709",
        "Data": "white",         
        "Other": "gray"
    }
)

# Update layout for dark mode
team_graph.update_layout(
    height=600,
    paper_bgcolor='rgb(15, 15, 15)',
    plot_bgcolor='rgb(15, 15, 15)',
    font=dict(color='white'),
    title_font=dict(color='white')
)

def create_timeline():
    all_versions = get_all_versions_in_project()
    timestamps = [version.createdAt.date() for version in all_versions]
    timestamps_frame = pd.DataFrame(timestamps, columns=["createdAt"]).value_counts().reset_index()
    timestamps_frame.columns = ["date", "count"]
    timestamps_frame["date"] = pd.to_datetime(timestamps_frame["date"])
    # timeline = px.line(timestamps_frame.sort_values("date"), x="date", y="count", title="Commit Activity Timeline", markers=True)
    return timestamps_frame
    


# Create Gradio interface
with gr.Blocks(title="Speckle Stream Activity Dashboard", css=custom_css, js=js_func, theme=gr.themes.Default(primary_hue="indigo", text_size="lg"), fill_width=True) as demo:

    with gr.Tab("Speckle Insights"):
        gr.Markdown("# Speckle Stream Activity Dashboard 📈")
        gr.Markdown("### HyperBuilding B Analytics")
        gr.Markdown("# Team Models Analysis", container=True)
        with gr.Row():
            with gr.Column(scale=2):
                viewer_iframe = gr.HTML()

            with gr.Column():
                models_res = [item for item in project.models.items if item.name.startswith('residential/')]
                models_name_res = [m.name for m in models_res]
                models_name_res = [name.split('/', 1)[1] if '/' in name else name for name in models_name_res]
                team_dropdown = gr.Dropdown(choices=["Residential", "Structure", "Service", "Facade", "Industrial", "Data"], label="Select Team",value="Residential")
                model_dropdown = gr.Dropdown(choices=models_name_res, label="Select Model")
                # version_dropdown = gr.Dropdown(label="Select Version")
                
        
        # with gr.Row():
        #     # model_stats = gr.Dataframe(label="Model Statistics", datatype=["str", "number"])
        #   
        gr.Markdown("#", height=50)  
        with gr.Row():
            gr.Markdown("# Application Usage", container=True)
            gr.Markdown("# Contributor Distribution", container=True)
        with gr.Row():
            connector_plot = gr.Plot(connector_graph, container=False, label="Connector Distribution")
            contributor_plot = gr.Plot(contributor_graph, container=False, label="Contributor Distribution")

        
        
        model_plot = gr.Plot(model_graph, container=False, label="Model Commit Distribution")
        team_plot = gr.Plot(team_graph, container=False, label="Team Commit Distribution")
            
        
        with gr.Row():
            timestamps_frame = create_timeline()
            timeline_plot = gr.LinePlot(timestamps_frame, x = "date", y = "count", height=400)
        
        with gr.Row(equal_height=True):
            with gr.Column():
                model_stats = gr.Dataframe(model_stats_df, label="Model Statistics", datatype=["str", "number"], show_fullscreen_button=True, show_copy_button=True, wrap=True, max_height=1000)
            with gr.Column():
                connector_stats = gr.Dataframe(connector_stats_df, label="Connector Statistics", datatype=["str", "number"])
                contributor_stats = gr.Dataframe(contributor_stats_df, label="Contributor Statistics", datatype=["str", "number"])
    
    with gr.Tab("Residential Team"):
        r_demo.render()
        
    # # with gr.Tab("Building Analysis"):
    # #     b_demo.render()

    # Load spekcle viewer
    def initialize_app():
        viewer_url = create_viewer_url('residential/shared/unit_exterior_walls')
        return viewer_url

    demo.load(fn=initialize_app, outputs=[viewer_iframe])


    # Event handlers
    team_dropdown.change(
        fn=update_model_selection_by_team,
        inputs=team_dropdown,
        outputs=[model_dropdown]
    )

    model_dropdown.change(
        fn=create_viewer_url,
        inputs=[model_dropdown],
        outputs=viewer_iframe
    )

    

    # version_dropdown.change(
    #     fn=update_viewer_and_stats,
    #     inputs=[model_dropdown, version_dropdown],
    #     outputs=[viewer_iframe]
    # )



demo.launch()

# gradio speckle_insights.py