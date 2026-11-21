# How many pixels does a growth measurement need?

Django Thompson, gap year, Oxford. Draft for comments, November 2026.

## Summary

If the features in an image are only a pixel or so across, a fitted
coarsening exponent comes out too low. In my 32-run new-seed simulation test
at 0.65 Tc, coarsening the images 4× moved the exponent from 0.23 to 0.18 at
50:50 composition, and from 0.24 to 0.17 at 15:85. That is a drop of between
a fifth and a third, enough to move a diffusion-type 1/3 most of the way
towards the 1/4 expected for grain-boundary diffusion. The usual checks on the
fit often don't catch it.

I wanted to know how many pixels a feature needs before you can trust the fit.
I tested this on simulated alloys, where I know the right answer, and on two
real alloys scanned in 3D as they aged: aluminium–germanium, and an
aluminium–copper semi-solid mixture in a blind test. In sharp images the error
dropped below about 0.01 once features were about two pixels across. Below one
pixel the exponent always read too slow.

The closest existing rule, the resolution criterion of Ledesma-Alonso et al.
(2018), already protects against this: when I applied their full criterion, it
never allowed a coarsening that biased the exponent. So my contribution is not
a new rule. I checked an existing static rule against a known answer for growth
rates, and measured how large the error gets, and how silently, when the rule
is broken.

The project began with a question about entropy and the direction of time from
my EPQ, which led me to simulations of phase separation.

*Figure: error in the measured growth exponent against pixels per domain, for
simulations, Al–Ge images followed over time, and Al–Cu images in the blind
test. To be added to the repository with the November results.*

**How the work was done.** I set the question and the pass/fail standard for
each test, and I checked and can explain every result. An AI assistant proposed
many of the specific tests, wrote the code and ran most of the analysis. The
full record is in `AI_USE_AND_CONTRIBUTIONS.md`.

## Background: why the exponent matters

When you age an alloy at high temperature it can split into two phases, and the
regions of each phase slowly get bigger. Their typical size L grows roughly as
a power of time, L ∝ t^n. If growth is driven by diffusion through the bulk,
the classic answer (Lifshitz–Slyozov–Wagner theory) is n = 1/3. People fit n
from micrographs to work out which mechanism is at play and to predict how the
material will change in service. The images are usually taken at one
magnification, so early on the features can be only a few pixels wide.

## The model

**The alloy.** A square grid where each site holds an A or a B atom. Like
neighbours lower the energy, so below a critical temperature Tc the mixture
separates into A-rich and B-rich regions. This is the 2D Ising model, about the
simplest model of phase separation there is.

**Kawasaki dynamics.** The only move allowed is swapping two neighbouring atoms,
accepted with the usual Metropolis rule. Atoms never appear or disappear, so
the composition stays fixed, like diffusion in a real alloy.

**The quench.** I start from a random mix, drop the temperature to 0.6 or
0.65 Tc (depending on the run set) and let it coarsen. Time is counted in Monte
Carlo sweeps, one attempted move per site. In 2D this model only creeps towards
1/3 (Huse, 1986), so over my time windows the true exponent is somewhere around
0.23–0.33.

**Why simulate.** I know where every atom is, so I have the exact full-resolution
picture. Real experiments never have that. Making realistic coarse images from a
simulation where the truth is known isn't a new trick: it has been used to
measure pixel errors in mechanics models (Rouwane et al., 2021). I haven't found
it used for growth rates.

## The test

At each time I made a lower-resolution copy of the image by averaging k × k
blocks of sites, like a coarser camera would, then turned it back into two
phases. I measured the typical domain size in both images using the two-point
correlation (roughly, how far apart two pixels can be and still usually be in
the same phase) and compared the growth exponents. By pixels per domain I mean
that correlation length divided by the pixel size. It is shorter than a
domain's full width, so at "one pixel per domain" a domain still spans a few
pixels; it just looks blocky.

Splitting the two steps showed where the error comes from. In the 32-run test,
block averaging alone changed the exponent by about −0.001 at 50:50, while
turning the averaged image back into two phases added about −0.054.

Each test and its pass/fail rule were written down before the test was run. An
AI assistant drafted these rules. One real-image test wasn't fully blind; see
the limits below.

## What I found

