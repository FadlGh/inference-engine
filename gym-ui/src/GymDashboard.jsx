import { useState, useEffect, useRef, useCallback } from "react";

const WS_BASE = "ws://localhost:8000/ws";

const PHASE_META = {
  up: { label: "Up", color: "#22c55e" },
  down: { label: "Down", color: "#f59e0b" },
  bottom: { label: "Bottom", color: "#ef4444" },
};

function Header({ running, connect, disconnect, exercise, setExercise }) {
  return (
    <div style={styles.header}>
      <div>
        <h1 style={styles.title}>MotionAI</h1>
        <p style={styles.subtitle}>Real-time movement analysis</p>
      </div>

      <div style={styles.headerControls}>
        <select
          value={exercise}
          disabled={running}
          onChange={(e) => setExercise(e.target.value)}
          style={styles.select}
        >
          <option value="pushup">Push-up</option>
          <option value="squat">Squat</option>
        </select>

        {!running ? (
          <button onClick={connect} style={styles.startBtn}>
            Start
          </button>
        ) : (
          <button onClick={disconnect} style={styles.stopBtn}>
            Stop
          </button>
        )}
      </div>
    </div>
  );
}

function CameraFeed({ running, imgRef, phase, angle }) {
  return (
    <div style={styles.cameraWrapper}>
      <img
        ref={imgRef}
        alt="pose feed"
        style={{
          ...styles.camera,
          display: running ? "block" : "none",
        }}
      />

      {!running && (
        <div style={styles.cameraPlaceholder}>
          <div style={{ fontSize: 48 }}>📷</div>
          <p>Session inactive</p>
        </div>
      )}

      {running && (
        <div style={styles.liveBadge}>
          <div style={styles.liveDot} />
          LIVE
        </div>
      )}

      {phase && (
        <div
          style={{
            ...styles.phaseBadge,
            borderColor: PHASE_META[phase]?.color,
            color: PHASE_META[phase]?.color,
          }}
        >
          {PHASE_META[phase]?.label}
        </div>
      )}

      {angle != null && <div style={styles.angleBadge}>{angle}°</div>}
    </div>
  );
}

function Metrics({ data, exercise }) {
  return (
    <div style={styles.metricsGrid}>
      <MetricCard label="REPS" value={data.reps ?? 0} accent />

      <MetricCard label="LAST TEMPO" value={data.tempo ?? "—"} unit="s" />

      <MetricCard label="AVG TEMPO" value={data.avg_tempo ?? "—"} unit="s" />

      <MetricCard
        label="EXERCISE"
        value={exercise === "pushup" ? "Push-up" : "Squat"}
      />
    </div>
  );
}

