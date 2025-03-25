import gradio as gr
import pandas as pd
import plotly.express as px
import numpy as np

# To activate the app with auto-update, run:
#python -m venv venv 
#venv/Scripts/activate
#pip install gradio and all other libraries attached
#gradio space_calculator.py

# Initial Data
values = [20, 2, 3, 10, 10, 3, 2, 0.5, 2.6, 10]

# Function to calculate the second column
def calculate_second_row(values, total_area):
    sum_values = sum(values)
    return [round((value * total_area) / sum_values, 1) for value in values]

# Function to create DataFrame
def create_dataframe(values, total_area):
    second_row = calculate_second_row(values, total_area)
    
    df = pd.DataFrame({
         'Sub-Category': [
            'Living Space', 
            'Circulation & Common Areas', 
            'Shared Amenities',
            'Energy Generation', 
            'Food Production', 
            'Waste Management',
            'Schools', 
            'Hospitals', 
            'Retail & Amenities', 
            'Green Spaces',
        ],
        'Category': [
            'Residential',
            'Residential', 
            'Residential',
            'Industrial', 
            'Industrial',
            'Industrial',
            'Services', 
            'Services',
            'Services', 
            'Services',
        ],
        
        'Area per person (m²)': values,
        'Total Area (m²)': second_row,
    })
    
    # Append Grand Totals
    grand_totals = pd.DataFrame({
        'Sub-Category': 'Grand Totals',
        'Category': ['All'],
        'Area per person (m²)': [sum(values)],
        'Total Area (m²)': [round(sum(second_row),0)]
    })
    
    df = pd.concat([df, grand_totals], ignore_index=True)
    return df

# Function to create category totals
def create_df_categoryTotals(df):
    categories = df['Category'].unique()
    category_totals = []

    for category in categories:
        if category != 'All':
            area_per_person = df.loc[df['Category'] == category, 'Area per person (m²)'].sum()
            total_area = df.loc[df['Category'] == category, 'Total Area (m²)'].sum()
            category_totals.append({
                'Category': category,
                'Total Area per person (m²)': area_per_person,
                'Total Area (m²)': total_area
            })

    df_totals = pd.DataFrame(category_totals)
    grand_totals = pd.DataFrame({
        'Category': ['Grand Totals'],
        'Total Area per person (m²)': [df_totals['Total Area per person (m²)'].sum()],
        'Total Area (m²)': [round(df_totals['Total Area (m²)'].sum(), 0)]
    })
    
    df_totals = pd.concat([df_totals, grand_totals], ignore_index=True)
    return df_totals


# Function to calculate population
def calculate_population(df):
    total_area = df.loc[df['Category'] == 'All', 'Total Area (m²)'].values[0]
    total_person_area = df.loc[df['Category'] == 'All', 'Area per person (m²)'].values[0]
    return int(total_area / total_person_area)

def create_piechart(values, names, categories):
    # Define color palettes
    color_palettes = {
        'Residential': px.colors.sequential.Emrld[1:],  
        'Industrial': px.colors.sequential.Blues[3:],
        'Services': px.colors.sequential.Purples[3:]
    }
    
    # Convert categories to a list if it's a Pandas Series
    if isinstance(categories, pd.Series):
        categories = categories.tolist()

    # Assign colors based on category
    color_sequence = []
    for i, cat in enumerate(categories):
        cat = str(cat).strip()  # Remove spaces
        cat = cat.capitalize()  # Ensure proper capitalization (matches keys)

        palette = color_palettes.get(cat, px.colors.sequential.Sunsetdark[3:])  # Default fallback

        if not palette:  # Fallback to gray if empty
            color_sequence.append("#CCCCCC")
        else:
            color_index = i % len(palette)
            color_sequence.append(palette[color_index])

    # Create pie chart
    graph = px.pie(values=values, names=names, hole=0.3, color_discrete_sequence=color_sequence)

    # Style adjustments
    graph.update_layout(
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
        font=dict(color='black'),
        title_font=dict(color='black')
    )

    graph.update_traces(textposition='outside', sort = False)  # Display values outside bars
    
    return graph

