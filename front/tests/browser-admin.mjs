// Vérification des maquettes seules : aucun backend ni compte n'est nécessaire.
import assert from "node:assert/strict";
import { withBrowser, until, pause } from "./browser-helpers.mjs";

await withBrowser(
  "admin-smoke",
  async ({
    command,
    evaluate,
    click,
    visibleText,
    screenshot,
    errors,
    origin,
  }) => {
    await command("Page.addScriptToEvaluateOnNewDocument", {
      source: `
    window.__adminRequests = [];
    const originalFetch = window.fetch.bind(window);
    window.fetch = (...args) => { window.__adminRequests.push(String(args[0])); return originalFetch(...args); };
  `,
    });
    const pages = [
      ["dashboard", "Vue d’ensemble"],
      ["organisations", "Organisations"],
      ["utilisateurs", "Utilisateurs"],
      ["reunions", "Réunions"],
      ["abonnements", "Abonnements"],
      ["usage", "Usage & coûts"],
      ["aifournisseurs", "IA & fournisseurs"],
      ["incidents", "Incidents"],
      ["audit", "Audit & sécurité"],
      ["configurations", "Configuration"],
    ];
    const navigate = async (path, title) => {
      await command("Page.navigate", { url: `${origin}/admin/${path}` });
      await until(
        () =>
          evaluate(
            `document.querySelector('h1')?.textContent === ${JSON.stringify(title)}`,
          ),
        path,
      );
      await pause(100);
    };
    const input = (selector, value, event = "input") =>
      evaluate(
        `(() => {const input=document.querySelector(${JSON.stringify(selector)}); if(!input) throw new Error('Missing input'); input.value=${JSON.stringify(value)}; input.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));})()`,
      );
    for (const [path, title] of pages) {
      await navigate(path, title);
      assert.equal(
        await evaluate('document.querySelectorAll(".a-sidebar nav a").length'),
        10,
      );
      assert.equal(
        await evaluate(
          "document.documentElement.scrollWidth <= innerWidth + 1",
        ),
        true,
        `${path}: desktop overflow`,
      );
      assert.equal(
        await evaluate(
          'window.__adminRequests.filter(url => url.includes("/api/")).length',
        ),
        0,
        `${path}: unexpected backend request`,
      );
      await screenshot(`${path}-desktop.png`);
    }
    await navigate("organisations", "Organisations");
    await input("input[type=search]", "Ivoir Trips");
    await until(
      () =>
        evaluate(
          'document.querySelectorAll(".a-data-table tbody tr").length === 1',
        ),
      "organization search",
    );
    await input("input[type=search]", "inexistant");
    await until(() => visibleText("Aucun résultat"), "empty search");
    await click("Réinitialiser les filtres");
    await click("Page 2");
    assert.ok(await visibleText("11–18 sur 18 organisations"));
    await click("Nouvelle organisation");
    await until(
      () => evaluate('!!document.querySelector("dialog[open]")'),
      "create dialog",
    );
    await input("dialog[open] input", "Organisation Test UI");
    await input("dialog[open] input[type=email]", "demo@example.test");
    await evaluate(
      'document.querySelector("dialog[open] form").requestSubmit()',
    );
    await until(
      () =>
        evaluate(
          'document.querySelector(".a-detail-heading h2")?.textContent === "Organisation Test UI"',
        ),
      "local creation",
    );
    await click("Suspendre");
    assert.ok(await visibleText("Réactiver"));
    await click("Fermer les détails");
    assert.equal(
      await evaluate('!!document.querySelector(".a-detail")'),
      false,
    );

    await navigate("utilisateurs", "Utilisateurs");
    await click("Inviter un utilisateur");
    await until(
      () => evaluate('!!document.querySelector("dialog[open]")'),
      "invite dialog",
    );
    await input("dialog[open] input", "Membre Test UI");
    await input("dialog[open] input[type=email]", "membre@example.test");
    await evaluate(
      'document.querySelector("dialog[open] form").requestSubmit()',
    );
    await until(() => visibleText("Invitation simulée"), "local invitation");

    await navigate("reunions?id=8449", "Réunions");
    await click("Simuler une relance");
    assert.ok(await visibleText("Relance simulée"));
    await click("Transcription");
    await input('input[aria-label="Rechercher dans le texte"]', "budget");
    assert.ok(await visibleText("budget"));
    await click("Résumé");
    assert.ok(await visibleText("Décisions prises"));
    await click("Logs IA");
    assert.ok(await visibleText("Journal IA de démonstration"));

    await navigate("abonnements", "Abonnements");
    await click("Modifier");
    await until(
      () => evaluate('!!document.querySelector("dialog[open]")'),
      "subscription dialog",
    );
    await input("dialog[open] label:nth-child(2) select", "Business", "change");
    await evaluate(
      'document.querySelector("dialog[open] form").requestSubmit()',
    );
    await until(
      () => visibleText("Abonnement de démonstration modifié."),
      "subscription save",
    );

    await navigate("aifournisseurs", "IA & fournisseurs");
    await click("Configurer la clé ElevenLabs");
    await until(
      () => evaluate('!!document.querySelector("dialog[open]")'),
      "provider dialog",
    );
    await click("Utiliser une clé de démonstration");
    assert.ok(await visibleText("Clé fictive configurée"));

    await navigate("incidents", "Incidents");
    await click("Voir les logs");
    assert.ok(await visibleText("Logs de démonstration"));
    await click("Rouvrir l’incident");
    assert.ok(await visibleText("Marquer comme résolu"));

    await navigate("audit", "Audit & sécurité");
    await click("Fermer les autres sessions");
    assert.ok(await visibleText("Autres sessions de démonstration fermées"));

    await navigate("configurations", "Configuration");
    await input("input", "Ruinion AI Démo");
    await click("Enregistrer les modifications");
    assert.ok(await visibleText("Paramètres de démonstration enregistrés"));
    for (const title of [
      "Réunions",
      "IA & fournisseurs",
      "Facturation",
      "E-mail & notifications",
      "Sécurité",
      "Intégrations",
      "Stockage",
      "Personnalisation",
    ]) {
      await click(title);
      await pause(40);
      assert.ok(
        await evaluate(
          'document.querySelectorAll(".a-main .a-panel").length > 0',
        ),
        title,
      );
    }
    await command("Emulation.setDeviceMetricsOverride", {
      width: 390,
      height: 844,
      deviceScaleFactor: 1,
      mobile: true,
    });
    for (const [path, title] of pages) {
      await navigate(path, title);
      assert.equal(
        await evaluate(
          "document.documentElement.scrollWidth <= innerWidth + 1",
        ),
        true,
        `${path}: mobile overflow`,
      );
      await screenshot(`${path}-mobile.png`);
    }
    await click("Ouvrir le menu administrateur");
    await until(
      () => evaluate('!!document.querySelector(".a-sidebar-container.open")'),
      "mobile navigation",
    );
    await evaluate(
      `document.querySelector('.a-sidebar nav a[href="/admin/dashboard"]').click()`,
    );
    await until(
      () => visibleText("Activité des 30 derniers jours"),
      "mobile menu navigation",
    );
    assert.equal(
      await evaluate('!!document.querySelector(".a-sidebar-container.open")'),
      false,
    );
    assert.equal(errors.length, 0, JSON.stringify(errors));
    console.log(
      "PASS: 10 pages desktop/mobile, no backend, search, empty state, pagination, details, dialogs, mock actions, settings, mobile menu.",
    );
  },
);
