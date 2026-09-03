# Move private data into a Finance Guru instance

## Create the instance

1. Create the local instance.

   ```bash
   uv run --project "<repo>" python -m src.cli.instance_init "<root>" --repo "<repo>"
   ```

2. Check that the instance virtual environment exists.

   ```bash
   test -d "<root>/.venv"
   ```

3. Check that the project link exists.

   ```bash
   test -L "<root>/.claude"
   ```

## Move the data

1. Move the user profile over the empty instance template.

   ```bash
   command mv "<repo>/fin-guru/data/user-profile.yaml" "<root>/user-profile.yaml"
   ```

2. Move the database and each [SQLite](https://www.sqlite.org/) sidecar that exists.

   ```bash
   command mv "<repo>/family_office.db" "<root>/family_office.db"
   command mv "<repo>/family_office.db-wal" "<root>/family_office.db-wal"
   command mv "<repo>/family_office.db-shm" "<root>/family_office.db-shm"
   command mv "<repo>/family_office.db-journal" "<root>/family_office.db-journal"
   ```

3. Move the environment and [SnapTrade](https://snaptrade.com/) routing files.

   ```bash
   command mv "<repo>/.env" "<root>/.env"
   command mv "<repo>/config/snaptrade-accounts.yaml" "<root>/snaptrade-accounts.yaml"
   ```

4. Replace the empty report directory with the nested report archive, then merge the second report archive.

   ```bash
   command rmdir "<root>/reports"
   command mv "<repo>/fin-guru-private/fin-guru/analysis/reports" "<root>/reports"
   command mv "<repo>/fin-guru-private/fin-guru/reports/"* "<root>/reports/"
   ```

5. Move the remaining analysis artifacts.

   ```bash
   command rmdir "<root>/analysis"
   command mv "<repo>/fin-guru-private/fin-guru/analysis" "<root>/analysis"
   ```

6. Move the tickets.

   ```bash
   command rmdir "<root>/tickets"
   command mv "<repo>/fin-guru-private/fin-guru/tickets" "<root>/tickets"
   ```

7. Replace the empty strategy directory with the first strategy archive, then merge the second archive.

   ```bash
   command rmdir "<root>/strategies"
   command mv "<repo>/fin-guru-private/strategies" "<root>/strategies"
   command mv "<repo>/fin-guru-private/fin-guru/strategies/"* "<root>/strategies/"
   ```

8. Move the hedging records.

   ```bash
   command rmdir "<root>/hedging"
   command mv "<repo>/fin-guru-private/hedging" "<root>/hedging"
   ```

9. Move the dividend schedule.

   ```bash
   command mv "<repo>/fin-guru-private/dividend-schedules.yaml" "<root>/dividend-schedules.yaml"
   ```

10. Replace the empty notes directory with the guides, then add the other reference material.

    ```bash
    command rmdir "<root>/notes"
    command mv "<repo>/fin-guru-private/guides" "<root>/notes"
    command mv "<repo>/fin-guru-private/dashboard" "<root>/notes/"
    command mv "<repo>/fin-guru-private/credit-cards" "<root>/notes/"
    command mv "<repo>/fin-guru-private/research" "<root>/notes/"
    command mv "<repo>/fin-guru-private/onboarding-summary.md" "<root>/notes/"
    command mv "<repo>/fin-guru-private/README.md" "<root>/notes/"
    command mv "<repo>/fin-guru-private/INDEX.md" "<root>/notes/"
    command mv "<repo>/.memory/notes/"* "<root>/notes/"
    command mv "<repo>/.dev/meeting-notes/"* "<root>/notes/"
    ```

11. Replace the empty imports directory with portfolio updates, then add transaction and retirement exports.

    ```bash
    command rmdir "<root>/imports"
    command mv "<repo>/notebooks/updates" "<root>/imports"
    command mv "<repo>/notebooks/transactions" "<root>/imports/transactions"
    command mv "<repo>/notebooks/retirement-accounts" "<root>/imports/retirement"
    ```

## Verify the instance

1. Change to the instance directory.

   ```bash
   cd "<root>"
   ```

2. Refresh the local database from the migrated credentials and routing file.

   ```bash
   uv run python -m src.integrations.refresh_all
   ```

3. Print the position and balance tables.

   ```bash
   uv run python -m src.integrations.refresh_all --show
   ```

4. Check the checkout for unexpected untracked files under the moved paths.

   ```bash
   git -C "<repo>" status --short --untracked-files=all
   ```

## Commit the instance

1. Change to the instance directory.

   ```bash
   cd "<root>"
   ```

2. Commit the migrated data and `uv.lock`.

   ```bash
   git add -A && git commit -m "migrate household data from the checkout"
   ```

## Start future sessions from the instance

1. Change to the instance directory before starting a Finance Guru session.

   ```bash
   cd "<root>"
   ```

2. Check the working directory.

   ```bash
   pwd
   ```
