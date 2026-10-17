## Q: Which technology investments could improve food security and sustainability outcomes?

**Route** (gpt-5.4-mini, 1.6s): technology, csr (cross-domain): This is cross-domain because it asks for technology investments and their potential impact on food security and sustainability, which requires both technology options and evidence on food-security drivers and sustainability priorities from SOFI. (confidence 0.93)

### Consolidated consulting recommendation (Manager Agent)

Invest in a targeted portfolio that combines rural–urban agrifood infrastructure with resilient digital connectivity, governed data/AI decision support, and financing models focused on high-need, underfinanced geographies. The strongest near-term technology plays are SD-WAN/SASE-enabled edge connectivity, multicloud networking, cold-chain and market-access data platforms, and RAG/MCP-enabled decision workflows. These should be aimed at the food-security drivers identified by SOFI: conflict, climate extremes, economic shocks, unaffordable nutritious foods, inequality, and weak rural–urban infrastructure. Evidence is strongest for the enabling technology capabilities and for food-security intervention priorities; quantified food-sector outcome improvements from the specific technologies remain a gap.

**Integrated recommendations**
- **[high] Prioritize resilient connectivity and digital infrastructure for farms, warehouses, food banks, ports, SMEs, and cold-chain nodes.**: SOFI identifies rural–urban infrastructure, cold storage, warehousing, electrification, digital tools, and market linkages as critical to food-security outcomes; Cisco SD-WAN/SASE-capable branch platforms can provide the secure, resilient edge connectivity needed to operate these assets reliably. [CSR-S8, TECH-S2, TECH-S3, TECH-S7]
- **[high] Build a governed food-security data platform for supply, demand, climate, inventory, price, logistics, and sustainability data.**: A shared data layer can support affordability, resilience, and market-access interventions while Google Cloud RAG-related services and BigQuery can ground AI outputs in fresh, private, and specialized datasets. [CSR-S10, CSR-S11, CSR-S14, TECH-S11, TECH-S12, TECH-S16]
- **[high] Deploy analytics and AI pilots focused on cold-chain loss reduction, stockout prevention, climate-risk planning, healthy-diet affordability, and supplier sustainability reporting.**: These use cases connect directly to SOFI drivers—climate shocks, economic stress, food loss, affordability, and inequality—while RAG can improve decision support and MCP can enable governed actions into logistics, inventory, or partner systems. [CSR-S3, CSR-S5, CSR-S12, TECH-S12, TECH-S14, TECH-S18, TECH-S19]
- **[medium] Use virtual cloud edge networking where food-system platforms span multiple clouds, agencies, NGOs, logistics partners, or private-sector systems.**: Food-security programmes often require cross-partner data exchange; Catalyst 8000V and Cloud OnRamp-style models can standardize secure multicloud connectivity and automation across Google Cloud, AWS, Azure, OCI, and partner networks. [TECH-S4, TECH-S5, TECH-S9, TECH-S10]
- **[high] Target financing and deployment to high-need communities with weak access to capital, and pair infrastructure with nutrition, women’s empowerment, and social-protection partners.**: SOFI warns that the places most affected by food insecurity and multiple malnutrition drivers often have the least access to finance; technology investments will have limited nutrition impact unless combined with affordability, education, inclusion, and local delivery models. [CSR-S4, CSR-S6, CSR-S9, CSR-S13, CSR-S16]

**How the domains connect**
- CSR’s emphasis on cold storage, warehousing, roads, electrification, water, and digital tools determines where TECH’s edge connectivity and SD-WAN investments should be deployed first.
- TECH’s RAG and data-platform capabilities are most valuable when grounded in CSR’s priority datasets: food prices, climate exposure, food insecurity, nutrition indicators, and rural–urban market access.
- CSR’s financing mismatch means technology investments should not be allocated only to easiest-to-serve sites; deployment models must include concessional, blended, or partner-funded approaches for high-risk geographies.
- TECH’s cybersecurity, observability, and governance recommendations are essential because CSR-priority programmes may involve vulnerable populations, public agencies, NGOs, and cross-border partner data.

**Conflicts and gaps**
- The technology evidence supports capabilities and deployment models, but does not quantify food-security or sustainability impact from these specific platforms.
- SOFI provides global intervention priorities, but geography-specific programme design requires local data on climate, conflict, markets, nutrition, infrastructure, and governance.
- Infrastructure and data platforms may improve availability and efficiency, but nutrition outcomes require affordability, health, WASH, education, and inclusion components.
- MCP-enabled AI agents create operational value but require strict identity, authorization, logging, and human approval before modifying logistics or inventory systems.

