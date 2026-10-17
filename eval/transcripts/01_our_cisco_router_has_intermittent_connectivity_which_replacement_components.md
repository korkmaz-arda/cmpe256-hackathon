## Q: Our Cisco router has intermittent connectivity. Which replacement components should we order, and what diagnostics should we run first?

**Route** (gpt-5.4-mini, 1.1s): technology: The request is entirely about Cisco router troubleshooting and replacement components, which falls squarely under the technology specialist scope. (confidence 0.98)

### Technology Agent (19.7s)
*Sub-question:* For a Cisco enterprise router with intermittent connectivity, which replacement components should we order first, and what diagnostic checks should we run before replacing parts?

Do not order a full set of replacement parts until you identify the exact router model, interface type, logs, and hardware health. For intermittent connectivity, the first spares to stage are usually low-risk, high-failure-probability field-replaceable items such as optics/SFPs, patch cables, and—if your platform supports redundant or replaceable power—power supplies; but compatibility must be confirmed against the exact chassis and module inventory before purchase.

**Findings**
- (✅ confirmed) Optics/transceivers are relevant replacement candidates on Cisco enterprise routers because Cisco platforms support SFP-based fiber/copper connectivity depending on platform, and Catalyst 8300 documentation explicitly references optics and transceiver modules. [S1, S5]
- (✅ confirmed) Power should be checked before replacing parts: Catalyst 8300 platforms have dual power supply by default for backup if the primary power supply fails, while Cisco 4000 ISR power redundancy is available by installing an optional power supply on supported models. [S1, S2]
- (✅ confirmed) Fan/thermal issues should be checked: Catalyst 8300 ships with a fan tray by default, and Catalyst 8200 documentation describes power and thermal management capabilities. [S1, S4]
- (✅ confirmed) If the router is a Cisco 4000 Series ISR, note that the platform is end-of-sale with end-of-support listed as January 31, 2030, and Cisco positions Catalyst 8200/8300 as replacement/upgrade platforms. [S3]
- (🔍 hypothesis) For an intermittent outage, the failed component is not yet known; likely causes include bad optics/SFPs, dirty fiber, failing copper patch cable, marginal power supply, overheating/fan issues, interface module fault, software bug, duplex/speed mismatch, WAN carrier issue, or capacity/congestion. [S1, S2, S4, S5]

**Recommendations**
- **[high] Order or stage compatible spare optics/SFPs and patch cables first, but only after confirming the exact interface type, speed, media, and supported transceiver list for the router/module.**: Intermittent connectivity is often physical-layer related, and optics/transceivers are field-replaceable and explicitly supported as a component category on Cisco platforms; however, the exact part number must match the platform and interface. [S1, S5]
- **[high] If the platform has redundant or replaceable power supplies, stage the correct power supply model as the next priority after optics/cabling.**: Power instability can cause intermittent failures. Catalyst 8300 includes dual power supplies by default, and Cisco 4000 ISR supports optional power redundancy on supported models, but the correct PSU depends on chassis and power requirements. [S1, S2]
- **[medium] Do not order NIM/SM/interface modules until diagnostics show errors isolated to a specific module or port group.**: Cisco routers support modular interfaces, but replacing a module without port-level evidence risks replacing a healthy part. Cisco 4000 ISR service modules support online insertion/removal on supported models, which can reduce disruption when a replacement is justified. [S2, S4]
- **[medium] If the device is a Cisco 4000 Series ISR and hardware is aging or near lifecycle planning windows, evaluate Catalyst 8200 or Catalyst 8300 as an upgrade path rather than only buying break/fix spares.**: Cisco lists the 4000 Series ISR as end-of-sale and identifies Catalyst 8200/8300 as replacement/upgrade platforms. [S3]
- **[high] Run diagnostics before replacing parts: collect `show version`, `show logging`, `show interfaces`, `show environment`, optics/SFP status, and recent change history.**: These checks separate confirmed faults from hypotheses: interface counters identify physical-layer errors, logs show link flaps or hardware alarms, environment checks show power/fan/temperature conditions, and version/change data helps identify software or configuration causes. [S1, S2, S4, S5]

