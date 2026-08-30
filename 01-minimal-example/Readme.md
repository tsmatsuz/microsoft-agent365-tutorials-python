# Basic (Primitive Echo Agent)

## Prerequisites

Please prepare and install the following components:

- Global Administrator account in your Entra ID tenant (organization)
- Microsoft 365 Copilot and Microsoft Agent 365 license (or Microsoft 365 Frontier for Autopilots license)
- PowerShell 7 or later
- Azure (`az` commands) CLI
- Agent 365 (`a365` commands) CLI
- Python

Next **register an application in Entra ID**.<br>
Please [refer](https://tsmatz.wordpress.com/2026/08/30/build-autopilot-agent-using-microsoft365-agents-sdk-and-agent365-sdk/) here for the procedure.

## Run code

All commands should be run on PowerShell 7 or later. (You cannot use current stable version, PowerShell 5.)<br>
Let's follow the steps below for code execution.

> Note : I strongly recommend you to work in Python virtual environment.

> Note : All these settings are experimented by using Agent 365 CLI (`a365`) version `1.1.214 (+90c444832f)`.

Clone this repository.

```cmd
git clone http://github.com/tsmatsuz/microsoft-agent365-tutorials-python.git
```

Make blank directory and change your working directory.

```
mkdir your-test
cd your-test
```

Run the following command.<br>
During the wizard, :
- log-in to your tenant as administrator 
- set client id that you have added in prerequisites above
- set blank as Messaging endpoint URL

```cmd
a365 setup all --aiteammate --agent-name {set-arbitrary-name}
```

After setting, please copy client secret value for the generated blueprint.

Copy all files/folers in the repository into this folder.

```cmd
cp -r ../microsoft-agent365-tutorials-python/01-minimal-example/* .
```

Change all the placeholders in `.env` file.

By running the following command, compress the four files — `app.py`, `.env`, `requirements.txt`, and `startup.sh` — into `deploy.zip`.

```cmd
Compress-Archive -Path "app.py", ".\.env", "requirements.txt", "startup.sh" -DestinationPath "deploy.zip"
```

By running the following `az` commands, create Azure web app resource and deploy your Python package — `deploy.zip`. (Please change the following placeholders.)

```cmd
RESOURCE_GROUP={set-resource-group-name}
RESOURCE_LOCATION={set-resource-location}  # such as, eastus, japaneast, ...
APP_SERVICE_PLAN={set-app-service-plan-name}
WEB_APP={set-web-app-name}

# log in to Azure
az login
# create a resource group
az group create --name $RESOURCE_GROUP --location $RESOURCE_LOCATION
# create an App Service Plan (Linux)
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B1 --is-linux
# create a Web App
az webapp create --name $WEB_APP --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON|3.12"
# enable deployment build automation
az webapp config appsettings set --name $WEB_APP --resource-group $RESOURCE_GROUP --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
# configure the startup command
az webapp config set --name $WEB_APP --resource-group $RESOURCE_GROUP --startup-file "bash startup.sh"
# deploy package
az webapp deploy --name $WEB_APP --resource-group $RESOURCE_GROUP --src-path deploy.zip
```

By running the following command, configure the agent endpoint of the created Azure web app in your blueprint. (Please change the following placeholder.)

```cmd
a365 setup blueprint --endpoint-only `
  --messaging-endpoint https://{your-webapp-name}.azurewebsites.net/api/messages
```

Change all the placeholders in `manifest/manifest.json` file and `manifest/agenticUserTemplateManifest.json` file.<br>
In modification, you should generate two new GUIDs and set these for `id` property.

By running the following command, create the manifest package — `manifest.zip`.

```cmd
a365 publish
```

Open Microsoft 365 Admin Center and go to `Agents – All agents`. Select `Add agent` and upload the generated `manifest.zip` file above.<br>
After you have added (uploaded) your agent's manifest, also please activate this agent. (Select the agent and click `Activate`.) To activate your agent, you should assign the appropriate license — Microsoft Agent 365 license or Microsoft 365 Frontier for Autopilots license.

![Add and active agent](https://tsmatz.wordpress.com/wp-content/uploads/2026/08/20260827_published_agent.jpg)

In Microsoft 365 Admin Center, select your generated agent, and click `Add - instance`.<br>
In the wizard, set the alias for the instance, which is used as agent user's principal name — such as, "`{your-alias}@{your-domain}.onmicrosoft.com`".

![Create agent instance](https://tsmatz.wordpress.com/wp-content/uploads/2026/08/20260827_instance_setting.jpg)

After you have added an agent instance, the agent will appear in your Microsoft Teams.<br>
Now you can talk with this agent, as shown in the figure below.

![Consume agent](https://tsmatz.wordpress.com/wp-content/uploads/2026/08/20260827_autopilot_agent.jpg)
