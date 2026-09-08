# Observability

Deploy an OpenAI model (such as, `gpt-5.2`, `gpt-5.4`, ...) on Microsoft Foundry, and set those environment varibales in `.env` file.

The subsequent installation and setup procedures are the same as those described in "[Basic](https://github.com/tsmatsuz/microsoft-agent365-tutorials-python/blob/master/01-minimal-example/Readme.md)" chapter.<br>
If you have already set up, run the following commands to recreate the deployment asset (`deploy.zip`) and upload it again.

```cmd
# create deploy.zip with new assets
Compress-Archive -Path "app.py", ".\.env", "requirements.txt", "startup.sh" -DestinationPath "deploy.zip"
# deploy again (upload and run deployment script)
az webapp deploy --name $WEB_APP --resource-group $RESOURCE_GROUP --src-path deploy.zip
```

![Consume agent](https://tsmatz.wordpress.com/wp-content/uploads/2026/09/20260905_teams_rollplay.jpg)

## View the collected logs (activities)

Open Microsoft Defender (https://security.microsoft.com/).

Go to "`System`" – "`Settings`" – "`Security for AI`" in navigation, and make sure that "`Agent 365`" and "`Microsoft 365 Connector`" are connected.

Run the following query (KQL) in Microsoft Defender advanced hunting.

```
let agentIdToFind = "YOUR-AGENT-APP-ID";
CloudAppEvents
| where Timestamp > ago(7d)
| where ActionType in (
    "InvokeAgent",
    "InferenceCall",
    "ExecuteToolBySDK",
    "ExecuteToolByGateway",
    "ExecuteToolByMCPServer"
)
| extend Data = parse_json(tostring(RawEventData))
| where tostring(Data.AgentId) == agentIdToFind
    or tostring(Data.TargetAgentId) == agentIdToFind
    or tostring(Data.PlatformTargetAgentId) == agentIdToFind
| project Timestamp, ActionType, Data
| order by Timestamp desc
```

> Note : In this example, I'm using Microsoft Agent Framework (MAF). This library depends on a lot of other libraries (Anthropic client, Gemini client, etc), so it is advisable to perform selective installation — such as, `agent-framework-core` and `agent-framework-openai`. (In this `requirements.txt`, all the dependency packages in MAF will be installed and it will take a while to complete installation.)