## Q: Our Cisco router has intermittent connectivity. Which replacement components should we order, and what diagnostics should we run first?

**Route** (gpt-5.4-mini, 1.2s): technology: The request is entirely about Cisco router troubleshooting and replacement parts, which falls under the Technology specialist scope. (confidence 0.98)

### Technology Agent (23.5s)
*Sub-question:* For a Cisco router with intermittent connectivity, which replacement components should we order first, and what diagnostic checks should we run before replacing parts? Please tailor the answer to Cisco enterprise routers and include model-specific guidance if relevant.

Do not order replacement parts solely on the symptom “intermittent connectivity.” For Cisco enterprise routers, the first spares to prioritize are the lowest-risk, commonly field-replaceable items that match the installed platform: approved optics/transceivers, patch cables, redundant/compatible power supplies, and—only after interface evidence—NIM/SM/PIM interface modules. Confirm the exact router model, module inventory, power state, interface counters, logs, and recent changes before replacing hardware.

**Findings**
- (✅ confirmed) Catalyst 8300 platforms support modular SM, NIM, and PIM slots, and all Catalyst 8300 platforms ship with dual power supplies for redundancy. [S7, S1, S9]
- (✅ confirmed) Catalyst 8300 optics/transceiver ordering must be validated against Cisco’s supported optics list; the retrieved datasheet points to a dedicated optics/transceivers list rather than embedding all part numbers. [S1, S8]
- (✅ confirmed) ISR 4400 models including ISR 4461, ISR 4451, and ISR 4431 support dual integrated power supplies for backup, and the ISR 4000 family supports modular network interfaces with online removal and insertion for module upgrades. [S4, S10, S11, S12]
- (✅ confirmed) ISR 4000 platforms have AC/DC power supply considerations: ISR4331 has separate AC and DC SKUs, while ISR4400 can support AC or DC power supply on the same chassis. [S5]
- (✅ confirmed) Cisco 4000 Series ISR is end-of-sale as of January 20, 2025, with end-of-support January 31, 2030; Cisco positions Catalyst 8200 and 8300 Series Edge Platforms as replacement/upgrade options. [S2]
- (🔍 hypothesis) Intermittent connectivity may be caused by optics/SFP issues, cabling, dirty fiber, WAN handoff instability, interface module faults, power/fan/environment problems, software defects, configuration changes, or capacity/licensing limits; these are plausible causes, not confirmed faults. [S1, S4, S6, S7]
- (✅ confirmed) If the router is an ASR 1000 used for aggregation or data-center/large WAN edge, redundant power supply availability is relevant, but exact field-replaceable part choices must be matched to the specific ASR model and installed modules. [S13]

**Recommendations**
- **[high] Order first: approved spare optics/transceivers and known-good patch cables for the affected WAN/LAN media type, but only after confirming the exact router model, interface type, speed, and Cisco-supported optic list.**: Intermittent links are often physical-layer related, optics are fast to swap, and Catalyst 8300 documentation explicitly separates optics/transceivers as a compatibility area requiring validation. [S1, S8]
- **[high] Order a compatible redundant power supply only if diagnostics show PSU alarms, power events, environmental instability, or the chassis lacks redundancy.**: Catalyst 8300 ships with dual power supplies for redundancy, and ISR 4400 models support dual integrated power supplies; however AC/DC and PoE requirements must match the chassis. [S1, S4, S5, S7]
- **[medium] Do not order a NIM, SM, or PIM replacement until interface counters, logs, or module diagnostics point to a specific slot or module.**: Catalyst 8300 supports SM/NIM/PIM slots and ISR 4000 supports modular network interfaces, but replacing modules without slot-level evidence risks misdiagnosis and unnecessary outage. [S4, S7]
- **[medium] If the platform is Cisco 4000 Series ISR and repair costs or part availability are poor, evaluate a Catalyst 8200 or Catalyst 8300 upgrade instead of only replacing parts.**: Cisco lists the 4000 Series ISR as end-of-sale and identifies Catalyst 8200/8300 as replacement/upgrade platforms for SD-WAN, SASE, 5G, modularity, security, and analytics. [S2, S3, S9]
- **[medium] For Catalyst 8300 branches, maintain spares for compatible optics, one matching PSU type, blank panels where needed, and critical NIM/PIM modules only if they are installed and business-critical.**: The datasheet identifies C8300 NIM/PIM blanks, optics/transceivers, dual PSU resiliency, and SM/NIM/PIM modularity as relevant platform elements. [S1, S7, S8]
- **[medium] For ISR 4431/4451/4461, prioritize PSU redundancy verification and interface-module evidence before procurement; use model-specific throughput/licensing data when deciding whether to replace a failed unit or upgrade.**: ISR 4431/4451/4461 have documented redundant PSU support, modular network interfaces, and distinct throughput/licensing characteristics. [S4, S10, S11, S12]

