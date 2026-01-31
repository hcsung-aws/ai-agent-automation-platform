"""Simple API for viewing execution logs and feedback."""
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from src.utils.execution_logger import get_session_logs, get_recent_logs, get_feedback

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


@app.get("/api/feedback")
async def api_feedback(
    rating: str = Query(None, description="Filter by rating: positive or negative"),
    limit: int = Query(50, description="Max results"),
):
    """Get feedback entries."""
    feedback = get_feedback(limit=limit, rating_filter=rating)
    return {"feedback": feedback, "count": len(feedback)}


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page():
    """Feedback dashboard page."""
    feedback = get_feedback(limit=100)
    positive = [f for f in feedback if f.get("rating") == "positive"]
    negative = [f for f in feedback if f.get("rating") == "negative"]
    
    html = """
    <html>
    <head>
        <title>Agent Feedback</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .stats { display: flex; gap: 20px; margin-bottom: 20px; }
            .stat-box { padding: 20px; border-radius: 8px; text-align: center; }
            .positive { background: #d4edda; color: #155724; }
            .negative { background: #f8d7da; color: #721c24; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #6c757d; color: white; }
            .truncate { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        </style>
    </head>
    <body>
        <h1>📊 Agent Feedback Dashboard</h1>
        <div class="stats">
            <div class="stat-box positive">
                <h2>👍 """ + str(len(positive)) + """</h2>
                <p>Positive</p>
            </div>
            <div class="stat-box negative">
                <h2>👎 """ + str(len(negative)) + """</h2>
                <p>Negative</p>
            </div>
        </div>
        
        <h2>Recent Feedback</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Rating</th>
                <th>User Input</th>
                <th>Comment</th>
            </tr>
    """
    
    for f in feedback[:50]:
        rating_emoji = "👍" if f.get("rating") == "positive" else "👎"
        comment = f.get("comment", "-") or "-"
        user_input = f.get("user_input", "")[:50]
        
        html += f"""
            <tr>
                <td>{f.get('timestamp', '')[:19]}</td>
                <td>{rating_emoji}</td>
                <td class="truncate">{user_input}</td>
                <td class="truncate">{comment}</td>
            </tr>
        """
    
    html += """
        </table>
        <p><a href="/">← Back to Logs</a> | <a href="/api/feedback">View JSON API</a></p>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
