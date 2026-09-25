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
    {
      title: "Decarbonising the Bündner Rheintal",
      place: "Canton of Graubünden, Switzerland",
      years: "2023 – 2025",
      tags: ["Regional planning", "Industry", "Net zero 2050"],
      summary:
        "ehubX modelled the energy system of the Bündner Rheintal, a region with heavy industry. The team built a model of the current system, calibrated it against historical data, and then searched for pathways to net zero by 2050. Three measures stood out: efficient electrification, carbon capture and storage, and using industrial waste heat. Together they could reach the target while cutting system costs by 20–40 %.",
      partners: "Canton of Graubünden, regional energy providers and industry (Round Table Energiesystem Bündner Rheintal)",
      links: [
        { label: "ETH Energy Blog article", url: "https://energyblog.ethz.ch/bundner-rheintal/" },
        { label: "Canton press release", url: "https://www.gr.ch/DE/Medien/Mitteilungen/MMStaka/2025/Seiten/2025011501.aspx" },
      ],
    },
    {
      title: "Net-zero planning for ESP Sisslerfeld",
      place: "Canton of Aargau, Switzerland",
      years: "",
      tags: ["Industrial area", "Sector coupling", "Load shifting"],
      summary:
        "Sisslerfeld is a development area spanning the municipalities of Eiken, Münchwilen, Sisseln and Stein. The project set up a continuous, integrated planning process to reach net-zero CO₂ by 2040 at the lowest cost, using synergies between industry, households and energy infrastructure. ehubX's load-shifting features were extended for this project.",
      partners: "",
      links: [],
      todo: true,
    },
    {
      title: "District heating with high-temperature aquifer storage (Bispebjerg)",
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
      type: "Preprint",
      year: 2025,
      title: "Decarbonisation pathways for the Bündner Rheintal energy system",
      authors: "Mutschler, R., Upadhyay, A., et al.",
      venue: "SSRN preprint 5291581",
      url: "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5291581",
      todo: true, // confirm exact title and author list
    },
    {
      type: "Conference paper",
      year: 2017,
      title: "The Ehub Modeling Tool: A flexible software package for district energy system optimization",
      authors: "Bollinger, L. A., Dorer, V.",
      venue: "Energy Procedia 122 (CISBAT 2017) — predecessor of ehubX",
      url: "https://doi.org/10.1016/j.egypro.2017.07.402",
      todo: true, // confirm DOI
    },
  ],

  theses: [
    // `level` is "PhD" or "MSc" (also fine: "BSc", "Semester project").
    // `status` is "Completed" or "Ongoing". Replace the placeholders below.
    {
      level: "PhD",
      status: "Ongoing",
      year: "20XX",
      title: "PhD thesis title",
      student: "Student name",
      institution: "University / department",
      supervisors: "Supervisor names",
      url: "",
      todo: true,
    },
    {
      level: "PhD",
      status: "Completed",
      year: "20XX",
      title: "PhD thesis title",
      student: "Student name",
      institution: "University / department",
      supervisors: "Supervisor names",
      url: "",
      todo: true,
    },
    {
      level: "MSc",
      status: "Completed",
      year: "20XX",
      title: "MSc thesis title",
      student: "Student name",
      institution: "University / department",
      supervisors: "Supervisor names",
      url: "",
      todo: true,
    },
    {
      level: "MSc",
      status: "Completed",
      year: "20XX",
      title: "MSc thesis title",
      student: "Student name",
      institution: "University / department",
      supervisors: "Supervisor names",
      url: "",
      todo: true,
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
