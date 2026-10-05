import { reactive, ref } from "vue";

// Données de présentation uniquement. Aucun service de l'application n'est appelé.
// Les modifications restent en mémoire et sont réinitialisées au rechargement.
export const money = (value) =>
  `${new Intl.NumberFormat("fr-FR").format(Math.round(value))} FCFA`;
export const number = (value) => new Intl.NumberFormat("fr-FR").format(value);
export const initials = (name) =>
  (name || "")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
export const normalize = (value) =>
  String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
export const tone = (value) =>
  ({
    Actif: "green",
    Active: "green",
    Terminé: "green",
    Résolu: "green",
    Succès: "green",
    Opérationnel: "green",
    Principal: "green",
    Suspendu: "red",
    Erreur: "red",
    Critique: "red",
    Échec: "red",
    "En essai": "orange",
    Majeur: "orange",
    Dégradé: "orange",
    Inactif: "gray",
    "En attente": "orange",
    "En cours": "blue",
    Mineur: "blue",
    Pro: "purple",
    Business: "blue",
    Entreprise: "purple",
    Administrateur: "purple",
    Propriétaire: "purple",
  })[value] || "gray";

export const navigation = [
  [
    "dashboard",
    "Vue d’ensemble",
    "home",
    "État global de la plateforme Ruinion AI",
  ],
  [
    "organisations",
    "Organisations",
    "building",
    "Toutes les organisations qui utilisent Ruinion AI",
  ],
  [
    "utilisateurs",
    "Utilisateurs",
    "users",
    "Tous les utilisateurs de la plateforme Ruinion AI",
  ],
  [
    "reunions",
    "Réunions",
    "calendar",
    "Toutes les réunions traitées sur la plateforme",
  ],
  [
    "abonnements",
    "Abonnements",
    "credit",
    "Gestion des plans, des abonnements et des quotas",
  ],
  [
    "usage",
    "Usage & coûts",
    "chart",
    "Suivi de l’utilisation de la plateforme et des coûts associés",
  ],
  [
    "aifournisseurs",
    "IA & fournisseurs",
    "cpu",
    "Configuration, suivi et performances des modèles et fournisseurs",
  ],
  [
    "incidents",
    "Incidents",
    "alert",
    "Suivi des erreurs, pannes et événements anormaux sur la plateforme",
  ],
  [
    "audit",
    "Audit & sécurité",
    "shield",
    "Suivi des actions et de la sécurité des comptes",
  ],
  [
    "configurations",
    "Configuration",
    "settings",
    "Paramètres généraux de la plateforme",
  ],
].map(([path, label, icon, description]) => ({
  path: `/admin/${path}`,
  label,
  icon,
  description,
}));