**Next steps**
- Map target geographies by food-security drivers: conflict, climate extremes, economic shocks, inequality, healthy-diet affordability, and financing access.
- Segment priority sites—farms, warehouses, cold-chain assets, food banks, ports, processors, SMEs, and cloud/data centers—by connectivity, power, security, and resilience needs.
- Select 3–5 outcome-led pilots such as cold-chain spoilage reduction, food-bank inventory optimization, climate-risk advisory, market-price monitoring, or supplier sustainability reporting.
- Inventory current WAN, 5G/cellular, satellite, IoT, cloud, ERP, logistics, inventory, and data-governance environments.
- Define data sources, access controls, freshness requirements, human-review rules, and whether each AI use case needs RAG only or MCP-enabled actions.
- Create a baseline and impact dashboard linking technology metrics to SOFI-aligned food-security, nutrition, market-access, and sustainability outcomes.

**How to measure impact (KPIs)**
- Critical-site connectivity availability: Track WAN/SD-WAN uptime, latency, packet loss, failover events, and application reachability by site type.
- Food loss and cold-chain performance: Measure spoilage rate, rejected shipments, temperature excursions, and post-harvest losses before and after deployment.
- Food-security and affordability outcomes: Track FIES moderate/severe food insecurity, cost of a healthy diet versus household income, and local price volatility.
- AI decision-support quality: Measure RAG groundedness, citation accuracy, forecast error, human approval rate, and exception-resolution time.
- Sustainability performance: Track energy use per facility or shipment, route miles avoided, emissions estimates, water-use efficiency, and waste diverted.

**Confidence:** medium: The recommendation is well supported on technology capabilities and SOFI intervention priorities, but the magnitude of food-security impact from specific technology deployments requires local baselines and pilot evidence.

### Technology Agent (29.0s)
*Sub-question:* Which technology investments (for example network, cloud, edge, or data-platform investments) could most effectively improve food security and sustainability outcomes, and what capabilities or deployment models are most relevant?

The highest-impact technology investments for food security and sustainability are usually a layered portfolio: resilient rural/edge connectivity, cloud and multicloud access, data platforms with AI/RAG for decision support, and secure agent/tool integration for operational workflows. The most relevant deployment models are secure SD-WAN/SASE at field sites and branches, virtual cloud edge routers for multicloud connectivity, and managed cloud AI/search services for grounding decisions in fresh private and public data.

**Findings**
- (✅ confirmed) Edge/branch network modernization is a strong foundation for food-system operations because Cisco Catalyst 8200 platforms are described as secure, flexible, scalable cloud-edge platforms for cloud applications, SASE, multilayer security, SD-WAN, and cloud-native agility. [S3, S7]
- (✅ confirmed) For larger or more demanding branch-to-cloud environments, Cisco Catalyst 8300 platforms are positioned for cloud-scale branch networking with optimized 5G, SD-WAN, software-defined routing, multicloud access, multilayer security, and enhanced visibility. [S2]
- (✅ confirmed) Virtual cloud edge investment can support multicloud food-system platforms: Cisco Catalyst 8000V is available for public clouds including AWS, Microsoft Azure, Google Cloud Platform, Oracle Cloud Infrastructure, and Alibaba Cloud, and supports SD-WAN Manager plus IOS XE CLI, REST, and NETCONF management. [S4, S9]
- (✅ confirmed) Multicloud connectivity is relevant where food-security programs need to connect analytics, logistics, ERP, IoT, and partner platforms across clouds; Catalyst 8000V documentation describes Cloud OnRamp automation, cross-cloud connectivity, and low-latency global connectivity use cases. [S5, S10]
- (✅ confirmed) RAG is relevant for food security and sustainability decision support because Google Cloud describes RAG as combining retrieval systems such as search/databases with LLMs, improving grounded generation with fresh, private, or specialized data. [S12, S14, S16]
- (✅ confirmed) Google Cloud identifies RAG-related services including RAG Engine in Gemini platform, Agent Search, Vector Search, and BigQuery, which are relevant capabilities for building search, analytics, and grounded AI over agricultural, supply-chain, climate, and policy data. [S11]
- (✅ confirmed) MCP is relevant when AI systems must do more than answer questions; Google Cloud describes MCP as an open standard for connecting AI applications to external tools and data sources, with governance, security, and access control through remote MCP servers. [S18, S19]
- (🔍 hypothesis) Likely high-impact use cases include precision agriculture, cold-chain monitoring, demand/supply forecasting, climate-risk planning, food-loss reduction, and compliance reporting, but these are hypotheses because the retrieved sources describe the enabling network/cloud/AI capabilities rather than food-sector outcome studies directly. [S1, S2, S11, S12, S19]

