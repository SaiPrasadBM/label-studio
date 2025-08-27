import { useEffect, useState, useContext } from "react";
// Minimal dependencies: avoid UI kit until route works reliably
import { useProject } from "../../../providers/ProjectProvider";
import { useCurrentUser } from "../../../providers/CurrentUser";

export const Assignments = () => {
  const { project } = useProject();
  const { user } = useCurrentUser();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);

  const canView = ["OWNER", "MAINTAINER"].includes((user?.org_role || "").toUpperCase());

  const load = async () => {
    if (!project?.id) return;
    setLoading(true);
    try {
      const resp = await fetch(`/api/ee/projects/${project.id}/assignments/active`);
      if (!resp.ok) throw new Error(`Failed to load assignments (${resp.status})`);
      const data = await resp.json();
      setItems(data.assignments || []);
    } catch (e) {
      // swallow error for now to prevent UI lib dependency
      // console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canView) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project?.id, canView]);

  if (!canView) return null;

  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Active Assignments</h2>
      <div style={{ marginBottom: 12 }}>
        <button onClick={load} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>
      {items.length === 0 ? (
        <div>No active assignments</div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="ls-table">
            <thead>
              <tr>
                <th>Task #</th>
                <th>Task ID</th>
                <th>Assignee</th>
                <th>Assignee ID</th>
                <th>Assigned By</th>
                <th>Assigned By ID</th>
                <th>Expires</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={`${row.task_id}:${row.assignee?.id}`}>
                  <td>{row.task_inner_id ?? row.task_id}</td>
                  <td>{row.task_id}</td>
                  <td>{`${row.assignee?.username || ""} (${row.assignee?.email || ""})`}</td>
                  <td>{row.assignee?.id}</td>
                  <td>{row.assigned_by ? `${row.assigned_by?.username || ""} (${row.assigned_by?.email || ""})` : '-'}</td>
                  <td>{row.assigned_by?.id ?? '-'}</td>
                  <td>{new Date(row.expire_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

Assignments.title = "Assignments";
Assignments.path = "/assignments";
Assignments.exact = true;
