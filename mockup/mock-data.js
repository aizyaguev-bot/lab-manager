// Mock data for the Lab Manager UI. Edit freely — the app reads window.MOCK_DATA on load.
// Replace these with your real device list once the backend is wired up.

window.MOCK_DATA = {
  racks: ["Rack-A1", "Rack-A2", "Rack-B1", "Rack-B2", "Rack-C1"],

  pdus: [
    {
      id: "pdu-a1-01",
      name: "PDU-Rack-A1-Top",
      model: "Raritan PX4-5874",
      ip: "10.10.20.11",
      rack: "Rack-A1",
      status: "online",
      firmware: "4.2.10.5-49152",
      inletVoltage: 208,
      outlets: makeOutlets(24, "a1-top", [
        ["GPU-Node-01", "on", 412],
        ["GPU-Node-02", "on", 398],
        ["GPU-Node-03", "on", 405],
        ["GPU-Node-04", "off", 0],
        ["Switch-Mellanox-A", "on", 78],
        ["Switch-Mellanox-B", "on", 81],
        ["Storage-NVMe-Shelf", "on", 240],
        ["Test-Bench-Dev", "off", 0],
      ]),
    },
    {
      id: "pdu-a1-02",
      name: "PDU-Rack-A1-Bot",
      model: "Raritan PX4-5874",
      ip: "10.10.20.12",
      rack: "Rack-A1",
      status: "online",
      firmware: "4.2.10.5-49152",
      inletVoltage: 208,
      outlets: makeOutlets(24, "a1-bot", [
        ["GPU-Node-05", "on", 418],
        ["GPU-Node-06", "on", 401],
        ["GPU-Node-07", "on", 422],
        ["GPU-Node-08", "on", 395],
        ["KVM-A1", "on", 22],
        ["Mgmt-Switch-A1", "on", 18],
      ]),
    },
    {
      id: "pdu-a2-01",
      name: "PDU-Rack-A2-Top",
      model: "Raritan PX4-5848",
      ip: "10.10.20.21",
      rack: "Rack-A2",
      status: "online",
      firmware: "4.2.10.5-49152",
      inletVoltage: 208,
      outlets: makeOutlets(24, "a2-top", [
        ["DGX-H100-01", "on", 1024],
        ["DGX-H100-02", "on", 998],
        ["Switch-Spectrum-X", "on", 145],
        ["Cooling-Pump-A", "on", 64],
      ]),
    },
    {
      id: "pdu-b1-01",
      name: "PDU-Rack-B1",
      model: "Raritan PX4-5874",
      ip: "10.10.20.31",
      rack: "Rack-B1",
      status: "online",
      firmware: "4.2.10.5-49152",
      inletVoltage: 208,
      outlets: makeOutlets(24, "b1", [
        ["GH200-Eval-01", "on", 612],
        ["GH200-Eval-02", "on", 605],
        ["Bench-Power-1", "off", 0],
        ["Bench-Power-2", "off", 0],
      ]),
    },
    {
      id: "pdu-c1-01",
      name: "PDU-Rack-C1",
      model: "Raritan PX4-5848",
      ip: "10.10.20.51",
      rack: "Rack-C1",
      status: "warning",
      firmware: "4.2.10.5-49152",
      inletVoltage: 208,
      alerts: ["Outlet 7: load above threshold (18.2A / 16A)"],
      outlets: makeOutlets(24, "c1", [
        ["Legacy-Test-Rig", "on", 220],
        ["DevBox-Build", "on", 180],
        ["Overloaded-Gear", "on", 3786, "warning"],
      ]),
    },
  ],

  kvms: [
    {
      id: "kvm-a1",
      name: "KVM-Rack-A1",
      model: "Raritan Dominion KX III",
      shortModel: "KX III",
      ip: "10.10.30.11",
      rack: "Rack-A1",
      status: "online",
      firmware: "3.8.2.5.10583",
      portCount: 16,
      ports: makePorts(16, [
        ["GPU-Node-01", "active", "linux-term"],
        ["GPU-Node-02", "active", "gpu-monitor"],
        ["GPU-Node-03", "active", "linux-term"],
        ["GPU-Node-04", "idle", "blank"],
        ["GPU-Node-05", "active", "linux-term"],
        ["GPU-Node-06", "active", "linux-term"],
        ["GPU-Node-07", "active", "linux-term"],
        ["GPU-Node-08", "active", "bios"],
      ]),
    },
    {
      id: "kvm-a2",
      name: "KVM-Rack-A2",
      model: "Raritan Dominion KX III",
      shortModel: "KX III",
      ip: "10.10.30.21",
      rack: "Rack-A2",
      status: "online",
      firmware: "3.8.2.5.10583",
      portCount: 16,
      ports: makePorts(16, [
        ["DGX-H100-01", "active", "nvidia-smi"],
        ["DGX-H100-02", "active", "linux-term"],
      ]),
    },
    {
      id: "kvm-b1",
      name: "KVM-Rack-B1",
      model: "Raritan Dominion LX II",
      shortModel: "LX II",
      ip: "10.10.30.31",
      rack: "Rack-B1",
      status: "online",
      firmware: "2.4.3.1.7",
      portCount: 8,
      ports: makePorts(8, [
        ["GH200-Eval-01", "active", "linux-term"],
        ["GH200-Eval-02", "active", "linux-term"],
        ["Legacy-Server", "active", "win-login"],
      ]),
      notes: "LX II is Java-era; live iframe embed may fall back to native viewer in a new tab.",
    },
  ],
};

function makeOutlets(count, prefix, named) {
  const result = [];
  for (let i = 1; i <= count; i++) {
    const entry = named[i - 1];
    if (entry) {
      const [label, state, watts, severity] = entry;
      result.push({
        id: `${prefix}-o${i}`,
        number: i,
        label,
        state,
        watts,
        current: watts ? +(watts / 208).toFixed(2) : 0,
        severity: severity || (state === "on" ? "ok" : "off"),
      });
    } else {
      result.push({
        id: `${prefix}-o${i}`,
        number: i,
        label: `Outlet ${i}`,
        state: "off",
        watts: 0,
        current: 0,
        severity: "off",
      });
    }
  }
  return result;
}

function makePorts(count, named) {
  const result = [];
  for (let i = 1; i <= count; i++) {
    const entry = named[i - 1];
    if (entry) {
      const [label, status, screenType] = entry;
      result.push({
        id: `p${i}`,
        number: i,
        label,
        status,
        screenType,
      });
    } else {
      result.push({
        id: `p${i}`,
        number: i,
        label: `Port ${i}`,
        status: "empty",
        screenType: "blank",
      });
    }
  }
  return result;
}