**Recommendations**
- **[high] Invest first in resilient edge connectivity for farms, warehouses, food banks, ports, and distribution centers using SD-WAN/SASE-capable branch platforms such as Cisco Catalyst 8200 for lean/small branches or Cisco Catalyst 8300 for higher-scale branch-to-cloud needs.**: Food-security operations depend on reliable field and branch connectivity for sensors, logistics, payments, inventory, and cloud analytics; the cited platforms support secure cloud-edge connectivity, SD-WAN, multilayer security, and flexible branch deployment. [S2, S3, S7]
- **[high] Use virtual cloud edge networking, such as Cisco Catalyst 8000V, where workloads span Google Cloud, AWS, Azure, OCI, or partner networks.**: This model helps standardize secure WAN extension into public clouds and supports multicloud connectivity and automation through Cisco Catalyst SD-WAN Manager and Cloud OnRamp. [S4, S5, S9, S10]
- **[high] Build a governed data platform for operational and sustainability data, with BigQuery and RAG-capable services where Google Cloud is in scope.**: RAG benefits from fresh, private, and specialized data; Google Cloud identifies BigQuery, RAG Engine, Agent Search, and Vector Search as related products for retrieval-augmented generation and enterprise search over large datasets. [S11, S12, S16]
- **[medium] Deploy RAG for decision-support workflows such as agronomist knowledge assistants, food-bank inventory Q&A, climate-risk briefings, supplier compliance search, and policy/program guidance.**: Google Cloud states RAG improves accuracy, relevance, and freshness by grounding LLM output in retrieved external data; it is especially useful for agents and chatbots needing private or specialized information. [S12, S14, S16]
- **[medium] Use MCP for AI agents that need to take controlled actions, such as querying databases, opening tickets, updating logistics systems, or calling partner APIs.**: Google Cloud describes MCP as a standardized way for AI applications to connect to external tools and data sources, with remote MCP servers supporting governance, security, and access control. [S17, S18, S19, S20]
- **[high] Treat cybersecurity and observability as core sustainability infrastructure, not add-ons: include SD-WAN analytics, ThousandEyes-style visibility, NGFW/SASE controls, and configuration governance.**: Cisco sources emphasize visibility into internet, cloud, and SaaS application issues, SD-WAN analytics, and integrated security controls for direct cloud/internet access. [S1, S2, S6, S8]

**Next steps**
- Map priority food-system locations and classify them by connectivity need: farm/field, warehouse, cold chain, retail/food bank, port, processing plant, and cloud/data center.
- Inventory current WAN, cellular/5G, satellite, LAN, IoT gateways, cloud regions, data stores, and security controls.
- Define 3–5 outcome-led pilots, for example cold-chain loss reduction, drought-risk advisory, food-bank inventory optimization, or supplier sustainability reporting.
- For each site class, size the network platform requirements: throughput, number/type of WAN links, 5G need, redundancy, interface modules, cloud connectivity, and security policy.
- For AI/data pilots, identify authoritative data sources, freshness requirements, access controls, and whether the use case needs RAG only or MCP-enabled actions.
- Create a measurement plan before deployment, linking technology metrics to operational outcomes such as spoilage, stockout rate, delivery delay, and energy use.

**Information needed from you**
- Target geography and site types: farms, warehouses, food banks, ports, processors, retail, or government agencies.
- Current network architecture, carrier links, cloud providers, and whether SD-WAN or SASE is already deployed.
- Scale requirements: number of sites, users, sensors, applications, throughput, availability targets, and latency-sensitive workloads.
- Data sources available: IoT telemetry, weather, satellite imagery, ERP, logistics, inventory, market prices, compliance documents, and partner data.
- Security and governance requirements, including data residency, partner access, auditability, and regulatory constraints.
- Primary outcome goals: yield improvement, food-loss reduction, affordability, traceability, resilience, emissions, water efficiency, or emergency response.