**Below one pixel, things go badly wrong.** At 4× coarsening the exponent came
out 0.05–0.08 too low, depending on composition. At 8× it was about 0.11 too
low.

**From about two pixels up, the simulations were fine** and the error stayed
under 0.01. A curve fitted on earlier runs predicted 32 new runs (new seeds, a
box twice as big) to within 0.01, and longer runs out to 6 million sweeps gave
about 0.001 at 2–5 pixels.

**The real images behaved the same way once I followed them over time.** I used
68 slices of a public 3D X-ray scan of an Al–Ge alloy aged at 375 °C for 15 to
315 minutes (Fell, 2023). Below one pixel the exponent was about 0.09 too low,
at about one pixel 0.02, and at 1.5–3 pixels only about 0.001. Coarsening a
single image further, instead of following the images over time, put the error
at 2–4 pixels at about 0.015 and suggested you'd need four pixels. That
single-image check agrees with the full method on the simulations but overstates
the error on these real images. It is good at showing whether a length is
sensitive to resolution, which is what my audit tool does, but it is not
accurate enough to predict the error in a growth rate.

**A second real material showed the same pattern in a blind test.** I wrote the
rules down before downloading anything, then used six scans of a published
time-resolved X-ray series of a semi-solid Al–Cu mixture, part solid and part
liquid, coarsening at constant temperature (Gibbs, Voorhees and Fife). At 3–6
pixels per domain the error was about 0.001, at about two pixels 0.010, at about
one pixel 0.025, and below one pixel 0.08 to 0.16. Cutting the slices the other
way gave the same picture. Whether the single-image check overstates the error
there depends on which way I slice. This microstructure is known to coarsen as
t^(1/3) without being self-similar (Sun et al., 2018), which may be why the
single-image check behaves differently on it.

**The size measure matters too.** With mean intercept length, growth could look
faster rather than slower. That came from single-pixel thermal noise in the
full-resolution images, and in a colder simulation with about seven times less
noise it went away, as I'd predicted beforehand.

**Blur raises the bar.** When I added blur to both real datasets before
coarsening, the exponent always read slower, never faster. At three pixels or
more, even a full pixel of blur kept the error near 0.01. At about two pixels,
half a pixel of blur pushed it to about 0.006 on Al–Ge and 0.017 on Al–Cu, and
a full pixel made it 0.03 to 0.04. Random noise on its own hardly mattered. So
the rule is closer to two pixels for sharp images and three or more for blurry
ones.

## Isn't this obvious?

Partly. That coarse images lose detail and get sizes wrong is well known (for
example Ledesma-Alonso et al., 2018; Zabler et al., 2007). Two-point
correlations have already been used to describe coarsening in the same Al–Cu
dataset I used (Sun et al., 2017); that work characterises the microstructure,
while I ask how much resolution biases the fitted growth rate. Coarse-graining
this same lattice model into blocks has even been used on purpose, to estimate
the exponent by renormalisation (Roland and Grant, 1988). That method compares
coarse pictures from different times, though. It doesn't measure the error a
coarse camera adds to an ordinary fit.

Existing practice is already cautious: people drop features smaller than about
ten pixels in EBSD, or a few voxels in tomography (Werz et al., 2014), and
Ledesma-Alonso et al. give a resolution criterion for image statistics. Their
criterion is set by the correlation length, and they lowered resolution by
decimation, not by block averaging and thresholding as I did. With all three of
their descriptors it asks for roughly 1.2 to 1.9 pixels per domain in my units,
close to my own two-pixel figure, and it never let a biased case through. A
cut-down version without their pore-size descriptor was far too lenient on the
real images, and plain 2 × 2 averaging let one biased case through.

What I add is the practical side: the size of the error in a fitted exponent
when these rules are broken, and the fact that it is easy to miss. Below one
pixel the error moves 1/3 more than halfway to 1/4, and in the simulations the
usual fit checks passed 43% of badly biased fits. I haven't found a study that
answers this question, but I could easily have missed one and would be glad to
be pointed to it.

## Why it matters in practice

