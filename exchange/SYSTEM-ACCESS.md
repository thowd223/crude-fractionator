# System access for automation and agents

What each system in the stack exposes for programs and agents, from public vendor documentation as of October 2026.
This is a desk study. Each line must be confirmed against the client's installed versions and licences; several
interfaces are separately licensed or need a server component installed.

Background: Hexagon spun off its Asset Lifecycle Intelligence business as **Octave** (distribution completed
28 May 2026). Product names are changing: Smart 3D → Octave Forte 3D, Smart P&ID → Octave Facets P&ID, HxGN SDx →
Octave InConcert Core, SDx2 → Octave InConcert. Documentation still sits at docs.hexagonppm.com.

## Access classes

| Class | Meaning for an agent |
|---|---|
| A. Web API (REST/OData) | An agent can call it through a service account. Best fit: scoped, auditable, server-side. |
| B. Desktop automation (COM/.NET) | Needs a licensed Windows workstation or VM running the application. Good for batch jobs; awkward for always-on agents. |
| C. File or database route | Batch import/export files, neutral files or direct SQL. Reliable, but no business rules unless you add them. |
| D. Documents only | No documented interface. Agents work from exported reports and issued documents. |

## By system

| System | Class | What is exposed | Read | Write | Events | Notes |
|---|---|---|---|---|---|---|
| Smart Instrumentation (SI) | A + C | Web API (OData v4 through Smart API Manager); Import Utility; SQL Server/Oracle database | Yes | Yes (Web API 2.x; earlier versions read-only) | No | Check the Web API version installed |
| Smart Electrical (SPEL) | A + C | Web API (OData v4): GET and PATCH on items and relationships, PDF download of cable block diagrams | Yes | Update of properties | No | Some OData operators unsupported |
| Smart P&ID (SPID) | A + C | Web API (OData, Smart API Manager): retrieve, update, relationships; import from reports; SI can read the SPID database directly | Yes | Yes | No | Drawing graphics stay in the client |
| Smart 3D (S3D) | A + B | Web API (OData) for model entities, mainly read, some actions; .NET API for in-process automation; reports and drawing extraction | Yes | Limited by Web API; full by .NET | No | Model writes should stay with designers |
| SPF / SDx / InConcert | A | Read-write OData APIs with OAuth 2.0; InConcert Assistant is Octave's own AI assistant over documents, data and models | Yes | Yes | Workflow-driven | Only as useful as what is published into it today |
| Smart Completions | A | Smart APIs on OData v4 with OAuth 2.0: assets, location and process breakdown, punch lists | Yes | Check version | No | Smart API use needs its own licence |
| HYSYS | B | COM automation: open cases, read and set streams and operations, run, save; community Python wrappers | Yes | Yes (case inputs) | No | Windows and a HYSYS licence per running instance |
| Flare / relief tool (Aspen Flare System Analyzer) | D / C | Imports from HYSYS and Aspen Plus; no documented automation found | Exports | No | No | Confirm with AspenTech |
| HTRI Xchanger Suite | B | HTRI Automation Server (COM/OLE, .NET): load case, change inputs, run, read outputs; parametric study tool in Excel | Yes | Yes (case files) | No | Documentation behind HTRI member login |
| CAESAR II | C | Neutral file (.cii) both ways, batch mode from the command line; PCF import from S3D | Yes (files) | Yes (files) | No | No scripting API found |
| Mechanical calc tool (PV Elite or equal) | D / C | Reports to Excel, Word and PDF; no documented API found | Exports | No | No | Confirm the tool and version in use |
| Tekla Structures | B | Tekla Open API (.NET): model and drawing objects; Trimble Connect API for cloud models | Yes | Yes | No | Needs a running Tekla instance |
| ETAP | B | etapPy (Python): run studies in batch, read project data and results, local or remote instances; bidirectional SPEL interface | Yes | Studies and results | No | etapPy is a licensed module |
| PHA tool (PHA-Pro or equal) | D / C | Exports to Excel and Word; no documented API found | Exports | No | No | Confirm the tool in use |
| Document Locator | B + C | SDK-API (import, check-in, check-out, view, search, workflow start); ODBC dynamic properties; SQL Server database; web client | Yes | Yes | Workflow | Ask ColumbiaSoft for the SDK reference |
| Purchasing DB (in-house SQL) | C | Your own database; add views and stored procedures as the agent interface | Yes | Yes (your rules) | You build them | The easiest system to open up, because you own it |
| Jovix | A | Jovix Connect API framework; existing connectors for P6 and for PO, shipment and receipt exchange with Smart Materials | Yes | Yes (PO and shipment loads) | Check | API reference available from Hexagon or Jovix |
| P6 | A + B | SOAP web services (read and write); Java/Pro API on premises; REST data service read-only (cloud); XML import | Yes | Yes (SOAP, API, XML) | No | Writes should go through a scheduler's approval |
| iConstruct | B | No public iConstruct API found; Navisworks .NET API underneath; imports from P6 and model properties | Through Navisworks | Through Navisworks | No | Confirm with Hexagon |
| Procore | A | REST API with OAuth, webhooks per project, Helix AI with Agent Builder (open beta) and prebuilt RFI and daily-log agents | Yes | Yes | Webhooks | Only community MCP servers exist; a company admin installs the app |
| DCS / SIS configuration | C | Vendor bulk-configuration tools (Excel/CSV) | Exports | Never by an agent | No | Safety-critical; read and compare only |
| Excel / Word | C | Office file formats; Microsoft Graph if files live in SharePoint or OneDrive | Yes | Yes | SharePoint events | Where most unstructured data lives today |