**Risks and assumptions**
- The food-security impact examples are inferred from the capabilities of the cited technologies; the retrieved sources do not quantify food-sector-specific outcome improvements.
- Product selection must be validated against exact throughput, interface, redundancy, environmental, and lifecycle requirements before procurement.
- AI decision-support systems can produce incorrect outputs if source data is incomplete, stale, biased, or poorly governed, so RAG quality evaluation and human review are required.
- Rural and remote sites may need carrier diversity, 5G, satellite, or offline-tolerant designs; the best access model depends on local coverage and power reliability.
- MCP-enabled agents should be restricted by identity, authorization, logging, and approval workflows before being allowed to modify operational systems.

**How to measure impact (KPIs)**
- Connectivity availability at critical food-system sites: Track WAN/SD-WAN uptime, packet loss, latency, failover events, and application reachability by site class.
- Food loss or spoilage reduction: Compare spoilage percentage, cold-chain temperature excursions, and rejected shipments before and after connectivity/IoT/data-platform deployment.
- Forecast and decision-support quality: Measure forecast error, RAG answer groundedness, citation accuracy, and human approval rate for AI-generated recommendations.
- Operational response time: Track time to detect and resolve logistics exceptions, stockouts, equipment alarms, and weather/climate disruptions.
- Sustainability performance: Measure energy use per shipment or facility, route miles avoided, emissions estimates, water-use efficiency, and waste diverted.

**Confidence:** medium: The recommended capabilities and deployment models are directly supported by Cisco and Google Cloud sources, but the question asks about food security and sustainability outcomes; specific sector outcome evidence was not present in the retrieved sources, so impact prioritization is partly inferential.

*Grounding:* 20 sources, 7 confirmed / 1 hypotheses, citation coverage 100%, grounding score 1.00
*Tools used:* `search_knowledge`, `search_knowledge`

**Sources cited**
- **TECH-S1**: Cisco Catalyst 8200 Series Edge Platforms <https://www.cisco.com/c/en/us/products/routers/catalyst-8200-series-edge-platforms/index.html>
- **TECH-S2**: Cisco Catalyst 8300 Series Edge Platforms <https://www.cisco.com/c/en/us/products/routers/catalyst-8300-series-edge-platforms/index.html>
- **TECH-S3**: Cisco Catalyst 8200 Series Edge Platforms <https://www.cisco.com/c/en/us/products/routers/catalyst-8200-series-edge-platforms/index.html>
- **TECH-S4**: Cisco Catalyst 8000V Edge Software Data Sheet, p.18 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8000v-edge-software/catalyst-8000v-edge-software-ds.pdf>
- **TECH-S5**: Cisco Catalyst 8000V Edge Software <https://www.cisco.com/c/en/us/products/routers/catalyst-8000v-edge-software/index.html>
- **TECH-S6**: Cisco Catalyst 8200 Series Edge Platforms <https://www.cisco.com/c/en/us/products/routers/catalyst-8200-series-edge-platforms/index.html>
- **TECH-S7**: Cisco Catalyst 8200 Series Edge Platforms Data Sheet, p.3 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8200-series-edge-platforms/nb-06-cat8200-series-edge-plat-ds-cte-en.pdf>
- **TECH-S8**: Cisco ASR 1000 Series Aggregation Services Routers Data Sheet, p.4 <https://www.cisco.com/c/en/us/products/collateral/routers/asr-1000-series-aggregation-services-routers/datasheet-c78-731632.pdf>
- **TECH-S9**: Cisco Catalyst 8000V Edge Software Data Sheet, p.12 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8000v-edge-software/catalyst-8000v-edge-software-ds.pdf>
- **TECH-S10**: Cisco Catalyst 8000V Edge Software Data Sheet, p.9 <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8000v-edge-software/catalyst-8000v-edge-software-ds.pdf>
- **TECH-S11**: What is Retrieval-Augmented Generation (RAG)? | Google Cloud <https://cloud.google.com/use-cases/retrieval-augmented-generation>
- **TECH-S12**: What is Retrieval-Augmented Generation (RAG)? | Google Cloud <https://cloud.google.com/use-cases/retrieval-augmented-generation>
- **TECH-S14**: What is Retrieval-Augmented Generation (RAG)? | Google Cloud <https://cloud.google.com/use-cases/retrieval-augmented-generation>
- **TECH-S16**: What is Retrieval-Augmented Generation (RAG)? | Google Cloud <https://cloud.google.com/use-cases/retrieval-augmented-generation>
- **TECH-S17**: What is Model Context Protocol (MCP)? A guide | Google Cloud <https://cloud.google.com/discover/what-is-model-context-protocol>
- **TECH-S18**: What is Model Context Protocol (MCP)? A guide | Google Cloud <https://cloud.google.com/discover/what-is-model-context-protocol>
- **TECH-S19**: Google Cloud MCP servers overview  |  Google Cloud Documentation <https://docs.cloud.google.com/mcp/overview>
- **TECH-S20**: What is Model Context Protocol (MCP)? A guide | Google Cloud <https://cloud.google.com/discover/what-is-model-context-protocol>

