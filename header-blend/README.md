# Fuel Gas Header Blender (proof of concept)

Standalone demo, separate from the crude-fractionator model. It uses none of
that project's data. Every stream flow and analysis in `index.html` is an
illustrative example value.

Open `index.html` in a browser. Toggle units off, edit flows, and optionally
hold header heat demand with natural gas make-up.

Method: ideal-gas molar mixing, header y_j = sum(F_i * y_ij) / sum(F_i).
LHV at 0 C / 1 atm, Wobbe = LHV / sqrt(SG).

For the client study this would be replaced by historian data per stream
(flow + GC/lab analyses), time alignment, reconciliation against the header
meter/analyser, and a property package if liquids or dew point matter.
