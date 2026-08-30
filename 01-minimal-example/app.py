from dotenv import load_dotenv
from os import environ
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
        await context.send_activity("Nice to meet you ! I'll echo all the messages ...")
    elif action == "remove":
        await context.send_activity("Sorry, but goodbye !")

# Handle messages from users
@agent_app.activity("message", auth_handlers=["AGENTIC"])
async def on_message_activity(context: TurnContext, state: TurnState):
    user_text = context.activity.text
    await context.send_activity(f"You said: {user_text}")

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