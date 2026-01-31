"""Simple API for viewing execution logs."""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from src.utils.execution_logger import get_session_logs, get_recent_logs

app = FastAPI(title="Agent Execution Logs")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with recent logs."""
    logs = get_recent_logs(limit=50)
    
    html = """
    <html>
    <head>
        <title>Agent Execution Logs</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .success { color: green; }
            .error { color: red; }
            .truncate { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        </style>
    </head>
    <body>
        <h1>Agent Execution Logs</h1>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Session</th>
                <th>Agent</th>
                <th>User Input</th>
                <th>Sub-Agents</th>
                <th>Time (ms)</th>
                <th>Status</th>
            </tr>
    """
    
    for log in logs:
        status_class = "success" if log.get("status") == "success" else "error"
        sub_agents = ", ".join(log.get("sub_agents", [])) or "-"
        user_input = log.get("user_input", "")[:50]
        
        html += f"""
            <tr>
                <td>{log.get('timestamp', '')[:19]}</td>
                <td>{log.get('session_id', '')}</td>
                <td>{log.get('agent_type', '')}</td>
                <td class="truncate" title="{log.get('user_input', '')}">{user_input}</td>
                <td>{sub_agents}</td>
                <td>{log.get('execution_time_ms', 0)}</td>
                <td class="{status_class}">{log.get('status', '')}</td>
            </tr>
        """
    
    html += """
        </table>
        <p><a href="/api/logs">View JSON API</a></p>
    </body>
    </html>
    """
    return html


@app.get("/api/logs")
async def api_logs(
    session_id: str = Query(None, description="Filter by session ID"),
    limit: int = Query(20, description="Max results"),
):
    """Get execution logs as JSON."""
    if session_id:
        logs = get_session_logs(session_id, limit=limit)
    else:
        logs = get_recent_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}


@app.get("/api/logs/{session_id}")
async def api_session_logs(session_id: str, limit: int = Query(50)):
    """Get logs for specific session."""
    logs = get_session_logs(session_id, limit=limit)
    return {"session_id": session_id, "logs": logs, "count": len(logs)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
