# proofTeX - Tools for proofing LaTeX documents

Yes, now you too can experience the joy of proofreading your work by [changing the font to Comic Sans](https://www.reddit.com/r/LifeProTips/comments/318ilc/lpt_when_reviewing_something_youve_written_change/) and [putting it through text-to-speech](https://www.reddit.com/r/LifeProTips/comments/318ilc/lpt_when_reviewing_something_youve_written_change/cpzblsu)!

## detex.py

Takes a LaTeX document as input and strips LaTeX code in a content-aware manner.

With the `--document` option, processes the entire file without waiting for a `\begin{document}` call (useful, for example, if the file is an extract from a larger work).

With the `--count` option, performs a word count, including text and text-like mathematics, but excluding complex mathematics, figures, footnotes and others.

With the `--tts` option, outputs text in a format suitable for use with a text-to-speech engine. I use [Festival](https://wiki.archlinux.org/index.php/Festival).

Licensed under the GNU Affero General Public License version 3 or later.

## wew.sty

Configures `fontspec` and `unicode-math` to use Comic Sans (or the metric-compatible free font Comic Relief) for all text, with suitable settings to simulate italics and boldface.

Licensed under the Apache License version 2.0.