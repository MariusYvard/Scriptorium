"""Cas d'eval du choix de police du preambule LaTeX (theme.py).

Une police nommee par la charte peut exister sur la machine qui redige et
manquer sur celle qui compile. fontspec echoue durement dans ce cas, et le
repli calcule a l'emission ne vaut que pour la machine qui l'a calcule. Ces cas
gardent la parade : la decision est deportee dans le document par
\\IfFontExistsTF, et la mesure de disponibilite reessaie avant d'abandonner.
"""
theme_p = charger("theme.py", "theme_polices")

_CHARTE = {"encre": "#16314E", "fond": "#FFFFFF", "accent": "#C8102E"}


def _preambule(police, titre=None):
    d = dict(_CHARTE, police=police)
    if titre:
        d["police_titre"] = titre
    return theme_p.latex(theme_p.charger(d))


# Une police reputee disponible garde son nom, mais sous garde de compilation.
_sauve = theme_p._polices_installees
theme_p._polices_installees = lambda: {"georgia", "verdana"}
try:
    _p = _preambule("Georgia, serif", "Verdana, sans-serif")
finally:
    theme_p._polices_installees = _sauve

verifier("polices : la police demandee reste le premier choix",
         "\\setmainfont{Georgia}" in _p, f"p={_p[-300:]}")
verifier("polices : le repli est pose dans le document, pas seulement calcule",
         "\\IfFontExistsTF{Georgia}" in _p
         and "\\setmainfont{Latin Modern Roman}" in _p)
verifier("polices : le generique de la pile choisit la famille de repli",
         "\\newfontfamily\\policetitre{Latin Modern Sans}" in _p, f"p={_p}")
verifier("polices : le repli previent au lieu de se taire",
         "PackageWarningNoLine" in _p)

# Une police absente partout : le repli devient le choix, sans garde inutile.
theme_p._polices_installees = lambda: {"arial"}
try:
    _q = _preambule("PoliceAbsente, serif")
finally:
    theme_p._polices_installees = _sauve
verifier("polices : une police introuvable retombe sur Latin Modern",
         "\\setmainfont{Latin Modern Roman}" in _q)
verifier("polices : aucune garde quand le choix vaut deja le repli",
         "\\IfFontExistsTF" not in _q, f"q={_q[-200:]}")
verifier("polices : l'absence est declaree en commentaire",
         "Attention" in _q and "PoliceAbsente" in _q)

# Disponibilite inconnue : le nom demande est repris, sous garde.
theme_p._polices_installees = lambda: None
try:
    _r = _preambule("Georgia, serif")
finally:
    theme_p._polices_installees = _sauve
verifier("polices : sans mesure, la demande est reprise mais gardee",
         "\\IfFontExistsTF{Georgia}" in _r and "Attention" not in _r,
         f"r={_r[-260:]}")

# La mesure reessaie avant d'abandonner : un premier appel muet ne conclut pas.
import subprocess as _sp
_sauve_run, _sauve_which = _sp.run, theme_p.shutil.which
_appels = []


def _run_lent(cmd, **kw):
    _appels.append(kw.get("timeout"))
    if len(_appels) == 1:
        raise _sp.TimeoutExpired(cmd, kw.get("timeout"))

    class _R:
        stdout = "Georgia\nVerdana\n"
    return _R()


theme_p.shutil.which = lambda nom: "/usr/bin/fc-list"
_sp.run = _run_lent
try:
    _vues = theme_p._polices_installees()
finally:
    _sp.run, theme_p.shutil.which = _sauve_run, _sauve_which
verifier("polices : un premier appel qui expire ne fait pas conclure a l'absence",
         _vues == {"georgia", "verdana"}, f"vues={_vues}")
verifier("polices : le second essai laisse plus de temps que le premier",
         len(_appels) == 2 and _appels[1] > _appels[0], f"delais={_appels}")
