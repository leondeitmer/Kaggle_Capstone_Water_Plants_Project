# Skills

In diesem Dokument werden alle im Projekt definierten Skills sowie die globalen Skills aufgeführt.

## Projekt-Skills

### [botanical-watering-skill](../skills/botanical-watering-skill/SKILL.md)
*   **Botanisches Regelwerk:** Definiert mathematische Kriterien und botanische Logiken zur Einschätzung des Wasserbedarfs von Pflanzen basierend auf Wetterdaten, Sonnenstunden und Pflanzeneigenschaften.
*   **Referenzdatenbank:** Nutzt die [plant_database.json](../skills/botanical-watering-skill/resources/plant_database.json), um Standardwerte wie den täglichen Wasserverlust (`base_depletion_pct`) und die optimalen täglichen Sonnenstunden (`optimal_sun_hours`) für verschiedene Pflanzenkategorien zu bestimmen.
*   **Bodenfeuchtigkeitsmodell:** Berechnet den täglichen Feuchtigkeitsverlust unter Berücksichtigung von Umgebungstemperatur, Abweichungen der Sonnenstunden vom Optimum, relativer Luftfeuchtigkeit und Regen (falls der Balkon nicht überdacht ist).
*   **Status-Kategorisierung:** Teilt den Zustand in *Healthy* ($\ge 50\%$), *Water Soon* ($25\% - 49\%$) und *Water Now* ($< 25\%$) ein und berechnet darauf basierend den nächsten Gießzeitpunkt.
*   **Deutsche Begründungstexte:** Erstellt prägnante Erklärungen (1–2 Sätze) in deutscher Sprache, welche die Berechnungsgründe verständlich zusammenfassen.
*   **Berechnungsskript:** Verweist auf das ausführbare Python-Skript [moisture_calculator.py](../skills/botanical-watering-skill/scripts/moisture_calculator.py).

### [git-commit-version](../skills/git-commit-version/SKILL.md)
*   **Commit-Namenskonvention:** Erzwingt das Format `<type>: <description>` für reguläre Commits und verlangt ein vorangestelltes Ausrufezeichen `!` für Breaking Changes bzw. spezielle Commits.
*   **Sicherheitsprüfungen vor dem Commit (Pre-Commit-Checks):** Verhindert das Committen von Code, der absolute lokale Pfade oder hartkodierte Zugangsdaten/Geheimnisse (z. B. `GEMINI_API_KEY`) enthält, und stellt sicher, dass `.env` nicht im Git-Index getrackt wird.
*   **Automatisierungsskript:** Verwendet das Helper-Skript [safe_commit.py](../skills/git-commit-version/scripts/safe_commit.py), um diese Prüfungen automatisiert auszuführen und fehlerhafte Commits abzubrechen.

### [prompt-documentation-skill](../skills/prompt-documentation-skill/SKILL.md)
*   **Standardisierte Dokumentation:** Bietet Richtlinien für AI-Agenten zur Erstellung strukturierter Markdown-Logs für Konversationen, Architekturentscheidungen und Projektarchitekturen.
*   **Sprachkonsistenz:** Dokumentationen werden konsequent auf Englisch verfasst, unabhängig von der Sprache der Chat-Diskussion.
*   **Entscheidungs-Rückverfolgbarkeit:** Dokumentiert nicht nur Ergebnisse, sondern auch verworfene Alternativen und Abwägungen (z. B. Speicheroptionen).
*   **Strukturierte Protokollierung:** Definiert eine klare Struktur für Konversationsprotokolle mit Metadaten, Projektübersicht, Diskussionshistorie und der vereinbarten Architektur.
*   **Referenzvorlage:** Nutzt [example_log.md](../skills/prompt-documentation-skill/references/example_log.md) als Referenzvorlage.

### [safety-check-skill](../skills/safety-check-skill/SKILL.md)
*   **Manuelle Sicherheitsprüfung (Chat-Only):** Dient als Quick-Checkliste zur manuellen Verifizierung von Code auf Sicherheitsrisiken vor der Übergabe oder Veröffentlichung.
*   **Sicherheitskriterien:** Prüft auf die Einhaltung relativer Pfade, das Fehlen von Passwörtern, Secrets, API-Keys in den Quelltexten sowie auf nicht getrackte `.env`-Dateien und URLs mit Token-Parametern.
*   **Interaktive Anwendung:** Ermöglicht es dem Entwickler, Code im Chat prüfen zu lassen, woraufhin der Agent gezielte Hinweise auf Sicherheitslücken gibt.

---

## Globale Skills

*   deploy-to-vercel
*   find-skills
*   google-agents-cli-adk-code
*   google-agents-cli-deploy
*   google-agents-cli-eval
*   google-agents-cli-observability
*   google-agents-cli-publish
*   google-agents-cli-scaffold
*   google-agents-cli-workflow
*   vercel-cli-with-tokens
*   vercel-composition-patterns
*   vercel-optimize
*   vercel-react-best-practices
*   vercel-react-native-skills
*   vercel-react-view-transitions
*   web-design-guidelines
*   writing-guidelines
