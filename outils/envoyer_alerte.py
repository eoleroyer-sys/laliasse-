#!/usr/bin/env python3
"""
Envoie une alerte La Liasse par Brevo, seulement aux inscrits concernés.

  python3 outils/envoyer_alerte.py alertes/FICHIER.txt --apercu    # fabrique l'e-mail, n'envoie rien
  python3 outils/envoyer_alerte.py alertes/FICHIER.txt --test      # l'envoie à EMAIL_TEST seulement
  python3 outils/envoyer_alerte.py alertes/FICHIER.txt --envoyer   # l'envoie aux segments concernés

Variables d'environnement (jamais écrites dans un fichier) :
  BREVO_API_KEY      clé API Brevo (obligatoire pour --test et --envoyer)
  EMAIL_TEST         ton adresse, pour --test
  EXPEDITEUR_EMAIL   par défaut contact@laliasse.fr
  EXPEDITEUR_NOM     par défaut La Liasse

Aucune dépendance : bibliothèque standard de Python 3.
"""
import argparse, datetime, html, json, os, pathlib, re, sys, urllib.error, urllib.request

RACINE = pathlib.Path(__file__).resolve().parent.parent
GABARIT = RACINE / "emails" / "alerte.html"
SEGMENTS = RACINE / "outils" / "segments.json"
API = os.environ.get("BREVO_API_URL", "https://api.brevo.com/v3")  # modifiable pour les tests

OBLIGATOIRES = ["titre", "date", "reference", "statut", "cibles", "apercu", "propose", "concerne", "etape", "source_nom", "source_url"]
STATUTS = {
    "propose": ("Proposé, pas encore voté", "#FBE4EA", "#8A1C3E"),
    "adopte": ("Adopté", "#DCEDE6", "#0E4A3C"),
    "rejete": ("Rejeté", "#ECEFEE", "#36443E"),
    "tombe": ("Tombé", "#ECEFEE", "#36443E"),
    "en_vigueur": ("En vigueur", "#DCEDE6", "#0E4A3C"),
}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
# Garde-fou AMF : une alerte informe, elle ne dit jamais quoi faire de son argent.
INTERDITS = re.compile(r"\b(achetez|vendez|cl[ôo]turez|investissez|placez|arbitrez|retirez votre|fermez votre)\b", re.I)


def stop(msg):
    print("ERREUR : " + msg, file=sys.stderr)
    sys.exit(1)


def lire_alerte(chemin):
    champs = {}
    for n, ligne in enumerate(pathlib.Path(chemin).read_text(encoding="utf-8").splitlines(), 1):
        if not ligne.strip() or ligne.lstrip().startswith("#"):
            continue
        if ":" not in ligne:
            stop(f"ligne {n} sans « nom: valeur » : {ligne!r}")
        cle, val = ligne.split(":", 1)
        champs[cle.strip().lower()] = val.strip()
    manquants = [c for c in OBLIGATOIRES if not champs.get(c)]
    if manquants:
        stop("champs manquants : " + ", ".join(manquants))
    if champs["statut"] not in STATUTS:
        stop("statut inconnu « %s » (choisir : %s)" % (champs["statut"], ", ".join(STATUTS)))
    try:
        champs["_date"] = datetime.date.fromisoformat(champs["date"])
    except ValueError:
        stop("date au format AAAA-MM-JJ attendue")
    for c in ("source_url", "verifier_url"):
        if champs.get(c) and not champs[c].startswith("https://"):
            stop(f"{c} doit commencer par https://")
    texte = " ".join(v for k, v in champs.items() if not k.startswith("_"))
    if INTERDITS.search(texte):
        stop("formulation de conseil détectée (« %s ») : une alerte informe, elle ne recommande pas." % INTERDITS.search(texte).group(0))
    if len(champs["titre"]) > 110:
        stop("titre trop long pour un objet d'e-mail (110 caractères au plus)")
    champs["_cibles"] = [c.strip() for c in champs["cibles"].split(",") if c.strip()]
    return champs


def segments_pour(cibles):
    table = json.loads(SEGMENTS.read_text(encoding="utf-8"))
    ids, absentes = [], []
    for c in cibles:
        if c not in table:
            stop(f"cible « {c} » inconnue de outils/segments.json")
        if int(table[c]) > 0:
            ids.append(int(table[c]))
        else:
            absentes.append(c)
    return sorted(set(ids)), absentes


