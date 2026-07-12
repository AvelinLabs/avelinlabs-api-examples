# Customer Grounding MCP Stdio Launch

The MCP adapter is a local stdio adapter that calls the authenticated AvelinLabs Runtime API. It is not a public remote MCP server.

Set environment variables:

```powershell
$env:AVELIN_MCP_API_BASE_URL = "https://api.avelinlabs.com"
$env:AVELIN_MCP_RUNTIME_API_KEY = "replace-with-runtime-api-key"
$env:AVELIN_MCP_REQUEST_TIMEOUT_SECONDS = "30"
```

Check version:

```powershell
python backend\scripts\run_avelin_mcp_server.py --version
```

Launch stdio adapter:

```powershell
python backend\scripts\run_avelin_mcp_server.py
```

Current Customer Grounding MCP tools expose text ingestion only. Use REST for file ingestion.