def highlight_last_row(s):
    color = 'rgba(73, 191, 102, 0.25)'  # Light blue with 50% transparency
    return [f'background-color: {color}' if i == s.index[-1] else '' for i in s.index]

# Initial calculation
default_total_area = 1000000
initial_df = create_dataframe(values, default_total_area)
initial_population = calculate_population(initial_df)
initial_dfTotals = create_df_categoryTotals(initial_df)

# highlight last row of dataframe
initial_df_styled = initial_df.style.apply(highlight_last_row, axis=0)
initial_dfTotals_styled = initial_dfTotals.style.apply(highlight_last_row, axis=0)

df_residential = initial_df[initial_df['Category'] == 'Residential']
df_service = initial_df[initial_df['Category'] == 'Services']
df_industrial = initial_df[initial_df['Category'] == 'Industrial']

# Gradio Interface
with gr.Blocks(theme=gr.themes.Default(primary_hue="indigo", text_size="lg"), css="""
        .custom-number input {
            font-size: 32px;  /* Increase font size */
            font-weight: bold; /* Make text bold */
            font-color: black; /* Ensure good contrast */
            background-color: black; /* Light gray background */
            text-align: center; /* Center align the number */
        }
        .panel {
        background-color: #626263 !important; /* Light grey background */
        padding: 255px; /* Add some padding */
        border-radius: 8px; /* Rounded corners */
        }
    """) as demo:
    gr.Markdown("# 🌇 Space Distribution Calculator")
    with gr.Row():
        with gr.Column(variant='panel'):
                gr.Markdown("# Inputs")
            # with gr.Column():
                # with gr.Row():
                total_area_input = gr.Number(label="Total area of plot in sq.m.", value=default_total_area, interactive=True) 
                gr.Examples(examples=[10000, 50000, 100000, 500000, 1000000], inputs = total_area_input)
                with gr.Row():
                    with gr.Column(scale =1, variant = 'compact',  min_width = 80):
                        gr.Markdown("### Residential area in sq.m.       per person")
                        input_1 = gr.Number(value=values[0], label="Living Space (minimum 10m²)", interactive=True)
                        input_2 = gr.Number(value=values[1], label="Circulation & Common Areas", interactive=True) 
                        input_3 = gr.Number(value=values[2], label="Shared Amenities", interactive=True)
                    with gr.Column(scale =1, variant = 'compact',  min_width = 80):
                        gr.Markdown("### Industrial area in sq.m.       per person")
                        input_4 = gr.Number(value=values[3], label="Energy Generation", interactive=True)
                        input_5 = gr.Number(value=values[4], label="Food Production", interactive=True) 
                        input_6 = gr.Number(value=values[5], label="Waste Management", interactive=True) 
            # with gr.Column(scale =1, variant = 'panel',  min_width = 80):
                
                with gr.Column(variant='compact'):
                    # with gr.Column(min_width=100):
                        gr.Markdown("### Service area in sq.m. per person")
                        with gr.Row():
                            with gr.Column(min_width=100):
                                input_7 = gr.Number(value=values[6], label="Schools", interactive=True)
                                input_8 = gr.Number(value=values[7], label="Hospitals", interactive=True) 
                            with gr.Column(min_width=100):
                                input_9 = gr.Number(value=values[8], label="Retail & Amenities", interactive=True)
                                input_10 = gr.Number(value=values[9], label="Green Spaces", interactive=True)      
            # with gr.Row():        
                btn = gr.Button(value="Recalculate", variant='primary')
        with gr.Column(scale=2):
                gr.Markdown("# Outputs")
                # gr.Markdown("#", height=50)
                gr.Markdown("## Population")
                population_output = gr.Number(value=initial_population, label="POPULATION", container=False, interactive=False, elem_classes="custom-number")
                gr.Markdown("#", height=5)
                gr.Markdown("### Calculated Space Distribution")
                output_df = gr.DataFrame(value=initial_df_styled, show_label=False, interactive=False, column_widths=[50,30,50, 50])
                gr.Markdown("#", height=2)
                gr.Markdown("### Calculated Space Distribution by Category")
                output_dfTotals = gr.DataFrame(value=initial_dfTotals_styled, show_label=False, interactive=False, column_widths=[80, 50, 50])
    gr.Markdown("# Graphs")
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Space Distribution", container=True)
            output_pie_chart = gr.Plot(value=create_piechart(initial_df['Total Area (m²)'][:-1], initial_df['Sub-Category'][:-1], initial_df['Category'][:-1]), label="Space Distribution Pie Chart", container=False)
            
        with gr.Column():
            gr.Markdown("## Space Distribution by Category", container=True)
            output_pie_chartTotals = gr.Plot(value=create_piechart(initial_dfTotals['Total Area (m²)'][:-1], initial_dfTotals['Category'][:-1], initial_dfTotals['Category'][:-1]), label="Space Distribution Pie Chart by Group", container=False)
    gr.Markdown("#", height=50)
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Residentiial Space Distribution", container=True)
            output_pie_chart_res = gr.Plot(value=create_piechart(df_residential['Total Area (m²)'], df_residential['Sub-Category'], df_residential['Category']), label="Residential Space Distribution", container=False)   
        with gr.Column():
            gr.Markdown("## Industrial Space Distribution", container=True)
            output_pie_chart_ind = gr.Plot(value=create_piechart(df_industrial['Total Area (m²)'], df_industrial['Sub-Category'], df_industrial['Category']), label="Industrial Space Distribution", container=False)
        with gr.Column():
            gr.Markdown("## Service Space Distribution", container=True)
            output_pie_chart_ser = gr.Plot(value=create_piechart(df_service['Total Area (m²)'], df_service['Sub-Category'], df_service['Category']), label="Service Space Distribution", container=False)


    def update_outputs(input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, total_area):
        values = [input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10]
        
        # Update the main DataFrame
        df = create_dataframe(values, total_area)
        population = calculate_population(df)
        dfTotals = create_df_categoryTotals(df)
        
        # **Update filtered DataFrames**
        df_residential = df[df['Category'] == 'Residential']
        df_industrial = df[df['Category'] == 'Industrial']
        df_service = df[df['Category'] == 'Services']

        # **Generate updated pie charts**
        pie_chart = create_piechart(df['Total Area (m²)'][:-1], df['Sub-Category'][:-1], df['Category'][:-1])
        pie_chartTotals = create_piechart(dfTotals['Total Area (m²)'][:-1], dfTotals['Category'][:-1], dfTotals['Category'][:-1])
        
        pie_chart_res = create_piechart(df_residential['Total Area (m²)'], df_residential['Sub-Category'], df_residential['Category'])
        pie_chart_ind = create_piechart(df_industrial['Total Area (m²)'], df_industrial['Sub-Category'], df_industrial['Category'])
        pie_chart_ser = create_piechart(df_service['Total Area (m²)'], df_service['Sub-Category'], df_service['Category'])
        
        # **Apply updated styling**
        df_styled = df.style.apply(highlight_last_row, axis=0)
        dfTotals_styled = dfTotals.style.apply(highlight_last_row, axis=0)
    
        return df_styled, population, dfTotals_styled, pie_chart, pie_chartTotals, pie_chart_res, pie_chart_ind, pie_chart_ser
   
    btn.click(fn=update_outputs, inputs=[input_1, input_2, input_3, input_4, input_5, input_6, input_7, input_8, input_9, input_10, total_area_input], outputs=[output_df, population_output, output_dfTotals, output_pie_chart, output_pie_chartTotals,
                                                                                                                                                                    output_pie_chart_res, output_pie_chart_ind, output_pie_chart_ser])

# Launch the app
demo.launch()

