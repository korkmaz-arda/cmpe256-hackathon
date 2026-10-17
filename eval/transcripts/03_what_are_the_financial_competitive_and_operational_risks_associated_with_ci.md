## Q: What are the financial, competitive, and operational risks associated with Cisco, Agilent and Alphabet?

**Route** (gpt-5.4-mini, 1.8s): sec: The request is specifically about risks disclosed in company annual reports for Cisco, Agilent, and Alphabet, which is covered by the SEC specialist. (confidence 0.98)

### SEC Agent (31.3s)
*Sub-question:* What are the key financial, competitive, and operational risks disclosed in Alphabet's FY2024 and FY2025 10-Ks?

Alphabet’s FY2024 and FY2025 10-Ks disclose a consistent risk profile: heavy advertising dependence, intensifying competition—especially in AI and digital advertising—and operational exposure from cybersecurity, privacy, regulatory/legal scrutiny, and large technical-infrastructure needs. The FY2025 filing updates the mix: advertising remains dominant but declined from “more than 75% of total revenues” in FY2024 to “more than 70% of total revenues” in FY2025, while AI, cloud, subscriptions, devices, debt financing, and data-center leases receive more emphasis as margin, execution, and compliance risks.

**Findings**
- (✅ confirmed) Financial risk: Alphabet remains highly dependent on advertising. FY2024 states it generated “more than 75% of total revenues from online advertising in 2024,” while FY2025 states it generated “more than 70% of total revenues from online advertising in 2025.” Reduced advertiser spending, loss of partners, ad-blocking, personalization limits, and shifts in ad formats could harm results. [S25, S36]
- (✅ confirmed) Financial risk: revenue growth and operating margins may decline. FY2024 cites possible revenue-growth decline from device/modalities changes, geographic mix, advertiser spending declines, competition, pricing pressure, product/policy changes, and shifts to lower-priced products; it also warns of margin pressure from lower-margin devices, Google Cloud, subscriptions, Other Bets, regulation, competition, and costs. FY2025 repeats this and adds that fixed costs may not correlate with revenue and efficiencies may not continue at prior rates. [S26, S28, S33, S34]
- (✅ confirmed) Financial risk: traffic acquisition costs and mix can pressure margins. FY2024 says TAC and TAC rate are affected by device mix, geographic mix, partner terms, partner mix, paid access points, product mix, relative channel growth, and revenue-share terms; FY2025 says TAC is expected to increase as advertising revenues grow, though the overall TAC rate has been decreasing due to mix shift from Google Network properties to Google Search & other properties. [S24, S32, S37]
- (✅ confirmed) Financial risk: international operations expose Alphabet to foreign-currency movements. FY2024 says international revenues are significant and exchange-rate fluctuations are not fully offset by hedging; FY2025 identifies principal currency exposures as the Australian dollar, British pound, Canadian dollar, Euro, and Japanese yen. [S23, S20]
- (✅ confirmed) Competitive risk: Alphabet faces broad competition across search, vertical search/e-commerce, online advertising platforms, offline advertising, digital content/application platforms, enterprise providers, referral/social products, workspace/connectivity products, and digital assistants; FY2025 adds stronger emphasis that competition from developers and providers of AI products and services may affect revenues. [S21, S29, S31, S38]
- (✅ confirmed) Competitive risk: successful competition depends on retaining users, advertisers, content providers, publishers, customers, and partners. FY2024 notes users are “literally one click away,” and FY2025 reiterates that competitors’ success in compelling products or attracting users, advertisers, publishers, customers, and content providers could harm financial condition and operating results. [S29, S33, S38]
- (✅ confirmed) Operational risk: cybersecurity, privacy, software, and AI-related security exposures are material. FY2025 cites risks from software supply chain and third-party dependencies, product vulnerabilities, theft of intellectual property, attempts to compromise infrastructure, cyberattacks, data exfiltration, state-sponsored actors, and AI-centric security risks; it also warns that data handling or privacy concerns could harm reputation, financial condition, and operating results. [S17, S19, S45, S47]
- (✅ confirmed) Operational/legal-regulatory risk: Alphabet faces evolving regulation, litigation, investigations, and enforcement in areas including AI, competition, consumer protection, content moderation, data privacy/security, IP, tax, labor, and sustainability. Both filings state regulatory changes and legal matters have resulted in fines and business-practice changes, and FY2025 warns AI development and commercialization could create regulatory action and legal liability. [S6, S16, S40, S41, S42, S49]

**Recommendations**
- **[high] For procurement or partnership decisions, require contract protections for service continuity, data security, privacy compliance, audit rights, and incident notification tied to Alphabet services used.**: Alphabet discloses material cybersecurity, privacy, third-party dependency, infrastructure-compromise, and regulatory risks that could affect service reliability and data handling. [S17, S19, S45, S47]
- **[high] Stress-test exposure to Google advertising products under scenarios of reduced personalization, ad-format shifts, higher TAC/margin pressure, and advertiser-spend cyclicality.**: Alphabet’s revenue base remains heavily advertising-dependent—“more than 75%” in FY2024 and “more than 70%” in FY2025—and filings warn advertiser spending and ad-technology changes could harm results. [S25, S36, S39]
- **[high] If evaluating Google Cloud or AI services, perform AI governance due diligence: model-risk controls, IP indemnities, privacy safeguards, content-safety controls, and regulatory-change allocation.**: FY2025 specifically identifies AI risks involving harmful content, inaccuracies, discrimination, IP infringement, privacy, cybersecurity, regulatory action, legal liability, and reputational harm. [S41, S48, S50]
- **[medium] Monitor Alphabet’s legal and regulatory proceedings as a vendor and counterparty risk factor, especially antitrust/competition and privacy matters.**: Alphabet states claims, investigations, enforcement actions, fines, and orders have caused and may continue to cause changes to products, services, business practices, and costs. [S40, S42, S43, S44]
- **[medium] Build a vendor concentration and substitutability plan for key Alphabet services, especially search advertising, cloud, identity, analytics, and AI dependencies.**: Alphabet operates in rapidly changing competitive markets and discloses risks around user/customer shifts, competing technologies, and infrastructure/cyber disruptions. [S21, S33, S17]