function MetricCard({ label, value, unit, accent }) {
  return (
    <div
      style={{
        ...styles.metricCard,
        border: accent
          ? "1px solid rgba(34,197,94,0.3)"
          : "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <div style={styles.metricLabel}>{label}</div>

      <div style={styles.metricValue}>
        {value}

        {unit && <span style={styles.metricUnit}>{unit}</span>}
      </div>
    </div>
  );
}

function Feedback({ message }) {
  if (!message) return null;

  const good = message === "Good rep!";

  return (
    <div
      style={{
        ...styles.feedback,
        background: good ? "rgba(34,197,94,0.12)" : "rgba(245,158,11,0.12)",
        border: good
          ? "1px solid rgba(34,197,94,0.25)"
          : "1px solid rgba(245,158,11,0.25)",
        color: good ? "#22c55e" : "#f59e0b",
      }}
    >
      {message}
    </div>
  );
}

function RepList({ rows }) {
  const safeRows = Array.isArray(rows) ? rows : [];

  if (safeRows.length === 0) {
    return <div style={styles.empty}>No reps recorded yet</div>;
  }

  return (
    <div style={styles.repList}>
      {safeRows
        .slice()
        .reverse()
        .map((r, i) => {
          const issues = Array.isArray(r?.issues) ? r.issues : [];

          return (
            <div key={i} style={styles.repCard}>
              <div style={styles.repTop}>
                <strong>Rep #{r?.rep ?? "-"}</strong>

                <span style={styles.repTime}>{r?.time ?? "--:--"}</span>
              </div>

              <div style={styles.repBadges}>
                <div style={styles.repBadge}>{r?.min_angle ?? "—"}°</div>

                <div style={styles.repBadge}>{r?.tempo ?? "—"}s</div>

                <div
                  style={{
                    ...styles.repBadge,
                    background:
                      issues.length === 0
                        ? "rgba(34,197,94,0.12)"
                        : "rgba(245,158,11,0.12)",
                    color: issues.length === 0 ? "#22c55e" : "#f59e0b",
                  }}
                >
                  {issues.length === 0 ? "Good form" : issues[0]}
                </div>
              </div>
            </div>
          );
        })}
    </div>
  );
}

export default function GymDashboard() {
  const [exercise, setExercise] = useState("pushup");

  const [running, setRunning] = useState(false);

  const [data, setData] = useState({});

  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const imgRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    setError(null);

    const ws = new WebSocket(`${WS_BASE}/${exercise}`);

    wsRef.current = ws;

    ws.onmessage = (e) => {
      const payload = JSON.parse(e.data);

      console.log(payload);

      if (payload.error) {
        setError(payload.error);
        setRunning(false);
        return;
      }

      if (imgRef.current && payload.frame) {
        imgRef.current.src = "data:image/jpeg;base64," + payload.frame;
      }

      setData((prev) => ({
        ...prev,
        ...payload,
      }));
    };

    ws.onerror = () => {
      setError("WebSocket error");
      setRunning(false);
    };

    ws.onclose = () => {
      setRunning(false);
    };

    setRunning(true);
  }, [exercise]);

  const disconnect = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ cmd: "stop" }));

    wsRef.current?.close();

    setRunning(false);
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <Header
          running={running}
          connect={connect}
          disconnect={disconnect}
          exercise={exercise}
          setExercise={setExercise}
        />

        {error && <div style={styles.error}>{error}</div>}

        <CameraFeed
          running={running}
          imgRef={imgRef}
          phase={data.phase}
          angle={data.angle}
        />

        <Metrics data={data} exercise={exercise} />

        <Feedback message={data.feedback} />

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Rep History</h2>

          <RepList rows={data.per_rep_log} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(to bottom, #0f172a, #020617)",
    color: "white",
    fontFamily: "Inter, system-ui, sans-serif",
    padding: 24,
  },

  container: {
    maxWidth: 1200,
    margin: "0 auto",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
    flexWrap: "wrap",
    gap: 16,
  },

  title: {
    margin: 0,
    fontSize: 32,
  },

  subtitle: {
    marginTop: 6,
    color: "rgba(255,255,255,0.55)",
  },

  headerControls: {
    display: "flex",
    gap: 12,
  },

  select: {
    background: "#111827",
    color: "white",
    border: "1px solid rgba(255,255,255,0.1)",
    padding: "10px 14px",
    borderRadius: 12,
    fontSize: 14,
  },

  startBtn: {
    background: "#22c55e",
    color: "white",
    border: "none",
    padding: "10px 18px",
    borderRadius: 12,
    cursor: "pointer",
    fontWeight: 600,
  },

  stopBtn: {
    background: "#ef4444",
    color: "white",
    border: "none",
    padding: "10px 18px",
    borderRadius: 12,
    cursor: "pointer",
    fontWeight: 600,
  },

  cameraWrapper: {
    position: "relative",
    width: "100%",
    aspectRatio: "16/9",
    background: "#111827",
    borderRadius: 24,
    overflow: "hidden",
    marginBottom: 24,
    border: "1px solid rgba(255,255,255,0.08)",
  },

  camera: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
  },

  cameraPlaceholder: {
    position: "absolute",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "column",
    color: "rgba(255,255,255,0.5)",
  },

  liveBadge: {
    position: "absolute",
    top: 16,
    left: 16,
    background: "rgba(0,0,0,0.6)",
    padding: "8px 14px",
    borderRadius: 999,
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 14,
    fontWeight: 600,
  },

  liveDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: "#22c55e",
  },

  phaseBadge: {
    position: "absolute",
    top: 16,
    left: 110,
    background: "rgba(0,0,0,0.6)",
    padding: "8px 14px",
    borderRadius: 999,
    border: "1px solid",
    fontWeight: 600,
  },

  angleBadge: {
    position: "absolute",
    top: 16,
    right: 16,
    background: "rgba(0,0,0,0.6)",
    padding: "10px 16px",
    borderRadius: 16,
    fontSize: 18,
    fontWeight: 700,
  },

  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 16,
    marginBottom: 20,
  },

  metricCard: {
    background: "rgba(255,255,255,0.04)",
    borderRadius: 20,
    padding: 20,
  },

  metricLabel: {
    color: "rgba(255,255,255,0.5)",
    fontSize: 12,
    marginBottom: 10,
  },

  metricValue: {
    fontSize: 36,
    fontWeight: 700,
  },

  metricUnit: {
    fontSize: 16,
    marginLeft: 4,
    color: "rgba(255,255,255,0.5)",
  },

  feedback: {
    padding: 16,
    borderRadius: 16,
    marginBottom: 24,
    fontWeight: 600,
  },

  section: {
    marginTop: 30,
  },

  sectionTitle: {
    marginBottom: 16,
  },

  repList: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },

  repCard: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 18,
    padding: 18,
  },

  repTop: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: 12,
  },

  repTime: {
    color: "rgba(255,255,255,0.5)",
    fontSize: 13,
  },

  repBadges: {
    display: "flex",
    gap: 10,
    flexWrap: "wrap",
  },

  repBadge: {
    background: "rgba(255,255,255,0.06)",
    padding: "6px 12px",
    borderRadius: 999,
    fontSize: 13,
  },

  empty: {
    background: "rgba(255,255,255,0.04)",
    borderRadius: 18,
    padding: 24,
    color: "rgba(255,255,255,0.5)",
  },

  error: {
    background: "rgba(239,68,68,0.12)",
    border: "1px solid rgba(239,68,68,0.2)",
    color: "#ef4444",
    padding: 16,
    borderRadius: 16,
    marginBottom: 20,
  },
};
