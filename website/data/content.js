/*
 * Editable content for the ehubX website.
 *
 * Add, remove or reorder entries below — no HTML knowledge needed.
 * Entries marked `todo: true` are placeholders that still need to be
 * checked/completed by the team; they are shown with a "draft" badge.
 * Delete the `todo` line once an entry is verified.
 */

window.EHUBX_CONTENT = {
  projects: [
    // `status` is "Ongoing" or "Completed" ("" to hide). Listed in this order.
    {
      title: "Energiesystem Bündner Rheintal 2050",
      status: "Ongoing",
      place: "Canton of Graubünden, Switzerland",
      years: "Phase I completed · Phase II ongoing",
      tags: ["Regional planning", "Industry", "Net zero 2050"],
      summary:
        "ehubX modelled the energy system of the Bündner Rheintal, a region with heavy industry. The team built a model of the current system, calibrated it against historical data, and then searched for pathways to net zero by 2050. Three measures stood out: efficient electrification, carbon capture and storage, and using industrial waste heat. Together they could reach the target while cutting system costs by 20–40 %. Phase II is now looking for transition pathways that hold up under uncertainty.",
      partners: "Canton of Graubünden, regional energy suppliers and industry",
      links: [
        { label: "Paper in Joule (2026)", url: "https://doi.org/10.1016/j.joule.2026.102533" },
        { label: "ETH Energy Blog article", url: "https://energyblog.ethz.ch/bundner-rheintal/" },
        { label: "Canton press release", url: "https://www.gr.ch/DE/Medien/Mitteilungen/MMStaka/2025/Seiten/2025011501.aspx" },
      ],
    },
    {
      title: "SWEET ACHIEVE: net zero for hard-to-abate sectors",
      status: "Ongoing",
      place: "Switzerland",
      years: "",
      tags: ["Industry", "Cement & waste", "Carbon removal"],
      summary:
        "Some industries, such as cement and waste treatment, are especially hard to decarbonise. ACHIEVE links the regional Rheintal model with the national SwissX model to study how prices for carbon dioxide removal and emissions trading shape their transition.",
      partners: "Empa-led consortium, funded by the Swiss Federal Office of Energy (SWEET programme)",
      links: [{ label: "Project website", url: "https://www.sweet-achieve.ch/" }],
    },
    {
      title: "SWEET reFuel.ch: renewable fuels and chemicals",
      status: "Ongoing",
      place: "Switzerland",
      years: "",
      tags: ["Renewable fuels", "Power-to-X", "Robust pathways"],
      summary:
        "reFuel.ch explores how Switzerland can supply itself with renewable fuels and chemicals. ehubX helps identify transition pathways that remain a good choice even when future prices, technologies and demand are uncertain.",
      partners: "Empa-led consortium, funded by the Swiss Federal Office of Energy (SWEET programme)",
      links: [{ label: "Project website", url: "https://www.sweet-refuel.ch/" }],
    },
    {
      title: "SwissX: an open model of the Swiss energy system",
      status: "Ongoing",
      place: "Switzerland",
      years: "",
      tags: ["National scale", "All sectors", "CCUS"],
      summary:
        "SwissX is a complete, open-source model of the Swiss energy system built with ehubX. It covers all sectors and the full chain of carbon capture, use, transport and storage, and is used to study how energy, carbon and materials interact. A publication is in preparation.",
      partners: "",
      links: [],
    },
    {
      title: "GOES: geothermal-based optimised energy systems",
      status: "Ongoing",
      place: "International · Swiss case: Empa campus, Dübendorf",
      years: "",
      tags: ["Geothermal", "Seasonal storage", "ATES"],
      summary:
        "GOES develops a standard, transferable way to design energy systems around geothermal energy, from the underground up to whole cities. The seasonal aquifer storage (ATES) module of ehubX was developed in this project. In Switzerland, high-temperature borehole storage is being integrated into the energy hub of the Empa campus in Dübendorf.",
      partners: "Funded by GEOTHERMICA, an ERA-NET Cofund under Horizon 2020",
      links: [
        { label: "Project website", url: "https://www.goes-project.info/" },
        { label: "GOES-CH (ARAMIS)", url: "https://www.aramis.admin.ch/Grunddaten/?ProjectID=51356&Sprache=en-US" },
      ],
    },
    {
      title: "Resilient aviation fuel supply for critical infrastructure",
      status: "Ongoing",
      place: "Switzerland",
      years: "",
      tags: ["Resilience", "Fuels", "Security of supply"],
      summary:
        "Together with armasuisse, the team is identifying options to keep critical infrastructure supplied with aviation fuel, even during supply disruptions.",
      partners: "armasuisse",
      links: [],
    },
    {
      title: "periASTY: energy communities in peri-urban areas",
      status: "Ongoing",
      place: "Europe · 9 Living Labs, incl. Sisslerfeld (Switzerland)",
      years: "",
      tags: ["Energy communities", "Sufficiency", "Living Labs"],
      summary:
        "Areas on the edge of cities often fall between urban and rural planning. periASTY helps them join Europe's climate-neutral transition through local renewable energy communities. The team builds optimisation models, assesses sufficiency measures that reduce demand and emissions, and feeds the results into system design and governance.",
      partners: "Horizon Europe / State Secretariat for Education, Research and Innovation (SERI)",
      links: [{ label: "Project website", url: "https://periasty.eu/" }],
    },
    {
      title: "Pol4PED: policies for Positive Energy Districts",
      status: "Ongoing",
      place: "Zurich · Vienna · Groningen",
      years: "",
      tags: ["Positive Energy Districts", "Policy", "Urban regeneration"],
      summary:
        "Positive Energy Districts produce more renewable energy than they use. Pol4PED develops policy mixes that help existing urban areas become one, combining technical, economic, legal and social aspects, with case studies in Zurich, Vienna and Groningen.",
      partners: "Driving Urban Transitions (DUT) / Swiss National Science Foundation (SNSF)",
      links: [{ label: "Project website", url: "https://www.pol4ped.eu/" }],
    },
    {
      title: "HEATWISE: waste heat from edge data centres",
      status: "Ongoing",
      place: "Europe · demonstrator at Empa NEST",
      years: "",
      tags: ["Waste heat", "Data centres", "Buildings"],
      summary:
        "Small data centres inside buildings produce a lot of heat. HEATWISE develops a self-running system that links buildings and edge data centres so this heat can be recovered and reused. A 20 kW edge data centre with hybrid liquid and air cooling is being demonstrated at Empa's NEST building.",
      partners: "Horizon Europe",
      links: [{ label: "Project website", url: "https://heatwise.eu/" }],
    },
    {
      title: "SWEET DecarbCH: decarbonising heating and cooling",
      status: "Ongoing",
      place: "Switzerland · case study Fraumünster, Zurich",
      years: "",
      tags: ["District heating", "Cooling", "Local energy planning"],
      summary:
        "DecarbCH aims to speed up and de-risk the switch to renewable heating and cooling in homes, services and industry. Empa contributes local energy planning for future thermal networks, a detailed assessment of the Fraumünster district heating system in Zurich, and guidelines for combined heating and cooling networks.",
      partners: "Funded by the Swiss Federal Office of Energy (SWEET programme)",
      links: [{ label: "Project website", url: "https://www.sweet-decarb.ch/" }],
    },
    {
      title: "SWEET PATHFNDR: pathways for renewable energy integration",
      status: "Ongoing",
      place: "Switzerland",
      years: "",
      tags: ["Transition pathways", "Renewables", "Policy"],
      summary:
        "PATHFNDR develops and analyses pathways for integrating renewable energy in Switzerland. It delivers feasible transition paths, planning and operation tools, pilot projects, and analyses of business opportunities and policies.",
      partners: "Hosted by ETH Zurich with Empa, PSI, ZHAW, HSLU, UNIGE, EPFL and TU Delft, plus 25 cooperation partners",
      links: [{ label: "Project website", url: "https://sweet-pathfndr.ch/" }],
    },
    {
      title: "NCCR Automation",
      status: "Ongoing",
      place: "Switzerland",
      years: "",
      tags: ["Automation", "Flexibility", "Prosumers"],
      summary:
        "As more people produce their own electricity, for example with rooftop solar, balancing supply and demand gets harder. This national research centre develops new automation methods, with attention to their social impact, to keep supply reliable in a more decentralised energy system.",
      partners: "Swiss National Science Foundation (SNSF)",
      links: [{ label: "Project website", url: "https://nccr-automation.ch/" }],
    },
    {
      title: "Energiezukunft 2050",
      status: "Completed",
      place: "Switzerland",
      years: "2022",
      tags: ["National scenarios", "Electricity", "Net zero"],
      summary:
        "A study with the Association of Swiss Electricity Companies (VSE) on how Switzerland's energy system could develop to 2050. Its results were an earlier step towards the SwissX model.",
      partners: "Association of Swiss Electricity Companies (VSE)",
      links: [{ label: "Study website", url: "https://www.strom.ch/de/energiezukunft-2050" }],
    },
    {
      title: "District heating with high-temperature aquifer storage (Bispebjerg)",
      status: "",
      place: "Copenhagen, Denmark",
      years: "",
      tags: ["District heating", "Seasonal storage", "ATES"],
      summary:
        "This study sized district-heating components, including heat stored underground in aquifers over the seasons (ATES), for Bispebjerg. The ATES model in ehubX was reworked based on what the team learned here.",
      partners: "",
      links: [],
      todo: true,
    },
  ],

  publications: [
    // Newest first. `type` is one of: "Journal article", "Preprint",
    // "Conference paper", "Report", "Thesis", "Software".
    {
      type: "Journal article",
      year: 2026,
      title: "Charting the path to net-zero via CCS and urban-industrial system integration: A Swiss case study",
      authors: "Upadhyay, A., Sulzer, M., Koirala, B., Obrist, M., Vulic, N., Chen, Y.-C. B., Beermann, D., Jakobsen, E., Mutschler, R.",
      venue: "Joule (2026), 102533",
      url: "https://doi.org/10.1016/j.joule.2026.102533",
    },
    {
      type: "Conference paper",
      year: 2017,
      title: "The Ehub Modeling Tool: A flexible software package for district energy system optimization",
      authors: "Bollinger, L. A., Dorer, V.",
      venue: "Energy Procedia 122, pp. 541–546 (CISBAT 2017) — predecessor of ehubX",
      url: "https://doi.org/10.1016/j.egypro.2017.07.402",
    },
  ],

  theses: [
    // `level` is "PhD", "MSc" or "BSc" (other values like "Semester project" also work).
    // `status` is "Completed" or "Ongoing"; leave "" to hide it.
    {
      level: "PhD",
      status: "Ongoing",
      year: "Since 2024",
      title: "Thesis title to be announced",
      student: "Arijit Upadhyay",
      institution: "ETH Zurich",
      supervisors: "",
      url: "",
    },
    {
      level: "MSc",
      status: "",
      year: "2026",
      title: "System Integration and Optimization of Wind Energy Potentials in Switzerland",
      student: "Xinge Gao (Lele)",
      institution: "ETH Zurich",
      supervisors: "",
      url: "",
    },
    {
      level: "MSc",
      status: "",
      year: "2025",
      title: "Advancing Net-Zero Strategies for Urban Energy Districts Using Energy System Optimization",
      student: "Matthias Vogt",
      institution: "ETH Zurich",
      supervisors: "",
      url: "",
    },
    {
      level: "MSc",
      status: "",
      year: "2024",
      title: "Enhanced Power Plant Flexibility Through Bitcoin Mining",
      student: "Tristan Strobl",
      institution: "ETH Zurich",
      supervisors: "",
      url: "",
    },
    {
      level: "BSc",
      status: "",
      year: "2025–2026",
      title: "Implementation and Validation of Realistic Wind Power Modelling in the ehubX Energy System Framework",
      student: "Laurenz Ebi",
      institution: "ETH Zurich",
      supervisors: "",
      url: "",
    },
  ],

  team: [
    "Dennis Beermann",
    "Leonie Fierz",
    "Andrew Bollinger",
    "Robin Mutschler",
    "Wassim Chedhli",
    "Barton Chen",
    "Binod Prasad Koirala",
    "Julien Marquant",
    "Michael Obrist",
    "Youssef Sherif",
    "Arijit Upadhyay",
    "Mashael Yazdanie",
  ],
};
