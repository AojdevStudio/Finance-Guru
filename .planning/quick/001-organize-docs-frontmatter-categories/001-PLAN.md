---
phase: quick
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/CONTRIBUTING.md
  - docs/setup/SETUP.md
  - docs/setup/api-keys.md
  - docs/setup/TROUBLESHOOTING.md
  - docs/guides/broker-csv-export-guide.md
  - docs/guides/required-csv-uploads.md
  - docs/reference/api.md
  - docs/reference/hooks.md
  - docs/reference/tools.md
  - docs/reports/codex-full-review-report.md
  - docs/reports/onboarding-flow-evaluation.md
  - docs/reports/pre-codex-validation-report.md
  - docs/reports/MANUAL_TEST_CHECKLIST.md
  - docs/index.md
autonomous: true

must_haves:
  truths:
    - "Only CONTRIBUTING.md exists at docs/ root level (besides index.md)"
    - "All markdown files have YAML frontmatter with title, description, category"
    - "Files are organized into logical subdirectories by purpose"
    - "Index.md links to all categorized documents"
    - "Internal links between docs are updated and functional"
  artifacts:
    - path: "docs/CONTRIBUTING.md"
      provides: "Contribution guidelines at root"
    - path: "docs/setup/"
      provides: "Setup and configuration docs"
    - path: "docs/guides/"
      provides: "User guides and walkthroughs"
    - path: "docs/reference/"
      provides: "Technical reference docs"
    - path: "docs/reports/"
      provides: "Evaluation and review reports"
    - path: "docs/index.md"
      provides: "Documentation hub with links to all categories"
  key_links:
    - from: "docs/index.md"
      to: "all categorized docs"
      via: "relative links"
    - from: "docs/setup/SETUP.md"
      to: "docs/setup/api-keys.md"
      via: "internal link"
---

<objective>
Reorganize the docs/ folder with proper YAML frontmatter, logical category subdirectories, and an updated index.

Purpose: Improve documentation discoverability and maintainability by organizing docs into clear categories with consistent metadata.

Output: Restructured docs/ with only CONTRIBUTING.md at root, all other docs in category subdirs (setup/, guides/, reference/, reports/), each with YAML frontmatter, and updated index.md linking to all docs.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@docs/index.md
@docs/contributing.md
@docs/SETUP.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create category directories and move files with frontmatter</name>
  <files>
    docs/CONTRIBUTING.md
    docs/setup/SETUP.md
    docs/setup/api-keys.md
    docs/setup/TROUBLESHOOTING.md
    docs/guides/broker-csv-export-guide.md
    docs/guides/required-csv-uploads.md
    docs/reference/api.md
    docs/reference/hooks.md
    docs/reference/tools.md
    docs/reports/codex-full-review-report.md
    docs/reports/onboarding-flow-evaluation.md
    docs/reports/pre-codex-validation-report.md
    docs/reports/MANUAL_TEST_CHECKLIST.md
  </files>
  <action>
    1. Create category directories: `mkdir -p docs/{setup,guides,reference,reports}`

    2. Move and add frontmatter to each file:

    **Root (rename only):**
    - `contributing.md` -> `CONTRIBUTING.md` (add frontmatter: title, description, category: root)

    **setup/** (installation and configuration):
    - `SETUP.md` -> `setup/SETUP.md`
    - `api-keys.md` -> `setup/api-keys.md`
    - `TROUBLESHOOTING.md` -> `setup/TROUBLESHOOTING.md`

    **guides/** (user walkthroughs):
    - `broker-csv-export-guide.md` -> `guides/broker-csv-export-guide.md`
    - `required-csv-uploads.md` -> `guides/required-csv-uploads.md`

    **reference/** (technical reference):
    - `api.md` -> `reference/api.md`
    - `hooks.md` -> `reference/hooks.md`
    - `tools.md` -> `reference/tools.md`

    **reports/** (evaluations and reports):
    - `codex-full-review-report.md` -> `reports/codex-full-review-report.md`
    - `onboarding-flow-evaluation.md` -> `reports/onboarding-flow-evaluation.md`
    - `pre-codex-validation-report.md` -> `reports/pre-codex-validation-report.md`
    - `MANUAL_TEST_CHECKLIST.md` -> `reports/MANUAL_TEST_CHECKLIST.md`

    3. Add YAML frontmatter to each file:
    ```yaml
    ---
    title: "Document Title"
    description: "Brief description of document purpose"
    category: setup|guides|reference|reports
    ---
    ```

    4. Keep existing subdirs untouched: csv-mappings/, images/, solutions/
  </action>
  <verify>
    - `ls docs/*.md` shows only CONTRIBUTING.md and index.md
    - `ls docs/setup/` shows 3 files
    - `ls docs/guides/` shows 2 files
    - `ls docs/reference/` shows 3 files
    - `ls docs/reports/` shows 4 files
    - `head -5 docs/setup/SETUP.md` shows YAML frontmatter
  </verify>
  <done>All docs moved to category subdirs with YAML frontmatter, only CONTRIBUTING.md remains at root</done>
</task>

<task type="auto">
  <name>Task 2: Update index.md and fix internal links</name>
  <files>
    docs/index.md
    docs/setup/SETUP.md
    docs/setup/TROUBLESHOOTING.md
    docs/reference/api.md
    docs/CONTRIBUTING.md
  </files>
  <action>
    1. Rewrite docs/index.md to serve as documentation hub:
       - Add YAML frontmatter (title, description, category: root)
       - Create sections for each category with links to all docs
       - Structure: Setup, Guides, Reference, Reports, Resources (csv-mappings, solutions)
       - Use relative paths from index.md location (e.g., `setup/SETUP.md`)

    2. Update internal links in moved files:
       - SETUP.md: Update links to api-keys.md, TROUBLESHOOTING.md (now same directory)
       - SETUP.md: Update link to contributing.md -> ../CONTRIBUTING.md
       - TROUBLESHOOTING.md: Update any links to other docs
       - api.md: No changes needed (external refs only)
       - CONTRIBUTING.md: Update link to docs/api.md -> reference/api.md

    3. Verify no broken links:
       - Check all relative paths are correct after move
       - Ensure image links still work (../images/ from subdirs)
  </action>
  <verify>
    - `grep -l "SETUP.md\|api-keys.md\|hooks.md" docs/index.md` returns docs/index.md (has links)
    - `grep "contributing.md" docs/setup/SETUP.md` returns empty (old link removed)
    - `grep "CONTRIBUTING.md" docs/setup/SETUP.md` returns match (new link works)
  </verify>
  <done>Index.md links to all categorized docs, internal links updated to reflect new structure</done>
</task>

</tasks>

<verification>
1. Only CONTRIBUTING.md and index.md at docs/ root: `ls docs/*.md`
2. All category dirs exist with files: `ls docs/{setup,guides,reference,reports}/`
3. Frontmatter present: `head -5 docs/setup/SETUP.md docs/guides/broker-csv-export-guide.md`
4. Index has all categories: `grep -E "^## " docs/index.md`
5. Existing subdirs preserved: `ls docs/{csv-mappings,images,solutions}/`
</verification>

<success_criteria>
- docs/ root contains only: CONTRIBUTING.md, index.md
- 4 category directories created: setup/, guides/, reference/, reports/
- All 12 moved files have YAML frontmatter with title, description, category
- index.md links to all docs organized by category
- Internal links updated (no broken references)
- Existing subdirs (csv-mappings/, images/, solutions/) unchanged
</success_criteria>

<output>
After completion, create `.planning/quick/001-organize-docs-frontmatter-categories/001-SUMMARY.md`
</output>