export const plans = [
  {
    name: "Essai",
    price: 0,
    users: 3,
    hours: 10,
    icon: "send",
    color: "green",
  },
  {
    name: "Pro",
    price: 25000,
    users: 20,
    hours: 30,
    icon: "crown",
    color: "purple",
  },
  {
    name: "Business",
    price: 50000,
    users: 50,
    hours: 100,
    icon: "building",
    color: "blue",
  },
  {
    name: "Entreprise",
    price: 150000,
    users: 200,
    hours: 500,
    icon: "star",
    color: "orange",
  },
];
const names = [
  "Ivoir Trips",
  "Société ABC",
  "Demo Corp",
  "Tech Solutions",
  "Groupe Horizon",
  "CI Énergies",
  "KPMG Côte d’Ivoire",
  "Canal+ CI",
  "SINOAFRIK AUTO",
  "Mondoukou Resort",
  "Atelier Abidjan",
  "Nova Conseil",
  "Baobab Studio",
  "Lagune Digital",
  "Akwa Finance",
  "Élan Formation",
  "Nimba Services",
  "Soleil Voyages",
];
export const organisations = reactive(
  names.map((name, i) => ({
    id: i + 1,
    name,
    plan: [
      "Pro",
      "Business",
      "Essai",
      "Pro",
      "Business",
      "Business",
      "Pro",
      "Entreprise",
    ][i % 8],
    status: i === 8 ? "Suspendu" : i === 2 || i === 11 ? "En essai" : "Actif",
    members: [11, 27, 3, 8, 19, 15, 12, 34, 4, 9][i % 10],
    meetings: [73, 142, 4, 31, 98, 67, 54, 221, 7, 28][i % 10],
    hours: [68, 76, 2, 12, 134, 89, 28, 403, 5, 38][i % 10],
    cost: [24700, 61300, 820, 12400, 38100, 29800, 27450, 98200, 1950, 9600][
      i % 10
    ],
    date: `${String(12 + (i % 16)).padStart(2, "0")}/09/2026`,
    email: `contact@${["ivoirtrips", "societeabc", "democorp", "techsolutions"][i % 4]}.example`,
    description:
      i === 0
        ? "Agence de tourisme, team building et événementiel."
        : "Une équipe qui simplifie ses réunions avec Ruinion AI.",
  })),
);
const userNames = [
  "Yannick Kouassi",
  "Mel Dossou",
  "Noël Kouamé",
  "Liliane V.",
  "Vanessa S.",
  "Émeric C.",
  "Franck A.",
  "Charles Atta",
  "Kouassi David",
  "Awa Bamba",
  "Fatou Koné",
  "Jean N’Guessan",
  "Aïcha Traoré",
  "Boris Yao",
  "Aminata Diallo",
  "Marc Koffi",
  "Sarah Kouadio",
  "Patrick B.",
  "Nadia Sy",
  "Paul D.",
  "Emma Konan",
  "Issa Touré",
  "Rose Aké",
  "Yves N’Dri",
];
export const users = reactive(
  userNames.map((name, i) => ({
    id: i + 1,
    name,
    email: `${normalize(name.split(" ")[0]).replace(/[^a-z]/g, "")}@exemple.test`,
    organization: names[i < 7 ? 0 : i % names.length],
    role: i === 0 ? "Propriétaire" : i % 7 === 0 ? "Administrateur" : "Membre",
    status: i === 9 ? "En attente" : i % 6 === 5 ? "Inactif" : "Actif",
    lastSeen: i === 9 ? "Jamais" : `Il y a ${(i % 5) + 1} h`,
    meetings: i === 9 ? 0 : 48 - i,
    date: "12 septembre 2026",
  })),
);
const titles = [
  "Réunion commerciale",
  "Point équipe TB",
  "Plan produit",
  "Revue stratégique",
  "Lancement du projet",
  "Suivi production",
  "Présentation client",
  "Réunion financière",
  "Point mensuel",
  "Atelier organisation",
];
export const meetings = reactive(
  Array.from({ length: 30 }, (_, i) => ({
    id: 8451 - i,
    title: titles[i % 10],
    organization: names[i === 0 || i === 1 ? 0 : i % names.length],
    creator: userNames[i % userNames.length],
    date: `${String(29 - (i % 25)).padStart(2, "0")}/09/2026`,
    duration: [102, 58, 75, 123, 45, 90, 65, 138, 52, 97][i % 10],
    cost: [487, 312, 420, 613, 198, 438, 362, 721, 296, 501][i % 10],
    status: i % 10 === 2 ? "Erreur" : i % 10 === 9 ? "En cours" : "Terminé",
  })),
);
export const providers = reactive([
  {
    name: "Mistral AI",
    icon: "cpu",
    color: "orange",
    status: "Actif",
    models: 2,
    calls: 8421,
    success: "98,2 %",
    latency: "6,4 s",
    configured: true,
  },
  {
    name: "OpenRouter",
    icon: "network",
    color: "navy",
    status: "Actif",
    models: 3,
    calls: 1238,
    success: "95,6 %",
    latency: "7,1 s",
    configured: true,
  },
  {
    name: "Voxtral",
    icon: "audio",
    color: "purple",
    status: "Actif",
    models: 1,
    calls: 1952,
    success: "97,4 %",
    latency: "12,3 s",
    configured: true,
  },
  {
    name: "ElevenLabs",
    icon: "audio",
    color: "gray",
    status: "Inactif",
    models: 1,
    calls: 0,
    success: "—",
    latency: "—",
    configured: false,
  },
]);
export const models = reactive([
  {
    id: 1,
    name: "voxtral-mini-latest",
    provider: "Voxtral",
    service: "Transcription",
    status: "Actif",
    role: "Principal",
    calls: 1842,
    success: "97,6 %",
    latency: "12,3 s",
    cost: 91200,
  },
  {
    id: 2,
    name: "whisper-large-v3",
    provider: "OpenRouter",
    service: "Transcription",
    status: "Actif",
    role: "Secours",
    calls: 110,
    success: "92,1 %",
    latency: "18,7 s",
    cost: 3400,
  },
  {
    id: 3,
    name: "mistral-large",
    provider: "Mistral AI",
    service: "Résumé (LLM)",
    status: "Actif",
    role: "Principal",
    calls: 8421,
    success: "98,2 %",
    latency: "6,4 s",
    cost: 37250,
  },
  {
    id: 4,
    name: "gemma",
    provider: "OpenRouter",
    service: "Résumé (LLM)",
    status: "Actif",
    role: "Secours",
    calls: 421,
    success: "93,1 %",
    latency: "8,9 s",
    cost: 4680,
  },
  {
    id: 5,
    name: "nex-n2.5-mini",
    provider: "OpenRouter",
    service: "Résumé (LLM)",
    status: "Actif",
    role: "Secours",
    calls: 312,
    success: "91,3 %",
    latency: "7,8 s",
    cost: 2450,
  },
  {
    id: 6,
    name: "text-embedding",
    provider: "Mistral AI",
    service: "Vectorisation",
    status: "Actif",
    role: "Principal",
    calls: 210,
    success: "99,0 %",
    latency: "1,2 s",
    cost: 820,
  },
  {
    id: 7,
    name: "multilingual-v2",
    provider: "ElevenLabs",
    service: "Synthèse vocale",
    status: "Inactif",
    role: "Secours",
    calls: 0,
    success: "—",
    latency: "—",
    cost: 0,
  },
]);
const incidentTitles = [
  "Limite de requêtes OpenRouter (429)",
  "Délai de transcription dépassé",
  "Erreur de génération Word",
  "Latence élevée Mistral Large",
  "Voxtral : passerelle indisponible",
  "Réponse JSON invalide",
  "Erreur d’authentification API",
  "Quota Mistral dépassé",
  "Espace disque faible",
  "Service OpenRouter indisponible",
  "Échec du téléversement",
  "Document incomplet",
];
export const incidents = reactive(
  incidentTitles.map((title, i) => ({
    id: 1023 - i,
    title,
    service: ["OpenRouter", "Transcription", "Documents", "Résumé (LLM)"][
      i % 4
    ],
    severity: ["Critique", "Majeur", "Mineur"][i % 3],
    status: i === 1 || i === 8 ? "En cours" : "Résolu",
    organization: names[i % 5],
    date: `${29 - i}/09/2026`,
    duration: [134, 97, 18, 65][i % 4],
    description:
      i === 0
        ? "Le fournisseur a renvoyé plusieurs erreurs 429. Le modèle de secours a pris le relais et le service a été rétabli."
        : "Un événement a interrompu cette étape du traitement. Les données de la réunion sont conservées.",
  })),
);
const actions = [
  "Plan modifié",
  "Membre ajouté",
  "Échec de connexion",
  "Fournisseur activé",
  "Réunion créée",
  "Rôle modifié",
  "Export des données",
  "Clé API ajoutée",
];
export const audit = reactive(
  Array.from({ length: 32 }, (_, i) => ({
    id: 1842 - i,
    date: `${String(29 - (i % 20)).padStart(2, "0")}/09/2026`,
    time: `${18 - (i % 9)}:42`,
    user: i % 8 === 2 ? "Système" : userNames[i % userNames.length],
    organization: names[i % names.length],
    action: actions[i % 8],
    category: [
      "Abonnements",
      "Utilisateurs",
      "Connexions",
      "Sécurité",
      "Réunions",
      "Utilisateurs",
      "Organisations",
      "Sécurité",
    ][i % 8],
    details: [
      "Passage du plan Pro au plan Business",
      "Invitation d’un membre dans l’organisation",
      "Identifiants incorrects",
      "Configuration du fournisseur mise à jour",
      "Traitement de la réunion lancé",
      "Permission de membre mise à jour",
      "Export du rapport mensuel",
      "Configuration d’une clé de démonstration",
    ][i % 8],
    ip: `192.0.2.${10 + i}`,
    status: i % 8 === 2 ? "Échec" : "Succès",
  })),
);
export const activity = [
  45, 38, 34, 52, 42, 74, 63, 81, 60, 57, 95, 74, 71, 92, 138, 62, 88, 80, 103,
  98, 121, 88, 69, 66, 55, 82, 63, 84, 70, 91,
];
export const duration = (value) =>
  value >= 60
    ? `${Math.floor(value / 60)} h ${String(value % 60).padStart(2, "0")}`
    : `${value} min`;