**Next steps**
- Map your organization’s spend and operational dependency on Alphabet services by product: Ads, Cloud, Workspace, Android/Play, YouTube, Maps, AI/APIs, and analytics.
- Review current Alphabet contracts for uptime SLAs, data-processing terms, breach notification, regulatory-change clauses, termination rights, and price-change protections.
- Assess whether any business-critical workflows rely on Google AI outputs and document human review, audit logging, and fallback procedures.
- Track Alphabet’s FY2025 legal matters note and subsequent filings for updates to competition, privacy, AI, and IP proceedings.
- Benchmark alternative suppliers for the highest-risk Alphabet dependencies.

**Information needed from you**
- Which Alphabet products or services the client uses or is considering.
- Annual spend and revenue dependency tied to Alphabet advertising, cloud, workspace, app distribution, or AI services.
- Data sensitivity and regulated-data categories processed through Alphabet services.
- Geographic footprint, especially EU, UK, US state privacy, and other regulated jurisdictions.
- Current contract terms, SLAs, DPAs, indemnities, and exit rights with Alphabet.
- Tolerance for vendor concentration and availability requirements for business-critical workflows.

**Risks and assumptions**
- This summary is limited to retrieved passages from Alphabet FY2024 and FY2025 10-Ks; detailed financial-statement figures beyond cited passages are not included unless retrieved.
- The filing does not state in the retrieved text a precise dollar amount for advertising revenue, TAC, legal fines, or cybersecurity costs for FY2024 or FY2025.
- Risk severity for a specific client depends on actual Alphabet product usage, data flows, contractual protections, and substitutability.

**How to measure impact (KPIs)**
- Alphabet dependency concentration: Percentage of annual digital-ad spend, cloud spend, productivity-suite seats, or AI/API usage tied to Alphabet products.
- Contractual risk coverage: Share of Alphabet contracts with current DPA, SLA, incident-notification, audit, indemnity, termination, and regulatory-change clauses.
- Incident resilience: Recovery time objective and tested failover success rate for workflows dependent on Alphabet services.
- AI governance compliance: Percentage of Google AI use cases with documented risk assessment, human review, data-classification approval, and output-monitoring controls.
- Regulatory exposure tracking: Quarterly review count of material Alphabet legal/regulatory updates affecting services used by the organization.

**Confidence:** high: The key risks are directly supported by multiple cited FY2024 and FY2025 10-K passages, including Item 1A Risk Factors, MD&A trends, cybersecurity disclosure, and market-risk disclosure.

*Grounding:* 50 sources, 8 confirmed / 0 hypotheses, citation coverage 100%, grounding score 1.00
*Tools used:* `search_knowledge`, `search_knowledge`, `search_knowledge`, `search_knowledge`, `search_knowledge`

**Sources cited**
- **S6**: Alphabet Inc. 10-K FY2024, p.32 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S16**: Alphabet Inc. 10-K FY2025, p.8 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S17**: Alphabet Inc. 10-K FY2025, p.25 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S19**: Alphabet Inc. 10-K FY2025, p.17 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S20**: Alphabet Inc. 10-K FY2025, p.42 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S21**: Alphabet Inc. 10-K FY2024, p.9 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S23**: Alphabet Inc. 10-K FY2024, p.32 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S24**: Alphabet Inc. 10-K FY2024, p.31 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S25**: Alphabet Inc. 10-K FY2024, p.11 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S26**: Alphabet Inc. 10-K FY2024, p.13 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S28**: Alphabet Inc. 10-K FY2024, p.13 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S29**: Alphabet Inc. 10-K FY2024, p.9 `data/SEC/Alphabet/0ca59726-c36c-45fe-a114-e147f8cd7237.pdf`
- **S31**: Alphabet Inc. 10-K FY2025, p.29 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S32**: Alphabet Inc. 10-K FY2025, p.29 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S33**: Alphabet Inc. 10-K FY2025, p.12 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S34**: Alphabet Inc. 10-K FY2025, p.12 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S36**: Alphabet Inc. 10-K FY2025, p.10 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S37**: Alphabet Inc. 10-K FY2025, p.30 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S38**: Alphabet Inc. 10-K FY2025, p.8 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S39**: Alphabet Inc. 10-K FY2025, p.10 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S40**: Alphabet Inc. 10-K FY2025, p.30 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S41**: Alphabet Inc. 10-K FY2025, p.19 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S42**: Alphabet Inc. 10-K FY2025, p.19 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S43**: Alphabet Inc. 10-K FY2025, p.21 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S44**: Alphabet Inc. 10-K FY2025, p.78 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S45**: Alphabet Inc. 10-K FY2025, p.16 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S47**: Alphabet Inc. 10-K FY2025, p.16 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S48**: Alphabet Inc. 10-K FY2025, p.15 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S49**: Alphabet Inc. 10-K FY2025, p.8 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`
- **S50**: Alphabet Inc. 10-K FY2025, p.15 `data/SEC/Alphabet/8873e505-7403-4c46-b377-81d814482cbb.pdf`

*Total time: 33.0s*