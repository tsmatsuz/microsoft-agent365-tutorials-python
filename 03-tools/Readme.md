# Tools

The installation and setup procedures are mostly the same as those described in "[Basic](https://github.com/tsmatsuz/microsoft-agent365-tutorials-python/blob/master/01-minimal-example/Readme.md)" chapter.

Add the following two steps to the procedures described in "2. Create assets" section.

## 1. Deploy model

Deploy an OpenAI model (such as, `gpt-5.2`, `gpt-5.4`, ...) on Microsoft Foundry, and set those environment varibales in `.env` file.

## 2. Grant additional permissions

By running the following command, set Mail tool in `ToolingManifest.json` file. (The `ToolingManifest.json` file is created.)

```cmd
a365 develop add-mcp-servers mcp_MailTools
```

By running the following command, grant tool's permissions to the blueprint.

```cmd
a365 setup permissions mcp
```

---

Once the assets are ready, perform steps from "3. Deploy" in "[Basic](https://github.com/tsmatsuz/microsoft-agent365-tutorials-python/blob/master/01-minimal-example/Readme.md)" chapter.

If you have already set up, run the following commands to recreate the deployment asset (`deploy.zip`) and upload it again.

```cmd
# create deploy.zip with new assets
Compress-Archive -Path "app.py", ".\.env", "requirements.txt", "startup.sh" -DestinationPath "deploy.zip"
# deploy again (upload and run deployment script)
az webapp deploy --name $WEB_APP --resource-group $RESOURCE_GROUP --src-path deploy.zip
```

Please try entering the prompt below and asking it to send an email to you.

"`Please list five recommended sightseeing spots in Osaka and email it to {my-user-name}@{my-org-domain}.onmicrosoft.com.`"

![Consume agent](https://tsmatz.wordpress.com/wp-content/uploads/2026/09/20260916_teams_rollplay.jpg)

> Note : In this example, I'm using Microsoft Agent Framework (MAF). This library depends on a lot of other libraries (Anthropic client, Gemini client, etc), so it is advisable to perform selective installation — such as, `agent-framework-core` and `agent-framework-openai`. (In this `requirements.txt`, all the dependency packages in MAF will be installed and it will take a while to complete installation.)