# SAR Agent ChatBot

This LLM agent uses tools to connect to external databases [(neon postgres)](https://neon.com/), query customer data to transaction records, analyze the transactions, and file SARs on the activity. The output is strictly structured for integration with other systems.


DB Structure:
![Neon](./screenshot_neon.jpg)


UI:
![SAR Agent](./screenshot.jpg)


## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |
| `uvicorn grok_proxy:app --reload --port 3001` | Run FastAPI                  |

