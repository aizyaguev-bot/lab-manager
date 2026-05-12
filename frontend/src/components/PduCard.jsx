import { useState } from "react";
import StatusDot from "./StatusDot";

export default function PduCard({ device, status, onOpen, onOutletAction }) {
  const outlets = status?.outlets || [];
  const on = outlets.filter(o => o.state === "on").length;
  const totalW = status?.total_watts || 0;
  const reachable = status ? status.reachable : null;
  const devStatus = reachable === false ? "offline" : reachable === true ? "online" : "unknown";

  return (
    <div className="bg-zinc-900/70 border border-zinc-800 hover:border-zinc-700 rounded-xl overflow-hidden transition">
      <div className="px-4 py-3 flex items-center gap-3 border-b border-zinc-800/80">
        <div className="w-9 h-9 rounded-md bg-zinc-800/70 border border-zinc-700 flex items-center justify-center text-zinc-300">
          <PduIcon />
        </div>
        <button onClick={onOpen} className="flex-1 text-left group">
          <div className="flex items-center gap-2">
            <span className="font-medium group-hover:text-nv-400 transition">{device.name}</span>
            <StatusDot status={devStatus} />
          </div>
          <div className="text-xs text-zinc-500 mt-0.5">{device.model} · {device.ip} · {device.rack}</div>
        </button>
        <button onClick={onOpen} className="text-xs text-zinc-400 hover:text-nv-400 px-2 py-1 rounded">Details →</button>
      </div>
      {status?.error && (
        <div className="px-4 py-2 bg-rose-500/10 border-b border-rose-500/30 text-rose-300 text-xs">⚠ {status.error}</div>
      )}
      <div className="p-4">
        {outlets.length > 0 ? (
          <div className="grid grid-cols-12 gap-1.5">
            {outlets.map(o => <OutletCell key={o.number} outlet={o} onAction={a => onOutletAction(o.number, a)} />)}
          </div>
        ) : (
          <div className="text-xs text-zinc-600 text-center py-4">
            {reachable === false ? "Cannot reach device" : "Loading outlets…"}
          </div>
        )}
      </div>
      <div className="px-4 py-2.5 border-t border-zinc-800/80 bg-zinc-950/40 text-xs text-zinc-400 flex justify-between">
        <span>{outlets.length > 0 ? `${on} of ${outlets.length} outlets active` : "—"}</span>
        <span className="tabular-nums text-zinc-200">{outlets.length > 0 ? `${(totalW/1000).toFixed(2)} kW` : "—"}</span>
      </div>
    </div>
  );
}

function OutletCell({ outlet, onAction }) {
  const [open, setOpen] = useState(false);
  const isOn = outlet.state === "on";
  const cls = isOn
    ? "bg-nv-400/15 border-nv-400/40 text-nv-300"
    : outlet.state === "unknown"
    ? "bg-zinc-800/50 border-zinc-700 text-zinc-600"
    : "bg-zinc-800/70 border-zinc-700 text-zinc-500";

  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)} title={`${outlet.label}\n${isOn ? `${outlet.watts}W` : outlet.state}`}
        className={`w-full aspect-square rounded border ${cls} hover:brightness-125 transition text-[10px] font-mono tabular-nums flex items-center justify-center`}>
        {outlet.number}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-20" onClick={() => setOpen(false)} />
          <div className="absolute z-30 top-full left-1/2 -translate-x-1/2 mt-1 w-52 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl p-2 text-sm">
            <div className="px-2 py-1.5 border-b border-zinc-800 mb-1">
              <div className="font-medium truncate">{outlet.label}</div>
              <div className="text-xs text-zinc-500">Outlet {outlet.number} · {isOn ? `${outlet.watts}W / ${outlet.current}A` : outlet.state}</div>
            </div>
            {isOn ? (
              <>
                <MI onClick={() => { onAction("cycle"); setOpen(false); }} icon="↻" label="Power cycle" />
                <MI onClick={() => { if (confirm(`Turn OFF ${outlet.label}?`)) { onAction("off"); setOpen(false); } }} icon="⏻" label="Turn off" danger />
              </>
            ) : (
              <MI onClick={() => { onAction("on"); setOpen(false); }} icon="⏻" label="Turn on" success />
            )}
          </div>
        </>
      )}
    </div>
  );
}

function MI({ onClick, icon, label, danger, success }) {
  const c = danger ? "hover:bg-rose-500/15 text-rose-300" : success ? "hover:bg-nv-400/15 text-nv-300" : "hover:bg-zinc-800 text-zinc-200";
  return (
    <button onClick={onClick} className={`w-full text-left px-2 py-1.5 rounded ${c} flex items-center gap-2`}>
      <span className="w-4 text-center">{icon}</span>{label}
    </button>
  );
}

function PduIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="8" width="18" height="8" rx="1.5"/>
      <circle cx="8" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="16" cy="12" r="1"/>
    </svg>
  );
}