**Next steps**
- Collect exact chassis model, serial number, IOS XE version, uptime, installed modules, and power-supply inventory using `show version`, `show inventory`, and `show platform`.
- Check physical/interface health with `show interfaces`, focusing on input errors, CRC, frame errors, carrier transitions, drops, resets, speed/duplex, and link flap timestamps.
- Check hardware and environmental health with `show environment`, `show platform`, `show logging`, and any PSU/fan/temperature alarms.
- For fiber links, inspect/clean fiber, reseat optics, compare DOM levels if supported, and test with known-good Cisco-supported optics and patch leads.
- Correlate failures with WAN-provider events, power events, recent config changes, IOS XE upgrades, SD-WAN policy changes, or traffic peaks.
- If a module or PSU is suspected, move the circuit to a known-good port/module where supported, or swap with a lab/maintenance-window spare to confirm before ordering production replacements.

**Information needed from you**
- Exact Cisco router model, e.g., Catalyst 8300, Catalyst 8200, ISR 4431/4451/4461, ISR 4331, ASR 1001/1002-X, etc.
- Affected interface type and media: copper, fiber, LTE/5G, serial, MPLS handoff, Internet handoff, or switch-facing LAN.
- Current outputs of `show version`, `show inventory`, `show interfaces`, `show logging`, and `show environment`.
- Installed optics/transceiver part numbers and module part numbers from `show inventory`.
- Whether the router has redundant PSUs installed and whether AC, DC, or PoE power is required.
- Timeline of recent changes: IOS XE upgrade, SD-WAN migration, provider change, cabling work, power event, or configuration change.

**Risks and assumptions**
- Assumption: the router is a Cisco enterprise edge or aggregation platform covered by the retrieved Cisco sources; exact component compatibility still depends on the specific chassis and module inventory.
- Risk: ordering optics, PSUs, or interface modules before checking compatibility may result in unusable parts.
- Risk: replacing hardware without checking interface counters, logs, optics levels, and power/environment status can leave the root cause unresolved.
- Risk: for ISR 4000 platforms, end-of-sale status may affect procurement strategy even though support continues until the published end-of-support date.
- Risk: intermittent faults can be external to the router, including provider circuits, upstream switches, cabling, rack power, or environmental conditions.

**How to measure impact (KPIs)**
- Link-flap count: Track interface up/down events from `show logging` or monitoring system before and after remediation.
- Interface error rate: Compare CRC/input/frame/error counters from `show interfaces` over fixed intervals.
- Mean time to repair: Measure time from incident open to stable service after spare replacement or corrective action.
- Power/environment alarm count: Monitor PSU, fan, and temperature alarms from `show environment` and NMS/SNMP telemetry.
- Repeat incident rate: Count recurring connectivity tickets for the same site/interface over 30–90 days.

**Confidence:** medium: The platform capabilities and lifecycle guidance are directly supported by Cisco sources, but the failed component cannot be confirmed without the client’s model, logs, counters, inventory, and environmental data.

*Grounding:* 13 sources, 6 confirmed / 1 hypotheses, citation coverage 100%, grounding score 0.95
*Tools used:* `search_knowledge`, `recommend_products`

**Sources cited**
- **S1**: Cisco Catalyst 8300 Series Edge Platforms Data Sheet, p.16 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.pdf>
- **S2**: Cisco 4000 Series Integrated Services Routers <https://www.cisco.com/c/en/us/products/routers/4000-series-integrated-services-routers-isr/index.html>
- **S3**: Cisco Catalyst 8200 Series Edge Platforms Data Sheet, p.10 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8200-series-edge-platforms/nb-06-cat8200-series-edge-plat-ds-cte-en.pdf>
- **S4**: Cisco 4000 Series Integrated Services Routers Data Sheet, p.5 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S5**: Cisco 4000 Series Integrated Services Routers Data Sheet, p.18 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S6**: Cisco 4000 Series Integrated Services Routers Data Sheet, p.18 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S7**: Cisco Catalyst 8300 Series Edge Platforms Data Sheet, p.4 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.pdf>
- **S8**: Cisco Catalyst 8300 Series Edge Platforms Data Sheet, p.2 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.pdf>
- **S9**: Catalog: Catalyst 8300 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.pdf>
- **S10**: Catalog: ISR4451 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S11**: Catalog: ISR4431 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S12**: Catalog: ISR4461 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S13**: Catalog: ASR1002-X <https://www.cisco.com/c/en/us/products/collateral/routers/asr-1000-series-aggregation-services-routers/datasheet-c78-731632.pdf>

*Total time: 24.6s*