**Next steps**
- Identify the exact router model, chassis PID, IOS XE version, installed modules, and affected interface names from `show version` and inventory output.
- Check `show logging` for link flaps, power events, fan/temperature alarms, module resets, or crash messages around the outage times.
- Check `show interfaces <interface>` for CRC, input errors, output drops, carrier transitions, speed/duplex, and link reset counters.
- Check `show environment` or equivalent platform health output for power-supply, fan, and temperature state.
- Inspect or swap the lowest-risk physical components first: fiber/copper patch cable, optic/SFP, patch-panel port, and provider handoff—one variable at a time.
- If errors follow a port/module rather than the cable or optic, then plan a compatible NIM/SM/interface-module replacement or chassis upgrade.

**Information needed from you**
- Exact Cisco router model and chassis PID, for example Catalyst 8300, Catalyst 8200, ISR 4000, or ASR 1000.
- Affected interface names, media type, optic/SFP type, and connected provider or switch handoff.
- Current IOS XE/software version and uptime from `show version`.
- Recent configuration, circuit, optic, cabling, power, or software changes.
- Relevant `show logging`, `show interfaces`, `show environment`, and inventory/output for installed modules.
- Whether the outage is a physical link flap, routing adjacency reset, tunnel/SD-WAN issue, packet loss, or complete router reboot.

**Risks and assumptions**
- Assumption: the issue is on a Cisco enterprise router covered by the available Cisco documentation; exact platform is not yet known.
- Risk: ordering optics, power supplies, or modules before confirming model compatibility can result in unusable spares.
- Risk: replacing hardware before checking logs and counters may miss software, configuration, carrier, or congestion causes.
- Risk: if the router is a Cisco 4000 Series ISR, spares may be affected by lifecycle status because the platform is end-of-sale.
- Risk: swapping multiple parts at once can obscure the true root cause.

**How to measure impact (KPIs)**
- Interface error rate: Track CRC, input errors, output errors, and carrier transitions before and after cable/SFP/module changes.
- Link flap frequency: Count link up/down events in `show logging` or syslog per 24-hour period.
- Hardware health alarms: Monitor power, fan, and temperature status from platform environment commands or NMS.
- Mean time between incidents: Compare number of user-impacting connectivity incidents per week before and after remediation.
- Packet loss/latency on affected path: Use IP SLA, NMS polling, or continuous ping toward WAN next hop and critical applications.

**Confidence:** medium: The component categories and platform capabilities are source-supported, but the correct replacement part numbers cannot be confirmed without the exact router model, installed modules, interface type, and diagnostic outputs.

*Grounding:* 6 sources, 4 confirmed / 1 hypotheses, citation coverage 100%, grounding score 0.89
*Tools used:* `search_knowledge`

**Sources cited**
- **S1**: Cisco Catalyst 8300 Series Edge Platforms Data Sheet, p.16 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.pdf>
- **S2**: Cisco 4000 Series Integrated Services Routers Data Sheet, p.6 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>
- **S3**: Cisco 4000 Series Integrated Services Routers <https://www.cisco.com/c/en/us/products/routers/4000-series-integrated-services-routers-isr/index.html>
- **S4**: Cisco Catalyst 8200 Series Edge Platforms Data Sheet, p.10 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8200-series-edge-platforms/nb-06-cat8200-series-edge-plat-ds-cte-en.pdf>
- **S5**: Cisco 4000 Series Integrated Services Routers Data Sheet, p.6 <https://www.cisco.com/c/en/us/products/collateral/routers/4000-series-integrated-services-routers-isr/data_sheet-c78-732542.pdf>

*Total time: 20.8s*