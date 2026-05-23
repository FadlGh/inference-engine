import { useState, useEffect, useRef, useCallback } from "react";

const WS_BASE = "ws://localhost:8000/ws";

const PHASE_META = {
  up:     { label: "Up",     color: "#1D9E75" },
  down:   { label: "Down",   color: "#EF9F27" },
  bottom: { label: "Bottom", color: "#E24B4A" },
};

function MetricCard({ label, value, unit = "", accent = false }) {
  return (
    <div style={{
      background: "var(--color-background-secondary)",
      borderRadius: "var(--border-radius-md)",
      padding: "12px 16px",
      display: "flex",
      flexDirection: "column",
      gap: 4,
      border: accent ? "1.5px solid var(--color-border-info)" : "0.5px solid var(--color-border-tertiary)",
    }}>
      <span style={{ fontSize: 12, color: "var(--color-text-secondary)", letterSpacing: "0.04em" }}>
        {label}
      </span>
      <span style={{ fontSize: 26, fontWeight: 500, color: "var(--color-text-primary)", lineHeight: 1 }}>
        {value ?? "—"}
        {value != null && unit && (
          <span style={{ fontSize: 14, fontWeight: 400, color: "var(--color-text-secondary)", marginLeft: 4 }}>
            {unit}
          </span>
        )}
      </span>
    </div>
  );
}

function PhasePill({ phase }) {
  const meta = PHASE_META[phase] ?? { label: phase, color: "#888" };
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "4px 12px",
      borderRadius: 999,
      background: meta.color + "22",
      border: `0.5px solid ${meta.color}66`,
      fontSize: 13,
      fontWeight: 500,
      color: meta.color,
    }}>
      <span style={{
        width: 7, height: 7, borderRadius: "50%",
        background: meta.color, flexShrink: 0,
      }} />
      {meta.label}
    </span>
  );
}

function FeedbackBanner({ msg }) {
  const isGood = msg === "Good rep!";
  if (!msg) return null;
  return (
    <div style={{
      padding: "10px 16px",
      borderRadius: "var(--border-radius-md)",
      background: isGood ? "var(--color-background-success)" : "var(--color-background-warning)",
      border: `0.5px solid ${isGood ? "var(--color-border-success)" : "var(--color-border-warning)"}`,
      color: isGood ? "var(--color-text-success)" : "var(--color-text-warning)",
      fontSize: 14,
      fontWeight: 500,
      display: "flex",
      alignItems: "center",
      gap: 8,
    }}>
      <i className={`ti ti-${isGood ? "circle-check" : "alert-triangle"}`} aria-hidden="true" />
      {msg}
    </div>
  );
}

