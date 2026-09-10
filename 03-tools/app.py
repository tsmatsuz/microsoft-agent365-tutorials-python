from dotenv import load_dotenv
from os import environ
import asyncio
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    MemoryStorage,
    Authorization,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    start_agent_process,
)
from aiohttp.web import Application, Request, Response, run_app
# added for Microsoft Agent Framework (MAF)
import httpx
from agent_framework import (
    Agent,
    MCPStreamableHTTPTool,
)
from agent_framework.openai import OpenAIChatClient

load_dotenv()

#####
# AgentApplication creation
#####
agents_sdk_config = load_configuration_from_env(environ)

connection_manager = MsalConnectionManager(**agents_sdk_config)
storage = MemoryStorage()
agent_app = AgentApplication[TurnState](
    storage=storage,
    adapter=CloudAdapter(connection_manager=connection_manager),
    authorization=Authorization(storage, connection_manager, **agents_sdk_config),
    **agents_sdk_config,
)

#####
# Handlers
#####

# Handle agent install / uninstall events
@agent_app.activity("installationUpdate")
async def on_installation_update(context: TurnContext, _: TurnState):
    action = context.activity.action
    if action == "add":
        await context.send_activity("Nice to meet you ! How can I help you ?")
    elif action == "remove":
        await context.send_activity("Sorry, but goodbye !")

# Handle messages from users
@agent_app.activity("message", auth_handlers=["AGENTIC"])
async def on_message_activity(context: TurnContext, state: TurnState):
    #####
    # Generate token for mcp_MailTools
    #####
    authToken = await agent_app.auth.exchange_token(
        context,
        scopes=["16b1878d-62c7-4009-aa25-68989d63bbad/Tools.ListInvoke.All"],
        auth_handler_id="AGENTIC",
    )
    token = authToken.token

    #####
    # MAF Agent creation ...
    #   with tool and custom auth
    #####

    # set the token as authorization header
    class MyCustomAuth(httpx.Auth):
        def auth_flow(self, request: httpx.Request):
            request.headers["Authorization"] = f"Bearer {token}"
            yield request

    # generate httpx.AsyncClient for custom authentication
    my_async_client = httpx.AsyncClient(
        auth=MyCustomAuth(),
        follow_redirects=True,
        timeout=120.0,
    )

    # define tool with your own httpx.AsyncClient
    mail_mcp = MCPStreamableHTTPTool(
        name="mcp_MailTools",
        url="https://agent365.svc.cloud.microsoft/agents/servers/mcp_MailTools",
        load_prompts=False,
        approval_mode="never_require",
        http_client=my_async_client,
    )

    # generate MAF agent with above tool
    openai_client = OpenAIChatClient(
        model=environ.get("AZURE_OPENAI_MODEL"),
        api_key=environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=environ.get("AZURE_OPENAI_ENDPOINT"),
    )
    openai_agent = Agent(
        client=openai_client,
        instructions="You are a helpful assistant.",
        tools=[mail_mcp],
    )

    #####
    # run MAF agent and reply
    #####
    user_text = context.activity.text
    result = await openai_agent.run(user_text)
    await context.send_activity(result.text)

#####
# Run app
#####
app = Application()

async def entry_point(req: Request) -> Response:
    return await start_agent_process(
        req, req.app["agent_app"], req.app["adapter"]
    )

app.router.add_post("/api/messages", entry_point)
app.router.add_get("/api/messages", lambda _: Response(status=200))

app["agent_configuration"] = connection_manager.get_default_connection_configuration()
app["agent_app"] = agent_app
app["adapter"] = agent_app.adapter

port = int(environ.get("PORT", 8000))
host_addr = environ.get("HOST", "localhost")
print(f"Running the app on http://{host_addr}:{port}/api/messages")
run_app(app, host=host_addr,  port=port, handle_signals=True)