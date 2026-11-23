# Preprint

`main.tex` is the preprint draft. Red boxes mark sections for the author to
write. Every simulation number, the table and figures 1 to 3 are regenerated
from archived trajectories by:

```bash
PYTHONPATH=. python paper/make_figures.py
latexmk -pdf paper/main.tex   # run inside paper/
```

`results/` holds the per-trajectory fits and summaries those numbers come from.
The real-image section waits for the November Al–Ge, Al–Cu and blur analyses
to be pushed, and for the printed-tile test.
