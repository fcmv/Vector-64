import type { BootProgress } from "../engine/connect";

export function BootScreen({ p, error }: { p?: BootProgress; error?: string }) {
  const pct = p && p.total > 0 ? Math.round((p.loaded / p.total) * 100) : 0;
  return (
    <div style={{ height: "100%", display: "grid", placeItems: "center", gap: 14 }}>
      <div style={{ width: 420, maxWidth: "80vw", textAlign: "center" }}>
        <div className="brand" style={{ fontSize: 13, marginBottom: 18 }}>
          STK<span>·</span>Vector-64 <span>/</span> Vector Scope
        </div>
        {error ? (
          <div role="alert">
            <h2>Unable to start the engine</h2>
            <p>{error}</p>
            <button onClick={() => location.reload()}>Reload</button>
          </div>
        ) : (
          <>
            <div className="evalbar" style={{ height: 6 }}>
              <div className="fill"
                style={{ left: 0, width: `${pct}%`, transition: "width .2s linear" }} />
            </div>
            <div className="num" style={{ marginTop: 10, fontSize: 11, color: "var(--fg-dim)" }}>
              {p?.phase === "net" ? "network" : "engine"} · {pct}%
            </div>
            {p?.note && (
              <div style={{ marginTop: 6, fontSize: 11, color: "var(--fg-faint)" }}>{p.note}</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
