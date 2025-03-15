from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.api.client import SpeckleClient
from specklepy.api import operations
from specklepy.objects.base import Base
from specklepy.core.api.inputs.version_inputs import CreateVersionInput
import plotly.express as px
from specklepy.core.api.operations import serialize as core_serialize
from specklepy.serialization.base_object_serializer import BaseObjectSerializer
import pandas as pd
from specklepy.objects import Base


# Identify the Project and Model

# project_id = "daeb18ed0a" #Kunshaus 
# model_id = "aab87740df"

project_id = "d3e86261bf" #Farnsworth House
model_id = "cd2eb6d0cc"
# model_id = "cd2eb6d0cc"

# Set up authentication and connection to server
client = SpeckleClient(host ="macad.speckle.xyz")
account = get_default_account()
client.authenticate_with_account(account)
transport = ServerTransport(project_id, client)

# # Get a list of active projects
# projects = client.active_user.get_projects(limit=3)
# for project in projects.items:
#     print(project.name)
#     print(project.id)

# Get a specific Model by ID
my_model = client.model.get(model_id, project_id)
print(my_model.name)

# Get the Referenced Object ID of the latest Version
versions = client.version.get_versions(model_id, project_id)
referenced_obj_id = versions.items[0].referencedObject
# Receive the referenced object (speckle object!)
print("Fetching data from the server...")
objData = operations.receive(referenced_obj_id, transport)

# operatons.serialize
print("Got the data!")

# speckle_object = objData["@Building"]

# child_obj = speckle_object["@{0}"][0]

child_obj = objData

print("Received Base object")


# child_obj = objData

# all_properties = child_obj.get_member_names()
# typed_properties = child_obj.get_typed_member_names()
# dynamic_properties = child_obj.get_dynamic_member_names()

# print("Properties received")

# obj = {}
# for p in dynamic_properties:
#     obj[p] = child_obj[p]


# PART TO ASSIGN PROPERTIES TO OBJECTS


MATERIALS_MAPPING = {
    "@Floors": "Concrete",
    "@FloorSlabs": "Concrete",
    "@Walls": "Concrete",
    "@Stairs": "Steel",
    "@Facade": "Glass",
    "@Roof": "Concrete",
    "@Columns": "Steel",
    "@Windows": "Glass",
}

DENSITY_MAPPING = {
    "@Floors": 2400,
    "@FloorSlabs": 2400,
    "@Walls": 2400,
    "@Stairs": 7800,
    "@Facade": 2500,
    "@Roof": 2400,
    "@Columns": 7800,
    "@Windows": 2500,
}

CARBON_MAPPING = {
    "@Floors": 0.159,
    "@FloorSlabs": 0.01,
    "@Walls": 0.159,
    "@Stairs": 0.13,
    "@Facade": 20.85,
    "@Roof": 0.159,
    "@Columns": 1.37,
    "@Windows": 0.11,
}


# first, get all the attribute names
names = child_obj.get_dynamic_member_names()
# then iterate through them to check if they exist in our mapping
# for name in names:
#     if name not in MATERIALS_MAPPING.keys():
#         break
#     # if they do, use this class method to get the class and init it
#     material = MATERIALS_MAPPING[name]
#     density = DENSITY_MAPPING[name]
#     carbon = CARBON_MAPPING[name]
#     # now we can add a `@material` attribute dynamically to each object.
#     # note that we're making it detachable with the `@`
#     prop = child_obj[name]
    
#     if isinstance(prop, list):
#         for item in prop:
#             item["@material"] = material
#             item["@density"] = density
#             item["@embodied_carbon"] = carbon
#     else:
#         prop["@material"] = material
#         prop["@density"] = density
#         prop["@embodied_carbon"] = carbon

# print("Properties assigned")

# # Send the updated object back to the server
# send_transport = ServerTransport(project_id, client) #sending to a different project/model
# hash = operations.send(base=child_obj, transports=[send_transport])

# # Create the actual commit that references this object
# version_data = CreateVersionInput(objectId=hash, modelId=model_id, projectId=project_id, message = "properties assigned (density & embodied carbon)", sourceApplication = "Python")
# client.version.create(version_data)
# print("New version was sent!")



#  //////////////////////////////////////////////////////////////////////////////////////////

data = {"element": [], "volume": [], "mass": [], "embodied carbon": []}
# child_obj = objData["@Building"]['@{0}'][0]
# # get the attributes on the level object
# names = child_obj.get_dynamic_member_names()
# iterate through and find the elements with a `volume` attribute
for name in names:
    if name not in MATERIALS_MAPPING.keys():
        break
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
    data["element"].append(name[1:]) # removing the prepending `@`

print("Finished!")
print(data)
print("Done!")

df = pd.DataFrame(data)

figures = {}

figures["volumes"] = px.pie(
    df,
    values="volume",
    names="element",
    color="element",
    title="Volumes of Elements (m3)",
)

figures["carbon bar"] = px.bar(
    df,
    x="element",
    y="embodied carbon",
    color="element",
    title="Embodied Carbon by Element (kgC02)",
)

figures["carbon pie"] = px.pie(
    df,
    values="embodied carbon",
    names="element",
    color="element",
    title="Embodied Carbon by Element (kgC02)",
)
for figure in figures:
    figures[figure].show()

 



