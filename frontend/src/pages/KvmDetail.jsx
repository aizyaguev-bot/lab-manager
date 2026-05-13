import { Fragment } from "react";
import StatusDot from "../components/StatusDot";

export default function KvmDetail({ device, status, onBack, onPortClick, onDelete }) {
  if (!device) return null;
  const ports = status?.ports || [];
  const active = ports.filter(p => p.status === "active").length;
  const isLx = device.model?.includes("LX");

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
          {isLx && (
            <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/30 text-amber-300 text-xs">
              LX II unit — clicking a port opens the native viewer in a new tab
            </div>
          )}
          <div className="p-4">
            <div className="text-xs uppercase tracking-wider text-zinc-500 mb-3">Ports</div>
            {ports.length === 0 ? (
              <div className="text-zinc-600 text-sm text-center py-8">
                {status?.reachable === false ? `Cannot reach device: ${status.error}` : "Loading…"}
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {ports.map(p => (
                  <div key={p.number} className="space-y-1">
                    <button onClick={() => onPortClick(p)}
                      className={`w-full relative rounded border ${p.status !== "empty" ? "border-zinc-700 hover:border-nv-400/60" : "border-zinc-800"} cursor-pointer overflow-hidden bg-black aspect-[4/3]`}>
                      <div className="screen linux-term absolute inset-0 flex flex-col p-3 pb-7 text-xs leading-4">
                        {p.label ? (
                          <>
                            <div className={`truncate ${p.status !== "empty" ? "" : "text-zinc-600"}`}>{p.label}</div>
                            <div className="text-zinc-600">port {p.number}</div>
                          </>
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center text-zinc-700 text-xs">empty</div>
                        )}
                      </div>
                      <div className="absolute inset-x-0 bottom-0 px-2 py-1.5 bg-gradient-to-t from-black/90 to-transparent">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-zinc-500 text-xs">P{p.number}</span>
                          <StatusDot status={p.status} />
                          <span className="truncate flex-1 text-zinc-200 text-xs">{p.label}</span>
                        </div>
                      </div>
                      {p.status === "active" && <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />}
                    </button>
                  </div>
                ))}
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
            <Row label="Model" v={device.model} />
            <Row label="Ports" v={ports.length ? `${active} / ${ports.length} active` : `${device.port_count || "—"} configured`} />
          </div>
          {device.notes && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-xs text-amber-200">ⓘ {device.notes}</div>
          )}
          <div className="bg-zinc-900/70 border border-zinc-800 rounded-xl p-4">
            <button onClick={onDelete} className="w-full text-left text-sm px-3 py-2 rounded hover:bg-rose-500/10 text-rose-400">
              Remove device
            </button>
          </div>
        </aside>
      </div>
    </main>
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
