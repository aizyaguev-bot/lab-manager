import { useState, useEffect } from "react";
import { api } from "../api/client";
import StatusDot from "./StatusDot";

export default function KvmViewerModal({ device, portNumber, portLabel, onClose }) {
  const [viewerInfo, setViewerInfo] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);
  const isLx = device.model?.includes("LX");

  useEffect(() => {
    api.getViewerUrl(device.id, portNumber)
      .then(setViewerInfo)
      .catch(() => setViewerInfo({ can_embed: false, launch_url: `https://${device.ip}/` }));
  }, [device.id, portNumber]);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div onClick={e => e.stopPropagation()}
        className={`bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden flex flex-col ${fullscreen ? "w-full h-full" : "w-full max-w-5xl h-[80vh]"}`}>
        <div className="px-4 py-2.5 border-b border-zinc-800 flex items-center gap-3 bg-zinc-900/50">
          <StatusDot status="active" />
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm truncate">{device.name} · Port {portNumber} · {portLabel}</div>
            <div className="text-[11px] text-zinc-500 font-mono truncate">{viewerInfo?.launch_url || "Loading…"}</div>
          </div>
          <button onClick={() => setFullscreen(f => !f)} className="text-xs px-2 py-1 rounded hover:bg-zinc-800 text-zinc-400">
            {fullscreen ? "Restore" : "Fullscreen"}
          </button>
          {viewerInfo?.launch_url && (
            <a href={viewerInfo.launch_url} target="_blank" rel="noreferrer" className="text-xs px-2 py-1 rounded hover:bg-zinc-800 text-zinc-400">
              Open in new tab ↗
            </a>
          )}
          <button onClick={onClose} className="text-zinc-400 hover:text-zinc-100 w-7 h-7 rounded hover:bg-zinc-800">✕</button>
        </div>

        <div className="flex-1 relative bg-black">
          {!viewerInfo && (
            <div className="absolute inset-0 flex items-center justify-center text-zinc-500 text-sm">Fetching viewer URL…</div>
          )}
          {viewerInfo && viewerInfo.can_embed && (
            <iframe title="kvm-viewer" src={viewerInfo.embed_url} className="w-full h-full bg-black" sandbox="allow-same-origin allow-scripts allow-forms allow-popups" />
          )}
          {viewerInfo && !viewerInfo.can_embed && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8">
              <div className="text-amber-400 text-4xl mb-3">⚠</div>
              <div className="text-lg font-medium mb-1">{isLx ? "Dominion LX II" : "KVM"} cannot embed</div>
              <div className="text-zinc-400 text-sm mb-4 max-w-md">
                {isLx
                  ? "LX II uses a Java-era viewer that browsers no longer support inline. The native viewer will open in a new tab."
                  : "This unit does not support iframe embedding. Use the native viewer instead."}
              </div>
              <a href={viewerInfo.launch_url} target="_blank" rel="noreferrer"
                className="bg-nv-400 hover:bg-nv-300 text-zinc-950 font-medium text-sm px-4 py-2 rounded-lg">
                Launch native viewer ↗
              </a>
            </div>
          )}
        </div>

        <div className="px-4 py-2 border-t border-zinc-800 bg-zinc-900/50 text-[11px] text-zinc-500 flex justify-between">
          <span>{isLx ? "LX II: native viewer in new tab" : "KX III: live HTML5 iframe"}</span>
          <span>Esc / click outside to close</span>
        </div>
      </div>
    </div>
  );
}