Coarsening exponents get used to work out the mechanism (about 1/3 for bulk
diffusion, 1/4 for grain-boundary diffusion, 1/5 along dislocations) and to
predict how parts age in service, for example γ′ precipitates in turbine-blade
superalloys or Fe–Cr steels. An error this size could send you to the wrong
mechanism, and the earliest images, where features are smallest, are the ones
at risk. The check is cheap: measure pixels per feature before fitting and be
suspicious of anything under about two, or more if the images are blurry.

## What I am less sure about

- The real-image results rest on two samples, a solid-state Al–Ge alloy and a
  semi-solid Al–Cu mixture, both seen in 2D slices of 3D scans. In the Al–Cu
  test only one coarsening level stayed clearly above two pixels, so it supports
  the threshold rather than pinning it down.
- Following the real images over time used only four time points for Al–Ge, and
  the slices don't line up between times, so treat those numbers as rough.
- The Al–Ge over-time test wasn't blind: rough numbers from these images had
  been seen before its rules were written.
- I threshold the coarse image so it keeps the original phase fraction, which a
  real user doesn't know. Blind thresholding (for example Otsu's method) still
  needs testing.
- The simulations are 2D, with sharp images, at three temperatures and three
  compositions, and they aren't calibrated to any real alloy.

## What I'd do with more data

The most useful next step is an ageing series of one solid-state alloy: the
same material imaged at several ageing times (ideally five or more), at a
magnification where the features are well resolved, so I can coarsen the
images myself. SEM images of γ′ precipitates in a nickel superalloy would be
ideal, but any two-phase coarsening series would work. I would follow growth
over time at full resolution and after coarsening by 2×, 4× and 8×, compare the
fitted exponents, and write the pass and fail rules down before looking. I'd
keep any images private and only publish aggregate numbers, unless the owner
agrees otherwise.

## Questions

1. Is the two-point correlation length the right size measure for growth
   measured from micrographs, or would you trust something else, such as
   particle size from segmentation?
2. Most of the bias comes from turning the coarse image back into two phases,
   not from the averaging. Is there anything in how real microscopes or
   segmentation pipelines work that would make that step better or worse than
   my version?
3. In your work, are growth rates ever fitted from images where features are
   only a few pixels across, for example at the earliest ageing times?
4. Do you know of a time series of images (one alloy at several ageing times)
   that I could test this on?

## References

- Fell (2023). Segmented X-ray tomography of solid-state-aged Al–Ge. Mendeley
  Data, doi:10.17632/hj9njz3rxp.1 (CC BY 4.0).
- Gibbs, J. W., Voorhees, P. W. & Fife, J. L. Liquid–solid metallic mixture
  coarsening data, Materials Data Facility, doi:10.18126/M2CC73. Segmentation
  method: Gibbs & Voorhees (2014), Integr. Mater. Manuf. Innov. 3, 6.
- Huse, D. A. (1986). Corrections to late-stage behavior in spinodal
  decomposition. Phys. Rev. B 34, 7845.
- Ledesma-Alonso, R. et al. (2018). Effect of the image resolution on the
  statistical descriptors of heterogeneous media. Phys. Rev. E 97, 023304.
- Lifshitz, I. M. & Slyozov, V. V. (1961). J. Phys. Chem. Solids 19, 35.
  Wagner, C. (1961). Z. Elektrochem. 65, 581.
- Roland, C. & Grant, M. (1988). Monte Carlo renormalization-group study of the
  late-stage dynamics of spinodal decomposition. Phys. Rev. Lett.
- Rouwane, A. et al. (2021). Adjusting fictitious domain parameters for fairly
  priced image-based modeling: application to the regularization of digital
  image correlation. Comput. Methods Appl. Mech. Eng.
- Sun, Y., Cecen, A., Gibbs, J. W., Kalidindi, S. R. & Voorhees, P. W. (2017).
  Analytics on large microstructure datasets using two-point spatial
  correlations: coarsening of dendritic structures. Acta Mater. 132, 374–388.
- Sun, Y. et al. (2018). Scientific Reports, doi:10.1038/s41598-018-36354-8
  (two-point correlations of interfacial curvature in coarsening Al–Cu;
  full title to be added).
- Werz, T. et al. (2014). Particle tracking during Ostwald ripening using
  time-resolved laboratory X-ray microtomography. Mater. Charact. 90, 185.
- Zabler, S. et al. (2007). Acta Materialia, doi:10.1016/j.actamat.2007.05.028.