function RepTable({ rows }) {
  if (!rows.length) return (
    <p style={{ fontSize: 13, color: "var(--color-text-secondary)", textAlign: "center", padding: "24px 0" }}>
      No reps yet
    </p>
  );
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, tableLayout: "fixed" }}>
        <thead>
          <tr style={{ borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
            {["Rep", "Time", "Min angle", "Tempo", "Notes"].map(h => (
              <th key={h} style={{
                padding: "6px 8px", textAlign: "left",
                color: "var(--color-text-secondary)", fontWeight: 500, fontSize: 12,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[...rows].reverse().map((r, i) => (
            <tr key={i} style={{ borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
              <td style={{ padding: "6px 8px", fontWeight: 500 }}>#{r.rep}</td>
              <td style={{ padding: "6px 8px", color: "var(--color-text-secondary)" }}>{r.time}</td>
              <td style={{ padding: "6px 8px" }}>{r.min_angle}°</td>
              <td style={{ padding: "6px 8px", color: "var(--color-text-secondary)" }}>
                {r.tempo != null ? `${r.tempo}s` : "—"}
              </td>
              <td style={{ padding: "6px 8px" }}>
                {r.issues.length === 0
                  ? <span style={{ color: "var(--color-text-success)", fontSize: 12 }}>✓ ok</span>
                  : <span style={{ color: "var(--color-text-warning)", fontSize: 12 }}>{r.issues[0]}</span>
                }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IssueList({ items, label }) {
  if (!items?.length) return null;
  return (
    <div>
      <p style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6, fontWeight: 500 }}>
        {label}
      </p>
      {items.map((it, i) => (
        <div key={i} style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "6px 10px", marginBottom: 4,
          background: "var(--color-background-warning)",
          borderRadius: "var(--border-radius-md)",
          border: "0.5px solid var(--color-border-warning)",
          fontSize: 13,
        }}>
          <span style={{ color: "var(--color-text-warning)" }}>{it.msg ?? it}</span>
          {it.count != null && (
            <span style={{
              fontSize: 11, fontWeight: 500, background: "#EF9F2733",
              color: "var(--color-text-warning)", padding: "2px 8px", borderRadius: 999,
            }}>{it.count}×</span>
          )}
        </div>
      ))}
    </div>
  );
}

export default function GymDashboard() {
  const [exercise, setExercise]       = useState("pushup");
  const [running, setRunning]         = useState(false);
  const [data, setData]               = useState(null);
  const [error, setError]             = useState(null);

  const wsRef     = useRef(null);
  const imgRef    = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close();
    setError(null);
    setData(null);

    const ws = new WebSocket(`${WS_BASE}/${exercise}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const payload = JSON.parse(e.data);
      if (payload.error) { setError(payload.error); setRunning(false); return; }
      if (imgRef.current) {
        imgRef.current.src = "data:image/jpeg;base64," + payload.frame;
      }
      setData(payload);
    };

    ws.onerror = () => { setError("WebSocket error — is the server running?"); setRunning(false); };
    ws.onclose = ()  => setRunning(false);

    setRunning(true);
  }, [exercise]);

  const disconnect = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ cmd: "stop" }));
    wsRef.current?.close();
    setRunning(false);
  }, []);

  useEffect(() => () => wsRef.current?.close(), []);

  const d = data ?? {};

  return (
    <div style={{ fontFamily: "var(--font-sans)", padding: "1.5rem 1rem", maxWidth: 720, margin: "0 auto" }}>
      <h2 style={{ hidden: true }} className="sr-only">Gym assistant dashboard</h2>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 500 }}>
            <i className="ti ti-barbell" aria-hidden="true" style={{ marginRight: 8, fontSize: 18 }} />
            Gym assistant
          </h2>
          <p style={{ margin: 0, fontSize: 13, color: "var(--color-text-secondary)" }}>
            Real-time form analysis
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select
            value={exercise}
            disabled={running}
            onChange={e => setExercise(e.target.value)}
            style={{ fontSize: 13 }}
          >
            <option value="pushup">Push-up</option>
            <option value="squat">Squat</option>
          </select>

          {!running ? (
            <button onClick={connect} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <i className="ti ti-player-play" aria-hidden="true" />
              Start
            </button>
          ) : (
            <button onClick={disconnect} style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--color-text-danger)", borderColor: "var(--color-border-danger)" }}>
              <i className="ti ti-player-stop" aria-hidden="true" />
              Stop
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          padding: "10px 14px", marginBottom: "1rem",
          background: "var(--color-background-danger)",
          border: "0.5px solid var(--color-border-danger)",
          borderRadius: "var(--border-radius-md)",
          color: "var(--color-text-danger)", fontSize: 13,
        }}>
          <i className="ti ti-alert-circle" aria-hidden="true" style={{ marginRight: 6 }} />
          {error}
        </div>
      )}

      {/* Camera feed */}
      <div style={{
        width: "100%", aspectRatio: "16/9",
        background: "var(--color-background-secondary)",
        border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: "var(--border-radius-lg)",
        overflow: "hidden", marginBottom: "1rem",
        display: "flex", alignItems: "center", justifyContent: "center",
        position: "relative",
      }}>
        <img ref={imgRef} alt="pose feed"
          style={{ width: "100%", height: "100%", objectFit: "cover",
            display: running ? "block" : "none" }}
        />
        {!running && (
          <div style={{ textAlign: "center", color: "var(--color-text-secondary)" }}>
            <i className="ti ti-camera-off" style={{ fontSize: 32, display: "block", marginBottom: 8 }} aria-hidden="true" />
            <span style={{ fontSize: 13 }}>Camera off — press Start</span>
          </div>
        )}

        {/* Overlay: phase pill */}
        {running && d.phase && (
          <div style={{ position: "absolute", top: 10, left: 10 }}>
            <PhasePill phase={d.phase} />
          </div>
        )}

        {/* Overlay: angle badge */}
        {running && d.angle != null && (
          <div style={{
            position: "absolute", top: 10, right: 10,
            background: "#00000066", borderRadius: "var(--border-radius-md)",
            padding: "4px 10px", color: "#fff", fontSize: 13, fontWeight: 500,
          }}>
            {d.angle}°
          </div>
        )}
      </div>

      {/* Feedback */}
      <div style={{ marginBottom: "1rem" }}>
        <FeedbackBanner msg={d.feedback} />
      </div>

      {/* Metric cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 10, marginBottom: "1.25rem" }}>
        <MetricCard label="Reps" value={d.reps ?? 0} accent />
        <MetricCard label="Last tempo" value={d.tempo} unit="s" />
        <MetricCard label="Avg tempo" value={d.avg_tempo} unit="s" />
        <MetricCard label="Exercise" value={d.exercise ?? (exercise === "pushup" ? "Push-up" : "Squat")} />
      </div>

      {/* Issues */}
      {(d.top_issues?.length > 0 || d.session_issues?.length > 0) && (
        <div style={{
          background: "var(--color-background-primary)",
          border: "0.5px solid var(--color-border-tertiary)",
          borderRadius: "var(--border-radius-lg)",
          padding: "1rem 1.25rem",
          marginBottom: "1.25rem",
        }}>
          <IssueList items={d.top_issues} label="Top form issues this session" />
          {d.top_issues?.length > 0 && d.session_issues?.length > 0 && (
            <div style={{ margin: "12px 0", borderTop: "0.5px solid var(--color-border-tertiary)" }} />
          )}
          <IssueList
            items={d.session_issues?.map(msg => ({ msg }))}
            label="Session-level observations"
          />
        </div>
      )}

      {/* Per-rep log */}
      <div style={{
        background: "var(--color-background-primary)",
        border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: "var(--border-radius-lg)",
        padding: "1rem 1.25rem",
      }}>
        <p style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 500, color: "var(--color-text-secondary)" }}>
          <i className="ti ti-list" aria-hidden="true" style={{ marginRight: 6 }} />
          Rep log
        </p>
        <RepTable rows={d.per_rep_log ?? []} />
      </div>

      {/* Server instructions (shown when not running) */}
      {!running && (
        <div style={{
          marginTop: "1.25rem",
          padding: "12px 16px",
          background: "var(--color-background-secondary)",
          border: "0.5px solid var(--color-border-tertiary)",
          borderRadius: "var(--border-radius-md)",
          fontSize: 12,
          color: "var(--color-text-secondary)",
          fontFamily: "var(--font-mono)",
        }}>
          Start server: <strong style={{ color: "var(--color-text-primary)" }}>uvicorn server:app --reload</strong>
          <br />
          Install deps: <strong style={{ color: "var(--color-text-primary)" }}>pip install fastapi uvicorn opencv-python mediapipe</strong>
        </div>
      )}
    </div>
  );
}