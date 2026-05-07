import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from main import graph
from src.notifications.auth import require_admin
from src.config import Settings
from src.notifications.pending import list_pending_reservations

log = logging.getLogger(__name__)
settings = Settings()  # type: ignore

app = FastAPI(title="Neo-Terra Parking Assistant")


def resume_graph_with_decision(
    thread_id: str, approved: bool, reason: str | None
) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    if not state.next:
        log.warning("No pending interrupt for thread_id=%s", thread_id)
        return

    payload = {"approved": approved}
    if not approved:
        payload["reason"] = reason or "No reason provided"

    graph.invoke(Command(resume=payload), config=config)
    log.info("Resumed graph thread_id=%s approved=%s", thread_id, approved)


class ChatRequest(BaseModel):
    message: str
    thread_id: str


class ChatResponse(BaseModel):
    response: str
    is_waiting_for_admin: bool = False


class AdminDecision(BaseModel):
    approved: bool
    reason: str = ""


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    state = graph.get_state(config)

    if state.next:
        return ChatResponse(
            response="Your reservation is pending admin approval. Please wait.",
            is_waiting_for_admin=True,
        )

    result = graph.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config,
    )

    new_state = graph.get_state(config)
    is_waiting = bool(new_state.next)

    return ChatResponse(
        response=result["messages"][-1].content, is_waiting_for_admin=is_waiting
    )


@app.post("/reservations/{thread_id}/approve")
def approve_reservation(thread_id: str, _: str = Depends(require_admin)):
    config = {"configurable": {"thread_id": thread_id}}

    state = graph.get_state(config)
    if not state.next:
        raise HTTPException(404, "No pending reservations for this thread.")

    result = graph.invoke(
        Command(resume={"approved": True}),
        config=config,
    )
    # result = graph.invoke({"reservation_status": "approved"})
    return {"status": "approved", "message": result["messages"][-1].content}


@app.post("/reservations/{thread_id}/reject")
def reject_reservation(
    thread_id: str, body: AdminDecision = None, _: str = Depends(require_admin)
):
    config = {"configurable": {"thread_id": thread_id}}

    state = graph.get_state(config)
    if not state.next:
        raise HTTPException(404, "No pending reservations for this thread.")

    reason = body.reason if body else "No reason provided."
    result = graph.invoke(
        Command(resume={"approved": False, "reason": reason}), config=config
    )
    # result = graph.invoke(
    #     {"reservation_status": "rejected", "rejection_status": reason}, config=config
    # )
    return {"status": "rejected", "message": result["messages"][-1].content}


@app.get("/admin/pending")
def admin_pending(_: str = Depends(require_admin)):
    items = list_pending_reservations(graph, settings.sqlite_db_path)
    return {
        "count": len(items),
        "items": [item.__dict__ for item in items],
    }


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return ADMIN_HTML


ADMIN_HTML = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Parking Admin</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 2rem; background: #fafafa; }
  h1 { margin-bottom: 0.25rem; }
  .sub { color: #666; margin-bottom: 1.5rem; }
  table { border-collapse: collapse; width: 100%; background: white; }
  th, td { border: 1px solid #ddd; padding: 0.6rem 0.8rem; text-align: left; }
  th { background: #f0f0f0; }
  button { padding: 0.4rem 0.8rem; margin-right: 0.3rem; cursor: pointer; border: 1px solid #888; border-radius: 4px; }
  button.approve { background: #2e7d32; color: white; border-color: #2e7d32; }
  button.reject  { background: #c62828; color: white; border-color: #c62828; }
  .empty { color: #888; padding: 2rem; text-align: center; background: white; border: 1px dashed #ccc; }
  .tid { font-family: monospace; font-size: 0.85em; color: #555; }
  .toast { position: fixed; top: 1rem; right: 1rem; padding: 0.8rem 1.2rem; background: #333; color: white; border-radius: 4px; opacity: 0; transition: opacity 0.3s; }
  .toast.show { opacity: 1; }
</style>
</head>
<body>
  <h1>Pending parking reservations</h1>
  <div class="sub">Auto-refreshes every 5s. <span id="count"></span></div>
  <div id="list"></div>
  <div id="toast" class="toast"></div>

<script>
const list = document.getElementById('list');
const countEl = document.getElementById('count');
const toast = document.getElementById('toast');

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

async function refresh() {
  try {
    const res = await fetch('/admin/pending');
    const data = await res.json();
    render(data.items);
    countEl.textContent = `(${data.count} pending)`;
  } catch (e) {
    countEl.textContent = '(connection error)';
  }
}

function render(items) {
  if (!items.length) {
    list.innerHTML = '<div class="empty">No pending reservations.</div>';
    return;
  }
  const rows = items.map(it => `
    <tr>
      <td>
        <div>${escapeHtml(it.name)} ${escapeHtml(it.surname)}</div>
        <div class="tid">thread: ${escapeHtml(it.thread_id)}</div>
      </td>
      <td>${escapeHtml(it.plate)}</td>
      <td>${escapeHtml(it.date_start)} → ${escapeHtml(it.date_end)}</td>
      <td>
        <button class="approve" onclick="decide('${it.thread_id}', true)">Approve</button>
        <button class="reject"  onclick="decide('${it.thread_id}', false)">Reject</button>
      </td>
    </tr>
  `).join('');
  list.innerHTML = `
    <table>
      <thead><tr><th>Requester</th><th>Plate</th><th>Dates</th><th>Action</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

async function decide(threadId, approved) {
  let body = null;
  let url;
  if (approved) {
    url = `/reservations/${encodeURIComponent(threadId)}/approve`;
  } else {
    const reason = prompt('Rejection reason (optional):') || '';
    url = `/reservations/${encodeURIComponent(threadId)}/reject`;
    body = JSON.stringify({ approved: false, reason });
  }
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    });
    if (!res.ok) throw new Error(await res.text());
    showToast(approved ? 'Approved' : 'Rejected');
    refresh();
  } catch (e) {
    showToast('Error: ' + e.message);
  }
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""
