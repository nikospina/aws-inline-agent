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

print (current_directory)

# Step 1: Define MCP stdio parameters
server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-v", "/workspace/aws-inline-agent:/local-directory", "mcp/filesystem", "/local-directory"],
    timeout=300000,
    env={"MCP_LOG_LEVEL": "DEBUG", "MCP_CONNECTION_TIMEOUT": "30", "MCP_REQUEST_TIMEOUT": "300"}
)

server_git_params = StdioServerParameters(
    command="python3.12",
    args=["-m", "mcp_server_git", "--repository", "/workspace/aws-inline-agent"],
)

#server_git_params = StdioServerParameters(
#    command="docker",
#    args=["run", "-i", "--rm", "-v", "/workspace:/workspace" , "mcp/git"],
#    timeout=300000,
#    env={"MCP_LOG_LEVEL": "DEBUG", "MCP_CONNECTION_TIMEOUT": "30", "MCP_REQUEST_TIMEOUT": "300"}
#)


async def invoke_agent(modelId):

    #time_mcp_client = await MCPStdio.create(server_params=server_params)
    filesystem_mcp_client = await MCPStdio.create(server_params=server_params)
    git_mcp_client = await MCPStdio.create(server_params=server_git_params)

    try:
        # Step 3: Define an action group
        filesystem_action_group = ActionGroup(
            name="filesystemActionGroup",
            description="Helps user to get iteraction with local files.",
            mcp_clients=[filesystem_mcp_client, git_mcp_client],
        )

        # Step 4: Invoke agent
        await InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly code secure assistant that is responsible for resolving user queries.""",
            # Step 4.3: Provide the agent name and action group
            agent_name="remediate_vulnerabilities_agent",
            action_groups=[filesystem_action_group],
        ).invoke(
            input_text="""
            Realiza las siguientes tareas:
            ------- SOLUCIÓN DE VULNERABILIDADES -------
            1. analiza los archivos del folder vulnerabilitiesFiles.
            2. Utiliza el pom.xml como referencia para corregir las vulnerabilidades reportadas en el reporte de inspector.
            3. Crear un nuevo archivo pom2.xml COMPLETO con todas las dependencias, configuraciones y ajustes realizados que sea compilable.
            4. No borre o excluya por completo alguna dependencia ya que el proyecto perderia su consistencia.
            5. En caso de que la ultima version disponible de alguna dependencia sea vulnerable, debe mantenerla.
            6. Tenga en cuenta que el proyecto conserve su compatibilidad con su respectiva version de java y spring boot.
            7. Tenga en cuenta que en la sección de dependency management deben quedar las dependencias ajustadas, ya que esta configuración asegura que no se traigan mas versiones como transitivas.
            8. La ruta del pom generado es ./output.
            9. Debes generar un archivo en formato .md de documentación en donde se explique cuales fueron las vulnerabilidades solucionadas y cuales no, debes dar un contexto de la vulnerabilidad y su criticiadad.
            10. Realiza commit de los ajustes realizados en en repositorio.
            11. Realiza el push al repositorio remoto."""
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


