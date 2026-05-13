import { Fragment } from "react";
import StatusDot from "../components/StatusDot";

export default function PduDetail({ device, status, onBack, onOutletAction, onDelete }) {
  if (!device) return null;
  const outlets = status?.outlets || [];
  const on = outlets.filter(o => o.state === "on").length;

  return (
    <main className="flex-1 px-6 py-5 max-w-[1600px] w-full mx-auto">
      <BackBar onBack={onBack} crumbs={["Dashboard", device.name]} />
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="lg:col-span-2 bg-zinc-900/70 border border-zinc-800 rounded-xl">
          <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
            <div>
              <div className="text-lg font-semibold">{device.name}</div>
              <div className="text-xs text-zinc-500">{device.model} · {device.ip}</div>
            </div>
            <a href={`https://${device.ip}/`} target="_blank" rel="noreferrer" className="text-xs text-zinc-400 hover:text-nv-400">
              Open native UI ↗
            </a>
          </div>
          <div className="p-4">
            <div className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Outlets</div>
            {outlets.length === 0 ? (
              <div className="text-zinc-600 text-sm text-center py-8">
                {status?.reachable === false ? `Cannot reach device: ${status.error}` : "Loading…"}
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {outlets.map(o => {
                  const hasName = !/^Outlet \d+$/.test(o.label);
                  const isOn = o.state === "on";
                  const hasWatts = o.watts > 0;
                  const borderCls = hasName
                    ? "border-nv-400/30 bg-nv-400/5"
                    : "border-rose-500/25 bg-rose-500/5";
                  return (
                    <div key={o.number} className={`flex items-center gap-3 p-2.5 rounded-lg border ${isOn ? borderCls : "border-zinc-800 bg-zinc-900/40"}`}>
                      <div className={`w-8 text-center font-mono text-xs shrink-0 ${hasName ? "text-nv-400/70" : "text-rose-500/60"}`}>{o.number}</div>
                      <div className="flex-1 min-w-0">
                        <div className={`truncate text-sm font-medium ${hasName ? "text-zinc-200" : "text-zinc-500"}`}>{o.label}</div>
                        <div className="text-[11px] tabular-nums mt-0.5">
                          {!isOn
                            ? <span className="text-zinc-600">{o.state}</span>
                            : hasWatts
                            ? <span className="text-zinc-400">{o.watts}W · {o.current}A</span>
                            : <span className="text-zinc-700">—</span>
                          }
                        </div>
                      </div>
                      <PowerButtons outlet={o} onAction={a => onOutletAction(o.number, a)} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>

        <aside className="space-y-4">
          <div className="bg-zinc-900/70 border border-zinc-800 rounded-xl p-4">
            <div className="text-xs uppercase tracking-wider text-zinc-500 mb-2">Summary</div>
            <Row label="Status">
              <StatusDot status={status?.reachable ? "online" : "offline"} />
              <span className="ml-1.5">{status?.reachable ? "Online" : status ? "Offline" : "Unknown"}</span>
            </Row>
            <Row label="Rack" v={device.rack} />
            <Row label="IP" v={device.ip} />
            <Row label="Inlet voltage" v={status ? `${status.inlet_voltage} V` : "—"} />
            <Row label="Active outlets" v={outlets.length ? `${on} / ${outlets.length}` : "—"} />
            <Row label="Total draw" v={status ? `${(status.total_watts/1000).toFixed(2)} kW` : "—"} />
          </div>
          <div className="bg-zinc-900/70 border border-zinc-800 rounded-xl p-4 space-y-1">
            <div className="text-xs uppercase tracking-wider text-zinc-500 mb-2">Quick actions</div>
            <button className="w-full text-left text-sm px-3 py-2 rounded hover:bg-zinc-800 text-zinc-200"
              onClick={() => { if (confirm("Turn ON all outlets?")) outlets.forEach(o => o.state !== "on" && onOutletAction(o.number, "on")); }}>
              ⏻ Turn on all outlets
            </button>
            <button className="w-full text-left text-sm px-3 py-2 rounded hover:bg-rose-500/15 text-rose-300"
              onClick={() => { if (confirm("Turn OFF all outlets on this PDU? This affects connected devices.")) outlets.forEach(o => o.state === "on" && onOutletAction(o.number, "off")); }}>
              ⏻ Turn off all outlets
            </button>
            <div className="border-t border-zinc-800 my-2" />
            <button onClick={onDelete} className="w-full text-left text-sm px-3 py-2 rounded hover:bg-rose-500/10 text-rose-400">
              Remove device
            </button>
          </div>
        </aside>
      </div>
    </main>
  );
}

function PowerButtons({ outlet, onAction }) {
  const on = outlet.state === "on";
  return (
    <div className="flex gap-1">
      {on ? (
        <>
          <button onClick={() => onAction("cycle")} title="Cycle" className="w-7 h-7 rounded border border-zinc-700 hover:border-nv-400/60 hover:bg-nv-400/10 text-zinc-300 text-sm">↻</button>
          <button onClick={() => { if (confirm(`Turn OFF outlet ${outlet.number}?`)) onAction("off"); }} title="Off" className="w-7 h-7 rounded border border-zinc-700 hover:border-rose-500/60 hover:bg-rose-500/10 text-zinc-300 text-sm">⏻</button>
        </>
      ) : (
        <button onClick={() => onAction("on")} className="px-2 h-7 rounded border border-zinc-700 hover:border-nv-400/60 hover:bg-nv-400/10 text-zinc-300 text-xs">on</button>
      )}
    </div>
  );
}

function Row({ label, v, children }) {
  return (
    <div className="flex items-center justify-between text-sm py-1.5 border-b border-zinc-800/50 last:border-0">
      <span className="text-zinc-500">{label}</span>
      <span className="text-zinc-200">{children ?? v}</span>
    </div>
  );
}

function BackBar({ onBack, crumbs }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <button onClick={onBack} className="text-zinc-400 hover:text-nv-400 flex items-center gap-1">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 18-6-6 6-6"/></svg>
        Back
      </button>
      <span className="text-zinc-600">/</span>
      {crumbs.map((c, i) => (
        <Fragment key={i}>
          <span className={i === crumbs.length - 1 ? "text-zinc-200" : "text-zinc-500"}>{c}</span>
          {i < crumbs.length - 1 && <span className="text-zinc-700">/</span>}
        </Fragment>
      ))}
    </div>
  );
}