## What this means for the agents and integrations

- **Ready for agents now (class A, read):** SI, SPEL, SPID, S3D (read), SPF/SDx, Smart Completions, P6, Procore,
  Jovix and your purchasing database. Four of the five wave 1 agents only need Document Locator reads plus these.
- **Batch, not live (class B):** HYSYS, HTRI, ETAP, Tekla and S3D .NET run on licensed Windows machines. Schedule
  them as jobs (export after each case or model revision) and let agents read the outputs.
- **Documents only (class D):** the relief tool, the vessel calculation tool and the PHA tool. Here the Drawing
  and P&ID reader and the Vendor document reviewer patterns apply: agents read exports, not the tool.
- **Write access:** keep agent writes to status and register fields (purchasing database, Jovix, P6 through
  approval, Procore drafts). Engineering tool writes stay with people or with reviewed batch loads.
- **Event triggers:** only Procore (webhooks), Document Locator and SPF workflows, and your own database can push
  events. Everything else is polled on a schedule.
- **Build one gateway:** wrap each system's API in a small service (for example an MCP server per system)
  with read-only scopes first and its own audit log. Agents call the gateway, never the tools directly.

## Sources

- Octave separation: https://investors.hexagon.com/share-information/octave-separation
- Product renames: https://www.cortexsoftware.com.au/blog/hexagons-software-spin-off-to-octave
- InConcert Assistant: https://www.octave.com/products/engineering-information-management/inconcert/assistant
- SI Web API: https://docs.hexagonppm.com/r/en-US/Intergraph-Smart-Instrumentation-Web-API-Release-Bulletin/Version-2.3.7/917202
- SPEL Web API: https://docs.hexagonppm.com/r/en-US/Intergraph-Smart-Electrical-Web-API-Release-Bulletin/Version-2.0.2/986087
- SPID Web API: https://docs.hexagonppm.com/r/en-US/Intergraph-Smart-P-ID-Web-API-Release-Bulletin/2.0.7/964193
- S3D Web API: https://docs.hexagonppm.com/r/en-US/Intergraph-Smart-3D-and-Smart-3D-Admin-Web-API-Installation-and-Configuration/Version-13/887112
- Hexagon OData APIs (SPF): https://hexagon.com/company/divisions/asset-lifecycle-intelligence/technology-compliance-standards/odata-api
- Smart Completions Smart API: https://docs.hexagonppm.com/r/en-US/Intergraph-Smart-Completions-Smart-API-Programmer-s-Getting-Started-Guide-5.3.19/5.3.19/1297392
- HTRI Automation Server: https://www.htri.net/techtip--using-the-htri-automation-server
- CAESAR II neutral file: https://docs.hexagonppm.com/r/LQZqZhXO_I9kILLMx0SxPw/lG30eJO~PywI3_bNGPtK4g
- Tekla Open API: https://developer.tekla.com/tekla-structures
- etapPy: https://etap.com/product/etappy ; ETAP–SPEL interface: https://etap.com/product/smartplant-electrical-interface
- Document Locator SDK-API: https://www.documentlocator.com/?p=3644
- Jovix: https://ineight.com/integration/jovix/ ; Smart Materials–Jovix connector: https://docs.hexagonppm.com/r/en-US/HxGN-Smart-Materials-Connector-for-Jovix-10.2/Version-10.2/1414724
- P6 web services: https://docs.oracle.com/cd/G18294_01/102089.htm
- Procore Helix and Agent Builder: https://www.businesswire.com/news/home/20251015796723/en/Procore-Advances-the-Future-of-Construction-with-New-AI-Innovations-at-Groundbreak-2025
- iConstruct: https://docs.hexagonppm.com/p/iConstruct
- HYSYS automation (community): https://cacklingtanuki.codeberg.page/aspen-pysys
