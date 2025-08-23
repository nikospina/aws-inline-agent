import os
import boto3

from mcp import StdioServerParameters


from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

current_directory = os.getcwd()

# Step 1: Define MCP stdio parameters
server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-v", "/workspace:/local-directory", "mcp/filesystem", "/local-directory"],
)


async def main():
    # Step 2: Create MCP Client
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
            instruction="""You are a friendly code secure assistant that is responsible for resolving user queries. """,
            # Step 4.3: Provide the agent name and action group
            agent_name="remediate_vulnerabilities_agent",
            action_groups=[filesystem_action_group],
        ).invoke(
            input_text="Ten en cuenta las vulnerabilidades reportadas en el reporte de inspector inspector_scan.json y el arbol de dependencias dependenciesTree.txt, para resolver las vulnerabilidades reportadas tomando como base el pom.xml, debes retornar un archivo pom.xml nuevo con el ajuste y la respectiva documentación en formato md."
        )

    finally:

        await filesystem_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())