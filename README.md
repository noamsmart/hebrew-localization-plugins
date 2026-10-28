# Hebrew Localization Plugins

מאגר הפלאגינים **hebrew-localization** כולל את **Hebrew Screen Localization** — זרימת עבודה לתרגום סרטים וסדרות לעברית, הכנת כתוביות RTL, התאמת דיבוב ובקרת איכות.

## התקנה ב-GitHub Copilot

1. פתחו **Settings ← Plugins**.
2. בחרו **Install ← Add marketplace**.
3. הזינו את המאגר:

   ```text
   noamsmart/hebrew-localization-plugins
   ```

4. לאחר שהמאגר נוסף, התקינו את הפלאגין באמצעות המזהה:

   ```text
   hebrew-screen-localization@hebrew-localization
   ```

הפלאגין כולל שרת MCP מקומי המופעל באמצעות Node.js. יכולות התמלול ועיבוד המדיה תלויות בכלי המדיה הזמינים במחשב.

## מבנה המאגר

- `marketplace.json` — קטלוג ה-marketplace.
- `plugins/hebrew-screen-localization/plugin.json` — מניפסט הפלאגין בפורמט Agent Plugins 1.0.
- `plugins/hebrew-screen-localization/mcp.json` — הגדרת שרת ה-MCP המקומי.
- `plugins/hebrew-screen-localization/skills/` — מיומנויות התרגום והלוקליזציה.

## אתר הפלאגין

https://hebrew-localization-noam-sasson.noam-sasson-ph.chatgpt.site/
