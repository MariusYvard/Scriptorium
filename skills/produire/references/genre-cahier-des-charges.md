# Playbook : cahier des charges et spécification technique

Document contractuel ou interne qui définit un besoin et les exigences d'une solution, pour une équipe technique, un prestataire ou un fournisseur. Finalité : que le lecteur puisse concevoir, chiffrer et vérifier. La précision et la testabilité priment sur le style.

## Structure

1. Contexte et objet : le besoin, le problème à résoudre, le périmètre (ce qui est inclus et ce qui est exclu).
2. Parties prenantes et utilisateurs.
3. Exigences fonctionnelles : ce que la solution doit faire, numérotées et atomiques.
4. Exigences non fonctionnelles : performance, sécurité, disponibilité, conformité, maintenabilité.
5. Contraintes : techniques, réglementaires, budgétaires, calendaires, d'interopérabilité.
6. Critères d'acceptation : comment vérifier que chaque exigence est remplie.
7. Livrables et jalons : calendrier, points de contrôle.
8. Annexes : interfaces, schémas, glossaire.

## Écrire une exigence

Une exigence est numérotée, atomique (une seule chose), vérifiable et sans ambiguïté. Employer "doit" pour l'obligatoire, "devrait" pour le recommandé. Bannir le vague ("rapide", "convivial") au profit du mesurable ("réponse sous 200 ms au 95e centile").

```
EX-[domaine]-[n] : Le système doit [action mesurable] dans [condition].
Critère d'acceptation : [test ou mesure qui valide l'exigence].
Priorité : [obligatoire / recommandé / optionnel].
```

## Barre de qualité

- Chaque exigence est numérotée, atomique et vérifiable.
- Le périmètre dit explicitement ce qui est exclu.
- Les exigences non fonctionnelles sont chiffrées (seuils, charges).
- Chaque exigence porte un critère d'acceptation.
- Aucun terme vague non défini, glossaire pour les sigles.

## Pièges à éviter

- Une exigence qui en cache plusieurs, donc non testable.
- Décrire une solution au lieu d'un besoin (sur-spécifier la mise en œuvre).
- Des adjectifs non mesurables.
- Oublier les exigences non fonctionnelles, souvent la cause des échecs.

## Publics et exemples

Genre de l'ingénieur et du chef de projet. Exemples : le cahier des charges d'un capteur (exigences de précision, d'environnement, de conformité) ; la spécification d'une interface applicative (contrats, charges, sécurité, critères d'acceptation).
