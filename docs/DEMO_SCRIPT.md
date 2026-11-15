# Demo script (about 4 minutes)

Before: `python run.py serve`, open http://127.0.0.1:8000, sign out. If an AI provider is configured, ask the question in step 2 once beforehand to confirm it works.

1. **Problem (30 s).** Home page. NASA's fire-in-space results are spread over long reports. CTRL+SPACE makes them searchable and comparable, and only states what a source says.
2. **Ask (60 s).** Click "What is the oxygen margin of safety for PMMA rods?". Show the cited points; click a chip to show the verbatim passage and NTRS link. Then ask "What is the best pizza topping in Cairo?" to show the refusal.
3. **Library (40 s).** Search "PMMA extinction", open the BASS-II sensor paper, show page-numbered passages and the "Open NTRS record" link.
4. **Compare (60 s).** Experiments → tick Material Ignition and Suppression Test, Saffire VI-3, Saffire VI-4 → Compare. Read one warning aloud. Point at a *Not extracted* cell: missing is never zero. Show the chart.
5. **Curation (30 s).** Sign in as admin → Review passages / Audit log. Explain that imported text needs human verification before it can support answers.
6. **Close (20 s).** Not NASA-endorsed; built on public NTRS data; next steps: import the BASS-II Summary Report and enable an AI provider.

Do not claim: NASA endorsement, safety certification, or AI accuracy figures (none have been measured with a real model yet).
