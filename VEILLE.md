# Veille du matin · La Liasse

Consignes pour la veille automatique (tâche planifiée chaque matin).

## But

Repérer ce qui a changé depuis la veille, dans la loi ou le budget, pour l'épargne des particuliers en France.
Pour chaque mesure qui en vaut la peine, écrire un fichier d'alerte dans `alertes/` et le pousser sur `main`.
Le dépôt déclenche alors un **envoi de test** à Eole (jamais aux inscrits). Eole relit, puis lance lui-même
le mode « envoyer » dans GitHub Actions.

## Ce qui compte

Placements suivis (valeurs exactes du champ `cibles`) :
`PEA`, `PEA-PME`, `Assurance-vie`, `PER`, `Compte-titres`, `Livrets`, `Epargne salariale`, `Crypto`,
`Location meublee`, `Immobilier locatif`, `Transmission`, `Retraite`.

Une alerte mérite d'être écrite si :
- un texte a franchi une étape (amendement adopté en commission ou en séance, vote d'une chambre, CMP, 49.3,
  décision du Conseil constitutionnel, publication au Journal officiel, décret, doctrine BOFiP) ;
- et elle change quelque chose de concret pour un épargnant (taux, plafond, fiscalité, date limite, condition).

Ne pas écrire d'alerte pour : une simple déclaration, une rumeur, un amendement seulement déposé,
une mesure déjà couverte par un fichier de `alertes/` sans nouvelle étape.

## Sources à consulter

Les sources officielles servent de preuve, la presse sert à repérer :
- Assemblée nationale et Sénat : dossiers législatifs PLF et PLFSS de l'année, comptes rendus, amendements adoptés.
- Légifrance / Journal officiel : lois, décrets publiés.
- BOFiP (bofip.impots.gouv.fr), service-public.fr, economie.gouv.fr, Banque de France (Livret A).
- Presse : Les Échos, Le Monde, Le Figaro Patrimoine, L'AGEFI, Capital, Boursorama.

`source_url` doit pointer vers une page **officielle** ouverte et lue, jamais un simple extrait de recherche.

## Format

Copier le modèle `alertes/2026-11-12-epargne-oubliee.txt`. Nom : `AAAA-MM-JJ-mots-cles.txt`, sans accents ni espaces.
Champs obligatoires : titre (110 caractères max), date, reference, statut (`propose`, `adopte`, `rejete`, `tombe`,
`en_vigueur`), cibles, apercu, propose, concerne, etape, source_nom, source_url. Facultatifs : verifier, verifier_url.

Avant de pousser : `python3 outils/envoyer_alerte.py alertes/FICHIER.txt --apercu` doit réussir.

## Règles de fond

- Information, jamais conseil : pas de « achetez, vendez, clôturez, investissez, placez, arbitrez ».
- Distinguer ce qui est proposé, adopté par une chambre, définitivement voté et en vigueur.
- Phrases courtes, vocabulaire simple, chiffres exacts avec leur date.
- Au plus 2 alertes par matin ; s'il n'y a rien de solide, ne rien pousser.