### Corporate Responsibility Agent (22.9s)
*Sub-question:* According to the UN FAO SOFI 2023 and 2024 reports, what are the main drivers of food insecurity and malnutrition, and which sustainability interventions or financing priorities are identified as most likely to improve outcomes?

SOFI 2023 and 2024 identify the main drivers of food insecurity and malnutrition as conflict, climate variability and extremes, economic slowdowns/downturns, unaffordable nutritious foods, unhealthy food environments, and persistent inequality. SOFI 2023 emphasizes urbanization and the rural–urban continuum: improving infrastructure, diversified food production, social protection, nutrition education, women’s empowerment, and SME/value-chain linkages can improve access to affordable healthy diets. SOFI 2024 emphasizes that financing must be broadened and better targeted to these drivers, especially because the countries most affected by food insecurity, malnutrition and multiple drivers often have the least access to finance.

**Findings**
- (✅ confirmed) Both reports identify conflict, climate variability and extremes, and economic slowdowns/downturns as major drivers of hunger, food insecurity and malnutrition, compounded by unaffordable nutritious foods and inequality. [S3, S5, S10, S12, S14]
- (✅ confirmed) SOFI 2024 adds that unhealthy food environments and high, persistent inequality are structural underlying factors that worsen the impact of the major drivers. [S10, S12, S14, S15]
- (✅ confirmed) SOFI 2024 states that many low- and middle-income countries are affected by at least one major driver, and that multiple drivers have compounding impacts associated with the highest increases in hunger and food insecurity. [S11]
- (✅ confirmed) SOFI 2024 finds a financing mismatch: countries with the highest food insecurity, multiple forms of malnutrition and exposure to major drivers tend to have the least access to financing. [S9, S16]
- (✅ confirmed) SOFI 2023 highlights rural–urban disparities in malnutrition linked to access to health care, water, sanitation and services; proximity to agricultural production does not automatically translate into healthier diets for children. [S1]
- (✅ confirmed) SOFI 2023 identifies infrastructure across the rural–urban continuum—roads, warehousing, cold storage, electrification, digital tools and water supply—as important for stronger agrifood linkages, SME efficiency, resilience, incomes and food security outcomes. [S8]
- (✅ confirmed) SOFI 2023 identifies cash transfers, especially when paired with nutrition education, as relevant for improving diets and child nutrition/health, and for easing liquidity constraints among poor households. [S4]
- (✅ confirmed) SOFI 2023 identifies irrigation, diversification beyond staple-focused programmes, biofortification where diverse production is not yet feasible, and women’s empowerment as pathways to improve access to nutritious foods and dietary diversity. [S2, S6]

