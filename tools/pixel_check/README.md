# Pixel check

A single-page browser tool that flags coarsening-exponent fits at risk from
image resolution. It measures the two-point correlation length in pixels (the
same half-height estimator as `research/imaging.image_length`), bands it
against this project's evidence, and for an ageing series refits the exponent
after a further 2× coarsening. Images never leave the browser.

Build: `python tools/pixel_check/build.py` (writes `index.html` with the
embedded example series). `tests/test_pixel_check_tool.py` checks that the
page's JavaScript reproduces the Python lengths exactly, using Node.

Not validated by any laboratory; see the Limits section on the page.
