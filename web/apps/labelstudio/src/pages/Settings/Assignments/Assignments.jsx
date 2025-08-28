import { useEffect, useMemo, useState } from "react";
import { Button } from "@humansignal/ui";
import { Spinner } from "../../../components";
import { useProject } from "../../../providers/ProjectProvider";
import { useCurrentUser } from "../../../providers/CurrentUser";
import { Block, Elem } from "../../../utils/bem";
import "./Assignments.scss";

export const Assignments = () => {
  const { project } = useProject();
  const { user } = useCurrentUser();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("expires");
  const [view, setView] = useState("table");

  const canView = ["OWNER", "MAINTAINER"].includes((user?.org_role || "").toUpperCase());

  const load = async () => {
    if (!project?.id) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`/api/ee/projects/${project.id}/assignments/active`);
      if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`);
      const data = await resp.json();
      setItems(data.assignments || []);
    } catch (e) {
      console.error("Failed to load assignments", e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canView) load();
  }, [project?.id, canView]);

  const filteredItems = useMemo(() => {
    const searchLower = search.toLowerCase();
    const filtered = items.filter(item => {
      const assignee = item.assignee?.username || item.assignee?.email || "";
      const assignedBy = item.assigned_by?.username || item.assigned_by?.email || "";
      return assignee.toLowerCase().includes(searchLower) || 
             assignedBy.toLowerCase().includes(searchLower);
    });

    return [...filtered].sort((a, b) => {
      if (sortBy === "expires") return new Date(a.expire_at) - new Date(b.expire_at);
      if (sortBy === "assignee") return (a.assignee?.username || "").localeCompare(b.assignee?.username || "");
      return 0;
    });
  }, [items, search, sortBy]);

  if (!canView) return null;

  const Count = (
    <Elem name="count">
      {filteredItems.length}
      <span className="muted"> of {items.length}</span>
    </Elem>
  );

  return (
    <Block name="assignments">
      <Elem name="header">
        <div className="assignments__header-left">
          <Elem name="title">Active Assignments</Elem>
          {Count}
        </div>
        <div className="assignments__header-right assignments__actions">
          <input
            className="assignments__input"
            placeholder="Filter by assignee or assigned by…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="assignments__select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="expires">Expires soonest</option>
            <option value="assignee">Assignee</option>
            <option value="task">Task #</option>
          </select>
          <div className="assignments__view">
            <Button size="small" type={view === "table" ? "primary" : "text"} onClick={() => setView("table")}>
              Table
            </Button>
            <Button size="small" type={view === "cards" ? "primary" : "text"} onClick={() => setView("cards")}>
              Cards
            </Button>
          </div>
          <Button size="small" type="text" onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </Button>
        </div>
      </Elem>

      {loading ? (
        <Elem name="loader"><Spinner size={24} /></Elem>
      ) : error ? (
        <Elem name="error">
          <Elem name="error-title">Failed to load assignments</Elem>
          <Elem name="error-text">{error}</Elem>
          <Button size="small" onClick={load}>Retry</Button>
        </Elem>
      ) : items.length === 0 ? (
        <Elem name="empty">
          <Elem name="empty-title">No active assignments</Elem>
          <Elem name="empty-text">Assignments created here will appear with assignee, owner and expiry info.</Elem>
        </Elem>
      ) : (
        <>
          {view === "table" ? (
            <Elem name="table-wrap">
              <table className="assignments__table">
                <colgroup>
                  <col style={{ width: '26%' }} />
                  <col style={{ width: '26%' }} />
                  <col style={{ width: '26%' }} />
                  <col style={{ width: '22%' }} />
                </colgroup>
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Assignee</th>
                    <th>Assigned by</th>
                    <th>Expires</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((row) => {
                    const taskNum = row.task_inner_id ?? row.task_id;
                    const eta = new Date(row.expire_at);
                    const mins = Math.max(0, Math.round((eta - Date.now()) / 60000));
                    return (
                      <tr key={`${row.task_id}:${row.assignee?.id}`}>
                        <td>
                          <div className="taskcell">
                            <div className="mono">Task #{taskNum}</div>
                            <div className="muted mono">ID {row.task_id}</div>
                          </div>
                        </td>
                        <td>
                          <div className="user">
                            <span className="user__name">{row.assignee?.username || ""}</span>
                            {row.assignee?.email && (
                              <span className="user__email" title={row.assignee.email}>{row.assignee.email}</span>
                            )}
                            {row.assignee?.id && <span className="user__meta">ID {row.assignee.id}</span>}
                          </div>
                        </td>
                        <td>
                          {row.assigned_by ? (
                            <div className="user">
                              <span className="user__name">{row.assigned_by?.username || ""}</span>
                              {row.assigned_by?.email && (
                                <span className="user__email" title={row.assigned_by.email}>{row.assigned_by.email}</span>
                              )}
                              {row.assigned_by?.id && <span className="user__meta">ID {row.assigned_by.id}</span>}
                            </div>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div className="expires">
                            <span>{eta.toLocaleString()}</span>
                            <span className={`expires__left ${mins <= 5 ? "danger" : ""}`}>
                              {mins} min left
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Elem>
          ) : (
            <Elem name="cards">
              {filteredItems.map((row) => {
                const taskNum = row.task_inner_id ?? row.task_id;
                const eta = new Date(row.expire_at);
                const mins = Math.max(0, Math.round((eta - Date.now()) / 60000));
                return (
                  <div className="assignments__card" key={`${row.task_id}:${row.assignee?.id}`}>
                    <div className="assignments__card-head">
                      <div className="assignments__badge">Task #{taskNum}</div>
                      <div className={`assignments__etag ${mins <= 5 ? 'danger' : ''}`}>{mins} min left</div>
                    </div>
                    <div className="assignments__card-body">
                      <div className="assignments__row">
                        <div className="label">Task ID</div>
                        <div className="value mono">{row.task_id}</div>
                      </div>
                      <div className="assignments__row">
                        <div className="label">Assignee</div>
                        <div className="value">
                          <div className="user">
                            <span className="user__name">{row.assignee?.username || ""}</span>
                            {row.assignee?.email && <span className="user__email">{row.assignee.email}</span>}
                            {row.assignee?.id && <span className="pill">ID {row.assignee.id}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="assignments__row">
                        <div className="label">Assigned By</div>
                        <div className="value">
                          {row.assigned_by ? (
                            <div className="user">
                              <span className="user__name">{row.assigned_by?.username || ""}</span>
                              {row.assigned_by?.email && <span className="user__email">{row.assigned_by.email}</span>}
                              {row.assigned_by?.id && <span className="pill pill--weak">ID {row.assigned_by.id}</span>}
                            </div>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </div>
                      </div>
                      <div className="assignments__row">
                        <div className="label">Expires</div>
                        <div className="value">
                          {eta.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </Elem>
          )}
        </>
      )}
    </Block>
  );
};

Assignments.title = "Assignments";
Assignments.path = "/assignments";
Assignments.exact = true;
