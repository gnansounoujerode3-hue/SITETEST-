# Méthodologie de motion design pour COOL

## Intention

Le mouvement doit aider à comprendre l’interface — indiquer qu’un élément est cliquable, guider le regard ou relier deux états — et non ralentir la navigation. Choisir **une animation principale par écran**, puis garder les autres effets discrets et cohérents.

## Quel outil choisir ?

| Besoin | Ressource | Usage recommandé |
|---|---|---|
| Boutons, cartes, loaders ou petits composants | [Uiverse](https://uiverse.io/) | Chercher une idée de composant, puis vérifier son accessibilité, son comportement mobile et sa licence avant de l’adapter. |
| Transitions CSS réglables | [Animista](https://animista.net/), [CSS Wand](https://www.csswand.dev/), [Hover.css](https://ianlunn.github.io/Hover/) | Préférer CSS pur pour les états locaux : survol, focus, appui, apparition simple. Éviter d’empiler plusieurs effets sur le même élément. |
| Composants animés React/Tailwind | [Magic UI](https://magicui.design/), [Aceternity UI](https://ui.aceternity.com/) | Réutiliser ponctuellement un motif complexe si le projet utilise déjà la pile nécessaire ; ne pas ajouter une dépendance entière pour un seul effet. |
| Séquences, SVG et animation au défilement | [GSAP](https://gsap.com/) et ses exemples [CodePen](https://codepen.io/) | Réserver GSAP/ScrollTrigger aux séquences coordonnées ou au scroll narratif. Prévoir le nettoyage des animations et ne pas bloquer le défilement. |
| Illustration vectorielle animée | [LottieFiles](https://lottiefiles.com/) | Utiliser une animation légère et pertinente, la charger au bon moment et fournir une image fixe ou un état statique si le mouvement est réduit. |

Les exemples sont des références de conception : vérifier les licences, versions et dépendances avant de reprendre du code dans le projet.

## Processus de conception

1. **Définir le rôle.** Écrire ce que le mouvement doit communiquer : retour d’action, hiérarchie, transition d’état ou narration. S’il n’a pas de rôle clair, le supprimer.
2. **Dessiner les états.** Décrire l’état initial, l’interaction et l’état final avant de coder. Le contenu doit rester compréhensible sans animation.
3. **Choisir une seule direction.** Par exemple : une légère montée à l’apparition, un reflet qui traverse un bouton, ou une séquence de révélation. Réserver les effets lumineux, parallaxes et boucles aux éléments importants.
4. **Régler durée et courbe.** Utiliser une accélération/décélération douce ; éviter les rebonds agressifs et les animations trop longues.
5. **Prototyper au plus simple.** Commencer en CSS. Passer à Framer Motion ou GSAP seulement si une chorégraphie, une physique ou une synchronisation le justifie.
6. **Tester et réduire.** Vérifier clavier, tactile, petits écrans, performances et préférence « réduire les animations » du système.

## Repères de rythme

| Situation | Durée indicative |
|---|---:|
| Retour d’appui ou activation | 100–180 ms |
| Survol / focus d’un contrôle | 150–220 ms |
| Transition d’état ou petite apparition | 220–400 ms |
| Entrée d’une section importante | 400–650 ms |
| Séquence narrative au scroll | 500–900 ms, uniquement si elle reste facile à parcourir |

Ces valeurs sont des points de départ, pas des règles fixes. Les éléments secondaires peuvent apparaître avec un léger décalage (environ 40–80 ms) ; éviter les longues cascades qui retardent l’accès au contenu.

## Base CSS accessible et performante

```css
:root {
  --motion-ease-out: cubic-bezier(.2, .8, .2, 1);
  --motion-fast: 180ms;
  --motion-enter: 480ms;
}

/* Les animations doivent idéalement modifier transform et opacity. */
[data-reveal] {
  opacity: 0;
  transform: translateY(14px);
  transition:
    opacity var(--motion-enter) var(--motion-ease-out),
    transform var(--motion-enter) var(--motion-ease-out);
}
[data-reveal].is-visible {
  opacity: 1;
  transform: translateY(0);
}

.button {
  transition: transform var(--motion-fast) var(--motion-ease-out),
              box-shadow var(--motion-fast) var(--motion-ease-out);
}
.button:hover { transform: translateY(-2px); }
.button:active { transform: scale(.98); }
.button:focus-visible { outline: 3px solid currentColor; outline-offset: 3px; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
  [data-reveal] { opacity: 1; transform: none; }
}
```

Déclencher les apparitions à l’entrée dans la fenêtre avec `IntersectionObserver` plutôt qu’avec des boucles de mesure au défilement. Si JavaScript ne se charge pas, le texte et les contrôles doivent rester visibles et utilisables. Les animations CSS ci-dessus illustrent un motif de départ ; elles doivent être intégrées aux conventions et aux styles déjà présents dans le projet.

## Règles de qualité

- Animer en priorité `transform` et `opacity` ; éviter d’animer continuellement `width`, `height`, `top`, `left` ou de grandes zones avec `filter`.
- Ne jamais faire dépendre une action, une information ou la lisibilité d’un mouvement.
- Toujours garder un `:focus-visible` identifiable ; le survol ne doit pas être l’unique retour d’état.
- Respecter `prefers-reduced-motion` : supprimer les déplacements/parallaxes et conserver une transition instantanée ou un état statique.
- Désactiver les animations hors écran et nettoyer les timelines/listeners à la sortie d’un composant.
- Sur mobile, privilégier les états tactiles et éviter les effets qui exigent un pointeur ou un défilement piloté.
- Contrôler le poids des animations Lottie, les polices et les images ; éviter plusieurs animations infinies simultanées.
- Tester sur un appareil modeste : pas de saccade, de saut de mise en page, de contenu caché ni de défilement capturé.

## Critère de validation

Une animation est prête si elle clarifie l’interface, se termine rapidement, fonctionne au clavier et au tactile, respecte la réduction des animations et n’empêche jamais l’accès immédiat au contenu.
