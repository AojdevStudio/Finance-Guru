import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://aojdevstudio.github.io/Finance-Guru",
  base: "/Finance-Guru/",
  integrations: [
    starlight({
      title: "Finance Guru",
      description: "Finance Guru is a local-first financial analysis and automation repository built for a private family office workflow. It combines a typed Python analysis engine, brokerage-data integrations, operational runbooks, and AI-assisted workflows.",
      favicon: "/favicon.svg",
      customCss: ["./src/styles/aoj-docs.css"],
      lastUpdated: true,
      sidebar: [
        {
          label: "Tutorials",
          items: [{ autogenerate: { directory: "tutorials" } }],
        },
        {
          label: "How-to guides",
          items: [{ autogenerate: { directory: "how-to" } }],
        },
        {
          label: "Reference",
          items: [{ autogenerate: { directory: "reference" } }],
        },
        {
          label: "Explanation",
          items: [{ autogenerate: { directory: "explanation" } }],
        },
        {
          label: "Project",
          items: [{ label: "Source repository", link: "https://github.com/AojdevStudio/Finance-Guru" }],
        },
      ],
    }),
  ],
});
