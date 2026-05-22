# Using These Skills

These are standard SKILLS.md folders and ZIP bundles that can be loaded into an AI agent environment that supports Skills. The enablement process is as follows:

1. Ask the host environment to load the skills bundle ZIP (or folder) from its URL (`file:` for local reference) or local path.

2. To install the plugin, place the plugin directory in the `.agents/plugins` directory of your AI agent environment. Activate it by adding its metadata to the `marketplace.json` file in the same directory.
2. Test the skill using the usage example documented in the SKILLS.md file.
3. Add it to a workflow schedule if the skill needs to run in automated form on a daily, weekly, or monthly basis.
