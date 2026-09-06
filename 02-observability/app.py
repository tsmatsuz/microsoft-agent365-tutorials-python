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
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from azure.core.credentials import AzureKeyCredential
# added for observability
from microsoft.opentelemetry import use_microsoft_opentelemetry
from microsoft.opentelemetry.a365.hosting.token_cache_helpers import (
    AgenticTokenCache, AgenticTokenStruct,
)
from microsoft_agents_a365.runtime.environment_utils import (
    get_observability_authentication_scope,
)
from microsoft_agents_a365.observability.core.middleware.baggage_builder import (
    BaggageBuilder,
)
from microsoft.opentelemetry.a365.hosting.scope_helpers.populate_baggage import (
    populate,
)

load_dotenv()

#####
# MAF Agent creation
#####
openai_client = OpenAIChatClient(
    model=environ.get("AZURE_OPENAI_MODEL"),
    api_key=environ.get("AZURE_OPENAI_API_KEY"),
    azure_endpoint=environ.get("AZURE_OPENAI_ENDPOINT"),
)
openai_agent = Agent(
    client=openai_client,
    instructions="You are a helpful assistant.",
    tools=[],
)

#####
# Setup for observability
#####
token_cache = AgenticTokenCache()
use_microsoft_opentelemetry(
    enable_a365=True,
    ##### enable_console=True,
    a365_enable_observability_exporter=True,  # should use with enable_a365=True
    enable_sensitive_data=True,
    # a365_token_resolver=lambda agent_id, tenant_id: (
    #     (t := asyncio.run(token_cache.get_observability_token(agent_id, tenant_id)))
    #     and t or None
    # ),
    a365_token_resolver=lambda agent_id, tenant_id: asyncio.run(token_cache.get_observability_token(agent_id, tenant_id)),
    instrumentation_options={
        "agent_framework": {"enabled": True},
    },
)

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
    # cache token for observability
    agent_id = context.activity.recipient.agentic_app_id
    tenant_id = context.activity.recipient.tenant_id
    token_cache.register_observability(
        agent_id=agent_id,
        tenant_id=tenant_id,
        token_generator=AgenticTokenStruct(
            authorization=agent_app.auth,
            turn_context=context,
        ),
        observability_scopes=get_observability_authentication_scope(),
    )

    # here we use populate(),
    #   instead of BaggageBuilder().tenant_id(...).agent_id(...).agentic_user_id(...).agentic_user_email(...) ...
    builder = BaggageBuilder()
    populate(builder, context)
    with builder.build():
        # run MAF agent and reply
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