export const sum = (rows, key) =>
  rows.reduce((total, row) => total + row[key], 0);
export const alerts = [
  {
    title: "OpenRouter — erreurs 429",
    text: "Limite de requêtes atteinte sur le modèle de secours.",
    time: "Il y a 2 h",
    severity: "Critique",
  },
  {
    title: "Délai de transcription dépassé",
    text: "Une réunion attend une nouvelle tentative.",
    time: "Il y a 6 h",
    severity: "Majeur",
  },
  {
    title: "Latence élevée sur Mistral",
    text: "Temps de réponse moyen supérieur à 10 secondes.",
    time: "Il y a 1 j",
    severity: "Mineur",
  },
];
export const toast = ref("");
let toastTimer;
export function notify(message) {
  toast.value = message;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.value = "";
  }, 4500);
}
export function exportFile(name, content, type = "text/plain;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function exportCsv(rows, columns, filename) {
  const cell = (value) =>
    `"${String(value ?? "")
      .replace(/^[=+@-]/, "'$&")
      .replaceAll('"', '""')}"`;
  exportFile(
    filename,
    "\uFEFF" +
      [
        columns.map((c) => cell(c.label)),
        ...rows.map((row) => columns.map((c) => cell(row[c.key]))),
      ]
        .map((row) => row.join(";"))
        .join("\r\n"),
    "text/csv;charset=utf-8",
  );
}