**Recommendations**
- **[high] Prioritize resilience investments in countries and communities exposed to conflict, climate extremes and economic shocks.**: These are the repeatedly identified major drivers; SOFI 2024 argues financing should cover interventions that strengthen agrifood-system resilience to them. Track impact through prevalence of undernourishment, moderate/severe food insecurity and child malnutrition indicators. [S10, S11, S14, S15]
- **[high] Finance rural–urban agrifood infrastructure: cold storage, warehousing, roads, dependable electrification, water supply and digital tools for small farms and SMEs.**: SOFI 2023 identifies these investments as critical for efficient SMEs, stronger rural–urban linkages, resilience to shocks, productivity, incomes and food security outcomes. [S8]
- **[high] Support social protection packages that combine cash transfers with nutrition education, and where relevant in-kind transfers or school meals.**: SOFI 2023 states income is a key determinant of healthy-diet affordability and that cash transfers with nutrition education have greater chances of improving child nutrition and health. [S4, S6]
- **[medium] Invest in diversified nutritious food production, irrigation for fruits and vegetables, and biofortified crops where diversified production is not yet feasible.**: SOFI 2023 notes that staple-focused programmes can undermine diversification, while irrigation and biofortification can improve dietary diversity and nutrient intake. [S2]
- **[medium] Embed women’s empowerment into food production and nutrition programmes, especially in rural areas.**: SOFI 2023 identifies women’s empowerment as one of the important pathways through which food production policies improve access to nutritious foods and household dietary diversity. [S6]
- **[medium] Use blended or innovative financing only where it is designed to overcome risk and access barriers in high-need countries, not only where projects are easiest to finance.**: SOFI 2024 warns that the countries most in need often face structural limitations and high perceived financial risk, restricting access to finance. [S9, S13, S16]

**Next steps**
- Map target geographies against the SOFI drivers: conflict exposure, climate extremes, economic shocks, healthy-diet affordability, inequality and food-environment risks.
- Select interventions by driver: resilience for climate/conflict/economic shocks; affordability measures for income and price barriers; infrastructure for rural–urban market failures; nutrition services for malnutrition risks.
- Set a baseline using SOFI-aligned indicators: PoU, FIES moderate/severe food insecurity, cost/affordability of a healthy diet, stunting, wasting and child overweight where relevant.
- Prioritize countries or regions where food-security need is high but financing access is limited.
- Design programmes with local partners, SMEs, women’s groups and public agencies to avoid isolated CSR projects.
- Create an impact-financing dashboard that reports both capital mobilized and nutrition/food-security outcomes.

**Information needed from you**
- Target countries or regions for the company’s CSR/ESG programme.
- Whether the company wants grantmaking, concessional finance, procurement, technology investment or blended finance.
- Priority populations: smallholder farmers, urban poor, women, children, displaced people or SMEs.
- Current company footprint in agrifood value chains, logistics, retail, finance, technology or health.
- Budget, time horizon and risk appetite.
- Existing local partners or government programmes to align with.

**Risks and assumptions**
- SOFI findings are global; intervention design must be adapted to local political economy, climate risk, markets and nutrition profiles.
- Financing may not reach highest-need countries unless risk barriers are explicitly addressed.
- Infrastructure investments can improve availability but may not improve nutrition without affordability, health, WASH and behaviour-change components.
- Biofortification or production diversification should complement, not replace, broader access to diverse healthy diets.
- Conflict settings may require humanitarian-development-peace coordination and safeguards.

**How to measure impact (KPIs)**
- Prevalence of moderate or severe food insecurity using FIES: Baseline and follow-up household surveys in target communities, disaggregated by gender, income group and rural–urban location.
- Affordability of a healthy diet: Track local cost of a healthy diet against household income or food budgets before and after interventions.
- Child stunting and wasting prevalence: Use health/nutrition surveillance or programme anthropometric screening for children under five.
- Dietary diversity or consumption of nutritious food groups: Household or individual dietary diversity surveys, especially among women and children.
- Resilient market access for nutritious foods: Measure cold-storage capacity, post-harvest losses, SME throughput, market availability and price stability for fruits, vegetables and other nutritious foods.

**Confidence:** high: The drivers and broad intervention/financing priorities are directly and repeatedly stated in SOFI 2023 and 2024 passages; programme-level prioritization still requires client geography and operating-context details.

*Grounding:* 16 sources, 8 confirmed / 0 hypotheses, citation coverage 100%, grounding score 0.96
*Tools used:* `search_knowledge`, `search_knowledge`

**Sources cited**
- **CSR-S1**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.69 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S2**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.150 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S3**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.173 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S4**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.141 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S5**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.9 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S6**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.150 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S8**: FAO SOFI 2023: The State of Food Security and Nutrition in the World, p.147 `data/FoodSecurity/SOFI-2023.pdf`
- **CSR-S9**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.9 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S10**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.84 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S11**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.94 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S12**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.23 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S13**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.141 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S14**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.24 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S15**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.178 `data/FoodSecurity/SOFI-2024.pdf`
- **CSR-S16**: FAO SOFI 2024: The State of Food Security and Nutrition in the World, p.27 `data/FoodSecurity/SOFI-2024.pdf`

*Total time: 45.8s*