from mcp import StdioServerParameters

import asyncio
from InlineAgent.agent import InlineAgent
from rich.console import Console
from rich.markdown import Markdown
import argparse
from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

import os

current_directory = os.getcwd()
print("Current Directory:", current_directory)
# r"C:\Users\nospina\Documents\cobiscorp\docker\python\src\InlineAgent:/local-directory"

print (current_directory)

# Step 1: Define MCP stdio parameters
server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--memory=5g", "--cpus=3","--rm", "-v", "/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/834218fee9ac663d74241ecdbe0ba96e3192925a12ec663f3ea2b3caaf6b0f43/src/InlineAgent:/local-directory", "mcp/filesystem", "/local-directory"],
)


async def invoke_agent(modelId):

    #time_mcp_client = await MCPStdio.create(server_params=server_params)
    filesystem_mcp_client = await MCPStdio.create(server_params=server_params)

    try:
        # Step 3: Define an action group
        filesystem_action_group = ActionGroup(
            name="filesystemActionGroup",
            description="Helps user to get iteraction with local files.",
            mcp_clients=[filesystem_mcp_client],
        )

        # Step 4: Invoke agent
        await InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly code secure assistant that is responsible for resolving user queries.""",
            # Step 4.3: Provide the agent name and action group
            agent_name="remediate_vulnerabilities_agent",
            action_groups=[filesystem_action_group],
        ).invoke(
            input_text="Realiza las siguientes tareas sin utilizar la tarea read_multiple_files del mcp filesystem: 1. ubicate en el folder vulnerabilitiesFiles. 2. analiza el archivo inspector_scan.json. 3. Utiliza el pom.xml de referencia para corregir las vulnerabilidades reportadas en el reporte de inspector inspector_scan.json. 4. utiliza la herramienta write_file del mcp filesystem para crear un archivo nuevo pom-fix-vulnerabilities.xml completo que contenga todos los ajustes en el folder vulnerabilitiesFiles y que sea compilable. 6. No borre por completo alguna dependencia ya que el proyecto perderia su consistencia. 7. Tenga en cuenta que el proyecto conserve su compatibilidad con su respectiva version de java y spring boot. 8. Tenga en cuenta que en la sección de dependency management deben quedar las dependencias ajustadas, ya que esta configuración asegura que no se traigan mas versiones como transitivas"
            #Ten en cuenta las vulnerabilidades reportadas en el reporte de inspector inspector_scan.json y el arbol de dependencias dependenciesTree.txt en la carpeta vulnerabilitiesFiles, para resolver las vulnerabilidades reportadas tomando como base el pom.xml, debes retornar un archivo pom.xml nuevo con el ajuste y la respectiva documentación en formato md.
        )

    finally:

        await filesystem_mcp_client.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "modelId", help="Amazon Bedrock Foundational Model Id", type=str
    )
    args = parser.parse_args()

    code = f"""
from bedrock_agents.agent import InlineAgent

InlineAgent(
    foundationModel="{args.modelId}",
    instruction="You are a friendly assistant that is supposed to say hello to everything.",
    userInput=True,
    agentName="hello-world-agent",
).invoke("Hi how are you? What can you do for me?")
"""
    console = Console()
    console.print(Markdown(f"**Running Hello world agent:**\n```python{code}```"))
    asyncio.run(invoke_agent(modelId=args.modelId))