def fabriquer_html(a):
    e = lambda s: html.escape(s, quote=True)
    libelle, fond, encre = STATUTS[a["statut"]]
    d = a["_date"]
    bloc_verifier = ""
    if a.get("verifier"):
        lien = f' <a href="{e(a["verifier_url"])}" style="color:#0E4A3C;">{e(a["verifier_url"].replace("https://", ""))}</a>' if a.get("verifier_url") else ""
        bloc_verifier = ('<p style="margin:0 0 4px;font-size:14px;font-weight:bold;color:#13201B;">À vérifier</p>'
                         f'<p style="margin:0 0 16px;">{e(a["verifier"])}{lien}</p>')
    valeurs = {
        "titre": e(a["titre"]), "apercu": e(a["apercu"]), "reference": e(a["reference"]),
        "statut": e(libelle), "statut_fond": fond, "statut_texte": encre,
        "date_longue": f"{d.day} {MOIS[d.month - 1]} {d.year}",
        "cibles": e(", ".join(a["_cibles"])), "propose": e(a["propose"]), "concerne": e(a["concerne"]),
        "etape": e(a["etape"]), "source_nom": e(a["source_nom"]), "source_url": e(a["source_url"]),
        "bloc_verifier": bloc_verifier,
    }
    page = GABARIT.read_text(encoding="utf-8")
    for k, v in valeurs.items():
        page = page.replace("{{" + k + "}}", v)
    reste = re.findall(r"\{\{[a-z_]+\}\}", page)
    if reste:
        stop("champs non remplis dans le gabarit : " + ", ".join(reste))
    return page


def appel(methode, chemin, corps=None):
    cle = os.environ.get("BREVO_API_KEY")
    if not cle:
        stop("variable BREVO_API_KEY absente")
    req = urllib.request.Request(API + chemin, method=methode,
                                 data=json.dumps(corps).encode() if corps is not None else None,
                                 headers={"api-key": cle, "accept": "application/json", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            brut = r.read()
            return r.status, (json.loads(brut) if brut else None)
    except urllib.error.HTTPError as err:
        stop(f"Brevo a répondu {err.code} sur {chemin} : {err.read().decode(errors='replace')}")


def main():
    p = argparse.ArgumentParser(description="Envoyer une alerte La Liasse par Brevo.")
    p.add_argument("fichier")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apercu", action="store_true", help="fabrique l'e-mail sans rien envoyer")
    mode.add_argument("--test", action="store_true", help="envoie à EMAIL_TEST seulement")
    mode.add_argument("--envoyer", action="store_true", help="envoie aux inscrits concernés")
    args = p.parse_args()

    a = lire_alerte(args.fichier)
    page = fabriquer_html(a)
    ids, absentes = segments_pour(a["_cibles"])
    nom_fichier = pathlib.Path(args.fichier).stem

    print("Alerte  :", a["titre"])
    print("Cibles  :", ", ".join(a["_cibles"]), "→ segments Brevo", ids or "aucun")
    if absentes:
        print("Attention : pas de segment pour", ", ".join(absentes), "(numéro à 0 dans outils/segments.json)")

    if args.apercu:
        sortie = RACINE / "outils" / f"apercu-{nom_fichier}.html"
        sortie.write_text(page, encoding="utf-8")
        print("Aperçu  :", sortie)
        return

    if args.envoyer and not ids:
        stop("aucun segment Brevo pour ces cibles : rien n'est envoyé")

    expediteur = {"name": os.environ.get("EXPEDITEUR_NOM", "La Liasse"),
                  "email": os.environ.get("EXPEDITEUR_EMAIL", "contact@laliasse.fr")}
    corps = {
        "name": f"Alerte {a['date']} · {a['titre']}"[:180],
        "subject": a["titre"],
        "previewText": a["apercu"],
        "sender": expediteur,
        "replyTo": expediteur["email"],
        "htmlContent": page,
        "tag": "alerte",
    }
    if ids:
        corps["recipients"] = {"segmentIds": ids}
    _, cree = appel("POST", "/emailCampaigns", corps)
    cid = cree["id"]
    print("Campagne Brevo créée :", cid)

    if args.test:
        dest = os.environ.get("EMAIL_TEST")
        if not dest:
            stop("variable EMAIL_TEST absente")
        appel("POST", f"/emailCampaigns/{cid}/sendTest", {"emailTo": [dest]})
        print("Test envoyé à", dest, "(la campagne reste en brouillon dans Brevo)")
    else:
        appel("POST", f"/emailCampaigns/{cid}/sendNow")
        print("Envoyée aux segments", ids)


if __name__ == "__main__":
    main()
