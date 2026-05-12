import StatusDot from "./StatusDot";

export default function KvmCard({ device, status, onOpen, onPortClick }) {
  const ports = status?.ports || [];
  const active = ports.filter(p => p.status === "active").length;
  const isLx = device.model?.includes("LX");
  const devStatus = status ? (status.reachable ? "online" : "offline") : "unknown";

  return (
    <div className="bg-zinc-900/70 border border-zinc-800 hover:border-zinc-700 rounded-xl overflow-hidden transition">
      <div className="px-4 py-3 flex items-center gap-3 border-b border-zinc-800/80">
        <div className="w-9 h-9 rounded-md bg-zinc-800/70 border border-zinc-700 flex items-center justify-center text-zinc-300">
          <KvmIcon />
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
      {isLx && (
        <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/30 text-amber-300 text-xs">
          LX II — viewer opens in new tab
        </div>
      )}
      <div className="p-4">
        {ports.length > 0 ? (
          <div className="grid grid-cols-4 gap-1.5">
            {ports.map(p => <PortThumb key={p.number} port={p} onClick={() => p.status !== "empty" && onPortClick(p)} />)}
          </div>
        ) : (
          <div className="text-xs text-zinc-600 text-center py-4">
            {status?.reachable === false ? "Cannot reach device" : "Loading ports…"}
          </div>
        )}
      </div>
      <div className="px-4 py-2.5 border-t border-zinc-800/80 bg-zinc-950/40 text-xs text-zinc-400 flex justify-between">
        <span>{ports.length > 0 ? `${active} of ${ports.length} ports active` : "—"}</span>
        <span className="text-zinc-200">{device.model?.includes("LX") ? "LX II" : "KX III"}</span>
      </div>
    </div>
  );
}

function PortThumb({ port, onClick }) {
  const active = port.status === "active";
  return (
    <button onClick={onClick} disabled={!active}
      className={`group relative rounded border ${active ? "border-zinc-700 hover:border-nv-400/60 cursor-pointer" : "border-zinc-800 cursor-not-allowed"} overflow-hidden bg-black aspect-[4/3]`}
      title={port.label}>
      <div className={`screen linux-term absolute inset-0 flex flex-col p-1.5 pb-4 text-[7px] leading-[10px] ${!active ? "opacity-20" : ""}`}>
        {active ? (
          <>
            <div className="truncate">{port.label}</div>
            <div className="truncate text-zinc-500">port {port.number}</div>
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-zinc-700 text-[9px]">empty</div>
        )}
      </div>
      <div className="absolute inset-x-0 bottom-0 px-1.5 py-1 bg-gradient-to-t from-black/90 to-transparent">
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono text-zinc-400">P{port.number}</span>
          {active && <span className="text-[10px] text-zinc-200 truncate flex-1">{port.label}</span>}
        </div>
      </div>
      {active && <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />}
    </button>
  );
}

function KvmIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2.5" y="4" width="19" height="13" rx="1.5"/>
      <path d="M8 21h8M12 17v4"/>
    </svg>
  );
}
